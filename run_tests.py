#!/usr/bin/env python
"""
Simple test runner for the ARTESP theme extension.
This script runs tests without requiring the full CKAN testing infrastructure.
"""

import os
import sys
import subprocess

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def run_test_file(file_path):
    """Run a test file using the unittest module."""
    print(f"\n{YELLOW}Running tests in {os.path.basename(file_path)}{RESET}")

    # Run the test file as a separate process
    result = subprocess.run(
        [sys.executable, file_path],
        capture_output=True,
        text=True
    )

    # Print the output
    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(f"{RED}{result.stderr}{RESET}")

    # Return True if the tests passed, False otherwise
    return result.returncode == 0

def run_standalone_tests():
    """Run standalone tests that don't require CKAN."""
    # Define the test files that can run without CKAN dependencies
    standalone_test_files = [
        'ckanext/artesp_theme/tests/test_file_structure.py',
        'ckanext/artesp_theme/tests/test_simple_helpers.py',
        'ckanext/artesp_theme/tests/test_simple_middleware.py',
        'ckanext/artesp_theme/tests/test_simple_plugin.py',
    ]

    passed_files = 0
    total_files = len(standalone_test_files)

    for file_path in standalone_test_files:
        if run_test_file(file_path):
            passed_files += 1

    print(f"\n{YELLOW}Summary:{RESET}")
    print(f"Ran {total_files} test files, {passed_files} passed, {total_files - passed_files} failed")

    return passed_files == total_files

if __name__ == "__main__":
    print(f"{YELLOW}Running standalone tests for ARTESP theme extension{RESET}")
    success = run_standalone_tests()
    sys.exit(0 if success else 1)
