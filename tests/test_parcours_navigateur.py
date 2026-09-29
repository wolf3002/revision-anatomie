"""Le parcours d'un chapitre, pilote dans un vrai navigateur.

Les tests de test_fiche_lecture.py verifient le HTML construit ; ceux-ci
verifient ce que l'utilisateur voit une fois interface.js execute -- la seule
facon de tenir l'invariant « aucune reponse avant tentative » dans les
exercices, et « rien de masque » sur la fiche. Le site est servi en http:// (les
modules ES ne s'executent pas en file://), comme outils/verifier_mobile.py le
fait pour ce qu'il mesure, avec le meme Chrome pilote par Playwright.

Deux onglets : Fiche (lire) et S'exercer (un parcours unique, un exercice a la
fois, monte avec la machinerie de la seance du jour restreinte au chapitre).
"""

import datetime
import functools
import http.server
import json
import sys
import threading
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import construire  # noqa: E402
from outils.verifier_mobile import _SCRIPT_ANALYSE, _obtenir_navigateur  # noqa: E402

pytestmark = pytest.mark.slow

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRES = {c["num"]: c for c in COURS["chapitres"]}
CLE = "uc1-anatomie-v1"

# Ce que l'exercice affiche en ce moment, d'apres la zone de seance.
_TYPE_AFFICHE = """() => {
  const zone = document.getElementById('seance-zone');
  if (!zone || zone.hidden) return null;
  if (!document.querySelector('.volet[data-volet=cartes]').hidden) return 'carte';
  if (!document.querySelector('.volet[data-volet=quiz]').hidden) return 'quiz';
  if (!document.getElementById('seance-planche').hidden) return 'planche';
  if (!document.getElementById('seance-muscle').hidden) return 'muscle';
  return null;
}"""


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

    def _ouvrir(nom, largeur=1280, hauteur=900):
        page = _obtenir_navigateur().new_page(
            viewport={"width": largeur, "height": hauteur}
        )
        pages.append(page)
        erreurs = []
        page.on("pageerror", lambda erreur: erreurs.append(str(erreur)))
        page.route("https://**", lambda route: route.abort())
        page.goto(url + nom, wait_until="load")
        page.wait_for_selector("html.js")
        page.erreurs = erreurs
        return page

    yield _ouvrir
    for page in pages:
        page.close()


def _panneaux_visibles(page):
    return page.eval_on_selector_all(
        ".panneau", "els => els.filter(e => !e.hidden).map(e => e.dataset.panneau)"
    )


def _onglet_actif(page):
    return page.evaluate(
        "document.querySelector('.onglet[aria-selected=true]').dataset.onglet"
    )


def _stockage(page):
    brut = page.evaluate(f"localStorage.getItem('{CLE}')")
    return json.loads(brut) if brut else {"items": {}}


def _suivant(page):
    page.click("#seance-suivant")
    page.wait_for_timeout(80)


def _parcourir(page, maximum=40):
    """Fait defiler la serie ; renvoie {type: 1er element affiche} au moment ou
    il l'est. S'arrete quand chaque type a ete vu, ou a `maximum` pas."""
    vus = {}
    for _ in range(maximum):
        type_ = page.evaluate(_TYPE_AFFICHE)
        if type_ is None:
            break
        vus.setdefault(type_, True)
        yield type_
        _suivant(page)


def _aller_a_un_exercice(page, cible):
    """Avance jusqu'au premier exercice du type demande et le laisse affiche."""
    for _ in range(40):
        type_ = page.evaluate(_TYPE_AFFICHE)
        assert type_ is not None, f"la serie s'est terminee sans {cible}"
        if type_ == cible:
            return
        _suivant(page)
    raise AssertionError(f"jamais vu : {cible}")


# --- Deux onglets, la fiche d'abord ---------------------------------------------


