from datetime import datetime, timedelta, timezone

import ckan.model as model
from flask import Blueprint, Response, abort, jsonify, render_template, request, g
from ckan.plugins import toolkit
from ckan.lib.helpers import flash_error, redirect_to
from ckan.lib.pagination import Page
import logging

import ckanext.artesp_theme.helpers as artesp_helpers
from ckanext.artesp_theme.logic import audit_capture, audit_query, auth_helpers

log = logging.getLogger(__name__)

artesp_theme = Blueprint('artesp_theme', __name__)

RATING_COMMENT_ALTCHA_CONFIG_KEY = "ckanext.artesp.rating.altcha_hmac_secret"
RATING_COMMENT_ALTCHA_ALGORITHM = "PBKDF2/SHA-256"
RATING_COMMENT_ALTCHA_COST = 1
RATING_COMMENT_ALTCHA_EXPIRES_MINUTES = 10


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


def sitemap():
    from ckan.common import config
    site_url = config.get('ckan.site_url', '').rstrip('/')
    urls = [{'loc': site_url + '/', 'lastmod': '', 'changefreq': 'daily', 'priority': '1.0'}]

    try:
        result = toolkit.get_action('package_search')(
            {}, {'q': '*:*', 'rows': 1000, 'include_private': False}
        )
        for pkg in result.get('results', []):
            urls.append({
                'loc': site_url + toolkit.url_for('dataset.read', id=pkg['name']),
                'lastmod': (pkg.get('metadata_modified') or '')[:10],
                'changefreq': 'weekly',
                'priority': '0.8',
            })
    except Exception:
        log.exception('sitemap: package_search failed')

    try:
        org_names = toolkit.get_action('organization_list')({}, {'all_fields': False})
        for name in org_names:
            urls.append({
                'loc': site_url + toolkit.url_for('organization.read', id=name),
                'lastmod': '',
                'changefreq': 'monthly',
                'priority': '0.6',
            })
    except Exception:
        log.exception('sitemap: organization_list failed')

    xml = render_template('home/sitemap.xml', urls=urls)
    return Response(xml, mimetype='application/xml')


