"""Testes de integração: fluxo GovBR OAuth2 para todos os tipos de usuário.

Usa o CKAN test client (Flask) com DB real e mocks apenas para a camada HTTP
externa (GovBRClient). Não requer Docker nem o mock-oauth2-server em execução.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest

import ckan.model as model
from ckanext.artesp_theme.govbr.models import UserInfo
from ckanext.artesp_theme.govbr.services import ExternalUserService
from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import auth_helpers

pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]

_MOCK_BASE_URL = "http://mock-oauth2-server:8888/oidc"


def _unique_sub():
    return uuid.uuid4().hex[:11]


def _userinfo(sub=None, name="Usuário GovBR", email=None):
    resolved_sub = sub or _unique_sub()
    resolved_email = email or f"govbr_{resolved_sub}@example.com"
    return UserInfo(
        sub=resolved_sub,
        name=name,
        email=resolved_email,
        email_verified=True,
    )


def _mock_config(base_url=_MOCK_BASE_URL):
    cfg = MagicMock()
    cfg.client_id = "mock-client"
    cfg.client_secret = "mock-secret"
    cfg.base_url = base_url
    cfg.scopes = ["openid", "email", "profile"]
    cfg.redirect_uri = "http://localhost:5000/user/oidc/callback"
    cfg.link_redirect_uri = "http://localhost:5000/user/oidc/link/callback"
    return cfg


def _make_mock_session(state, verifier):
    """Cria um substituto para flask.session que retorna state/verifier válidos."""
    store = {"govbr_state": state, "govbr_code_verifier": verifier}
    mock_sess = MagicMock()
    mock_sess.pop.side_effect = lambda k, default=None: store.pop(k, default)
    mock_sess.__setitem__ = MagicMock()
    mock_sess.__getitem__ = lambda self, k: store.get(k)
    mock_sess.modified = True
    return mock_sess


def _do_govbr_login(app, userinfo, state="test_state", verifier="test_verifier"):
    """Executa o fluxo completo de callback GovBR com state válido."""
    mock_sess = _make_mock_session(state, verifier)

    with (
        patch(
            "ckanext.artesp_theme.govbr.blueprint.GovBRConfig.from_ckan_config",
            return_value=_mock_config(),
        ),
        patch("ckanext.artesp_theme.govbr.blueprint.GovBRClient") as MockClient,
        patch("ckanext.artesp_theme.govbr.blueprint.session", new=mock_sess),
    ):
        client_instance = MockClient.return_value
        client_instance.exchange_code.return_value = "access_token_test"
        client_instance.get_userinfo.return_value = userinfo

        resp = app.get(
            f"/user/oidc/callback?code=authcode&state={state}",
            follow_redirects=False,
        )
    return resp


# ---------------------------------------------------------------------------
# Usuário externo novo (primeiro login GovBR)
# ---------------------------------------------------------------------------

class TestNovoUsuarioExterno:
    """Novo usuário GovBR: callback cria conta externa no CKAN."""

    def test_callback_cria_usuario_no_banco(self, app):
        sub = _unique_sub()
        userinfo = _userinfo(sub=sub)

        resp = _do_govbr_login(app, userinfo)

        assert resp.status_code in (302, 303), "Callback deve redirecionar após login"

        svc = ExternalUserService()
        ckan_user = svc.get_by_govbr_sub(sub)
        assert ckan_user is not None, "Usuário deve existir no banco após login"

    def test_usuario_criado_tem_user_type_external(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))

        svc = ExternalUserService()
        ckan_user = svc.get_by_govbr_sub(sub)
        extras = (ckan_user.plugin_extras or {}).get("artesp", {})
        assert extras.get("user_type") == "external"

    def test_is_external_user_retorna_true(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))

        svc = ExternalUserService()
        ckan_user = svc.get_by_govbr_sub(sub)
        assert auth_helpers.is_external_user(ckan_user) is True

    def test_govbr_sub_salvo_em_plugin_extras(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))

        svc = ExternalUserService()
        ckan_user = svc.get_by_govbr_sub(sub)
        extras = (ckan_user.plugin_extras or {}).get("artesp", {})
        assert extras.get("govbr_sub") == sub


# ---------------------------------------------------------------------------
# Usuário externo retornando (login repetido)
# ---------------------------------------------------------------------------

class TestUsuarioExternoRetornando:
    """Segundo login com mesmo sub reutiliza conta existente."""

    def test_segundo_login_reutiliza_mesma_conta(self, app):
        sub = _unique_sub()
        userinfo = _userinfo(sub=sub)

        _do_govbr_login(app, userinfo)
        _do_govbr_login(app, userinfo)

        svc = ExternalUserService()
        user = svc.get_by_govbr_sub(sub)
        assert user is not None

        # Verificar que só há um usuário com esse govbr_sub
        all_users = model.Session.query(model.User).filter(
            model.User.state == "active"
        ).all()
        matching = [
            u for u in all_users
            if (u.plugin_extras or {}).get("artesp", {}).get("govbr_sub") == sub
        ]
        assert len(matching) == 1, "Deve existir apenas um usuário para o mesmo sub"

    def test_usuario_retornando_continua_externo(self, app):
        sub = _unique_sub()
        userinfo = _userinfo(sub=sub)

        _do_govbr_login(app, userinfo)
        _do_govbr_login(app, userinfo)

        svc = ExternalUserService()
        ckan_user = svc.get_by_govbr_sub(sub)
        assert auth_helpers.is_external_user(ckan_user) is True


# ---------------------------------------------------------------------------
# Restrições de operações de escrita para usuário externo
# ---------------------------------------------------------------------------

class TestRestricoesUsuarioExterno:
    """Usuário externo é bloqueado em todas as operações de escrita."""

    def _ctx(self, ckan_user):
        return {
            "user": ckan_user.name,
            "auth_user_obj": ckan_user,
            "model": model,
        }

    def test_externo_nao_pode_criar_dataset(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))
        ckan_user = ExternalUserService().get_by_govbr_sub(sub)

        result = artesp_auth.package_create(self._ctx(ckan_user), {})
        assert result["success"] is False
        assert "External users" in result["msg"]

    def test_externo_nao_pode_criar_organizacao(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))
        ckan_user = ExternalUserService().get_by_govbr_sub(sub)

        result = artesp_auth.organization_create(self._ctx(ckan_user), {})
        assert result["success"] is False

    def test_externo_nao_pode_criar_recurso(self, app):
        sub = _unique_sub()
        _do_govbr_login(app, _userinfo(sub=sub))
        ckan_user = ExternalUserService().get_by_govbr_sub(sub)

        result = artesp_auth.resource_create(
            self._ctx(ckan_user),
            {"id": "r1", "package_id": "pkg1"},
        )
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Usuário interno (LDAP) — sem conta GovBR
# ---------------------------------------------------------------------------

class TestUsuarioInterno:
    """Usuário LDAP (interno) não é classificado como externo."""

    def test_usuario_sem_plugin_extras_nao_e_externo(self):
        user = MagicMock()
        user.plugin_extras = {}
        assert auth_helpers.is_external_user(user) is False

    def test_usuario_com_user_type_internal_nao_e_externo(self):
        user = MagicMock()
        user.plugin_extras = {"artesp": {"user_type": "internal"}}
        assert auth_helpers.is_external_user(user) is False

    def test_usuario_none_nao_e_externo(self):
        assert auth_helpers.is_external_user(None) is False


# ---------------------------------------------------------------------------
# Usuário LDAP com GovBR vinculado (linked)
# ---------------------------------------------------------------------------

class TestUsuarioInternoVinculado:
    """LDAP com govbr_sub vinculado continua sendo interno."""

    def test_usuario_ldap_vinculado_nao_e_externo(self):
        user = MagicMock()
        user.plugin_extras = {
            "artesp": {"user_type": "internal", "govbr_sub": "12345678901"}
        }
        assert auth_helpers.is_external_user(user) is False

    def test_link_callback_redireciona_sem_autenticacao(self, app):
        resp = app.get("/user/oidc/link/callback?code=c&state=wrong", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_link_route_redireciona_sem_autenticacao(self, app):
        resp = app.get("/user/oidc/link", follow_redirects=False)
        location = resp.headers.get("Location", "")
        assert "login" in location


# ---------------------------------------------------------------------------
# Validação de estado OAuth2 (segurança)
# ---------------------------------------------------------------------------

class TestSegurancaOAuth2:
    """Validação de state protege contra CSRF."""

    def test_callback_sem_state_redireciona(self, app):
        resp = app.get("/user/oidc/callback", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_callback_com_state_errado_redireciona(self, app):
        resp = app.get("/user/oidc/callback?code=c&state=wrong", follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_callback_sem_code_redireciona(self, app):
        mock_sess = _make_mock_session("st", "vf")
        with patch("ckanext.artesp_theme.govbr.blueprint.session", new=mock_sess):
            resp = app.get("/user/oidc/callback?state=st", follow_redirects=False)
        assert resp.status_code in (302, 303)
