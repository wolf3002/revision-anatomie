import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.verifier_mobile import LARGEURS, verifier_page

_RESET = "<style>*{margin:0;box-sizing:border-box}body{font-family:sans-serif}</style>"


def _ecrire(tmp_path: Path, nom: str, corps: str) -> Path:
    chemin = tmp_path / nom
    chemin.write_text(
        f"<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"{_RESET}</head><body>{corps}</body></html>",
        encoding="utf-8",
    )
    return chemin


def test_les_huit_largeurs_de_reference_sont_exposees():
    assert LARGEURS == (320, 360, 390, 414, 768, 1024, 1280, 1920)


def test_page_saine_ne_produit_aucun_defaut_a_aucune_largeur(tmp_path):
    corps = """
    <header><h1>Terminologie anatomique</h1></header>
    <main>
      <p>Corps humain, vivant, debout, les membres superieurs allonges le
      long du corps, la paume des mains tournee en avant, le regard droit
      et horizontal.</p>
      <button style="min-height:48px;padding:8px 16px;font-size:16px;">
        Retourner
      </button>
      <a href="#suite" style="display:inline-block;min-height:48px;
      line-height:48px;padding-inline:16px;">Suite</a>
    </main>
    """
    page = _ecrire(tmp_path, "page_saine.html", corps)

    assert verifier_page(page) == []


def test_bloc_trop_large_deborde_aux_petites_largeurs_pas_aux_grandes(tmp_path):
    corps = """
    <main>
      <div class="bloc-large" style="width:900px;height:60px;background:#ccc;">
        Bloc fixe de 900px de large, en dur.
      </div>
    </main>
    """
    page = _ecrire(tmp_path, "page_debordement.html", corps)

    defauts = verifier_page(page, largeurs=(320, 1920))
    defauts_320 = [d for d in defauts if "[320px]" in d]
    defauts_1920 = [d for d in defauts if "[1920px]" in d]

    assert defauts_320, "un bloc de 900px devrait deborder a 320px"
    assert not defauts_1920, "un bloc de 900px ne deborde pas a 1920px"


def test_tableau_dans_conteneur_defilant_ne_produit_aucun_defaut(tmp_path):
    corps = """
    <main>
      <div class="enveloppe" style="width:100%;max-width:300px;overflow-x:auto;">
        <table style="width:900px;border-collapse:collapse;">
          <tr><th>Muscle</th><th>Origine</th><th>Terminaison</th>
              <th>Action</th><th>Note</th></tr>
          <tr><td>Biceps</td><td>Scapula</td><td>Radius</td>
              <td>Flexion</td><td>-</td></tr>
        </table>
      </div>
    </main>
    """
    page = _ecrire(tmp_path, "page_tableau_scrollable.html", corps)

    assert verifier_page(page) == []


def test_bouton_trop_petit_est_signale_sous_768px_seulement(tmp_path):
    corps = """
    <main>
      <button style="height:20px;padding:0;line-height:20px;
      font-size:12px;">OK</button>
    </main>
    """
    page = _ecrire(tmp_path, "page_bouton_petit.html", corps)

    defauts = verifier_page(page, largeurs=(320, 768, 1024))
    defauts_320 = [d for d in defauts if "[320px]" in d]
    defauts_768 = [d for d in defauts if "[768px]" in d]
    defauts_1024 = [d for d in defauts if "[1024px]" in d]

    assert any("44px" in d for d in defauts_320)
    assert defauts_768 == []
    assert defauts_1024 == []


@pytest.mark.slow
def test_integration_toutes_largeurs_sur_plusieurs_pages(tmp_path):
    # Test lent (lance Chrome 8 x 2 pages) : a lancer explicitement avec
    # python3 -m pytest tests/test_verifier_mobile.py -m slow
    page_saine = _ecrire(tmp_path, "saine.html", "<p>Bonjour.</p>")
    page_large = _ecrire(
        tmp_path,
        "large.html",
        '<div style="width:2000px;height:10px;"></div>',
    )

    assert verifier_page(page_saine) == []
    assert verifier_page(page_large) != []


def test_page_introuvable_est_signalee(tmp_path):
    chemin = tmp_path / "absent.html"
    defauts = verifier_page(chemin)
    assert defauts != []
    assert "introuvable" in defauts[0]
