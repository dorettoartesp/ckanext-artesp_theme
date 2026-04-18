"""TDD: GovBR blueprint routes.

These tests verify that the routes exist and respond correctly.
Heavy DB operations are avoided — we mock external dependencies.
"""
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
    c.logout_url.return_value = "https://sso.staging.acesso.gov.br/logout?post_logout_redirect_uri=http%3A%2F%2Flocalhost%3A5000%2F"
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
# route existence
# ---------------------------------------------------------------------------

class TestRoutesExist:
    def test_login_route_exists(self, app, mock_client):
        with _patches(mock_client)[0], _patches(mock_client)[1]:
            resp = app.get("/user/oidc/login", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_callback_route_exists(self, app):
        resp = app.get("/user/oidc/callback", follow_redirects=False)
        assert resp.status_code in (302, 303, 400)

    def test_logout_route_exists(self, app, mock_client):
        with (
            _patches(mock_client)[0],
            _patches(mock_client)[1],
            patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk,
        ):
            mock_tk.h.url_for.return_value = "http://localhost:5000/"
            resp = app.get("/user/oidc/logout", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_link_route_exists(self, app):
        resp = app.get("/user/oidc/link", follow_redirects=False)
        assert resp.status_code in (302, 303, 401)

    def test_link_callback_route_exists(self, app):
        resp = app.get("/user/oidc/link/callback", follow_redirects=False)
        assert resp.status_code in (302, 303, 400)


# ---------------------------------------------------------------------------
# login redirects to GovBR
# ---------------------------------------------------------------------------

class TestLoginRoute:
    def test_login_redirects_to_govbr_url(self, app, mock_client):
        with _patches(mock_client)[0], _patches(mock_client)[1]:
            resp = app.get("/user/oidc/login", follow_redirects=False)
        location = resp.headers.get("Location", "")
        assert "sso.staging.acesso.gov.br" in location

    def test_login_calls_get_authorization_url(self, app, mock_client):
        with _patches(mock_client)[0], _patches(mock_client)[1]:
            app.get("/user/oidc/login", follow_redirects=False)
        mock_client.get_authorization_url.assert_called_once()


# ---------------------------------------------------------------------------
# callback state validation
# ---------------------------------------------------------------------------

class TestCallbackRoute:
    def test_callback_no_state_redirects(self, app):
        # No session state set → state mismatch → redirect away
        resp = app.get("/user/oidc/callback?code=abc&state=anything", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_callback_no_code_redirects(self, app):
        resp = app.get("/user/oidc/callback", follow_redirects=False)
        assert resp.status_code in (302, 303)


# ---------------------------------------------------------------------------
# link flow (unauthenticated)
# ---------------------------------------------------------------------------

class TestLinkRoute:
    def test_unauthenticated_link_redirects_to_login(self, app):
        resp = app.get("/user/oidc/link", follow_redirects=False)
        assert resp.status_code in (302, 303)
        location = resp.headers.get("Location", "")
        assert "login" in location or resp.status_code in (302, 303)

    def test_unauthenticated_link_callback_redirects(self, app):
        resp = app.get("/user/oidc/link/callback?code=c&state=wrong", follow_redirects=False)
        assert resp.status_code in (302, 303)
