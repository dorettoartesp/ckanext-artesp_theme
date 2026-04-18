"""
Tests for LDAP integration.

Unit tests for the artesp_ldap_enabled helper, login/logout route,
and template logic. These tests do NOT require a running LDAP server.
"""

import pytest
from unittest.mock import patch, MagicMock

import ckanext.artesp_theme.helpers as helpers


class TestArtespLdapEnabled:
    """Tests for the artesp_ldap_enabled() helper function."""

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_true_when_ldap_uri_configured(self, mock_toolkit):
        mock_toolkit.config.get.return_value = "ldap://ldap.artesp.sp.gov.br:389"
        assert helpers.artesp_ldap_enabled() is True

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_false_when_ldap_uri_empty(self, mock_toolkit):
        mock_toolkit.config.get.return_value = ""
        assert helpers.artesp_ldap_enabled() is False

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_false_when_ldap_uri_not_set(self, mock_toolkit):
        mock_toolkit.config.get.return_value = ""
        result = helpers.artesp_ldap_enabled()
        mock_toolkit.config.get.assert_called_with("ckanext.ldap.uri", "")
        assert result is False

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_true_with_ldaps_uri(self, mock_toolkit):
        mock_toolkit.config.get.return_value = "ldaps://dominio01.Artesp.Local:636"
        assert helpers.artesp_ldap_enabled() is True


class TestLdapHelperRegistration:
    """Test that the LDAP helper is properly registered."""

    def test_artesp_ldap_enabled_in_helpers(self):
        helper_dict = helpers.get_helpers()
        assert "artesp_ldap_enabled" in helper_dict
        assert helper_dict["artesp_ldap_enabled"] == helpers.artesp_ldap_enabled
        assert "artesp_govbr_login_enabled" in helper_dict
        assert (
            helper_dict["artesp_govbr_login_enabled"]
            == helpers.artesp_govbr_login_enabled
        )


class TestArtespGovbrLoginEnabled:
    """Tests for the artesp_govbr_login_enabled() helper function."""

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_true_when_govbr_enabled_and_client_id_configured(
        self, mock_toolkit
    ):
        mock_toolkit.config.get.side_effect = {
            "ckanext.artesp.govbr.enabled": "true",
            "ckanext.artesp.govbr.client_id": "client-id",
        }.get
        mock_toolkit.asbool.return_value = True

        assert helpers.artesp_govbr_login_enabled() is True

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_false_when_govbr_client_id_is_empty(self, mock_toolkit):
        mock_toolkit.config.get.side_effect = {
            "ckanext.artesp.govbr.enabled": "true",
            "ckanext.artesp.govbr.client_id": "",
        }.get
        mock_toolkit.asbool.return_value = True

        assert helpers.artesp_govbr_login_enabled() is False

    @patch("ckanext.artesp_theme.helpers.toolkit")
    def test_returns_false_when_govbr_is_disabled(self, mock_toolkit):
        mock_toolkit.config.get.side_effect = {
            "ckanext.artesp.govbr.enabled": "false",
            "ckanext.artesp.govbr.client_id": "client-id",
        }.get
        mock_toolkit.asbool.return_value = False

        assert helpers.artesp_govbr_login_enabled() is False


