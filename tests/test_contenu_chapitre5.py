import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_5 = next(c for c in COURS["chapitres"] if c["num"] == 5)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_5_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_5["cartes"]) <= 25
    assert 8 <= len(CHAPITRE_5["quiz"]) <= 12
    assert 2 <= len(CHAPITRE_5["pieges"]) <= 4
    assert 1 <= len(CHAPITRE_5["planches"]) <= 3


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 136 -l 189 -layout).
    # 136 est la premiere slide de sommaire du chapitre 5, 189 sa derniere
    # slide (credit "Muscles abdominaux - Leurs roles", sans contenu propre).
    # Neuf slides sans texte extractible (138, 157, 167, 170, 174, 176, 181,
    # 184, 189) ont ete rendues en PNG (pdftoppm) et lues a l'oeil : six
    # d'entre elles (157, 174, 181, 189, et partiellement 138/167/170) ne
    # sont que des slides de credit source ou de titre de section sans
    # information propre ; 176 et 184 portent de vraies planches annotees.
    assert CHAPITRE_5["slides"] == [136, 189]


def test_la_table_musculaire_a_les_six_muscles_documentes():
    # Le cours ne donne une origine/terminaison/action individuelles que pour
    # six muscles du tronc : le carre des lombes et l'ilio-psoas (lateraux),
    # le transverse, les deux obliques et le droit de l'abdomen (ventraux).
    # Les muscles dorsaux profonds et superficiels sont nommes par groupes
    # SANS origine/terminaison individuelle (slides 171, 175) : le schema
    # exige ces trois champs non vides, donc ils ne peuvent pas devenir des
    # lignes de la table sans inventer des donnees absentes du cours.
    noms = {m["nom"] for m in CHAPITRE_5["muscles"]}
    assert noms == {
        "Carré des lombes",
        "Ilio-psoas",
        "Transverse de l'abdomen",
        "Oblique interne",
        "Oblique externe",
        "Droit de l'abdomen",
    }


def test_chaque_muscle_a_ses_trois_colonnes_non_vides_et_sa_slide():
    debut, fin = CHAPITRE_5["slides"]
    for muscle in CHAPITRE_5["muscles"]:
        assert muscle["origine"], muscle["nom"]
        assert muscle["terminaison"], muscle["nom"]
        assert muscle["actions"], muscle["nom"]
        assert debut <= muscle["slide"] <= fin, muscle["nom"]


def test_les_slides_des_muscles_sont_celles_relevees_dans_le_pdf():
    # Relevees une par une (pas recopiees d'un brief) : "carre des lombes"
    # est bien sur la slide 179, jamais 176 (176 est une planche muette sur
    # les muscles superficiels du dos -- trapeze, deltoide, rhomboides,
    # grand dorsal -- qui ne nomme pas le carre des lombes).
    attendues = {
        "Carré des lombes": 179,
        "Ilio-psoas": 180,
        "Transverse de l'abdomen": 185,
        "Oblique interne": 186,
        "Oblique externe": 187,
        "Droit de l'abdomen": 188,
    }
    for muscle in CHAPITRE_5["muscles"]:
        assert muscle["slide"] == attendues[muscle["nom"]], muscle["nom"]


def test_orientation_des_fibres_abdominales_est_couverte():
    # Information centrale du chapitre (cf plan) : c'est elle qui explique
    # les actions des quatre muscles abdominaux.
    texte = json.dumps(CHAPITRE_5, ensure_ascii=False).lower()
    for orientation in (
        "transversale",
        "éventail vers le haut",
        "oblique vers le bas",
        "verticale",
    ):
        assert orientation in texte, f"orientation absente : {orientation}"


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_5["cartes"]]
    attendus = [f"c5-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_5["quiz"]]
    attendus = [f"q5-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_5["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_5["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_5["slides"]
    entrees = (
        CHAPITRE_5["sections"]
        + CHAPITRE_5["cartes"]
        + CHAPITRE_5["quiz"]
        + CHAPITRE_5["pieges"]
        + CHAPITRE_5["planches"]
    )
    for entree in entrees:
        assert debut <= entree["slide"] <= fin, entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_5["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_5_existent():
    # Suggerees par le plan (colonne + courbures/regions, vertebre type,
    # orientation des fibres abdominales) et confirmees par le contenu reel.
    assert {
        "rachis-courbures-regions",
        "vertebre-vue-superieure",
        "fibres-abdominales-orientation",
    } <= {p["id"] for p in CHAPITRE_5["planches"]}


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_5["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_aucune_planche_ne_deborde_de_320_unites_de_large():
    for planche in CHAPITRE_5["planches"]:
        _, _, largeur, _ = (float(v) for v in planche["vb"].split())
        assert largeur <= 320, planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_5, ensure_ascii=False).lower()
    for notion in (
        "rachis",
        "cervicales",
        "thoraciques",
        "lombaires",
        "atlas",
        "axis",
        "sacrum",
        "coccyx",
        "squelette axial",
        "lordose",
        "cyphose",
        "scoliose",
        "corps vertébral",
        "arc postérieur",
        "processus transverses",
        "processus épineux",
        "pédicules",
        "lames",
        "ligament longitudinal",
        "ligament jaune",
        "anneau fibreux",
        "nucleus pulposus",
        "hernie discale",
        "vraies côtes",
        "côtes flottantes",
        "manubrium",
        "processus xiphoïde",
        "muscles dorsaux",
        "muscles ventraux",
        "carré des lombes",
        "ilio-psoas",
        "transverse de l'abdomen",
        "oblique interne",
        "oblique externe",
        "droit de l'abdomen",
        "ligne blanche",
    ):
        assert notion in texte, f"notion absente du chapitre 5 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_5["pieges"], ensure_ascii=False).lower()
    for notion in (
        "côté contracté",
        "iliaque",
        "flottantes",
        "occiput",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
