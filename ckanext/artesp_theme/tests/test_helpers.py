"""Tests for helpers.py.

Tests the helper functions provided by the ARTESP theme extension.
"""

import datetime
import pytest
from unittest import mock
from markupsafe import Markup

import ckan.tests.factories as factories
import ckanext.artesp_theme.helpers as helpers


def test_artesp_theme_hello():
    """Test the artesp_theme_hello helper function."""
    assert helpers.artesp_theme_hello() == "Hello, artesp_theme!"


def test_safe_html_with_double_encoded_html():
    """Test that safe_html correctly decodes double-encoded HTML."""
    # Test with double-encoded HTML
    double_encoded = '&amp;lt;i class=&amp;quot;fa fa-home&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
    result = helpers.safe_html(double_encoded)

    # Check that the result is a Markup object
    assert isinstance(result, Markup)

    # Check that the result is the correctly decoded HTML
    assert str(result) == '<i class="fa fa-home"></i>'


def test_safe_html_with_regular_string():
    """Test that safe_html returns regular strings unchanged."""
    # Test with a regular string
    regular_string = 'Hello, world!'
    result = helpers.safe_html(regular_string)

    # Check that the result is the same string
    assert result == regular_string


def test_safe_html_with_none():
    """Test that safe_html handles None values correctly."""
    # Test with None
    result = helpers.safe_html(None)

    # Check that the result is None
    assert result is None


def test_fix_fontawesome_icon():
    """Test that fix_fontawesome_icon creates the correct HTML."""
    # Test with a simple icon name
    result = helpers.fix_fontawesome_icon('home')

    # Check that the result is a Markup object
    assert isinstance(result, Markup)

    # Check that the result is the correct HTML
    assert str(result) == '<i class="fa fa-home"></i> '


@pytest.mark.usefixtures("clean_db")
def test_get_package_count():
    """Test that get_package_count returns the correct count."""
    # Create some datasets
    factories.Dataset()
    factories.Dataset()
    factories.Dataset()

    # Mock the package_search action to return a fixed count
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(return_value={'count': 3})
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_package_count()

        # Check that the result is the correct count
        assert result == 3


@pytest.mark.usefixtures("clean_db")
def test_get_package_count_error():
    """Test that get_package_count handles errors correctly."""
    # Mock the package_search action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_package_count()

        # Check that the result is 0
        assert result == 0


@pytest.mark.usefixtures("clean_db")
def test_get_resource_count():
    """Test that get_resource_count returns the correct count."""
    # Create a dataset with resources
    dataset = factories.Dataset()
    factories.Resource(package_id=dataset['id'])
    factories.Resource(package_id=dataset['id'])

    # Mock the package_search action to return a fixed result
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(return_value={
            'results': [
                {'resources': [{'id': 'res1'}, {'id': 'res2'}]},
                {'resources': [{'id': 'res3'}]}
            ]
        })
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_resource_count()

        # Check that the result is the correct count
        assert result == 3


@pytest.mark.usefixtures("clean_db")
def test_get_resource_count_error():
    """Test that get_resource_count handles errors correctly."""
    # Mock the package_search action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_resource_count()

        # Check that the result is 0
        assert result == 0


@pytest.mark.usefixtures("clean_db")
def test_get_latest_datasets():
    """Test that get_latest_datasets returns the correct datasets."""
    # Create some datasets
    dataset1 = factories.Dataset()
    dataset2 = factories.Dataset()
    dataset3 = factories.Dataset()

    # Mock the package_search action to return a fixed result
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(return_value={
            'results': [dataset1, dataset2, dataset3]
        })
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_latest_datasets(limit=3)

        # Check that the result is the correct list of datasets
        assert result == [dataset1, dataset2, dataset3]

        # Check that package_search was called with the correct parameters
        mock_package_search.assert_called_once_with(
            {},
            {
                'rows': 3,
                'sort': 'metadata_created desc',
                'include_private': False
            }
        )


@pytest.mark.usefixtures("clean_db")
def test_get_latest_datasets_error():
    """Test that get_latest_datasets handles errors correctly."""
    # Mock the package_search action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_package_search = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_package_search

        # Call the helper function
        result = helpers.get_latest_datasets()

        # Check that the result is an empty list
        assert result == []


@pytest.mark.usefixtures("clean_db")
def test_get_organization_count():
    """Test that get_organization_count returns the correct count."""
    # Create some organizations
    factories.Organization()
    factories.Organization()

    # Mock the organization_list action to return a fixed result
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_organization_list = mock.MagicMock(return_value=['org1', 'org2'])
        mock_get_action.return_value = mock_organization_list

        # Call the helper function
        result = helpers.get_organization_count()

        # Check that the result is the correct count
        assert result == 2

        # Check that organization_list was called with the correct parameters
        mock_organization_list.assert_called_once_with({}, {'all_fields': False})


@pytest.mark.usefixtures("clean_db")
def test_get_organization_count_error():
    """Test that get_organization_count handles errors correctly."""
    # Mock the organization_list action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_organization_list = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_organization_list

        # Call the helper function
        result = helpers.get_organization_count()

        # Check that the result is 0
        assert result == 0


