import json
import uuid

import pytest
from bs4 import BeautifulSoup
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.integration
@pytest.mark.usefixtures("with_plugins")
def test_dataset_resource_pagination_search_and_seo(app):
    suffix = uuid.uuid4().hex[:8]
    dataset = factories.Dataset(
        name="dataset-resource-page-{}".format(suffix),
        owner_org=_artesp_org()["id"],
    )
    for index in range(21):
        factories.Resource(
            package_id=dataset["id"],
            name="Arquivo {:02d}".format(index),
            description=(
                "Fiscalização especial" if index == 20 else "Descricao comum"
            ),
            format="CSV",
        )

    page_two = app.get(
        "/dataset/{}?resource_page=2".format(dataset["name"])
    )
    page_two_html = BeautifulSoup(page_two.body, "html.parser")

    assert page_two.status_code == 200
    assert "Arquivo 20" in page_two.body
    assert "Arquivo 19" not in page_two_html.select_one("ul.resource-list").text
    assert page_two_html.select_one('link[rel="canonical"]')["href"].endswith(
        "?resource_page=2"
    )
    dataset_jsonld = json.loads(
        page_two_html.select_one('script[type="application/ld+json"]').string
    )
    assert len(dataset_jsonld["distribution"]) == 21

    search_response = app.get(
        "/dataset/{}?resource_q=fiscalizacao".format(dataset["name"])
    )
    search_html = BeautifulSoup(search_response.body, "html.parser")

    assert search_response.status_code == 200
    assert "Arquivo 20" in search_response.body
    assert "Arquivo 00" not in search_html.select_one("ul.resource-list").text
    assert search_html.select_one('meta[name="robots"]')["content"] == (
        "noindex,follow"
    )
    assert search_html.select_one('link[rel="canonical"]')["href"].endswith(
        "/dataset/{}".format(dataset["name"])
    )

    invalid_page = app.get(
        "/dataset/{}?resource_page=3".format(dataset["name"]),
        expect_errors=True,
    )
    assert invalid_page.status_code == 404

    api_response = app.get(
        "/api/3/action/package_show?id={}".format(dataset["name"])
    )
    assert len(api_response.json["result"]["resources"]) == 21
