import datetime
import logging
import time
from markupsafe import Markup

from sqlalchemy import desc
from ckan.common import session as ckan_session
from ckan.plugins import toolkit
from ckan.model.resource import Resource
from ckan.model.package import Package
from ckan.model.meta import Session

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.logic import dashboard_statistics

log = logging.getLogger(__name__)

_HELPERS_CACHE: dict = {}
_HELPERS_CACHE_TTL = 300  # segundos

RATING_COMMENT_ALTCHA_CONFIG_KEY = "ckanext.artesp.rating.altcha_hmac_secret"
RATING_COMMENT_ALTCHA_SCRIPT_URL = (
    "https://cdn.jsdelivr.net/npm/altcha@3.0.4/dist/main/altcha.i18n.min.js"
)
RATING_COMMENT_ALTCHA_STYLESHEET_URL = (
    "https://cdn.jsdelivr.net/npm/altcha@3.0.4/dist/external/altcha.min.css"
)

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
        return Session.query(Resource).filter(Resource.state == 'active').count()
    except Exception as e:
        log.error(f"Error counting resources: {str(e)}")
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
    
def get_featured_datasets(limit=3):
    """
    Return a list of datasets, with featured datasets appearing first.

    The sorting order is:
    1. Datasets with the custom field 'featuredDataset' set to 'true'.
    2. All other datasets.
    Within each group, datasets are sorted by most recently modified.
    """
    try:
        # Search for all datasets, sorting by featured status and then modification date
        search_params = {
            'sort': 'featuredDataset desc, metadata_modified desc',
            'rows': limit,
            'include_private': False
        }
        datasets = toolkit.get_action('package_search')({}, search_params)
        return datasets.get('results', [])
    except Exception as e:
        log.error(f"Error getting featured datasets: {str(e)}")
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
    results = []
    try:
        query = (
            Session.query(Resource, Package.title, Package.name)
            .join(Package, Resource.package_id == Package.id)
            .filter(Resource.state == 'active')
            .filter(Package.state == 'active')
            .filter(Package.private.is_(False))
        )
        if dataset_id:
            query = query.filter(Resource.package_id == dataset_id)
        elif org_id:
            query = query.filter(Package.owner_org == org_id)
        rows = query.order_by(desc(Resource.metadata_modified)).limit(limit).all()
        for res, pkg_title, pkg_name in rows:
            results.append({
                'resource': res,
                'dataset': {'title': pkg_title, 'name': pkg_name},
                'parent_dataset_title': pkg_title,
            })
    except Exception as e:
        log.error("[ckanext-artesp_theme] Failed to get latest resources", exc_info=True)
    return results

def get_featured_groups(limit=4):
    cache_key = ('featured_groups', limit)
    now = time.monotonic()
    cached = _HELPERS_CACHE.get(cache_key)
    if cached and cached['expires_at'] > now:
        return cached['data']

    result = []
    try:
        groups = toolkit.get_action('group_list')({}, {
            'all_fields': True,
            'include_datasets': True,
        })
        groups.sort(key=lambda g: g.get('package_count', 0), reverse=True)
        result = groups[:limit]
    except toolkit.ObjectNotFound:
        log.info("[ckanext-artesp_theme] No groups found to feature.")
    except Exception as e:
        log.error(f"[ckanext-artesp_theme] Error getting featured groups: {str(e)}", exc_info=True)

    _HELPERS_CACHE[cache_key] = {'data': result, 'expires_at': now + _HELPERS_CACHE_TTL}
    return result


def clear_dashboard_statistics_cache():
    dashboard_statistics.clear_dashboard_statistics_cache()


def get_dashboard_statistics(data_dict=None):
    return dashboard_statistics.get_dashboard_statistics(data_dict or {})


def artesp_ldap_enabled():
    """Check if LDAP authentication is enabled."""
    return bool(toolkit.config.get('ckanext.ldap.uri', ''))


def artesp_govbr_login_enabled():
    enabled = toolkit.asbool(toolkit.config.get("ckanext.artesp.govbr.enabled", False))
    client_id = toolkit.config.get("ckanext.artesp.govbr.client_id", "")
    return enabled and bool(client_id.strip())


def get_artesp_organization():
    org = auth_helpers.get_artesp_org()
    if not org:
        return None

    return {
        "id": org.id,
        "name": org.name,
        "title": org.title,
        "display_name": auth_helpers.get_artesp_org_display_name(),
    }


