import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

import outils.verifier_mobile as verifier_mobile
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


def test_element_casse_sous_un_conteneur_defilant_reste_signale(tmp_path):
    # Contre-exemple du cas sain ci-dessus : un conteneur defilant existe
    # bien dans la page, mais DEUX niveaux plus bas, un badge en position
    # absolute sort de son propre parent immediat (non defilant, lui). Ce
    # parent n'a rien a voir avec le defilement de .scroller -- le badge
    # doit rester signale. Revue independante : l'ancienne version
    # excluait tout element vivant sous N'IMPORTE QUEL ancetre defilant, a
    # n'importe quelle profondeur, donc aurait laisse passer ce badge.
    corps = """
    <div class="scroller" style="overflow-x:auto;width:100%;">
      <div class="niveau-a" style="width:100%;">
        <div class="carte" style="position:relative;width:100px;height:40px;
        margin:20px;background:#eee;">
          <span class="badge" style="position:absolute;left:70px;top:0;
          width:50px;height:20px;background:red;color:#fff;">NEW</span>
        </div>
      </div>
    </div>
    """
    page = _ecrire(tmp_path, "page_badge_casse_sous_scroller.html", corps)

    defauts = verifier_page(page, largeurs=(320,))

    assert any("badge" in d and "cadre" in d for d in defauts), defauts


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


def test_le_seuil_de_hauteur_de_cible_tactile_est_reellement_utilise(tmp_path):
    # Piege releve en revue : _CIBLE_TACTILE_MIN_PX existait mais n'etait
    # jamais lue, le seuil reel etait recopie en dur dans le script JS. Ce
    # test prouve que changer le parametre Python change bien le resultat.
    corps = """
    <main>
      <button style="height:30px;padding:0;line-height:30px;
      font-size:12px;">OK</button>
    </main>
    """
    page = _ecrire(tmp_path, "page_bouton_30px.html", corps)

    defauts_defaut = verifier_page(page, largeurs=(320,))
    defauts_seuil_abaisse = verifier_page(
        page, largeurs=(320,), cible_tactile_min_px=20
    )

    assert any("44px" in d for d in defauts_defaut)
    assert defauts_seuil_abaisse == []


def test_le_seuil_de_largeur_max_de_cible_tactile_est_reellement_utilise(tmp_path):
    # Meme piege pour _LARGEUR_CIBLE_TACTILE_MAX : a 800px (>= 768, hors zone
    # par defaut) le bouton de 30px n'est pas signale ; l'etendre a 1024px
    # doit le faire rentrer dans la zone controlee et le signaler.
    corps = """
    <main>
      <button style="height:30px;padding:0;line-height:30px;
      font-size:12px;">OK</button>
    </main>
    """
    page = _ecrire(tmp_path, "page_bouton_30px_800.html", corps)

    defauts_defaut = verifier_page(page, largeurs=(800,))
    defauts_seuil_etendu = verifier_page(
        page, largeurs=(800,), largeur_cible_tactile_max=1024
    )

    assert defauts_defaut == []
    assert any("44px" in d for d in defauts_seuil_etendu)


def test_message_clair_si_playwright_est_absent(tmp_path, monkeypatch):
    # Un import casse doit produire un message qui dit quoi installer, pas
    # une trace d'import brute ; simule l'absence du paquet sans le
    # desinstaller.
    page = _ecrire(tmp_path, "page.html", "<p>ok</p>")
    monkeypatch.setattr(verifier_mobile, "sync_playwright", None)
    monkeypatch.setattr(verifier_mobile, "_navigateur", None)

    with pytest.raises(RuntimeError, match="playwright"):
        verifier_page(page)


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
