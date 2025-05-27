import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import os.path
from ckanext.artesp_theme.middleware import make_middleware


# import ckanext.artesp_theme.cli as cli
import ckanext.artesp_theme.helpers as helpers
from ckanext.artesp_theme.controllers import artesp_theme
from ckanext.artesp_theme.logic import validators


class ArtespThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IMiddleware)
    plugins.implements(plugins.IValidators)

    # plugins.implements(plugins.IAuthFunctions)
    # plugins.implements(plugins.IActions)
    # plugins.implements(plugins.IClick)


    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "artesp_theme")


    # IAuthFunctions

    # def get_auth_functions(self):
    #     return auth.get_auth_functions()

    # IActions

    # def get_actions(self):
    #     return action.get_actions()

    # IBlueprint

    def get_blueprint(self):
        return [artesp_theme]

    # IClick

    # def get_commands(self):
    #     return cli.get_commands()

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IValidators

    def get_validators(self):
        return validators.get_validators()

    # ITranslation

    def i18n_directory(self):
        """Return the path to the translation directory."""
        return os.path.join(os.path.dirname(__file__), 'i18n')

    def i18n_locales(self):
        """Return a list of available locales."""
        return ['pt_BR']

    def i18n_domain(self):
        """Return the gettext domain for this plugin."""
        return 'ckanext-artesp_theme'

    # IMiddleware

    def make_middleware(self, app, config):
        """
        Return a WSGI middleware to fix double-encoded Font Awesome icons.
        """
        return make_middleware(app, config)

    def make_error_log_middleware(self, app, config):
        """
        Return a WSGI middleware for error logging.

        Args:
            app: The WSGI application
            config: The configuration dictionary (not used)

        Returns:
            The WSGI application (unchanged)
        """
        # config parameter is required by CKAN but not used
        return app

