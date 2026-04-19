from urllib.parse import urlparse

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.logic.action.create import (
    group_create as core_group_create,
    package_collaborator_create as core_package_collaborator_create,
)
from ckan.logic.action.create import package_create as core_package_create

import ckanext.artesp_theme.logic.schema as schema
from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.logic import dashboard_statistics

try:
    from ckanext.unfold.adapters import ADAPTERS as UNFOLD_ADAPTERS
except ImportError:
    UNFOLD_ADAPTERS = {}


UNFOLD_VIEW_TYPE = "unfold_view"
UNFOLD_VIEW_TITLE = "Unfold"
UNFOLD_ARCHIVE_EXTENSIONS = tuple(
    sorted(UNFOLD_ADAPTERS.keys(), key=len, reverse=True)
)
UNFOLD_MIMETYPE_ALIASES = {
    "application/vnd.rar": "rar",
    "application/x-rar-compressed": "rar",
    "application/rar": "rar",
    "application/zip": "zip",
    "application/x-zip-compressed": "zip",
    "application/x-7z-compressed": "7z",
    "application/java-archive": "jar",
    "application/x-tar": "tar",
    "application/gzip": "tar.gz",
    "application/x-gzip": "tar.gz",
    "application/x-bzip2": "tar.bz2",
    "application/x-xz": "tar.xz",
    "application/x-archive": "ar",
    "application/x-debian-package": "deb",
    "application/vnd.debian.binary-package": "deb",
    "application/x-rpm": "rpm",
}


@tk.side_effect_free
def artesp_theme_get_sum(context, data_dict):
    tk.check_access("artesp_theme_get_sum", context, data_dict)
    data, errors = tk.navl_validate(data_dict, schema.artesp_theme_get_sum(), context)

    if errors:
        raise tk.ValidationError(errors)

    return {
        "left": data["left"],
        "right": data["right"],
        "sum": data["left"] + data["right"],
    }


@tk.side_effect_free
def artesp_theme_dashboard_statistics(context, data_dict):
    tk.check_access("artesp_theme_dashboard_statistics", context, data_dict)
    return dashboard_statistics.get_dashboard_statistics(data_dict or {})


def package_create(context, data_dict):
    tk.check_access("package_create", context, data_dict)

    if not data_dict or not data_dict.get("owner_org"):
        raise tk.NotAuthorized(tk._("Datasets must define owner_org."))

    if not auth_helpers.is_artesp_owner_org(data_dict.get("owner_org")):
        raise tk.NotAuthorized(
            tk._("Datasets can only be created in the ARTESP organization.")
        )

    action_context = dict(context)
    action_context["ignore_auth"] = True

    package = core_package_create(action_context, dict(data_dict or {}))
    sync_unfold_resource_views(context, package.get("resources", []))
    return package


def package_collaborator_create(context, data_dict):
    normalized_data = auth_helpers.normalize_package_collaborator_create_data(
        context, data_dict
    )
    tk.check_access("package_collaborator_create", context, normalized_data)

    action_context = dict(context)
    action_context["ignore_auth"] = True

    return core_package_collaborator_create(action_context, normalized_data)


def group_create(context, data_dict):
    tk.check_access("group_create", context, data_dict)

    action_context = dict(context)
    action_context["ignore_auth"] = True

    group = core_group_create(action_context, dict(data_dict or {}))
    auth_helpers.ensure_all_ldap_users_in_group(group.get("id") or group.get("name"))
    return group


def sync_unfold_resource_views(context, resources):
    for resource in resources or []:
        sync_unfold_resource_view(context, resource)


def sync_unfold_resource_view(context, resource):
    if not resource or not resource.get("id"):
        return

    if not plugins.plugin_loaded("unfold") or not UNFOLD_ADAPTERS:
        return

    normalize_resource_for_unfold(resource)
    supported = _resource_supports_unfold(resource)
    action_context = _build_internal_context(context)
    existing_views = tk.get_action("resource_view_list")(
        action_context,
        {"id": resource["id"]},
    )
    unfold_views = [
        view for view in existing_views if view.get("view_type") == UNFOLD_VIEW_TYPE
    ]

    if supported and not unfold_views:
        tk.get_action("resource_view_create")(
            action_context,
            {
                "resource_id": resource["id"],
                "view_type": UNFOLD_VIEW_TYPE,
                "title": UNFOLD_VIEW_TITLE,
            },
        )
        return

    if supported and len(unfold_views) <= 1:
        return

    for view in unfold_views[1:] if supported else unfold_views:
        tk.get_action("resource_view_delete")(action_context, {"id": view["id"]})


def _build_internal_context(context):
    internal_context = dict(context or {})
    internal_context.setdefault("model", model)
    internal_context.setdefault("user", "")
    internal_context["ignore_auth"] = True
    return internal_context


def _resource_supports_unfold(resource):
    return _detect_unfold_format(resource) in UNFOLD_ADAPTERS


def normalize_resource_for_unfold(resource):
    normalized_format = _detect_unfold_format(resource)
    if normalized_format:
        resource["format"] = normalized_format
    return resource


def _detect_unfold_format(resource):
    if not resource:
        return None

    for field in ("format", "mimetype", "mimetype_inner"):
        normalized = _normalize_unfold_candidate(resource.get(field))
        if normalized:
            return normalized

    for field in ("name", "url"):
        normalized = _extract_unfold_extension(resource.get(field))
        if normalized:
            return normalized

    return None


def _normalize_unfold_candidate(value):
    if not value:
        return None

    candidate = value.strip().lower()
    if not candidate:
        return None

    if candidate in UNFOLD_ADAPTERS:
        return candidate

    if candidate in UNFOLD_MIMETYPE_ALIASES:
        return UNFOLD_MIMETYPE_ALIASES[candidate]

    return _extract_unfold_extension(candidate)


def _extract_unfold_extension(value):
    if not value:
        return None

    candidate = value.strip().lower()
    if not candidate:
        return None

    parsed_path = urlparse(candidate).path or candidate
    for extension in UNFOLD_ARCHIVE_EXTENSIONS:
        if parsed_path.endswith(".{0}".format(extension)) or parsed_path == extension:
            return extension

    return None


_USER_UPDATE_ALLOWED = frozenset({"about", "image_url", "image_upload", "clear_upload"})


def user_update(context, data_dict):
    """Restringe user_update a apenas 'about' e foto para não-sysadmin."""
    from ckan.logic.action.update import user_update as core_user_update
    requester = context.get("auth_user_obj") or model.User.get(context.get("user", ""))
    if requester and not requester.sysadmin:
        allowed = {k: v for k, v in data_dict.items() if k in _USER_UPDATE_ALLOWED}
        allowed["id"] = data_dict.get("id") or data_dict.get("name", "")
        data_dict = allowed
    return core_user_update(context, data_dict)


def get_actions():
    return {
        "artesp_theme_dashboard_statistics": artesp_theme_dashboard_statistics,
        "group_create": group_create,
        "package_create": package_create,
        "package_collaborator_create": package_collaborator_create,
        "artesp_theme_get_sum": artesp_theme_get_sum,
        "user_update": user_update,
    }
