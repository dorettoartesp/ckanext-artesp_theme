from pathlib import Path


def test_dashboard_statistics_css_uses_artesp_style_baseline_tokens():
    css_path = (
        Path(__file__).resolve().parents[2]
        / "assets/css/modules/dashboard-statistics.css"
    )
    css = css_path.read_text(encoding="utf-8").lower()

    assert "--artesp-red: #ff161f" in css
    assert "--artesp-blue: #034ea2" in css
    assert "--artesp-text: #333333" in css
    assert "--artesp-muted: #888888" in css
    assert "--artesp-border: #bfbfbf" in css
    assert "font-family: rawline" in css
    assert "border-left: 4px solid var(--artesp-red)" in css
    assert "border-radius: 25px" in css
