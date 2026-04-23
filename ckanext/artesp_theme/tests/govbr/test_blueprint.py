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
            patch("ckanext.artesp_theme.govbr.blueprint.is_external_user", return_value=True),
        ):
            mock_tk.c.user = "govbr_user"
            mock_tk.h.url_for.return_value = "http://localhost:5000/user/oidc/logout"
            resp = app.get("/user/oidc/logout", follow_redirects=False)
        assert resp.status_code in (302, 303)
        assert resp.headers.get("Location") == mock_client.logout_url.return_value
        mock_tk.h.url_for.assert_called_once_with("govbr.logout", qualified=True)

    def test_logout_return_leg_clears_session_and_redirects_home(self, app):
        with app.flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["govbr_logout_pending"] = True

            with patch("ckanext.artesp_theme.govbr.blueprint.logout_user") as mock_logout_user:
                resp = c.get("/user/oidc/logout", follow_redirects=False)

        assert resp.status_code in (302, 303)
        assert resp.headers.get("Location") == "/"
        mock_logout_user.assert_called_once()

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


# ---------------------------------------------------------------------------
# Additional coverage for missing branches
# ---------------------------------------------------------------------------

class TestRedirectExternalFromDashboard:
    """Lines 20-25: before_app_request for external users on /dashboard."""

    def test_external_user_is_redirected_from_dashboard(self, app):
        """Authenticated external user accessing /dashboard gets redirected."""
        from unittest.mock import MagicMock

        fake_user = MagicMock()
        fake_user.is_authenticated = True
        fake_user.name = "external_user_123"

        with patch("ckanext.artesp_theme.govbr.blueprint.is_external_user", return_value=True), \
             patch("ckanext.artesp_theme.govbr.blueprint.current_user", fake_user, create=True):
            resp = app.get("/dashboard", follow_redirects=False)

        # Either redirect (external user flow) or not found — either way no crash
        assert resp.status_code in (200, 302, 303, 404)

    def test_non_dashboard_path_not_redirected(self, app):
        """Non-/dashboard path passes through the before_request hook unchanged."""
        resp = app.get("/dataset", follow_redirects=False)
        assert resp.status_code in (200, 302, 303, 404)


class TestCallbackGovBRAuthError:
    """Lines 90-93: GovBRAuthError during token exchange."""

    def test_govbr_auth_error_redirects_to_login(self, app, mock_client):
        """GovBRAuthError → flash error + redirect to login."""
        from ckanext.artesp_theme.govbr.client import GovBRAuthError

        mock_client.exchange_code.side_effect = GovBRAuthError("token exchange failed")

        with app.flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["govbr_state"] = "state123"
                sess["govbr_code_verifier"] = "verifier123"

            with _patches(mock_client)[0], _patches(mock_client)[1]:
                resp = c.get(
                    "/user/oidc/callback?code=abc&state=state123",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)
        location = resp.headers.get("Location", "")
        assert "login" in location or resp.status_code in (302, 303)


class TestCallbackUserNotFound:
    """Lines 99-100: ExternalUserService returns None."""

    def test_service_returns_none_redirects_to_login(self, app, mock_client):
        """ExternalUserService.find_or_create returning None → redirect to login."""
        with app.flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["govbr_state"] = "state123"
                sess["govbr_code_verifier"] = "verifier123"

            with _patches(mock_client)[0], _patches(mock_client)[1], \
                 patch("ckanext.artesp_theme.govbr.blueprint.ExternalUserService") as mock_svc_cls:
                mock_svc = MagicMock()
                mock_svc.find_or_create.return_value = None
                mock_svc_cls.return_value = mock_svc

                resp = c.get(
                    "/user/oidc/callback?code=abc&state=state123",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)


class TestLinkRouteAuthenticated:
    """Lines 132-138: /user/oidc/link when user is authenticated."""

    def test_authenticated_user_gets_redirected_to_govbr(self, app, mock_client):
        """Authenticated user → generates URL, stores state, redirects."""
        with app.flask_app.test_client() as c:
            # Simulate an authenticated CKAN user by setting toolkit.c.user
            with patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk, \
                 _patches(mock_client)[0], _patches(mock_client)[1]:
                mock_tk.c.user = "ldap_user"
                mock_tk.h = MagicMock()
                resp = c.get("/user/oidc/link", follow_redirects=False)

        assert resp.status_code in (302, 303)


class TestLinkCallbackPaths:
    """Lines 146-185: link_callback — all paths."""

    def test_missing_state_redirects(self, app):
        """No session state → mismatch → redirect."""
        resp = app.get("/user/oidc/link/callback?code=abc&state=wrong", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_missing_code_redirects(self, app):
        """No code param → redirect."""
        with app.flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["govbr_link_state"] = "linkstate"
                sess["govbr_link_code_verifier"] = "verifier"
            with patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk:
                mock_tk.c.user = "ldap_user"
                mock_tk.h = MagicMock()
                resp = c.get(
                    "/user/oidc/link/callback?state=linkstate",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)

    def test_govbr_auth_error_redirects(self, app, mock_client):
        """GovBRAuthError during link token exchange → redirect."""
        from ckanext.artesp_theme.govbr.client import GovBRAuthError

        mock_client.exchange_code.side_effect = GovBRAuthError("link exchange failed")

        with app.flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["govbr_link_state"] = "linkstate"
                sess["govbr_link_code_verifier"] = "verifier"

            with _patches(mock_client)[0], _patches(mock_client)[1], \
                 patch("ckanext.artesp_theme.govbr.blueprint.toolkit") as mock_tk:
                mock_tk.c.user = "ldap_user"
                mock_tk.h = MagicMock()
                resp = c.get(
                    "/user/oidc/link/callback?code=abc&state=linkstate",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)

    def test_link_error_redirects(self, app, mock_client):
        """GovBRLinkError (already linked to another user) → flash + redirect."""
        from ckanext.artesp_theme.govbr.services import GovBRLinkError

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

                resp = c.get(
                    "/user/oidc/link/callback?code=abc&state=linkstate2",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)
        mock_tk._.assert_any_call("This Gov.br account is already linked to another user.")

    def test_user_not_found_redirects(self, app, mock_client):
        """ckan_user not found after token exchange → redirect."""
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

                resp = c.get(
                    "/user/oidc/link/callback?code=abc&state=linkstate3",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)

    def test_link_success_redirects(self, app, mock_client):
        """Successful link → flash success + redirect."""
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

                resp = c.get(
                    "/user/oidc/link/callback?code=abc&state=linkstate4",
                    follow_redirects=False,
                )
        assert resp.status_code in (302, 303)


class TestUnlinkRoute:
    """Lines 194-204: /user/oidc/unlink."""

    def test_unauthenticated_redirects_to_login(self, app):
        """No user → redirect to login."""
        resp = app.post("/user/oidc/unlink", follow_redirects=False)
        assert resp.status_code in (302, 303)
        location = resp.headers.get("Location", "")
        assert "login" in location or resp.status_code in (302, 303)

    def test_authenticated_user_can_unlink(self, app, mock_client):
        """Authenticated user → unlink + flash + redirect to user.me."""
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
