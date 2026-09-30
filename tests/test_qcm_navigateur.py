"""Chaque question se corrige toujours correctement apres le melange des choix, dans un
vrai navigateur.

Le melange (outils/construire.py) permute les boutons du DOM et recalcule `bonne` dans
cours.json ; interface.js compare l'index du bouton clique a `bonne`. Si les deux ne
parlent pas du meme ordre, une reponse juste est notee fausse -- et rien, cote Python,
ne le voit. Ce test le pilote comme une personne : il lit la bonne reponse dans la
SOURCE (contenu/cours.json, ordre non melange), clique le bouton qui porte ce texte,
et exige « bon » ; il clique aussi volontairement une mauvaise reponse et exige que
CE bouton soit « mauvais » et que la bonne soit designee.

Trois chemins, car chacun assemble DOM et donnees autrement :
  - la page d'un chapitre (S'exercer) : modeles du reservoir de la page + cours.json ;
  - la seance du jour de site/ : pages de chapitre recuperees par fetch + cours.json ;
  - la variante autonome, en file:// : reservoir de l'accueil + cours-data.js.
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
from outils.empaqueter import empaqueter  # noqa: E402
from outils.verifier_mobile import _obtenir_navigateur  # noqa: E402

pytestmark = pytest.mark.slow

SOURCE = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
QUESTIONS = {q["id"]: q for c in SOURCE["chapitres"] for q in c["quiz"]}
CLE = "uc1-anatomie-v1"

# Le type d'exercice affiche : seul le volet des questions nous interesse ici.
_QUESTION_AFFICHEE = """() => {
  const zone = document.getElementById('seance-zone');
  const volet = document.querySelector('.volet[data-volet=quiz]');
  if (!zone || zone.hidden || !volet || volet.hidden) return null;
  const q = volet.querySelector('.question');
  return q ? q.id : null;
}"""
_SEANCE_OUVERTE = "() => { const z = document.getElementById('seance-zone'); return !!z && !z.hidden; }"
_TEXTES_DES_BOUTONS = """() => Array.from(
  document.querySelectorAll('#seance-zone .question .choix')).map(b => b.textContent)"""


class _Silencieux(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def url():
    construire(RACINE)
    gestionnaire = functools.partial(_Silencieux, directory=str(RACINE / "site"))
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{serveur.server_address[1]}/"
    serveur.shutdown()


@pytest.fixture(scope="module")
def url_autonome():
    empaqueter(RACINE)
    return (RACINE / "site-autonome").as_uri() + "/"


def _etat_tout_su_sauf_les_questions():
    """Un stockage ou tout est deja su aujourd'hui, sauf les questions : la seance du
    jour ne propose alors que des questions."""
    aujourdhui = datetime.date.today().isoformat()
    items = {}

    def _su(identifiant, type_, chapitre):
        items[identifiant] = {
            "id": identifiant,
            "type": type_,
            "chapitre": chapitre,
            "statut": "su",
            "derniereVue": aujourdhui,
            "echecs": 0,
        }

    for chapitre in SOURCE["chapitres"]:
        for carte in chapitre["cartes"]:
            _su(carte["id"], "carte", chapitre["num"])
        for planche in chapitre["planches"]:
            for pastille in planche["pastilles"]:
                _su(f"{planche['id']}#{pastille['n']}", "pastille", chapitre["num"])
        for muscle in chapitre["muscles"]:
            _su(f"{chapitre['num']}#muscle#{muscle['nom']}", "muscle", chapitre["num"])
    return {"dateExamen": None, "theme": "auto", "items": items}


@pytest.fixture
def ouvrir():
    pages = []

    def _ouvrir(adresse, etat=None):
        page = _obtenir_navigateur().new_page(viewport={"width": 1280, "height": 900})
        pages.append(page)
        erreurs = []
        page.on("pageerror", lambda erreur: erreurs.append(str(erreur)))
        page.route("https://**", lambda route: route.abort())
        if etat is not None:
            page.add_init_script(
                f"if (!localStorage.getItem('{CLE}')) "
                f"localStorage.setItem('{CLE}', {json.dumps(json.dumps(etat))});"
            )
        page.goto(adresse, wait_until="load")
        page.erreurs = erreurs
        return page

    yield _ouvrir
    for page in pages:
        page.close()


def _stockage(page):
    brut = page.evaluate(f"localStorage.getItem('{CLE}')")
    return json.loads(brut) if brut else {"items": {}}


def _repondre(page, identifiant, juste):
    """Clique la bonne reponse (d'apres la SOURCE) ou une mauvaise, et controle le
    verdict affiche et le verdict enregistre. Renvoie le nombre de boutons."""
    question = QUESTIONS[identifiant]
    attendu = question["choix"][question["bonne"]]
    textes = page.evaluate(_TEXTES_DES_BOUTONS)
    # Les boutons portent les memes choix que la source, dans un autre ordre.
    assert sorted(textes) == sorted(question["choix"]), identifiant
    assert textes.count(attendu) == 1, identifiant
    cible = (
        textes.index(attendu)
        if juste
        else next(i for i, texte in enumerate(textes) if texte != attendu)
    )
    boutons = page.locator("#seance-zone .question .choix")
    boutons.nth(cible).click()

    verdicts = page.evaluate(
        """() => Array.from(document.querySelectorAll('#seance-zone .question .choix'))
             .map(b => [b.textContent, b.dataset.verdict || ''])"""
    )
    bons = [texte for texte, verdict in verdicts if verdict == "bon"]
    mauvais = [texte for texte, verdict in verdicts if verdict == "mauvais"]
    assert bons == [attendu], (identifiant, verdicts)
    if juste:
        assert mauvais == [], (identifiant, verdicts)
    else:
        assert mauvais == [textes[cible]], (identifiant, verdicts)
    # L'explication apparait, et le verdict est enregistre comme il faut.
    assert (
        page.evaluate(
            "getComputedStyle(document.querySelector('#seance-zone .question__expl')).display"
        )
        != "none"
    )
    assert _stockage(page)["items"][identifiant]["statut"] == (
        "su" if juste else "rate"
    )
    return len(textes)


def _parcourir_une_serie(page, alterner, maximum=200):
    """Fait defiler la serie en cours ; a chaque question, repond. Si `alterner`, la
    premiere fois on se trompe une question sur deux (elle revient en fin de serie : la
    seconde fois on repond juste). Renvoie {id: nombre de fois vue}."""
    vues = {}
    for _ in range(maximum):
        if not page.evaluate(_SEANCE_OUVERTE):
            break
        identifiant = page.evaluate(_QUESTION_AFFICHEE)
        if identifiant:
            vues[identifiant] = vues.get(identifiant, 0) + 1
            juste = not (alterner and vues[identifiant] == 1 and len(vues) % 2 == 0)
            _repondre(page, identifiant, juste)
        page.click("#seance-suivant")
        page.wait_for_timeout(60)
    return vues


def _parcourir_toutes_les_questions(page, attendues, alterner):
    """Enchaine les series (25 items chacune) jusqu'a avoir vu toutes les questions
    `attendues`, en n'ayant laisse que des questions a revoir (voir l'etat seme)."""
    vues = {}
    for _ in range(8):
        if not page.evaluate(_SEANCE_OUVERTE):
            page.click("#seance")  # « Commencer » / « Continuer » / « Demarrer »
            page.wait_for_selector("#seance-zone:not([hidden])", timeout=3000)
        for identifiant, fois in _parcourir_une_serie(page, alterner).items():
            vues[identifiant] = vues.get(identifiant, 0) + fois
        if set(attendues) <= set(vues):
            break
    return vues


@pytest.mark.parametrize("num", range(1, 8))
def test_chaque_question_d_un_chapitre_se_corrige_juste_apres_melange(ouvrir, url, num):
    page = ouvrir(f"{url}chapitre-{num}.html#exercer", etat=_etat_tout_su_sauf_les_questions())
    page.wait_for_selector("#seance-zone:not([hidden])")
    attendues = {q["id"] for q in SOURCE["chapitres"][num - 1]["quiz"]}
    vues = _parcourir_toutes_les_questions(page, attendues, alterner=True)
    assert set(vues) == attendues, attendues ^ set(vues)
    assert not page.erreurs


def test_la_seance_du_jour_corrige_juste_les_82_questions_apres_melange(ouvrir, url):
    # Accueil de site/ : la seance recupere chaque page de chapitre par fetch (DOM
    # melange) et lit `bonne` dans assets/cours.json (melange) -- deux sources a
    # recouper. L'etat ne laisse a revoir que les questions ; la seance en propose 25
    # a la fois, on enchaine les series jusqu'a les avoir toutes vues.
    page = ouvrir(url + "index.html", etat=_etat_tout_su_sauf_les_questions())
    vues = _parcourir_toutes_les_questions(page, QUESTIONS, alterner=False)
    assert set(vues) == set(QUESTIONS), set(QUESTIONS) - set(vues)
    assert not page.erreurs


def test_la_seance_du_jour_note_fausse_une_mauvaise_reponse_apres_melange(ouvrir, url):
    page = ouvrir(url + "index.html", etat=_etat_tout_su_sauf_les_questions())
    page.click("#seance")
    page.wait_for_selector("#seance-zone:not([hidden])")
    for _ in range(12):
        identifiant = page.evaluate(_QUESTION_AFFICHEE)
        if identifiant:
            _repondre(page, identifiant, juste=False)
        page.click("#seance-suivant")
        page.wait_for_timeout(60)
    assert not page.erreurs


@pytest.mark.parametrize("num", [3, 6, 7])
def test_variante_autonome_page_de_chapitre_corrige_juste_apres_melange(
    ouvrir, url_autonome, num
):
    page = ouvrir(
        f"{url_autonome}chapitre-{num}.html#exercer", etat=_etat_tout_su_sauf_les_questions()
    )
    page.wait_for_selector("#seance-zone:not([hidden])")
    attendues = {q["id"] for q in SOURCE["chapitres"][num - 1]["quiz"]}
    vues = _parcourir_toutes_les_questions(page, attendues, alterner=True)
    assert set(vues) == attendues, attendues ^ set(vues)
    assert not page.erreurs


def test_variante_autonome_seance_du_jour_corrige_juste_les_82_questions(
    ouvrir, url_autonome
):
    page = ouvrir(url_autonome + "index.html", etat=_etat_tout_su_sauf_les_questions())
    vues = _parcourir_toutes_les_questions(page, QUESTIONS, alterner=False)
    assert set(vues) == set(QUESTIONS), set(QUESTIONS) - set(vues)
    assert not page.erreurs
