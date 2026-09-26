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
        "muscles": [
            {
                "nom": "Muscle factice",
                "origine": ["Origine factice"],
                "terminaison": ["Terminaison factice"],
                "actions": ["Action factice"],
                "slide": 1,
            }
        ]
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
        "muscles": [
            {
                "nom": "Muscle factice",
                "origine": ["O"],
                "terminaison": ["T"],
                "actions": ["A"],
                "slide": 123,
            }
        ]
    }
    rendu = _rendre_volet("muscles", chapitre_factice)
    ligne = rendu[rendu.index("<tbody>") :]
    debut_th, fin_th = ligne.index("<th>"), ligne.index("</th>")
    assert "slide 123" in ligne[debut_th:fin_th]
    # Le renvoi vit dans le <th> du nom, pas dans une 4e colonne : la bascule
    # mobile mappe .muscles td:nth-of-type(1/2/3) sur exactement trois <td>.
    assert rendu.count("<td>") == 3


def test_les_six_pieges_du_chapitre_1_sont_rendus_avec_leur_slide():
    # Contrat rompu releve en revue de branche : le contenu produit des pieges,
    # le validateur les valide, mais le generateur ne les consommait jamais --
    # zero occurrence dans site/chapitre-1.html avant ce correctif.
    import html
    import json

    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    pieges = cours["chapitres"][0]["pieges"]
    assert len(pieges) == 6
    for piege in pieges:
        assert html.escape(piege["titre"]) in PAGE, piege["titre"]
        assert f"slide {piege['slide']}" in PAGE


def test_l_onglet_pieges_est_present():
    assert 'data-onglet="pieges"' in PAGE


def test_un_piege_n_est_pas_masque():
    # Mise en garde, pas un exercice : lue d'emblee, jamais derriere une
    # tentative -- a la difference du verso d'une carte ou d'une explication
    # de quiz.
    from outils.construire import _rendre_volet

    chapitre_factice = {"pieges": [{"titre": "T", "texte": "Attention.", "slide": 9}]}
    rendu = _rendre_volet("pieges", chapitre_factice)
    assert "Attention." in rendu
    assert 'data-etat="cachee"' not in rendu


def test_l_onglet_muscles_est_absent_quand_il_n_y_a_pas_de_muscle():
    assert 'data-onglet="muscles"' not in PAGE


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


def test_l_accueil_demande_la_date_d_examen():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'type="date"' in accueil
