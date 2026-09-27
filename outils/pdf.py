"""Fiches HTML imprimables (outils/fiches.py) -> PDF, via Chrome headless.

Pas de dependance Python a un moteur PDF : on delegue la mise en page a
Chrome lui-meme (celui qui affichera le HTML), en mode --headless, exactement
la commande decrite dans la spec (docs/superpowers/specs/2026-09-18-site-
revision-anatomie-design.md, section 8).
"""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from outils.fiches import construire_fiches  # noqa: E402

_CANDIDATS_CHROME = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)


def _chemin_chrome():
    for nom in _CANDIDATS_CHROME:
        chemin = shutil.which(nom)
        if chemin:
            return chemin
    raise RuntimeError(
        "Aucun executable Chrome/Chromium trouve (essaye : "
        + ", ".join(_CANDIDATS_CHROME)
        + ") ; impossible de convertir les fiches en PDF."
    )


def generer_pdfs(racine: Path) -> list[Path]:
    racine = Path(racine)
    chrome = _chemin_chrome()
    fichiers_html = construire_fiches(racine)

    ecrits = []
    for html_ in fichiers_html:
        pdf = html_.with_suffix(".pdf")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                # Force Chrome a achever tous les etages de composition avant
                # de dessiner : observe en pratique, une pagination lancee
                # trop tot pouvait ponctuellement "oublier" de repeter le
                # <thead> d'un tableau coupe entre deux pages (constate sur
                # la table musculaire du chapitre 7, non reproductible a
                # chaque essai) -- ce drapeau elimine cette course.
                "--run-all-compositor-stages-before-draw",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}",
                str(html_),
            ],
            check=True,
            capture_output=True,
        )
        ecrits.append(pdf)
    return ecrits


if __name__ == "__main__":
    for chemin in generer_pdfs(Path(__file__).resolve().parents[1]):
        print(chemin)
