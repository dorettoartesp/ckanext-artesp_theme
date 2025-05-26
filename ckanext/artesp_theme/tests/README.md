# CKAN ARTESP Theme Extension Tests

This directory contains the test suite for the CKAN ARTESP theme extension. The tests are organized by functionality and follow CKAN's testing conventions.

## Test Organization

The test files are organized as follows:

- **test_plugin.py**: Tests for the ArtespThemePlugin class and its implementation of various CKAN interfaces (IConfigurer, ITemplateHelpers, IBlueprint, ITranslation, IMiddleware).
- **test_helpers.py**: Tests for all helper functions provided by the extension, including statistics helpers, HTML utilities, and dataset/resource retrieval functions.
- **test_views.py**: Tests for the Flask blueprint routes and controllers (about_ckan, terms, privacy, contact, harvesting) and the stats page access restriction.
- **test_middleware.py**: Tests for the FontAwesomeFixMiddleware and make_middleware function.
- **test_i18n.py**: Tests for internationalization features, including translation file existence and content.
- **test_assets.py**: Tests for CSS and JS asset configuration and proper structure of CSS modules.
- **test_templates.py**: Tests for template overrides and customizations, including key UI elements like the hero section, latest datasets, and stats.
- **test_template_structure.py**: Tests for the existence of template directories and files.
- **test_standalone.py**: A utility script to verify the existence and content of test files without running the actual tests.

## Running the Tests

### Prerequisites

To run the tests, you need a properly configured CKAN development environment with the following dependencies:

- Python 3.6+
- pytest
- pytest-ckan
- CKAN development installation

### Recommended: Running Tests in Docker

The most reliable way to run the tests is using the CKAN Docker container, where all dependencies are correctly configured:

```bash
# From the root directory of the artesp-ckan-ui project
docker-compose exec ckan bash -c "cd /usr/lib/ckan/default/src/ckanext-artesp_theme && python -m pytest -xvs ckanext/artesp_theme/tests/"
```

This approach ensures that all dependencies are correctly installed and configured.

### Running Tests Locally

If you prefer to run tests locally, make sure you have the correct environment set up:

#### Running All Tests

From the root directory of the extension, run:

```bash
python -m pytest -xvs ckanext/artesp_theme/tests/
```

#### Running Specific Test Files

To run tests from a specific file:

```bash
python -m pytest -xvs ckanext/artesp_theme/tests/test_helpers.py
```

#### Running Specific Test Functions

To run a specific test function:

```bash
python -m pytest -xvs ckanext/artesp_theme/tests/test_helpers.py::test_artesp_theme_hello
```

### Running the Standalone Test Verification

If you're having trouble running the tests with pytest, you can use the standalone verification script:

```bash
cd ckanext/artesp_theme/tests/
python test_standalone.py
```

This will verify that all test files exist and contain test functions without actually running the tests. The script will output a summary of all test files and the number of test functions in each file.

## Test Coverage

The test suite covers:

1. **Plugin Configuration**: Tests for proper registration of templates, public directories, and assets.
2. **Helper Functions**: Tests for all helper functions, including error handling.
3. **Views and Controllers**: Tests for all routes and access restrictions.
4. **Middleware**: Tests for the Font Awesome icon fixing middleware.
5. **Internationalization**: Tests for translation files and content.
6. **Assets**: Tests for CSS and JS asset configuration.
7. **Templates**: Tests for template overrides and customizations.

## Writing New Tests

When adding new functionality to the extension, please follow these guidelines for writing tests:

1. Create tests in the appropriate test file based on functionality.
2. Follow CKAN's testing conventions and patterns.
3. Use pytest fixtures and mocks where appropriate.
4. Include docstrings explaining the purpose of each test.
5. Use descriptive test function names that clearly indicate what is being tested.

## Troubleshooting

If you encounter issues running the tests:

1. Ensure you have activated the CKAN virtual environment.
2. Verify that all dependencies are installed.
3. Check that your CKAN configuration is correct.
4. Try running the standalone test verification script to check that the test files are properly structured.

### Known Issues

#### RQ Compatibility Issue

You may encounter the following error when running the tests:

```
ImportError: cannot import name 'push_connection' from 'rq.connections'
```

This is due to a compatibility issue between the installed version of RQ (Redis Queue) and the version expected by CKAN. To resolve this:

1. Install a compatible version of RQ:
   ```bash
   pip install rq==1.10.1
   ```

2. If you still encounter issues, you can use the standalone test verification script:
   ```bash
   python test_standalone.py
   ```

#### Python 3 Compatibility with Pylons

You may also encounter a syntax error related to Pylons:

```
SyntaxError: multiple exception types must be parenthesized
```

This occurs because Pylons uses Python 2 syntax for exception handling. To work around this:

1. Run tests in a Python 2.7 environment if possible
2. Use the standalone test verification script to verify test structure
3. Consider running individual test modules that don't depend on Pylons

### Alternative Testing Approaches

If you're unable to run the tests with pytest-ckan due to compatibility issues, consider these alternatives:

1. **Standalone Verification**: Use `test_standalone.py` to verify test structure without running the tests.

2. **Docker-based Testing**: Run tests in the CKAN Docker container where all dependencies are correctly configured:
   ```bash
   docker-compose exec ckan pytest -xvs /usr/lib/ckan/default/src/ckanext-artesp_theme/ckanext/artesp_theme/tests/
   ```

3. **Manual Testing**: Test the extension functionality manually in a running CKAN instance.

For more information on CKAN testing, see the [CKAN testing documentation](https://docs.ckan.org/en/latest/contributing/testing.html).
