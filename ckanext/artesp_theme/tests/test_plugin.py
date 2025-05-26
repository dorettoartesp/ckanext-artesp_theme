"""
Tests for plugin.py.

Tests the ArtespThemePlugin class and its implementation of various CKAN interfaces.
"""
import os
import pytest
from unittest import mock

import ckan.plugins as plugins
import ckanext.artesp_theme.plugin as plugin
from ckanext.artesp_theme.controllers import artesp_theme


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_plugin_loaded():
    """Test that the artesp_theme plugin is loaded."""
    assert plugins.plugin_loaded("artesp_theme")


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_update_config():
    """Test that the plugin correctly adds template, public, and resource directories."""
    # Create a mock config object
    config = {}

    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call update_config
    with mock.patch('ckan.plugins.toolkit.add_template_directory') as mock_add_template_directory, \
         mock.patch('ckan.plugins.toolkit.add_public_directory') as mock_add_public_directory, \
         mock.patch('ckan.plugins.toolkit.add_resource') as mock_add_resource:

        plugin_instance.update_config(config)

        # Check that the correct directories were added
        mock_add_template_directory.assert_called_once_with(config, "templates")
        mock_add_public_directory.assert_called_once_with(config, "public")
        mock_add_resource.assert_called_once_with("assets", "artesp_theme")


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_get_blueprint():
    """Test that the plugin correctly returns the blueprint."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call get_blueprint
    blueprints = plugin_instance.get_blueprint()

    # Check that the correct blueprint was returned
    assert len(blueprints) == 1
    assert blueprints[0] == artesp_theme


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_get_helpers():
    """Test that the plugin correctly returns the helpers."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call get_helpers
    helpers_dict = plugin_instance.get_helpers()

    # Check that the helpers dictionary contains expected keys
    assert "artesp_theme_hello" in helpers_dict
    assert "get_package_count" in helpers_dict
    assert "get_resource_count" in helpers_dict
    assert "get_latest_datasets" in helpers_dict
    assert "get_organization_count" in helpers_dict
    assert "get_group_count" in helpers_dict
    assert "get_year" in helpers_dict
    assert "safe_html" in helpers_dict
    assert "fix_fontawesome_icon" in helpers_dict


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_i18n_directory():
    """Test that the plugin correctly returns the i18n directory."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call i18n_directory
    i18n_dir = plugin_instance.i18n_directory()

    # Check that the correct directory was returned
    expected_dir = os.path.join(os.path.dirname(plugin.__file__), 'i18n')
    assert i18n_dir == expected_dir


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_i18n_locales():
    """Test that the plugin correctly returns the supported locales."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call i18n_locales
    locales = plugin_instance.i18n_locales()

    # Check that the correct locales were returned
    assert locales == ['pt_BR']


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_i18n_domain():
    """Test that the plugin correctly returns the i18n domain."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Call i18n_domain
    domain = plugin_instance.i18n_domain()

    # Check that the correct domain was returned
    assert domain == 'ckanext-artesp_theme'


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_make_middleware():
    """Test that the plugin correctly creates the middleware."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Create a mock app
    mock_app = mock.MagicMock()

    # Call make_middleware
    with mock.patch('ckanext.artesp_theme.middleware.make_middleware') as mock_make_middleware:
        plugin_instance.make_middleware(mock_app, {})

        # Check that make_middleware was called with the correct arguments
        mock_make_middleware.assert_called_once_with(mock_app, {})


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_make_error_log_middleware():
    """Test that the plugin correctly returns the app unchanged for error logging middleware."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")

    # Create a mock app
    mock_app = mock.MagicMock()

    # Call make_error_log_middleware
    result = plugin_instance.make_error_log_middleware(mock_app, {})

    # Check that the app was returned unchanged
    assert result == mock_app
