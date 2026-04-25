"""Additional focused tests for controllers.py coverage gaps."""

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import ckan.plugins.toolkit as tk
import pytest
from flask import g
from ckan.tests import factories

import ckanext.artesp_theme.controllers as controllers


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "non_clean_db"),
]


@pytest.mark.parametrize("path", ["/terms", "/privacy", "/harvesting"])
def test_static_routes_render_successfully(app, reset_db, path):
    resp = app.get(path)

    assert resp.status_code == 200


def test_statistics_route_forwards_query_params(app, monkeypatch, reset_db):
    captured = {}

    monkeypatch.setattr(
        controllers.artesp_helpers,
        "get_dashboard_statistics",
        lambda data_dict: captured.update(data_dict) or {"ok": True},
    )
    monkeypatch.setattr(
        controllers,
        "render_template",
        lambda template, dashboard: {"template": template, "dashboard": dashboard},
    )

    with app.flask_app.test_request_context("/estatisticas?theme=light&period=6m"):
        resp = controllers.statistics()

    assert resp["template"] == "statistics/index.html"
    assert captured == {"theme": "light", "period": "6m"}


class TestDatasetCollaboratorSubmit:
    def test_redirects_to_collaborator_list_on_success(self, app, monkeypatch):
        calls = []

        monkeypatch.setattr(
            controllers.toolkit,
            "get_action",
            lambda name: lambda context, data_dict: calls.append((context, data_dict)),
        )
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: f"/{endpoint}/{kwargs['id']}",
        )
        monkeypatch.setattr(controllers, "redirect_to", lambda url: url)

        with app.flask_app.test_request_context(
            "/dataset/collaborators/dataset-id/submit",
            method="POST",
            data={"username": "collaborator", "capacity": "editor"},
        ), patch("ckan.common.current_user", SimpleNamespace(name="owner")):
            result = controllers._dataset_collaborator_submit("dataset-id")

        assert result == "/dataset.collaborators_read/dataset-id"
        assert calls == [
            (
                {"user": "owner"},
                {"id": "dataset-id", "username": "collaborator", "capacity": "editor"},
            )
        ]

    def test_redirects_back_on_not_authorized(self, app, monkeypatch):
        flashed = []

        monkeypatch.setattr(
            controllers.toolkit,
            "get_action",
            lambda name: lambda context, data_dict: (_ for _ in ()).throw(
                tk.NotAuthorized("blocked")
            ),
        )
        monkeypatch.setattr(controllers, "flash_error", lambda message: flashed.append(message))
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: f"/{endpoint}/{kwargs['id']}",
        )
        monkeypatch.setattr(controllers, "redirect_to", lambda url: url)

        with app.flask_app.test_request_context(
            "/dataset/collaborators/dataset-id/submit",
            method="POST",
            data={"username": "collaborator"},
        ), patch("ckan.common.current_user", SimpleNamespace(name="owner")):
            result = controllers._dataset_collaborator_submit("dataset-id")

        assert flashed == ["blocked"]
        assert result == "/dataset.new_collaborator/dataset-id"

    def test_redirects_back_with_user_id_on_object_not_found(self, app, monkeypatch):
        flashed = []

        monkeypatch.setattr(
            controllers.toolkit,
            "get_action",
            lambda name: lambda context, data_dict: (_ for _ in ()).throw(
                tk.ObjectNotFound()
            ),
        )
        monkeypatch.setattr(controllers, "flash_error", lambda message: flashed.append(message))
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: (
                f"/{endpoint}/{kwargs['id']}?user_id={kwargs.get('user_id')}"
                if "user_id" in kwargs
                else f"/{endpoint}/{kwargs['id']}"
            ),
        )
        monkeypatch.setattr(controllers, "redirect_to", lambda url: url)
        monkeypatch.setattr(controllers.toolkit, "_", lambda message: message)

        with app.flask_app.test_request_context(
            "/dataset/collaborators/dataset-id/submit?user_id=user-123",
            method="POST",
            data={"username": "missing-user"},
        ), patch("ckan.common.current_user", SimpleNamespace(name="owner")):
            result = controllers._dataset_collaborator_submit("dataset-id")

        assert flashed == ["User not found"]
        assert result == "/dataset.new_collaborator/dataset-id?user_id=user-123"

    def test_formats_validation_error_summary_from_error_dict(self, app, monkeypatch):
        flashed = []

        class DictOnlyValidationError(tk.ValidationError):
            @property
            def error_summary(self):
                return {}

        validation_error = DictOnlyValidationError(
            {"username": ["Required"], "capacity": ["Bad"]}
        )

        monkeypatch.setattr(
            controllers.toolkit,
            "get_action",
            lambda name: lambda context, data_dict: (_ for _ in ()).throw(
                validation_error
            ),
        )
        monkeypatch.setattr(controllers, "flash_error", lambda message: flashed.append(message))
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: f"/{endpoint}/{kwargs['id']}",
        )
        monkeypatch.setattr(controllers, "redirect_to", lambda url: url)

        with app.flask_app.test_request_context(
            "/dataset/collaborators/dataset-id/submit",
            method="POST",
            data={"username": ""},
        ), patch("ckan.common.current_user", SimpleNamespace(name="owner")):
            result = controllers._dataset_collaborator_submit("dataset-id")

        assert "username: Required" in flashed[0]
        assert "capacity: Bad" in flashed[0]
        assert result == "/dataset.new_collaborator/dataset-id"


