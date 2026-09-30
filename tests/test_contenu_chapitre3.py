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
    assert 18 <= len(CHAPITRE_3["cartes"]) <= 35
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


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------
import math
import re


def _planche(planche_id):
    return next(p for p in CHAPITRE_3["planches"] if p["id"] == planche_id)


def _prose(chapitre):
    """Texte lisible du chapitre, hors trace SVG."""
    donnees = {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
    donnees["pastilles"] = [p["pastilles"] for p in chapitre["planches"]]
    return json.dumps(donnees, ensure_ascii=False)


def _point_de_bezier_quadratique(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * a + 2 * t * (1 - t) * b + t**2 * c for a, b, c in zip(p0, p1, p2))


def test_le_ligament_de_la_planche_est_dit_extracapsulaire_et_cite_les_slides_100_et_104():
    # Le cours distingue ligaments intra- et extracapsulaires (slide 104), et la slide 100
    # montre le ligament articulaire. Le trace montre un ligament HORS de la capsule ; l'ancien
    # indice (« hors de la capsule ») enseignait que tout ligament l'est.
    planche = _planche("articulation-synoviale-coupe")
    pastille = next(p for p in planche["pastilles"] if p["n"] == 6)
    assert pastille["t"] == "Ligament extracapsulaire"
    assert "ici hors de la capsule" in pastille["indice"]
    slides = slides_de(planche)
    assert 100 in slides and 104 in slides


def test_la_fleche_du_ligament_part_du_ligament_et_non_de_la_capsule():
    planche = _planche("articulation-synoviale-coupe")
    dessin = planche["dessin"]
    ligament = re.search(r"<path d='M(\d+),(\d+) Q(\d+),(\d+) (\d+),(\d+)' [^>]*stroke-width='3'", dessin)
    capsule = re.search(r"<path d='M300,150 Q(\d+),(\d+) (\d+),(\d+)'", dessin)
    assert ligament and capsule
    l0, l1, l2 = (int(ligament[1]), int(ligament[2])), (int(ligament[3]), int(ligament[4])), (int(ligament[5]), int(ligament[6]))
    c0, c1, c2 = (300, 150), (int(capsule[1]), int(capsule[2])), (int(capsule[3]), int(capsule[4]))
    # La fleche du repere 6 : celle qui aboutit a gauche de la pastille 6 (x = 390 - 18).
    pastille = next(p for p in planche["pastilles"] if p["n"] == 6)
    fleches = re.findall(r"<path d='M(\d+),(\d+) L(\d+),(\d+)' marker-end", dessin)
    depart = next(
        (int(f[0]), int(f[1]))
        for f in fleches
        if abs(int(f[2]) - (pastille["x"] - 18)) <= 2 and abs(int(f[3]) - pastille["y"]) <= 10
    )
    pas = [i / 500 for i in range(501)]
    distance_ligament = min(math.dist(depart, _point_de_bezier_quadratique(l0, l1, l2, t)) for t in pas)
    distance_capsule = min(math.dist(depart, _point_de_bezier_quadratique(c0, c1, c2, t)) for t in pas)
    assert distance_ligament <= 2
    assert distance_ligament < distance_capsule


def test_l_ellipsoide_a_son_exemple_le_poignet():
    # Slide 84, legende de la figure : « ... entre l'extremite distale du radius, le
    # scaphoide et le semi-lunaire du carpe (poignet) ». Texte dans l'image ; le cours
    # n'emploie pas « radio-carpienne » ici.
    planche = _planche("diarthrose-ellipsoide")
    assert [p["t"] for p in planche["pastilles"]][-1] == "Ex : le poignet"
    assert len(planche["pastilles"]) == 4
    section = next(s for s in CHAPITRE_3["sections"] if s["titre"].startswith("B."))
    assert "poignet" in " ".join(section["points"])
    carte = next(c for c in CHAPITRE_3["cartes"] if c["id"] == "c3-08")
    assert "poignet" in carte["r"] and "exemple" in carte["q"].lower()
    assert "radio-carpienne" not in _prose(CHAPITRE_3).lower()


def test_l_exemple_de_la_spheroide_cite_la_slide_82():
    # « EX: LA HANCHE » est en slide 82 ; la slide 81 ne porte que la forme et les 3 axes.
    entrees = [
        next(s for s in CHAPITRE_3["sections"] if s["titre"].startswith("A.")),
        next(c for c in CHAPITRE_3["cartes"] if c["id"] == "c3-07"),
        next(q for q in CHAPITRE_3["quiz"] if q["id"] == "q3-01"),
        _planche("diarthrose-spheroide"),
    ]
    for entree in entrees:
        assert slides_de(entree) == [81, 82], entree.get("id", entree.get("titre"))


def test_aucun_ajout_non_source_dans_le_chapitre_3():
    texte = _prose(CHAPITRE_3)
    for expression in (
        "quasi plane",
        "usure ou à l'inflammation",
        "luxation congénitale",
        "lubrifie mal",
        "synovie fluide",
        "coin de fibrocartilage",
        "c'est ce qui les rend particulièrement mobiles",
        "pas des structures de protection",
        "d'où l'intérêt de l'échauffement",
    ):
        assert expression not in texte, expression


def test_les_cinq_categories_et_les_trois_familles_ont_leur_carte():
    cartes = {c["id"]: c for c in CHAPITRE_3["cartes"]}
    texte_categories = " ".join(c["r"].lower() for c in CHAPITRE_3["cartes"] if "catégories" in c["q"])
    for categorie in ("protection", "amortissement des pressions", "adaptation des surfaces", "maintien", "glissement"):
        assert categorie in texte_categories, categorie
    comparaison = next(c for c in CHAPITRE_3["cartes"] if c["q"].startswith("Compare les trois familles"))
    for terme in ("synarthroses", "amphiarthroses", "diarthroses", "mobilité", "cartilage", "cavité", "exemple"):
        assert terme in (comparaison["q"] + " " + comparaison["r"]).lower(), terme
    # Le cours range deux structures dans deux categories chacune : c'est dit quelque part.
    doubles = " ".join(c["r"].lower() for c in CHAPITRE_3["cartes"] if "deux catégories" in c["q"])
    assert "cartilage articulaire" in doubles and "synovie" in doubles and "membrane fibreuse" in doubles
    assert set(cartes) >= {"c3-28", "c3-29", "c3-30", "c3-31", "c3-32"}


# Ni le cours ni aucune source ne dit quelle confusion est la plus courante chez les eleves :
# une affirmation de frequence donne au site une autorite qu'il n'a pas. « On inverse
# facilement » ou « confusion classique » decrivent un risque sans pretendre le mesurer.
FORMULES_DE_FREQUENCE = ("fréquen", "le plus souvent", "la plupart", "généralement")


def test_aucune_affirmation_de_frequence_n_est_laissee_au_chapitre_3():
    prose = _prose(CHAPITRE_3).lower()
    for formule in FORMULES_DE_FREQUENCE:
        assert formule not in prose, formule
