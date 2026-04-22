"""SQLAlchemy model for the dataset rating feature."""
from __future__ import annotations

import datetime as _dt
import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

import ckan.model as ckan_model
import ckan.model.domain_object as domain_object
import ckan.model.meta as meta


RATING_STATUSES = (
    "pendente",
    "necessita_esclarecimentos",
    "aprovado",
    "finalizado",
    "rejeitado",
)

RATING_STATUS_LABELS = {
    "pendente": "Pendente",
    "necessita_esclarecimentos": "Necessita esclarecimentos",
    "aprovado": "Aprovado",
    "finalizado": "Finalizado",
    "rejeitado": "Rejeitado",
}

RATING_STATUS_COLORS = {
    "pendente": "#e67e22",
    "necessita_esclarecimentos": "#3498db",
    "aprovado": "#27ae60",
    "finalizado": "#7f8c8d",
    "rejeitado": "#c0392b",
}


def _default_rating_status(comment: Optional[str]) -> str:
    if (comment or "").strip():
        return "pendente"
    return "finalizado"


dataset_rating_table = sa.Table(
    "dataset_rating",
    meta.metadata,
    sa.Column("id", sa.types.UnicodeText, primary_key=True),
    sa.Column(
        "user_id",
        sa.types.UnicodeText,
        sa.ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "package_id",
        sa.types.UnicodeText,
        sa.ForeignKey("package.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("overall_rating", sa.types.SmallInteger, nullable=False),
    sa.Column("criteria", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    sa.Column("comment", sa.types.UnicodeText, nullable=True),
    sa.Column("status", sa.types.String(50), nullable=False),
    sa.Column("created_at", sa.types.DateTime, nullable=False),
    sa.Column("updated_at", sa.types.DateTime, nullable=False),
    sa.CheckConstraint(
        "overall_rating BETWEEN 1 AND 5", name="ck_dataset_rating_overall",
    ),
    sa.UniqueConstraint("user_id", "package_id", name="uq_dataset_rating_user_pkg"),
    sa.Index("ix_dataset_rating_pkg_updated", "package_id", "updated_at"),
)

rating_action_table = sa.Table(
    "rating_action",
    meta.metadata,
    sa.Column("id", sa.types.UnicodeText, primary_key=True),
    sa.Column(
        "rating_id",
        sa.types.UnicodeText,
        sa.ForeignKey("dataset_rating.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("actor_id", sa.types.UnicodeText, nullable=False),
    sa.Column("status_before", sa.types.String(50), nullable=True),
    sa.Column("status_after", sa.types.String(50), nullable=False),
    sa.Column("note", sa.types.UnicodeText, nullable=True),
    sa.Column("email_sent", sa.types.Boolean, nullable=False, default=False),
    sa.Column("created_at", sa.types.DateTime, nullable=False),
)


class DatasetRating(domain_object.DomainObject):
    """Single user's rating for a package (one row per user, package pair)."""

    id: str
    user_id: str
    package_id: str
    overall_rating: int
    criteria: dict
    comment: Optional[str]
    status: str
    created_at: _dt.datetime
    updated_at: _dt.datetime

    def __init__(
        self,
        user_id: str,
        package_id: str,
        overall_rating: int,
        criteria: Optional[dict] = None,
        comment: Optional[str] = None,
    ) -> None:
        now = _dt.datetime.utcnow()
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.package_id = package_id
        self.overall_rating = overall_rating
        self.criteria = criteria or {}
        self.comment = comment
        self.status = _default_rating_status(comment)
        self.created_at = now
        self.updated_at = now

    @classmethod
    def get_for(cls, user_id: str, package_id: str) -> Optional["DatasetRating"]:
        """Return the rating record for ``(user_id, package_id)`` or None."""
        return (
            ckan_model.Session.query(cls)
            .filter_by(user_id=user_id, package_id=package_id)
            .first()
        )

    @classmethod
    def list_for_package(cls, package_id: str) -> list["DatasetRating"]:
        return (
            ckan_model.Session.query(cls)
            .filter_by(package_id=package_id)
            .order_by(cls.updated_at.desc())
            .all()
        )


class RatingAction(domain_object.DomainObject):
    """Audit trail entry for a status change in a dataset rating."""

    id: str
    rating_id: str
    actor_id: str
    status_before: Optional[str]
    status_after: str
    note: Optional[str]
    email_sent: bool
    created_at: _dt.datetime

    def __init__(
        self,
        rating_id: str,
        actor_id: str,
        status_after: str,
        status_before: Optional[str] = None,
        note: Optional[str] = None,
        email_sent: bool = False,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.rating_id = rating_id
        self.actor_id = actor_id
        self.status_before = status_before
        self.status_after = status_after
        self.note = note
        self.email_sent = email_sent
        self.created_at = _dt.datetime.utcnow()


meta.registry.map_imperatively(DatasetRating, dataset_rating_table)
meta.registry.map_imperatively(RatingAction, rating_action_table)