def test_un_chapitre_s_ouvre_sur_la_fiche_et_elle_seule(ouvrir):
    page = ouvrir("chapitre-6.html")
    assert _onglet_actif(page) == "fiche"
    assert _panneaux_visibles(page) == ["fiche"]
    assert page.locator("#seance-zone").is_hidden()
    # Deux onglets, pas six.
    assert page.locator(".onglet").all_text_contents() == ["Fiche", "S'exercer"]
    assert page.locator("#actions-carte").is_hidden()


def test_la_fiche_montre_tout_et_n_a_ni_champ_ni_bouton_de_mode(ouvrir):
    page = ouvrir("chapitre-6.html")
    fiche = page.locator(".fiche")
    assert fiche.locator("input").count() == 0
    assert fiche.locator("button").count() == 0
    # Les libelles de planche sont visibles (fiche = planche legendee).
    invisibles = fiche.locator(".pastille__t").evaluate_all(
        "els => els.filter(e => getComputedStyle(e).visibility === 'hidden').length"
    )
    assert invisibles == 0 and fiche.locator(".pastille__t").count() > 0
    # Les pieges y sont lus, avec leur notion (l'onglet Pieges n'existe plus).
    assert fiche.locator("article.piege").count() == len(CHAPITRES[6]["pieges"])
    # La table musculaire est en lecture : valeurs visibles, rien a completer.
    assert fiche.locator("table.table-ref tbody td").count() > 0
    assert fiche.locator("table.table-ref .muscle__champ").count() == 0
    # Aucun bouton de mode, aucun reglage sur la page qu'on lit.
    assert page.locator("[data-visible-sur]").count() == 0
    assert page.locator("[data-action=reglages-bascule]").count() == 0


def test_la_fiche_mene_aux_exercices_en_un_clic(ouvrir):
    page = ouvrir("chapitre-3.html")
    page.click(".fiche-suite a")
    assert _onglet_actif(page) == "exercer"
    assert _panneaux_visibles(page) == ["exercer"]
    page.wait_for_selector("#seance-zone:not([hidden])")


def test_le_lien_de_fin_de_fiche_montre_le_debut_du_premier_exercice(ouvrir):
    # Fiche lue jusqu'en bas : le premier exercice doit commencer a l'ecran, pas
    # quelque part au milieu de la page (ni au-dessus de la fenetre).
    page = ouvrir("chapitre-6.html", 320, 640)
    page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'})")
    page.click(".fiche-suite a")
    page.wait_for_selector("#seance-zone:not([hidden])")
    page.wait_for_timeout(900)  # defilement doux
    haut = page.evaluate("document.getElementById('seance-compte').getBoundingClientRect().top")
    assert 0 <= haut < 640, haut


def test_les_fleches_changent_d_onglet_quand_un_onglet_a_le_focus(ouvrir):
    page = ouvrir("chapitre-3.html")
    page.focus('.onglet[data-onglet="fiche"]')
    page.keyboard.press("ArrowRight")
    assert _onglet_actif(page) == "exercer"
    page.keyboard.press("ArrowLeft")
    assert _onglet_actif(page) == "fiche"
    # Ailleurs, les fleches ne changent rien : elles servent a lire.
    page.evaluate("document.activeElement.blur()")
    page.keyboard.press("ArrowRight")
    assert _onglet_actif(page) == "fiche"


def test_le_lien_d_accueil_ramene_a_l_accueil(ouvrir):
    page = ouvrir("chapitre-3.html")
    page.click("a.retour")
    page.wait_for_selector("#seance")
    assert page.url.endswith("index.html")


def test_espace_fait_defiler_la_fiche(ouvrir):
    # L'ancien raccourci detournait Espace sur tous les onglets : sur le texte
    # qu'on lit, il ne faisait plus defiler la page.
    page = ouvrir("chapitre-6.html")
    assert page.evaluate("window.scrollY") == 0
    page.keyboard.press("Space")
    page.wait_for_timeout(600)
    assert page.evaluate("window.scrollY") > 0


# --- S'exercer : un parcours unique, un exercice a la fois --------------------------


