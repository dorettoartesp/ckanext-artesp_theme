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
    sort = request.args.get('sort', 'created desc')
    format_filter = request.args.get('format', None)

    # Construct a Solr query for resources
    # resource_search expects 'query' parameter in the format 'field:term'
    log.info(f"Resource Search - User Query: {q}, Format Filter: {format_filter}, Sort: {sort}")

    try:
        if q:
            # Check if the query already contains field syntax (e.g., "format:PDF" or "name:test")
            if ':' in q:
                # User is using advanced syntax, pass it through
                data_dict = {
                    'query': q,
                    'limit': limit,
                    'offset': offset,
                    'order_by': sort.split()[0] if sort else 'created'
                }
                results = toolkit.get_action('resource_search')(None, data_dict)
                count = results['count']
                resources = results['results']
            else:
                # Search across multiple fields and combine results
                # We need to do separate searches because resource_search ANDs multiple queries
                search_term = q.strip()
                all_resources = {}  # Use dict to avoid duplicates, keyed by resource id

                # Search in each field
                for field in ['name', 'description', 'format']:
                    try:
                        field_results = toolkit.get_action('resource_search')(None, {
                            'query': f'{field}:{search_term}',
                            'limit': 1000,  # Get all matches for combining
                            'order_by': sort.split()[0] if sort else 'created'
                        })
                        for resource in field_results.get('results', []):
                            all_resources[resource['id']] = resource
                    except Exception as field_error:
                        log.warning(f"Resource Search - Error searching {field}: {field_error}")

                # Convert back to list
                resources_list = list(all_resources.values())

                # Apply format filter if present
                if format_filter:
                    resources_list = [r for r in resources_list if r.get('format') == format_filter]

                count = len(resources_list)

                # Apply pagination manually
                start_idx = offset
                end_idx = offset + limit
                resources = resources_list[start_idx:end_idx]
        else:
            # Empty query - search in name field for anything
            data_dict = {
                'query': 'name:',
                'limit': 1000 if format_filter else limit,
                'offset': 0 if format_filter else offset,
                'order_by': sort.split()[0] if sort else 'created'
            }
            results = toolkit.get_action('resource_search')(None, data_dict)
            resources_list = results['results']

            # Apply format filter if present
            if format_filter:
                resources_list = [r for r in resources_list if r.get('format') == format_filter]

            count = len(resources_list)

            # Apply pagination if format filter was used
            if format_filter:
                start_idx = offset
                end_idx = offset + limit
                resources = resources_list[start_idx:end_idx]
            else:
                count = results['count']
                resources = resources_list

        log.info(f"Resource Search - Found {count} total results, returning {len(resources)} resources")

        # Enrich resources with package (dataset) information
        for resource in resources:
            try:
                package = toolkit.get_action('package_show')(None, {'id': resource['package_id']})
                resource['package_name'] = package.get('title') or package.get('name')
            except Exception as pkg_error:
                log.warning(f"Could not fetch package info for {resource['package_id']}: {pkg_error}")
                resource['package_name'] = None

        # Calculate format facets from ALL results (not just current page)
        format_facets = {}
        try:
            # Always get all results to calculate accurate facets
            if q and ':' not in q:
                # Multi-field search - need to combine results
                all_results_set = {}
                for field in ['name', 'description', 'format']:
                    try:
                        field_results = toolkit.get_action('resource_search')(None, {
                            'query': f'{field}:{q.strip()}',
                            'limit': 1000,
                            'order_by': 'created'
                        })
                        for res in field_results.get('results', []):
                            all_results_set[res['id']] = res
                    except:
                        pass
                all_results = list(all_results_set.values())
            else:
                # Simple search or no query
                facet_query = q if (q and ':' in q) else 'name:'
                all_results_data = toolkit.get_action('resource_search')(None, {
                    'query': facet_query,
                    'limit': 1000,
                    'order_by': 'created'
                })
                all_results = all_results_data.get('results', [])

            # Apply format filter if present for accurate facet counts
            if format_filter:
                # When filtering, show all available formats but highlight the filtered one
                for res in all_results:
                    fmt = res.get('format')
                    if fmt:
                        format_facets[fmt] = format_facets.get(fmt, 0) + 1
            else:
                # No filter, count all formats
                for res in all_results:
                    fmt = res.get('format')
                    if fmt:
                        format_facets[fmt] = format_facets.get(fmt, 0) + 1
        except Exception as e:
            log.error(f"Error calculating format facets: {e}")
            pass

    except Exception as e:
        log.error(f"Resource Search - Error: {e}")
        resources = []
        count = 0
        format_facets = {}

    def pager_url(q=None, page=None):
        params = {}
        if q:
            params['q'] = q
        if page:
            params['page'] = page
        return toolkit.url_for('artesp_theme.resource_search', **params)

    page_obj = Page(
        collection=resources,
        page=page,
        items_per_page=limit,
        item_count=count,
        url=pager_url,
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
