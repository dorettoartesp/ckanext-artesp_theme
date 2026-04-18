"""TDD: GovBRConfig, GovBRClient, UserInfo."""
import base64
import hashlib
import json
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from ckanext.artesp_theme.govbr.config import GovBRConfig
from ckanext.artesp_theme.govbr.client import GovBRClient, GovBRAuthError
from ckanext.artesp_theme.govbr.models import UserInfo


@pytest.fixture
def config():
    return GovBRConfig(
        client_id="test_client",
        client_secret="test_secret",
        base_url="https://sso.staging.acesso.gov.br",
        scopes=["openid", "email", "profile"],
        redirect_uri="http://localhost:5000/user/govbr/callback",
        link_redirect_uri="http://localhost:5000/user/govbr/link/callback",
    )


@pytest.fixture
def client(config):
    return GovBRClient(config)


class TestGovBRConfig:
    def test_fields_stored(self, config):
        assert config.client_id == "test_client"
        assert config.base_url == "https://sso.staging.acesso.gov.br"
        assert config.scopes == ["openid", "email", "profile"]

    def test_from_ckan_config_raises_if_client_id_empty(self):
        with patch(
            "ckanext.artesp_theme.govbr.config.toolkit"
        ) as mock_toolkit:
            mock_toolkit.config = {
                "ckanext.artesp.govbr.client_id": "",
                "ckanext.artesp.govbr.client_secret": "s",
                "ckanext.artesp.govbr.base_url": "https://sso.staging.acesso.gov.br",
                "ckanext.artesp.govbr.redirect_uri": "http://localhost/cb",
                "ckanext.artesp.govbr.link_redirect_uri": "http://localhost/link/cb",
                "ckanext.artesp.govbr.scopes": "openid email profile",
            }
            with pytest.raises(ValueError, match="client_id"):
                GovBRConfig.from_ckan_config()

    def test_from_ckan_config_parses_scopes(self):
        with patch(
            "ckanext.artesp_theme.govbr.config.toolkit"
        ) as mock_toolkit:
            mock_toolkit.config = {
                "ckanext.artesp.govbr.client_id": "cid",
                "ckanext.artesp.govbr.client_secret": "cs",
                "ckanext.artesp.govbr.base_url": "https://sso.staging.acesso.gov.br",
                "ckanext.artesp.govbr.redirect_uri": "http://localhost/cb",
                "ckanext.artesp.govbr.link_redirect_uri": "http://localhost/link/cb",
                "ckanext.artesp.govbr.scopes": "openid email profile",
            }
            cfg = GovBRConfig.from_ckan_config()
            assert cfg.scopes == ["openid", "email", "profile"]


class TestPKCE:
    def test_get_authorization_url_returns_three_values(self, client):
        url, state, verifier = client.get_authorization_url(
            "http://localhost/cb"
        )
        assert url.startswith("https://sso.staging.acesso.gov.br/authorize")
        assert state
        assert verifier

    def test_code_verifier_length(self, client):
        _, _, verifier = client.get_authorization_url("http://localhost/cb")
        assert 43 <= len(verifier) <= 128

    def test_code_challenge_is_s256(self, client):
        url, state, verifier = client.get_authorization_url(
            "http://localhost/cb"
        )
        digest = hashlib.sha256(verifier.encode()).digest()
        expected_challenge = (
            base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        )
        assert f"code_challenge={expected_challenge}" in url
        assert "code_challenge_method=S256" in url

    def test_state_included_in_url(self, client):
        url, state, _ = client.get_authorization_url("http://localhost/cb")
        assert f"state={state}" in url

    def test_redirect_uri_included_in_url(self, client):
        url, _, _ = client.get_authorization_url("http://localhost/cb")
        assert "redirect_uri=" in url

    def test_scopes_included_in_url(self, client):
        url, _, _ = client.get_authorization_url("http://localhost/cb")
        assert "openid" in url


class TestExchangeCode:
    def test_returns_access_token_on_success(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "tok123",
            "token_type": "Bearer",
        }
        with patch("requests.post", return_value=mock_response):
            token = client.exchange_code(
                code="code123",
                state="state123",
                code_verifier="verifier123",
                redirect_uri="http://localhost/cb",
            )
        assert token == "tok123"

    def test_raises_on_http_error(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(GovBRAuthError):
                client.exchange_code("code", "state", "verifier", "http://localhost/cb")

    def test_sends_code_verifier_not_challenge(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "tok"}
        with patch("requests.post", return_value=mock_response) as mock_post:
            client.exchange_code("code", "state", "verifier123", "http://localhost/cb")
            call_kwargs = mock_post.call_args
            data = call_kwargs[1].get("data", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
            assert data.get("code_verifier") == "verifier123"
            assert "code_challenge" not in data


class TestGetUserinfo:
    def test_returns_userinfo_dataclass(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "12345678901",
            "name": "João Silva",
            "email": "joao@example.com",
            "email_verified": True,
        }
        with patch("requests.get", return_value=mock_response):
            info = client.get_userinfo("tok123")
        assert isinstance(info, UserInfo)
        assert info.sub == "12345678901"
        assert info.name == "João Silva"
        assert info.email == "joao@example.com"
        assert info.email_verified is True

    def test_raises_on_http_error(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_token"}
        with patch("requests.get", return_value=mock_response):
            with pytest.raises(GovBRAuthError):
                client.get_userinfo("bad_token")

    def test_bearer_token_in_header(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "11111111111",
            "name": "Test",
            "email": "t@t.com",
        }
        with patch("requests.get", return_value=mock_response) as mock_get:
            client.get_userinfo("mytoken")
            headers = mock_get.call_args[1].get("headers", {})
            assert headers.get("Authorization") == "Bearer mytoken"


class TestLogoutUrl:
    def test_logout_url_contains_govbr_endpoint(self, client):
        url = client.logout_url("http://localhost:5000/")
        assert "sso.staging.acesso.gov.br/logout" in url

    def test_logout_url_contains_redirect(self, client):
        url = client.logout_url("http://localhost:5000/")
        assert "post_logout_redirect_uri" in url


class TestUserInfo:
    def test_frozen_dataclass(self):
        info = UserInfo(sub="123", name="Test", email="t@t.com")
        with pytest.raises((AttributeError, TypeError)):
            info.sub = "456"

    def test_email_verified_defaults_false(self):
        info = UserInfo(sub="123", name="Test", email="t@t.com")
        assert info.email_verified is False
