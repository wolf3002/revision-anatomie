"""La page d'un chapitre s'ouvre sur la fiche : on lit, puis on se teste.

Tout le site repose sur le rappel actif, juste pour une matiere deja
rencontree : on ne retrouve pas ce qu'on n'a jamais lu. Ces tests fixent
l'ordre lecture -> exercices, le contenu de la fiche (complet, rien de masque)
et, surtout, que la fiche ne partage avec les onglets de test ni classe ni
identifiant que le script equipe -- sans quoi elle en heriterait les champs de
saisie ou serait clonee a leur place par la seance du jour.
"""

import html
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import (  # noqa: E402
    GROUPES,
    ONGLETS,
    _rendre_planche,
    _rendre_volet,
    _section_pour,
    construire,
)

construire(RACINE)
COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRES = COURS["chapitres"]


def _page(num):
    return (RACINE / "site" / f"chapitre-{num}.html").read_text(encoding="utf-8")


def _volet(page, cle):
    """Le contenu du <section class="volet" data-volet="cle">, sans dependance
    a une bibliotheque HTML : les volets ne s'imbriquent pas."""
    m = re.search(
        rf'<section class="volet" data-volet="{cle}">(.*?)</section>\s*'
        r'(?:<section class="volet"|</div>)',
        page,
        re.DOTALL,
    )
    assert m, f"volet {cle} introuvable"
    return m.group(1)


def _onglets(page):
    return re.findall(r'<button class="onglet" data-onglet="(\w+)">', page)


# --- L'ordre : lire d'abord, s'exercer ensuite --------------------------------


def test_l_ordre_des_onglets_est_lecture_puis_exercices():
    assert [cle for cle, _, _ in ONGLETS] == [
        "fiche",
        "pieges",
        "planche",
        "cartes",
        "quiz",
        "muscles",
    ]


def test_les_onglets_sont_repartis_en_deux_groupes_nommes():
    assert [(cle, libelle) for cle, libelle, _ in GROUPES] == [
        ("apprendre", "Apprendre"),
        ("tester", "Se tester"),
    ]
    apprendre, tester = (tuple(o[0] for o in onglets) for _, _, onglets in GROUPES)
    assert apprendre == ("fiche", "pieges")
    assert tester == ("planche", "cartes", "quiz", "muscles")


def test_chaque_chapitre_s_ouvre_sur_la_fiche():
    # interface.js active le PREMIER onglet du DOM : la fiche doit donc l'etre.
    for chapitre in CHAPITRES:
        assert _onglets(_page(chapitre["num"]))[0] == "fiche", chapitre["num"]


def test_les_onglets_d_un_chapitre_suivent_l_ordre_et_omettent_les_vides():
    for chapitre in CHAPITRES:
        attendu = ["fiche", "pieges", "planche", "cartes", "quiz"]
        if chapitre["muscles"]:
            attendu.append("muscles")
        assert _onglets(_page(chapitre["num"])) == attendu, chapitre["num"]


def test_la_barre_distingue_les_deux_groupes_et_les_numerote():
    page = _page(6)
    groupes = re.findall(
        r'<div class="onglets__groupe" data-groupe="(\w+)" role="group" '
        r'aria-labelledby="(onglets-\w+)">'
        r'<span class="onglets__etiquette" id="\2">'
        r'<span class="onglets__rang mono">(\d)</span>([^<]+)</span>',
        page,
    )
    assert groupes == [
        ("apprendre", "onglets-apprendre", "1", "Apprendre"),
        ("tester", "onglets-tester", "2", "Se tester"),
    ]
    # Les boutons sont dans le bon groupe : la fiche avant l'etiquette 2.
    assert page.index('data-onglet="fiche"') < page.index('data-groupe="tester"')
    assert page.index('data-groupe="tester"') < page.index('data-onglet="planche"')


# --- Guider le premier passage -------------------------------------------------


def test_chaque_chapitre_dit_quoi_faire_dans_quel_ordre():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        m = re.search(r'<p class="guide">(.*?)</p>', page, re.DOTALL)
        assert m, chapitre["num"]
        texte = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        assert "fiche" in texte and "teste-toi" in texte
        # Une seule phrase : un seul point final.
        assert texte.count(".") == 1, texte
        # La ligne est AVANT la barre d'onglets : c'est ce qu'on lit en premier.
        assert page.index('class="guide"') < page.index('class="onglets"')


