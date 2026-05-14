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
    limit: int | None


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


def _apply_page(query, page: int, limit: int | None):
    if limit is None:
        return query
    return query.offset((page - 1) * limit).limit(limit)


def _format_datetime(value):
    if not value:
        return ""
    return value.isoformat()


def _tag_names(package) -> str:
    return ", ".join(sorted(tag.name for tag in package.get_tags()))


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

    rows = _apply_page(query, page, limit).all()

    return ManagementResult(
        items=[
            {
                "id": user.id,
                "name": user.name,
                "fullname": user.fullname or "",
                "email": user.email or "",
                "created": user.created,
                "created_iso": _format_datetime(user.created),
                "updated_iso": "",
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

    rows = _apply_page(query, page, limit).all()

    return ManagementResult(
        items=[
            {
                "id": package.id,
                "name": package.name,
                "title": package.title or package.name,
                "state": package.state,
                "private": bool(package.private),
                "notes": package.notes or "",
                "license_id": getattr(package, "license_id", "") or "",
                "metadata_created": package.metadata_created,
                "metadata_created_iso": _format_datetime(package.metadata_created),
                "metadata_modified": package.metadata_modified,
                "metadata_modified_iso": _format_datetime(package.metadata_modified),
                "creator_name": creator_name or "",
                "owner_org": owner_org_name or "",
                "resource_count": resource_count or 0,
                "collaborator_count": collaborator_count or 0,
                "tags": _tag_names(package),
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
        model.Session.query(
            model.Resource,
            model.Package,
            model.User.name.label("creator_name"),
            model.Group.name.label("owner_org_name"),
        )
        .join(model.Package, model.Package.id == model.Resource.package_id)
        .outerjoin(model.User, model.User.id == model.Package.creator_user_id)
        .outerjoin(model.Group, model.Group.id == model.Package.owner_org)
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

    rows = _apply_page(query, page, limit).all()

    return ManagementResult(
        items=[
            {
                "id": resource.id,
                "name": resource.name or resource.url or resource.id,
                "description": resource.description or "",
                "format": resource.format or "",
                "mimetype": resource.mimetype or "",
                "state": resource.state,
                "url": resource.url or "",
                "size": resource.size or "",
                "created": resource.created,
                "created_iso": _format_datetime(resource.created),
                "last_modified": resource.last_modified,
                "last_modified_iso": _format_datetime(resource.last_modified),
                "metadata_modified": resource.metadata_modified,
                "metadata_modified_iso": _format_datetime(resource.metadata_modified),
                "package_id": package.id,
                "package_name": package.name,
                "package_title": package.title or package.name,
                "owner_org": owner_org_name or "",
                "creator_name": creator_name or "",
            }
            for resource, package, creator_name, owner_org_name in rows
        ],
        count=count,
        page=page,
        limit=limit,
    )


def export_admin_user_management(filters):
    users = get_admin_user_management(filters, page=1, limit=None)
    return [
        {
            "id": user["id"],
            "usuario": user["name"],
            "nome_completo": user["fullname"],
            "email": user["email"],
            "estado": user["state"],
            "sysadmin": "sim" if user["sysadmin"] else "nao",
            "criado_em": user["created_iso"],
            "atualizado_em": user["updated_iso"],
            "datasets_criados": user["created_dataset_count"],
        }
        for user in users.items
    ]


def export_admin_dataset_management(filters):
    datasets = get_admin_dataset_management(filters, page=1, limit=None)
    return [
        {
            "id": dataset["id"],
            "nome": dataset["name"],
            "titulo": dataset["title"],
            "descricao": dataset["notes"],
            "estado": dataset["state"],
            "privado": "sim" if dataset["private"] else "nao",
            "organizacao": dataset["owner_org"],
            "criador": dataset["creator_name"],
            "licenca": dataset["license_id"],
            "criado_em": dataset["metadata_created_iso"],
            "modificado_em": dataset["metadata_modified_iso"],
            "recursos": dataset["resource_count"],
            "colaboradores": dataset["collaborator_count"],
            "tags": dataset["tags"],
        }
        for dataset in datasets.items
    ]


def export_admin_resource_management(filters):
    resources = get_admin_resource_management(filters, page=1, limit=None)
    return [
        {
            "id": resource["id"],
            "nome": resource["name"],
            "descricao": resource["description"],
            "formato": resource["format"],
            "mimetype": resource["mimetype"],
            "estado": resource["state"],
            "url": resource["url"],
            "tamanho": resource["size"],
            "criado_em": resource["created_iso"],
            "ultima_modificacao": resource["last_modified_iso"],
            "metadata_modificada_em": resource["metadata_modified_iso"],
            "dataset_id": resource["package_id"],
            "dataset_nome": resource["package_name"],
            "dataset_titulo": resource["package_title"],
            "organizacao": resource["owner_org"],
            "criador_dataset": resource["creator_name"],
        }
        for resource in resources.items
    ]
