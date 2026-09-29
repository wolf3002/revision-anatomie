import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contenu.schema import valider_cours


def cours_minimal(**remplacements):
    chapitre = {
        "num": 1,
        "titre": "Terminologie anatomique",
        "slides": [7, 45],
        "sections": [
            {"titre": "Position anatomique", "points": ["Debout"], "slide": 9}
        ],
        "planches": [],
        "cartes": [{"id": "c1-01", "q": "Question ?", "r": "Reponse", "slide": 9}],
        "quiz": [
            {
                "id": "q1-01",
                "q": "Question ?",
                "choix": ["A", "B", "C"],
                "bonne": 0,
                "expl": "Parce que.",
                "slide": 9,
            }
        ],
        "muscles": [],
        "pieges": [{"titre": "Piege", "texte": "Attention.", "slide": 9}],
    }
    chapitre.update(remplacements)
    return {
        "meta": {"cours": "UC1", "source": "cours.pdf", "slides": 328},
        "chapitres": [chapitre],
    }


def test_cours_conforme_ne_produit_aucune_erreur():
    assert valider_cours(cours_minimal()) == []


def test_slide_hors_plage_du_chapitre_est_signalee():
    cours = cours_minimal(cartes=[{"id": "c1-01", "q": "Q ?", "r": "R", "slide": 300}])
    erreurs = valider_cours(cours)
    assert any("300" in e and "c1-01" in e for e in erreurs)


def test_identifiant_duplique_est_signale():
    cours = cours_minimal(
        cartes=[
            {"id": "c1-01", "q": "Q1 ?", "r": "R1", "slide": 9},
            {"id": "c1-01", "q": "Q2 ?", "r": "R2", "slide": 10},
        ]
    )
    assert any("c1-01" in e and "double" in e for e in valider_cours(cours))


def test_quiz_avec_moins_de_trois_choix_est_signale():
    cours = cours_minimal(
        quiz=[
            {
                "id": "q1-01",
                "q": "Q ?",
                "choix": ["A", "B"],
                "bonne": 0,
                "expl": "E",
                "slide": 9,
            }
        ]
    )
    assert any("q1-01" in e and "choix" in e for e in valider_cours(cours))


def test_bonne_reponse_hors_bornes_est_signalee():
    cours = cours_minimal(
        quiz=[
            {
                "id": "q1-01",
                "q": "Q ?",
                "choix": ["A", "B", "C"],
                "bonne": 5,
                "expl": "E",
                "slide": 9,
            }
        ]
    )
    assert any("q1-01" in e and "bonne" in e for e in valider_cours(cours))


def test_explication_de_quiz_vide_est_signalee():
    cours = cours_minimal(
        quiz=[
            {
                "id": "q1-01",
                "q": "Q ?",
                "choix": ["A", "B", "C"],
                "bonne": 0,
                "expl": "",
                "slide": 9,
            }
        ]
    )
    assert any("q1-01" in e and "explication" in e for e in valider_cours(cours))


def test_planche_contenant_du_texte_dans_le_trace_est_refusee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><text x='5' y='5'>Femur</text></g>",
                "pastilles": [
                    {"n": 1, "x": 10, "y": 10, "t": "Femur", "ancre": "start"}
                ],
            }
        ]
    )
    assert any("p1" in e and "text" in e for e in valider_cours(cours))


def test_pastille_hors_du_cadre_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [
                    {"n": 1, "x": 480, "y": 10, "t": "Femur", "ancre": "start"}
                ],
            }
        ]
    )
    assert any("p1" in e and "cadre" in e for e in valider_cours(cours))


def test_numerotation_de_pastilles_non_contigue_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [
                    {"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"},
                    {"n": 3, "x": 20, "y": 20, "t": "B", "ancre": "start"},
                ],
            }
        ]
    )
    assert any("p1" in e and "numerotation" in e for e in valider_cours(cours))


def test_mention_hors_cours_autorise_une_slide_absente():
    cours = cours_minimal(
        cartes=[
            {"id": "c1-01", "q": "Q ?", "r": "R", "hors_cours": True},
        ]
    )
    assert valider_cours(cours) == []


def test_planche_sans_slide_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [{"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"}],
            }
        ]
    )
    assert any("p1" in e and "slide" in e for e in valider_cours(cours))


def test_planche_avec_slide_hors_plage_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [{"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"}],
                "slide": 300,
            }
        ]
    )
    erreurs = valider_cours(cours)
    assert any("p1" in e and "300" in e for e in erreurs)


def test_pastille_middle_dont_le_libelle_deborde_est_signalee():
    # viewBox de hauteur 100 ; pastille middle a y=90 -> libelle a 90+24=114, hors cadre.
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [{"n": 1, "x": 50, "y": 90, "t": "A", "ancre": "middle"}],
            }
        ]
    )
    erreurs = valider_cours(cours)
    assert any("p1" in e and "decale" in e for e in erreurs)
    # message distinct de celui de la pastille hors cadre (defaut deja teste ailleurs)
    assert not any("hors du cadre" in e for e in erreurs)


def test_pastille_middle_avec_marge_suffisante_est_acceptee():
    # viewBox de hauteur 100 ; pastille middle a y=70 -> libelle a 70+24=94, dans le cadre.
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [{"n": 1, "x": 50, "y": 70, "t": "A", "ancre": "middle"}],
                "slide": 9,
            }
        ]
    )
    assert valider_cours(cours) == []