def test_s_exercer_enchaine_des_exercices_de_types_varies_sans_second_clic(ouvrir):
    page = ouvrir("chapitre-6.html")
    page.click('.onglet[data-onglet="exercer"]')
    page.wait_for_selector("#seance-zone:not([hidden])")
    assert _onglet_actif(page) == "exercer" and _panneaux_visibles(page) == ["exercer"]
    # Le compteur dit ou on en est ; le depart s'efface pendant la serie.
    assert page.inner_text("#seance-compte").startswith("1 / ")
    assert page.locator("[data-seance-debut]").is_hidden()
    types = list(_parcourir(page, maximum=8))
    # Cartes, questions, planches muettes et muscles melanges : un chapitre a
    # quatre formats les montre tous les quatre dans les premiers exercices.
    assert {"carte", "quiz", "planche", "muscle"} <= set(types), types
    # Jamais deux exercices de meme format d'affilee tant qu'un autre attend.
    assert all(a != b for a, b in zip(types, types[1:])), types
    assert not page.erreurs


def test_un_chapitre_sans_muscle_n_en_montre_pas(ouvrir):
    page = ouvrir("chapitre-1.html#exercer")
    page.wait_for_selector("#seance-zone:not([hidden])")
    types = set(_parcourir(page, maximum=12))
    assert types == {"carte", "quiz", "planche"}


def test_s_exercer_ne_tire_que_des_items_du_chapitre(ouvrir):
    page = ouvrir("chapitre-5.html#exercer")
    page.wait_for_selector("#seance-zone:not([hidden])")
    chapitre = CHAPITRES[5]
    ids = {c["id"] for c in chapitre["cartes"]} | {q["id"] for q in chapitre["quiz"]}
    ids |= {p["id"] for p in chapitre["planches"]}
    affiches = []
    for _ in range(40):
        type_ = page.evaluate(_TYPE_AFFICHE)
        if type_ is None:
            break
        affiches.append(
            page.evaluate(
                """() => {
                  const z = document.getElementById('seance-zone');
                  const el = z.querySelector('.carte, .question, .planche, .muscles tbody tr');
                  return el.id || el.dataset.id;
                }"""
            )
        )
        _suivant(page)
    assert affiches
    for identifiant in affiches:
        assert identifiant in ids or identifiant.startswith("5#muscle#"), identifiant
    assert not page.erreurs


def test_aucune_reponse_avant_tentative_dans_s_exercer(ouvrir):
    page = ouvrir("chapitre-6.html#exercer")
    page.wait_for_selector("#seance-zone:not([hidden])")

    # Carte : le verso est masque tant qu'on n'a pas retourne.
    _aller_a_un_exercice(page, "carte")
    verso = "getComputedStyle(document.querySelector('#seance-zone .carte__r')).visibility"
    assert page.evaluate(verso) == "hidden"
    page.keyboard.press("Space")
    assert page.evaluate(verso) == "visible"

    # Quiz : ni explication ni verdict avant d'avoir repondu.
    _aller_a_un_exercice(page, "quiz")
    assert page.evaluate(
        "getComputedStyle(document.querySelector('#seance-zone .question__expl')).display"
    ) == "none"
    assert page.locator("#seance-zone [data-verdict]").count() == 0
    page.locator("#seance-zone .choix").first.click()
    assert page.evaluate(
        "getComputedStyle(document.querySelector('#seance-zone .question__expl')).display"
    ) != "none"
    assert page.locator("#seance-zone .choix[data-verdict=bon]").count() == 1

    # Planche : muette (libelles invisibles), champs a remplir ; la correction
    # (libelles, « attendu ») n'arrive qu'apres Verifier.
    _aller_a_un_exercice(page, "planche")
    assert page.evaluate("document.querySelector('#seance-planche figure').dataset.mode") == "muet"
    libelles = page.eval_on_selector_all(
        "#seance-planche .pastille__t",
        "els => els.filter(e => getComputedStyle(e).visibility !== 'hidden').length",
    )
    assert libelles == 0
    assert page.locator("#seance-planche .legendes input:visible").count() > 0
    assert page.locator("#seance-planche .legendes__etat").count() == 0
    champs = page.locator("#seance-planche .legendes input")
    for i in range(champs.count()):
        champs.nth(i).fill("zzz")
    page.click("#seance-planche figure > button.action")
    assert page.evaluate("document.querySelector('#seance-planche figure').dataset.mode") == "legende"
    etats = page.locator("#seance-planche .legendes__etat").all_inner_texts()
    assert etats and all(e.startswith("faux — attendu : ") for e in etats)
    # Verifie une fois : les champs se figent, on ne recopie pas la correction.
    assert page.locator("#seance-planche .legendes input[readonly]").count() == champs.count()
    assert page.locator("#seance-planche figure > button.action:visible").count() == 0

    # Muscle : valeurs masquees, un champ par colonne ; correction apres seulement.
    _aller_a_un_exercice(page, "muscle")
    valeurs = page.eval_on_selector_all(
        "#seance-muscle .muscle__valeur",
        "els => els.filter(e => getComputedStyle(e).display !== 'none').length",
    )
    assert valeurs == 0
    assert page.locator("#seance-muscle .muscle__champ input:visible").count() == 3
    assert page.locator("#seance-muscle .muscle__etat:not(:empty)").count() == 0
    page.click("#seance-muscle table + button")
    etats = page.locator("#seance-muscle .muscle__etat").all_inner_texts()
    assert len(etats) == 3 and all(e.startswith("faux — attendu : ") for e in etats)
    assert not page.erreurs


