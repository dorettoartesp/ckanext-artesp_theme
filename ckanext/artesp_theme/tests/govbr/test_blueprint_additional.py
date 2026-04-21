"""Additional focused tests for govbr.blueprint coverage gaps."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from ckanext.artesp_theme.govbr import blueprint


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def test_set_repoze_user_calls_login_user_for_existing_user():
    fake_user = SimpleNamespace(name="existing-user")

    with patch("ckan.common.login_user") as mock_login_user, patch(
        "ckan.model.User.get", return_value=fake_user
    ):
        blueprint._set_repoze_user("existing-user")

    mock_login_user.assert_called_once_with(fake_user)


def test_set_repoze_user_skips_missing_user():
    with patch("ckan.common.login_user") as mock_login_user, patch(
        "ckan.model.User.get", return_value=None
    ):
        blueprint._set_repoze_user("missing-user")

    mock_login_user.assert_not_called()


def test_flash_error_uses_toolkit_helper(monkeypatch):
    flashed = []

    monkeypatch.setattr(blueprint.toolkit.h, "flash_error", lambda message: flashed.append(message))
    monkeypatch.setattr(blueprint.toolkit, "_", lambda message: f"translated:{message}")

    blueprint._flash_error("failure")

    assert flashed == ["translated:failure"]


def test_redirect_external_from_dashboard_redirects_external_user(app):
    fake_user = SimpleNamespace(is_authenticated=True, name="external-user")

    with app.flask_app.test_request_context("/dashboard"), patch(
        "ckan.common.current_user", fake_user
    ), patch(
        "ckanext.artesp_theme.govbr.blueprint.is_external_user", return_value=True
    ):
        response = blueprint.redirect_external_from_dashboard()

    assert response.status_code == 302
    assert response.location.endswith("/user/external-user/followed")


def test_followed_renders_expected_context(monkeypatch):
    rendered = {}

    def fake_get_action(name):
        if name == "user_show":
            return lambda context, data_dict: {"id": "alice", "name": "alice"}
        if name == "followee_list":
            return lambda context, data_dict: [{"type": "dataset", "display_name": "Base X"}]
        raise AssertionError(name)

    monkeypatch.setattr(blueprint.toolkit, "get_action", fake_get_action)
    monkeypatch.setattr(
        "ckan.lib.base.render",
        lambda template, extra_vars: rendered.update(
            {"template": template, "extra_vars": extra_vars}
        )
        or "rendered-followed",
    )

    with patch("ckan.model.User.get", return_value=SimpleNamespace(sysadmin=False)), patch.object(
        blueprint.toolkit,
        "c",
        SimpleNamespace(user="alice"),
    ):
        result = blueprint.followed("alice")

    assert result == "rendered-followed"
    assert rendered["template"] == "user/govbr_followed.html"
    assert rendered["extra_vars"]["is_myself"] is True
    assert rendered["extra_vars"]["followees"] == [
        {"type": "dataset", "display_name": "Base X"}
    ]
