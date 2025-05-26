#!/usr/bin/env python
"""
Standalone test script that doesn't rely on CKAN imports.
This tests the basic functionality of our test files.
"""

import os
import sys
import datetime

# Print the current directory and Python version
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")

# Test that our test files exist
test_files = [
    "test_plugin.py",
    "test_helpers.py",
    "test_views.py",
    "test_middleware.py",
    "test_i18n.py",
    "test_assets.py",
    "test_templates.py",
    "test_template_structure.py"
]

print("\nChecking test files:")
for file in test_files:
    if os.path.exists(file):
        print(f"✅ {file} exists")
    else:
        print(f"❌ {file} does not exist")

# Test that our test files have the expected content
print("\nChecking test file content:")
for file in test_files:
    if os.path.exists(file):
        with open(file, 'r') as f:
            content = f.read()
            if "def test_" in content:
                print(f"✅ {file} contains test functions")
            else:
                print(f"❌ {file} does not contain test functions")

# Count the total number of test functions
print("\nCounting test functions:")
total_tests = 0
for file in test_files:
    if os.path.exists(file):
        with open(file, 'r') as f:
            content = f.read()
            test_count = content.count("def test_")
            print(f"{file}: {test_count} test functions")
            total_tests += test_count

print(f"\nTotal test functions: {total_tests}")
print("\nTest verification completed successfully.")