def test_les_pointes_de_fleche_d_une_planche_d_exercice_se_resolvent_dans_le_clone(ouvrir):
    # Le trace porte <marker id="fleche">, reference par url(#fleche) : le
    # navigateur prend le PREMIER id du document. Celui du modele du reservoir
    # (sous-arbre masque) ne se rend pas -- les pointes disparaitraient. Le clone
    # affiche doit donc passer avant lui.
    page = ouvrir("chapitre-1.html#exercer")
    page.wait_for_selector("#seance-zone:not([hidden])")
    _aller_a_un_exercice(page, "planche")
    hors_clone = page.evaluate(
        """() => {
          const refs = [...document.querySelectorAll('#seance-planche svg [marker-end], '
            + '#seance-planche svg [marker-start]')];
          const ids = new Set(refs.flatMap((e) => [e.getAttribute('marker-end'),
            e.getAttribute('marker-start')]).filter(Boolean)
            .map((v) => v.replace(/^url\\(#|\\)$/g, '').replace(/\\)$/, '')));
          return { nb: ids.size,
                   dehors: [...ids].filter((id) =>
                     !document.getElementById(id)?.closest('#seance-planche')) };
        }"""
    )
    assert hors_clone["nb"] > 0, "la planche du chapitre 1 doit porter une fleche"
    assert hors_clone["dehors"] == []


def test_un_verdict_est_memorise_et_survit_au_rechargement(ouvrir):
    page = ouvrir("chapitre-2.html#exercer")
    page.wait_for_selector("#seance-zone .carte")
    identifiant = page.evaluate("document.querySelector('#seance-zone .carte').id")
    assert identifiant == "c2-01"
    page.keyboard.press("Space")
    page.keyboard.press("3")
    item = _stockage(page)["items"][identifiant]
    assert item["statut"] == "su"
    assert item["derniereVue"] == datetime.date.today().isoformat()
    assert item["chapitre"] == 2 and item["type"] == "carte"

    # Recharger : la progression est la, et l'onglet ouvert aussi (#exercer).
    page.reload(wait_until="load")
    page.wait_for_selector("#seance-zone .carte")
    assert _stockage(page)["items"][identifiant]["statut"] == "su"
    assert _onglet_actif(page) == "exercer"
    # Une carte sue aujourd'hui n'est plus due : la serie repart sur une autre.
    assert page.evaluate("document.querySelector('#seance-zone .carte').id") != identifiant