def test_l_accueil_dit_de_lire_la_fiche_avant_la_seance():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<p class="guide">(.*?)</p>', accueil, re.DOTALL)
    assert m
    texte = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    assert "fiche" in texte and "séance du jour" in texte
    assert texte.index("fiche") < texte.index("séance du jour")
    assert texte.count(".") == 1
    # Avant le bouton de la seance : un nouvel arrivant le voit d'abord.
    assert accueil.index('class="guide"') < accueil.index('id="seance"')


# --- La fiche est complete -------------------------------------------------------


def test_la_fiche_reprend_chaque_section_et_chaque_point():
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        for section in chapitre["sections"]:
            assert html.escape(section["titre"]) in fiche, section["titre"]
            assert f"slide {section['slide']}" in fiche
            for point in section["points"]:
                assert f"<li>{html.escape(point)}</li>" in fiche, point


def test_la_fiche_a_un_plan_dont_chaque_entree_pointe_une_section():
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        cibles = re.findall(r'<a href="#(fiche-[\w-]+)">', fiche)
        attendu = len(chapitre["sections"]) + (1 if chapitre["muscles"] else 0)
        assert len(cibles) == attendu, chapitre["num"]
        for cible in cibles:
            assert fiche.count(f'id="{cible}"') == 1, cible


def test_le_plan_est_replie_a_la_construction_quand_il_est_long():
    # 27 ou 44 entrees ouvertes repousseraient la premiere section d'un ecran.
    assert '<details class="plan" open>' in _page(1)  # 9 sections
    assert '<details class="plan">' in _page(6)  # 44 sections + la table


def test_chaque_planche_est_legendee_dans_la_fiche():
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        assert fiche.count('<figure class="planche-fiche">') == len(
            chapitre["planches"]
        )
        for planche in chapitre["planches"]:
            assert html.escape(planche["titre"]) in fiche
            for pastille in planche["pastilles"]:
                assert (
                    f'class="pastille__t" x="{pastille["x"] + _decalage(pastille)[0]}"'
                    in fiche
                )
                assert html.escape(pastille["t"]) in fiche


def _decalage(pastille):
    from contenu.schema import DECALAGE_LIBELLE

    return DECALAGE_LIBELLE[pastille["ancre"]]


def test_une_planche_est_rattachee_a_la_section_qui_la_traite():
    # Chaque planche du cours tombe pile sur une section de meme slide : la
    # figure vient donc juste apres le texte qui la commente.
    for chapitre in CHAPITRES:
        sections = chapitre["sections"]
        for planche in chapitre["planches"]:
            assert (
                sections[_section_pour(sections, planche["slide"])]["slide"]
                == planche["slide"]
            )


def test_les_pieges_sont_lus_dans_la_fiche_et_dans_leur_onglet():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        fiche = _volet(page, "fiche")
        assert fiche.count('<article class="piege">') == len(chapitre["pieges"])
        assert _volet(page, "pieges").count('<article class="piege">') == len(
            chapitre["pieges"]
        )


def test_la_table_musculaire_est_en_reference_pour_les_chapitres_5_a_7():
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        if not chapitre["muscles"]:
            assert "table-ref" not in fiche
            continue
        assert fiche.count("<tr><th>") == len(chapitre["muscles"])
        for muscle in chapitre["muscles"]:
            assert html.escape(muscle["nom"]) in fiche
            for cle in ("origine", "terminaison", "actions"):
                assert html.escape(" ; ".join(muscle[cle])) in fiche
        # Aucune cellule vide : c'est la table de lecture, pas celle a completer.
        assert "<td></td>" not in fiche
        assert len(re.findall(r"<td>[^<]+</td>", fiche)) == 3 * len(chapitre["muscles"])