class TestValidateRatingCommentCaptcha:
    def test_requires_configured_secret(self, app):
        with app.flask_app.test_request_context("/dataset/example/rate", method="POST"):
            with pytest.raises(tk.ValidationError):
                controllers._validate_rating_comment_captcha()

    def test_requires_payload(self, app):
        with patch.object(
            controllers.toolkit,
            "config",
            {controllers.RATING_COMMENT_ALTCHA_CONFIG_KEY: "rating-secret"},
        ):
            with app.flask_app.test_request_context("/dataset/example/rate", method="POST"):
                with pytest.raises(tk.ValidationError):
                    controllers._validate_rating_comment_captcha()

    def test_raises_validation_error_when_altcha_is_unavailable(self, app):
        with patch.object(
            controllers.toolkit,
            "config",
            {controllers.RATING_COMMENT_ALTCHA_CONFIG_KEY: "rating-secret"},
        ):
            with app.flask_app.test_request_context(
                "/dataset/example/rate",
                method="POST",
                data={"altcha": "token"},
            ), patch.dict(sys.modules, {"altcha": None}):
                with pytest.raises(tk.ValidationError):
                    controllers._validate_rating_comment_captcha()

    def test_accepts_truthy_tuple_result(self, app):
        fake_altcha = types.SimpleNamespace(verify_solution=lambda payload, secret: (True, {}))
        with patch.object(
            controllers.toolkit,
            "config",
            {controllers.RATING_COMMENT_ALTCHA_CONFIG_KEY: "rating-secret"},
        ):
            with app.flask_app.test_request_context(
                "/dataset/example/rate",
                method="POST",
                data={"altcha": "token"},
            ), patch.dict(sys.modules, {"altcha": fake_altcha}):
                assert controllers._validate_rating_comment_captcha() is None

    def test_rejects_failed_result_object(self, app):
        fake_altcha = types.SimpleNamespace(
            verify_solution=lambda payload, secret: SimpleNamespace(
                verified=False,
                expired=True,
                invalid_signature=False,
                invalid_solution=True,
                error="bad solution",
            )
        )
        with patch.object(
            controllers.toolkit,
            "config",
            {controllers.RATING_COMMENT_ALTCHA_CONFIG_KEY: "rating-secret"},
        ):
            with app.flask_app.test_request_context(
                "/dataset/example/rate",
                method="POST",
                data={"altcha": "token"},
            ), patch.dict(sys.modules, {"altcha": fake_altcha}):
                with pytest.raises(tk.ValidationError):
                    controllers._validate_rating_comment_captcha()


class TestStatsRestriction:
    def test_restrict_stats_page_access_redirects_anonymous(self, app, monkeypatch):
        monkeypatch.setattr(controllers, "redirect_to", lambda url: url)
        monkeypatch.setattr(controllers.toolkit, "url_for", lambda endpoint: "/user/login")
        monkeypatch.setattr(controllers.toolkit, "_", lambda message: message)

        with app.flask_app.test_request_context("/stats"):
            g.user = ""
            assert controllers.restrict_stats_page_access() == "/user/login"

    def test_restrict_stats_page_access_allows_authenticated_user(self, app):
        with app.flask_app.test_request_context("/stats"):
            g.user = "alice"
            assert controllers.restrict_stats_page_access() is None