def test_la_fin_d_une_serie_dit_ce_qui_a_ete_fait_et_propose_de_continuer(ouvrir):
    page = ouvrir("chapitre-2.html#exercer")
    page.wait_for_selector("#seance-zone .carte")
    page.keyboard.press("Space")
    page.keyboard.press("2")
    page.click("#seance-quitter")
    assert page.locator("#seance-zone").is_hidden()
    assert "1 item(s) révisé(s)" in page.inner_text("#seance-message")
    bouton = page.locator("#seance")
    assert bouton.is_visible() and bouton.text_content().strip() == "Continuer"
    bouton.click()
    page.wait_for_selector("#seance-zone:not([hidden])")


def test_les_raccourcis_ne_jugent_pas_une_carte_qu_on_ne_voit_pas(ouvrir):
    page = ouvrir("chapitre-2.html#exercer")
    page.wait_for_selector("#seance-zone .carte")
    page.keyboard.press("Space")
    assert page.locator("#actions-carte").is_visible()
    # Retour sur la fiche : la barre des verdicts disparait, et « 1 » n'y juge rien.
    page.click('.onglet[data-onglet="fiche"]')
    assert page.locator("#actions-carte").is_hidden()
    page.keyboard.press("1")
    assert _stockage(page)["items"] == {}
    # Retour sur S'exercer : la serie reprend la ou elle etait (meme carte).
    page.click('.onglet[data-onglet="exercer"]')
    assert page.evaluate("document.querySelector('#seance-zone .carte').id") == "c2-01"
    assert page.locator("#actions-carte").is_visible()


# --- La seance du jour n'a pas bouge --------------------------------------------------


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


def test_la_seance_du_jour_melange_les_chapitres(ouvrir):
    page = ouvrir("index.html")
    page.click("#seance")
    page.wait_for_selector("#seance-zone .carte")
    chapitres = set()
    for _ in range(12):
        if page.evaluate(_TYPE_AFFICHE) is None:
            break
        # Cartes et questions portent leur chapitre dans leur identifiant (c3-04).
        identifiant = page.evaluate(
            """() => {
              const el = document.querySelector('#seance-zone .carte, #seance-zone .question');
              return el ? el.id : null;
            }"""
        )
        if identifiant:
            chapitres.add(int(identifiant[1]))
        _suivant(page)
    assert len(chapitres) > 1, chapitres


def test_un_verdict_de_seance_du_jour_fait_avancer_l_indication_du_chapitre(ouvrir):
    page = ouvrir("index.html")
    valeur = ".progression li[data-chapitre='1'] .anneau__valeur"
    assert page.inner_text(valeur) == "pas commencé"
    page.click("#seance")
    page.wait_for_selector("#seance-zone .carte")
    identifiant = page.evaluate("document.querySelector('#seance-zone .carte').id")
    page.keyboard.press("Space")
    page.keyboard.press("3")
    chapitre = identifiant[1]
    assert "% su" in page.inner_text(
        f".progression li[data-chapitre='{chapitre}'] .anneau__valeur"
    )
    assert (
        page.get_attribute(f".progression li[data-chapitre='{chapitre}']", "data-etat")
        == "touche"
    )


# --- L'accueil se comprend sans explication -------------------------------------------


def test_l_accueil_propose_deux_actions_par_chapitre(ouvrir):
    page = ouvrir("index.html")
    assert page.locator("li.chapitre").count() == 7
    assert page.locator("li.chapitre a:has-text('Lire la fiche')").count() == 7
    assert page.locator("li.chapitre a:has-text('S\\'exercer')").count() == 7
    # Une phrase, le bouton de seance, les chapitres : rien d'autre a l'ecran
    # que la date d'examen, tant qu'elle n'est pas renseignee.
    assert page.locator("#invite-date-examen").is_visible()
    assert page.locator("#reglages-panneau").is_hidden()
    assert page.locator("[data-action=reglages-bascule]").count() == 1


