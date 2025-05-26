"""Tests for file structure using unittest.

Tests the structure of the directories and files without requiring CKAN imports.
"""

import os
import unittest


class TestFileStructure(unittest.TestCase):
    """Test the structure of the directories and files."""
    
    def setUp(self):
        """Set up the test environment."""
        # Get the path to the extension directory
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.extension_dir = os.path.dirname(self.current_dir)
    
    def test_templates_directory_exists(self):
        """Test that the templates directory exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        self.assertTrue(os.path.isdir(templates_dir), f"Templates directory not found: {templates_dir}")
    
    def test_static_directory_exists(self):
        """Test that the static directory exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        static_dir = os.path.join(templates_dir, 'static')
        self.assertTrue(os.path.isdir(static_dir), f"Static directory not found: {static_dir}")
    
    def test_static_pages_exist(self):
        """Test that the static pages exist."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        static_dir = os.path.join(templates_dir, 'static')
        
        # Check that the static pages exist
        about_ckan_file = os.path.join(static_dir, 'about_ckan.html')
        self.assertTrue(os.path.isfile(about_ckan_file), f"File not found: {about_ckan_file}")
        
        terms_file = os.path.join(static_dir, 'terms.html')
        self.assertTrue(os.path.isfile(terms_file), f"File not found: {terms_file}")
        
        privacy_file = os.path.join(static_dir, 'privacy.html')
        self.assertTrue(os.path.isfile(privacy_file), f"File not found: {privacy_file}")
        
        contact_file = os.path.join(static_dir, 'contact.html')
        self.assertTrue(os.path.isfile(contact_file), f"File not found: {contact_file}")
        
        harvesting_file = os.path.join(static_dir, 'harvesting.html')
        self.assertTrue(os.path.isfile(harvesting_file), f"File not found: {harvesting_file}")
    
    def test_static_base_template_exists(self):
        """Test that the static base template exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        static_dir = os.path.join(templates_dir, 'static')
        base_file = os.path.join(static_dir, 'base.html')
        self.assertTrue(os.path.isfile(base_file), f"File not found: {base_file}")
    
    def test_home_directory_exists(self):
        """Test that the home directory exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        home_dir = os.path.join(templates_dir, 'home')
        self.assertTrue(os.path.isdir(home_dir), f"Directory not found: {home_dir}")
    
    def test_page_template_exists(self):
        """Test that the page.html template exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        page_file = os.path.join(templates_dir, 'page.html')
        self.assertTrue(os.path.isfile(page_file), f"File not found: {page_file}")
    
    def test_header_template_exists(self):
        """Test that the header.html template exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        header_file = os.path.join(templates_dir, 'header.html')
        self.assertTrue(os.path.isfile(header_file), f"File not found: {header_file}")
    
    def test_footer_template_exists(self):
        """Test that the footer.html template exists."""
        templates_dir = os.path.join(self.extension_dir, 'templates')
        footer_file = os.path.join(templates_dir, 'footer.html')
        self.assertTrue(os.path.isfile(footer_file), f"File not found: {footer_file}")
    
    def test_assets_directory_exists(self):
        """Test that the assets directory exists."""
        assets_dir = os.path.join(self.extension_dir, 'assets')
        self.assertTrue(os.path.isdir(assets_dir), f"Directory not found: {assets_dir}")
    
    def test_webassets_yml_exists(self):
        """Test that the webassets.yml file exists."""
        assets_dir = os.path.join(self.extension_dir, 'assets')
        webassets_yml = os.path.join(assets_dir, 'webassets.yml')
        self.assertTrue(os.path.isfile(webassets_yml), f"File not found: {webassets_yml}")
    
    def test_i18n_directory_exists(self):
        """Test that the i18n directory exists."""
        i18n_dir = os.path.join(self.extension_dir, 'i18n')
        self.assertTrue(os.path.isdir(i18n_dir), f"Directory not found: {i18n_dir}")
    
    def test_pt_br_locale_exists(self):
        """Test that the pt_BR locale directory exists."""
        i18n_dir = os.path.join(self.extension_dir, 'i18n')
        pt_br_dir = os.path.join(i18n_dir, 'pt_BR')
        self.assertTrue(os.path.isdir(pt_br_dir), f"Directory not found: {pt_br_dir}")
        
        lc_messages_dir = os.path.join(pt_br_dir, 'LC_MESSAGES')
        self.assertTrue(os.path.isdir(lc_messages_dir), f"Directory not found: {lc_messages_dir}")


if __name__ == '__main__':
    unittest.main()