def test_pastille_avec_ancre_invalide_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [{"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "centre"}],
            }
        ]
    )
    assert any("p1" in e and "ancre" in e for e in valider_cours(cours))


def test_pastille_avec_indice_vide_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [
                    {
                        "n": 1,
                        "x": 10,
                        "y": 10,
                        "t": "A",
                        "ancre": "start",
                        "indice": "   ",
                    }
                ],
            }
        ]
    )
    assert any("p1" in e and "indice" in e for e in valider_cours(cours))


def test_pastille_avec_plan_invalide_est_signalee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [
                    {
                        "n": 1,
                        "x": 10,
                        "y": 10,
                        "t": "A",
                        "ancre": "start",
                        "plan": "transverse",
                    }
                ],
            }
        ]
    )
    assert any("p1" in e and "plan" in e for e in valider_cours(cours))


def test_pastille_sans_plan_ou_avec_plan_valide_est_acceptee():
    cours = cours_minimal(
        planches=[
            {
                "id": "p1",
                "titre": "T",
                "vb": "0 0 100 100",
                "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
                "pastilles": [
                    {"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"},
                    {
                        "n": 2,
                        "x": 20,
                        "y": 20,
                        "t": "B",
                        "ancre": "start",
                        "plan": "sagittal",
                    },
                ],
                "slide": 9,
            }
        ]
    )
    assert valider_cours(cours) == []


def test_valider_planche_seule_sans_bornes_accepte_absence_de_slide():
    from contenu.schema import valider_planche

    planche = {
        "id": "p1",
        "titre": "T",
        "vb": "0 0 100 100",
        "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
        "pastilles": [{"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"}],
    }
    assert valider_planche(planche) == []


# --- Emprise du texte d'un libelle ---------------------------------------------
#
# valider_planche ne verifiait que le point d'ancrage : « Tete de la fibula »,
# ancre a 176 unites dans un viewBox de 220, etait accepte et rogne a 77 %.


def _planche_a_une_pastille(vb, x, y, texte, ancre):
    return {
        "id": "p1",
        "titre": "T",
        "vb": vb,
        "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
        "pastilles": [{"n": 1, "x": x, "y": y, "t": texte, "ancre": ancre}],
    }


def test_une_etiquette_longue_ancree_pres_du_bord_droit_est_refusee():
    from contenu.schema import valider_planche

    # Ancre « start » a x=180 : le texte commence a 194 et s'etend sur plus de 100
    # unites dans un cadre de 220 -- le cas reel de « Tete de la fibula ».
    planche = _planche_a_une_pastille("0 0 220 400", 180, 320, "Tête de la fibula", "start")
    erreurs = valider_planche(planche)
    assert len(erreurs) == 1
    assert "deborde" in erreurs[0] and "droite" in erreurs[0]
    assert "Tête de la fibula" in erreurs[0]


def test_une_etiquette_longue_ancree_pres_du_bord_gauche_est_refusee():
    from contenu.schema import valider_planche

    planche = _planche_a_une_pastille("0 0 220 400", 96, 150, "Semi-membraneux", "end")
    erreurs = valider_planche(planche)
    assert len(erreurs) == 1 and "gauche" in erreurs[0]


def test_une_etiquette_centree_trop_large_pour_le_cadre_est_refusee():
    from contenu.schema import valider_planche

    planche = _planche_a_une_pastille("0 0 120 100", 60, 40, "Tubérosité ischiatique", "middle")
    assert valider_planche(planche)


def test_la_meme_etiquette_tient_quand_le_cadre_est_elargi():
    from contenu.schema import valider_planche

    planche = _planche_a_une_pastille("0 0 340 400", 180, 320, "Tête de la fibula", "start")
    assert valider_planche(planche) == []
    # ... ou quand le libelle passe sous la pastille (ancre « middle ») et que le
    # trace est decale : c'est la solution retenue pour les ischio-jambiers.
    planche = _planche_a_une_pastille("0 0 300 400", 210, 320, "Tête de la fibula", "middle")
    assert valider_planche(planche) == []


def test_un_libelle_qui_deborde_en_hauteur_est_refuse():
    from contenu.schema import valider_planche

    # Ancre « middle » : le texte est pose 24 unites sous la pastille.
    planche = _planche_a_une_pastille("0 0 200 60", 100, 40, "Court", "middle")
    erreurs = valider_planche(planche)
    assert any("hauteur" in e for e in erreurs) or any("cadre" in e for e in erreurs)


def test_l_estimation_de_largeur_couvre_les_mesures_de_chrome():
    # Largeurs getBBox() mesurees dans Chrome (police Public Sans, 15 px) : le
    # controle doit les estimer par exces, sans jamais les sous-estimer de plus
    # de 5 % (constantes documentees dans contenu/schema.py).
    from contenu.schema import largeur_estimee_libelle

    mesures = {
        "Tête de la fibula": 111.1,
        "Vaste intermédiaire": 135.3,
        "Tibio-fibulaire proximale": 170.1,
        "Endomysium": 88.9,
        "Semi-membraneux": 132.3,
        "Rotation, pronation, supination": 221.0,
    }
    for texte, mesure in mesures.items():
        estimee = largeur_estimee_libelle(texte)
        assert estimee >= mesure * 0.95, (texte, estimee, mesure)
        assert estimee <= mesure * 1.25, (texte, estimee, mesure)
