"""Tests for middleware.py.

Tests the FontAwesomeFixMiddleware and make_middleware function.
"""

import pytest
from unittest import mock

from ckanext.artesp_theme.middleware import FontAwesomeFixMiddleware, make_middleware


def test_fontawesome_fix_middleware_init():
    """Test that the FontAwesomeFixMiddleware initializes correctly."""
    # Create a mock app
    mock_app = mock.MagicMock()
    
    # Create the middleware
    middleware = FontAwesomeFixMiddleware(mock_app)
    
    # Check that the app was stored correctly
    assert middleware.app == mock_app
    
    # Check that the pattern was compiled
    assert middleware.pattern is not None


def test_fontawesome_fix_middleware_call_non_html():
    """Test that the middleware passes through non-HTML responses unchanged."""
    # Create a mock app that returns a non-HTML response
    mock_app = mock.MagicMock()
    mock_app.return_value = [b'{"key": "value"}']
    
    # Create a mock start_response function
    mock_start_response = mock.MagicMock()
    
    # Create the middleware
    middleware = FontAwesomeFixMiddleware(mock_app)
    
    # Call the middleware with a request that returns a non-HTML response
    environ = {}
    headers = [('Content-Type', 'application/json')]
    
    # Mock the app to call start_response with the headers
    def mock_app_side_effect(environ, start_response):
        start_response('200 OK', headers)
        return [b'{"key": "value"}']
    
    mock_app.side_effect = mock_app_side_effect
    
    # Call the middleware
    result = middleware(environ, mock_start_response)
    
    # Check that the app was called with the correct arguments
    mock_app.assert_called_once_with(environ, mock_start_response)
    
    # Check that the result is the same as the app's return value
    assert result == [b'{"key": "value"}']


def test_fontawesome_fix_middleware_call_html_with_double_encoded_icons():
    """Test that the middleware fixes double-encoded Font Awesome icons in HTML responses."""
    # Create a mock app that returns an HTML response with double-encoded icons
    mock_app = mock.MagicMock()
    
    # Create a mock start_response function
    mock_start_response = mock.MagicMock()
    
    # Create the middleware
    middleware = FontAwesomeFixMiddleware(mock_app)
    
    # Call the middleware with a request that returns an HTML response with double-encoded icons
    environ = {}
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # HTML with double-encoded Font Awesome icons
    html_with_icons = b'<html><body>Test &amp;lt;i class=&amp;quot;fa fa-home&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;</body></html>'
    
    # Mock the app to call start_response with the headers and return the HTML
    def mock_app_side_effect(environ, start_response):
        start_response('200 OK', headers)
        return [html_with_icons]
    
    mock_app.side_effect = mock_app_side_effect
    
    # Call the middleware
    result = middleware(environ, mock_start_response)
    
    # Check that the app was called with the correct arguments
    mock_app.assert_called_once()
    
    # Check that the result contains the fixed HTML
    assert b'<i class="fa fa-home"></i>' in result[0]


def test_fontawesome_fix_middleware_call_html_without_double_encoded_icons():
    """Test that the middleware doesn't change HTML responses without double-encoded icons."""
    # Create a mock app that returns an HTML response without double-encoded icons
    mock_app = mock.MagicMock()
    
    # Create a mock start_response function
    mock_start_response = mock.MagicMock()
    
    # Create the middleware
    middleware = FontAwesomeFixMiddleware(mock_app)
    
    # Call the middleware with a request that returns an HTML response without double-encoded icons
    environ = {}
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # HTML without double-encoded Font Awesome icons
    html_without_icons = b'<html><body>Test <i class="fa fa-home"></i></body></html>'
    
    # Mock the app to call start_response with the headers and return the HTML
    def mock_app_side_effect(environ, start_response):
        start_response('200 OK', headers)
        return [html_without_icons]
    
    mock_app.side_effect = mock_app_side_effect
    
    # Call the middleware
    result = middleware(environ, mock_start_response)
    
    # Check that the app was called with the correct arguments
    mock_app.assert_called_once()
    
    # Check that the result is the same as the input HTML (no changes)
    assert b'<i class="fa fa-home"></i>' in result[0]


def test_make_middleware_with_flask_app():
    """Test that make_middleware correctly handles Flask apps."""
    # Create a mock Flask app
    mock_flask_app = mock.MagicMock()
    mock_flask_app.after_request = mock.MagicMock()
    
    # Call make_middleware with the Flask app
    result = make_middleware(mock_flask_app)
    
    # Check that the result is the Flask app
    assert result == mock_flask_app
    
    # Check that after_request was called
    assert mock_flask_app.after_request.called


def test_make_middleware_with_wsgi_app():
    """Test that make_middleware correctly handles WSGI apps."""
    # Create a mock WSGI app
    mock_wsgi_app = mock.MagicMock()
    
    # Call make_middleware with the WSGI app
    result = make_middleware(mock_wsgi_app)
    
    # Check that the result is a FontAwesomeFixMiddleware instance
    assert isinstance(result, FontAwesomeFixMiddleware)
    
    # Check that the middleware's app is the WSGI app
    assert result.app == mock_wsgi_app
