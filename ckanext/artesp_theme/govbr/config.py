from dataclasses import dataclass, field

from ckan.plugins import toolkit


@dataclass
class GovBRConfig:
    client_id: str
    client_secret: str
    base_url: str
    scopes: list
    redirect_uri: str
    link_redirect_uri: str
    logout_path: str = "logout"
    authorize_base_url: str = None

    @property
    def effective_authorize_base_url(self) -> str:
        return (self.authorize_base_url or self.base_url).rstrip("/")

    @classmethod
    def from_ckan_config(cls) -> "GovBRConfig":
        client_id = toolkit.config.get("ckanext.artesp.govbr.client_id", "")
        if not client_id:
            raise ValueError(
                "ckanext.artesp.govbr.client_id is required but not configured"
            )
        scopes_str = toolkit.config.get(
            "ckanext.artesp.govbr.scopes", "openid email profile"
        )
        authorize_base_url = toolkit.config.get(
            "ckanext.artesp.govbr.authorize_base_url", ""
        ).rstrip("/") or None
        logout_path = toolkit.config.get(
            "ckanext.artesp.govbr.logout_path", "logout"
        ).strip("/") or "logout"
        return cls(
            client_id=client_id,
            client_secret=toolkit.config.get(
                "ckanext.artesp.govbr.client_secret", ""
            ),
            base_url=toolkit.config.get(
                "ckanext.artesp.govbr.base_url",
                "https://sso.staging.acesso.gov.br",
            ).rstrip("/"),
            authorize_base_url=authorize_base_url,
            scopes=scopes_str.split(),
            redirect_uri=toolkit.config.get(
                "ckanext.artesp.govbr.redirect_uri", ""
            ),
            link_redirect_uri=toolkit.config.get(
                "ckanext.artesp.govbr.link_redirect_uri", ""
            ),
            logout_path=logout_path,
        )
