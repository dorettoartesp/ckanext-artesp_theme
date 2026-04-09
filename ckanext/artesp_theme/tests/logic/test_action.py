"""Tests for action.py."""

import ckan.model as model

from ckanext.artesp_theme.logic import action as artesp_action


def test_artesp_theme_get_sum():
    result = artesp_action.artesp_theme_get_sum(
        {"ignore_auth": True},
        {"left": 10, "right": 30},
    )
    assert result["sum"] == 40


def test_package_collaborator_create_uses_normalized_payload(monkeypatch):
    captured = {}
    normalized_data = {
        "id": "dataset-id",
        "user_id": "user-id",
        "capacity": "editor",
    }

    def fake_normalize(context, data_dict):
        captured["normalize"] = (context.copy(), dict(data_dict))
        return dict(normalized_data)

    def fake_check_access(action_name, context, data_dict):
        captured["check_access"] = (action_name, context.copy(), dict(data_dict))

    def fake_core_action(context, data_dict):
        captured["core_action"] = (context.copy(), dict(data_dict))
        return {"ok": True}

    monkeypatch.setattr(
        artesp_action.auth_helpers,
        "normalize_package_collaborator_create_data",
        fake_normalize,
    )
    monkeypatch.setattr(artesp_action.tk, "check_access", fake_check_access)
    monkeypatch.setattr(
        artesp_action,
        "core_package_collaborator_create",
        fake_core_action,
    )

    result = artesp_action.package_collaborator_create(
        {"user": "creator"},
        {"id": "dataset-id", "username": "joao.silva"},
    )

    assert result == {"ok": True}
    assert captured["check_access"][0] == "package_collaborator_create"
    assert captured["check_access"][2] == normalized_data
    assert captured["core_action"][0]["ignore_auth"] is True
    assert captured["core_action"][1] == normalized_data


def test_group_create_syncs_existing_ldap_users(monkeypatch):
    captured = {}
    created_group = {"id": "group-id", "name": "group-name"}

    def fake_check_access(action_name, context, data_dict):
        captured["check_access"] = (action_name, context.copy(), dict(data_dict))

    def fake_core_action(context, data_dict):
        captured["core_action"] = (context.copy(), dict(data_dict))
        return dict(created_group)

    def fake_sync(group_identifier):
        captured["sync"] = group_identifier
        return 2

    monkeypatch.setattr(artesp_action.tk, "check_access", fake_check_access)
    monkeypatch.setattr(artesp_action, "core_group_create", fake_core_action)
    monkeypatch.setattr(
        artesp_action.auth_helpers,
        "ensure_all_ldap_users_in_group",
        fake_sync,
    )

    result = artesp_action.group_create(
        {"user": "ckan_admin"},
        {"name": "grupo-operacional", "title": "Grupo Operacional"},
    )

    assert result == created_group
    assert captured["check_access"][0] == "group_create"
    assert captured["core_action"][0]["ignore_auth"] is True
    assert captured["sync"] == "group-id"


