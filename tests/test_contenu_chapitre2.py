import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_2 = next(c for c in COURS["chapitres"] if c["num"] == 2)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_2_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_2["cartes"]) <= 30
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
        assert all(debut <= s <= fin for s in slides_de(entree)), entree.get("id", entree.get("titre"))


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


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------


def _texte(entrees):
    return json.dumps(entrees, ensure_ascii=False)


def _prose(chapitre):
    """Tout le texte lisible du chapitre, hors trace SVG (dont les coordonnees contiennent
    n'importe quel nombre)."""
    return _texte(
        {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
        | {"pastilles": [p["pastilles"] for p in chapitre["planches"]]}
    )


def test_la_slide_48_est_reprise_par_des_cartes():
    # La legende de la slide 48 (rouge = elastique, bleu = hyalin, vert = fibreux) et ses huit
    # localisations n'etaient reprises nulle part.
    cartes = [c for c in CHAPITRE_2["cartes"] if c["slide"] == 48]
    assert len(cartes) >= 1
    texte = _texte(cartes).lower()
    for terme in (
        "rouge", "bleu", "vert", "élastique", "hyalin", "fibreux",
        "auriculaire", "trompe auditive", "épiglottique", "laryngé",
        "nez", "trachée", "costaux", "disque intervertébral", "symphyse pubienne",
    ):
        assert terme in texte, terme


def test_q2_02_ne_pretend_plus_que_le_cours_ne_localise_pas_le_cartilage_elastique():
    question = next(q for q in CHAPITRE_2["quiz"] if q["id"] == "q2-02")
    assert "aucune localisation" not in question["expl"]
    assert "auriculaire" in question["expl"]
    assert 48 in slides_de(question)


def test_le_vocabulaire_absent_du_cours_n_est_pas_employe():
    # « maxillaire » n'apparait nulle part dans le cours (« mâchoire supérieure »), le
    # chiffre 33 non plus (le cours ne compte pas les vertebres du sacrum ni du coccyx).
    texte = _prose(CHAPITRE_2)
    assert "maxillaire" not in texte.lower()
    assert "33" not in texte
    assert "cicatrise" not in texte
    assert "Sur les 21 os de la tête, un seul" not in texte


def test_q2_06_ne_propose_que_des_repartitions_de_la_colonne_mobile():
    # L'enonce demande la colonne MOBILE : aucun distracteur ne doit y ajouter la fixe.
    question = next(q for q in CHAPITRE_2["quiz"] if q["id"] == "q2-06")
    assert question["choix"][question["bonne"]] == "7 cervicales, 12 thoraciques, 5 lombaires"
    for choix in question["choix"]:
        assert "sacrum" not in choix and "coccyx" not in choix, choix


def test_c2_10_ne_designe_pas_le_mauvais_squelette():
    # « ce dernier » designait grammaticalement le squelette appendiculaire, alors que la
    # reponse decrit l'axial.
    carte = next(c for c in CHAPITRE_2["cartes"] if c["id"] == "c2-10")
    assert "ce dernier" not in carte["q"]
    assert "squelette axial" in carte["q"]


# Ni le cours ni aucune source ne dit quelle confusion est la plus courante chez les eleves :
# une affirmation de frequence donne au site une autorite qu'il n'a pas. « On inverse
# facilement » ou « confusion classique » decrivent un risque sans pretendre le mesurer.
FORMULES_DE_FREQUENCE = ("fréquen", "le plus souvent", "la plupart", "généralement")


def test_aucune_affirmation_de_frequence_n_est_laissee_au_chapitre_2():
    prose = _prose(CHAPITRE_2).lower()
    for formule in FORMULES_DE_FREQUENCE:
        assert formule not in prose, formule
