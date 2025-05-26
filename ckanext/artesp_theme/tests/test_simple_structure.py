"""Tests for template structure using unittest.

Tests the structure of the template directories and files without requiring CKAN.
"""

import os
import sys
import unittest

# Get the absolute path to the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the plugin module directly
import plugin


class TestTemplateStructure(unittest.TestCase):
    """Test the structure of the template directories and files."""

    def test_templates_directory_exists(self):
        """Test that the templates directory exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the directory exists
        self.assertTrue(os.path.isdir(templates_dir))

    def test_static_directory_exists(self):
        """Test that the static directory exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Get the path to the static directory
        static_dir = os.path.join(templates_dir, 'static')

        # Check that the static directory exists
        self.assertTrue(os.path.isdir(static_dir))

    def test_static_pages_exist(self):
        """Test that the static pages exist."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Get the path to the static directory
        static_dir = os.path.join(templates_dir, 'static')

        # Check that the static pages exist
        about_ckan_file = os.path.join(static_dir, 'about_ckan.html')
        self.assertTrue(os.path.isfile(about_ckan_file))

        terms_file = os.path.join(static_dir, 'terms.html')
        self.assertTrue(os.path.isfile(terms_file))

        privacy_file = os.path.join(static_dir, 'privacy.html')
        self.assertTrue(os.path.isfile(privacy_file))

        contact_file = os.path.join(static_dir, 'contact.html')
        self.assertTrue(os.path.isfile(contact_file))

        harvesting_file = os.path.join(static_dir, 'harvesting.html')
        self.assertTrue(os.path.isfile(harvesting_file))

    def test_static_base_template_exists(self):
        """Test that the static base template exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Get the path to the static directory
        static_dir = os.path.join(templates_dir, 'static')

        # Check that the base template exists
        base_file = os.path.join(static_dir, 'base.html')
        self.assertTrue(os.path.isfile(base_file))

    def test_home_directory_exists(self):
        """Test that the home directory exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the home directory exists
        home_dir = os.path.join(templates_dir, 'home')
        self.assertTrue(os.path.isdir(home_dir))

    def test_page_template_exists(self):
        """Test that the page.html template exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the page.html template exists
        page_file = os.path.join(templates_dir, 'page.html')
        self.assertTrue(os.path.isfile(page_file))

    def test_header_template_exists(self):
        """Test that the header.html template exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the header.html template exists
        header_file = os.path.join(templates_dir, 'header.html')
        self.assertTrue(os.path.isfile(header_file))

    def test_footer_template_exists(self):
        """Test that the footer.html template exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the footer.html template exists
        footer_file = os.path.join(templates_dir, 'footer.html')
        self.assertTrue(os.path.isfile(footer_file))


if __name__ == '__main__':
    unittest.main()