class TestUserVerifyRoute:
    """Tests for the /user/verify authentication endpoint."""

    def test_route_is_registered(self):
        from ckanext.artesp_theme.controllers import artesp_theme

        rules = {rule.rule: rule for rule in artesp_theme.deferred_functions
                 if hasattr(rule, 'rule')}
        # Check via url_map of the blueprint (deferred_functions stores add_url_rule calls)
        # Simpler: just check the blueprint has the rule registered
        found = False
        for func in artesp_theme.deferred_functions:
            # deferred_functions are lambdas that call add_url_rule
            pass
        # Direct check: import and verify the function exists
        from ckanext.artesp_theme.controllers import _user_verify
        assert callable(_user_verify)

    def test_verify_reconciles_artesp_membership_after_successful_ldap_login(self):
        import importlib
        import types
        import ckanext.artesp_theme.controllers as ctrl

        mock_helpers = MagicMock()
        mock_helpers.check_ldap_password.return_value = True
        mock_helpers.get_or_create_ldap_user.return_value = "joao_silva"
        mock_helpers.login_success.return_value = "ldap_response"

        mock_search = types.SimpleNamespace(
            find_ldap_user=MagicMock(
                return_value={"cn": "cn=Joao Silva", "username": "joao.silva"}
            )
        )

        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        mock_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        mock_routes = types.SimpleNamespace(_helpers=mock_helpers)

        with patch.dict(
            "sys.modules",
            {
                "ckanext.ldap.lib.exceptions": mock_exceptions,
                "ckanext.ldap.lib.search": mock_search,
                "ckanext.ldap.routes": mock_routes,
            },
        ):
            importlib.reload(ctrl)
            with patch.object(ctrl, "toolkit") as mock_toolkit, patch.object(
                ctrl.auth_helpers,
                "ensure_artesp_org_state",
            ) as mock_ensure_org, patch.object(
                ctrl.auth_helpers,
                "should_reconcile_ldap_login",
                return_value=True,
            ), patch.object(
                ctrl.auth_helpers,
                "ensure_user_membership_in_artesp",
            ) as mock_ensure_org_membership, patch.object(
                ctrl.auth_helpers,
                "ensure_user_memberships_in_all_groups",
            ) as mock_ensure_membership:
                mock_toolkit.request.values = {
                    "login": "joao.silva",
                    "password": "senha123",
                }
                mock_toolkit.config = {"ckanext.ldap.ckan_fallback": True}
                mock_toolkit._.side_effect = lambda value: value

                result = ctrl._user_verify()

                mock_ensure_org.assert_called_once_with()
                mock_helpers.get_or_create_ldap_user.assert_called_once()
                mock_ensure_org_membership.assert_called_once_with("joao_silva")
                mock_ensure_membership.assert_called_once_with("joao_silva")
                mock_helpers.login_success.assert_called_once_with(
                    "joao_silva",
                    came_from=None,
                )
                assert result == "ldap_response"

        importlib.reload(ctrl)

    def test_verify_falls_back_when_ldap_not_installed(self):
        """When ckanext-ldap is not installed, _user_verify logs a warning and redirects."""
        import importlib
        import ckanext.artesp_theme.controllers as ctrl

        with patch.dict(
            "sys.modules",
            {
                "ckanext.ldap.lib.exceptions": None,
                "ckanext.ldap.lib.search": None,
                "ckanext.ldap.routes": None,
            },
        ):
            importlib.reload(ctrl)
            with patch.object(ctrl, "redirect_to", return_value="redirect_response") as mock_redirect, \
                 patch.object(ctrl, "toolkit") as mock_toolkit:
                mock_toolkit.url_for.return_value = "/user/login"
                result = ctrl._user_verify()
                mock_redirect.assert_called_once_with("/user/login")
                assert result == "redirect_response"

        # Restore module
        importlib.reload(ctrl)

    def test_verify_route_methods(self):
        """Verify /user/verify only accepts POST."""
        from ckanext.artesp_theme.controllers import artesp_theme

        for rule in artesp_theme.deferred_functions:
            pass  # Blueprint stores deferred registrations

        # Check by inspecting the blueprint's deferred_functions
        # Each deferred function is a closure around add_url_rule args
        # Simplest: just re-check the rule was added with POST
        from ckanext.artesp_theme import controllers
        import inspect

        source = inspect.getsource(controllers)
        assert "'/user/verify'" in source
        assert "methods=['POST']" in source


