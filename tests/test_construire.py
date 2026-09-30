import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import construire

FICHIERS = construire(RACINE)
PAGE = (RACINE / "site" / "chapitre-1.html").read_text(encoding="utf-8")


def test_la_page_du_chapitre_1_est_ecrite():
    assert (RACINE / "site" / "chapitre-1.html") in FICHIERS


def test_la_page_interdit_l_indexation():
    assert 'name="robots"' in PAGE and "noindex" in PAGE


def test_toutes_les_cartes_sont_dans_le_dom():
    import json

    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    for carte in cours["chapitres"][0]["cartes"]:
        assert carte["id"] in PAGE, carte["id"]


def test_les_reponses_sont_masquees_par_defaut():
    assert 'data-etat="cachee"' in PAGE


def test_chaque_renvoi_de_slide_est_affiche():
    assert "slide 9" in PAGE


def test_une_entree_hors_cours_est_visiblement_marquee():
    # Aucune entree du chapitre 1 ne porte hors_cours=True : sans ce test batard,
    # la disparition de la branche dans _src() passerait inapercue.
    from outils.construire import _rendre_volet

    chapitre_factice = {
        "cartes": [
            {
                "id": "hc-01",
                "q": "Question hors cours",
                "r": "Reponse",
                "hors_cours": True,
            }
        ]
    }
    assert "[hors cours]" in _rendre_volet("cartes", chapitre_factice)


def test_la_table_des_muscles_est_structuree():
    # Code mort pour le chapitre 1 (muscles=[]) : les chapitres 5 a 7 en dependent.
    from outils.construire import _rendre_volet

    chapitre_factice = {
        "num": 5,
        "muscles": [
            {
                "nom": "Muscle factice",
                "origine": ["Origine factice"],
                "terminaison": ["Terminaison factice"],
                "actions": ["Action factice"],
                "slide": 1,
            }
        ],
    }
    rendu = _rendre_volet("muscles", chapitre_factice)
    assert '<table class="muscles">' in rendu
    assert "<caption>" in rendu
    assert "<thead>" in rendu and "<tbody>" in rendu
    for colonne in ("Muscle", "Origine", "Terminaison", "Action"):
        assert colonne in rendu
    assert "Muscle factice" in rendu


def test_la_ligne_de_muscle_affiche_son_renvoi_de_slide():
    # Le seul volet ou _src() n'etait jamais appele -- invariant de tracabilite
    # rompu (contenu/schema.py exige et valide un slide par muscle).
    from outils.construire import _rendre_volet

    chapitre_factice = {
        "num": 5,
        "muscles": [
            {
                "nom": "Muscle factice",
                "origine": ["O"],
                "terminaison": ["T"],
                "actions": ["A"],
                "slide": 123,
            }
        ],
    }
    rendu = _rendre_volet("muscles", chapitre_factice)
    ligne = rendu[rendu.index("<tbody>") :]
    debut_th, fin_th = ligne.index("<th>"), ligne.index("</th>")
    assert "slide 123" in ligne[debut_th:fin_th]
    # Le renvoi vit dans le <th> du nom, pas dans une 4e colonne : la bascule
    # mobile mappe .muscles td:nth-of-type(1/2/3) sur exactement trois <td>.
    assert rendu.count("<td>") == 3


def test_une_ligne_de_muscle_porte_son_identifiant_planifiable():
    # Defaut Critical (plan chapitres-2-a-7, tache 1) : sans data-id, le
    # planificateur ne peut pas faire revenir un muscle rate. Le nom peut
    # contenir des espaces/apostrophes -- invalides dans un attribut id --
    # d'ou data-id, lu par interface.js/exercices.itemsDuCours (meme formule
    # {chapitre}#muscle#{nom}).
    from outils.construire import _rendre_volet

    chapitre_factice = {
        "num": 6,
        "muscles": [
            {
                "nom": "Fléchisseur ulnaire du carpe",
                "origine": ["O"],
                "terminaison": ["T"],
                "actions": ["A"],
                "slide": 200,
            }
        ],
    }
    rendu = _rendre_volet("muscles", chapitre_factice)
    assert 'data-id="6#muscle#Fléchisseur ulnaire du carpe"' in rendu


