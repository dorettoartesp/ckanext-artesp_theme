from pathlib import Path


EXTENSION_ROOT = Path(__file__).resolve().parents[2]


def test_election_period_header_has_temporary_top_spacing():
    header = (EXTENSION_ROOT / "templates/header.html").read_text(encoding="utf-8")
    layout = (EXTENSION_ROOT / "assets/css/modules/layout.css").read_text(
        encoding="utf-8"
    )

    assert 'class="minimal-header election-period-header"' in header
    assert ".minimal-header.election-period-header {" in layout
    assert "padding-top: 1rem;" in layout
