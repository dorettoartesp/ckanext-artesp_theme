import hashlib

import ckan.model as model
from ckan.plugins import toolkit

from .models import UserInfo


class GovBRLinkError(Exception):
    """Raised when a govbr_sub is already linked to another user."""


class ExternalUserService:
    """Manages the lifecycle of GovBR-authenticated CKAN users."""

    _ARTESP_KEY = "artesp"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def derive_username(self, sub: str) -> str:
        return "govbr_" + hashlib.sha256(sub.encode()).hexdigest()[:12]

    def find_or_create(self, userinfo: UserInfo):
        """Return an existing CKAN user for this govbr_sub or create a new one."""
        user = self._find_by_govbr_sub(userinfo.sub)
        if user is not None:
            return user

        user = self._find_by_email(userinfo.email) if userinfo.email and userinfo.email_verified else None
        if user is not None:
            extras = self._ensure_artesp_extras(user)
            existing_sub = extras.get("govbr_sub")
            if existing_sub and existing_sub != userinfo.sub:
                raise GovBRLinkError(
                    f"govbr_sub {userinfo.sub!r} is already linked to user {user.name!r}"
                )

            extras["user_type"] = "internal"
            extras["govbr_sub"] = userinfo.sub
            self._save_user(user)
            return user

        username = self.derive_username(userinfo.sub)
        user = self._find_by_name(username)
        if user is None:
            user = self._create_external_user(userinfo)

        self._set_artesp_extras(user, user_type="external", govbr_sub=userinfo.sub)
        self._save_user(user)
        return user

    def link_account(self, ckan_user, userinfo: UserInfo) -> None:
        """Store govbr_sub in plugin_extras of an existing (LDAP) user."""
        existing = self._find_by_govbr_sub(userinfo.sub)
        if existing is not None and existing.name != ckan_user.name:
            raise GovBRLinkError(
                f"govbr_sub {userinfo.sub!r} is already linked to user {existing.name!r}"
            )

        extras = self._ensure_artesp_extras(ckan_user)
        extras["govbr_sub"] = userinfo.sub
        self._save_user(ckan_user)

    def unlink_account(self, ckan_user) -> None:
        """Remove govbr_sub from plugin_extras."""
        extras = self._ensure_artesp_extras(ckan_user)
        extras.pop("govbr_sub", None)
        self._save_user(ckan_user)

    def get_by_govbr_sub(self, sub: str):
        """Public wrapper — returns CKAN user or None."""
        return self._find_by_govbr_sub(sub)

    # ------------------------------------------------------------------
    # Internal helpers (mockable in tests)
    # ------------------------------------------------------------------

    def _find_by_govbr_sub(self, sub: str):
        users = model.Session.query(model.User).filter(
            model.User.plugin_extras["artesp"]["govbr_sub"].astext == sub,
            model.User.state == "active",
        ).all()
        return users[0] if users else None

    def _find_by_name(self, name: str):
        return model.User.get(name)

    def _find_by_email(self, email: str):
        if not email:
            return None
        return (
            model.Session.query(model.User)
            .filter(model.User.email == email)
            .filter(model.User.state == "active")
            .one_or_none()
        )

    def _create_external_user(self, userinfo: UserInfo):
        username = self.derive_username(userinfo.sub)
        user_dict = toolkit.get_action("user_create")(
            {"ignore_auth": True},
            {
                "name": username,
                "email": userinfo.email or f"{username}@govbr.invalid",
                "password": self._random_password(),
                "fullname": userinfo.name,
                "plugin_extras": {
                    self._ARTESP_KEY: {
                        "user_type": "external",
                        "govbr_sub": userinfo.sub,
                    }
                },
            },
        )
        return model.User.get(user_dict["name"])

    def _save_user(self, user) -> None:
        model.Session.add(user)
        model.Session.commit()

    # ------------------------------------------------------------------
    # plugin_extras helpers
    # ------------------------------------------------------------------

    def _ensure_artesp_extras(self, user) -> dict:
        if not isinstance(user.plugin_extras, dict):
            user.plugin_extras = {}
        if self._ARTESP_KEY not in user.plugin_extras:
            user.plugin_extras[self._ARTESP_KEY] = {}
        return user.plugin_extras[self._ARTESP_KEY]

    def _set_artesp_extras(self, user, **kwargs) -> None:
        extras = self._ensure_artesp_extras(user)
        extras.update(kwargs)

    @staticmethod
    def _random_password() -> str:
        import secrets
        return secrets.token_urlsafe(32)
