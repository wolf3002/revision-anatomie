import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_6 = next(c for c in COURS["chapitres"] if c["num"] == 6)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_6_couvre_le_volume_cible():
    assert 20 <= len(CHAPITRE_6["cartes"]) <= 25
    assert 10 <= len(CHAPITRE_6["quiz"]) <= 12
    assert 3 <= len(CHAPITRE_6["pieges"]) <= 4
    assert 2 <= len(CHAPITRE_6["planches"]) <= 4


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 191 -l 266 -layout).
    # 191 est la premiere slide de sommaire du chapitre 6, 266 sa derniere
    # slide (mouvements du poignet, recapitulatif de fin de chapitre).
    # Quinze slides sans texte extractible (197, 219, 224, 227, 232, 235,
    # 238, 241, 248, 252, 256, 257, 259, 260, 262) ont ete rendues en PNG
    # (pdftoppm) et lues a l'oeil : la plupart sont des cartons de credit
    # source ou de titre de sous-section sans information propre ; 224 est
    # une planche clinique isolee (palpation du scaphoide dans la tabatiere
    # anatomique) ; 238, 256, 259, 260 sont des illustrations qui repetent
    # sans rien ajouter le texte deja donne sur la slide textuelle adjacente.
    assert CHAPITRE_6["slides"] == [191, 266]


def test_la_table_musculaire_a_les_onze_muscles_documentes():
    # Le cours documente individuellement (origine + terminaison + action)
    # onze muscles de ce chapitre. Le subscapulaire a bien sa propre slide
    # (250) mais celle-ci ne donne QUE son action ("Adducteur et rotateur
    # medial du bras") : ni origine ni terminaison n'y sont ecrites, ni dans
    # aucune autre slide du chapitre (verifie par rendu de la slide 250 en
    # image). Le schema exige les trois colonnes non vides : le subscapulaire
    # ne peut donc pas devenir une ligne de la table sans inventer une
    # origine/terminaison absente du cours.
    noms = {m["nom"] for m in CHAPITRE_6["muscles"]}
    assert noms == {
        "Petit rhomboïde",
        "Grand rhomboïde",
        "Trapèze",
        "Grand dorsal",
        "Grand pectoral",
        "Dentelé antérieur",
        "Deltoïde",
        "Biceps brachial",
        "Coraco-brachial",
        "Brachial",
        "Triceps brachial",
    }
    assert "Subscapulaire" not in noms


def test_chaque_muscle_a_ses_trois_colonnes_non_vides_et_sa_slide():
    debut, fin = CHAPITRE_6["slides"]
    for muscle in CHAPITRE_6["muscles"]:
        assert muscle["origine"], muscle["nom"]
        assert muscle["terminaison"], muscle["nom"]
        assert muscle["actions"], muscle["nom"]
        assert debut <= muscle["slide"] <= fin, muscle["nom"]


def test_les_slides_des_muscles_sont_celles_relevees_dans_le_pdf():
    # Relevees une par une : le petit et le grand rhomboide partagent la
    # meme slide (229, qui donne les deux muscles cote a cote), coraco-
    # brachial et brachial partagent la slide 258 pour la meme raison.
    attendues = {
        "Petit rhomboïde": 229,
        "Grand rhomboïde": 229,
        "Trapèze": 231,
        "Grand dorsal": 234,
        "Grand pectoral": 240,
        "Dentelé antérieur": 242,
        "Deltoïde": 247,
        "Biceps brachial": 255,
        "Coraco-brachial": 258,
        "Brachial": 258,
        "Triceps brachial": 261,
    }
    for muscle in CHAPITRE_6["muscles"]:
        assert muscle["slide"] == attendues[muscle["nom"]], muscle["nom"]


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_6["cartes"]]
    attendus = [f"c6-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_6["quiz"]]
    attendus = [f"q6-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_6["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_6["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_6["slides"]
    entrees = (
        CHAPITRE_6["sections"]
        + CHAPITRE_6["cartes"]
        + CHAPITRE_6["quiz"]
        + CHAPITRE_6["pieges"]
        + CHAPITRE_6["planches"]
    )
    for entree in entrees:
        assert debut <= entree["slide"] <= fin, entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_6["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_6_existent():
    # Suggerees par le plan (squelette du membre + articulations, scapula et
    # ses reperes, faisceaux du deltoide, coiffe des rotateurs) et confirmees
    # par le contenu reel.
    assert {
        "squelette-membre-superieur-articulations",
        "scapula-reperes",
        "deltoide-trois-faisceaux",
        "coiffe-rotateurs-vue-postero-laterale",
    } <= {p["id"] for p in CHAPITRE_6["planches"]}


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_6["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_aucune_planche_ne_deborde_de_320_unites_de_large():
    for planche in CHAPITRE_6["planches"]:
        _, _, largeur, _ = (float(v) for v in planche["vb"].split())
        assert largeur <= 320, planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_6, ensure_ascii=False).lower()
    for notion in (
        "ceinture scapulaire",
        "clavicule",
        "scapula",
        "sterno-claviculaire",
        "acromio-claviculaire",
        "scapulo-humérale",
        "cavité glénoïdale",
        "processus coracoïde",
        "acromion",
        "épine",
        "huméro-ulnaire",
        "huméro-radiale",
        "radio-ulnaire proximale",
        "radio-ulnaire distale",
        "ginglyme",
        "sphéroïde",
        "trochoïde",
        "prono-supination",
        "radius",
        "ulna",
        "scaphoïde",
        "lunatum",
        "radio-carpienne",
        "27 os",
        "carpe",
        "métacarpe",
        "phalanges",
        "trapèze",
        "grand dorsal",
        "rhomboïde",
        "grand pectoral",
        "dentelé antérieur",
        "deltoïde",
        "faisceau claviculaire",
        "faisceau acromial",
        "faisceau épineux",
        "coiffe des rotateurs",
        "supra-épineux",
        "infra-épineux",
        "petit rond",
        "grand rond",
        "subscapulaire",
        "biceps brachial",
        "coraco-brachial",
        "triceps brachial",
        "pronateur",
        "supinateur",
    ):
        assert notion in texte, f"notion absente du chapitre 6 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_6["pieges"], ensure_ascii=False).lower()
    for notion in (
        "coiffe des rotateurs",
        "deltoïde",
        "grand rond",
        "faisceau",
        "ginglyme",
        "sphéroïde",
        "trochoïde",
        "scaphoïde",
        "lunatum",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
