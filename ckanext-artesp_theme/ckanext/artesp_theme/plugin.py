import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


# import ckanext.artesp_theme.cli as cli
import ckanext.artesp_theme.helpers as helpers
from ckanext.artesp_theme.controllers import artesp_theme
# from ckanext.artesp_theme.logic import (
#     action, auth, validators
# )


class ArtespThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)

    # plugins.implements(plugins.IAuthFunctions)
    # plugins.implements(plugins.IActions)
    # plugins.implements(plugins.IClick)
    # plugins.implements(plugins.IValidators)


    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "artesp_assets")


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

    # def get_validators(self):
    #     return validators.get_validators()

