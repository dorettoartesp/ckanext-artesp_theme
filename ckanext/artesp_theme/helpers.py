import datetime
import logging
import re
from markupsafe import Markup

from sqlalchemy import desc
from ckan.plugins import toolkit
from ckan.model.resource import Resource
from ckan.model.package import Package
from ckan.model.meta import Session

log = logging.getLogger(__name__)

def artesp_theme_hello():
    return "Hello, artesp_theme!"

def safe_html(html_string):
    """
    Safely render HTML content that might have been double-encoded.
    This is useful for fixing Font Awesome icons that are being double-encoded.
    """
    if not html_string:
        return html_string

    # If the string contains encoded HTML tags (common pattern for double-encoded FA icons)
    if '&amp;lt;i class=' in html_string:
        # First decode the double-encoded HTML
        decoded = html_string.replace('&amp;lt;', '<').replace('&amp;gt;', '>')
        decoded = decoded.replace('&amp;quot;', '"').replace('&amp;#39;', "'")
        # Return as a safe Markup object to prevent further escaping
        return Markup(decoded)

    # If it's already a Markup object or doesn't need fixing, return as is
    return html_string


def fix_fontawesome_icon(icon_name):
    """
    Create a Font Awesome icon that won't be double-encoded.

    Args:
        icon_name: The name of the Font Awesome icon (without the 'fa-' prefix)

    Returns:
        A Markup object containing the Font Awesome icon HTML
    """
    return Markup(f'<i class="fa fa-{icon_name}"></i> ')


def get_package_count():
    """Return the number of packages (datasets) in the system."""
    try:
        # Use package_search to get the total count
        result = toolkit.get_action('package_search')({}, {'rows': 0})
        return result.get('count', 0)
    except Exception:
        # Return 0 if there's an error
        return 0


def get_resource_count():
    """Return the number of resources in the system."""
    try:
        # Get all packages
        packages = toolkit.get_action('package_search')({}, {'rows': 1000})

        # Count resources in each package
        resource_count = 0
        for package in packages.get('results', []):
            resource_count += len(package.get('resources', []))

        return resource_count
    except Exception as e:
        log.error(f"Error counting resources: {str(e)}")
        # Return 0 if there's an error
        return 0


def get_latest_datasets(limit=3):
    """Return a list of the latest datasets."""
    try:
        # Get the latest datasets
        datasets = toolkit.get_action('package_search')(
            {},
            {
                'rows': limit,
                'sort': 'metadata_created desc',
                'include_private': False
            }
        )
        return datasets.get('results', [])
    except Exception as e:
        log.error(f"Error getting latest datasets: {str(e)}")
        # Return empty list if there's an error
        return []


def get_organization_count():
    """Return the number of organizations in the system."""
    try:
        # Use organization_list to get all organizations
        orgs = toolkit.get_action('organization_list')({}, {'all_fields': False})
        return len(orgs)
    except Exception as e:
        log.error(f"Error counting organizations: {str(e)}")
        # Return 0 if there's an error
        return 0

def get_group_count():
    """Return the number of groups in the system."""
    try:
        # Use group_list to get all groups
        groups = toolkit.get_action('group_list')({}, {'all_fields': False})
        return len(groups)
    except Exception as e:
        log.error(f"Error counting groups: {str(e)}")
        # Return 0 if there's an error
        return 0

def get_year():
    """Return the current year."""
    return datetime.datetime.now().year

def get_latest_resources(limit=5, org_id=None, dataset_id=None):
    context = {'session': Session}
    results = []

    try:
        # Start base query
        query = Session.query(Resource).filter(Resource.state == 'active')

        # Filter by dataset or organization if provided
        if dataset_id:
            query = query.filter(Resource.package_id == dataset_id)
        elif org_id:
            query = query.join(Package).filter(Package.owner_org == org_id)

        # Order by last_modified descending and apply limit
        resources = query.order_by(desc(Resource.last_modified)).limit(limit).all()
        for res in resources:
            try:
                # Get the full dataset dictionary
                dataset_dict = toolkit.get_action('package_show')(context, {'id': res.package_id})

                results.append({
                    'resource': res,
                    'dataset': dataset_dict,
                    'parent_dataset_title': dataset_dict.get('title')  # Add title as separate key
                })

            except Exception as e:
                log.warning(f"[ckanext-artesp_theme] Failed to fetch dataset for resource {res.id}: {str(e)}")

    except Exception as e:
        log.error("[ckanext-artesp_theme] Failed to get latest resources", exc_info=True)

    return results

def get_featured_groups(limit=4):
    """
    Return a list of featured groups.
    Fetches a list of groups with their details, including title, name, image URL, and dataset count.
    Currently, it takes the first 'limit' groups returned by the 'group_list' action.
    This could be extended to sort by package_count or a specific 'featured' tag if needed.
    """
    try:
        group_list_params = {
            'all_fields': True,        # Fetches most group attributes
            'include_datasets': True,  # Adds 'package_count' and 'display_name'
            # Example: 'sort': 'name asc',
            # To sort by dataset count (popularity), you might need to fetch all,
            # sort in Python, then slice. For now, we take the default order.
        }
        groups = toolkit.get_action('group_list')({}, group_list_params)

        # If sorting is desired, e.g., by package_count:
        # groups.sort(key=lambda g: g.get('package_count', 0), reverse=True)

        return groups[:limit]

    except toolkit.ObjectNotFound:
        log.info("[ckanext-artesp_theme] No groups found to feature.")
        return []
    except Exception as e:
        log.error(f"[ckanext-artesp_theme] Error getting featured groups: {str(e)}", exc_info=True)
        return []


def get_helpers():
    return {
        "artesp_theme_hello": artesp_theme_hello,
        "get_package_count": get_package_count,
        "get_resource_count": get_resource_count,
        "get_latest_datasets": get_latest_datasets,
        "get_latest_resources": get_latest_resources,
        "get_organization_count": get_organization_count,
        "get_group_count": get_group_count,
        "get_featured_groups": get_featured_groups,
        "get_year": get_year,
        "safe_html": safe_html,
        "fix_fontawesome_icon": fix_fontawesome_icon,
    }
