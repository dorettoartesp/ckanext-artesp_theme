import os.path

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.artesp_theme.audit_model  # noqa: F401 — registers AuditEvent mapping
import ckanext.artesp_theme.helpers as helpers
import ckanext.artesp_theme.model  # noqa: F401 — registers DatasetRating imperative mapping
from ckanext.artesp_theme.controllers import artesp_theme
from ckanext.artesp_theme.govbr.blueprint import govbr as govbr_blueprint
from ckanext.artesp_theme.logic import action as artesp_action
from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import validators
from ckanext.artesp_theme.middleware import make_middleware


class ArtespThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IMiddleware)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IResourceController, inherit=True)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "artesp_theme")

    def declare_config_options(self, declaration, key):
        declaration.annotate("GovBR OAuth2 integration")
        declaration.declare_bool(key.ckanext.artesp.govbr.enabled).set_default(False)
        declaration.declare(key.ckanext.artesp.govbr.client_id).set_default("")
        declaration.declare(key.ckanext.artesp.govbr.client_secret).set_default("")
        declaration.declare(key.ckanext.artesp.govbr.base_url).set_default(
            "https://sso.staging.acesso.gov.br"
        )
        declaration.declare(key.ckanext.artesp.govbr.authorize_base_url).set_default("")
        declaration.declare(key.ckanext.artesp.govbr.redirect_uri).set_default("")
        declaration.declare(key.ckanext.artesp.govbr.link_redirect_uri).set_default("")
        declaration.declare(key.ckanext.artesp.govbr.scopes).set_default(
            "openid email profile"
        )
        declaration.annotate("Dataset rating comment captcha")
        declaration.declare(key.ckanext.artesp.rating.altcha_hmac_secret).set_default("")

    def get_auth_functions(self):
        return artesp_auth.get_auth_functions()

    def get_actions(self):
        return artesp_action.get_actions()

    def after_resource_create(self, context, resource):
        artesp_action.sync_unfold_resource_view(context, resource)

    def after_resource_update(self, context, resource):
        artesp_action.sync_unfold_resource_view(context, resource)

    def before_resource_show(self, resource):
        artesp_action.normalize_resource_for_unfold(resource)
        artesp_action.sync_unfold_resource_view({}, resource)
        return resource

    def get_blueprint(self):
        return [artesp_theme, govbr_blueprint]

    def get_helpers(self):
        return helpers.get_helpers()

    def get_validators(self):
        return validators.get_validators()

    def i18n_directory(self):
        return os.path.join(os.path.dirname(__file__), "i18n")

    def i18n_locales(self):
        return ["pt_BR"]

    def i18n_domain(self):
        return "ckanext-artesp_theme"

    def make_middleware(self, app, config):
        return make_middleware(app, config)

    def make_error_log_middleware(self, app, config):
        return app
