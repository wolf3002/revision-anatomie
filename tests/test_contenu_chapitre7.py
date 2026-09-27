import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_7 = next(c for c in COURS["chapitres"] if c["num"] == 7)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_7_couvre_le_volume_cible():
    assert 20 <= len(CHAPITRE_7["cartes"]) <= 25
    assert 10 <= len(CHAPITRE_7["quiz"]) <= 12
    assert 3 <= len(CHAPITRE_7["pieges"]) <= 4
    assert 2 <= len(CHAPITRE_7["planches"]) <= 4


def test_les_bornes_de_slides_sont_celles_relevees():
    # Relevees slide par slide dans le PDF (pdftotext -f 268 -l 328 -layout).
    # 268 est la premiere slide de sommaire du chapitre 7, 328 sa derniere
    # slide (gastrocnemien et soleaire) : c'est la fin du document (328 pages
    # au total, meta.slides le confirme).
    # Huit slides sans texte extractible (280, 285, 292, 297, 307, 317, 321,
    # 322) ont ete rendues en PNG (pdftoppm) et lues a l'oeil : 280, 285, 292,
    # 317, 321, 322 sont des cartons de credit source ou de titre de
    # sous-section sans information propre ; 297 et 307 sont des planches
    # illustrees (vues postero-laterale et anterieure du membre inferieur)
    # qui ne font que nommer des muscles deja donnes en detail sur leur slide
    # dediee, sans origine/terminaison/action nouvelle.
    assert CHAPITRE_7["slides"] == [268, 328]


def test_la_table_musculaire_a_les_dix_sept_muscles_documentes():
    # Le cours documente individuellement (origine + terminaison + action)
    # dix-sept muscles de ce chapitre (le quadriceps regroupe ses 4 chefs
    # sous une seule entree, comme le triceps brachial et le deltoide au
    # chapitre 6). D'autres sont cites en liste sans detail : pectine,
    # piriforme, obturateur interne/externe, jumeau superieur/inferieur,
    # carre femoral, plantaire, poplite, tibial posterieur, long flechisseur
    # des orteils/de l'hallux, long extenseur des orteils/de l'hallux, court/
    # long/troisieme fibulaire -- verifie par lecture de toutes les slides de
    # myologie (298 a 328), aucune ne leur donne une origine ET une
    # terminaison.
    noms = {m["nom"] for m in CHAPITRE_7["muscles"]}
    assert noms == {
        "Ilio-psoas",
        "Petit glutéal",
        "Moyen glutéal",
        "Grand glutéal",
        "Tenseur du fascia lata",
        "Sartorius",
        "Quadriceps fémoral",
        "Court adducteur",
        "Long adducteur",
        "Grand adducteur",
        "Gracile",
        "Biceps fémoral",
        "Semi-tendineux",
        "Semi-membraneux",
        "Tibial antérieur",
        "Gastrocnémien",
        "Soléaire",
    }
    assert "Pectiné" not in noms
    assert "Piriforme" not in noms


def test_chaque_muscle_a_ses_trois_colonnes_non_vides_et_sa_slide():
    debut, fin = CHAPITRE_7["slides"]
    for muscle in CHAPITRE_7["muscles"]:
        assert muscle["origine"], muscle["nom"]
        assert muscle["terminaison"], muscle["nom"]
        assert muscle["actions"], muscle["nom"]
        assert debut <= muscle["slide"] <= fin, muscle["nom"]


def test_les_slides_des_muscles_sont_celles_relevees_dans_le_pdf():
    # Relevees une par une : semi-tendineux et semi-membraneux partagent la
    # meme slide (320, qui donne les deux muscles cote a cote) ; gastrocnemien
    # et soleaire partagent la slide 328 pour la meme raison. Le quadriceps
    # est attribue a la slide 311, celle qui donne l'origine de chaque chef,
    # la terminaison commune et les actions (la slide 310 ne fait que nommer
    # les 4 chefs, sans origine/terminaison/action).
    attendues = {
        "Ilio-psoas": 299,
        "Petit glutéal": 300,
        "Moyen glutéal": 301,
        "Grand glutéal": 302,
        "Tenseur du fascia lata": 303,
        "Sartorius": 309,
        "Quadriceps fémoral": 311,
        "Court adducteur": 313,
        "Long adducteur": 314,
        "Grand adducteur": 315,
        "Gracile": 316,
        "Biceps fémoral": 319,
        "Semi-tendineux": 320,
        "Semi-membraneux": 320,
        "Tibial antérieur": 325,
        "Gastrocnémien": 328,
        "Soléaire": 328,
    }
    for muscle in CHAPITRE_7["muscles"]:
        assert muscle["slide"] == attendues[muscle["nom"]], muscle["nom"]