def test_les_sections_ne_dependent_pas_de_l_ordre_du_json():
    sections = [
        {"titre": "A", "slide": 10, "points": ["a"]},
        {"titre": "B", "slide": 20, "points": ["b"]},
        {"titre": "C", "slide": 30, "points": ["c"]},
    ]
    assert _section_pour(sections, 20) == 1  # pile sur une section
    assert _section_pour(sections, 25) == 1  # entre deux : la derniere qui precede
    assert _section_pour(sections, 99) == 2  # apres la derniere
    assert _section_pour(sections, 3) == 0  # avant la premiere : la premiere
    assert _section_pour(sections, None) == 2  # sans slide : la derniere


# --- Rien de masque dans la fiche ---------------------------------------------------


def test_la_fiche_ne_masque_rien_et_n_a_aucun_champ():
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        assert 'data-etat="cachee"' not in fiche
        assert "hidden" not in fiche
        assert 'data-mode="muet"' not in fiche
        assert "<input" not in fiche and "<button" not in fiche
        assert "muscle__valeur" not in fiche


# --- La fiche n'est pas equipee par le script -------------------------------------------


def test_la_fiche_ne_partage_aucune_classe_que_le_script_equipe():
    # interface.js cible .planche, .muscles, .carte, .question : un seul de ces
    # noms dans la fiche lui ajouterait des champs de saisie et un mode muet.
    for chapitre in CHAPITRES:
        fiche = _volet(_page(chapitre["num"]), "fiche")
        for interdit in (
            'class="planche"',
            'class="muscles"',
            'class="carte"',
            'class="question"',
        ):
            assert interdit not in fiche, interdit
        assert not re.search(r'class="(?:[^"]* )?planche(?: [^"]*)?"', fiche)
        assert not re.search(r'class="(?:[^"]* )?muscles(?: [^"]*)?"', fiche)


def test_aucun_identifiant_de_la_fiche_n_existe_ailleurs_dans_la_page():
    # La seance du jour retrouve un item par getElementById / tr[data-id] dans
    # la page du chapitre ; la fiche est le premier volet du DOM, elle gagnerait.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        fiche = _volet(page, "fiche")
        reste = page.replace(fiche, "")
        identifiants = re.findall(r"""\bid=['"]([^'"]+)['"]""", fiche)
        assert identifiants
        for identifiant in identifiants:
            assert f'id="{identifiant}"' not in reste, identifiant
            assert f"id='{identifiant}'" not in reste, identifiant
        assert "data-id=" not in fiche


def test_les_marqueurs_de_fleche_de_la_fiche_ont_leurs_propres_id():
    # Le trace porte <marker id='fleche'>, reference par url(#fleche). Deux
    # copies dans la page : le navigateur prend la PREMIERE -- celle de la
    # fiche, display:none sur un onglet de test -- et ne rend plus la pointe.
    fiche = _volet(_page(1), "fiche")
    assert "id='fleche'" not in fiche and "url(#fleche)" not in fiche
    assert "id='fiche-pl01-fleche'" in fiche and "url(#fiche-pl01-fleche)" in fiche
    # L'onglet Planche garde l'identifiant d'origine.
    assert "id='fleche'" in _volet(_page(1), "planche")


def test_le_rendu_des_onglets_de_test_et_des_pdf_est_inchange():
    # outils/fiches.py (PDF, qui ne change pas) reutilise _rendre_planche et
    # _rendre_volet("muscles") : leur enveloppe et leurs classes restent celles
    # d'avant la fiche.
    planche = CHAPITRES[0]["planches"][0]
    rendu = _rendre_planche(planche)
    assert rendu.startswith(
        f'<figure class="planche" id="{planche["id"]}" data-mode="legende">'
    )
    assert "fiche-pl" not in rendu and "id='fleche'" in rendu
    tableau = _rendre_volet("muscles", CHAPITRES[4])
    assert '<table class="muscles">' in tableau and 'data-id="5#muscle#' in tableau


# --- Les onglets de test gardent leur regle : aucune reponse avant tentative ----------


def test_les_onglets_de_test_restent_masques_a_la_construction():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        cartes = _volet(page, "cartes")
        assert cartes.count('data-etat="cachee"') == len(chapitre["cartes"])
        quiz = _volet(page, "quiz")
        assert quiz.count('class="question__expl" data-etat="cachee"') == len(
            chapitre["quiz"]
        )
