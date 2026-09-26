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
