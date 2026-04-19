import gettext
from pathlib import Path


LOCALE_DIR = (
    Path(__file__).resolve().parents[1] / "i18n"
)


def test_follow_button_translations_for_pt_br():
    translations = gettext.translation(
        "ckanext-artesp_theme",
        localedir=str(LOCALE_DIR),
        languages=["pt_BR"],
    )

    assert translations.gettext("Follow") == "Seguir"
    assert translations.gettext("Unfollow") == "Desseguir"
