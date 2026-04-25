"""Capture CKAN runtime events into AuditEvent rows."""
from __future__ import annotations

import logging
from typing import Any, Optional

import ckan.model as model
from flask import has_request_context, request, session
from sqlalchemy.exc import ProgrammingError

from ckanext.artesp_theme.audit_model import AuditEvent, audit_event_table
from ckanext.artesp_theme.logic import auth_helpers

log = logging.getLogger(__name__)


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
    _persist_event(event)


def handle_user_logged_in(sender, **kwargs):
    if _request_path() == "/user/verify":
        return

    user = kwargs.get("user")
    record_auth_event(
        event_action="login_success",
        success=True,
        auth_provider=_auth_provider(),
        actor_name=getattr(user, "name", None),
        actor_identifier=getattr(user, "id", None),
        actor=user,
    )


def handle_user_logged_out(sender, **kwargs):
    user = kwargs.get("user")
    record_auth_event(
        event_action="logout",
        success=True,
        auth_provider=_auth_provider(),
        actor_name=getattr(user, "name", None),
        actor_identifier=getattr(user, "id", None),
        actor=user,
    )


def handle_failed_login(sender, **kwargs):
    record_auth_event(
        event_action="login_failure",
        success=False,
        auth_provider="local",
        actor_name=sender,
        actor_identifier=None,
    )


def record_auth_event(
    *,
    event_action: str,
    success: bool,
    auth_provider: Optional[str],
    actor_name: Optional[str],
    actor_identifier: Optional[str],
    actor=None,
    request_path: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
):
    event = AuditEvent(
        event_family="authentication",
        event_action=event_action,
        success=success,
        actor_id=getattr(actor, "id", None) or actor_identifier,
        actor_name=actor_name,
        actor_display_name=getattr(actor, "display_name", None),
        actor_type=_actor_type(actor),
        auth_provider=auth_provider,
        channel=_channel(),
        request_path=request_path or _request_path(),
        ip_address=_ip_address(),
        user_agent=_user_agent(),
        details=details or {},
    )
    _persist_event(event)


def _persist_event(event: AuditEvent) -> None:
    bind = model.Session.get_bind()
    values = {
        "id": event.id,
        "occurred_at": event.occurred_at,
        "event_family": event.event_family,
        "event_action": event.event_action,
        "success": event.success,
        "actor_id": event.actor_id,
        "actor_name": event.actor_name,
        "actor_display_name": event.actor_display_name,
        "actor_type": event.actor_type,
        "auth_provider": event.auth_provider,
        "channel": event.channel,
        "request_path": event.request_path,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "package_id": event.package_id,
        "package_name": event.package_name,
        "resource_id": event.resource_id,
        "resource_name": event.resource_name,
        "details": event.details,
    }

    try:
        with bind.begin() as connection:
            connection.execute(audit_event_table.insert().values(**values))
    except ProgrammingError:
        log.warning(
            "Skipping audit event because audit_event table is unavailable",
            extra={
                "event_family": event.event_family,
                "event_action": event.event_action,
            },
            exc_info=True,
        )


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
    try:
        path = getattr(request, "path", "")
    except RuntimeError:
        return ""
    return path or ""


def _auth_provider() -> str:
    try:
        provider = session.get("artesp_auth_provider")
    except RuntimeError:
        return "local"
    return provider or "local"


def _ip_address() -> Optional[str]:
    try:
        headers = getattr(request, "headers", {}) or {}
    except RuntimeError:
        return None
    forwarded_for = headers.get("X-Forwarded-For") if hasattr(headers, "get") else None
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    try:
        environ = getattr(request, "environ", {}) or {}
    except RuntimeError:
        return None
    return environ.get("REMOTE_ADDR")


def _user_agent() -> Optional[str]:
    try:
        user_agent = getattr(request, "user_agent", None)
    except RuntimeError:
        return None
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
