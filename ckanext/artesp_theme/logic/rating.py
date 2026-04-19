"""Core domain module for the dataset rating feature.

Holds the canonical criteria constant and the ldap/govbr author classification
helpers. Keep this module free of HTTP, captcha and notification concerns.
"""
from __future__ import annotations

from sqlalchemy import text

from ckan import model


RATING_CRITERIA: tuple[str, ...] = (
    "links_work",
    "up_to_date",
    "well_structured",
)


def is_ldap_user(user_id: str) -> bool:
    """Return True when ``user_id`` is present in the ``ldap_user`` table.

    Uses a point query to avoid loading every LDAP user on each classification.
    Returns False defensively when the ``ldap_user`` table is unavailable
    (e.g. in a test environment without the ldap extension).
    """
    if not user_id:
        return False
    try:
        row = model.Session.execute(
            text("SELECT 1 FROM ldap_user WHERE user_id = :uid LIMIT 1"),
            {"uid": user_id},
        ).first()
    except Exception:
        model.Session.rollback()
        return False
    return row is not None


def get_rating_author_kind(user_id: str) -> str:
    """Return the canonical author classification for the rating feature.

    Only two kinds exist: ``"ldap"`` and ``"govbr"``. Legacy
    ``plugin_extras.artesp.user_type = internal/external`` is ignored here.
    """
    return "ldap" if is_ldap_user(user_id) else "govbr"
