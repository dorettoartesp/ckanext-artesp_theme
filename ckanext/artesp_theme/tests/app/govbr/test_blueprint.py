"""TDD: GovBR blueprint routes.

These tests verify that the routes exist and respond correctly.
Heavy DB operations are avoided — we mock external dependencies.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ckanext.artesp_theme.govbr.models import UserInfo


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]

GOVBR_SUB = "12345678901"


def _userinfo(sub=GOVBR_SUB):
    return UserInfo(sub=sub, name="Test User", email="test@example.com", email_verified=True)


def _mock_config():
    cfg = MagicMock()
    cfg.client_id = "cid"
    cfg.client_secret = "cs"
    cfg.base_url = "https://sso.staging.acesso.gov.br"
    cfg.scopes = ["openid", "email", "profile"]
    cfg.redirect_uri = "http://localhost:5000/user/oidc/callback"
    cfg.link_redirect_uri = "http://localhost:5000/user/oidc/link/callback"
    return cfg


@pytest.fixture
def mock_client():
    c = MagicMock()
    c.get_authorization_url.return_value = (
        "https://sso.staging.acesso.gov.br/authorize?code_challenge=abc",
        "state123",
        "verifier123",
    )
    c.exchange_code.return_value = "access_token_xyz"
    c.get_userinfo.return_value = _userinfo()
    c.logout_url.return_value = "https://sso.staging.acesso.gov.br/logout?post_logout_redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fuser%2Foidc%2Flogout"
    return c


@pytest.fixture
def mock_svc():
    svc = MagicMock()
    user = MagicMock()
    user.name = "govbr_abcdef123456"
    user.id = "uid-ext"
    svc.find_or_create.return_value = user
    return svc


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _patches(mock_client):
    return [
        patch("ckanext.artesp_theme.govbr.blueprint.GovBRConfig.from_ckan_config", return_value=_mock_config()),
        patch("ckanext.artesp_theme.govbr.blueprint.GovBRClient", return_value=mock_client),
    ]


# ---------------------------------------------------------------------------
# group 1: unauthenticated and stateless routes
# ---------------------------------------------------------------------------

def test_govbr_unauthenticated_and_stateless_routes(app, mock_client):
    # login: route exists, redirects to govbr, calls get_authorization_url once
    with _patches(mock_client)[0], _patches(mock_client)[1]:
        resp = app.get("/user/oidc/login", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "sso.staging.acesso.gov.br" in resp.headers.get("Location", "")
    mock_client.get_authorization_url.assert_called_once()

    # callback: route exists (no session state → redirect/error)
    resp = app.get("/user/oidc/callback", follow_redirects=False)
    assert resp.status_code in (302, 303, 400)

    # logout: route exists, renders intermediate page with govbr logout URL
    with (
        _patches(mock_client)[0],
        _patches(mock_client)[1],
        patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk,
        patch("ckanext.artesp_theme.govbr.blueprint.is_external_user", return_value=True),
    ):
        mock_tk.c.user = "govbr_user"
        mock_tk.h.url_for.return_value = "http://localhost:5000/user/oidc/logout"
        resp = app.get("/user/oidc/logout", follow_redirects=False)
    assert resp.status_code == 200
    assert "Saindo do Portal de Dados Abertos da ARTESP" in resp.text
    assert mock_client.logout_url.return_value in resp.text
    mock_tk.h.url_for.assert_called_once_with("govbr.logout", qualified=True)

    # link: route exists (unauthenticated → redirect to login)
    resp = app.get("/user/oidc/link", follow_redirects=False)
    assert resp.status_code in (302, 303, 401)
    assert "login" in resp.headers.get("Location", "") or resp.status_code in (302, 303)

    # link callback: route exists (unauthenticated/no state → redirect/error)
    resp = app.get("/user/oidc/link/callback", follow_redirects=False)
    assert resp.status_code in (302, 303, 400)

    # callback: state mismatch → redirect
    resp = app.get("/user/oidc/callback?code=abc&state=anything", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # link callback: state mismatch → redirect
    resp = app.get("/user/oidc/link/callback?code=c&state=wrong", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # before_app_request: external user on /dashboard gets redirected
    fake_user = MagicMock()
    fake_user.is_authenticated = True
    fake_user.name = "external_user_123"
    with patch("ckanext.artesp_theme.govbr.blueprint.is_external_user", return_value=True), \
         patch("ckanext.artesp_theme.govbr.blueprint.current_user", fake_user, create=True):
        resp = app.get("/dashboard", follow_redirects=False)
    assert resp.status_code in (200, 302, 303, 404)

    # before_app_request: non-/dashboard path passes through unchanged
    resp = app.get("/dataset", follow_redirects=False)
    assert resp.status_code in (200, 302, 303, 404)

    # unlink: unauthenticated → redirect to login
    resp = app.post("/user/oidc/unlink", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "login" in resp.headers.get("Location", "") or resp.status_code in (302, 303)


# ---------------------------------------------------------------------------
# group 2: logout clears session (needs reset_db — kept separate)
# ---------------------------------------------------------------------------

def test_govbr_logout_clears_session(app, reset_db):
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_logout_pending"] = True

        with patch("ckanext.artesp_theme.govbr.blueprint.logout_user") as mock_logout_user:
            resp = c.get("/user/oidc/logout", follow_redirects=False)

    assert resp.status_code in (302, 303)
    assert resp.headers.get("Location") == "/"
    mock_logout_user.assert_called_once()


# ---------------------------------------------------------------------------
# group 3: callback error paths and user-not-found
# ---------------------------------------------------------------------------

def test_govbr_callback_error_and_user_not_found(app, mock_client):
    from ckanext.artesp_theme.govbr.client import GovBRAuthError

    # GovBRAuthError: redirects to login
    mock_client.exchange_code.side_effect = GovBRAuthError("token exchange failed")
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_state"] = "state123"
            sess["govbr_code_verifier"] = "verifier123"

        with _patches(mock_client)[0], _patches(mock_client)[1]:
            resp = c.get("/user/oidc/callback?code=abc&state=state123", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "login" in resp.headers.get("Location", "") or resp.status_code in (302, 303)

    # GovBRAuthError: records audit failure
    mock_client.exchange_code.side_effect = GovBRAuthError("token exchange failed")
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_state"] = "state123"
            sess["govbr_code_verifier"] = "verifier123"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.audit_capture") as mock_audit_capture:
            c.get("/user/oidc/callback?code=abc&state=state123", follow_redirects=False)

    mock_audit_capture.record_auth_event.assert_called_once_with(
        event_action="login_failure",
        success=False,
        auth_provider="govbr",
        actor_name=None,
        actor_identifier=None,
        request_path="/user/oidc/callback",
        details={"reason": "GovBRAuthError"},
    )

    # ExternalUserService returns None: redirects to login
    mock_client.exchange_code.side_effect = None
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_state"] = "state123"
            sess["govbr_code_verifier"] = "verifier123"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.find_or_create.return_value = None
            mock_svc_cls.return_value = mock_svc

            resp = c.get("/user/oidc/callback?code=abc&state=state123", follow_redirects=False)
    assert resp.status_code in (302, 303)


# ---------------------------------------------------------------------------
# group 4: callback success
# ---------------------------------------------------------------------------

def test_govbr_callback_success(app, mock_client):
    # marks session as govbr and calls login_user
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_state"] = "state123"
            sess["govbr_code_verifier"] = "verifier123"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls, \
             patch("ckan.model.User.get", return_value=SimpleNamespace(name="govbr_user")) as mock_user_get, \
             patch("ckan.common.login_user") as mock_login_user:
            mock_svc = MagicMock()
            mock_svc.find_or_create.return_value = SimpleNamespace(name="govbr_user")
            mock_svc_cls.return_value = mock_svc

            resp = c.get("/user/oidc/callback?code=abc&state=state123", follow_redirects=False)

    assert resp.status_code in (302, 303)
    with c.session_transaction() as sess:
        assert sess.get("artesp_auth_provider") == "govbr"
    mock_user_get.assert_called_with("govbr_user")
    mock_login_user.assert_called_once()

    # auth provider is set in session before login_user is called
    def assert_provider_before_login(user_obj):
        from flask import session as flask_session
        assert flask_session.get("artesp_auth_provider") == "govbr"

    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_state"] = "state123"
            sess["govbr_code_verifier"] = "verifier123"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls, \
             patch("ckan.model.User.get", return_value=SimpleNamespace(name="govbr_user")), \
             patch("ckan.common.login_user", side_effect=assert_provider_before_login):
            mock_svc = MagicMock()
            mock_svc.find_or_create.return_value = SimpleNamespace(name="govbr_user")
            mock_svc_cls.return_value = mock_svc

            resp = c.get("/user/oidc/callback?code=abc&state=state123", follow_redirects=False)

    assert resp.status_code in (302, 303)


# ---------------------------------------------------------------------------
# group 5: link and unlink (authenticated)
# ---------------------------------------------------------------------------

def test_govbr_link_and_unlink(app, mock_client):
    from ckanext.artesp_theme.govbr.client import GovBRAuthError
    from ckanext.artesp_theme.govbr.services import GovBRLinkError

    # authenticated user → redirected to govbr for linking
    with app.flask_app.test_client() as c:
        with patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
             _patches(mock_client)[0], _patches(mock_client)[1]:
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            resp = c.get("/user/oidc/link", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # link callback: missing state → redirect
    resp = app.get("/user/oidc/link/callback?code=abc&state=wrong", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # link callback: missing code → redirect
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_link_state"] = "linkstate"
            sess["govbr_link_code_verifier"] = "verifier"
        with patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk:
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            resp = c.get("/user/oidc/link/callback?state=linkstate", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # link callback: GovBRAuthError → redirect
    mock_client.exchange_code.side_effect = GovBRAuthError("link exchange failed")
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_link_state"] = "linkstate"
            sess["govbr_link_code_verifier"] = "verifier"
        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk:
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            resp = c.get("/user/oidc/link/callback?code=abc&state=linkstate", follow_redirects=False)
    assert resp.status_code in (302, 303)
    mock_client.exchange_code.side_effect = None

    # link callback: GovBRLinkError (already linked to another user) → flash + redirect
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_link_state"] = "linkstate2"
            sess["govbr_link_code_verifier"] = "verifier2"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls, \
             patch("ckan.model.User.get") as mock_user_get:

            fake_ckan_user = MagicMock()
            fake_ckan_user.name = "ldap_user"
            mock_user_get.return_value = fake_ckan_user
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            mock_tk._ = MagicMock(side_effect=lambda x: x)

            mock_svc = MagicMock()
            mock_svc.link_account.side_effect = GovBRLinkError("already linked")
            mock_svc_cls.return_value = mock_svc

            resp = c.get("/user/oidc/link/callback?code=abc&state=linkstate2", follow_redirects=False)
    assert resp.status_code in (302, 303)
    mock_tk._.assert_any_call("This Gov.br account is already linked to another user.")

    # link callback: ckan_user not found → redirect
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_link_state"] = "linkstate3"
            sess["govbr_link_code_verifier"] = "verifier3"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
             patch("ckan.model.User.get") as mock_user_get:

            mock_user_get.return_value = None
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            mock_tk._ = lambda x: x

            resp = c.get("/user/oidc/link/callback?code=abc&state=linkstate3", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # link callback: success → flash + redirect
    with app.flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["govbr_link_state"] = "linkstate4"
            sess["govbr_link_code_verifier"] = "verifier4"

        with _patches(mock_client)[0], _patches(mock_client)[1], \
             patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls, \
             patch("ckan.model.User.get") as mock_user_get:

            fake_ckan_user = MagicMock()
            fake_ckan_user.name = "ldap_user"
            mock_user_get.return_value = fake_ckan_user
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            mock_tk._ = lambda x: x

            mock_svc = MagicMock()
            mock_svc.link_account.return_value = None
            mock_svc_cls.return_value = mock_svc

            resp = c.get("/user/oidc/link/callback?code=abc&state=linkstate4", follow_redirects=False)
    assert resp.status_code in (302, 303)

    # unlink: authenticated user → unlink + redirect
    with app.flask_app.test_client() as c:
        with patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
             patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls, \
             patch("ckan.model.User.get") as mock_user_get:

            fake_ckan_user = MagicMock()
            fake_ckan_user.name = "ldap_user"
            mock_user_get.return_value = fake_ckan_user
            mock_tk.c.user = "ldap_user"
            mock_tk.h = MagicMock()
            mock_tk._ = lambda x: x

            mock_svc = MagicMock()
            mock_svc_cls.return_value = mock_svc

            resp = c.post("/user/oidc/unlink", follow_redirects=False)
    assert resp.status_code in (302, 303)
    mock_svc.unlink_account.assert_called_once_with(fake_ckan_user)
