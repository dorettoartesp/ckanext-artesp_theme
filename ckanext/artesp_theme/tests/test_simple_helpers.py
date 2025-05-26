"""Tests for helpers using unittest.

Tests the helper functions without requiring CKAN imports.
"""

import os
import sys
import unittest
import datetime
from unittest import mock

# Get the absolute path to the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the helpers module directly
try:
    from markupsafe import Markup
    import helpers
    MARKUPSAFE_AVAILABLE = True
except ImportError:
    MARKUPSAFE_AVAILABLE = False


@unittest.skipIf(not MARKUPSAFE_AVAILABLE, "MarkupSafe not available")
class TestHelpers(unittest.TestCase):
    """Test the helper functions."""
    
    def test_artesp_theme_hello(self):
        """Test the artesp_theme_hello helper function."""
        self.assertEqual(helpers.artesp_theme_hello(), "Hello, artesp_theme!")
    
    def test_get_year(self):
        """Test that get_year returns the current year."""
        current_year = datetime.datetime.now().year
        self.assertEqual(helpers.get_year(), current_year)
    
    @unittest.skipIf(not hasattr(helpers, 'safe_html'), "safe_html function not available")
    def test_safe_html_with_double_encoded_html(self):
        """Test that safe_html correctly decodes double-encoded HTML."""
        double_encoded = '&amp;lt;i class=&amp;quot;fa fa-home&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
        result = helpers.safe_html(double_encoded)
        
        # Check that the result is a Markup object
        self.assertIsInstance(result, Markup)
        
        # Check that the result is the correctly decoded HTML
        self.assertEqual(str(result), '<i class="fa fa-home"></i>')
    
    @unittest.skipIf(not hasattr(helpers, 'safe_html'), "safe_html function not available")
    def test_safe_html_with_regular_string(self):
        """Test that safe_html returns regular strings unchanged."""
        regular_string = 'Hello, world!'
        result = helpers.safe_html(regular_string)
        
        # Check that the result is the same string
        self.assertEqual(result, regular_string)
    
    @unittest.skipIf(not hasattr(helpers, 'safe_html'), "safe_html function not available")
    def test_safe_html_with_none(self):
        """Test that safe_html handles None values correctly."""
        result = helpers.safe_html(None)
        
        # Check that the result is None
        self.assertIsNone(result)
    
    @unittest.skipIf(not hasattr(helpers, 'fix_fontawesome_icon'), "fix_fontawesome_icon function not available")
    def test_fix_fontawesome_icon(self):
        """Test that fix_fontawesome_icon creates the correct HTML."""
        result = helpers.fix_fontawesome_icon('home')
        
        # Check that the result is a Markup object
        self.assertIsInstance(result, Markup)
        
        # Check that the result is the correct HTML
        self.assertEqual(str(result), '<i class="fa fa-home"></i> ')


if __name__ == '__main__':
    unittest.main()
