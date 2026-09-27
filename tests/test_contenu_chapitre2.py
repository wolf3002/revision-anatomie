import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_2 = next(c for c in COURS["chapitres"] if c["num"] == 2)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_2_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_2["cartes"]) <= 25
    assert 8 <= len(CHAPITRE_2["quiz"]) <= 12
    assert 2 <= len(CHAPITRE_2["pieges"]) <= 4
    assert 1 <= len(CHAPITRE_2["planches"]) <= 3


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 45 -l 70 -layout) :
    # le chapitre commence en 45, avant sa slide de titre en 46.
    assert CHAPITRE_2["slides"] == [45, 70]


def test_le_chapitre_2_na_pas_de_muscles():
    assert CHAPITRE_2["muscles"] == []


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_2["cartes"]]
    attendus = [f"c2-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_2["quiz"]]
    attendus = [f"q2-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_2["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_2["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_2["slides"]
    entrees = (
        CHAPITRE_2["sections"]
        + CHAPITRE_2["cartes"]
        + CHAPITRE_2["quiz"]
        + CHAPITRE_2["pieges"]
        + CHAPITRE_2["planches"]
    )
    for entree in entrees:
        assert debut <= entree["slide"] <= fin, entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_2["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_2_existent():
    # Suggerees par le plan (tache 2) : l'os long en coupe (seule notion
    # d'os assez spatiale pour un schema) et l'opposition axial/appendiculaire.
    assert {"os-long-coupe", "squelette-axial-appendiculaire"} <= {
        p["id"] for p in CHAPITRE_2["planches"]
    }


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_2["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_2, ensure_ascii=False).lower()
    for notion in (
        "cartilage",
        "hyalin",
        "élastique",
        "fibreux",
        "périchondre",
        "vascularisé",
        "squelette axial",
        "squelette appendiculaire",
        "mandibule",
        "colonne mobile",
        "colonne fixe",
        "sacrum",
        "coccyx",
        "diaphyse",
        "épiphyse",
        "métaphyse",
        "périoste",
        "os compact",
        "os spongieux",
        "moelle rouge",
        "moelle jaune",
        "206 os",
    ):
        assert notion in texte, f"notion absente du chapitre 2 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_2["pieges"], ensure_ascii=False).lower()
    for notion in (
        "pas vascularisé",
        "mandibule",
        "vertèbres",
        "minéraux",
        "organiques",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
