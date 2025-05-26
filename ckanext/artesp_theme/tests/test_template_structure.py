"""Tests for template structure.

Tests the structure of the template directories and files.
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import the plugin module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import ckanext.artesp_theme.plugin as plugin


class TestTemplateStructure(unittest.TestCase):
    """Test the structure of the template directories and files."""

    def test_templates_directory_exists(self):
        """Test that the templates directory exists."""
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

        # Check that the directory exists
        self.assertTrue(os.path.isdir(templates_dir))


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_static_directory_exists():
    """Test that the static directory exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Check that the static directory exists
    static_dir = os.path.join(templates_dir, 'static')
    assert os.path.isdir(static_dir)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_static_pages_exist():
    """Test that the static pages exist."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Get the path to the static directory
    static_dir = os.path.join(templates_dir, 'static')

    # Check that the static pages exist
    about_ckan_file = os.path.join(static_dir, 'about_ckan.html')
    assert os.path.isfile(about_ckan_file)

    terms_file = os.path.join(static_dir, 'terms.html')
    assert os.path.isfile(terms_file)

    privacy_file = os.path.join(static_dir, 'privacy.html')
    assert os.path.isfile(privacy_file)

    contact_file = os.path.join(static_dir, 'contact.html')
    assert os.path.isfile(contact_file)

    harvesting_file = os.path.join(static_dir, 'harvesting.html')
    assert os.path.isfile(harvesting_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_static_base_template_exists():
    """Test that the static base template exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Get the path to the static directory
    static_dir = os.path.join(templates_dir, 'static')

    # Check that the base template exists
    base_file = os.path.join(static_dir, 'base.html')
    assert os.path.isfile(base_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_home_directory_exists():
    """Test that the home directory exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Check that the home directory exists
    home_dir = os.path.join(templates_dir, 'home')
    assert os.path.isdir(home_dir)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_page_template_exists():
    """Test that the page.html template exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Check that the page.html template exists
    page_file = os.path.join(templates_dir, 'page.html')
    assert os.path.isfile(page_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_header_template_exists():
    """Test that the header.html template exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Check that the header.html template exists
    header_file = os.path.join(templates_dir, 'header.html')
    assert os.path.isfile(header_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_footer_template_exists():
    """Test that the footer.html template exists."""
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')

    # Check that the footer.html template exists
    footer_file = os.path.join(templates_dir, 'footer.html')
    assert os.path.isfile(footer_file)
