"""La variante autonome (site-autonome/), ouverte en file:// comme le fait son
destinataire : la seance du jour doit VERIFIER une planche et un muscle.

Defaut releve au pilotage : sur l'accueil autonome, la seance ne va pas chercher
chapitre-N.html (impossible en file://), elle clone des modeles caches
(#reservoir-seance). interface.js equipait ces modeles au chargement comme s'ils
etaient des exercices : le clone d'une planche recevait un bouton « Verifier »
sans ecouteur (importNode ne copie pas les ecouteurs) -- le bouton ne repondait
pas et rien n'etait verifie ni enregistre --, et celui d'une table de muscles un
second jeu de champs, dont le vide faisait echouer chaque ligne. Un bouton qui ne
repond pas est pire qu'un bouton absent : on croit avoir valide sa reponse.

On force une seance faite uniquement de pastilles et de muscles (cartes et quiz
deja « sus » aujourd'hui), on repond juste, et on exige des marqueurs de
verification, un verdict enregistre et une progression qui survit au
rechargement.
"""

import datetime
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.empaqueter import empaqueter  # noqa: E402
from outils.verifier_mobile import _obtenir_navigateur  # noqa: E402

pytestmark = pytest.mark.slow

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CLE = "uc1-anatomie-v1"


def _etat_sans_carte_ni_quiz_a_revoir():
    aujourdhui = datetime.date.today().isoformat()
    items = {}
    for chapitre in COURS["chapitres"]:
        for entree in chapitre["cartes"] + chapitre["quiz"]:
            items[entree["id"]] = {
                "id": entree["id"],
                "type": "carte",
                "chapitre": chapitre["num"],
                "statut": "su",
                "derniereVue": aujourdhui,
                "echecs": 0,
            }
    return {"dateExamen": None, "theme": "auto", "items": items}


@pytest.fixture(scope="module")
def accueil_autonome():
    empaqueter(RACINE)
    return (RACINE / "site-autonome" / "index.html").as_uri()


@pytest.fixture
def page(accueil_autonome):
    page = _obtenir_navigateur().new_page(viewport={"width": 1280, "height": 900})
    page.route("https://**", lambda route: route.abort())
    erreurs = []
    page.on("pageerror", lambda erreur: erreurs.append(str(erreur)))
    # Pose l'etat une seule fois : un rechargement ne doit pas l'ecraser.
    page.add_init_script(
        f"if (!localStorage.getItem('{CLE}')) "
        f"localStorage.setItem('{CLE}', {json.dumps(json.dumps(_etat_sans_carte_ni_quiz_a_revoir()))});"
    )
    page.goto(accueil_autonome, wait_until="load")
    page.erreurs = erreurs
    yield page
    page.close()


def _stockage(page):
    return json.loads(page.evaluate(f"localStorage.getItem('{CLE}')"))


def _remplir_avec_les_bonnes_reponses(zone):
    champs = zone.locator("input:visible")
    for i in range(champs.count()):
        champs.nth(i).fill(champs.nth(i).get_attribute("data-attendu") or "")


def _lancer_la_seance_jusqu_a(page, types):
    """Avance dans la seance jusqu'a avoir montre chaque type demande ; renvoie
    {type: (zone, controle)} au moment ou il est affiche."""
    page.click("#seance")
    page.wait_for_selector("#seance-zone:not([hidden])")
    trouves = {}
    for _ in range(60):
        for type_, selecteur in (
            ("planche", "#seance-planche"),
            ("muscle", "#seance-muscle"),
        ):
            if type_ in types and type_ not in trouves:
                if page.evaluate(f"!document.querySelector('{selecteur}').hidden"):
                    yield type_, page.locator(selecteur)
                    trouves[type_] = True
        if set(types) <= set(trouves):
            return
        page.click("#seance-suivant")
        page.wait_for_timeout(150)
    raise AssertionError(f"jamais vu en seance : {set(types) - set(trouves)}")


def test_une_planche_verifiee_en_seance_est_marquee_verifiee(page):
    for type_, zone in _lancer_la_seance_jusqu_a(page, ["planche"]):
        assert type_ == "planche"
        # Un seul jeu de champs et un seul bouton : le modele du reservoir n'a
        # pas ete equipe, seul le clone l'est.
        assert zone.locator(".legendes").count() == 1
        assert zone.locator("figure > button.action").count() == 1
        _remplir_avec_les_bonnes_reponses(zone)
        zone.locator("figure > button.action:visible").click()
        assert (
            page.evaluate(
                "document.querySelector('#seance-planche figure').dataset.verifie"
            )
            == "oui"
        )
        # ... et toutes les pastilles sont jugees justes.
        verdicts = zone.locator("input").evaluate_all(
            "els => els.map(e => e.dataset.verdict)"
        )
        assert verdicts and set(verdicts) == {"bon"}
    assert not page.erreurs


