from flask import Blueprint, render_template, request, g
from ckan.plugins import toolkit
from ckan.lib.helpers import flash_error, redirect_to
from ckan.lib.pagination import Page
import logging

import ckanext.artesp_theme.helpers as artesp_helpers
from ckanext.artesp_theme.logic import auth_helpers

log = logging.getLogger(__name__)

artesp_theme = Blueprint('artesp_theme', __name__)


def about_ckan():
    return render_template('static/about_ckan.html')


def terms():
    return render_template('static/terms.html')


def privacy():
    return render_template('static/privacy.html')


def harvesting():
    return render_template('static/harvesting.html')


def statistics():
    dashboard = artesp_helpers.get_dashboard_statistics(
        {
            "theme": request.args.get("theme"),
            "period": request.args.get("period"),
        }
    )
    return render_template("statistics/index.html", dashboard=dashboard)


artesp_theme.add_url_rule('/about-ckan', view_func=about_ckan)
artesp_theme.add_url_rule('/terms', view_func=terms)
artesp_theme.add_url_rule('/privacy', view_func=privacy)
artesp_theme.add_url_rule('/harvesting', view_func=harvesting)
artesp_theme.add_url_rule('/estatisticas', view_func=statistics)


def _user_verify():
    """Authentication endpoint that delegates to the configured identity provider."""
    try:
        from ckan.model import User
        from ckanext.ldap.lib.exceptions import MultipleMatchError, UserConflictError
        from ckanext.ldap.lib.search import find_ldap_user
        from ckanext.ldap.routes import _helpers

        params = toolkit.request.values
        came_from = params.get('came_from', None)

        if 'login' in params and 'password' in params:
            login = params['login']
            password = params['password']
            try:
                ldap_user_dict = find_ldap_user(login)
            except MultipleMatchError as e:
                return _helpers.login_failed(notice=str(e))

            if ldap_user_dict and _helpers.check_ldap_password(
                ldap_user_dict['cn'], password
            ):
                try:
                    if auth_helpers.should_reconcile_ldap_login():
                        auth_helpers.ensure_artesp_org_state()
                    user_name = _helpers.get_or_create_ldap_user(ldap_user_dict)
                    auth_helpers.ensure_user_membership_in_artesp(user_name)
                    auth_helpers.ensure_user_memberships_in_all_groups(user_name)
                except UserConflictError as e:
                    return _helpers.login_failed(error=str(e))
                return _helpers.login_success(user_name, came_from=came_from)
            elif ldap_user_dict:
                if toolkit.config['ckanext.ldap.ckan_fallback']:
                    exists = _helpers.ckan_user_exists(login)
                    if exists['exists'] and not exists['is_ldap']:
                        return _helpers.login_failed(
                            error=toolkit._(
                                'Conflito de nome de usuário. Por favor, entre em contato com o administrador do site.'
                            )
                        )
                return _helpers.login_failed(
                    error=toolkit._('Nome de usuário ou senha incorretos.') + ' [LDAP1]'
                )
            elif toolkit.config['ckanext.ldap.ckan_fallback']:
                try:
                    user_dict = _helpers.get_user_dict(login)
                    user = User.by_name(user_dict['name'])
                except toolkit.ObjectNotFound:
                    user = None
                if user and user.validate_password(password):
                    return _helpers.login_success(user.name, came_from=came_from)
                return _helpers.login_failed(
                    error=toolkit._('Nome de usuário ou senha incorretos.') + ' [LDAP2]'
                )
            else:
                return _helpers.login_failed(
                    error=toolkit._('Nome de usuário ou senha incorretos.') + ' [LDAP3]'
                )

        return _helpers.login_failed(
            error=toolkit._('Por favor, insira o nome de usuário e a senha.')
        )
    except ImportError:
        log.warning("ckanext-ldap not available, falling back to default login")
        return redirect_to(toolkit.url_for('user.login'))


artesp_theme.add_url_rule(
    '/user/verify', view_func=_user_verify, methods=['POST']
)


def _dataset_collaborator_submit(id):
    from ckan.common import current_user

    context = {'user': getattr(current_user, 'name', '')}
    username = (request.form.get('username') or '').strip()
    capacity = (request.form.get('capacity') or '').strip()

    data_dict = {
        'id': id,
        'username': username,
    }
    if capacity:
        data_dict['capacity'] = capacity

    try:
        toolkit.get_action('package_collaborator_create')(context, data_dict)
    except toolkit.NotAuthorized as exc:
        flash_error(str(exc))
    except toolkit.ObjectNotFound:
        flash_error(toolkit._('User not found'))
    except toolkit.ValidationError as exc:
        message = exc.error_summary
        if not message and exc.error_dict:
            message = '; '.join(
                '{}: {}'.format(field, ', '.join(errors))
                for field, errors in exc.error_dict.items()
            )
        flash_error(message or toolkit._('Unable to save collaborator.'))
    else:
        return redirect_to(toolkit.url_for('dataset.collaborators_read', id=id))

    redirect_kwargs = {'id': id}
    if request.args.get('user_id'):
        redirect_kwargs['user_id'] = request.args['user_id']
    return redirect_to(toolkit.url_for('dataset.new_collaborator', **redirect_kwargs))


