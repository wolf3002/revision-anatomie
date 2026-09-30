import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_4 = next(c for c in COURS["chapitres"] if c["num"] == 4)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_4_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_4["cartes"]) <= 25
    assert 8 <= len(CHAPITRE_4["quiz"]) <= 12
    assert 2 <= len(CHAPITRE_4["pieges"]) <= 4
    assert 1 <= len(CHAPITRE_4["planches"]) <= 3


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 111 -l 134 -layout) :
    # 111 est la slide de titre/sommaire du chapitre, 134 sa derniere slide.
    # Trois slides sans texte extractible (115, 120, 121) ont ete rendues en
    # PNG (pdftoppm) et lues a l'oeil.
    assert CHAPITRE_4["slides"] == [111, 134]


def test_le_chapitre_4_na_pas_de_muscles():
    # Ce chapitre traite du muscle en general (structure, proprietes), pas
    # de muscles nommes -- la table musculaire vient aux chapitres 5 a 7.
    assert CHAPITRE_4["muscles"] == []


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_4["cartes"]]
    attendus = [f"c4-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_4["quiz"]]
    attendus = [f"q4-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_4["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_4["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_4["slides"]
    entrees = (
        CHAPITRE_4["sections"]
        + CHAPITRE_4["cartes"]
        + CHAPITRE_4["quiz"]
        + CHAPITRE_4["pieges"]
        + CHAPITRE_4["planches"]
    )
    for entree in entrees:
        assert all(debut <= s <= fin for s in slides_de(entree)), entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_4["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_4_existent():
    # Suggerees par le plan (tache 2) : l'emboitement des enveloppes du
    # muscle en coupe, et le sarcomere entre deux stries Z. Les cinq
    # proprietes ne sont pas spatiales : elles restent des cartes de texte,
    # pas un schema fabrique pour faire joli.
    assert {"enveloppes-muscle-coupe", "sarcomere-stries-z"} <= {
        p["id"] for p in CHAPITRE_4["planches"]
    }


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_4["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_aucune_planche_ne_deborde_de_320_unites_de_large():
    # Contrainte du plan (tache 2) : une planche qui ne tient pas dans
    # 320 px se decompose en planches autonomes -- jamais de defilement
    # horizontal. Verifie ici sur le viewBox ; le mode muet (rendu reel,
    # lu a l'oeil) est le test d'acceptation final.
    for planche in CHAPITRE_4["planches"]:
        _, _, largeur, _ = (float(v) for v in planche["vb"].split())
        assert largeur <= 320, planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_4, ensure_ascii=False).lower()
    for notion in (
        "myologie",
        "muscles squelettiques",
        "muscles lisses",
        "muscles mixtes",
        "600 muscles",
        "ventre",
        "tendon",
        "épimysium",
        "périmysium",
        "endomysium",
        "sarcolemme",
        "myofibrille",
        "sarcomère",
        "strie",
        "actine",
        "myosine",
        "filament épais",
        "filament fin",
        "excitabilité",
        "unité motrice",
        "motoneurone",
        "contractilité",
        "secousse musculaire",
        "temps de latence",
        "temps de contraction",
        "temps de relâchement",
        "période réfractaire",
        "élasticité",
        "tonicité",
        "tonus",
        "plasticité",
    ):
        assert notion in texte, f"notion absente du chapitre 4 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_4["pieges"], ensure_ascii=False).lower()
    for notion in (
        "myofibrille",
        "sarcolemme",
        "excitabilité",
        "relâchement",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
