from ckan.plugins import toolkit
import datetime


def artesp_theme_hello():
    return "Hello, artesp_theme!"


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
        # Log the error
        toolkit.get_logger().error(f"Error counting resources: {str(e)}")
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
        # Log the error
        toolkit.get_logger().error(f"Error getting latest datasets: {str(e)}")
        # Return empty list if there's an error
        return []


def get_organization_count():
    """Return the number of organizations in the system."""
    try:
        # Use organization_list to get all organizations
        orgs = toolkit.get_action('organization_list')({}, {'all_fields': False})
        return len(orgs)
    except Exception as e:
        # Log the error
        toolkit.get_logger().error(f"Error counting organizations: {str(e)}")
        # Return 0 if there's an error
        return 0


def get_year():
    """Return the current year."""
    return datetime.datetime.now().year


def get_helpers():
    return {
        "artesp_theme_hello": artesp_theme_hello,
        "get_package_count": get_package_count,
        "get_resource_count": get_resource_count,
        "get_latest_datasets": get_latest_datasets,
        "get_organization_count": get_organization_count,
        "get_year": get_year,
    }
