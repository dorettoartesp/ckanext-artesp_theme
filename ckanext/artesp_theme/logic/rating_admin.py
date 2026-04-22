"""Business helpers for rating administration views."""

from __future__ import annotations

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.model import (
    DatasetRating,
    RatingAction,
    RATING_STATUSES,
    RATING_STATUS_COLORS,
    RATING_STATUS_LABELS,
)


def get_ratings_for_package(
    pkg_id: str,
    status_filter: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    query = model.Session.query(DatasetRating).filter_by(package_id=pkg_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    query = query.order_by(DatasetRating.created_at.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    ratings = query.all()
    return [
        {
            "id": rating.id,
            "package_id": rating.package_id,
            "user_id": rating.user_id,
            "author_name": _get_user_display_name(rating.user_id),
            "overall_rating": rating.overall_rating,
            "criteria": rating.criteria,
            "comment": rating.comment,
            "status": getattr(rating, "status", None),
            "status_label": RATING_STATUS_LABELS.get(getattr(rating, "status", None), getattr(rating, "status", None)),
            "status_color": RATING_STATUS_COLORS.get(getattr(rating, "status", None), "#7f8c8d"),
            "created_at": rating.created_at,
        }
        for rating in ratings
    ]


def get_ratings_for_user(
    user_id: str,
    status_filter: str | None = None,
    dataset_filter: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    package_ids = _get_editable_package_ids(user_id)
    if not package_ids:
        return []

    if dataset_filter:
        pkg = model.Package.get(dataset_filter)
        if pkg and pkg.id in package_ids:
            package_ids = {pkg.id}
        else:
            return []

    roles = _get_user_roles_for_packages(user_id, package_ids)

    query = model.Session.query(DatasetRating).filter(
        DatasetRating.package_id.in_(package_ids)
    )
    if status_filter:
        query = query.filter_by(status=status_filter)

    query = query.order_by(DatasetRating.created_at.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    ratings = query.all()
    rows = []
    for rating in ratings:
        package = model.Package.get(rating.package_id)
        rows.append(
            {
                "id": rating.id,
                "package_id": rating.package_id,
                "dataset_name": (
                    (package.title or package.name)
                    if package
                    else rating.package_id
                ),
                "dataset_slug": package.name if package else rating.package_id,
                "user_role": roles.get(rating.package_id, ""),
                "user_id": rating.user_id,
                "author_name": _get_user_display_name(rating.user_id),
                "overall_rating": rating.overall_rating,
                "criteria": rating.criteria,
                "comment": rating.comment,
                "status": getattr(rating, "status", None),
                "status_label": RATING_STATUS_LABELS.get(
                    getattr(rating, "status", None),
                    getattr(rating, "status", None),
                ),
                "status_color": RATING_STATUS_COLORS.get(
                    getattr(rating, "status", None),
                    "#7f8c8d",
                ),
                "created_at": rating.created_at,
            }
        )
    return rows


def get_editable_packages_for_user(user_id: str) -> list[dict]:
    """Return [{id, name, title}] for active packages the user can edit, sorted by title."""
    package_ids = _get_editable_package_ids(user_id)
    packages = []
    for pkg_id in package_ids:
        pkg = model.Package.get(pkg_id)
        if pkg and pkg.state == "active":
            packages.append({"id": pkg.id, "name": pkg.name, "title": pkg.title or pkg.name})
    return sorted(packages, key=lambda p: p["title"].lower())


def create_rating_action(
    rating_id: str,
    actor_id: str,
    new_status: str,
    note: str | None,
    send_email: bool,
) -> RatingAction:
    if new_status not in RATING_STATUSES:
        raise tk.ValidationError({"new_status": ["Invalid status."]})

    rating = model.Session.query(DatasetRating).get(rating_id)
    if rating is None:
        raise tk.ObjectNotFound("Rating not found")

    action = RatingAction(
        rating_id=rating.id,
        actor_id=actor_id,
        status_before=rating.status,
        status_after=new_status,
        note=note,
        email_sent=False,
    )
    rating.status = new_status

    if send_email:
        action.email_sent = _send_action_email(rating, new_status, note)

    model.Session.add(action)
    model.Session.commit()
    return action


def get_rating_detail(rating_id: str) -> dict:
    rating = model.Session.query(DatasetRating).get(rating_id)
    if rating is None:
        raise tk.ObjectNotFound("Rating not found")

    actions = (
        model.Session.query(RatingAction)
        .filter_by(rating_id=rating_id)
        .order_by(RatingAction.created_at.asc())
        .all()
    )

    return {
        "rating": {
            "id": rating.id,
            "package_id": rating.package_id,
            "user_id": rating.user_id,
            "author_name": _get_user_display_name(rating.user_id),
            "overall_rating": rating.overall_rating,
            "criteria": rating.criteria,
            "comment": rating.comment,
            "status": rating.status,
            "status_label": RATING_STATUS_LABELS.get(rating.status, rating.status),
            "status_color": RATING_STATUS_COLORS.get(rating.status, "#7f8c8d"),
            "created_at": rating.created_at,
        },
        "actions": [
            {
                "actor_id": action.actor_id,
                "actor_name": _get_actor_name(action.actor_id),
                "status_before": action.status_before,
                "status_after": action.status_after,
                "note": action.note,
                "email_sent": action.email_sent,
                "created_at": action.created_at,
            }
            for action in actions
        ],
    }


def _send_action_email(rating, new_status: str, note: str | None) -> bool:
    return False


_CAPACITY_LABELS = {
    "admin": "Administrador",
    "editor": "Editor",
}


def _get_user_roles_for_packages(user_id: str, package_ids: set[str]) -> dict[str, str]:
    """Return {package_id: role_label} for the given user and package set."""
    roles: dict[str, str] = {}

    owned = (
        model.Session.query(model.Package.id)
        .filter(model.Package.creator_user_id == user_id)
        .filter(model.Package.id.in_(package_ids))
        .all()
    )
    for (pkg_id,) in owned:
        roles[pkg_id] = "Criador"

    if auth_helpers.is_dataset_collaborators_enabled():
        collaborators = (
            model.Session.query(model.PackageMember)
            .filter(model.PackageMember.user_id == user_id)
            .filter(model.PackageMember.package_id.in_(package_ids))
            .filter(model.PackageMember.capacity.in_(auth_helpers.EDIT_CAPACITIES))
            .all()
        )
        for collab in collaborators:
            if collab.package_id not in roles:
                roles[collab.package_id] = _CAPACITY_LABELS.get(collab.capacity, collab.capacity)

    return roles


def _get_editable_package_ids(user_id: str) -> set[str]:
    package_ids: set[str] = set()

    owned_packages = (
        model.Session.query(model.Package)
        .filter(model.Package.creator_user_id == user_id)
        .filter(model.Package.state == "active")
        .all()
    )
    package_ids.update(package.id for package in owned_packages)

    if auth_helpers.is_dataset_collaborators_enabled():
        collaborators = (
            model.Session.query(model.PackageMember)
            .filter(model.PackageMember.user_id == user_id)
            .filter(model.PackageMember.capacity.in_(auth_helpers.EDIT_CAPACITIES))
            .all()
        )
        package_ids.update(collaborator.package_id for collaborator in collaborators)

    return package_ids


def _get_actor_name(actor_id: str) -> str:
    if actor_id == "system":
        return "Sistema"

    user = model.User.get(actor_id)
    if not user:
        return actor_id

    return user.fullname or user.name


def _get_user_display_name(user_id: str) -> str:
    user = model.User.get(user_id)
    if not user:
        return user_id

    return user.fullname or user.name