artesp_theme.add_url_rule('/about-ckan', view_func=about_ckan)
artesp_theme.add_url_rule('/terms', view_func=terms)
artesp_theme.add_url_rule('/privacy', view_func=privacy)
artesp_theme.add_url_rule('/harvesting', view_func=harvesting)
artesp_theme.add_url_rule('/estatisticas', view_func=statistics)
artesp_theme.add_url_rule('/sitemap.xml', view_func=sitemap)


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
                    audit_capture.record_auth_event(
                        event_action="login_failure",
                        success=False,
                        auth_provider="ldap",
                        actor_name=login,
                        actor_identifier=login,
                        request_path="/user/verify",
                        details={"reason": "UserConflictError"},
                    )
                    return _helpers.login_failed(error=str(e))
                except toolkit.ValidationError as e:
                    audit_capture.record_auth_event(
                        event_action="login_failure",
                        success=False,
                        auth_provider="ldap",
                        actor_name=login,
                        actor_identifier=login,
                        request_path="/user/verify",
                        details={"reason": "ValidationError", "error": str(e.error_dict)},
                    )
                    return _helpers.login_failed(
                        error=toolkit._('Conflito de conta. Por favor, entre em contato com o administrador do site.')
                    )
                audit_capture.record_auth_event(
                    event_action="login_success",
                    success=True,
                    auth_provider="ldap",
                    actor_name=user_name,
                    actor_identifier=user_name,
                    request_path="/user/verify",
                )
                return _helpers.login_success(user_name, came_from=came_from)
            elif ldap_user_dict:
                if toolkit.config['ckanext.ldap.ckan_fallback']:
                    exists = _helpers.ckan_user_exists(login)
                    if exists['exists'] and not exists['is_ldap']:
                        audit_capture.record_auth_event(
                            event_action="login_failure",
                            success=False,
                            auth_provider="ldap",
                            actor_name=login,
                            actor_identifier=login,
                            request_path="/user/verify",
                            details={"reason": "username_conflict"},
                        )
                        return _helpers.login_failed(
                            error=toolkit._(
                                'Conflito de nome de usuário. Por favor, entre em contato com o administrador do site.'
                            )
                        )
                audit_capture.record_auth_event(
                    event_action="login_failure",
                    success=False,
                    auth_provider="ldap",
                    actor_name=login,
                    actor_identifier=login,
                    request_path="/user/verify",
                    details={"reason": "invalid_password"},
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
                    audit_capture.record_auth_event(
                        event_action="login_success",
                        success=True,
                        auth_provider="local",
                        actor_name=user.name,
                        actor_identifier=user.name,
                        request_path="/user/verify",
                    )
                    return _helpers.login_success(user.name, came_from=came_from)
                audit_capture.record_auth_event(
                    event_action="login_failure",
                    success=False,
                    auth_provider="local",
                    actor_name=login,
                    actor_identifier=login,
                    request_path="/user/verify",
                    details={"reason": "fallback_invalid_credentials"},
                )
                return _helpers.login_failed(
                    error=toolkit._('Nome de usuário ou senha incorretos.') + ' [LDAP2]'
                )
            else:
                audit_capture.record_auth_event(
                    event_action="login_failure",
                    success=False,
                    auth_provider="ldap",
                    actor_name=login,
                    actor_identifier=login,
                    request_path="/user/verify",
                    details={"reason": "user_not_found"},
                )
                return _helpers.login_failed(
                    error=toolkit._('Nome de usuário ou senha incorretos.') + ' [LDAP3]'
                )

        audit_capture.record_auth_event(
            event_action="login_failure",
            success=False,
            auth_provider="ldap",
            actor_name=params.get("login"),
            actor_identifier=params.get("login"),
            request_path="/user/verify",
            details={"reason": "missing_credentials"},
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


def audit_admin():
    user = model.User.get(g.user) if g.user else None
    if not user or not getattr(user, "sysadmin", False):
        abort(403)

    filters = {
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
        "scope": request.args.get("scope", "all"),
        "action": request.args.get("action", ""),
        "provider": request.args.get("provider", "all"),
        "channel": request.args.get("channel", "all"),
        "user": request.args.get("user", ""),
        "ip": request.args.get("ip", ""),
        "object": request.args.get("object", ""),
        "sort_by": request.args.get("sort_by", "occurred_at"),
        "sort_dir": request.args.get("sort_dir", "desc"),
        "page": request.args.get("page", "1"),
    }
    result = audit_query.search_audit_events(filters)
    return render_template(
        "admin/audit.html",
        **result,
        scope_choices=audit_query.SCOPE_CHOICES,
        action_choices=audit_query.ACTION_CHOICES,
        provider_choices=audit_query.PROVIDER_CHOICES,
        channel_choices=audit_query.CHANNEL_CHOICES,
    )


artesp_theme.add_url_rule(
    "/admin/audit",
    endpoint="audit_admin",
    view_func=audit_admin,
    methods=["GET"],
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


def _get_rating_comment_altcha_secret() -> str:
    return (toolkit.config.get(RATING_COMMENT_ALTCHA_CONFIG_KEY) or "").strip()


def _validate_rating_comment_captcha():
    secret = _get_rating_comment_altcha_secret()
    if not secret:
        raise toolkit.ValidationError({"captcha": [toolkit._("Captcha not configured")]})

    payload = (request.form.get("altcha") or "").strip()
    if not payload:
        raise toolkit.ValidationError(
            {"captcha": [toolkit._("Captcha verification is required to submit a comment.")]}
        )

    try:
        from altcha import verify_solution
    except ImportError as exc:
        log.exception("ALTCHA library unavailable for dataset comment verification")
        raise toolkit.ValidationError(
            {"captcha": [toolkit._("Captcha validation failed. Please try again.")]}
        ) from exc

    result = verify_solution(payload, secret)
    verified = getattr(result, "verified", None)
    if verified is None and isinstance(result, tuple):
        verified = bool(result[0])
    if verified is None:
        verified = bool(result)

    if verified:
        return

    log.info(
        "rating_comment_altcha_failed expired=%s invalid_signature=%s invalid_solution=%s error=%s",
        getattr(result, "expired", None),
        getattr(result, "invalid_signature", None),
        getattr(result, "invalid_solution", None),
        getattr(result, "error", None),
    )
    raise toolkit.ValidationError(
        {"captcha": [toolkit._("Captcha validation failed. Please try again.")]}
    )


def rating_comment_captcha_challenge():
    from ckan.common import current_user

    if not getattr(current_user, "is_authenticated", False):
        abort(403)

    secret = _get_rating_comment_altcha_secret()
    if not secret:
        abort(404)

    try:
        from altcha import create_challenge
    except ImportError:
        log.exception("ALTCHA library unavailable for challenge generation")
        abort(503)

    challenge = create_challenge(
        algorithm=RATING_COMMENT_ALTCHA_ALGORITHM,
        cost=RATING_COMMENT_ALTCHA_COST,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=RATING_COMMENT_ALTCHA_EXPIRES_MINUTES),
        hmac_secret=secret,
    )
    response = jsonify(challenge.to_dict())
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


def rating_submit(package_name: str):
    from ckan.common import current_user
    from ckan.lib.helpers import flash_error as _flash_error, flash_success as _flash_success
    from ckanext.artesp_theme.logic.rating import RATING_CRITERIA

    if not getattr(current_user, "is_authenticated", False):
        return redirect_to(toolkit.url_for("user.login"))

    comment = request.form.get("comment", "")
    comment_requires_captcha = bool(comment.strip())

    if comment_requires_captcha:
        try:
            _validate_rating_comment_captcha()
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
                "comment": comment,
            },
        )
        _flash_success(toolkit._("Sua avaliação foi enviada com sucesso."))
        return redirect_to(
            toolkit.url_for("dataset.read", id=package_name, rating_submitted=1)
        )
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


