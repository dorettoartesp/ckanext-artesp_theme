from pathlib import Path

import pytest

from ckan.lib import base


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_upload_field_exposes_progress_metadata(app):
    with app.flask_app.test_request_context("/dataset/teste/resource/new"):
        html = base.render_snippet(
            "package/snippets/resource_form.html",
            data={},
            errors={},
            error_summary={},
            include_metadata=False,
            pkg_name="teste",
            stage=None,
            dataset_type="dataset",
        )

    assert 'data-artesp-resource-upload' in html
    assert 'data-resource-upload-max-size-mb="1024"' in html
    assert 'data-resource-upload-status' in html
    assert 'aria-live="polite"' in html
    assert 'data-resource-upload-file-name' in html
    assert 'data-resource-upload-file-size' in html
    assert 'data-resource-upload-overlay' in html
    assert 'data-resource-upload-overlay-message' in html
    assert 'role="alertdialog"' in html
    assert 'aria-modal="true"' in html
    assert "Nenhum arquivo selecionado" in html
    assert "Pronto para enviar" in html
    assert "Enviando arquivo. Aguarde." in html
    assert "Não feche esta janela até o envio terminar." in html
    assert "No file selected" not in html
    assert "Sending file. Please wait." not in html


def test_resource_upload_progress_assets_are_registered():
    webassets = (ASSETS_DIR / "webassets.yml").read_text(encoding="utf-8")

    assert "js/resource-upload-progress.js" in webassets
    assert "css/modules/resource-upload-progress.css" in webassets
    assert (ASSETS_DIR / "js/resource-upload-progress.js").exists()
    assert (ASSETS_DIR / "css/modules/resource-upload-progress.css").exists()


def test_resource_upload_progress_preserves_submit_action():
    script = (ASSETS_DIR / "js/resource-upload-progress.js").read_text(
        encoding="utf-8"
    )

    assert "preserveSubmitAction" in script
    assert 'input.type = "hidden"' in script
    assert 'input.name = "save"' in script
    assert 'button.name !== "save"' in script
