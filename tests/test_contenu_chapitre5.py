import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_5 = next(c for c in COURS["chapitres"] if c["num"] == 5)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_5_couvre_le_volume_cible():
    assert 18 <= len(CHAPITRE_5["cartes"]) <= 25
    assert 8 <= len(CHAPITRE_5["quiz"]) <= 12
    assert 2 <= len(CHAPITRE_5["pieges"]) <= 5
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
        assert all(debut <= s <= fin for s in slides_de(muscle)), muscle["nom"]


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
        assert all(debut <= s <= fin for s in slides_de(entree)), entree.get("id", entree.get("titre"))


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


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------
def _prose(chapitre):
    """Texte lisible du chapitre, hors trace SVG."""
    donnees = {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
    donnees["pastilles"] = [p["pastilles"] for p in chapitre["planches"]]
    return json.dumps(donnees, ensure_ascii=False)


def _section(slide):
    return next(s for s in CHAPITRE_5["sections"] if slides_de(s)[0] == slide)


def _carte(identifiant):
    return next(c for c in CHAPITRE_5["cartes"] if c["id"] == identifiant)


def _question(identifiant):
    return next(q for q in CHAPITRE_5["quiz"] if q["id"] == identifiant)


def _piege(debut):
    return next(p for p in CHAPITRE_5["pieges"] if p["titre"].startswith(debut))


def _planche(identifiant):
    return next(p for p in CHAPITRE_5["planches"] if p["id"] == identifiant)


def test_q5_08_ne_compte_plus_d_interlignes_et_n_a_plus_de_distracteur_juste():
    # Entre l'atlas et l'axis, il n'y a pas non plus de disque : ce distracteur etait
    # anatomiquement correct, et piegeait quelqu'un qui connait l'anatomie.
    q = _question("q5-08")
    assert "l'atlas et l'axis" not in q["choix"]
    assert "C7 et T1" in q["choix"]
    assert q["choix"][q["bonne"]] == "l'occiput et l'atlas"
    assert "interligne" not in q["expl"]
    assert "24" not in q["expl"]
    assert "23" in q["expl"] and "sauf entre l'occiput et l'atlas" in q["expl"]


def test_le_piege_des_disques_ne_dit_plus_le_seul_niveau():
    piege = _piege("Il n'y a pas de disque intervertébral")
    assert "seul niveau" not in piege["texte"]
    assert "interligne" not in json.dumps(piege, ensure_ascii=False)
    assert "occiput" in piege["texte"]


def test_le_piege_de_l_ilio_psoas_n_affirme_plus_que_terminaison_et_action_sont_du_psoas():
    # Slide 180 : terminaison et action sont celles de l'ilio-psoas entier. Seule
    # l'origine listee est celle du grand psoas ; l'origine de l'iliaque n'est pas donnee.
    piege = _piege("L'ilio-psoas")
    texte = piege["texte"]
    assert "concernent spécifiquement" not in texte
    assert "pas le faisceau iliaque" not in texte
    assert "grand psoas seul" in texte
    assert "ne donne pas d'origine pour l'iliaque" in texte
    assert "dans son ensemble" in texte
    assert slides_de(piege) == [180]
    assert "(grand psoas)" not in " ".join(_section(180)["points"])


def test_les_renvois_du_chapitre_5_citent_les_slides_qui_portent_leur_contenu():
    # Corps vertebral et canal rachidien sont nommes en 145 ; les orientations de fibres
    # des quatre muscles en 185, 186, 187 et 188. Le champ d'une planche est unique :
    # une liste au niveau de la planche.
    assert slides_de(_planche("vertebre-vue-superieure")) == [145, 147]
    assert slides_de(_planche("fibres-abdominales-orientation")) == [185, 186, 187, 188]
    assert slides_de(_section(184)) == [184, 185]
    assert slides_de(_carte("c5-22")) == [186, 187]
    assert slides_de(_piege("L'oblique interne")) == [186, 187]


def test_la_table_musculaire_du_chapitre_5_est_intacte():
    # 18 colonnes sur 18 exactes a l'audit : ni renvoi ni texte ne bougent.
    muscles = {m["nom"]: m for m in CHAPITRE_5["muscles"]}
    assert muscles["Ilio-psoas"]["origine"] == [
        "processus transverses de L1 à L5",
        "corps vertébraux de T12 à L5",
    ]
    assert muscles["Ilio-psoas"]["terminaison"] == ["petit trochanter du fémur"]
    assert muscles["Ilio-psoas"]["actions"] == ["fléchisseur de la cuisse"]
    assert all(isinstance(m["slide"], int) for m in CHAPITRE_5["muscles"])


def test_la_nomenclature_usuelle_des_cotes_est_signalee_hors_cours():
    # Le cours ecrit « vraies cotes 1 a 10 » (slides 161 et 162) ; on ne le corrige pas.
    # L'ecart avec la nomenclature usuelle est dit, dans une entree marquee hors cours.
    piege = _piege("La nomenclature usuelle des côtes")
    assert piege["hors_cours"] is True
    assert "côtes 1 à 7" in piege["texte"] and "côtes 8 à 10" in piege["texte"]
    assert "vraies côtes 1 à 10" in piege["texte"]
    sourcé = _piege("Le cours ne distingue que 2 catégories")
    assert "hors_cours" not in sourcé
    assert "1 à 10" in sourcé["texte"]
    assert "parfois enseignée ailleurs" not in json.dumps(CHAPITRE_5["pieges"], ensure_ascii=False)
    # Le cours reste reproduit tel quel : la carte et la question ne sont pas « corrigees ».
    assert "1 à 10" in _carte("c5-15")["q"]
    assert _question("q5-09")["choix"][_question("q5-09")["bonne"]] == "les côtes 11 et 12"


def test_la_somme_de_24_est_donnee_avec_sa_source():
    # Le total est ecrit a la slide 58 (chapitre 2), pas sur la slide 139.
    for texte in (
        " ".join(_section(139)["points"]),
        _carte("c5-01")["r"],
        _question("q5-01")["expl"],
    ):
        assert "slide 58" in texte


def test_les_causalites_et_superlatifs_non_sources_sont_retires_du_chapitre_5():
    texte = _prose(CHAPITRE_5).lower()
    for expression in (
        "24 interlignes",
        "convexité",
        "2 supérieurs",
        "sous l'oblique externe",
        "le plus superficiel",
        "la confusion la plus fréquente",
        "inverse le sens de rotation",
        "à cause de l'orientation",
        "parfois enseignée ailleurs",
        "isolées",
        "spécifiquement le grand psoas",
    ):
        assert expression not in texte, expression
