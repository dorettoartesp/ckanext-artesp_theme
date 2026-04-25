import ckanext.artesp_theme.plugin as plugin


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
