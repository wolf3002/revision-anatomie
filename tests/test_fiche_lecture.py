"""La page d'un chapitre s'ouvre sur la fiche : on lit, puis on s'exerce.

Tout le site repose sur le rappel actif, juste pour une matiere deja
rencontree : on ne retrouve pas ce qu'on n'a jamais lu. Ces tests fixent
l'ordre lecture -> exercices (deux onglets : Fiche, S'exercer), le contenu de la
fiche (complet, rien de masque : elle absorbe les pieges) et, surtout, que la
fiche ne partage avec les exercices ni classe ni identifiant que le script
equipe -- sans quoi elle en heriterait les champs de saisie ou serait clonee a
leur place par le deroule d'exercices.
"""

import html
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import (  # noqa: E402
    EXERCICES,
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


def _fiche(page):
    """Le contenu de la fiche (<div class="fiche">), sans le lien de fin de
    fiche qui la suit : c'est la seule chose qu'elle doit contenir."""
    m = re.search(r'<div class="fiche">(.*?)</div>\s*<p class="fiche-suite', page, re.DOTALL)
    assert m, "fiche introuvable"
    return m.group(1)


def _reservoir(page):
    """Le reservoir cache : les modeles d'exercice que le script clone un a un."""
    m = re.search(
        r'<div id="reservoir-exercices" data-reservoir hidden aria-hidden="true">(.*?)</div>\s*'
        r'<div class="actions"',
        page,
        re.DOTALL,
    )
    assert m, "reservoir introuvable"
    return m.group(1)


def _onglets(page):
    return re.findall(r'<button class="onglet" data-onglet="(\w+)"', page)


# --- L'ordre : lire d'abord, s'exercer ensuite --------------------------------


def test_deux_onglets_dans_l_ordre_lecture_puis_exercices():
    assert [(cle, libelle) for cle, libelle in ONGLETS] == [
        ("fiche", "Fiche"),
        ("exercer", "S'exercer"),
    ]


def test_les_formats_d_exercice_sont_ceux_de_la_seance_du_jour():
    # Les quatre formats que itemsDuCours sait planifier : cartes, questions,
    # pastilles de planche, muscles. Aucun n'est perdu dans S'exercer.
    assert [source for _, source in EXERCICES] == ["cartes", "quiz", "planches", "muscles"]


def test_chaque_chapitre_s_ouvre_sur_la_fiche():
    # interface.js active le PREMIER onglet du DOM : la fiche doit donc l'etre.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert _onglets(page)[0] == "fiche", chapitre["num"]
        assert (
            '<button class="onglet" data-onglet="fiche" role="tab" id="onglet-fiche" '
            'aria-controls="fiche" aria-selected="true">' in page
        )
        # Le volet des exercices est cache a la construction, la fiche non.
        assert re.search(r'<section class="panneau" id="fiche" data-panneau="fiche" [^>]*>', page)
        assert re.search(
            r'<section class="panneau" id="exercer" data-panneau="exercer" [^>]* hidden>', page
        )


def test_un_chapitre_n_a_que_les_deux_onglets():
    for chapitre in CHAPITRES:
        assert _onglets(_page(chapitre["num"])) == ["fiche", "exercer"], chapitre["num"]


def test_la_fiche_mene_aux_exercices_par_un_lien_pas_par_un_bouton():
    # Fin de fiche : « tout lu ? ». Un lien, hors de la fiche (qui reste sans
    # bouton) et masque sans JavaScript, ou il ne ferait rien.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert (
            '<p class="fiche-suite js-seulement">\n        '
            '<a class="action action--majeure" href="#exercer" data-aller="exercer">'
            "S&#x27;exercer sur ce chapitre</a>" in page
        )
        assert page.index('class="fiche"') < page.index('class="fiche-suite')


def test_le_lien_d_accueil_est_present_sur_chaque_chapitre():
    for chapitre in CHAPITRES:
        assert '<a class="retour" href="index.html">' in _page(chapitre["num"])


# --- Un seul deroule d'exercices, le meme partout --------------------------------


def test_s_exercer_reprend_le_bloc_de_la_seance_du_jour():
    # Meme balisage, memes identifiants : interface.js cable le bloc une seule
    # fois, et seul data-chapitre change ce qu'il en tire.
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    identifiants = (
        "seance",
        "seance-message",
        "seance-zone",
        "seance-compte",
        "seance-consolidation",
        "seance-planche",
        "seance-muscle",
        "seance-suivant",
        "seance-quitter",
    )
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert f'<section class="seance seance--chapitre" aria-label="Exercices du chapitre" data-chapitre="{chapitre["num"]}">' in page
        for identifiant in identifiants:
            assert f'id="{identifiant}"' in page, (chapitre["num"], identifiant)
            assert f'id="{identifiant}"' in accueil, identifiant
    # L'accueil, lui, n'est restreint a aucun chapitre.
    assert "data-chapitre=" not in re.search(
        r'<section class="seance[^>]*>', accueil
    ).group(0)


def test_le_reservoir_d_un_chapitre_porte_ses_exercices_et_eux_seuls():
    for chapitre in CHAPITRES:
        reservoir = _reservoir(_page(chapitre["num"]))
        assert reservoir.count('class="carte"') == len(chapitre["cartes"])
        assert reservoir.count('class="question"') == len(chapitre["quiz"])
        assert reservoir.count('class="planche"') == len(chapitre["planches"])
        assert reservoir.count('class="muscles"') == (1 if chapitre["muscles"] else 0)
        for carte in chapitre["cartes"]:
            assert f'id="{carte["id"]}"' in reservoir
        for planche in chapitre["planches"]:
            assert f'id="{planche["id"]}"' in reservoir
        assert 'class="piege"' not in reservoir


