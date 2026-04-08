"""Tests for action.py."""

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
