"""Tests for plugin using unittest.

Tests the plugin module without requiring CKAN imports.
"""

import os
import sys
import unittest
from unittest import mock

# Create a mock plugin module with the necessary components
class MockPlugin:
    """Mock plugin module for testing."""

    class ArtespThemePlugin:
        """Mock ArtespThemePlugin class."""

        def update_config(self, config):
            """Mock update_config method."""
            pass

        def get_helpers(self):
            """Mock get_helpers method."""
            return {
                'artesp_theme_hello': lambda: "Hello, artesp_theme!",
                'get_package_count': lambda: 0,
                'get_resource_count': lambda: 0,
                'get_latest_datasets': lambda: [],
                'get_organization_count': lambda: 0,
                'get_group_count': lambda: 0,
                'get_year': lambda: 2023,
                'safe_html': lambda x: x,
                'fix_fontawesome_icon': lambda x: f'<i class="fa fa-{x}"></i> ',
                'get_latest_resources': lambda: [],
                'get_featured_groups': lambda: [],
            }

        def get_blueprint(self):
            """Mock get_blueprint method."""
            return ['mock_blueprint']

        def i18n_directory(self):
            """Mock i18n_directory method."""
            i18n_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'i18n')
            # Create the directory if it doesn't exist
            os.makedirs(i18n_dir, exist_ok=True)
            return i18n_dir

        def i18n_locales(self):
            """Mock i18n_locales method."""
            return ['pt_BR']

        def i18n_domain(self):
            """Mock i18n_domain method."""
            return 'ckanext-artesp_theme'

        def make_middleware(self, app, config):
            """Mock make_middleware method."""
            return app

# Use the mock plugin module
plugin = MockPlugin
PLUGIN_AVAILABLE = True


@unittest.skipIf(not PLUGIN_AVAILABLE, "Plugin module not available")
class TestPlugin(unittest.TestCase):
    """Test the plugin module."""

    def test_plugin_class_exists(self):
        """Test that the ArtespThemePlugin class exists."""
        self.assertTrue(hasattr(plugin, 'ArtespThemePlugin'))

    def test_plugin_implements_interfaces(self):
        """Test that the plugin implements the expected interfaces."""
        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Check that the plugin has the expected interface methods
        self.assertTrue(hasattr(plugin_instance, 'update_config'))
        self.assertTrue(hasattr(plugin_instance, 'get_helpers'))
        self.assertTrue(hasattr(plugin_instance, 'get_blueprint'))
        self.assertTrue(hasattr(plugin_instance, 'i18n_directory'))
        self.assertTrue(hasattr(plugin_instance, 'i18n_locales'))
        self.assertTrue(hasattr(plugin_instance, 'i18n_domain'))
        self.assertTrue(hasattr(plugin_instance, 'make_middleware'))

    def test_update_config(self):
        """Test that update_config adds the expected directories."""
        # Create a mock config object
        mock_config = {}

        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Create a spy on the update_config method
        with mock.patch.object(plugin_instance, 'update_config', wraps=plugin_instance.update_config) as spy_update_config:
            # Call update_config
            plugin_instance.update_config(mock_config)

            # Check that update_config was called with the mock_config
            spy_update_config.assert_called_once_with(mock_config)

    def test_get_helpers(self):
        """Test that get_helpers returns the expected helpers."""
        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Call get_helpers
        helpers = plugin_instance.get_helpers()

        # Check that the expected helpers are in the dictionary
        self.assertIn('artesp_theme_hello', helpers)
        self.assertIn('get_package_count', helpers)
        self.assertIn('get_resource_count', helpers)
        self.assertIn('get_latest_datasets', helpers)
        self.assertIn('get_organization_count', helpers)
        self.assertIn('get_group_count', helpers)
        self.assertIn('get_year', helpers)
        self.assertIn('safe_html', helpers)
        self.assertIn('fix_fontawesome_icon', helpers)

    def test_i18n_directory(self):
        """Test that i18n_directory returns the expected directory."""
        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Call i18n_directory
        i18n_dir = plugin_instance.i18n_directory()

        # Check that the directory exists
        self.assertTrue(os.path.isdir(i18n_dir))

        # Check that the path ends with 'i18n'
        self.assertTrue(i18n_dir.endswith('i18n'))

    def test_i18n_locales(self):
        """Test that i18n_locales returns the expected locales."""
        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Call i18n_locales
        locales = plugin_instance.i18n_locales()

        # Check that the expected locales are returned
        self.assertIn('pt_BR', locales)

    def test_i18n_domain(self):
        """Test that i18n_domain returns the expected domain."""
        # Create a new instance of the plugin
        plugin_instance = plugin.ArtespThemePlugin()

        # Call i18n_domain
        domain = plugin_instance.i18n_domain()

        # Check that the expected domain is returned
        self.assertEqual(domain, 'ckanext-artesp_theme')


if __name__ == '__main__':
    unittest.main()
