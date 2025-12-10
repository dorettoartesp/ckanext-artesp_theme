import pytest
import time
from ckan.plugins import toolkit
from ckan.tests import factories
import ckan.lib.search as search

@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestResourceSearchSorting:
    
    def test_resource_search_default_sort_is_metadata_modified_desc(self, app):
        """
        Test that the default sort order is by metadata_modified (last update) descending.
        """
        user = factories.Sysadmin()
        org = factories.Organization(user=user)
        dataset = factories.Dataset(owner_org=org['id'], user=user)
        
        # Create first resource
        res1 = factories.Resource(
            package_id=dataset['id'],
            name="Older Resource",
            description="Created first",
            user=user
        )
        
        # Wait a bit to ensure timestamp difference
        time.sleep(1.5)
        
        # Create second resource
        res2 = factories.Resource(
            package_id=dataset['id'],
            name="Newer Resource",
            description="Created second",
            user=user
        )

        # Update the first resource so it becomes the "newest" in terms of modification
        time.sleep(1.5)
        toolkit.get_action('resource_patch')({'user': user['name']}, {
            'id': res1['id'],
            'description': "Updated Description"
        })
        
        # Re-index
        search.commit()
        
        # Default search (no params)
        url = toolkit.url_for("artesp_theme.resource_search")
        resp = app.get(url)
        
        assert resp.status_code == 200
        
        body = resp.body
        pos_res1 = body.find("Older Resource") # The name of res1 (Updated)
        pos_res2 = body.find("Newer Resource") # The name of res2
        
        assert pos_res1 != -1
        assert pos_res2 != -1
        
        # res1 (Updated) should be first (smaller index)
        assert pos_res1 < pos_res2, f"Expected Older Resource (updated) at {pos_res1} to be before Newer Resource at {pos_res2}"

    def test_resource_search_explicit_sort(self, app):
        """
        Test explicit sorting.
        """
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'])
        
        res1 = factories.Resource(package_id=dataset['id'], name="A Resource")
        time.sleep(1.5)
        res2 = factories.Resource(package_id=dataset['id'], name="B Resource")
        
        search.commit()
        
        # Sort by created asc (Oldest first) -> A then B
        url = toolkit.url_for("artesp_theme.resource_search", sort="created asc")
        resp = app.get(url)
        
        body = resp.body
        pos_res1 = body.find("A Resource")
        pos_res2 = body.find("B Resource")
        
        assert pos_res1 != -1
        assert pos_res2 != -1
        assert pos_res1 < pos_res2, f"Expected A ({pos_res1}) to be before B ({pos_res2}) in created asc sort"
        
        # Sort by created desc (Newest first) -> B then A
        url = toolkit.url_for("artesp_theme.resource_search", sort="created desc")
        resp = app.get(url)
        
        body = resp.body
        pos_res1 = body.find("A Resource")
        pos_res2 = body.find("B Resource")
        
        assert pos_res1 != -1
        assert pos_res2 != -1
        assert pos_res2 < pos_res1, f"Expected B ({pos_res2}) to be before A ({pos_res1}) in created desc sort"