artesp_theme.add_url_rule(
    '/dataset/collaborators/<id>/submit',
    endpoint='dataset_collaborator_submit',
    view_func=_dataset_collaborator_submit,
    methods=['POST'],
)


def resource_search():
    """
    Controller for searching resources directly.
    """
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    sort = request.args.get('sort', 'metadata_modified desc')
    format_filter = request.args.get('format', None)
    group_filter = request.args.get('group', None)

    # Construct a Solr query for resources
    # resource_search expects 'query' parameter in the format 'field:term'
    log.info(f"Resource Search - User Query: {q}, Format Filter: {format_filter}, Sort: {sort}")

    try:
        # Determine query string
        query_string = q.strip() if q else ''
        
        # Check if we should use field search or simple search
        # If query has ':', it's likely a specific field search
        is_field_search = ':' in query_string

        all_resources = {}

        if query_string:
            if is_field_search:
                # Advanced syntax, pass it through
                try:
                    data_dict = {
                        'query': query_string,
                        'limit': 2000, # Fetch more for manual sorting
                        'offset': 0
                    }
                    results = toolkit.get_action('resource_search')(None, data_dict)
                    for res in results['results']:
                        all_resources[res['id']] = res
                except Exception as e:
                     log.warning(f"Resource Search - Error searching advanced query {query_string}: {e}")
            else:
                # Search across multiple fields and combine results
                for field in ['name', 'description', 'format']:
                    try:
                        field_results = toolkit.get_action('resource_search')(None, {
                            'query': f'{field}:{query_string}',
                            'limit': 1000,
                        })
                        for resource in field_results.get('results', []):
                            all_resources[resource['id']] = resource
                    except Exception as field_error:
                        pass
        else:
             # Empty query - search in name field for anything
            data_dict = {
                'query': 'name:',
                'limit': 2000,
                'offset': 0
            }
            results = toolkit.get_action('resource_search')(None, data_dict)
            for res in results['results']:
                all_resources[res['id']] = res

        # Convert to list
        resources_list = list(all_resources.values())

        # Enrich ALL resources with package (dataset) information BEFORE filtering/pagination
        # This allows us to calculate group facets and improves performance with caching
        package_cache = {}
        for resource in resources_list:
            try:
                pkg_id = resource['package_id']

                # Check cache first to avoid duplicate package_show calls
                if pkg_id not in package_cache:
                    package = toolkit.get_action('package_show')(None, {'id': pkg_id})
                    package_cache[pkg_id] = package
                else:
                    package = package_cache[pkg_id]

                # Store package metadata with resource
                resource['package_name'] = package.get('title') or package.get('name')
                resource['groups'] = package.get('groups', [])

            except Exception as pkg_error:
                log.warning(f"Could not fetch package info for {resource['package_id']}: {pkg_error}")
                resource['package_name'] = None
                resource['groups'] = []

        # Apply format filter
        if format_filter:
            resources_list = [r for r in resources_list if r.get('format') == format_filter]

        # Apply group filter
        if group_filter:
            resources_list = [r for r in resources_list
                              if any(g.get('name') == group_filter for g in r.get('groups', []))]

        # Apply Manual Sorting
        if sort:
            try:
                parts = sort.split()
                sort_field = parts[0]
                sort_dir = parts[1] if len(parts) > 1 else 'asc'
                reverse = sort_dir.lower() == 'desc'
            except Exception:
                sort_field = 'metadata_modified'
                reverse = True
            
            # Helper to get sort value safely
            def get_sort_value(x):
                val = x.get(sort_field)
                if val is None:
                    # Fallback for missing values
                    return ''
                return str(val).lower()

            resources_list.sort(key=get_sort_value, reverse=reverse)

        count = len(resources_list)

        # Apply pagination manually
        start_idx = offset
        end_idx = offset + limit
        resources = resources_list[start_idx:end_idx]

        log.info(f"Resource Search - Found {count} total results, returning {len(resources)} resources")

        # Calculate format facets from ALL results (before pagination)
        format_facets = {}
        for res in resources_list:
            fmt = res.get('format')
            if fmt:
                format_facets[fmt] = format_facets.get(fmt, 0) + 1

        # Calculate group facets from ALL results (before pagination)
        group_facets = {}
        for res in resources_list:
            for group in res.get('groups', []):
                group_name = group.get('name')
                group_title = group.get('title') or group_name
                if group_name:
                    if group_name not in group_facets:
                        group_facets[group_name] = {'title': group_title, 'count': 0}
                    group_facets[group_name]['count'] += 1

    except Exception as e:
        log.error(f"Resource Search - Error: {e}")
        resources = []
        count = 0
        format_facets = {}
        group_facets = {}

    def pager_url(q=None, page=None, sort=None, format=None, group=None):
        params = {}
        if q:
            params['q'] = q
        if page:
            params['page'] = page
        if sort:
            params['sort'] = sort
        if format:
            params['format'] = format
        if group:
            params['group'] = group
        return toolkit.url_for('artesp_theme.resource_search', **params)

    page_obj = Page(
        collection=resources,
        page=page,
        items_per_page=limit,
        item_count=count,
        url=lambda **kwargs: pager_url(
            q=kwargs.get('q', q),
            page=kwargs.get('page'),
            sort=kwargs.get('sort', sort),
            format=kwargs.get('format', format_filter),
            group=kwargs.get('group', group_filter)
        ),
    )

    # Sort facets by count (descending)
    sorted_facets = sorted(format_facets.items(), key=lambda x: x[1], reverse=True)
    sorted_group_facets = sorted(group_facets.items(), key=lambda x: x[1]['count'], reverse=True)

    return render_template(
        'resource/search.html',
        q=q,
        page=page_obj,
        resources=resources,
        count=count,
        sort_by_selected=sort,
        format_facets=sorted_facets,
        format_filter=format_filter,
        group_facets=sorted_group_facets,
        group_filter=group_filter
    )