def test_lire_la_fiche_ouvre_la_fiche_et_s_exercer_les_exercices(ouvrir):
    page = ouvrir("index.html")
    page.click("li.chapitre[data-chapitre='4'] a:has-text('Lire la fiche')")
    page.wait_for_selector("html.js")
    assert page.url.endswith("chapitre-4.html")
    assert _onglet_actif(page) == "fiche" and page.locator("#seance-zone").is_hidden()
    page.go_back()
    page.click("li.chapitre[data-chapitre='4'] a:has-text('S\\'exercer')")
    page.wait_for_selector("#seance-zone:not([hidden])")
    assert page.url.endswith("chapitre-4.html#exercer")
    assert _onglet_actif(page) == "exercer"


def test_les_reglages_s_ouvrent_derriere_un_lien_et_la_date_d_examen_s_efface_de_l_accueil(ouvrir):
    page = ouvrir("index.html")
    lien = page.locator("[data-action=reglages-bascule]")
    assert lien.is_visible()
    lien.click()
    panneau = page.locator("#reglages-panneau")
    assert panneau.is_visible()
    texte = " ".join(panneau.text_content().split())
    for attendu in ("Thème", "Date d'examen", "Exporter la progression", "Importer une progression", "Réinitialiser"):
        assert attendu in texte, attendu
    # La date renseignee (ici depuis l'invite), l'invite disparait et les
    # reglages la montrent.
    lien.click()
    page.fill("#invite-date-examen-saisie", "2027-01-15")
    assert page.locator("#invite-date-examen").is_hidden()
    assert _stockage(page)["dateExamen"] == "2027-01-15"
    page.reload(wait_until="load")
    page.wait_for_selector("html.js")
    assert page.locator("#invite-date-examen").is_hidden()


def test_le_theme_choisi_s_applique_aussi_aux_pages_de_chapitre(ouvrir):
    page = ouvrir("index.html")
    page.click("[data-action=reglages-bascule]")
    page.click("[data-theme-choix=sombre]")
    page.click("li.chapitre[data-chapitre='1'] a:has-text('Lire la fiche')")
    page.wait_for_selector("html.js")
    assert page.evaluate("document.documentElement.dataset.theme") == "sombre"


# --- Mise en page : aucun debordement, de 320 a 1920 px --------------------------------


def test_aucun_defaut_de_mise_en_page_sur_la_fiche_et_chaque_exercice(ouvrir):
    # outils/verifier_mobile.py tourne en file:// : les modules ES n'y sont pas
    # executes, il ne voit donc que la page SANS script (la fiche). Ce test reprend
    # ses controles sur la page telle qu'elle s'affiche AVEC le script : la fiche,
    # puis chaque format d'exercice avant ET apres tentative (planche legendee et
    # ses corrections, table de muscles et ses « attendu », quiz corrige). Quatre
    # largeurs : telephone, juste au-dessus du seuil de 720 px, ordinateur, grand
    # ecran.
    config = {"cibleMin": 44, "largeurMax": 768}
    defauts = []

    def controler(page, contexte):
        for defaut in page.evaluate(_SCRIPT_ANALYSE, config):
            defauts.append(f"{contexte} : {defaut['selecteur']} {defaut['detail']}")

    for num in range(1, 8):
        for largeur in (320, 768, 1280, 1920):
            page = ouvrir(f"chapitre-{num}.html", largeur)
            page.evaluate("document.querySelector('.plan').open = true")
            controler(page, f"ch.{num} [{largeur}px] fiche")

            page.click('.onglet[data-onglet="exercer"]')
            page.wait_for_selector("#seance-zone:not([hidden])")
            deja = set()
            for _ in range(30):
                type_ = page.evaluate(_TYPE_AFFICHE)
                if type_ is None or len(deja) == 4:
                    break
                if type_ not in deja:
                    deja.add(type_)
                    controler(page, f"ch.{num} [{largeur}px] {type_}")
                    # Apres tentative : la correction s'affiche, elle aussi doit tenir.
                    if type_ == "carte":
                        page.keyboard.press("Space")
                    elif type_ == "quiz":
                        page.locator("#seance-zone .choix").first.click()
                    elif type_ == "planche":
                        for champ in page.locator("#seance-planche .legendes input").all():
                            champ.fill("zzz")
                        page.click("#seance-planche figure > button.action")
                    elif type_ == "muscle":
                        page.click("#seance-muscle table + button")
                    controler(page, f"ch.{num} [{largeur}px] {type_} corrige")
                _suivant(page)
    assert defauts == []