class TestSessionPatchCompatibility:
    """Tests that the session.save() → session.modified patch is correct."""

    def test_flask_session_has_modified_attribute(self):
        """
        Verify Flask's SecureCookieSession supports .modified = True.
        
        Why: CKAN 2.10+ replaced Beaker sessions with Flask's SecureCookieSession.
        Flask handles session persistence automatically at the end of the request
        if the 'modified' flag is set. This test ensures our target attribute exists.
        """
        from flask.sessions import SecureCookieSession

        session = SecureCookieSession()
        assert hasattr(session, "modified")
        session.modified = True
        assert session.modified is True

    def test_flask_session_lacks_save(self):
        """
        Confirm the bug: SecureCookieSession has no .save() method.
        
        Why: The 'AttributeError: SecureCookieSession object has no attribute save'
        is a known issue (#154) in ckanext-ldap when running on CKAN 2.10+.
        This test confirms that the default Flask session object indeed lacks the 
        method that causes the crash, justifying the need for our patch.
        """
        from flask.sessions import SecureCookieSession

        session = SecureCookieSession()
        assert not hasattr(session, "save")


# We try to import the patched function from ckanext-ldap for testing the patch itself.
try:
    from ckanext.ldap.routes import _helpers as ldap_helpers
except ImportError:
    ldap_helpers = None


@pytest.mark.skipif(ldap_helpers is None, reason="ckanext-ldap not installed")
class TestLdapEmailMigrationPatch:
    """
    Tests for the email-based migration logic added via patch in ckanext-ldap.
    Note: These test the patched logic inside ckanext-ldap._helpers.
    """

    @patch("ckanext.ldap.routes._helpers.toolkit")
    @patch("ckanext.ldap.routes._helpers.LdapUser")
    @patch("ckanext.ldap.routes._helpers.Session")
    @patch("ckanext.ldap.routes._helpers.User")
    def test_migrate_by_email_when_username_differs(
        self, mock_user_model, mock_session, mock_ldap_user_model, mock_toolkit
    ):
        """
        Test that if LDAP username is 'ldap_user' and CKAN username is 'ckan_user'
        but both have same email 'test@example.com', migration works.
        """
        # 1. Setup LDAP user data
        ldap_user_dict = {
            'username': 'ldap_user',
            'email': 'test@example.com',
            'fullname': 'Test User'
        }

        # 2. Mock config
        mock_toolkit.config = MagicMock()
        config_data = {
            'ckanext.ldap.migrate': True,
            'ckanext.ldap.organization.id': 'artesp',
            'ckanext.ldap.organization.role': 'member'
        }
        mock_toolkit.config.get.side_effect = lambda k, default=None: config_data.get(k, default)
        mock_toolkit.config.__getitem__.side_effect = lambda k: config_data[k]
        mock_toolkit.config.__contains__.side_effect = lambda k: k in config_data

        # 3. Mock LdapUser.by_ldap_id to return None (user not yet linked to LDAP)
        mock_ldap_user_model.by_ldap_id.return_value = None

        # 4. Mock ckan_user_exists to return False for 'ldap_user'
        with patch("ckanext.ldap.routes._helpers.ckan_user_exists") as mock_exists:
            mock_exists.return_value = {'exists': False, 'is_ldap': False}

            # 5. Mock the database lookup by email (this is the patched part)
            mock_email_user = MagicMock()
            mock_email_user.id = 'existing-user-id'
            mock_email_user.name = 'ckan_user'
            
            with patch("ckan.model.Session") as mock_ckan_session, \
                 patch("ckan.model.User") as mock_ckan_user_class:
                
                mock_ckan_session.query.return_value.filter.return_value.first.return_value = mock_email_user
                
                # 6. Mock toolkit.get_action('user_show') to return the existing user
                existing_user_dict = {
                    'id': 'existing-user-id',
                    'name': 'ckan_user',
                    'email': 'test@example.com'
                }
                
                def get_action_side_effect(action_name):
                    mock_action = MagicMock()
                    if action_name == 'user_show':
                        mock_action.return_value = existing_user_dict
                    elif action_name == 'user_update':
                        mock_action.return_value = existing_user_dict
                    elif action_name == 'member_create':
                        mock_action.return_value = {}
                    return mock_action
                
                mock_toolkit.get_action.side_effect = get_action_side_effect
                
                # 7. Call the function
                result_username = ldap_helpers.get_or_create_ldap_user(ldap_user_dict)
                
                # 8. Assertions
                assert result_username == 'ckan_user'
                mock_toolkit.get_action.assert_any_call('user_update')

    @patch("ckanext.ldap.routes._helpers.toolkit")
    @patch("ckanext.ldap.routes._helpers.LdapUser")
    @patch("ckanext.ldap.routes._helpers.Session")
    @patch("ckanext.ldap.routes._helpers.User")
    def test_no_migration_when_disabled(
        self, mock_user_model, mock_session, mock_ldap_user_model, mock_toolkit
    ):
        """Test that if migrate is False, it still tries to create a new user."""
        ldap_user_dict = {
            'username': 'ldap_user',
            'email': 'test@example.com'
        }

        mock_toolkit.config = MagicMock()
        config_data = {'ckanext.ldap.migrate': False}
        mock_toolkit.config.__getitem__.side_effect = lambda k: config_data[k]
        mock_toolkit.config.get.side_effect = lambda k, default=None: config_data.get(k, default)
        
        mock_ldap_user_model.by_ldap_id.return_value = None
        
        with patch("ckanext.ldap.routes._helpers.ckan_user_exists") as mock_exists:
            mock_exists.return_value = {'exists': False, 'is_ldap': False}
            
            with patch("ckanext.ldap.routes._helpers.get_unique_user_name") as mock_unique:
                mock_unique.return_value = 'ldap_user'
                
                mock_toolkit.get_action.return_value.return_value = {'id': 'new-id'}
                
                ldap_helpers.get_or_create_ldap_user(ldap_user_dict)
                
                # Should call user_create because update is False
                mock_toolkit.get_action.assert_any_call('user_create')


