import pytest
from bs4 import BeautifulSoup

from ckan.lib import base


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_description_exposes_full_plain_text_in_title(app):
    description = (
        '**Descricao completa** com "aspas" e conteudo adicional que excede '
        "o resumo visivel de oitenta caracteres para validar o tooltip."
    )
    resource = {
        "id": "resource-id",
        "name": "Recurso de teste",
        "description": description,
        "format": "CSV",
        "has_views": False,
        "url": "https://example.com/recurso.csv",
        "url_type": "upload",
    }
    package = {"name": "dataset-teste", "type": "dataset"}

    with app.flask_app.test_request_context("/dataset/dataset-teste"):
        rendered = base.render_snippet(
            "package/snippets/resource_item.html",
            res=resource,
            pkg=package,
            can_edit=False,
            url_is_edit=False,
        )

    expected_title = (
        'Descricao completa com "aspas" e conteudo adicional que excede '
        "o resumo visivel de oitenta caracteres para validar o tooltip."
    )

    parsed = BeautifulSoup(rendered, "html.parser")
    description_element = parsed.select_one("p.description")

    assert description_element["title"] == expected_title
    assert "**Descricao completa**" not in rendered