def test_aucun_defaut_de_mise_en_page_sur_l_accueil_avec_javascript(ouvrir):
    config = {"cibleMin": 44, "largeurMax": 768}
    defauts = []
    for largeur in (320, 360, 414, 768, 1024, 1280, 1920):
        page = ouvrir("index.html", largeur)
        page.click("[data-action=reglages-bascule]")
        for defaut in page.evaluate(_SCRIPT_ANALYSE, config):
            defauts.append(f"[{largeur}px] {defaut['selecteur']} {defaut['detail']}")
        page.click("#seance")
        page.wait_for_selector("#seance-zone .carte")
        for defaut in page.evaluate(_SCRIPT_ANALYSE, config):
            defauts.append(f"[{largeur}px] seance {defaut['selecteur']} {defaut['detail']}")
    assert defauts == []


# --- Sans JavaScript : la fiche se lit telle quelle ----------------------------------------


def test_sans_javascript_la_fiche_se_lit_et_la_page_dit_que_les_exercices_en_ont_besoin(url):
    # Script absent : la fiche est entiere, sans rien de masque. Les exercices
    # (et la barre d'onglets, le lien de fin de fiche) ne sont pas proposes : une
    # ligne dit pourquoi. La table de 17 muscles du chapitre 7 se lit une fois.
    contexte = _obtenir_navigateur().new_context(
        java_script_enabled=False, viewport={"width": 1280, "height": 900}
    )
    try:
        page = contexte.new_page()
        page.route("https://**", lambda route: route.abort())
        page.goto(url + "chapitre-7.html", wait_until="load")
        assert page.locator(".fiche").is_visible()
        assert page.locator(".fiche-section").count() == len(CHAPITRES[7]["sections"]) + 1
        assert page.locator(".fiche article.piege").count() == len(CHAPITRES[7]["pieges"])
        assert page.locator(".fiche .planche-fiche").count() == len(CHAPITRES[7]["planches"])
        assert page.locator(".onglets").is_hidden()
        assert page.locator(".fiche-suite").is_hidden()
        assert page.locator('.panneau[data-panneau="exercer"]').is_hidden()
        assert page.locator(".sans-js").is_visible()
        # Ni carte, ni question, ni champ visibles : seule la fiche est lue.
        assert page.locator(".carte:visible, .question:visible, input:visible").count() == 0
        tables = [t for t in page.locator("table").all() if t.is_visible()]
        assert len(tables) == 1  # la table de lecture de la fiche, une seule fois
    finally:
        contexte.close()


def test_sans_javascript_l_accueil_mene_aux_fiches_et_ne_propose_pas_ce_qui_ne_marche_pas(url):
    contexte = _obtenir_navigateur().new_context(
        java_script_enabled=False, viewport={"width": 1280, "height": 900}
    )
    try:
        page = contexte.new_page()
        page.route("https://**", lambda route: route.abort())
        page.goto(url + "index.html", wait_until="load")
        assert page.locator("li.chapitre a:has-text('Lire la fiche'):visible").count() == 7
        assert page.locator("li.chapitre a:has-text('S\\'exercer'):visible").count() == 0
        assert page.locator("#seance").is_hidden()
    finally:
        contexte.close()


def test_avec_javascript_la_note_sans_script_disparait(ouvrir):
    page = ouvrir("chapitre-7.html")
    assert page.evaluate("document.documentElement.classList.contains('js')")
    assert page.locator(".sans-js").is_hidden()
    assert page.locator(".onglets").is_visible()
