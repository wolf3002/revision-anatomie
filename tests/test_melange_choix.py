"""Le melange des choix des QCM (outils/construire.py, section « Le melange »).

Le risque de ce melange n'est pas qu'il rate : c'est qu'il « marche » en cassant la
correction. Le site tient l'ordre des choix a deux endroits -- les boutons du DOM
(data-index) et `bonne` dans cours.json -- et la fiche PDF a un troisieme (le corrige,
qui marque la bonne reponse). Si l'un est melange sans l'autre, une reponse juste est
notee fausse. Les tests ci-dessous verifient donc CHAQUE sortie contre la source, en
comparant des TEXTES de reponse (ce que la personne lit) et jamais des index.
"""

import collections
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import (  # noqa: E402
    GRAINE_MELANGE,
    charger_cours,
    construire,
    melanger_cours,
    melanger_question,
    permutation_choix,
    serialiser_cours,
)
from outils.empaqueter import empaqueter  # noqa: E402
from outils.fiches import construire_fiches  # noqa: E402

BRUT = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
MELANGE = charger_cours(RACINE)

construire(RACINE)
construire_fiches(RACINE)
empaqueter(RACINE)

SITE = RACINE / "site"
AUTONOME = RACINE / "site-autonome"


def _questions(cours):
    return [(c["num"], q) for c in cours["chapitres"] for q in c.get("quiz", [])]


def _texte_juste(question):
    return question["choix"][question["bonne"]]


# --- La permutation ---------------------------------------------------------------


@pytest.mark.parametrize("nombre", [2, 3, 4, 5, 6])
def test_la_permutation_est_une_permutation(nombre):
    for numero in range(60):
        ordre = permutation_choix(f"q9-{numero:02d}", nombre)
        assert sorted(ordre) == list(range(nombre)), (numero, ordre)


def test_la_permutation_ne_depend_que_de_l_identifiant():
    assert permutation_choix("q3-07", 4) == permutation_choix("q3-07", 4)
    # Deux questions differentes n'ont pas toutes la meme permutation.
    assert len({tuple(permutation_choix(f"q1-{n:02d}", 4)) for n in range(1, 13)}) > 1


def test_la_permutation_est_figee_pour_quelques_identifiants():
    # Valeurs de reference : si elles bougent, TOUS les ordres du site changent (et il
    # faut regenerer les fiches PDF). Changer GRAINE_MELANGE ou le hachage est une
    # decision, pas un effet de bord -- ce test la rend visible.
    assert GRAINE_MELANGE == "uc1-anatomie/choix-des-qcm/v30"
    assert permutation_choix("q1-01", 4) == [0, 2, 3, 1]
    assert permutation_choix("q3-07", 4) == [0, 3, 2, 1]
    assert permutation_choix("q6-12", 4) == [3, 1, 0, 2]
    assert permutation_choix("q2-03", 3) == [2, 1, 0]


