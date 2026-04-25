import pytest
from ckan.plugins import toolkit
from ckanext.artesp_theme import controllers


def _patch_resource_actions(monkeypatch, resources, package_title_prefix="Dataset"):
    def fake_get_action(name):
        if name == "resource_search":
            return lambda context, data_dict: {
                "results": [dict(resource) for resource in resources]
            }
        if name == "package_show":
            return lambda context, data_dict: {
                "id": data_dict["id"],
                "title": f"{package_title_prefix} {data_dict['id']}",
                "name": data_dict["id"],
                "groups": [],
            }
        raise AssertionError(name)

    monkeypatch.setattr(controllers.toolkit, "get_action", fake_get_action)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.app
@pytest.mark.usefixtures("with_plugins")
class TestResourceSearch:

    def test_resource_search_endpoint_exists(self, app, monkeypatch):
        _patch_resource_actions(monkeypatch, [])
        url = toolkit.url_for("artesp_theme.resource_search")
        resp = app.get(url)
        assert resp.status_code == 200

    def test_resource_search_finds_resource(self, app, monkeypatch):
        resource_name = "Relatório de Disponibilidade 1"
        resource_description = "Arquivo contendo dados de disponibilidade 1."
        _patch_resource_actions(
            monkeypatch,
            [
                {
                    "id": "res-1",
                    "package_id": "pkg-1",
                    "name": resource_name,
                    "description": resource_description,
                    "metadata_modified": "2026-04-25T00:00:00",
                }
            ],
        )

        url = toolkit.url_for("artesp_theme.resource_search", q="disponibilidade")
        resp = app.get(url)

        assert resp.status_code == 200
        assert resource_name in resp.body
        assert resource_description[:-1] in resp.body

    def test_resource_search_partial_match(self, app, monkeypatch):
        resource_name = "Faturamento Anual 1"
        _patch_resource_actions(
            monkeypatch,
            [
                {
                    "id": "res-1",
                    "package_id": "pkg-1",
                    "name": resource_name,
                    "format": "CSV",
                    "metadata_modified": "2026-04-25T00:00:00",
                }
            ],
        )

        url = toolkit.url_for("artesp_theme.resource_search", q="Fatura")
        resp = app.get(url)

        assert resp.status_code == 200
        assert resource_name in resp.body

    def test_resource_search_no_results(self, app, monkeypatch):
        _patch_resource_actions(monkeypatch, [])
        url = toolkit.url_for(
            "artesp_theme.resource_search",
            q="UnicornioInexistente",
        )
        resp = app.get(url)

        assert resp.status_code == 200
        assert "No resources found" in resp.body