def test_les_valeurs_de_muscle_restent_lisibles_sans_javascript():
    # Complement du defaut Critical : les valeurs ne sont PAS masquees a la
    # construction (aucun data-etat="cachee" ici, a la difference du verso
    # d'une carte) -- si le script echoue, la table degrade en reference lue.
    # C'est interface.js qui les masque dynamiquement (mode="champs" par
    # defaut) en s'appuyant sur le wrapper .muscle__valeur ci-dessous.
    from outils.construire import _rendre_volet

    chapitre_factice = {
        "num": 5,
        "muscles": [
            {
                "nom": "Muscle factice",
                "origine": ["Origine lisible"],
                "terminaison": ["Terminaison lisible"],
                "actions": ["Action lisible"],
                "slide": 1,
            }
        ],
    }
    rendu = _rendre_volet("muscles", chapitre_factice)
    assert 'data-etat="cachee"' not in rendu
    assert rendu.count('<span class="muscle__valeur">') == 3
    for valeur in ("Origine lisible", "Terminaison lisible", "Action lisible"):
        assert valeur in rendu


def test_les_six_pieges_du_chapitre_1_sont_rendus_avec_leur_slide():
    # Contrat rompu releve en revue de branche : le contenu produit des pieges,
    # le validateur les valide, mais le generateur ne les consommait jamais --
    # zero occurrence dans site/chapitre-1.html avant ce correctif.
    import html
    import json

    from contenu.schema import slides_de
    from outils.construire import _libelle_slides

    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    pieges = cours["chapitres"][0]["pieges"]
    assert len(pieges) == 6
    for piege in pieges:
        assert html.escape(piege["titre"]) in PAGE, piege["titre"]
        assert _libelle_slides(slides_de(piege)) in PAGE


def test_une_page_de_chapitre_n_a_que_deux_onglets_fiche_puis_s_exercer():
    # Six onglets (fiche, pieges, planche, cartes, quiz, muscles) n'en font plus
    # que deux : la fiche absorbe les pieges, S'exercer enchaine les quatre formats.
    import re

    assert re.findall(r'data-onglet="(\w+)"', PAGE) == ["fiche", "exercer"]
    for ancien in ("pieges", "planche", "cartes", "quiz", "muscles"):
        assert f'data-onglet="{ancien}"' not in PAGE, ancien


def test_un_piege_n_est_pas_masque():
    # Mise en garde, pas un exercice : lue d'emblee, jamais derriere une
    # tentative -- a la difference du verso d'une carte ou d'une explication
    # de quiz.
    from outils.construire import _rendre_volet

    chapitre_factice = {"pieges": [{"titre": "T", "texte": "Attention.", "slide": 9}]}
    rendu = _rendre_volet("pieges", chapitre_factice)
    assert "Attention." in rendu
    assert 'data-etat="cachee"' not in rendu


def test_pas_de_table_de_muscles_quand_le_chapitre_n_en_a_pas():
    # Ni table a lire dans la fiche, ni table a completer dans les exercices.
    assert "table-ref" not in PAGE
    assert 'class="muscles"' not in PAGE


def test_le_contenu_du_cours_est_present_sans_javascript():
    assert "Corps humain, vivant, debout" in PAGE


def test_une_copie_du_contenu_est_publiee_pour_le_client():
    assert (RACINE / "site" / "assets" / "cours.json").exists()


def test_l_accueil_est_ecrit():
    assert (RACINE / "site" / "index.html").exists()


def test_l_accueil_propose_la_seance_du_jour():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'id="seance"' in accueil


