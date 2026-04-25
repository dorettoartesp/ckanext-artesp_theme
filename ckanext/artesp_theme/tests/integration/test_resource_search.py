import uuid

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories
import ckan.lib.search as search

from ckanext.artesp_theme.logic import auth_helpers


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.integration
@pytest.mark.usefixtures("with_plugins")
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
        org = _artesp_org()
        unique_suffix = uuid.uuid4().hex[:8]
        resource_name = "Relatório de Disponibilidade {}".format(unique_suffix)
        resource_description = "Arquivo contendo dados de disponibilidade {}.".format(
            unique_suffix
        )

        # Create a dataset with a resource named "Disponibilidade"
        dataset = factories.Dataset(owner_org=org['id'])
        factories.Resource(
            package_id=dataset['id'],
            name=resource_name,
            description=resource_description,
        )

        # Force Solr commit to make sure data is searchable
        search.commit()

        # Search for "disponibilidade"
        url = toolkit.url_for("artesp_theme.resource_search", q="disponibilidade")
        resp = app.get(url)

        assert resp.status_code == 200

        # Check if the resource name appears in the response HTML
        assert resource_name in resp.body
        # Check if the description appears
        assert resource_description[:-1] in resp.body

    def test_resource_search_partial_match(self, app):
        """
        Test searching by a partial term.
        """
        org = _artesp_org()
        unique_suffix = uuid.uuid4().hex[:8]
        resource_name = "Faturamento Anual {}".format(unique_suffix)

        dataset = factories.Dataset(owner_org=org['id'])
        factories.Resource(
            package_id=dataset['id'],
            name=resource_name,
            format="CSV"
        )

        search.commit()

        # Search for "Fatura"
        url = toolkit.url_for("artesp_theme.resource_search", q="Fatura")
        resp = app.get(url)

        assert resp.status_code == 200
        assert resource_name in resp.body

    def test_resource_search_no_results(self, app):
        """
        Test search with a term that doesn't exist.
        """
        url = toolkit.url_for(
            "artesp_theme.resource_search",
            q="UnicornioInexistente{}".format(uuid.uuid4().hex),
        )
        resp = app.get(url)
        
        assert resp.status_code == 200
        assert "No resources found" in resp.body