def get_default_dataset_collaborator_capacity():
    return auth_helpers.get_default_dataset_collaborator_capacity()


def artesp_is_external_user():
    user = getattr(toolkit.c, "userobj", None)
    if user is None:
        username = getattr(toolkit.c, "user", None)
        if username:
            import ckan.model as model
            user = model.User.get(username)
    elif not getattr(user, "plugin_extras", None):
        username = getattr(user, "name", None) or getattr(toolkit.c, "user", None)
        if username:
            import ckan.model as model
            db_user = model.User.get(username)
            if db_user is not None:
                user = db_user

    return auth_helpers.is_external_user(user)


def artesp_auth_provider():
    """Return the auth provider for the current session, if any."""
    return ckan_session.get("artesp_auth_provider")


def artesp_is_user_external(user_dict):
    """Verifica se um usuário (dict) é do tipo externo (GovBR).

    user_show só retorna plugin_extras para sysadmin; busca no modelo como fallback.
    """
    if not user_dict:
        return False
    plugin_extras = user_dict.get("plugin_extras")
    if not plugin_extras:
        try:
            import ckan.model as model
            user_obj = model.User.get(user_dict.get("name") or user_dict.get("id", ""))
            plugin_extras = (user_obj.plugin_extras if user_obj else None) or {}
        except Exception:
            plugin_extras = {}
    return (plugin_extras or {}).get("artesp", {}).get("user_type") == "external"


def get_dataset_rating_summary(package_id: str) -> dict:
    import ckan.plugins.toolkit as tk
    try:
        return tk.get_action("dataset_rating_summary")({}, {"package_id": package_id})
    except Exception:
        return {
            "package_id": package_id,
            "overall": {"count": 0, "average": None, "criteria": {}},
        }


def get_current_user_dataset_rating(package_id: str) -> dict | None:
    import ckan.plugins.toolkit as tk
    from ckan.common import current_user
    if not getattr(current_user, "is_authenticated", False):
        return None
    try:
        return tk.get_action("dataset_rating_show")(
            {"user": current_user.name}, {"package_id": package_id}
        )
    except Exception:
        return None


def rating_comment_captcha_enabled() -> bool:
    return bool((toolkit.config.get(RATING_COMMENT_ALTCHA_CONFIG_KEY) or "").strip())


def get_rating_comment_captcha_challenge_url() -> str | None:
    if not rating_comment_captcha_enabled():
        return None
    return toolkit.url_for("artesp_theme.rating_comment_captcha_challenge")


def get_rating_comment_captcha_script_url() -> str:
    return RATING_COMMENT_ALTCHA_SCRIPT_URL


def get_rating_comment_captcha_stylesheet_url() -> str:
    return RATING_COMMENT_ALTCHA_STYLESHEET_URL


# ── SEO helpers ─────────────────────────────────────────────────────────────

from flask import request as flask_request


def seo_canonical_url():
    """Returns the canonical URL of the current page without query parameters."""
    return flask_request.base_url


def seo_meta_description(pkg_dict=None, org_dict=None, group_dict=None, length=155):
    """Returns a truncated plain-text description for <meta name="description">."""
    if pkg_dict:
        raw = toolkit.h.get_translated(pkg_dict, 'notes') or ''
    elif org_dict:
        raw = toolkit.h.get_translated(org_dict, 'description') or ''
    elif group_dict:
        raw = toolkit.h.get_translated(group_dict, 'description') or ''
    else:
        raw = toolkit.config.get('ckan.site_description', '')
    return toolkit.h.markdown_extract(raw, extract_length=length)