def test_un_muscle_verifie_en_seance_n_a_qu_un_champ_par_colonne(page):
    for type_, zone in _lancer_la_seance_jusqu_a(page, ["muscle"]):
        assert type_ == "muscle"
        # Origine, terminaison, action : trois champs, pas six (un second jeu
        # heritait du modele equipe au chargement et faisait echouer la ligne).
        assert zone.locator(".muscle__champ").count() == 3
        _remplir_avec_les_bonnes_reponses(zone)
        zone.locator("table + button.action").click()
        assert (
            page.evaluate(
                "document.querySelector('#seance-muscle tbody tr').dataset.verifie"
            )
            == "oui"
        )
        verdicts = zone.locator("input").evaluate_all(
            "els => els.map(e => e.dataset.verdict)"
        )
        assert verdicts and set(verdicts) == {"bon"}
    assert not page.erreurs


def test_les_verdicts_de_planche_et_de_muscle_sont_enregistres_et_survivent_au_rechargement(
    page,
):
    avant = {
        li: page.inner_text(f".progression li[data-chapitre='{li}'] .anneau__valeur")
        for li in range(1, 8)
    }
    for _type, zone in _lancer_la_seance_jusqu_a(page, ["planche", "muscle"]):
        _remplir_avec_les_bonnes_reponses(zone)
        zone.locator("button.action:visible").last.click()
    verdicts = {
        identifiant: item
        for identifiant, item in _stockage(page)["items"].items()
        if "#" in identifiant
    }
    pastilles = [i for i in verdicts if "#muscle#" not in i]
    muscles = [i for i in verdicts if "#muscle#" in i]
    assert pastilles and muscles, verdicts
    for item in verdicts.values():
        assert (
            item["statut"] == "su"
            and item["derniereVue"] == datetime.date.today().isoformat()
        )

    apres = {
        li: page.inner_text(f".progression li[data-chapitre='{li}'] .anneau__valeur")
        for li in range(1, 8)
    }
    assert apres != avant  # la progression a bouge

    page.reload(wait_until="load")
    page.wait_for_selector("#seance")
    assert {i for i in _stockage(page)["items"] if "#" in i} == set(verdicts)
    apres_rechargement = {
        li: page.inner_text(f".progression li[data-chapitre='{li}'] .anneau__valeur")
        for li in range(1, 8)
    }
    assert apres_rechargement == apres
    assert not page.erreurs


def test_s_exercer_marche_en_file_sur_une_page_de_chapitre(accueil_autonome):
    # Le site autonome n'a pas de serveur : la page d'un chapitre ne peut rien
    # recuperer. S'exercer clone ses modeles depuis le reservoir de la page.
    # Chapitre 6 : les quatre formats.
    chapitre = (RACINE / "site-autonome" / "chapitre-6.html").as_uri() + "#exercer"
    page = _obtenir_navigateur().new_page(viewport={"width": 1280, "height": 900})
    erreurs = []
    page.on("pageerror", lambda erreur: erreurs.append(str(erreur)))
    page.route("https://**", lambda route: route.abort())
    try:
        page.goto(chapitre, wait_until="load")
        page.wait_for_selector("#seance-zone .carte")
        # Un chapitre a la fois, sans reseau : cartes, questions, planches, muscles.
        vus = set()
        for _ in range(8):
            for type_, selecteur in (
                ("carte", "#seance-zone .carte"),
                ("quiz", "#seance-zone .question"),
                ("planche", "#seance-planche figure"),
                ("muscle", "#seance-muscle tbody tr"),
            ):
                if page.locator(selecteur).count():
                    vus.add(type_)
            page.click("#seance-suivant")
            page.wait_for_timeout(80)
        assert vus == {"carte", "quiz", "planche", "muscle"}, vus

        page.click("#seance-quitter")
        page.click("#seance")
        page.wait_for_selector("#seance-zone .carte")
        identifiant = page.evaluate("document.querySelector('#seance-zone .carte').id")
        assert identifiant.startswith("c6-")
        page.keyboard.press("Space")
        page.keyboard.press("3")
        assert _stockage(page)["items"][identifiant]["statut"] == "su"
        assert not erreurs
    finally:
        page.close()
