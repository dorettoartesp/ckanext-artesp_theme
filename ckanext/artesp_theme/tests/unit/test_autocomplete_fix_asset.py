from pathlib import Path


EXTENSION_ROOT = Path(__file__).resolve().parents[2]


def test_autocomplete_fix_asset_is_loaded_after_ckan_core_modules():
    page_template = EXTENSION_ROOT / "templates/page.html"
    base_template = EXTENSION_ROOT / "templates/base.html"
    assets = EXTENSION_ROOT / "assets/webassets.yml"

    page = page_template.read_text(encoding="utf-8")
    base = base_template.read_text(encoding="utf-8")
    webassets = assets.read_text(encoding="utf-8")

    assert "{% asset 'base/ckan' %}" in page
    assert "{% asset 'artesp_theme/artesp-autocomplete-fix-js' %}" in base
    assert "artesp-autocomplete-fix-js:" in webassets
    assert "js/autocomplete-fix.js" in webassets


def test_autocomplete_fix_patches_core_module_to_use_ckan_jquery():
    script_path = EXTENSION_ROOT / "assets/js/autocomplete-fix.js"
    script = script_path.read_text(encoding="utf-8")

    assert "ckan.module.registry.autocomplete" in script
    assert "patchMethod" in script
    assert "Function.prototype.toString.call(original)" in script
    assert ".replace(/\\$\\.fn/g, 'jQuery.fn')" in script
    assert ".replace(/\\$\\(/g, 'jQuery(')" in script
    assert "new Function('jQuery'" in script
    assert "setupAutoComplete" in script
    assert "lookup" in script
    assert "formatResult" in script
    assert "templateResult" in script
