import pytest
from ckan.plugins import toolkit
from ckan.tests import factories
import ckan.lib.search as search

@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestResourceSearch:
    
    def test_resource_search_endpoint_exists(self, app):
        """
        Test that the /resource_search route exists and returns 200 OK.
        """
        url = toolkit.url_for("artesp_theme.resource_search")
        resp = app.get(url)
        assert resp.status_code == 200

    def test_resource_search_finds_resource(self, app):
        """
        Test that searching for a known resource returns it in the results.
        This verifies the Solr query construction in the controller.
        """
        # Create an organization first
        org = factories.Organization()

        # Create a dataset with a resource named "Disponibilidade"
        dataset = factories.Dataset(owner_org=org['id'])
        resource = factories.Resource(
            package_id=dataset['id'],
            name="Relatório de Disponibilidade 2025",
            description="Arquivo contendo dados de disponibilidade."
        )

        # Force Solr commit to make sure data is searchable
        search.commit()

        # Search for "disponibilidade"
        url = toolkit.url_for("artesp_theme.resource_search", q="disponibilidade")
        resp = app.get(url)

        assert resp.status_code == 200

        # Check if the resource name appears in the response HTML
        assert "Relatório de Disponibilidade 2025" in resp.body
        # Check if the description appears
        assert "Arquivo contendo dados de disponibilidade" in resp.body

    def test_resource_search_partial_match(self, app):
        """
        Test searching by a partial term.
        """
        # Create an organization first
        org = factories.Organization()

        dataset = factories.Dataset(owner_org=org['id'])
        resource = factories.Resource(
            package_id=dataset['id'],
            name="Faturamento Anual",
            format="CSV"
        )

        search.commit()

        # Search for "Fatura"
        url = toolkit.url_for("artesp_theme.resource_search", q="Fatura")
        resp = app.get(url)

        assert resp.status_code == 200
        assert "Faturamento Anual" in resp.body

    def test_resource_search_no_results(self, app):
        """
        Test search with a term that doesn't exist.
        """
        url = toolkit.url_for("artesp_theme.resource_search", q="UnicornioInexistente")
        resp = app.get(url)
        
        assert resp.status_code == 200
        assert "No resources found" in resp.body