artesp_theme.add_url_rule('/resources', view_func=resource_search)


def _check_captcha_fail_closed():
    from ckan.lib import captcha as _captcha
    if not toolkit.config.get("ckan.recaptcha.privatekey"):
        raise toolkit.ValidationError({"captcha": [toolkit._("Captcha not configured")]})
    _captcha.check_recaptcha(request)


def rating_submit(package_name: str):
    from ckan.common import current_user
    from ckan.lib.helpers import flash_error as _flash_error, flash_success as _flash_success
    from ckanext.artesp_theme.logic.rating import RATING_CRITERIA

    if not getattr(current_user, "is_authenticated", False):
        return redirect_to(toolkit.url_for("user.login"))

    try:
        _check_captcha_fail_closed()
    except toolkit.ValidationError:
        flash_error(toolkit._("Captcha validation failed. Please try again."))
        return redirect_to(toolkit.url_for("dataset.read", id=package_name))

    criteria = {}
    for key in RATING_CRITERIA:
        raw = (request.form.get(f"criteria_{key}") or "").strip().lower()
        if raw:
            criteria[key] = raw in ("true", "1", "yes")

    action_context = {"user": current_user.name}

    try:
        pkg = toolkit.get_action("package_show")(action_context, {"id": package_name})
        toolkit.get_action("dataset_rating_upsert")(
            action_context,
            {
                "package_id": pkg["id"],
                "overall_rating": request.form.get("overall_rating"),
                "criteria": criteria,
                "comment": request.form.get("comment", ""),
            },
        )
        _flash_success(toolkit._("Your rating was submitted successfully."))
    except toolkit.ValidationError as exc:
        errors = "; ".join(
            v[0] if isinstance(v, list) else str(v)
            for v in exc.error_dict.values()
        )
        flash_error(toolkit._("Invalid rating: {errors}").format(errors=errors))
    except toolkit.NotAuthorized:
        flash_error(toolkit._("You are not authorized to rate this dataset."))
        return redirect_to(toolkit.url_for("dataset.search"))
    except toolkit.ObjectNotFound:
        flash_error(toolkit._("Dataset not found or you are not allowed to rate it."))
        return redirect_to(toolkit.url_for("dataset.search"))

    return redirect_to(toolkit.url_for("dataset.read", id=package_name))


artesp_theme.add_url_rule(
    "/dataset/<package_name>/rate",
    endpoint="rating_submit",
    view_func=rating_submit,
    methods=["POST"],
)

@artesp_theme.before_app_request
def restrict_stats_page_access():
    """
    Restricts access to the /stats page to authenticated users.
    """
    if request.path == '/stats':
        if not g.user:  # g.user is the username, empty for anonymous
            flash_error(toolkit._('You must be logged in to access the statistics page.'))
            return redirect_to(toolkit.url_for('user.login'))
    return None # Continue processing the request
