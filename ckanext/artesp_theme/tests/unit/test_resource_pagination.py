import pytest

from ckanext.artesp_theme import resource_pagination


def _resources(count):
    return [
        {
            "id": "resource-{:02d}".format(index),
            "name": "Recurso {:02d}".format(index),
            "description": "Descricao do recurso {:02d}".format(index),
            "position": index,
        }
        for index in range(count)
    ]


def test_build_resource_page_paginates_resources_in_original_order():
    result = resource_pagination.build_resource_page(
        _resources(45), raw_page="2", query=""
    )

    assert result.page == 2
    assert result.page_count == 3
    assert result.total == 45
    assert result.filtered_total == 45
    assert [resource["id"] for resource in result.resources] == [
        "resource-{:02d}".format(index) for index in range(20, 40)
    ]


def test_build_resource_page_filters_name_and_description_without_case_or_accents():
    resources = [
        {
            "id": "portaria",
            "name": "PORTARIA 123",
            "description": "Regulacao rodoviaria",
        },
        {
            "id": "relatorio",
            "name": "Relatorio anual",
            "description": "Fiscalização de concessões",
        },
        {
            "id": "csv",
            "name": "Dados operacionais",
            "description": "Arquivo tabular",
            "format": "PORTARIA",
        },
    ]

    by_name = resource_pagination.build_resource_page(
        resources, raw_page="1", query="portária"
    )
    by_description = resource_pagination.build_resource_page(
        resources, raw_page="1", query="FISCALIZACAO"
    )

    assert [resource["id"] for resource in by_name.resources] == ["portaria"]
    assert [resource["id"] for resource in by_description.resources] == [
        "relatorio"
    ]


@pytest.mark.parametrize("raw_page", ["0", "-1", "abc", "4"])
def test_build_resource_page_rejects_invalid_or_missing_pages(raw_page):
    with pytest.raises(resource_pagination.ResourcePageNotFound):
        resource_pagination.build_resource_page(
            _resources(45), raw_page=raw_page, query=""
        )


def test_build_resource_page_allows_empty_search_on_first_page():
    result = resource_pagination.build_resource_page(
        _resources(5), raw_page="1", query="inexistente"
    )

    assert result.resources == []
    assert result.total == 5
    assert result.filtered_total == 0
    assert result.page_count == 1