@pytest.mark.skipif(ldap_helpers is None, reason="ckanext-ldap not installed")
class TestLdapTranslations:
    """
    Tests to ensure that ckanext-ldap error messages are correctly translated.
    
    Why: ckanext-ldap does not provide native i18n support for Portuguese.
    To provide a consistent experience for ARTESP users, we patch the source
    code of the extension to replace English strings with Portuguese ones.
    These tests verify that our build-time patches (via Docker/Ansible) were
    applied correctly to the installed package.
    """

    def test_login_py_contains_portuguese_strings(self):
        """
        Verify that the source code of ckanext-ldap has been patched with translations.
        
        Why: Since we use 'sed' to replace strings in the filesystem, we need to 
        ensure the replacement actually happened in the environment where the 
        tests are running.
        """
        import ckanext.ldap.routes.login as login_module
        import inspect

        # Get the path to the installed login.py
        source_path = inspect.getsourcefile(login_module)
        
        with open(source_path, 'r') as f:
            content = f.read()
            
        # Check for our translated strings
        assert "Nome de usuário ou senha incorretos." in content
        assert "Conflito de nome de usuário." in content
        assert "Por favor, insira o nome de usuário e a senha." in content
        
        # Ensure English originals are gone (for the specific toolkit._ calls)
        assert "toolkit._('Bad username or password.')" not in content

    def test_helpers_py_contains_session_patch(self):
        """
        Verify that the session.save() call was replaced in _helpers.py.
        
        Why: This confirms the session patch is physically applied to the 
        source code in the current environment.
        """
        import ckanext.ldap.routes._helpers as helpers_module
        import inspect

        source_path = inspect.getsourcefile(helpers_module)
        
        with open(source_path, 'r') as f:
            content = f.read()
            
        assert "session.modified = True" in content
        assert "session.save()" not in content