def rating_admin_index(id: str):
    import urllib.parse
    from ckan.common import current_user
    from ckanext.artesp_theme.logic import rating_admin
    from ckanext.artesp_theme.model import RATING_STATUSES, RATING_STATUS_LABELS

    if not getattr(current_user, "is_authenticated", False):
        return redirect_to(toolkit.url_for("user.login"))
    if current_user.name != id:
        abort(403)

    user = model.User.get(current_user.name)
    if not user or auth_helpers.is_external_user(user):
        abort(403)

    _PER_PAGE = 20
    page = max(1, int((request.args.get("page") or 1)))

    status_filters = request.args.getlist("status") or None
    rating_filters_raw = request.args.getlist("rating")
    rating_filters = [int(r) for r in rating_filters_raw if r.isdigit()] or None
    date_from = (request.args.get("date_from") or "").strip() or None
    date_to = (request.args.get("date_to") or "").strip() or None
    dataset_filter = (request.args.get("dataset") or "").strip() or None
    sort_by = (request.args.get("sort_by") or "").strip() or None
    sort_dir = request.args.get("sort_dir", "desc")
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    all_ratings = rating_admin.get_ratings_for_user(user.id)
    status_counts = {"all": len(all_ratings)}
    for status in RATING_STATUSES:
        status_counts[status] = sum(1 for r in all_ratings if r["status"] == status)

    filtered_ratings = rating_admin.get_ratings_for_user(
        user.id,
        status_filters=status_filters,
        rating_filters=rating_filters,
        date_from=date_from,
        date_to=date_to,
        dataset_filter=dataset_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    total_filtered = len(filtered_ratings)
    total_pages = max(1, (total_filtered + _PER_PAGE - 1) // _PER_PAGE)
    offset = (page - 1) * _PER_PAGE
    ratings = filtered_ratings[offset: offset + _PER_PAGE]

    editable_packages = rating_admin.get_editable_packages_for_user(user.id)

    filter_params = []
    for s in (status_filters or []):
        filter_params.append(("status", s))
    for r in (rating_filters or []):
        filter_params.append(("rating", str(r)))
    if date_from:
        filter_params.append(("date_from", date_from))
    if date_to:
        filter_params.append(("date_to", date_to))
    if dataset_filter:
        filter_params.append(("dataset", dataset_filter))
    if sort_by:
        filter_params.append(("sort_by", sort_by))
        filter_params.append(("sort_dir", sort_dir))
    filter_qs = urllib.parse.urlencode(filter_params)

    return render_template(
        "user/rating_admin_index.html",
        user=user,
        ratings=ratings,
        current_status_filters=status_filters or [],
        current_rating_filters=[str(r) for r in (rating_filters or [])],
        current_date_from=date_from or "",
        current_date_to=date_to or "",
        current_dataset=dataset_filter or "",
        current_sort_by=sort_by or "",
        current_sort_dir=sort_dir,
        status_counts=status_counts,
        status_choices=[
            {"value": s, "label": RATING_STATUS_LABELS.get(s, s)}
            for s in RATING_STATUSES
        ],
        filter_qs=filter_qs,
        page=page,
        total_pages=total_pages,
        editable_packages=editable_packages,
    )


def rating_admin_list(package_name: str):
    from ckan.common import current_user
    from ckanext.artesp_theme.logic import rating_admin
    from ckanext.artesp_theme.model import RATING_STATUSES, RATING_STATUS_LABELS

    package = model.Package.get(package_name)
    if package is None:
        abort(404)

    user = model.User.get(current_user.name) if getattr(current_user, "is_authenticated", False) else None
    if not auth_helpers.user_can_edit_package(package, user):
        abort(403)

    status_filter = (request.args.get("status") or "").strip() or None
    all_ratings = rating_admin.get_ratings_for_package(package.id)
    ratings = rating_admin.get_ratings_for_package(package.id, status_filter=status_filter)
    status_counts = {"all": len(all_ratings)}
    for status in RATING_STATUSES:
        status_counts[status] = sum(1 for r in all_ratings if r["status"] == status)

    return render_template(
        "package/rating_admin_list.html",
        pkg=package,
        ratings=ratings,
        current_status=status_filter or "all",
        status_counts=status_counts,
        status_choices=[
            {"value": "all", "label": toolkit._("Todos")},
            *[
                {"value": status, "label": RATING_STATUS_LABELS.get(status, status)}
                for status in RATING_STATUSES
            ],
        ],
    )


def rating_admin_detail(package_name: str, rating_id: str):
    from ckan.common import current_user
    from ckanext.artesp_theme.logic import rating_admin
    from ckanext.artesp_theme.model import RATING_STATUSES, RATING_STATUS_LABELS

    package = model.Package.get(package_name)
    if package is None:
        abort(404)

    user = model.User.get(current_user.name) if getattr(current_user, "is_authenticated", False) else None
    if not auth_helpers.user_can_edit_package(package, user):
        abort(403)

    detail = rating_admin.get_rating_detail(rating_id)
    if detail["rating"]["package_id"] != package.id:
        abort(404)

    return render_template(
        "package/rating_admin_detail.html",
        pkg=package,
        rating=detail["rating"],
        actions=detail["actions"],
        status_choices=[
            {"value": status, "label": RATING_STATUS_LABELS.get(status, status)}
            for status in RATING_STATUSES
        ],
    )


def rating_admin_action(package_name: str, rating_id: str):
    from ckan.common import current_user
    from ckanext.artesp_theme.logic import rating_admin

    package = model.Package.get(package_name)
    if package is None:
        abort(404)

    user = model.User.get(current_user.name) if getattr(current_user, "is_authenticated", False) else None
    if not auth_helpers.user_can_edit_package(package, user):
        abort(403)

    detail = rating_admin.get_rating_detail(rating_id)
    if detail["rating"]["package_id"] != package.id:
        abort(404)

    rating_admin.create_rating_action(
        rating_id=rating_id,
        actor_id=user.id,
        new_status=(request.form.get("new_status") or "").strip(),
        note=(request.form.get("note") or "").strip(),
        send_email=bool((request.form.get("send_email") or "").strip()),
    )
    return redirect_to(
        toolkit.url_for(
            "artesp_theme.rating_admin_detail",
            package_name=package_name,
            rating_id=rating_id,
        )
    )


artesp_theme.add_url_rule(
    "/user/<id>/rating-admin",
    endpoint="rating_admin_index",
    view_func=rating_admin_index,
    methods=["GET"],
)

artesp_theme.add_url_rule(
    "/dataset/<package_name>/rating-admin",
    endpoint="rating_admin_list",
    view_func=rating_admin_list,
    methods=["GET"],
)

artesp_theme.add_url_rule(
    "/dataset/<package_name>/rating-admin/<rating_id>",
    endpoint="rating_admin_detail",
    view_func=rating_admin_detail,
    methods=["GET"],
)

artesp_theme.add_url_rule(
    "/dataset/<package_name>/rating-admin/<rating_id>/action",
    endpoint="rating_admin_action",
    view_func=rating_admin_action,
    methods=["POST"],
)


artesp_theme.add_url_rule(
    "/dataset/<package_name>/rate",
    endpoint="rating_submit",
    view_func=rating_submit,
    methods=["POST"],
)

artesp_theme.add_url_rule(
    "/dataset-rating/comment-captcha/challenge",
    endpoint="rating_comment_captcha_challenge",
    view_func=rating_comment_captcha_challenge,
    methods=["GET"],
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
