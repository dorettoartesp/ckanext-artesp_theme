"""Tests for internationalization features.

Tests the internationalization features of the ARTESP theme extension.
"""

import os
import pytest
import polib
from unittest import mock

import ckan.plugins as plugins
import ckanext.artesp_theme.plugin as plugin


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_i18n_directory_exists():
    """Test that the i18n directory exists."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Check that the directory exists
    assert os.path.isdir(i18n_dir)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_pt_br_locale_exists():
    """Test that the pt_BR locale directory exists."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Check that the pt_BR locale directory exists
    pt_br_dir = os.path.join(i18n_dir, 'pt_BR')
    assert os.path.isdir(pt_br_dir)
    
    # Check that the LC_MESSAGES directory exists
    lc_messages_dir = os.path.join(pt_br_dir, 'LC_MESSAGES')
    assert os.path.isdir(lc_messages_dir)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_translation_files_exist():
    """Test that the translation files exist."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Check that the .po file exists
    po_file = os.path.join(i18n_dir, 'pt_BR', 'LC_MESSAGES', 'ckanext-artesp_theme.po')
    assert os.path.isfile(po_file)
    
    # Check that the .mo file exists
    mo_file = os.path.join(i18n_dir, 'pt_BR', 'LC_MESSAGES', 'ckanext-artesp_theme.mo')
    assert os.path.isfile(mo_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_pot_file_exists():
    """Test that the .pot file exists."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Check that the .pot file exists
    pot_file = os.path.join(i18n_dir, 'ckanext-artesp_theme.pot')
    assert os.path.isfile(pot_file)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_po_file_has_translations():
    """Test that the .po file has translations."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Get the .po file
    po_file = os.path.join(i18n_dir, 'pt_BR', 'LC_MESSAGES', 'ckanext-artesp_theme.po')
    
    # Parse the .po file
    po = polib.pofile(po_file)
    
    # Check that there are entries in the .po file
    assert len(po) > 0
    
    # Check that at least some entries have translations
    translated_entries = [entry for entry in po if entry.msgstr]
    assert len(translated_entries) > 0


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_static_page_translations():
    """Test that static pages have translations."""
    # Get the plugin instance
    plugin_instance = plugins.get_plugin("artesp_theme")
    
    # Get the i18n directory
    i18n_dir = plugin_instance.i18n_directory()
    
    # Get the .po file
    po_file = os.path.join(i18n_dir, 'pt_BR', 'LC_MESSAGES', 'ckanext-artesp_theme.po')
    
    # Parse the .po file
    po = polib.pofile(po_file)
    
    # Check for translations of common static page content
    static_page_strings = [
        "About CKAN",
        "Terms of Use",
        "Privacy Policy",
        "Contact Us"
    ]
    
    # Count how many of these strings have translations
    translated_count = 0
    for string in static_page_strings:
        for entry in po:
            if string in entry.msgid and entry.msgstr:
                translated_count += 1
                break
    
    # Check that at least some static page strings have translations
    assert translated_count > 0