def seo_jsonld_dataset(pkg_dict):
    """Returns a Schema.org Dataset dict for use in a JSON-LD script tag."""
    site_url = toolkit.config.get('ckan.site_url', '').rstrip('/')
    pkg_url = site_url + toolkit.url_for('dataset.read', id=pkg_dict.get('name', ''))

    description = toolkit.h.markdown_extract(
        toolkit.h.get_translated(pkg_dict, 'notes') or '', extract_length=500
    )

    keywords = [tag['name'] for tag in pkg_dict.get('tags', [])]

    distribution = []
    for res in pkg_dict.get('resources', []):
        distribution.append({
            '@type': 'DataDownload',
            'name': res.get('name') or res.get('id', ''),
            'contentUrl': res.get('url', ''),
            'encodingFormat': res.get('mimetype') or res.get('format', ''),
        })

    jsonld = {
        '@context': 'https://schema.org',
        '@type': 'Dataset',
        'name': toolkit.h.get_translated(pkg_dict, 'title') or pkg_dict.get('name', ''),
        'description': description,
        'url': pkg_url,
        'keywords': keywords,
        'datePublished': (pkg_dict.get('metadata_created') or '')[:10],
        'dateModified': (pkg_dict.get('metadata_modified') or '')[:10],
    }

    if pkg_dict.get('license_url'):
        jsonld['license'] = pkg_dict['license_url']
    elif pkg_dict.get('license_title'):
        jsonld['license'] = pkg_dict['license_title']

    if pkg_dict.get('organization'):
        org = pkg_dict['organization']
        jsonld['creator'] = {
            '@type': 'Organization',
            'name': org.get('title') or org.get('name', ''),
        }

    if distribution:
        jsonld['distribution'] = distribution

    return jsonld


def seo_jsonld_organization(org_dict):
    """Returns a Schema.org GovernmentOrganization dict for an organization page."""
    site_url = toolkit.config.get('ckan.site_url', '').rstrip('/')
    org_url = site_url + toolkit.url_for('organization.read', id=org_dict.get('name', ''))

    description = toolkit.h.markdown_extract(
        toolkit.h.get_translated(org_dict, 'description') or '', extract_length=300
    )

    return {
        '@context': 'https://schema.org',
        '@type': 'GovernmentOrganization',
        'name': org_dict.get('display_name') or org_dict.get('title') or org_dict.get('name', ''),
        'description': description,
        'url': org_url,
    }


def seo_jsonld_site():
    """Returns a Schema.org GovernmentOrganization dict for the ARTESP site homepage."""
    site_url = toolkit.config.get('ckan.site_url', '').rstrip('/')
    site_title = toolkit.config.get('ckan.site_title', 'ARTESP Dados Abertos')
    site_description = toolkit.config.get('ckan.site_description', '')

    jsonld = {
        '@context': 'https://schema.org',
        '@type': 'GovernmentOrganization',
        'name': site_title,
        'url': site_url,
    }

    if site_description:
        jsonld['description'] = site_description

    return jsonld


def get_helpers():
    return {
        "artesp_theme_hello": artesp_theme_hello,
        "artesp_ldap_enabled": artesp_ldap_enabled,
        "artesp_govbr_login_enabled": artesp_govbr_login_enabled,
        "artesp_is_external_user": artesp_is_external_user,
        "artesp_auth_provider": artesp_auth_provider,
        "artesp_is_user_external": artesp_is_user_external,
        "get_package_count": get_package_count,
        "get_resource_count": get_resource_count,
        "get_latest_datasets": get_latest_datasets,
        "get_featured_datasets": get_featured_datasets,
        "get_latest_resources": get_latest_resources,
        "get_organization_count": get_organization_count,
        "get_group_count": get_group_count,
        "get_featured_groups": get_featured_groups,
        "get_dashboard_statistics": get_dashboard_statistics,
        "get_year": get_year,
        "safe_html": safe_html,
        "fix_fontawesome_icon": fix_fontawesome_icon,
        "get_artesp_organization": get_artesp_organization,
        "get_default_dataset_collaborator_capacity": get_default_dataset_collaborator_capacity,
        "get_dataset_rating_summary": get_dataset_rating_summary,
        "get_current_user_dataset_rating": get_current_user_dataset_rating,
        "rating_comment_captcha_enabled": rating_comment_captcha_enabled,
        "get_rating_comment_captcha_challenge_url": get_rating_comment_captcha_challenge_url,
        "get_rating_comment_captcha_script_url": get_rating_comment_captcha_script_url,
        "get_rating_comment_captcha_stylesheet_url": get_rating_comment_captcha_stylesheet_url,
        "seo_canonical_url": seo_canonical_url,
        "seo_meta_description": seo_meta_description,
        "seo_jsonld_dataset": seo_jsonld_dataset,
        "seo_jsonld_organization": seo_jsonld_organization,
        "seo_jsonld_site": seo_jsonld_site,
    }
