"""TDD: auth functions block write operations for external users."""
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import auth_helpers


def _external_user(name="ext_user"):
    u = MagicMock()
    u.name = name
    u.id = "uid-ext"
    u.sysadmin = False
    u.plugin_extras = {"artesp": {"user_type": "external"}}
    return u


def _internal_user(name="int_user"):
    u = MagicMock()
    u.name = name
    u.id = "uid-int"
    u.sysadmin = False
    u.plugin_extras = {"artesp": {"user_type": "internal"}}
    return u


def _ctx(user):
    return {"user": user.name, "auth_user_obj": user, "model": MagicMock()}


class TestExternalUserBlocked:
    """External users must be denied all write operations."""

    @pytest.mark.parametrize("auth_fn", [
        artesp_auth.package_create,
        artesp_auth.organization_create,
        artesp_auth.organization_update,
        artesp_auth.organization_delete,
        artesp_auth.group_create,
        artesp_auth.group_update,
        artesp_auth.group_delete,
    ])
    def test_write_action_denied_for_external_user(self, auth_fn):
        user = _external_user()
        ctx = _ctx(user)
        with patch.object(auth_helpers, "is_external_user", return_value=True):
            result = auth_fn(ctx, {})
        assert result["success"] is False

    @pytest.mark.parametrize("auth_fn", [
        artesp_auth.package_update,
        artesp_auth.package_delete,
    ])
    def test_package_write_denied_for_external_user(self, auth_fn):
        user = _external_user()
        ctx = _ctx(user)
        with patch.object(auth_helpers, "is_external_user", return_value=True):
            result = auth_fn(ctx, {"id": "some-dataset"})
        assert result["success"] is False

    @pytest.mark.parametrize("auth_fn", [
        artesp_auth.resource_create,
        artesp_auth.resource_update,
        artesp_auth.resource_delete,
    ])
    def test_resource_write_denied_for_external_user(self, auth_fn):
        user = _external_user()
        ctx = _ctx(user)
        with patch.object(auth_helpers, "is_external_user", return_value=True):
            result = auth_fn(ctx, {"id": "some-resource", "package_id": "pkg"})
        assert result["success"] is False

    @pytest.mark.parametrize(
        ("auth_fn", "payload", "existing_collaborator"),
        [
            (
                artesp_auth.package_collaborator_list,
                {"id": "some-dataset"},
                None,
            ),
            (
                artesp_auth.package_collaborator_create,
                {
                    "id": "some-dataset",
                    "user_id": "target-user-id",
                    "capacity": "editor",
                },
                None,
            ),
            (
                artesp_auth.package_collaborator_delete,
                {"id": "some-dataset", "user_id": "target-user-id"},
                MagicMock(),
            ),
        ],
    )
    def test_dataset_collaborator_actions_denied_for_external_user(
        self,
        auth_fn,
        payload,
        existing_collaborator,
    ):
        user = _external_user()
        target_user = MagicMock()
        target_user.id = "target-user-id"
        package = MagicMock()
        ctx = _ctx(user)

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(auth_helpers, "is_external_user", return_value=True)
            )
            stack.enter_context(
                patch.object(auth_helpers, "is_sysadmin", return_value=False)
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "get_authenticated_user",
                    return_value=user,
                )
            )
            stack.enter_context(
                patch.object(auth_helpers, "is_valid_user", return_value=True)
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "is_dataset_collaborators_enabled",
                    return_value=True,
                )
            )
            stack.enter_context(
                patch.object(auth_helpers, "get_package", return_value=package)
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "dataset_belongs_to_artesp",
                    return_value=True,
                )
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "user_can_manage_collaborators",
                    return_value=True,
                )
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "requested_capacity_is_allowed",
                    return_value=True,
                )
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "get_default_dataset_collaborator_capacity",
                    return_value="editor",
                )
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "get_target_user",
                    return_value=target_user,
                )
            )
            stack.enter_context(
                patch.object(
                    auth_helpers,
                    "get_collaborator_by_user_id",
                    return_value=existing_collaborator,
                )
            )

            result = auth_fn(ctx, payload)

        assert result["success"] is False
        assert "External users cannot perform write operations." in result["msg"]


class TestInternalUserNotAffected:
    """Existing auth logic for internal users should be unaffected."""

    def test_package_create_internal_user_not_blocked_by_external_check(self):
        user = _internal_user()
        ctx = _ctx(user)
        with patch.object(auth_helpers, "is_external_user", return_value=False):
            with patch.object(auth_helpers, "is_sysadmin", return_value=False):
                with patch.object(auth_helpers, "get_authenticated_user", return_value=user):
                    with patch.object(auth_helpers, "is_valid_user", return_value=True):
                        with patch.object(auth_helpers, "get_artesp_org", return_value=MagicMock()):
                            result = artesp_auth.package_create(ctx, {})
        assert result["success"] is True
