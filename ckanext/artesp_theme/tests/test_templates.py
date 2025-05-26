"""Tests for templates.

Tests the template overrides and customizations of the ARTESP theme extension.
"""

import os
import pytest
from bs4 import BeautifulSoup
from unittest import mock

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_contains_hero_section(app):
    """Test that the homepage contains the hero section."""
    # Make a GET request to the homepage
    response = app.get('/')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the hero section exists
    hero_section = soup.find('div', class_='hero')
    assert hero_section is not None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_contains_latest_datasets_section(app):
    """Test that the homepage contains the latest datasets section."""
    # Create some datasets
    factories.Dataset()
    factories.Dataset()
    factories.Dataset()
    
    # Make a GET request to the homepage
    response = app.get('/')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the latest datasets section exists
    latest_datasets_section = soup.find('div', class_='latest-datasets')
    assert latest_datasets_section is not None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_contains_stats_section(app):
    """Test that the homepage contains the stats section."""
    # Make a GET request to the homepage
    response = app.get('/')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the stats section exists
    stats_section = soup.find('div', class_='stats-section')
    assert stats_section is not None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_footer_contains_custom_links(app):
    """Test that the footer contains the custom links."""
    # Make a GET request to the homepage
    response = app.get('/')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the footer exists
    footer = soup.find('footer')
    assert footer is not None
    
    # Check that the footer contains the custom links
    about_link = footer.find('a', href='/about-ckan')
    assert about_link is not None
    
    terms_link = footer.find('a', href='/terms')
    assert terms_link is not None
    
    privacy_link = footer.find('a', href='/privacy')
    assert privacy_link is not None
    
    contact_link = footer.find('a', href='/contact')
    assert contact_link is not None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_dataset_search_page(app):
    """Test that the dataset search page has the custom layout."""
    # Make a GET request to the dataset search page
    response = app.get('/dataset')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the search form exists
    search_form = soup.find('form', class_='search-form')
    assert search_form is not None
    
    # Check that the search results count exists
    search_results_count = soup.find('div', class_='search-results-count')
    assert search_results_count is not None
    
    # Check that the order-by dropdown exists
    order_by = soup.find('select', id='field-order-by')
    assert order_by is not None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_dataset_create_page_stages(app):
    """Test that the dataset create page has the custom stages styling."""
    # Create a sysadmin user
    sysadmin = factories.Sysadmin()
    
    # Create an organization (required for creating datasets)
    organization = factories.Organization()
    
    # Make a GET request to the dataset create page as the sysadmin
    response = app.get('/dataset/new', extra_environ={'REMOTE_USER': sysadmin['name']})
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the stages element exists
    stages = soup.find('ol', class_='stages')
    assert stages is not None
    
    # Check that the first stage is active
    active_stage = stages.find('li', class_='active')
    assert active_stage is not None
    assert active_stage.text.strip() == '1. Create dataset'


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_govsp_header_in_page_html(app):
    """Test that the São Paulo government header is in the page.html template."""
    # Make a GET request to the homepage
    response = app.get('/')
    
    # Check that the response status code is 200
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.body, 'html.parser')
    
    # Check that the govsp-topo section exists
    govsp_topo = soup.find('div', id='govsp-topo')
    assert govsp_topo is not None
    
    # Check that it's a direct child of the body (full width)
    assert govsp_topo.parent.name == 'body'


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_templates_directory_structure():
    """Test that the templates directory has the expected structure."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the path to the templates directory
    templates_dir = os.path.join(os.path.dirname(plugin.__file__), 'templates')
    
    # Check that the templates directory exists
    assert os.path.isdir(templates_dir)
    
    # Check that the static directory exists
    static_dir = os.path.join(templates_dir, 'static')
    assert os.path.isdir(static_dir)
    
    # Check that the static pages exist
    about_ckan_file = os.path.join(static_dir, 'about_ckan.html')
    assert os.path.isfile(about_ckan_file)
    
    terms_file = os.path.join(static_dir, 'terms.html')
    assert os.path.isfile(terms_file)
    
    privacy_file = os.path.join(static_dir, 'privacy.html')
    assert os.path.isfile(privacy_file)
    
    contact_file = os.path.join(static_dir, 'contact.html')
    assert os.path.isfile(contact_file)
    
    # Check that the base template exists
    base_file = os.path.join(static_dir, 'base.html')
    assert os.path.isfile(base_file)
