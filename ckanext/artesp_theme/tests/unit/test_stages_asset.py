from pathlib import Path


EXTENSION_ROOT = Path(__file__).resolve().parents[2]


def test_stages_asset_overrides_ckan_green_pseudo_elements():
    css = (
        EXTENSION_ROOT / "assets/css/modules/stages.css"
    ).read_text(encoding="utf-8")

    assert ".stages li.active:after" in css
    assert ".stages li.complete:after" in css
    assert ".stages li.active:before" in css
    assert ".stages li.complete:before" in css
    assert ".stages li.active .highlight" in css
    assert ".stages li.complete .highlight" in css
    assert "--tw-blue-100" in css
    assert "--secondary" in css
    assert "#8cc68a" not in css
    assert "#c5e2c4" not in css
