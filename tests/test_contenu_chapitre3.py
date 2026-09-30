import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_3 = next(c for c in COURS["chapitres"] if c["num"] == 3)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_3_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_3["cartes"]) <= 27
    assert 8 <= len(CHAPITRE_3["quiz"]) <= 12
    assert 2 <= len(CHAPITRE_3["pieges"]) <= 4


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 72 -l 109 -layout) :
    # 72 est la slide de titre/sommaire du chapitre, 109 sa derniere slide
    # (une image sans texte extractible -- rendue en PNG et lue).
    assert CHAPITRE_3["slides"] == [72, 109]


def test_le_chapitre_3_na_pas_de_muscles():
    assert CHAPITRE_3["muscles"] == []


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_3["cartes"]]
    attendus = [f"c3-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_3["quiz"]]
    attendus = [f"q3-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_3["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_3["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_3["slides"]
    entrees = (
        CHAPITRE_3["sections"]
        + CHAPITRE_3["cartes"]
        + CHAPITRE_3["quiz"]
        + CHAPITRE_3["pieges"]
        + CHAPITRE_3["planches"]
    )
    for entree in entrees:
        assert all(debut <= s <= fin for s in slides_de(entree)), entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_3["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_3_existent():
    # L'articulation synoviale type (slide 77) et les sept diarthroses
    # (slides 81-94), chacune eclatee en planche autonome (comme les trois
    # plans anatomiques du chapitre 1) : une planche large a 7 panneaux ne
    # tiendrait pas dans 320 px.
    assert {
        "articulation-synoviale-coupe",
        "diarthrose-spheroide",
        "diarthrose-ellipsoide",
        "diarthrose-selle",
        "diarthrose-ginglyme",
        "diarthrose-trochoide",
        "diarthrose-bicondylienne",
        "diarthrose-plane",
    } <= {p["id"] for p in CHAPITRE_3["planches"]}


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_3["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_3, ensure_ascii=False).lower()
    for notion in (
        "arthrologie",
        "synarthrose",
        "amphiarthrose",
        "diarthrose",
        "sphéroïde",
        "ellipsoïde",
        "en selle",
        "ginglyme",
        "trochoïde",
        "bicondylienne",
        "arthrodie",
        "capsule articulaire",
        "membrane fibreuse",
        "membrane synoviale",
        "cartilage articulaire",
        "ménisque",
        "ligament",
        "intracapsulaire",
        "extracapsulaire",
        "synovie",
        "entorse",
        "hyperlaxité",
        "luxation",
    ):
        assert notion in texte, f"notion absente du chapitre 3 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_3["pieges"], ensure_ascii=False).lower()
    for notion in (
        "ne se régénère pas",
        "visqueuse",
        "blocage progressif",
        "entorses",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
