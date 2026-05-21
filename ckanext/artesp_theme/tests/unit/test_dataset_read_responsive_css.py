from pathlib import Path


EXTENSION_ROOT = Path(__file__).resolve().parents[2]


def test_dataset_read_template_marks_wrapper_for_mobile_sidebar_rule():
    template = (
        EXTENSION_ROOT
        / "templates/package/read.html"
    ).read_text(encoding="utf-8")

    assert "block wrapper_class" in template
    assert "dataset-read-wrapper" in template


def test_dataset_read_mobile_sidebar_is_hidden_below_bootstrap_md():
    css = (
        EXTENSION_ROOT
        / "assets/css/modules/responsive.css"
    ).read_text(encoding="utf-8")

    assert "@media (max-width: 767.98px)" in css
    assert ".wrapper.dataset-read-wrapper > aside.secondary" in css
    assert "display: none" in css
