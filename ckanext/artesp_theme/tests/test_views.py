"""Tests for controllers.py.

Tests the Flask blueprint routes and controllers provided by the ARTESP theme extension.
"""

import pytest
from unittest import mock
from flask import g

import ckan.plugins.toolkit as tk
from ckan.tests import factories


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_about_ckan_page(app):
    """Test that the about_ckan page returns a 200 response."""
    # Get the URL for the about_ckan page
    url = tk.h.url_for("artesp_theme.about_ckan")

    # Make a GET request to the URL
    response = app.get(url)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response contains expected content
    assert "About CKAN" in response.body.decode('utf-8')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_terms_page(app):
    """Test that the terms page returns a 200 response."""
    # Get the URL for the terms page
    url = tk.h.url_for("artesp_theme.terms")

    # Make a GET request to the URL
    response = app.get(url)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response contains expected content
    assert "Terms" in response.body.decode('utf-8')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_privacy_page(app):
    """Test that the privacy page returns a 200 response."""
    # Get the URL for the privacy page
    url = tk.h.url_for("artesp_theme.privacy")

    # Make a GET request to the URL
    response = app.get(url)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response contains expected content
    assert "Privacy" in response.body.decode('utf-8')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_contact_page(app):
    """Test that the contact page returns a 200 response."""
    # Get the URL for the contact page
    url = tk.h.url_for("artesp_theme.contact")

    # Make a GET request to the URL
    response = app.get(url)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response contains expected content
    assert "Contact" in response.body.decode('utf-8')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_harvesting_page(app):
    """Test that the harvesting page returns a 200 response."""
    # Get the URL for the harvesting page
    url = tk.h.url_for("artesp_theme.harvesting")

    # Make a GET request to the URL
    response = app.get(url)

    # Check that the response status code is 200
    assert response.status_code == 200

    # Check that the response contains expected content
    assert "Harvesting" in response.body.decode('utf-8')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_stats_page_access_restriction_anonymous(monkeypatch):
    """Test that anonymous users are redirected from the stats page."""
    # Mock the request path to be '/stats'
    monkeypatch.setattr('flask.request.path', '/stats')

    # Mock g.user to be None (anonymous user)
    monkeypatch.setattr(g, 'user', None)

    # Mock the flash_error and redirect_to functions
    with mock.patch('ckan.lib.helpers.flash_error') as mock_flash_error, \
         mock.patch('ckan.lib.helpers.redirect_to') as mock_redirect_to:

        # Mock redirect_to to return a specific URL
        mock_redirect_to.return_value = '/user/login'

        # Import the function to test
        from ckanext.artesp_theme.controllers import restrict_stats_page_access

        # Call the function
        result = restrict_stats_page_access()

        # Check that flash_error was called with the correct message
        mock_flash_error.assert_called_once_with(tk._('You must be logged in to access the statistics page.'))

        # Check that redirect_to was called with the correct URL
        mock_redirect_to.assert_called_once_with(tk.url_for('user.login'))

        # Check that the result is the redirect URL
        assert result == '/user/login'


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_stats_page_access_restriction_authenticated(monkeypatch):
    """Test that authenticated users can access the stats page."""
    # Create a user
    user = factories.User()

    # Mock the request path to be '/stats'
    monkeypatch.setattr('flask.request.path', '/stats')

    # Mock g.user to be the user's name (authenticated user)
    monkeypatch.setattr(g, 'user', user['name'])

    # Import the function to test
    from ckanext.artesp_theme.controllers import restrict_stats_page_access

    # Call the function
    result = restrict_stats_page_access()

    # Check that the result is None (no redirect)
    assert result is None


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_non_stats_page_access(monkeypatch):
    """Test that the stats page access restriction doesn't affect other pages."""
    # Mock the request path to be something other than '/stats'
    monkeypatch.setattr('flask.request.path', '/dataset')

    # Mock g.user to be None (anonymous user)
    monkeypatch.setattr(g, 'user', None)

    # Import the function to test
    from ckanext.artesp_theme.controllers import restrict_stats_page_access

    # Call the function
    result = restrict_stats_page_access()

    # Check that the result is None (no redirect)
    assert result is None
