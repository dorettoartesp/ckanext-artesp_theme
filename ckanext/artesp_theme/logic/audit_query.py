from __future__ import annotations

from datetime import datetime, timedelta

import ckan.model as model
from sqlalchemy import or_

from ckanext.artesp_theme.audit_model import AuditEvent


PAGE_SIZE = 50

SCOPE_CHOICES = [
    ("all", "Todos"),
    ("authentication", "Autenticação"),
    ("dataset", "Dataset"),
    ("resource", "Resource"),
]

ACTION_CHOICES = [
    ("all", "Todas"),
    ("login_success", "Login com sucesso"),
    ("login_failure", "Falha de login"),
    ("logout", "Logout"),
    ("package_create", "Criar dataset"),
    ("package_update", "Atualizar dataset"),
    ("package_delete", "Excluir dataset"),
    ("resource_create", "Criar resource"),
    ("resource_update", "Atualizar resource"),
    ("resource_delete", "Excluir resource"),
]

PROVIDER_CHOICES = [
    ("all", "Todos"),
    ("govbr", "Gov.br"),
    ("ldap", "LDAP"),
    ("local", "Local"),
]

CHANNEL_CHOICES = [
    ("all", "Todos"),
    ("web", "Web"),
    ("api", "API"),
]

SORTABLE_FIELDS = {
    "occurred_at": AuditEvent.occurred_at,
    "event_family": AuditEvent.event_family,
    "event_action": AuditEvent.event_action,
    "actor_name": AuditEvent.actor_name,
    "actor_type": AuditEvent.actor_type,
    "auth_provider": AuditEvent.auth_provider,
    "channel": AuditEvent.channel,
    "ip_address": AuditEvent.ip_address,
    "package_name": AuditEvent.package_name,
    "resource_name": AuditEvent.resource_name,
}


def search_audit_events(raw_filters: dict[str, str] | None = None) -> dict[str, object]:
    filters = _normalize_filters(raw_filters or {})
    query = model.Session.query(AuditEvent)
    query = _apply_filters(query, filters)
    query = _apply_sort(query, filters)

    item_count = query.count()
    offset = (filters["page"] - 1) * PAGE_SIZE
    events = query.offset(offset).limit(PAGE_SIZE).all()

    return {
        "events": events,
        "item_count": item_count,
        "page": filters["page"],
        "page_size": PAGE_SIZE,
        "page_count": max(1, (item_count + PAGE_SIZE - 1) // PAGE_SIZE),
        "has_prev": filters["page"] > 1,
        "has_next": offset + len(events) < item_count,
        "filters": _serialize_filters(filters),
    }


def _normalize_filters(raw_filters: dict[str, str]) -> dict[str, object]:
    page = _parse_page(raw_filters.get("page"))
    return {
        "date_from": (raw_filters.get("date_from") or "").strip(),
        "date_to": (raw_filters.get("date_to") or "").strip(),
        "scope": (raw_filters.get("scope") or "all").strip() or "all",
        "action": (raw_filters.get("action") or "all").strip() or "all",
        "provider": (raw_filters.get("provider") or "all").strip() or "all",
        "channel": (raw_filters.get("channel") or "all").strip() or "all",
        "user": (raw_filters.get("user") or "").strip(),
        "ip": (raw_filters.get("ip") or "").strip(),
        "object": (raw_filters.get("object") or "").strip(),
        "sort_by": _parse_sort_by(raw_filters.get("sort_by")),
        "sort_dir": _parse_sort_dir(raw_filters.get("sort_dir")),
        "page": page,
    }


def _serialize_filters(filters: dict[str, object]) -> dict[str, str]:
    serialized = dict(filters)
    serialized["page"] = str(filters["page"])
    return serialized


def _parse_page(value: str | None) -> int:
    try:
        return max(1, int(value or "1"))
    except (TypeError, ValueError):
        return 1


def _parse_sort_by(value: str | None) -> str:
    candidate = (value or "occurred_at").strip()
    return candidate if candidate in SORTABLE_FIELDS else "occurred_at"


def _parse_sort_dir(value: str | None) -> str:
    candidate = (value or "desc").strip().lower()
    return candidate if candidate in {"asc", "desc"} else "desc"


def _apply_filters(query, filters: dict[str, object]):
    if filters["scope"] != "all":
        query = query.filter(AuditEvent.event_family == filters["scope"])
    if filters["action"] != "all":
        query = query.filter(AuditEvent.event_action == filters["action"])
    if filters["provider"] != "all":
        query = query.filter(AuditEvent.auth_provider == filters["provider"])
    if filters["channel"] != "all":
        query = query.filter(AuditEvent.channel == filters["channel"])
    if filters["user"]:
        query = query.filter(AuditEvent.actor_name.ilike(f"%{filters['user']}%"))
    if filters["ip"]:
        query = query.filter(AuditEvent.ip_address == filters["ip"])
    if filters["object"]:
        object_filter = f"%{filters['object']}%"
        query = query.filter(
            or_(
                AuditEvent.package_name.ilike(object_filter),
                AuditEvent.resource_name.ilike(object_filter),
            )
        )
    if filters["date_from"]:
        date_from = _parse_date(filters["date_from"])
        if date_from:
            query = query.filter(AuditEvent.occurred_at >= date_from)
    if filters["date_to"]:
        date_to = _parse_date(filters["date_to"])
        if date_to:
            query = query.filter(AuditEvent.occurred_at < date_to + timedelta(days=1))
    return query


def _apply_sort(query, filters: dict[str, object]):
    sortable_field = SORTABLE_FIELDS[filters["sort_by"]]
    direction = filters["sort_dir"]
    if direction == "asc":
        query = query.order_by(sortable_field.asc(), AuditEvent.occurred_at.asc())
    else:
        query = query.order_by(sortable_field.desc(), AuditEvent.occurred_at.desc())
    return query


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
