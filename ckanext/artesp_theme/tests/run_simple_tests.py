#!/usr/bin/env python
"""
Simple script to test helper functions directly without using pytest.
"""

import sys
import os
import datetime
from markupsafe import Markup

# Get the absolute path to the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the helpers module directly
import helpers

def test_artesp_theme_hello():
    """Test the artesp_theme_hello helper function."""
    result = helpers.artesp_theme_hello()
    expected = "Hello, artesp_theme!"

    if result == expected:
        print(f"✅ test_artesp_theme_hello: PASSED")
    else:
        print(f"❌ test_artesp_theme_hello: FAILED")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")


def test_fix_fontawesome_icon():
    """Test that fix_fontawesome_icon creates the correct HTML."""
    # Test with a simple icon name
    result = helpers.fix_fontawesome_icon('home')
    expected = '<i class="fa fa-home"></i> '

    if str(result) == expected and isinstance(result, Markup):
        print(f"✅ test_fix_fontawesome_icon: PASSED")
    else:
        print(f"❌ test_fix_fontawesome_icon: FAILED")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print(f"  Type: {type(result)}")


def test_get_year():
    """Test that get_year returns the current year."""
    # Get the current year
    current_year = datetime.datetime.now().year

    # Call the helper function
    result = helpers.get_year()

    if result == current_year:
        print(f"✅ test_get_year: PASSED")
    else:
        print(f"❌ test_get_year: FAILED")
        print(f"  Expected: {current_year}")
        print(f"  Got: {result}")


def test_safe_html_with_double_encoded_html():
    """Test that safe_html correctly decodes double-encoded HTML."""
    # Test with double-encoded HTML
    double_encoded = '&amp;lt;i class=&amp;quot;fa fa-home&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
    result = helpers.safe_html(double_encoded)
    expected = '<i class="fa fa-home"></i>'

    if str(result) == expected and isinstance(result, Markup):
        print(f"✅ test_safe_html_with_double_encoded_html: PASSED")
    else:
        print(f"❌ test_safe_html_with_double_encoded_html: FAILED")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print(f"  Type: {type(result)}")


def test_safe_html_with_regular_string():
    """Test that safe_html returns regular strings unchanged."""
    # Test with a regular string
    regular_string = 'Hello, world!'
    result = helpers.safe_html(regular_string)

    if result == regular_string:
        print(f"✅ test_safe_html_with_regular_string: PASSED")
    else:
        print(f"❌ test_safe_html_with_regular_string: FAILED")
        print(f"  Expected: {regular_string}")
        print(f"  Got: {result}")


def test_safe_html_with_none():
    """Test that safe_html handles None values correctly."""
    # Test with None
    result = helpers.safe_html(None)

    if result is None:
        print(f"✅ test_safe_html_with_none: PASSED")
    else:
        print(f"❌ test_safe_html_with_none: FAILED")
        print(f"  Expected: None")
        print(f"  Got: {result}")


if __name__ == "__main__":
    print("Running simple tests for helper functions...")
    test_artesp_theme_hello()
    test_fix_fontawesome_icon()
    test_get_year()
    test_safe_html_with_double_encoded_html()
    test_safe_html_with_regular_string()
    test_safe_html_with_none()
    print("All tests completed.")
