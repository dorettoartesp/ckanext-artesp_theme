import base64
import hashlib
import secrets
import urllib.parse

import requests

from .config import GovBRConfig
from .models import UserInfo


class GovBRAuthError(Exception):
    """Raised when GovBR returns an auth error."""


class GovBRClient:
    """Handles the GovBR Authorization Code + PKCE/S256 OAuth2 flow.

    No CKAN imports — purely HTTP.
    """

    def __init__(self, config: GovBRConfig) -> None:
        self._config = config

    def get_authorization_url(self, redirect_uri: str) -> tuple:
        """Return (authorization_url, state, code_verifier)."""
        code_verifier = secrets.token_urlsafe(96)
        code_challenge = self._s256(code_verifier)
        state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self._config.client_id,
            "scope": " ".join(self._config.scopes),
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": secrets.token_urlsafe(16),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        url = f"{self._config.effective_authorize_base_url}/authorize?{urllib.parse.urlencode(params)}"
        return url, state, code_verifier

    def exchange_code(
        self,
        code: str,
        state: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> str:
        """Exchange authorization code for access_token. Raises GovBRAuthError on failure."""
        response = requests.post(
            f"{self._config.base_url}/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            auth=(self._config.client_id, self._config.client_secret),
        )
        if response.status_code != 200:
            raise GovBRAuthError(
                f"Token exchange failed: {response.status_code} {response.text}"
            )
        return response.json()["access_token"]

    def get_userinfo(self, access_token: str) -> UserInfo:
        """Fetch user info from GovBR /userinfo/. Raises GovBRAuthError on failure."""
        response = requests.get(
            f"{self._config.base_url}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise GovBRAuthError(
                f"Userinfo failed: {response.status_code} {response.text}"
            )
        data = response.json()
        return UserInfo(
            sub=data["sub"],
            name=data.get("name", ""),
            email=data.get("email", ""),
            email_verified=data.get("email_verified", False),
        )

    def logout_url(self, post_logout_redirect_uri: str) -> str:
        """Build GovBR logout URL with post-logout redirect."""
        params = urllib.parse.urlencode(
            {"post_logout_redirect_uri": post_logout_redirect_uri}
        )
        return f"{self._config.base_url}/logout?{params}"

    @staticmethod
    def _s256(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
