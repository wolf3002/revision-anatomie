"""Le parcours d'un chapitre, pilote dans un vrai navigateur.

Les tests de test_fiche_lecture.py verifient le HTML construit ; ceux-ci
verifient ce que l'utilisateur voit une fois interface.js execute -- la seule
facon de tenir l'invariant « aucune reponse avant tentative » sur les onglets
de test, et « rien de masque » sur la fiche. Le site est servi en http:// (les
modules ES ne s'executent pas en file://), comme outils/verifier_mobile.py le
fait pour ce qu'il mesure, avec le meme Chrome pilote par Playwright.
"""

import functools
import http.server
import sys
import threading
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import construire  # noqa: E402
from outils.verifier_mobile import _obtenir_navigateur  # noqa: E402

pytestmark = pytest.mark.slow


class _Silencieux(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def url():
    construire(RACINE)
    gestionnaire = functools.partial(_Silencieux, directory=str(RACINE / "site"))
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
    fil = threading.Thread(target=serveur.serve_forever, daemon=True)
    fil.start()
    yield f"http://127.0.0.1:{serveur.server_address[1]}/"
    serveur.shutdown()


@pytest.fixture
def ouvrir(url):
    pages = []

    def _ouvrir(nom, largeur=1280):
        page = _obtenir_navigateur().new_page(
            viewport={"width": largeur, "height": 900}
        )
        pages.append(page)
        page.route("https://**", lambda route: route.abort())
        page.goto(url + nom, wait_until="load")
        page.wait_for_selector(".onglet[aria-selected='true'], #seance")
        return page

    yield _ouvrir
    for page in pages:
        page.close()


def _volets_visibles(page):
    return page.eval_on_selector_all(
        ".volet", "els => els.filter(e => !e.hidden).map(e => e.dataset.volet)"
    )


def _onglet_actif(page):
    return page.evaluate(
        "document.querySelector('.onglet[aria-selected=true]').dataset.onglet"
    )


def test_un_chapitre_s_ouvre_sur_la_fiche_et_elle_seule(ouvrir):
    page = ouvrir("chapitre-6.html")
    assert _onglet_actif(page) == "fiche"
    assert _volets_visibles(page) == ["fiche"]


def test_la_fiche_montre_tout_et_n_a_ni_champ_ni_bouton_de_mode(ouvrir):
    page = ouvrir("chapitre-6.html")
    fiche = page.locator('.volet[data-volet="fiche"]')
    assert fiche.locator("input").count() == 0
    # Les libelles de planche sont visibles (fiche = planche legendee).
    invisibles = fiche.locator(".pastille__t").evaluate_all(
        "els => els.filter(e => getComputedStyle(e).visibility === 'hidden').length"
    )
    assert invisibles == 0 and fiche.locator(".pastille__t").count() > 0
    # Les boutons qui pilotent un onglet de test ne se montrent pas ici.
    assert page.locator("[data-visible-sur]:visible").count() == 0
    # La table musculaire est en lecture : valeurs visibles, rien a completer.
    assert fiche.locator("table.table-ref tbody td").count() > 0
    assert fiche.locator("table.table-ref .muscle__champ").count() == 0


def test_les_onglets_de_test_n_exposent_aucune_reponse_d_emblee(ouvrir):
    page = ouvrir("chapitre-6.html")

    page.click('.onglet[data-onglet="cartes"]')
    versos = page.eval_on_selector_all(
        ".volet[data-volet=cartes] .carte__r",
        "els => els.map(e => getComputedStyle(e).visibility)",
    )
    assert versos and set(versos) == {"hidden"}

    page.click('.onglet[data-onglet="quiz"]')
    expl = page.eval_on_selector_all(
        ".volet[data-volet=quiz] .question__expl",
        "els => els.map(e => getComputedStyle(e).display)",
    )
    assert expl and set(expl) == {"none"}
    assert page.locator(".volet[data-volet=quiz] [data-verdict]").count() == 0

    # L'onglet Planche s'ouvre MUET : la version legendee est dans la fiche.
    page.click('.onglet[data-onglet="planche"]')
    modes = page.eval_on_selector_all(
        ".volet[data-volet=planche] .planche", "els => els.map(e => e.dataset.mode)"
    )
    assert modes and set(modes) == {"muet"}
    libelles = page.eval_on_selector_all(
        ".volet[data-volet=planche] .pastille__t",
        "els => els.filter(e => getComputedStyle(e).visibility !== 'hidden').length",
    )
    assert libelles == 0
    assert (
        page.locator(".volet[data-volet=planche] .legendes input:visible").count() > 0
    )

    page.click('.onglet[data-onglet="muscles"]')
    assert (
        page.evaluate("document.querySelector('table.muscles').dataset.mode")
        == "champs"
    )
    valeurs = page.eval_on_selector_all(
        ".volet[data-volet=muscles] .muscle__valeur",
        "els => els.filter(e => getComputedStyle(e).display !== 'none').length",
    )
    assert valeurs == 0


def test_les_boutons_de_mode_ne_se_montrent_que_sur_leur_onglet(ouvrir):
    page = ouvrir("chapitre-6.html")

    def visibles():
        return sorted(
            page.eval_on_selector_all(
                "[data-visible-sur]:not([hidden])",
                "els => els.map(e => e.dataset.action)",
            )
        )

    assert visibles() == []
    page.click('.onglet[data-onglet="planche"]')
    assert visibles() == ["mode-planches"]
    page.click('.onglet[data-onglet="muscles"]')
    assert visibles() == ["mode-muscles"]
    page.click('.onglet[data-onglet="cartes"]')
    assert visibles() == []


def test_le_mode_muet_reste_basculable_et_M_n_agit_que_sur_l_onglet_planche(ouvrir):
    page = ouvrir("chapitre-2.html")
    mode = "document.querySelector('.volet[data-volet=planche] .planche').dataset.mode"

    page.click('.onglet[data-onglet="cartes"]')
    page.keyboard.press("m")
    assert page.evaluate(mode) == "muet"  # ailleurs que sur Planche : sans effet

    page.click('.onglet[data-onglet="planche"]')
    page.keyboard.press("m")
    assert page.evaluate(mode) == "legende"
    page.click("[data-action=mode-planches]")
    assert page.evaluate(mode) == "muet"


def test_la_seance_du_jour_tire_toujours_des_items_masques(ouvrir):
    page = ouvrir("index.html")
    page.click("#seance")
    page.wait_for_selector("#seance-zone:not([hidden])")
    # Premier item d'une seance neuve : une carte, verso masque jusqu'au geste.
    page.wait_for_selector("#seance-zone .carte")
    verso = (
        "getComputedStyle(document.querySelector('#seance-zone .carte__r')).visibility"
    )
    assert page.evaluate(verso) == "hidden"
    page.keyboard.press("Space")
    assert page.evaluate(verso) == "visible"


def test_aucun_defaut_de_mise_en_page_sur_chaque_onglet_avec_javascript(ouvrir):
    # outils/verifier_mobile.py tourne en file:// : les modules ES n'y sont pas
    # executes, il ne voit donc que la page SANS script -- fiche, cartes et quiz
    # (les volets de simple relecture y sont retires, style.css §5.2a). Ce test
    # reprend ses controles, page par page, onglet par onglet, sur la page telle
    # qu'elle s'affiche AVEC le script : planche muette et ses champs, table de
    # muscles a completer, boutons de mode. Trois largeurs : telephone, juste
    # au-dessus du seuil de 720 px (rail lateral), grand ecran.
    from outils.verifier_mobile import _SCRIPT_ANALYSE

    config = {"cibleMin": 44, "largeurMax": 768}
    defauts = []
    for num in range(1, 8):
        for largeur in (320, 768, 1280):
            page = ouvrir(f"chapitre-{num}.html", largeur)
            for onglet in page.eval_on_selector_all(
                ".onglet", "els => els.map(e => e.dataset.onglet)"
            ):
                page.click(f'.onglet[data-onglet="{onglet}"]')
                if onglet == "fiche":
                    page.evaluate("document.querySelector('.plan').open = true")
                for defaut in page.evaluate(_SCRIPT_ANALYSE, config):
                    defauts.append(
                        f"ch.{num} [{largeur}px] {onglet} : {defaut['selecteur']} "
                        f"{defaut['detail']}"
                    )
    assert defauts == []


def test_sans_javascript_chaque_volet_est_nomme_et_rien_n_est_lu_deux_fois(url):
    # Script absent : tous les volets se suivent, la barre d'onglets est inerte.
    # La fiche, les cartes et le quiz restent, chacun sous son titre ; Pieges,
    # Planche et Muscles, qui ne font que repeter la fiche, sont retires --
    # sinon la table de 17 muscles du chapitre 7 se lirait deux fois.
    contexte = _obtenir_navigateur().new_context(
        java_script_enabled=False, viewport={"width": 1280, "height": 900}
    )
    try:
        page = contexte.new_page()
        page.route("https://**", lambda route: route.abort())
        page.goto(url + "chapitre-7.html", wait_until="load")
        visibles = {
            cle: page.locator(f'.volet[data-volet="{cle}"]').is_visible()
            for cle in ("fiche", "pieges", "planche", "cartes", "quiz", "muscles")
        }
        assert visibles == {
            "fiche": True,
            "pieges": False,
            "planche": False,
            "cartes": True,
            "quiz": True,
            "muscles": False,
        }
        titres = page.locator(".volet__titre:visible").all_inner_texts()
        assert [t.lower() for t in titres] == [
            "apprendre · fiche",
            "se tester · cartes",
            "se tester · quiz",
        ]
        tables = [
            t for t in page.locator("table").all() if t.is_visible()
        ]
        assert len(tables) == 1  # la table de lecture de la fiche, une seule fois
    finally:
        contexte.close()


def test_avec_javascript_les_titres_de_volet_disparaissent(ouvrir):
    page = ouvrir("chapitre-7.html")
    assert page.evaluate("document.documentElement.classList.contains('js')")
    assert page.locator(".volet__titre:visible").count() == 0
    # Les trois volets retires sans script redeviennent des onglets a part entiere.
    for cle in ("pieges", "planche", "muscles"):
        page.click(f'.onglet[data-onglet="{cle}"]')
        assert _volets_visibles(page) == [cle]
