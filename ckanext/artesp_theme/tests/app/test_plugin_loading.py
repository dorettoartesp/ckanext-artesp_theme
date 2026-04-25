import ckan.plugins as plugins
import pytest

import ckanext.artesp_theme.plugin as plugin
import ckan.plugins.toolkit as toolkit


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_plugin_loads_and_registers_expected_interfaces():
    assert plugins.plugin_loaded("artesp_theme")

    plugin_instance = plugin.ArtespThemePlugin()
    auth_functions = plugin_instance.get_auth_functions()
    actions = plugin_instance.get_actions()

    assert "package_create" in auth_functions
    assert "package_update" in auth_functions
    assert "package_collaborator_create" in auth_functions
    assert "artesp_theme_get_sum" in actions

    subscriptions = plugin_instance.get_signal_subscriptions()

    assert toolkit.signals.action_succeeded in subscriptions
    assert toolkit.signals.user_logged_in in subscriptions
    assert toolkit.signals.user_logged_out in subscriptions
    assert toolkit.signals.failed_login in subscriptions
