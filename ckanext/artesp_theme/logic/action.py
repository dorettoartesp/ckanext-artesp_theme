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


def _enqueue_rating_notification(package_id: str, rating_id: str) -> None:
    from ckan.lib import jobs
    from ckanext.artesp_theme.logic import rating_notifications
    jobs.enqueue(
        rating_notifications.send_rating_comment_notifications,
        kwargs={"package_id": package_id, "rating_id": rating_id},
    )


def dataset_rating_upsert(context, data_dict):
    import logging
    from datetime import datetime, timezone

    import ckan.lib.navl.dictization_functions as dfunc
    from ckanext.artesp_theme.model import DatasetRating, dataset_rating_table
    from ckanext.artesp_theme.logic import schema as rating_schema

    log = logging.getLogger(__name__)

    tk.check_access("dataset_rating_upsert", context, data_dict)

    data, errors = dfunc.validate(data_dict, rating_schema.dataset_rating_upsert_schema(), context)
    if errors:
        raise tk.ValidationError(errors)

    user = context.get("auth_user_obj") or model.User.get(context.get("user", ""))
    if not user:
        raise tk.NotAuthorized(tk._("Must be logged in to rate a dataset."))

    user_id = user.id
    package_id = data["package_id"]
    criteria = data.get("criteria") or {}
    comment = data.get("comment") or ""

    existing = DatasetRating.get_for(user_id, package_id)
    prev_comment = (existing.comment or "") if existing else ""
    created = existing is None

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if existing is None:
        rating = DatasetRating(
            user_id=user_id,
            package_id=package_id,
            overall_rating=data["overall_rating"],
            criteria=criteria,
            comment=comment,
        )
        model.Session.add(rating)
    else:
        existing.overall_rating = data["overall_rating"]
        existing.criteria = criteria
        existing.comment = comment
        existing.updated_at = now
        rating = existing

    model.Session.commit()

    comment_changed = bool(comment) and comment != prev_comment
    notification_enqueued = False
    if comment_changed:
        try:
            _enqueue_rating_notification(package_id, rating.id)
            notification_enqueued = True
        except Exception:
            log.warning("Failed to enqueue rating notification for rating=%s", rating.id)

    return {
        "id": rating.id,
        "created": created,
        "comment_notification_enqueued": notification_enqueued,
    }


@tk.side_effect_free
def dataset_rating_show(context, data_dict):
    import ckan.lib.navl.dictization_functions as dfunc
    from ckanext.artesp_theme.model import DatasetRating
    from ckanext.artesp_theme.logic import schema as rating_schema

    tk.check_access("dataset_rating_show", context, data_dict)

    data, errors = dfunc.validate(data_dict, rating_schema.dataset_rating_show_schema(), context)
    if errors:
        raise tk.ValidationError(errors)

    user = context.get("auth_user_obj") or model.User.get(context.get("user", ""))
    if not user:
        return None

    rating = DatasetRating.get_for(user.id, data["package_id"])
    if rating is None:
        return None

    return {
        "id": rating.id,
        "package_id": rating.package_id,
        "overall_rating": rating.overall_rating,
        "criteria": rating.criteria,
        "comment": rating.comment,
        "created_at": rating.created_at.isoformat(),
        "updated_at": rating.updated_at.isoformat(),
    }


@tk.side_effect_free
def dataset_rating_summary(context, data_dict):
    import ckan.lib.navl.dictization_functions as dfunc
    from ckanext.artesp_theme.model import DatasetRating
    from ckanext.artesp_theme.logic import schema as rating_schema
    from ckanext.artesp_theme.logic.rating import RATING_CRITERIA

    tk.check_access("dataset_rating_summary", context, data_dict)

    data, errors = dfunc.validate(data_dict, rating_schema.dataset_rating_summary_schema(), context)
    if errors:
        raise tk.ValidationError(errors)

    package_id = data["package_id"]
    ratings = DatasetRating.list_for_package(package_id)

    count = len(ratings)
    average = round(sum(r.overall_rating for r in ratings) / count, 2) if count else None

    criteria_agg = {
        key: {"yes": 0, "no": 0} for key in RATING_CRITERIA
    }
    for r in ratings:
        for key in RATING_CRITERIA:
            if r.criteria and r.criteria.get(key):
                criteria_agg[key]["yes"] += 1
            else:
                criteria_agg[key]["no"] += 1

    return {
        "package_id": package_id,
        "overall": {
            "count": count,
            "average": average,
            "criteria": criteria_agg,
        },
    }


def get_actions():
    return {
        "artesp_theme_dashboard_statistics": artesp_theme_dashboard_statistics,
        "group_create": group_create,
        "package_create": package_create,
        "package_collaborator_create": package_collaborator_create,
        "artesp_theme_get_sum": artesp_theme_get_sum,
        "user_update": user_update,
        "dataset_rating_upsert": dataset_rating_upsert,
        "dataset_rating_show": dataset_rating_show,
        "dataset_rating_summary": dataset_rating_summary,
    }
