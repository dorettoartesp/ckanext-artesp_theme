"""Read helpers for the ARTESP sysadmin management center."""

from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa

import ckan.model as model


DEFAULT_LIMIT = 50


@dataclass
class ManagementResult:
    items: list[dict]
    count: int
    page: int
    limit: int


def _coerce_page(value) -> int:
    try:
        page = int(value)
    except (TypeError, ValueError):
        return 1
    return max(page, 1)


def _like(term: str) -> str:
    return "%{}%".format(term.strip())


def _sort_direction(filters) -> str:
    direction = (filters or {}).get("sort_dir", "asc").strip().lower()
    if direction not in {"asc", "desc"}:
        return "asc"
    return direction


def _ordered(column, direction: str):
    return column.desc() if direction == "desc" else column.asc()


def get_admin_user_management(filters, page=1, limit=DEFAULT_LIMIT):
    page = _coerce_page(page)
    q = (filters or {}).get("q", "").strip()
    sysadmin = (filters or {}).get("sysadmin", "").strip()
    sort_by = (filters or {}).get("sort_by", "").strip()
    sort_dir = _sort_direction(filters)

    created_count = (
        model.Session.query(sa.func.count(model.Package.id))
        .filter(model.Package.creator_user_id == model.User.id)
        .filter(model.Package.type == "dataset")
        .filter(model.Package.state != model.State.DELETED)
        .correlate(model.User)
        .scalar_subquery()
    )

    query = (
        model.Session.query(
            model.User,
            created_count.label("created_dataset_count"),
        )
        .filter(model.User.state != model.State.DELETED)
        .filter(model.User.name != "default")
    )

    if q:
        like = _like(q)
        query = query.filter(
            sa.or_(
                model.User.name.ilike(like),
                model.User.fullname.ilike(like),
                model.User.email.ilike(like),
            )
        )
    if sysadmin in {"true", "false"}:
        query = query.filter(model.User.sysadmin.is_(sysadmin == "true"))

    count = query.count()
    sort_columns = {
        "name": sa.func.lower(model.User.name),
        "email": sa.func.lower(model.User.email),
        "state": model.User.state,
        "datasets": created_count,
    }
    if sort_by in sort_columns:
        query = query.order_by(_ordered(sort_columns[sort_by], sort_dir), model.User.name)
    else:
        query = query.order_by(model.User.sysadmin.desc(), model.User.name)

    rows = query.offset((page - 1) * limit).limit(limit).all()

    return ManagementResult(
        items=[
            {
                "id": user.id,
                "name": user.name,
                "fullname": user.fullname or "",
                "email": user.email or "",
                "state": user.state,
                "sysadmin": bool(user.sysadmin),
                "created_dataset_count": created_dataset_count or 0,
            }
            for user, created_dataset_count in rows
        ],
        count=count,
        page=page,
        limit=limit,
    )


def get_admin_dataset_management(filters, page=1, limit=DEFAULT_LIMIT):
    page = _coerce_page(page)
    q = (filters or {}).get("q", "").strip()
    state = (filters or {}).get("state", "").strip()
    sort_by = (filters or {}).get("sort_by", "").strip()
    sort_dir = _sort_direction(filters)

    resource_count = (
        model.Session.query(sa.func.count(model.Resource.id))
        .filter(model.Resource.package_id == model.Package.id)
        .filter(model.Resource.state != model.State.DELETED)
        .correlate(model.Package)
        .scalar_subquery()
    )

    collaborator_count = (
        model.Session.query(sa.func.count(model.PackageMember.user_id))
        .filter(model.PackageMember.package_id == model.Package.id)
        .correlate(model.Package)
        .scalar_subquery()
    )

    query = (
        model.Session.query(
            model.Package,
            model.User.name.label("creator_name"),
            model.Group.name.label("owner_org_name"),
            resource_count.label("resource_count"),
            collaborator_count.label("collaborator_count"),
        )
        .outerjoin(model.User, model.User.id == model.Package.creator_user_id)
        .outerjoin(model.Group, model.Group.id == model.Package.owner_org)
        .filter(model.Package.type == "dataset")
        .filter(model.Package.state != model.State.DELETED)
    )

    if q:
        like = _like(q)
        query = query.filter(
            sa.or_(model.Package.name.ilike(like), model.Package.title.ilike(like))
        )
    if state:
        query = query.filter(model.Package.state == state)

    count = query.count()
    sort_columns = {
        "title": sa.func.lower(model.Package.title),
        "owner_org": sa.func.lower(model.Group.name),
        "creator": sa.func.lower(model.User.name),
        "resources": resource_count,
    }
    if sort_by in sort_columns:
        query = query.order_by(_ordered(sort_columns[sort_by], sort_dir), model.Package.name)
    else:
        query = query.order_by(model.Package.metadata_modified.desc(), model.Package.name)

    rows = query.offset((page - 1) * limit).limit(limit).all()

    return ManagementResult(
        items=[
            {
                "id": package.id,
                "name": package.name,
                "title": package.title or package.name,
                "state": package.state,
                "private": bool(package.private),
                "creator_name": creator_name or "",
                "owner_org": owner_org_name or "",
                "resource_count": resource_count or 0,
                "collaborator_count": collaborator_count or 0,
            }
            for package, creator_name, owner_org_name, resource_count, collaborator_count in rows
        ],
        count=count,
        page=page,
        limit=limit,
    )


def get_admin_resource_management(filters, page=1, limit=DEFAULT_LIMIT):
    page = _coerce_page(page)
    q = (filters or {}).get("q", "").strip()
    format_filter = (filters or {}).get("format", "").strip()
    sort_by = (filters or {}).get("sort_by", "").strip()
    sort_dir = _sort_direction(filters)

    query = (
        model.Session.query(model.Resource, model.Package)
        .join(model.Package, model.Package.id == model.Resource.package_id)
        .filter(model.Resource.state != model.State.DELETED)
        .filter(model.Package.state != model.State.DELETED)
        .filter(model.Package.type == "dataset")
    )

    if q:
        like = _like(q)
        query = query.filter(
            sa.or_(
                model.Resource.name.ilike(like),
                model.Resource.description.ilike(like),
                model.Package.name.ilike(like),
                model.Package.title.ilike(like),
            )
        )
    if format_filter:
        query = query.filter(model.Resource.format.ilike(format_filter))

    count = query.count()
    sort_columns = {
        "name": sa.func.lower(model.Resource.name),
        "dataset": sa.func.lower(model.Package.title),
        "format": sa.func.lower(model.Resource.format),
        "updated": model.Resource.metadata_modified,
    }
    if sort_by in sort_columns:
        query = query.order_by(_ordered(sort_columns[sort_by], sort_dir), model.Resource.name)
    else:
        query = query.order_by(model.Resource.metadata_modified.desc(), model.Resource.name)

    rows = query.offset((page - 1) * limit).limit(limit).all()

    return ManagementResult(
        items=[
            {
                "id": resource.id,
                "name": resource.name or resource.url or resource.id,
                "format": resource.format or "",
                "state": resource.state,
                "metadata_modified": resource.metadata_modified,
                "package_id": package.id,
                "package_name": package.name,
                "package_title": package.title or package.name,
            }
            for resource, package in rows
        ],
        count=count,
        page=page,
        limit=limit,
    )
