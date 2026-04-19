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
    sa.Column("created_at", sa.types.DateTime, nullable=False),
    sa.Column("updated_at", sa.types.DateTime, nullable=False),
    sa.CheckConstraint(
        "overall_rating BETWEEN 1 AND 5", name="ck_dataset_rating_overall",
    ),
    sa.UniqueConstraint("user_id", "package_id", name="uq_dataset_rating_user_pkg"),
    sa.Index("ix_dataset_rating_pkg_updated", "package_id", "updated_at"),
)


class DatasetRating(domain_object.DomainObject):
    """Single user's rating for a package (one row per user, package pair)."""

    id: str
    user_id: str
    package_id: str
    overall_rating: int
    criteria: dict
    comment: Optional[str]
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


meta.registry.map_imperatively(DatasetRating, dataset_rating_table)
