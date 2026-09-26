import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
CSS = RACINE / "site" / "assets" / "style.css"

CLAIR = {
    "papier": "#EDEFF2",
    "carte": "#FFFFFF",
    "encre": "#101A22",
    "encre-doux": "#4A5A66",
    "trait": "#C9D2D9",
    "frontal": "#C1553A",
    "sagittal": "#1F6F78",
    "transversal": "#B0821F",
}
SOMBRE = {
    "papier": "#0E1418",
    "carte": "#161F25",
    "encre": "#E6EDF2",
    "encre-doux": "#97A7B2",
    "trait": "#2A3841",
    "frontal": "#E07A5F",
    "sagittal": "#3FA3AD",
    "transversal": "#DCA83A",
}


def _canal(valeur):
    valeur /= 255
    return valeur / 12.92 if valeur <= 0.04045 else ((valeur + 0.055) / 1.055) ** 2.4


def luminance(hexa):
    r, v, b = (int(hexa[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _canal(r) + 0.7152 * _canal(v) + 0.0722 * _canal(b)


def contraste(premier, second):
    a, b = sorted((luminance(premier), luminance(second)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def test_le_texte_atteint_le_niveau_AA():
    for palette in (CLAIR, SOMBRE):
        for fond in ("papier", "carte"):
            assert contraste(palette["encre"], palette[fond]) >= 4.5
            assert contraste(palette["encre-doux"], palette[fond]) >= 4.5


def test_les_trois_plans_restent_lisibles_sur_les_deux_fonds():
    for palette in (CLAIR, SOMBRE):
        for plan in ("frontal", "sagittal", "transversal"):
            for fond in ("papier", "carte"):
                assert contraste(palette[plan], palette[fond]) >= 3.0, (plan, fond)


def test_la_feuille_de_style_declare_toutes_les_variables():
    css = CSS.read_text(encoding="utf-8")
    for nom, valeur in CLAIR.items():
        assert f"--{nom}: {valeur}" in css, nom
    for valeur in SOMBRE.values():
        assert valeur in css


def test_le_mouvement_est_desactivable():
    css = CSS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css


def test_les_cibles_tactiles_sont_declarees():
    css = CSS.read_text(encoding="utf-8")
    assert re.search(r"min-height:\s*44px", css)
