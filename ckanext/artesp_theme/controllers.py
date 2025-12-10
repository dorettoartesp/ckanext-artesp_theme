from flask import Blueprint, render_template, request, g
from ckan.plugins import toolkit
from ckan.lib.helpers import flash_error, redirect_to
from ckan.lib.pagination import Page
import logging

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


artesp_theme.add_url_rule('/about-ckan', view_func=about_ckan)
artesp_theme.add_url_rule('/terms', view_func=terms)
artesp_theme.add_url_rule('/privacy', view_func=privacy)
artesp_theme.add_url_rule('/harvesting', view_func=harvesting)


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

        # Apply format filter
        if format_filter:
            resources_list = [r for r in resources_list if r.get('format') == format_filter]

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

        # Enrich resources with package (dataset) information
        for resource in resources:
            try:
                package = toolkit.get_action('package_show')(None, {'id': resource['package_id']})
                resource['package_name'] = package.get('title') or package.get('name')
            except Exception as pkg_error:
                log.warning(f"Could not fetch package info for {resource['package_id']}: {pkg_error}")
                resource['package_name'] = None

        # Calculate format facets from ALL results (before pagination)
        format_facets = {}
        for res in resources_list:
            fmt = res.get('format')
            if fmt:
                format_facets[fmt] = format_facets.get(fmt, 0) + 1

    except Exception as e:
        log.error(f"Resource Search - Error: {e}")
        resources = []
        count = 0
        format_facets = {}

    def pager_url(q=None, page=None, sort=None):
        params = {}
        if q:
            params['q'] = q
        if page:
            params['page'] = page
        if sort:
            params['sort'] = sort
        return toolkit.url_for('artesp_theme.resource_search', **params)

    page_obj = Page(
        collection=resources,
        page=page,
        items_per_page=limit,
        item_count=count,
        url=lambda **kwargs: pager_url(q=kwargs.get('q', q), page=kwargs.get('page'), sort=kwargs.get('sort', sort)),
    )

    # Sort facets by count (descending)
    sorted_facets = sorted(format_facets.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        'resource/search.html',
        q=q,
        page=page_obj,
        resources=resources,
        count=count,
        sort_by_selected=sort,
        format_facets=sorted_facets,
        format_filter=format_filter
    )


artesp_theme.add_url_rule('/resources', view_func=resource_search)

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
