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
    assert 18 <= len(CHAPITRE_4["cartes"]) <= 30
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


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------
def _prose(chapitre):
    """Texte lisible du chapitre, hors trace SVG."""
    donnees = {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
    donnees["pastilles"] = [p["pastilles"] for p in chapitre["planches"]]
    return json.dumps(donnees, ensure_ascii=False)


def _section(slide):
    return next(s for s in CHAPITRE_4["sections"] if slides_de(s)[0] == slide)


def _carte(identifiant):
    return next(c for c in CHAPITRE_4["cartes"] if c["id"] == identifiant)


def _question(identifiant):
    return next(q for q in CHAPITRE_4["quiz"] if q["id"] == identifiant)


def _piege(debut):
    return next(p for p in CHAPITRE_4["pieges"] if p["titre"].startswith(debut))


def test_la_section_de_la_slide_119_cite_la_phrase_du_cours_mot_pour_mot():
    # Slide 119 : « La cellule musculaire s'appelle myofibrille. » Fausse en anatomie, et
    # contredite par les slides 117 et 120. Le site ne la reecrit plus en silence : il la
    # cite, dit que le cours se contredit, et donne la version juste.
    section = _section(119)
    texte = " ".join(section["points"])
    assert "La cellule musculaire s'appelle myofibrille." in texte
    assert "se contredit" in texte
    assert "117" in texte and "120" in texte
    assert "la cellule musculaire est la fibre musculaire (le myocyte)" in texte
    assert "fausse en anatomie" in texte


def test_le_piege_de_la_myofibrille_expose_les_trois_slides():
    piege = _piege("Le cours se contredit")
    assert slides_de(piege) == [117, 119, 120]
    texte = piege["texte"]
    assert "Slide 119" in texte and "Slide 117" in texte and "Slide 120" in texte
    assert "La cellule musculaire s'appelle myofibrille." in texte
    assert "Myocyte (fibre musculaire)" in texte
    assert "fausse en anatomie" in texte
    assert "sarcoplasme" in texte and "noyau" in texte
    # Ne tranche pas a la place du cours : les deux formulations, chacune avec sa slide.
    assert "ne pas supposer laquelle" in texte


def test_une_carte_pose_la_contradiction_des_slides_117_119_120():
    carte = _carte("c4-26")
    assert slides_de(carte) == [117, 119, 120]
    assert "La cellule musculaire s'appelle myofibrille." in carte["r"]
    assert "se contredit" in carte["r"]


def test_les_renvois_incomplets_du_chapitre_4_citent_toutes_leurs_slides():
    assert slides_de(_section(123)) == [123, 124]
    assert slides_de(_question("q4-03")) == [117, 120]
    assert slides_de(_question("q4-11")) == [127, 128]
    assert slides_de(_piege("Excitabilité et contractilité")) == [123, 126]


def test_la_secousse_musculaire_cite_son_graphique_slide_128():
    # « le plus long des trois » n'est lisible que sur le graphique : la latence n'est
    # comparee au relachement nulle part dans le texte de la slide 127.
    assert slides_de(_section(127)) == [127, 128]
    assert 128 in slides_de(_carte("c4-29"))
    assert "plus long des trois" in _question("q4-11")["expl"]
    assert "slide 128" in _question("q4-11")["expl"]


def test_les_legendes_des_slides_117_et_120_sont_couvertes():
    # Strie A, strie I, zone claire, sarcoplasme et noyau sont ecrits dans les schemas.
    texte = _prose(CHAPITRE_4).lower()
    for legende in ("strie a", "strie i", "zone claire", "sarcoplasme", "noyau", "ligne z"):
        assert legende in texte, legende
    assert 120 in slides_de(_carte("c4-27"))
    assert 117 in slides_de(_carte("c4-28"))


def test_aucun_ajout_non_source_dans_le_chapitre_4():
    texte = _prose(CHAPITRE_4).lower()
    for expression in (
        "conjonctif",
        "conjonctive",
        "recrutement",
        "chefs charnus",
        "chef charnu",
        "tendon commun",
        "tendon central",
        "plusieurs ventres en série",
        "languettes",
        "propre à la fibre",
        "propre de la fibre",
        "se détacher",
        "à chaque cycle",
    ):
        assert expression not in texte, expression


def test_les_formes_musculaires_sont_donnees_comme_lecture_du_dessin():
    # La slide 115 n'a que des noms : ni definition, ni nombre de chefs.
    section = _section(115)
    texte = " ".join(section["points"])
    assert "sans aucun texte" in texte
    assert "Lecture du dessin" in texte
    assert "dessin" in _carte("c4-08")["r"]


def test_le_role_du_calcium_et_de_l_atp_est_marque_hors_cours():
    # La slide 121 n'a que des legendes ; le role est une lecture usuelle du schema.
    assert _carte("c4-16").get("hors_cours") is True
    assert "hors_cours" not in _carte("c4-15")
    assert "Lecture usuelle" in " ".join(_section(121)["points"])
