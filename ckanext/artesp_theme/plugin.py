import os.path

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.artesp_theme.helpers as helpers
from ckanext.artesp_theme.controllers import artesp_theme
from ckanext.artesp_theme.logic import action as artesp_action
from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import validators
from ckanext.artesp_theme.middleware import make_middleware


class ArtespThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IMiddleware)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "artesp_theme")

    def get_auth_functions(self):
        return artesp_auth.get_auth_functions()

    def get_actions(self):
        return artesp_action.get_actions()

    def get_blueprint(self):
        return [artesp_theme]

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