def test_sync_unfold_resource_view_creates_view_for_supported_formats(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(artesp_action.plugins, "plugin_loaded", lambda name: name == "unfold")
    monkeypatch.setattr(
        artesp_action,
        "UNFOLD_ADAPTERS",
        {"rar": object()},
    )

    def fake_get_action(action_name):
        if action_name == "resource_view_list":
            return lambda context, data_dict: []
        if action_name == "resource_view_create":
            def _create(context, data_dict):
                captured["create"] = (context.copy(), dict(data_dict))
                return {"id": "view-id", "view_type": data_dict["view_type"]}
            return _create
        raise AssertionError(action_name)

    monkeypatch.setattr(artesp_action.tk, "get_action", fake_get_action)

    artesp_action.sync_unfold_resource_view(
        {"user": "creator"},
        {
            "id": "resource-id",
            "format": "application/vnd.rar",
            "mimetype": "application/vnd.rar",
            "name": "arquivo.rar",
        },
    )

    assert captured["create"][0]["ignore_auth"] is True
    assert captured["create"][0]["model"] is model
    assert captured["create"][1] == {
        "resource_id": "resource-id",
        "view_type": "unfold_view",
        "title": "Unfold",
    }


def test_detect_unfold_format_uses_mimetype_and_filename_fallbacks(monkeypatch):
    monkeypatch.setattr(
        artesp_action,
        "UNFOLD_ADAPTERS",
        {"rar": object(), "tar.gz": object()},
    )
    monkeypatch.setattr(
        artesp_action,
        "UNFOLD_ARCHIVE_EXTENSIONS",
        ("tar.gz", "rar"),
    )

    assert (
        artesp_action._detect_unfold_format(
            {"format": "application/vnd.rar", "name": "arquivo-sem-extensao"}
        )
        == "rar"
    )
    assert (
        artesp_action._detect_unfold_format(
            {"name": "pacote.tar.gz", "format": ""}
        )
        == "tar.gz"
    )


def test_normalize_resource_for_unfold_rewrites_supported_mimetype(monkeypatch):
    monkeypatch.setattr(
        artesp_action,
        "UNFOLD_ADAPTERS",
        {"rar": object()},
    )

    resource = {
        "id": "resource-id",
        "format": "application/vnd.rar",
        "mimetype": "application/vnd.rar",
        "name": "arquivo.rar",
    }

    normalized = artesp_action.normalize_resource_for_unfold(resource)

    assert normalized is resource
    assert resource["format"] == "rar"


def test_sync_unfold_resource_view_deletes_stale_or_duplicate_views(monkeypatch):
    captured = {"deleted_ids": []}

    monkeypatch.setattr(artesp_action.plugins, "plugin_loaded", lambda name: name == "unfold")
    monkeypatch.setattr(
        artesp_action,
        "UNFOLD_ADAPTERS",
        {"zip": object()},
    )

    def fake_get_action(action_name):
        if action_name == "resource_view_list":
            return lambda context, data_dict: [
                {"id": "keep-view", "view_type": "unfold_view"},
                {"id": "drop-view", "view_type": "unfold_view"},
            ]
        if action_name == "resource_view_delete":
            def _delete(context, data_dict):
                captured["deleted_ids"].append(data_dict["id"])
                return {"success": True}
            return _delete
        raise AssertionError(action_name)

    monkeypatch.setattr(artesp_action.tk, "get_action", fake_get_action)

    artesp_action.sync_unfold_resource_view(
        {"user": "creator"},
        {"id": "resource-id", "format": "zip"},
    )

    assert captured["deleted_ids"] == ["drop-view"]

    captured["deleted_ids"].clear()

    def fake_get_action_unsupported(action_name):
        if action_name == "resource_view_list":
            return lambda context, data_dict: [
                {"id": "drop-view", "view_type": "unfold_view"},
            ]
        if action_name == "resource_view_delete":
            def _delete(context, data_dict):
                captured["deleted_ids"].append(data_dict["id"])
                return {"success": True}
            return _delete
        raise AssertionError(action_name)

    monkeypatch.setattr(artesp_action.tk, "get_action", fake_get_action_unsupported)

    artesp_action.sync_unfold_resource_view(
        {"user": "creator"},
        {"id": "resource-id", "format": "csv"},
    )

    assert captured["deleted_ids"] == ["drop-view"]


def test_package_create_syncs_unfold_views_for_created_resources(monkeypatch):
    captured = {}
    created_package = {
        "id": "package-id",
        "resources": [
            {"id": "resource-a", "format": "zip"},
            {"id": "resource-b", "format": "csv"},
        ],
    }

    def fake_check_access(action_name, context, data_dict):
        captured["check_access"] = (action_name, context.copy(), dict(data_dict))

    def fake_core_action(context, data_dict):
        captured["core_action"] = (context.copy(), dict(data_dict))
        return dict(created_package)

    def fake_is_artesp_owner_org(owner_org):
        return owner_org == "artesp-id"

    def fake_sync(context, resources):
        captured["sync"] = (context.copy(), list(resources))

    monkeypatch.setattr(artesp_action.tk, "check_access", fake_check_access)
    monkeypatch.setattr(artesp_action, "core_package_create", fake_core_action)
    monkeypatch.setattr(
        artesp_action.auth_helpers,
        "is_artesp_owner_org",
        fake_is_artesp_owner_org,
    )
    monkeypatch.setattr(artesp_action, "sync_unfold_resource_views", fake_sync)

    result = artesp_action.package_create(
        {"user": "creator"},
        {"name": "dataset", "title": "Dataset", "owner_org": "artesp-id"},
    )

    assert result == created_package
    assert captured["core_action"][0]["ignore_auth"] is True
    assert captured["sync"][1] == created_package["resources"]