def test_la_permutation_ne_depend_ni_du_processus_ni_de_l_horloge():
    # `hash()` de Python est sale a chaque processus (PYTHONHASHSEED) : un melange qui
    # s'en servirait donnerait deux pages differentes a deux constructions. On relance
    # le calcul dans deux processus a graines de hachage differentes.
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from outils.construire import permutation_choix;"
        "print([permutation_choix(f'q{c}-{n:02d}', 4) for c in range(1, 8) for n in range(1, 13)])"
    )
    sorties = set()
    for graine in ("0", "1", "12345", "random"):
        env = {**os.environ, "PYTHONHASHSEED": graine}
        sorties.add(
            subprocess.run(
                [sys.executable, "-c", code, str(RACINE)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            ).stdout
        )
    assert len(sorties) == 1


def test_deux_constructions_donnent_le_meme_cours_et_les_memes_pages():
    assert charger_cours(RACINE) == charger_cours(RACINE)
    avant = {p.name: p.read_bytes() for p in SITE.glob("chapitre-*.html")}
    avant_json = (SITE / "assets" / "cours.json").read_bytes()
    construire(RACINE)
    assert {p.name: p.read_bytes() for p in SITE.glob("chapitre-*.html")} == avant
    assert (SITE / "assets" / "cours.json").read_bytes() == avant_json


def test_ajouter_ou_retoucher_une_question_ne_deplace_pas_les_autres():
    # La permutation d'une question ne depend que de son identifiant.
    seul = melanger_question(BRUT["chapitres"][2]["quiz"][6])
    autre = json.loads(json.dumps(BRUT))
    autre["chapitres"][2]["quiz"].insert(
        0,
        {
            "id": "q3-99",
            "q": "Nouvelle ?",
            "choix": ["a", "b", "c", "d"],
            "bonne": 0,
            "expl": "E",
            "slide": 80,
        },
    )
    autre["chapitres"][2]["quiz"][7]["expl"] += " (retouchee)"
    dans_le_cours = melanger_cours(autre)["chapitres"][2]["quiz"][7]
    assert dans_le_cours["choix"] == seul["choix"]
    assert dans_le_cours["bonne"] == seul["bonne"]


# --- `bonne` suit la permutation ------------------------------------------------------


def test_le_choix_juste_reste_le_meme_texte_apres_melange():
    """Le test qui compte : melanger sans recalculer `bonne` casserait toutes les
    corrections. On compare le TEXTE de la bonne reponse, avant et apres."""
    for (num, brut), (_, melange) in zip(_questions(BRUT), _questions(MELANGE)):
        assert brut["id"] == melange["id"]
        assert _texte_juste(melange) == _texte_juste(brut), brut["id"]


def test_les_choix_sont_les_memes_a_l_ordre_pres():
    for (_, brut), (_, melange) in zip(_questions(BRUT), _questions(MELANGE)):
        assert sorted(melange["choix"]) == sorted(brut["choix"]), brut["id"]
        assert len(melange["choix"]) == len(brut["choix"])
        assert 0 <= melange["bonne"] < len(melange["choix"])


def test_bonne_est_bien_recalcule_et_pas_seulement_conserve():
    # Garde contre un test vide : si le melange ne deplacait jamais la bonne reponse,
    # le test precedent serait vrai meme avec `bonne` inchange. Ici la bonne reponse
    # bouge dans la plupart des questions, et son index bouge avec elle.
    deplacees = [
        (brut["bonne"], melange["bonne"])
        for (_, brut), (_, melange) in zip(_questions(BRUT), _questions(MELANGE))
        if melange["bonne"] != brut["bonne"]
    ]
    assert len(deplacees) > 0.5 * len(_questions(BRUT))


@pytest.mark.parametrize("nombre", [3, 4])
def test_bonne_suit_la_permutation_pour_chaque_position_de_depart(nombre):
    for numero in range(40):
        for bonne in range(nombre):
            choix = [f"choix {i}" for i in range(nombre)]
            question = {
                "id": f"qx-{numero:02d}",
                "q": "Q ?",
                "choix": choix,
                "bonne": bonne,
                "expl": "E",
                "slide": 1,
            }
            resultat = melanger_question(question)
            assert resultat["choix"][resultat["bonne"]] == choix[bonne]


def test_le_melange_ne_change_que_choix_et_bonne_et_ne_modifie_pas_son_argument():
    copie = json.loads(json.dumps(BRUT))
    resultat = melanger_cours(copie)
    assert copie == BRUT  # l'argument n'a pas ete touche
    for (_, brut), (_, melange) in zip(_questions(BRUT), _questions(resultat)):
        assert {k: v for k, v in melange.items() if k not in ("choix", "bonne")} == {
            k: v for k, v in brut.items() if k not in ("choix", "bonne")
        }
        assert list(melange) == list(brut)  # meme ordre des cles
    # Rien d'autre que les questions n'a bouge.
    for a, b in zip(BRUT["chapitres"], resultat["chapitres"]):
        assert {k: v for k, v in a.items() if k != "quiz"} == {
            k: v for k, v in b.items() if k != "quiz"
        }
    assert resultat["meta"] == BRUT["meta"]


def test_une_question_dont_bonne_est_hors_bornes_leve_une_erreur():
    question = {"id": "q1-01", "choix": ["a", "b", "c"], "bonne": 3}
    with pytest.raises(ValueError):
        melanger_question(question)


# --- La repartition -----------------------------------------------------------------


def _repartition(cours):
    compte = collections.Counter(q["bonne"] for _, q in _questions(cours))
    total = sum(compte.values())
    return {position: compte[position] / total for position in range(4)}


def test_avant_le_melange_la_position_a_dominait():
    # Le defaut d'origine, fige : 50 bonnes reponses sur 82 en position A.
    assert _repartition(BRUT)[0] > 0.6


def test_aucune_position_ne_depasse_40_pour_cent_des_bonnes_reponses():
    parts = _repartition(MELANGE)
    assert max(parts.values()) <= 0.40, parts
    # Chaque position sert : un melange qui n'utiliserait que B et C serait tout aussi
    # exploitable que le defaut d'origine.
    assert min(parts.values()) >= 0.10, parts


def test_le_biais_de_position_a_disparu_dans_chaque_chapitre():
    # Avant : 100 % en A sur les chapitres 6 et 7. Par chapitre l'echantillon est petit
    # (11 ou 12 questions) : on ne demande pas la platitude, on interdit le retour d'une
    # position qui ecrase les autres.
    for chapitre in MELANGE["chapitres"]:
        compte = collections.Counter(q["bonne"] for q in chapitre["quiz"])
        assert max(compte.values()) <= 0.5 * len(chapitre["quiz"]), (
            chapitre["num"],
            compte,
        )


# --- Le site : DOM et cours.json parlent du meme ordre ---------------------------------

_RE_QUESTION = re.compile(
    r'<article class="question" id="([^"]+)">(.*?)</article>', re.S
)
_RE_BOUTON = re.compile(
    r'<button class="choix" data-index="(\d+)">(.*?)</button>', re.S
)


def _boutons_par_question(page):
    """{id: [(data-index, texte)]}, dans l'ordre d'affichage."""
    resultat = {}
    for identifiant, corps in _RE_QUESTION.findall(page):
        resultat[identifiant] = [
            (int(i), html.unescape(texte)) for i, texte in _RE_BOUTON.findall(corps)
        ]
    return resultat


def _verifier_dom_contre_donnees(boutons, donnees_par_id, source):
    """Pour chaque question : les boutons affichent les choix dans l'ordre des donnees,
    data-index numerote la position, et le bouton d'index `bonne` porte le texte de la
    bonne reponse de la SOURCE (contenu/cours.json)."""
    brut_par_id = {q["id"]: q for _, q in _questions(BRUT)}
    assert set(boutons) == set(donnees_par_id), source
    for identifiant, rendus in boutons.items():
        donnees = donnees_par_id[identifiant]
        assert [i for i, _ in rendus] == list(range(len(donnees["choix"]))), identifiant
        assert [t for _, t in rendus] == donnees["choix"], (source, identifiant)
        texte_du_bouton_bonne = dict(rendus)[donnees["bonne"]]
        assert texte_du_bouton_bonne == _texte_juste(brut_par_id[identifiant]), (
            source,
            identifiant,
        )


def test_les_pages_du_site_affichent_les_choix_dans_l_ordre_melange():
    for chapitre in MELANGE["chapitres"]:
        page = (SITE / f"chapitre-{chapitre['num']}.html").read_text(encoding="utf-8")
        _verifier_dom_contre_donnees(
            _boutons_par_question(page),
            {q["id"]: q for q in chapitre["quiz"]},
            f"site/chapitre-{chapitre['num']}.html",
        )


def test_cours_json_du_site_donne_un_bonne_qui_designe_le_bouton_juste():
    publie = json.loads((SITE / "assets" / "cours.json").read_text(encoding="utf-8"))
    assert publie == MELANGE
    brut_par_id = {q["id"]: q for _, q in _questions(BRUT)}
    boutons = {}
    for chapitre in MELANGE["chapitres"]:
        page = (SITE / f"chapitre-{chapitre['num']}.html").read_text(encoding="utf-8")
        boutons.update(_boutons_par_question(page))
    for _, question in _questions(publie):
        identifiant = question["id"]
        # interface.js clique le bouton data-index=i puis compare i a `bonne` : le
        # bouton d'index `bonne` doit porter la bonne reponse de la source.
        rendus = dict(boutons[identifiant])
        assert rendus[question["bonne"]] == _texte_juste(brut_par_id[identifiant]), (
            identifiant
        )
        # ... et chaque bouton d'un autre index porte un texte faux.
        for index, texte in rendus.items():
            if index != question["bonne"]:
                assert texte != _texte_juste(brut_par_id[identifiant]), identifiant


def test_cours_json_du_site_ne_differe_de_la_source_que_par_le_melange():
    publie = json.loads((SITE / "assets" / "cours.json").read_text(encoding="utf-8"))
    assert publie != BRUT
    for a, b in zip(BRUT["chapitres"], publie["chapitres"]):
        assert {k: v for k, v in a.items() if k != "quiz"} == {
            k: v for k, v in b.items() if k != "quiz"
        }
    # La mise en forme est celle de la source : le diff git ne montre que le melange.
    assert (SITE / "assets" / "cours.json").read_text(
        encoding="utf-8"
    ) == serialiser_cours(MELANGE)
    assert (RACINE / "contenu" / "cours.json").read_text(
        encoding="utf-8"
    ) == serialiser_cours(BRUT)


def test_la_variante_autonome_suit_le_meme_ordre():
    m = re.search(
        r"window\.COURS_JSON = (.*);\s*$",
        (AUTONOME / "assets" / "cours-data.js").read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert json.loads(m.group(1)) == MELANGE
    donnees = {q["id"]: q for _, q in _questions(MELANGE)}
    pages = {"index.html": None}
    pages.update({f"chapitre-{c['num']}.html": c["num"] for c in MELANGE["chapitres"]})
    boutons_vus = {}
    for nom in pages:
        page = (AUTONOME / nom).read_text(encoding="utf-8")
        boutons = _boutons_par_question(page)
        if nom == "index.html":
            # Le reservoir de la seance du jour porte les 82 questions.
            assert len(boutons) == len(donnees)
            _verifier_dom_contre_donnees(boutons, donnees, f"site-autonome/{nom}")
        boutons_vus.update(boutons)
    assert len(boutons_vus) == len(donnees)


# --- Les fiches PDF : meme ordre, corrige a l'avenant ------------------------------------

_RE_ENONCE = re.compile(
    r'<article class="fiche-quiz" id="([^"]+)">.*?<ol class="fiche-quiz__choix" type="A">(.*?)</ol>',
    re.S,
)
_RE_CORRIGE = re.compile(
    r'<article class="fiche-corrige__quiz"><p class="fiche-corrige__q">(.*?)</p><ol type="A">(.*?)</ol>',
    re.S,
)
_RE_LI = re.compile(r'<li( class="fiche-corrige__bonne")?>(.*?)</li>', re.S)


def _page_fiche(num):
    return (SITE / "pdf" / f"fiche-{num:02d}.html").read_text(encoding="utf-8")


def test_la_fiche_pose_les_questions_dans_le_meme_ordre_que_le_site():
    for chapitre in MELANGE["chapitres"]:
        page = _page_fiche(chapitre["num"])
        enonces = {
            identifiant: [
                html.unescape(t) for t in re.findall(r"<li>(.*?)</li>", liste, re.S)
            ]
            for identifiant, liste in _RE_ENONCE.findall(page)
        }
        assert set(enonces) == {q["id"] for q in chapitre["quiz"]}
        for question in chapitre["quiz"]:
            assert enonces[question["id"]] == question["choix"], question["id"]


def test_le_corrige_de_la_fiche_marque_la_bonne_reponse_de_la_source():
    brut_par_question = {q["q"]: q for _, q in _questions(BRUT)}
    for chapitre in MELANGE["chapitres"]:
        page = _page_fiche(chapitre["num"])
        corriges = _RE_CORRIGE.findall(page)
        assert len(corriges) == len(chapitre["quiz"])
        for (enonce, liste), question in zip(corriges, chapitre["quiz"]):
            assert html.unescape(enonce) == question["q"]
            lignes = [
                (bool(marque), html.unescape(t)) for marque, t in _RE_LI.findall(liste)
            ]
            assert [t for _, t in lignes] == question["choix"], question["id"]
            marquees = [t for marque, t in lignes if marque]
            # Exactement une reponse marquee, et c'est celle de la SOURCE.
            assert marquees == [_texte_juste(brut_par_question[question["q"]])], (
                question["id"]
            )
            # La lettre du corrige (A, B, C, D) est celle du bouton du site.
            assert [marque for marque, _ in lignes].index(True) == question["bonne"]


def _texte_pdf(num):
    sortie = subprocess.run(
        ["pdftotext", "-layout", str(SITE / "pdf" / f"fiche-{num:02d}.pdf"), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return " ".join(sortie.split())


def test_les_pdf_versionnes_portent_l_ordre_melange():
    # Les PDF sont commis (outils/pdf.py) : un PDF oublie lors de la regeneration
    # garderait l'ancien ordre alors que le site a change -- le corrige papier ne
    # correspondrait plus. On lit le texte des PDF et on verifie que les choix de
    # chaque question y apparaissent dans l'ordre melange.
    for chapitre in MELANGE["chapitres"]:
        texte = _texte_pdf(chapitre["num"])
        enonces = texte[: texte.index("Corrigé")]
        for question in chapitre["quiz"]:
            # Les quatre lettres et leurs choix, a la suite : « A. <choix 0> B. <choix 1> ... ».
            # Chercher le texte d'un choix seul ne suffit pas (« Le plan frontal » figure
            # aussi ailleurs dans la fiche).
            attendu = " ".join(
                f"{'ABCD'[i]}. {' '.join(choix.split())}"
                for i, choix in enumerate(question["choix"])
            )
            assert attendu in enonces, (chapitre["num"], question["id"], attendu)


# --- Les explications ne designent pas un choix par son rang ---------------------------
#
# Une fois les choix melanges, « la premiere option » ou « le troisieme distracteur » ne
# designe plus rien de stable : l'explication affichee apres la reponse serait fausse ou
# trompeuse. Cinq explications (q1-03, q1-08, q2-03, q4-02, q4-05) le faisaient ; elles
# nomment desormais le choix par son contenu. Ce test empeche le retour de la formule, y
# compris dans le contenu ajoute plus tard.

_RANG = r"(?:premi[eè]re?s?|deuxi[eè]mes?|second[e]?s?|troisi[eè]mes?|quatri[eè]mes?|derni[eè]re?s?)"
_CIBLE = r"(?:options?|distracteurs?|propositions?|choix|r[ée]ponses?|items?)"
_DESIGNATION_PAR_LE_RANG = re.compile(
    rf"\b{_RANG}\b(?:\W+\w+){{0,2}}?\W+{_CIBLE}\b"  # « la premiere option »
    rf"|\b{_CIBLE}\b\W+(?:\w+\W+){{0,2}}?{_RANG}\b"  # « l'option numero... », « choix 3 »
    r"|\bles (?:deux|trois) (?:premi|derni)\w+"  # « les deux derniers »
    r"|\b(?:option|r[ée]ponse|choix|proposition)s?\s+[A-D]\b"  # « la reponse B »
    r"|\(\s*[A-D]\s*\)|\b[A-D]\s*\)",  # « (B) », « B) »
    re.IGNORECASE,
)


def test_aucune_explication_ni_enonce_ne_designe_un_choix_par_son_rang():
    fautifs = [
        (q["id"], champ, m.group(0))
        for _, q in _questions(BRUT)
        for champ in ("q", "expl")
        for m in _DESIGNATION_PAR_LE_RANG.finditer(q[champ])
    ]
    assert fautifs == []


@pytest.mark.parametrize(
    "phrase",
    [
        "La première option inverse exactement ce couple",  # q2-03, avant correction
        "La troisième option est plus retorse",  # q1-08
        "Le premier distracteur inverse les deux",  # q4-05
        "les deux derniers introduisent la tropomyosine",  # q4-05
        "Les deux autres options ne sont pas des inventions ; la seconde proposition",
        "La réponse B est fausse",
        "Le choix (C) confond les deux",
    ],
)
def test_le_detecteur_reconnait_les_formules_qu_il_doit_interdire(phrase):
    assert _DESIGNATION_PAR_LE_RANG.search(phrase), phrase


@pytest.mark.parametrize(
    "phrase",
    [
        "recouverte par une deuxième membrane, le sarcolemme",  # q4-02, sens anatomique
        "Les trois autres options confondent ou inversent ce couple",
        "Le distracteur le plus tentant est le maxillaire",
        "C'est la première côte qui est concernée",
    ],
)
def test_le_detecteur_laisse_passer_les_usages_legitimes(phrase):
    assert not _DESIGNATION_PAR_LE_RANG.search(phrase), phrase
