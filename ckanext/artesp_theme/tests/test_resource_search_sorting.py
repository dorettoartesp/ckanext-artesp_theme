import pytest
from ckan.plugins import toolkit

from ckanext.artesp_theme import controllers


def _patch_resource_actions(monkeypatch, resources):
    def fake_get_action(name):
        if name == "resource_search":
            return lambda context, data_dict: {
                "results": [dict(resource) for resource in resources]
            }
        if name == "package_show":
            return lambda context, data_dict: {
                "id": data_dict["id"],
                "title": "Dataset {}".format(data_dict["id"]),
                "name": data_dict["id"],
                "groups": [],
            }
        raise AssertionError(name)

    monkeypatch.setattr(controllers.toolkit, "get_action", fake_get_action)

@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
class TestResourceSearchSorting:
    
    def test_resource_search_default_sort_is_metadata_modified_desc(self, app, monkeypatch):
        """
        Test that the default sort order is by metadata_modified (last update) descending.
        """
        _patch_resource_actions(
            monkeypatch,
            [
                {
                    "id": "res-older",
                    "package_id": "pkg-1",
                    "name": "Older Resource",
                    "metadata_modified": "2025-01-03T00:00:00",
                },
                {
                    "id": "res-newer",
                    "package_id": "pkg-1",
                    "name": "Newer Resource",
                    "metadata_modified": "2025-01-02T00:00:00",
                },
            ],
        )
        
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

    def test_resource_search_explicit_sort(self, app, monkeypatch):
        """
        Test explicit sorting.
        """
        _patch_resource_actions(
            monkeypatch,
            [
                {
                    "id": "res-a",
                    "package_id": "pkg-1",
                    "name": "A Resource",
                    "created": "2025-01-01T00:00:00",
                },
                {
                    "id": "res-b",
                    "package_id": "pkg-1",
                    "name": "B Resource",
                    "created": "2025-01-02T00:00:00",
                },
            ],
        )
        
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
