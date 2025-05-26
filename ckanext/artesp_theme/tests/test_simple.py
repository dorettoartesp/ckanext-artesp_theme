"""Simple tests that don't require CKAN environment."""

import os
import pytest
from unittest import mock

import ckanext.artesp_theme.helpers as helpers


def test_artesp_theme_hello():
    """Test the artesp_theme_hello helper function."""
    assert helpers.artesp_theme_hello() == "Hello, artesp_theme!"


def test_fix_fontawesome_icon():
    """Test that fix_fontawesome_icon creates the correct HTML."""
    # Test with a simple icon name
    result = helpers.fix_fontawesome_icon('home')
    
    # Check that the result is the correct HTML
    assert str(result) == '<i class="fa fa-home"></i> '


def test_get_year():
    """Test that get_year returns the current year."""
    import datetime
    # Get the current year
    current_year = datetime.datetime.now().year
    
    # Call the helper function
    result = helpers.get_year()
    
    # Check that the result is the current year
    assert result == current_year
