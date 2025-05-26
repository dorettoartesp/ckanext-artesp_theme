"""Tests for assets.

Tests the CSS and JS assets of the ARTESP theme extension.
"""

import os
import pytest
import yaml
from unittest import mock

import ckan.plugins as plugins
import ckanext.artesp_theme.plugin as plugin


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_webassets_yml_exists():
    """Test that the webassets.yml file exists."""
    # Get the path to the assets directory
    assets_dir = os.path.join(os.path.dirname(plugin.__file__), 'assets')
    
    # Check that the webassets.yml file exists
    webassets_yml = os.path.join(assets_dir, 'webassets.yml')
    assert os.path.isfile(webassets_yml)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_webassets_yml_content():
    """Test that the webassets.yml file has the expected content."""
    # Get the path to the assets directory
    assets_dir = os.path.join(os.path.dirname(plugin.__file__), 'assets')
    
    # Get the webassets.yml file
    webassets_yml = os.path.join(assets_dir, 'webassets.yml')
    
    # Parse the YAML file
    with open(webassets_yml, 'r') as f:
        webassets = yaml.safe_load(f)
    
    # Check that the expected bundles are defined
    assert 'artesp-theme-js' in webassets
    assert 'artesp-theme-css' in webassets
    
    # Check that the JS bundle has the expected properties
    js_bundle = webassets['artesp-theme-js']
    assert 'filter' in js_bundle
    assert 'output' in js_bundle
    assert 'contents' in js_bundle
    
    # Check that the CSS bundle has the expected properties
    css_bundle = webassets['artesp-theme-css']
    assert 'filter' in css_bundle
    assert 'output' in css_bundle
    assert 'contents' in css_bundle


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_js_files_exist():
    """Test that the JS files referenced in webassets.yml exist."""
    # Get the path to the assets directory
    assets_dir = os.path.join(os.path.dirname(plugin.__file__), 'assets')
    
    # Get the webassets.yml file
    webassets_yml = os.path.join(assets_dir, 'webassets.yml')
    
    # Parse the YAML file
    with open(webassets_yml, 'r') as f:
        webassets = yaml.safe_load(f)
    
    # Get the JS files
    js_files = webassets['artesp-theme-js']['contents']
    
    # Check that each JS file exists
    for js_file in js_files:
        js_path = os.path.join(assets_dir, js_file)
        assert os.path.isfile(js_path), f"JS file {js_file} does not exist"


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_css_files_exist():
    """Test that the CSS files referenced in webassets.yml exist."""
    # Get the path to the assets directory
    assets_dir = os.path.join(os.path.dirname(plugin.__file__), 'assets')
    
    # Get the webassets.yml file
    webassets_yml = os.path.join(assets_dir, 'webassets.yml')
    
    # Parse the YAML file
    with open(webassets_yml, 'r') as f:
        webassets = yaml.safe_load(f)
    
    # Get the CSS files
    css_files = webassets['artesp-theme-css']['contents']
    
    # Check that each CSS file exists
    for css_file in css_files:
        css_path = os.path.join(assets_dir, css_file)
        assert os.path.isfile(css_path), f"CSS file {css_file} does not exist"


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_css_modules_structure():
    """Test that the CSS modules follow the expected structure."""
    # Get the path to the assets directory
    assets_dir = os.path.join(os.path.dirname(plugin.__file__), 'assets')
    
    # Get the webassets.yml file
    webassets_yml = os.path.join(assets_dir, 'webassets.yml')
    
    # Parse the YAML file
    with open(webassets_yml, 'r') as f:
        webassets = yaml.safe_load(f)
    
    # Get the CSS files
    css_files = webassets['artesp-theme-css']['contents']
    
    # Check that the CSS files follow the expected structure
    # Variables should come first
    assert any('variables.css' in css_file for css_file in css_files[:2]), "variables.css should be one of the first CSS files"
    
    # Base styles should come early
    assert any('base.css' in css_file for css_file in css_files[:3]), "base.css should be one of the first CSS files"
    
    # Layout should come before components
    layout_index = next((i for i, css_file in enumerate(css_files) if 'layout.css' in css_file), -1)
    components_index = next((i for i, css_file in enumerate(css_files) if 'components.css' in css_file), -1)
    assert layout_index < components_index, "layout.css should come before components.css"
    
    # Responsive should come last
    responsive_index = next((i for i, css_file in enumerate(css_files) if 'responsive.css' in css_file), -1)
    assert responsive_index > -1, "responsive.css should be included"
    assert responsive_index > components_index, "responsive.css should come after components.css"
