"""Capture CKAN runtime events into AuditEvent rows."""
from __future__ import annotations

from typing import Any, Optional

import ckan.model as model
from flask import has_request_context, request

from ckanext.artesp_theme.audit_model import AuditEvent
from ckanext.artesp_theme.logic import auth_helpers


_TRACKED_ACTIONS = {
    "package_create": "dataset",
    "package_update": "dataset",
    "package_delete": "dataset",
    "resource_create": "resource",
    "resource_update": "resource",
    "resource_delete": "resource",
}


def handle_action_succeeded(sender, **kwargs):
    action_name = sender
    event_family = _TRACKED_ACTIONS.get(action_name)
    if not event_family:
        return

    context = kwargs.get("context") or {}
    data_dict = kwargs.get("data_dict") or {}
    result = kwargs.get("result")

    actor = auth_helpers.get_authenticated_user(context)
    event = AuditEvent(
        event_family=event_family,
        event_action=action_name,
        success=True,
        actor_id=getattr(actor, "id", None),
        actor_name=getattr(actor, "name", None),
        actor_display_name=getattr(actor, "display_name", None),
        actor_type=_actor_type(actor),
        channel=_channel(),
        request_path=_request_path(),
        ip_address=_ip_address(),
        user_agent=_user_agent(),
        package_id=_package_id(action_name, data_dict, result),
        package_name=_package_name(action_name, data_dict, result),
        resource_id=_resource_id(action_name, data_dict, result),
        resource_name=_resource_name(action_name, data_dict, result),
    )
    model.Session.add(event)
    model.Session.commit()


def _actor_type(actor) -> str:
    if not actor:
        return "anonymous"
    if getattr(actor, "sysadmin", False):
        return "sysadmin"
    if auth_helpers.is_external_user(actor):
        return "external"
    return "internal"


def _channel() -> str:
    path = _request_path()
    if path.startswith("/api/"):
        return "api"
    return "web"


def _request_path() -> str:
    if has_request_context():
        return request.path or ""
    path = getattr(request, "path", "")
    return path or ""


def _ip_address() -> Optional[str]:
    headers = getattr(request, "headers", {}) or {}
    forwarded_for = headers.get("X-Forwarded-For") if hasattr(headers, "get") else None
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    environ = getattr(request, "environ", {}) or {}
    return environ.get("REMOTE_ADDR")


def _user_agent() -> Optional[str]:
    user_agent = getattr(request, "user_agent", None)
    return getattr(user_agent, "string", None)


def _package_id(action_name: str, data_dict: dict[str, Any], result: Any) -> Optional[str]:
    if action_name in {"package_create", "package_update"} and isinstance(result, dict):
        return result.get("id")

    package = _package_obj(action_name, data_dict)
    return getattr(package, "id", None)


def _package_name(action_name: str, data_dict: dict[str, Any], result: Any) -> Optional[str]:
    if action_name in {"package_create", "package_update"} and isinstance(result, dict):
        return result.get("name")

    package = _package_obj(action_name, data_dict)
    return getattr(package, "name", None)


def _resource_id(action_name: str, data_dict: dict[str, Any], result: Any) -> Optional[str]:
    if action_name in {"resource_create", "resource_update"} and isinstance(result, dict):
        return result.get("id")

    resource = _resource_obj(action_name, data_dict)
    return getattr(resource, "id", None)


def _resource_name(action_name: str, data_dict: dict[str, Any], result: Any) -> Optional[str]:
    if action_name in {"resource_create", "resource_update"} and isinstance(result, dict):
        return result.get("name")

    resource = _resource_obj(action_name, data_dict)
    return getattr(resource, "name", None)


def _package_obj(action_name: str, data_dict: dict[str, Any]):
    if action_name.startswith("package_"):
        return auth_helpers.get_package(data_dict)
    return auth_helpers.get_package_from_resource(data_dict)


def _resource_obj(action_name: str, data_dict: dict[str, Any]):
    if not action_name.startswith("resource_"):
        return None
    return auth_helpers.get_resource(data_dict)
