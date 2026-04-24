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


def test_plugin_delegates_resource_hooks_to_unfold_sync(monkeypatch):
    plugin_instance = plugin.ArtespThemePlugin()
    captured = []
    normalized_resource = {
        "id": "resource-id",
        "format": "rar",
    }

    def fake_sync(context, resource):
        captured.append((context, resource))

    def fake_normalize(resource):
        resource["format"] = "rar"
        return normalized_resource

    monkeypatch.setattr(plugin.artesp_action, "sync_unfold_resource_view", fake_sync)
    monkeypatch.setattr(plugin.artesp_action, "normalize_resource_for_unfold", fake_normalize)

    context = {"user": "creator"}
    resource = {"id": "resource-id", "format": "application/vnd.rar"}

    plugin_instance.after_resource_create(context, resource)
    plugin_instance.after_resource_update(context, resource)
    returned_resource = plugin_instance.before_resource_show(resource)

    assert captured == [
        (context, resource),
        (context, resource),
        ({}, resource),
    ]
    assert returned_resource == resource