def test_l_accueil_liste_les_chapitres_disponibles():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert "chapitre-1.html" in accueil


def test_chaque_chapitre_de_l_accueil_a_deux_actions_explicites():
    import json
    import re

    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    lignes = re.findall(r'<li class="chapitre".*?</li>', accueil, re.DOTALL)
    assert len(lignes) == len(cours["chapitres"]) == 7
    for ligne, chapitre in zip(lignes, cours["chapitres"]):
        num = chapitre["num"]
        assert f'<a class="action" href="chapitre-{num}.html">Lire la fiche</a>' in ligne
        assert f'href="chapitre-{num}.html#exercer">S&#x27;exercer</a>' in ligne
        # Une seule sobre indication de progression par chapitre, l'anneau
        # portant le numero.
        assert ligne.count('class="anneau__valeur') == 1
        assert f'class="anneau__num" x="24" y="24">{num}</text>' in ligne


def test_l_accueil_demande_la_date_d_examen():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'type="date"' in accueil


# --- Le renvoi de slide : un entier ou une liste --------------------------------


def test_une_slide_seule_s_affiche_au_singulier():
    from outils.construire import _src

    assert _src({"slide": 319}) == '<span class="src">slide 319</span>'


def test_deux_slides_s_affichent_avec_et():
    from outils.construire import _src

    assert _src({"slide": [319, 320]}) == '<span class="src">slides 319 et 320</span>'


def test_trois_slides_s_affichent_avec_virgules_puis_et():
    from outils.construire import _src

    assert (
        _src({"slide": [309, 316, 320]})
        == '<span class="src">slides 309, 316 et 320</span>'
    )


def test_une_liste_d_un_seul_element_s_affiche_comme_un_entier():
    from outils.construire import _src

    assert _src({"slide": [319]}) == _src({"slide": 319})


def test_les_slides_s_affichent_dans_l_ordre_croissant():
    from outils.construire import _src

    assert "slides 309, 316 et 320" in _src({"slide": [320, 309, 316]})


def test_hors_cours_l_emporte_sur_la_slide():
    from outils.construire import _src

    assert "[hors cours]" in _src({"hors_cours": True, "slide": [1, 2]})


def test_une_entree_sans_slide_ni_hors_cours_fait_echouer_le_rendu():
    import pytest

    from outils.construire import _src

    with pytest.raises(ValueError):
        _src({"id": "c1-01"})
    with pytest.raises(ValueError):
        _src({"id": "c1-01", "slide": []})


def test_le_renvoi_de_slide_est_rendu_dans_chaque_volet_pour_les_deux_formes():
    from outils.construire import _rendre_piege, _rendre_planche, _rendre_volet

    muscle = {
        "nom": "Biceps femoral",
        "origine": ["o"],
        "terminaison": ["t"],
        "actions": ["a"],
    }
    for slide, attendu in ((319, "slide 319"), ([319, 320], "slides 319 et 320")):
        chapitre = {
            "num": 7,
            "cartes": [{"id": "c7-01", "q": "Q", "r": "R", "slide": slide}],
            "quiz": [
                {
                    "id": "q7-01",
                    "q": "Q",
                    "choix": ["a", "b", "c"],
                    "bonne": 0,
                    "expl": "E",
                    "slide": slide,
                }
            ],
            "muscles": [{**muscle, "slide": slide}],
        }
        for cle in ("cartes", "quiz", "muscles"):
            assert f">{attendu}<" in _rendre_volet(cle, chapitre), (cle, slide)
        piege = {"titre": "T", "texte": "X", "slide": slide}
        assert f">{attendu}<" in _rendre_piege(piege), slide
        planche = {
            "id": "p1",
            "titre": "T",
            "vb": "0 0 100 100",
            "dessin": "<g/>",
            "pastilles": [],
            "slide": slide,
        }
        assert f">{attendu}<" in _rendre_planche(planche), slide
