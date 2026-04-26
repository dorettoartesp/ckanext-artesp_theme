"""
In-process HTML response cache for the anonymous home page.

TTL: 30 seconds. Only serves anonymous GET / with no pending flash messages.
Cleared on dataset, resource, organization and group mutations so content stays
consistent after a publish event.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Response

log = logging.getLogger(__name__)

_CACHE: dict = {}
_CACHE_TTL = 30  # seconds
_LOCK = threading.Lock()

_INVALIDATING_ACTIONS = frozenset({
    "package_create", "package_update", "package_delete",
    "resource_create", "resource_update", "resource_delete",
    "organization_create", "organization_update", "organization_delete",
    "group_create", "group_update", "group_delete",
})


def _is_cacheable() -> bool:
    from flask import request, session
    from ckan.common import current_user
    return (
        request.method == "GET"
        and request.path == "/"
        and not getattr(current_user, "is_authenticated", False)
        and not session.get("_flashes")
    )


def get() -> Response | None:
    """Return a cached Response for anonymous home requests, or None."""
    try:
        if not _is_cacheable():
            return None
    except RuntimeError:
        return None

    now = time.monotonic()
    cached = _CACHE.get("home")
    if cached and cached["expires_at"] > now:
        from flask import Response
        log.debug("home_cache: HIT")
        resp = Response(cached["data"], content_type="text/html; charset=utf-8")
        resp.headers["X-Home-Cache"] = "HIT"
        return resp
    return None


def store(response: Response) -> Response:
    """Cache the home page HTML after a successful anonymous render."""
    try:
        if not _is_cacheable():
            return response
    except RuntimeError:
        return response

    if response.status_code != 200:
        return response
    if "text/html" not in (response.content_type or ""):
        return response

    with _LOCK:
        _CACHE["home"] = {
            "data": response.get_data(),
            "expires_at": time.monotonic() + _CACHE_TTL,
        }
    log.debug("home_cache: STORED")
    response.headers["X-Home-Cache"] = "MISS"
    return response


def clear() -> None:
    """Invalidate HTML cache and all related in-process helper caches."""
    with _LOCK:
        _CACHE.clear()

    # Also evict helper caches so the next re-render fetches fresh data.
    try:
        from ckanext.artesp_theme.helpers import _HELPERS_CACHE
        _HELPERS_CACHE.clear()
    except Exception:
        pass

    try:
        from ckanext.artesp_theme.logic.action import _PACKAGE_SEARCH_CACHE
        _PACKAGE_SEARCH_CACHE.clear()
    except Exception:
        pass

    log.debug("home_cache: CLEARED")


def should_invalidate(action_name: str) -> bool:
    return action_name in _INVALIDATING_ACTIONS
