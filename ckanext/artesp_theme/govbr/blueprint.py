import logging

from flask import Blueprint, redirect, request, session, url_for
from ckan.plugins import toolkit

from .client import GovBRAuthError, GovBRClient
from .config import GovBRConfig
from .services import ExternalUserService, GovBRLinkError
from ckanext.artesp_theme.logic.auth_helpers import is_external_user

log = logging.getLogger(__name__)

govbr = Blueprint("govbr", __name__)


@govbr.before_app_request
def redirect_external_from_dashboard():
    if not request.path.startswith("/dashboard"):
        return
    try:
        from ckan.common import current_user
        if current_user.is_authenticated and is_external_user(current_user):
            return redirect(url_for("govbr.followed", id=current_user.name))
    except Exception:
        pass

_SESSION_STATE = "govbr_state"
_SESSION_VERIFIER = "govbr_code_verifier"
_SESSION_LINK_STATE = "govbr_link_state"
_SESSION_LINK_VERIFIER = "govbr_link_code_verifier"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _set_repoze_user(username: str) -> None:
    """Persist the logged-in user via CKAN's official login_user."""
    import ckan.model as model
    from ckan.common import login_user
    user_obj = model.User.get(username)
    if user_obj:
        login_user(user_obj)


def _flash_error(msg: str):
    toolkit.h.flash_error(toolkit._(msg))


def _get_client() -> GovBRClient:
    return GovBRClient(GovBRConfig.from_ckan_config())


# ---------------------------------------------------------------------------
# login flow
# ---------------------------------------------------------------------------

@govbr.route("/user/oidc/login")
def login():
    client = _get_client()
    config = GovBRConfig.from_ckan_config()
    url, state, verifier = client.get_authorization_url(config.redirect_uri)
    session[_SESSION_STATE] = state
    session[_SESSION_VERIFIER] = verifier
    session.modified = True
    return redirect(url)


@govbr.route("/user/oidc/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    expected_state = session.pop(_SESSION_STATE, None)
    verifier = session.pop(_SESSION_VERIFIER, None)

    if not state or state != expected_state:
        _flash_error("Invalid OAuth2 state. Please try again.")
        return redirect(url_for("user.login"))

    if not code:
        _flash_error("Authorization code missing.")
        return redirect(url_for("user.login"))

    try:
        config = GovBRConfig.from_ckan_config()
        client = _get_client()
        access_token = client.exchange_code(code, state, verifier, config.redirect_uri)
        userinfo = client.get_userinfo(access_token)
    except GovBRAuthError as exc:
        log.warning("GovBR auth error: %s", exc)
        _flash_error("Login via Gov.br failed. Please try again.")
        return redirect(url_for("user.login"))

    service = ExternalUserService()
    ckan_user = service.find_or_create(userinfo)

    if not ckan_user:
        _flash_error("Unable to create or retrieve your account.")
        return redirect(url_for("user.login"))

    _set_repoze_user(ckan_user.name)
    return redirect(url_for("home.index"))


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

@govbr.route("/user/oidc/logout")
def logout():
    client = _get_client()
    post_logout_uri = toolkit.h.url_for("home.index", qualified=True)
    govbr_logout = client.logout_url(post_logout_uri)

    # Clear CKAN session
    session.pop("ckan.user", None)
    session.modified = True

    return redirect(govbr_logout)


# ---------------------------------------------------------------------------
# link flow (authenticated LDAP user linking their GovBR account)
# ---------------------------------------------------------------------------

@govbr.route("/user/oidc/link")
def link():
    if not toolkit.c.user:
        return redirect(url_for("user.login"))

    client = _get_client()
    config = GovBRConfig.from_ckan_config()
    url, state, verifier = client.get_authorization_url(config.link_redirect_uri)
    session[_SESSION_LINK_STATE] = state
    session[_SESSION_LINK_VERIFIER] = verifier
    session.modified = True
    return redirect(url)


@govbr.route("/user/oidc/link/callback")
def link_callback():
    if not toolkit.c.user:
        return redirect(url_for("user.login"))

    code = request.args.get("code")
    state = request.args.get("state")

    expected_state = session.pop(_SESSION_LINK_STATE, None)
    verifier = session.pop(_SESSION_LINK_VERIFIER, None)

    if not state or state != expected_state:
        _flash_error("Invalid OAuth2 state. Please try again.")
        return redirect(url_for("user.me"))

    if not code:
        _flash_error("Authorization code missing.")
        return redirect(url_for("user.me"))

    try:
        config = GovBRConfig.from_ckan_config()
        client = _get_client()
        access_token = client.exchange_code(code, state, verifier, config.link_redirect_uri)
        userinfo = client.get_userinfo(access_token)
    except GovBRAuthError as exc:
        log.warning("GovBR link auth error: %s", exc)
        _flash_error("Gov.br authentication failed.")
        return redirect(url_for("user.me"))

    import ckan.model as model
    ckan_user = model.User.get(toolkit.c.user)
    if not ckan_user:
        _flash_error("Could not find your account.")
        return redirect(url_for("user.me"))

    try:
        service = ExternalUserService()
        service.link_account(ckan_user, userinfo)
    except GovBRLinkError as exc:
        log.warning("GovBR link error: %s", exc)
        _flash_error("This Gov.br account is already linked to another user.")
        return redirect(url_for("user.me"))

    toolkit.h.flash_success(toolkit._("Gov.br account linked successfully."))
    return redirect(url_for("user.me"))


# ---------------------------------------------------------------------------
# unlink (POST only)
# ---------------------------------------------------------------------------

@govbr.route("/user/oidc/unlink", methods=["POST"])
def unlink():
    if not toolkit.c.user:
        return redirect(url_for("user.login"))

    import ckan.model as model
    ckan_user = model.User.get(toolkit.c.user)
    if ckan_user:
        service = ExternalUserService()
        service.unlink_account(ckan_user)
        toolkit.h.flash_success(toolkit._("Gov.br account unlinked."))

    return redirect(url_for("user.me"))


# ---------------------------------------------------------------------------
# followed items (for external users and any user)
# ---------------------------------------------------------------------------

@govbr.route("/user/<id>/followed")
def followed(id: str):
    import ckan.model as model
    from ckan.lib.base import render

    user_dict = toolkit.get_action("user_show")(
        {"ignore_auth": True},
        {"id": id, "include_plugin_extras": True},
    )
    followees = toolkit.get_action("followee_list")(
        {"ignore_auth": True},
        {"id": id},
    )
    user_obj = model.User.get(id)
    is_myself = toolkit.c.user and toolkit.c.user == user_dict.get("name")
    return render(
        "user/govbr_followed.html",
        extra_vars={
            "user_dict": user_dict,
            "user": user_dict,
            "followees": followees,
            "is_myself": is_myself,
            "is_sysadmin": getattr(user_obj, "sysadmin", False),
            "am_following": False,
        },
    )