def test_les_identifiants_de_cartes_sont_contigus():
    ids = [c["id"] for c in CHAPITRE_7["cartes"]]
    attendus = [f"c7-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_les_identifiants_de_quiz_sont_contigus():
    ids = [q["id"] for q in CHAPITRE_7["quiz"]]
    attendus = [f"q7-{i:02d}" for i in range(1, len(ids) + 1)]
    assert ids == attendus


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_7["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_chaque_question_a_au_moins_trois_choix():
    for question in CHAPITRE_7["quiz"]:
        assert len(question["choix"]) >= 3, question["id"]


def test_toutes_les_slides_sont_dans_la_plage_du_chapitre():
    debut, fin = CHAPITRE_7["slides"]
    entrees = (
        CHAPITRE_7["sections"]
        + CHAPITRE_7["cartes"]
        + CHAPITRE_7["quiz"]
        + CHAPITRE_7["pieges"]
        + CHAPITRE_7["planches"]
    )
    for entree in entrees:
        assert debut <= entree["slide"] <= fin, entree.get("id", entree.get("titre"))


def test_aucune_planche_ne_contient_une_etiquette_dans_son_trace():
    for planche in CHAPITRE_7["planches"]:
        assert "<text" not in planche["dessin"], planche["id"]


def test_les_planches_attendues_du_chapitre_7_existent():
    # Suggerees par le plan (squelette du membre + articulations, os coxal et
    # ses 3 parties, quadriceps et ses 4 chefs, ischio-jambiers et leurs 3
    # terminaisons distinctes) et confirmees par le contenu reel.
    assert {
        "squelette-membre-inferieur-articulations",
        "os-coxal-trois-parties",
        "quadriceps-quatre-chefs",
        "ischio-jambiers-trois-terminaisons",
    } <= {p["id"] for p in CHAPITRE_7["planches"]}


def test_les_libelles_sont_uniques_dans_chaque_planche():
    for planche in CHAPITRE_7["planches"]:
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), planche["id"]


def test_aucune_planche_ne_deborde_de_320_unites_de_large():
    for planche in CHAPITRE_7["planches"]:
        _, _, largeur, _ = (float(v) for v in planche["vb"].split())
        assert largeur <= 320, planche["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_7, ensure_ascii=False).lower()
    for notion in (
        "ceinture pelvienne",
        "os coxal",
        "ilium",
        "ischium",
        "pubis",
        "sacrum",
        "coccyx",
        "symphyse pubienne",
        "sacro-iliaque",
        "sacro-coccygienne",
        "acétabulum",
        "coxo-fémorale",
        "fémur",
        "tibio-fémorale",
        "fémoro-patellaire",
        "patella",
        "tibia",
        "fibula",
        "talo-crurale",
        "entorses",
        "26 os",
        "tarse",
        "métatarse",
        "phalanges",
        "ilio-psoas",
        "glutéal",
        "tenseur du fascia lata",
        "sartorius",
        "patte d'oie",
        "quadriceps",
        "droit fémoral",
        "vaste médial",
        "vaste latéral",
        "vaste intermédiaire",
        "ligament patellaire",
        "adducteur",
        "gracile",
        "ischio-jambiers",
        "biceps fémoral",
        "semi-tendineux",
        "semi-membraneux",
        "tête de la fibula",
        "plateau tibial",
        "tibial antérieur",
        "triceps sural",
        "gastrocnémien",
        "soléaire",
        "calcanéus",
        "ligne âpre",
        "tubérosité ischiatique",
        "ligament croisé",
        "ménisque",
    ):
        assert notion in texte, f"notion absente du chapitre 7 : {notion}"


def test_les_pieges_couvrent_les_confusions_signalees_par_le_plan():
    texte = json.dumps(CHAPITRE_7["pieges"], ensure_ascii=False).lower()
    for notion in (
        "droit fémoral",
        "franchit",
        "ischio-jambiers",
        "tête de la fibula",
        "patte d'oie",
        "plateau tibial",
        "gastrocnémien",
        "soléaire",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"