def test_audit_admin_forwards_filters_to_query_service(app, monkeypatch):
    captured = {}
    expected_payload = {"events": [], "item_count": 0, "page": 1}
    sysadmin = factories.Sysadmin()

    monkeypatch.setattr(
        controllers,
        "render_template",
        lambda template, **kwargs: {"template": template, **kwargs},
    )
    monkeypatch.setattr(
        controllers.audit_query,
        "search_audit_events",
        lambda filters: captured.update(filters) or expected_payload,
    )

    with app.flask_app.test_request_context(
        "/admin/audit?scope=dataset&provider=govbr&channel=api&user=alice&ip=203.0.113.10&object=rodovia&page=2&sort_by=package_name&sort_dir=asc"
    ):
        g.user = sysadmin["name"]
        response = controllers.audit_admin()

    assert response["template"] == "admin/audit.html"
    assert response["events"] == []
    assert response["item_count"] == 0
    assert captured == {
        "scope": "dataset",
        "provider": "govbr",
        "channel": "api",
        "user": "alice",
        "ip": "203.0.113.10",
        "object": "rodovia",
        "page": "2",
        "date_from": "",
        "date_to": "",
        "action": "",
        "sort_by": "package_name",
        "sort_dir": "asc",
    }


class TestUserVerifyAdditionalBranches:
    def test_returns_login_failed_on_multiple_match(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_helpers = MagicMock()
        mock_helpers.login_failed.return_value = "login-failed"
        fake_search = types.SimpleNamespace(
            find_ldap_user=MagicMock(side_effect=MultipleMatchError("many matches"))
        )
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit:
            mock_toolkit.request.values = {"login": "alice", "password": "secret"}
            result = controllers._user_verify()

        assert result == "login-failed"
        mock_helpers.login_failed.assert_called_once_with(notice="many matches")

    def test_returns_login_failed_on_user_conflict_after_valid_ldap_password(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_helpers = MagicMock()
        mock_helpers.check_ldap_password.return_value = True
        mock_helpers.get_or_create_ldap_user.side_effect = UserConflictError("conflict")
        mock_helpers.login_failed.return_value = "login-failed"
        fake_search = types.SimpleNamespace(
            find_ldap_user=MagicMock(return_value={"cn": "cn=Alice"})
        )
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit:
            mock_toolkit.request.values = {"login": "alice", "password": "secret"}
            mock_toolkit.config = {"ckanext.ldap.ckan_fallback": False}
            result = controllers._user_verify()

        assert result == "login-failed"
        mock_helpers.login_failed.assert_called_once_with(error="conflict")

    def test_returns_login_failed_for_ldap_conflict_when_fallback_user_exists(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_helpers = MagicMock()
        mock_helpers.check_ldap_password.return_value = False
        mock_helpers.ckan_user_exists.return_value = {"exists": True, "is_ldap": False}
        mock_helpers.login_failed.return_value = "login-failed"
        fake_search = types.SimpleNamespace(
            find_ldap_user=MagicMock(return_value={"cn": "cn=Alice"})
        )
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit:
            mock_toolkit.request.values = {"login": "alice", "password": "secret"}
            mock_toolkit.config = {"ckanext.ldap.ckan_fallback": True}
            mock_toolkit._ = lambda message: message
            result = controllers._user_verify()

        assert result == "login-failed"
        assert "Conflito de nome de usuário" in mock_helpers.login_failed.call_args.kwargs["error"]

    def test_returns_login_success_for_ckan_fallback_user(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        fake_user = SimpleNamespace(name="alice", validate_password=lambda password: True)
        fake_user_model = SimpleNamespace(by_name=lambda username: fake_user)
        mock_helpers = MagicMock()
        mock_helpers.get_user_dict.return_value = {"name": "alice"}
        mock_helpers.login_success.return_value = "login-success"
        fake_search = types.SimpleNamespace(find_ldap_user=MagicMock(return_value=None))
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit, patch.dict(
            sys.modules,
            {"ckan.model": types.SimpleNamespace(User=fake_user_model)},
        ):
            mock_toolkit.request.values = {"login": "alice", "password": "secret"}
            mock_toolkit.config = {"ckanext.ldap.ckan_fallback": True}
            result = controllers._user_verify()

        assert result == "login-success"
        mock_helpers.login_success.assert_called_once_with("alice", came_from=None)

    def test_records_ldap_success_when_login_succeeds(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_helpers = MagicMock()
        mock_helpers.check_ldap_password.return_value = True
        mock_helpers.get_or_create_ldap_user.return_value = "alice"
        mock_helpers.login_success.return_value = "login-success"
        fake_search = types.SimpleNamespace(
            find_ldap_user=MagicMock(return_value={"cn": "cn=Alice"})
        )
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit, patch.object(
            controllers, "audit_capture"
        ) as mock_audit_capture:
            mock_toolkit.request.values = {"login": "alice", "password": "secret"}
            mock_toolkit.config = {"ckanext.ldap.ckan_fallback": False}
            result = controllers._user_verify()

        assert result == "login-success"
        mock_audit_capture.record_auth_event.assert_called_once_with(
            event_action="login_success",
            success=True,
            auth_provider="ldap",
            actor_name="alice",
            actor_identifier="alice",
            request_path="/user/verify",
        )

    def test_returns_login_failed_when_password_payload_is_missing(self):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_helpers = MagicMock()
        mock_helpers.login_failed.return_value = "login-failed"
        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_search = types.SimpleNamespace(find_ldap_user=MagicMock())
        fake_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ), patch.object(controllers, "toolkit") as mock_toolkit:
            mock_toolkit.request.values = {"login": "alice"}
            mock_toolkit._ = lambda message: message
            result = controllers._user_verify()

        assert result == "login-failed"
        assert (
            mock_helpers.login_failed.call_args.kwargs["error"]
            == "Por favor, insira o nome de usuário e a senha."
        )


class TestResourceSearchAdditionalBranches:
    def test_resource_search_handles_advanced_query_error(self, app, monkeypatch):
        monkeypatch.setattr(
            controllers.toolkit,
            "get_action",
            lambda name: lambda context, data_dict: (_ for _ in ()).throw(
                Exception("advanced query failed")
            ),
        )
        monkeypatch.setattr(
            controllers,
            "Page",
            lambda **kwargs: SimpleNamespace(item_count=kwargs["item_count"]),
        )
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: "/resources",
        )
        monkeypatch.setattr(
            controllers,
            "render_template",
            lambda template, **kwargs: kwargs,
        )

        with app.flask_app.test_request_context("/resources?q=format:csv"):
            result = controllers.resource_search()

        assert result["count"] == 0
        assert result["resources"] == []

    def test_resource_search_handles_field_errors_package_errors_and_pager(self, app, monkeypatch):
        resources_by_query = {
            "name:report": [
                {
                    "id": "res-1",
                    "package_id": "pkg-1",
                    "name": "Report",
                    "format": "CSV",
                    "metadata_modified": "2026-01-01",
                },
                {
                    "id": "res-2",
                    "package_id": "pkg-2",
                    "name": "Broken Package",
                    "format": "CSV",
                    "metadata_modified": None,
                },
            ],
            "format:report": [
                {
                    "id": "res-1",
                    "package_id": "pkg-1",
                    "name": "Report",
                    "format": "CSV",
                    "metadata_modified": "2026-01-01",
                }
            ],
        }

        def fake_get_action(name):
            if name == "resource_search":
                def action(context, data_dict):
                    query = data_dict["query"]
                    if query == "description:report":
                        raise Exception("description failed")
                    return {"results": list(resources_by_query.get(query, []))}
                return action
            if name == "package_show":
                def action(context, data_dict):
                    if data_dict["id"] == "pkg-2":
                        raise Exception("package missing")
                    return {
                        "id": "pkg-1",
                        "name": "dataset-1",
                        "title": "Dataset 1",
                        "groups": [{"name": "group-a", "title": "Group A"}],
                    }
                return action
            raise AssertionError(name)

        class FakePage:
            def __init__(self, **kwargs):
                self.collection = kwargs["collection"]
                self.item_count = kwargs["item_count"]
                self.generated_url = kwargs["url"](
                    q="report",
                    page=2,
                    sort="missing asc",
                    format="CSV",
                    group="group-a",
                )

        monkeypatch.setattr(controllers.toolkit, "get_action", fake_get_action)
        monkeypatch.setattr(controllers, "Page", FakePage)
        monkeypatch.setattr(
            controllers.toolkit,
            "url_for",
            lambda endpoint, **kwargs: "/resources",
        )
        monkeypatch.setattr(
            controllers,
            "render_template",
            lambda template, **kwargs: kwargs,
        )

        with app.flask_app.test_request_context(
            "/resources?q=report&sort=missing asc&format=CSV&group=group-a"
        ):
            result = controllers.resource_search()

        assert result["count"] == 1
        assert result["resources"][0]["id"] == "res-1"
        assert result["format_facets"] == [("CSV", 1)]
        assert result["group_facets"] == [("group-a", {"title": "Group A", "count": 1})]
        assert result["page"].generated_url == "/resources"