def test_le_reservoir_vient_apres_la_zone_d_exercice():
    # Un <marker id="fleche"> ne se resout que sur le PREMIER id du document :
    # celui du clone affiche, pas celui du modele masque.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert page.index('id="seance-zone"') < page.index('id="reservoir-exercices"')


def test_l_accueil_tient_en_une_phrase_puis_la_seance_puis_les_chapitres():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<p class="guide">(.*?)</p>', accueil, re.DOTALL)
    assert m
    texte = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    assert "fiche" in texte and "exerce-toi" in texte
    assert texte.index("fiche") < texte.index("exerce-toi")
    # Une seule phrase : un seul point final.
    assert texte.count(".") == 1, texte
    # Dans l'ordre : la phrase, le bouton de seance, la liste des chapitres.
    assert (
        accueil.index('class="guide"')
        < accueil.index('id="seance"')
        < accueil.index('class="chapitres progression"')
    )


def test_les_reglages_sont_derriere_un_seul_lien_discret():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    liens = re.findall(r'data-action="reglages-bascule"', accueil)
    assert len(liens) == 1
    assert '<button type="button" class="lien-discret" data-action="reglages-bascule"' in accueil
    panneau = re.search(r'<section id="reglages-panneau".*?</section>', accueil, re.DOTALL).group(0)
    assert " hidden>" in panneau.split("\n", 1)[0]
    # Tout ce qui etait eparpille est la, et seulement la.
    for attendu in (
        "data-theme-choix=",
        'id="reglages-date-examen"',
        'data-action="exporter"',
        'id="reglages-import"',
        'data-action="reinitialiser"',
    ):
        assert attendu in panneau, attendu
    # Plus de reglages sur une page de chapitre : on y lit.
    for chapitre in CHAPITRES:
        assert "reglages" not in _page(chapitre["num"])


def test_la_progression_ne_fait_plus_un_bloc_a_part():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert "progression-bloc" not in accueil and 'id="progression-titre"' not in accueil
    # L'anneau vit dans la ligne du chapitre.
    assert accueil.count('<svg class="anneau"') == 7


# --- La fiche est complete -------------------------------------------------------


def test_la_fiche_reprend_chaque_section_et_chaque_point():
    for chapitre in CHAPITRES:
        fiche = _fiche(_page(chapitre["num"]))
        for section in chapitre["sections"]:
            assert html.escape(section["titre"]) in fiche, section["titre"]
            assert f"slide {section['slide']}" in fiche
            for point in section["points"]:
                assert f"<li>{html.escape(point)}</li>" in fiche, point


def test_la_fiche_a_un_plan_dont_chaque_entree_pointe_une_section():
    for chapitre in CHAPITRES:
        fiche = _fiche(_page(chapitre["num"]))
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
        fiche = _fiche(_page(chapitre["num"]))
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


def test_les_pieges_sont_lus_dans_la_fiche_et_nulle_part_ailleurs():
    # L'onglet Pieges est absorbe : chaque piege est lu ou sa notion est traitee,
    # une seule fois dans la page.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        fiche = _fiche(page)
        assert fiche.count('<article class="piege">') == len(chapitre["pieges"])
        assert page.count('<article class="piege">') == len(chapitre["pieges"])
        for piege in chapitre["pieges"]:
            assert html.escape(piege["titre"]) in fiche
            assert f"slide {piege['slide']}" in fiche


def test_la_table_musculaire_est_en_reference_pour_les_chapitres_5_a_7():
    for chapitre in CHAPITRES:
        fiche = _fiche(_page(chapitre["num"]))
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
        fiche = _fiche(_page(chapitre["num"]))
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
        fiche = _fiche(_page(chapitre["num"]))
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
        fiche = _fiche(page)
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
    fiche = _fiche(_page(1))
    assert "id='fleche'" not in fiche and "url(#fleche)" not in fiche
    assert "id='fiche-pl01-fleche'" in fiche and "url(#fiche-pl01-fleche)" in fiche
    # Le modele du reservoir garde l'identifiant d'origine.
    assert "id='fleche'" in _reservoir(_page(1))


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


# --- S'exercer garde sa regle : aucune reponse avant tentative -----------------------


def test_les_modeles_d_exercice_restent_masques_a_la_construction():
    for chapitre in CHAPITRES:
        reservoir = _reservoir(_page(chapitre["num"]))
        assert reservoir.count('<p class="carte__r" data-etat="cachee">') == len(
            chapitre["cartes"]
        )
        assert reservoir.count('class="question__expl" data-etat="cachee"') == len(
            chapitre["quiz"]
        )
        # Ni carte ni question ne sont montrees hors du reservoir : seul le clone
        # que le script insere en zone d'exercice l'est, et il porte le meme masque.
        reste = _page(chapitre["num"]).replace(reservoir, "")
        assert 'class="carte"' not in reste and 'class="question"' not in reste


def test_sans_javascript_la_page_dit_que_les_exercices_en_ont_besoin():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert '<p class="sans-js">Les exercices demandent JavaScript.' in page
        # La barre d'onglets et les liens qui menent aux exercices se retirent
        # sans script (style.css §5.2a).
        assert '<div class="onglets js-seulement" role="tablist"' in page
