"""Tests for middleware using unittest.

Tests the middleware functions without requiring CKAN imports.
"""

import os
import sys
import unittest
from unittest import mock

# Get the absolute path to the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the middleware module directly
try:
    import middleware
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False


@unittest.skipIf(not MIDDLEWARE_AVAILABLE, "Middleware module not available")
class TestMiddleware(unittest.TestCase):
    """Test the middleware functions."""

    def test_fontawesome_fix_middleware_init(self):
        """Test that the FontAwesomeFixMiddleware initializes correctly."""
        # Create a mock app
        mock_app = mock.MagicMock()

        # Create the middleware
        middleware_instance = middleware.FontAwesomeFixMiddleware(mock_app)

        # Check that the app was stored correctly
        self.assertEqual(middleware_instance.app, mock_app)

        # Check that the pattern was compiled
        self.assertIsNotNone(middleware_instance.pattern)

    def test_fontawesome_fix_middleware_call_non_html(self):
        """Test that the middleware passes through non-HTML responses unchanged."""
        # Create a mock app that returns a non-HTML response
        mock_app = mock.MagicMock()

        # Create a mock start_response function
        mock_start_response = mock.MagicMock()

        # Create the middleware
        middleware_instance = middleware.FontAwesomeFixMiddleware(mock_app)

        # Call the middleware with a request that returns a non-HTML response
        environ = {}
        headers = [('Content-Type', 'application/json')]

        # Mock the app to call start_response with the headers
        def mock_app_side_effect(environ, start_response):
            start_response('200 OK', headers)
            return [b'{"key": "value"}']

        mock_app.side_effect = mock_app_side_effect

        # Call the middleware
        result = middleware_instance(environ, mock_start_response)

        # Check that the app was called
        self.assertTrue(mock_app.called)

        # Check that the result contains the expected JSON
        self.assertEqual(result[0], b'{"key": "value"}')

    def test_make_middleware_with_wsgi_app(self):
        """Test that make_middleware correctly handles WSGI apps."""
        # Create a mock WSGI app (without after_request attribute)
        mock_wsgi_app = mock.MagicMock(spec=[])

        # Call make_middleware with the WSGI app
        result = middleware.make_middleware(mock_wsgi_app, {})

        # Check that the result is a FontAwesomeFixMiddleware instance
        self.assertIsInstance(result, middleware.FontAwesomeFixMiddleware)

        # Check that the middleware's app is the WSGI app
        self.assertEqual(result.app, mock_wsgi_app)


if __name__ == '__main__':
    unittest.main()