@pytest.mark.usefixtures("clean_db")
def test_get_group_count():
    """Test that get_group_count returns the correct count."""
    # Create some groups
    factories.Group()
    factories.Group()
    factories.Group()

    # Mock the group_list action to return a fixed result
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_group_list = mock.MagicMock(return_value=['group1', 'group2', 'group3'])
        mock_get_action.return_value = mock_group_list

        # Call the helper function
        result = helpers.get_group_count()

        # Check that the result is the correct count
        assert result == 3

        # Check that group_list was called with the correct parameters
        mock_group_list.assert_called_once_with({}, {'all_fields': False})


@pytest.mark.usefixtures("clean_db")
def test_get_group_count_error():
    """Test that get_group_count handles errors correctly."""
    # Mock the group_list action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_group_list = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_group_list

        # Call the helper function
        result = helpers.get_group_count()

        # Check that the result is 0
        assert result == 0


def test_get_year():
    """Test that get_year returns the current year."""
    # Get the current year
    current_year = datetime.datetime.now().year

    # Call the helper function
    result = helpers.get_year()

    # Check that the result is the current year
    assert result == current_year


@pytest.mark.usefixtures("clean_db")
def test_get_latest_resources():
    """Test that get_latest_resources returns the correct resources."""
    # Create a dataset with resources
    dataset = factories.Dataset()
    # Create resources (not directly used in test but needed for database setup)
    factories.Resource(package_id=dataset['id'])
    factories.Resource(package_id=dataset['id'])

    # Mock the SQLAlchemy query
    with mock.patch('ckan.model.meta.Session.query') as mock_query:
        # Set up the mock query chain
        mock_filter = mock.MagicMock()
        mock_order_by = mock.MagicMock()
        mock_limit = mock.MagicMock()

        mock_query.return_value.filter.return_value = mock_filter
        mock_filter.join.return_value.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.limit.return_value = mock_limit
        mock_limit.all.return_value = [mock.MagicMock(), mock.MagicMock()]

        # Mock the package_show action
        with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            mock_package_show = mock.MagicMock(return_value=dataset)
            mock_get_action.return_value = mock_package_show

            # Call the helper function
            result = helpers.get_latest_resources(limit=2)

            # Check that the result is a list with 2 items
            assert len(result) == 2

            # Check that package_show was called for each resource
            assert mock_package_show.call_count == 2


@pytest.mark.usefixtures("clean_db")
def test_get_latest_resources_error():
    """Test that get_latest_resources handles errors correctly."""
    # Mock the SQLAlchemy query to raise an exception
    with mock.patch('ckan.model.meta.Session.query', side_effect=Exception('Test error')):
        # Call the helper function
        result = helpers.get_latest_resources()

        # Check that the result is an empty list
        assert result == []


@pytest.mark.usefixtures("clean_db")
def test_get_featured_groups():
    """Test that get_featured_groups returns the correct groups."""
    # Create some groups (not directly used in test but needed for database setup)
    factories.Group()
    factories.Group()

    # Mock the group_list action to return a fixed result
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_group_list = mock.MagicMock(return_value=[
            {'name': 'group1', 'display_name': 'Group 1', 'package_count': 3},
            {'name': 'group2', 'display_name': 'Group 2', 'package_count': 2},
            {'name': 'group3', 'display_name': 'Group 3', 'package_count': 1},
            {'name': 'group4', 'display_name': 'Group 4', 'package_count': 0},
            {'name': 'group5', 'display_name': 'Group 5', 'package_count': 5}
        ])
        mock_get_action.return_value = mock_group_list

        # Call the helper function with limit=2
        result = helpers.get_featured_groups(limit=2)

        # Check that the result is a list with 2 items
        assert len(result) == 2

        # Check that group_list was called with the correct parameters
        mock_group_list.assert_called_once_with({}, {
            'all_fields': True,
            'include_datasets': True
        })


@pytest.mark.usefixtures("clean_db")
def test_get_featured_groups_error():
    """Test that get_featured_groups handles errors correctly."""
    # Mock the group_list action to raise an exception
    with mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
        mock_group_list = mock.MagicMock(side_effect=Exception('Test error'))
        mock_get_action.return_value = mock_group_list

        # Call the helper function
        result = helpers.get_featured_groups()

        # Check that the result is an empty list
        assert result == []


def test_get_helpers():
    """Test that get_helpers returns a dictionary with all helper functions."""
    # Call the function
    helpers_dict = helpers.get_helpers()

    # Check that the dictionary contains all expected helpers
    assert "artesp_theme_hello" in helpers_dict
    assert "get_package_count" in helpers_dict
    assert "get_resource_count" in helpers_dict
    assert "get_latest_datasets" in helpers_dict
    assert "get_latest_resources" in helpers_dict
    assert "get_organization_count" in helpers_dict
    assert "get_group_count" in helpers_dict
    assert "get_featured_groups" in helpers_dict
    assert "get_year" in helpers_dict
    assert "safe_html" in helpers_dict
    assert "fix_fontawesome_icon" in helpers_dict
