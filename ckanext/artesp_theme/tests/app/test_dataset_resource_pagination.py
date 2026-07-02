import pytest
from markupsafe import Markup

from ckan.lib import base
from ckanext.artesp_theme import helpers
from ckanext.artesp_theme.plugin import ArtespThemePlugin


def _package(resource_count=45):
    return {
        "id": "dataset-id",
        "name": "dataset-teste",
        "type": "dataset",
        "num_resources": resource_count,
        "resources": [
            {
                "id": "resource-{:02d}".format(index),
                "name": "Recurso {:02d}".format(index),
                "description": "Descricao {:02d}".format(index),
                "format": "CSV",
                "has_views": False,
                "url": "https://example.com/resource-{:02d}.csv".format(index),
                "url_type": "upload",
            }
            for index in range(resource_count)
        ],
    }


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_before_dataset_view_filters_and_paginates_dataset_resources(app):
    package = _package()

    with app.flask_app.test_request_context(
        "/dataset/dataset-teste?resource_q=recurso&resource_page=2"
    ):
        result = ArtespThemePlugin().before_dataset_view(package)
        pagination = helpers.get_dataset_resource_pagination()

        assert [resource["id"] for resource in result["resources"]] == [
            "resource-{:02d}".format(index) for index in range(20, 40)
        ]
        assert result["num_resources"] == 45
        assert pagination.page == 2
        assert pagination.item_count == 45
        pager_html = pagination.pager()
        assert "resource_q=recurso" in pager_html
        assert "resource_page=3" in pager_html
        assert helpers.get_dataset_resource_query() == "recurso"
        assert len(helpers.get_full_dataset_resources(result)) == 45


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_before_dataset_view_does_not_paginate_other_routes(app):
    package = _package()

    with app.flask_app.test_request_context(
        "/api/3/action/package_show?id=dataset-teste"
    ):
        result = ArtespThemePlugin().before_dataset_view(package)

    assert len(result["resources"]) == 45


class _Pagination:
    def pager(self):
        return Markup('<nav class="pagination-test">Paginas</nav>')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_list_renders_server_side_search_and_pagination(app):
    package = _package(resource_count=1)

    with app.flask_app.test_request_context("/dataset/dataset-teste"):
        html = base.render_snippet(
            "package/snippets/resources_list.html",
            pkg=package,
            resources=package["resources"],
            can_edit=True,
            resource_query="recurso",
            resource_filtered_total=1,
            resource_pagination=_Pagination(),
        )

    assert 'method="get"' in html
    assert 'name="resource_q"' in html
    assert 'value="recurso"' in html
    assert "Search" in html
    assert "Clear" in html
    assert 'href="/dataset/dataset-teste"' in html
    assert "1 resource found" in html
    assert 'class="pagination-test"' in html
    assert "Data and Resources" not in html
    assert html.count("dataset-resource-action") == 2
    assert 'class="heading resource-card-link"' in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_list_renders_filtered_empty_state(app):
    package = _package(resource_count=0)

    with app.flask_app.test_request_context("/dataset/dataset-teste"):
        html = base.render_snippet(
            "package/snippets/resources_list.html",
            pkg=package,
            resources=[],
            can_edit=True,
            resource_query="inexistente",
            resource_filtered_total=0,
            resource_pagination=_Pagination(),
        )

    assert 'No resources found for "inexistente"' in html
    assert "why not add some?" not in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_search_clear_button_is_translated_to_portuguese(app):
    package = _package(resource_count=1)

    with app.flask_app.test_request_context(
        "/dataset/dataset-teste",
        environ_overrides={"CKAN_LANG": "pt_BR"},
    ):
        html = base.render_snippet(
            "package/snippets/resources_list.html",
            pkg=package,
            resources=package["resources"],
            can_edit=True,
            resource_query="recurso",
            resource_filtered_total=1,
            resource_pagination=_Pagination(),
        )

    assert "Limpar" in html
    assert ">Clear<" not in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_search_placeholder_is_translated_to_portuguese(app):
    package = _package(resource_count=1)

    with app.flask_app.test_request_context(
        "/dataset/dataset-teste",
        environ_overrides={"CKAN_LANG": "pt_BR"},
    ):
        html = base.render_snippet(
            "package/snippets/resources_list.html",
            pkg=package,
            resources=package["resources"],
            can_edit=True,
            resource_query="",
            resource_filtered_total=1,
            resource_pagination=_Pagination(),
        )

    assert (
        'placeholder="Utilize este campo para buscar recursos neste conjunto de dados..."'
        in html
    )
    assert 'data-placeholder-mobile="Buscar recurso..."' in html
