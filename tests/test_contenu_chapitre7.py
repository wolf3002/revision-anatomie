import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_7 = next(c for c in COURS["chapitres"] if c["num"] == 7)


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_7_couvre_le_volume_cible():
    assert 20 <= len(CHAPITRE_7["cartes"]) <= 25
    assert 10 <= len(CHAPITRE_7["quiz"]) <= 12
    assert 3 <= len(CHAPITRE_7["pieges"]) <= 4
    # Cinq depuis la decoupe du squelette du membre inferieur en deux planches
    # (bassin-hanche-genou / jambe-cheville) : deux libelles de 100 et 170 unites
    # de part et d'autre du genou ne tenaient pas dans 300 unites de large.
    assert 2 <= len(CHAPITRE_7["planches"]) <= 5


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
        assert all(debut <= s <= fin for s in slides_de(muscle)), muscle["nom"]


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
        assert all(debut <= s <= fin for s in slides_de(entree)), entree.get("id", entree.get("titre"))


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
        "squelette-membre-inferieur-jambe-cheville",
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
    # « franchit » n'est plus exige : le cours n'enonce jamais ce principe (audit exhaustif du
    # 2026-09-30). Les pieges du quadriceps et du triceps sural portent desormais le fait
    # du cours (quel chef, quel muscle est AUSSI fléchisseur), pas la deduction.
    for notion in (
        "droit fémoral",
        "fléchisseur de la cuisse",
        "fléchisseur de la jambe",
        "ischio-jambiers",
        "tête de la fibula",
        "patte d'oie",
        "plateau tibial",
        "gastrocnémien",
        "soléaire",
    ):
        assert notion in texte, f"piege attendu absent : {notion}"


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------
def _prose(chapitre):
    """Texte lisible du chapitre, hors trace SVG."""
    donnees = {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
    donnees["pastilles"] = [p["pastilles"] for p in chapitre["planches"]]
    return json.dumps(donnees, ensure_ascii=False)


def _section(slide):
    return next(s for s in CHAPITRE_7["sections"] if slides_de(s)[0] == slide)


def _carte(identifiant):
    return next(c for c in CHAPITRE_7["cartes"] if c["id"] == identifiant)


def _question(identifiant):
    return next(q for q in CHAPITRE_7["quiz"] if q["id"] == identifiant)


def _piege(debut):
    return next(p for p in CHAPITRE_7["pieges"] if p["titre"].startswith(debut))


def _planche(identifiant):
    return next(p for p in CHAPITRE_7["planches"] if p["id"] == identifiant)


def test_c7_06_seul_l_acetabulum_est_a_la_jonction_des_trois_parties():
    # Slide 278 : les 3 parties colorees se rejoignent dans l'acetabulum ; le foramen
    # obturé n'est borde que par l'ischium et le pubis.
    reponse = _carte("c7-06")["r"]
    assert "L'acétabulum et le foramen obturé sont" not in reponse
    assert "acétabulum" in reponse and "à la jonction des 3 parties" in reponse
    assert "n'est bordé que par l'ischium et le pubis" in reponse
    assert slides_de(_carte("c7-06")) == [278, 279]


def test_les_ischio_jambiers_ne_partagent_ni_la_meme_origine_ni_les_memes_actions():
    # Le chef court du biceps naît de la ligne apre (slide 319) ; seul son chef long
    # étend la cuisse.
    prose = _prose(CHAPITRE_7)
    for expression in (
        "partagent la même origine",
        "partagent origine et actions",
        "même origine et les mêmes actions",
        "origine commune",
        "Tous les 3 s'originent",
    ):
        assert expression not in prose, expression
    piege = _piege("Les ischio-jambiers")["texte"]
    assert "semi-tendineux et le semi-membraneux naissent de la tubérosité ischiatique" in piege
    assert "un seul y naît" in piege and "ligne âpre" in piege
    assert "réserve cette action au chef long" in piege
    for texte in (_carte("c7-22")["r"], _question("q7-03")["expl"]):
        assert "un seul" in texte and "chef long" in texte
    # La planche ne dit plus « origine commune » non plus.
    planche = _planche("ischio-jambiers-trois-terminaisons")
    assert "origine commune" not in planche["titre"]
    assert "chef long" in planche["pastilles"][0]["indice"]


def test_la_hanche_n_est_plus_attribuee_a_la_ceinture_pelvienne():
    # Slide 275 : la ceinture pelvienne compte 4 articulations, sans la coxo-fémorale.
    reponse = _carte("c7-02")["r"]
    assert "Ceinture pelvienne : sacrum + os coxal ; articulations sacro-iliaque et coxo-fémorale" not in reponse
    assert "en aval de la cheville" not in _prose(CHAPITRE_7)
    assert "slide 275" in reponse
    assert "pas comptée parmi les 4 articulations de la ceinture pelvienne" in reponse
    point = _section(271)["points"][0]
    assert "et articulation coxo-fémorale (hanche)" not in point
    assert "ne fait pas partie des 4 articulations de la ceinture pelvienne (slide 275)" in point
    # ... et la question du même chapitre reste d'accord.
    assert "n'appartient PAS à la ceinture pelvienne" in _question("q7-06")["expl"]


def test_le_cours_n_enonce_jamais_le_principe_franchit_et_le_sens_vient_de_la_slide():
    # Aucune entree sourcee ne deduit le sens d'une action de « franchit ». Le principe
    # dit « peut agir sur », jamais « dans quel sens » : le sens est celui de la slide.
    prose = _prose(CHAPITRE_7).lower()
    assert "franchi" not in prose
    for identifiant, texte, action in (
        ("q7-01", _question("q7-01")["expl"], "la flexion de la cuisse"),
        ("q7-05", _question("q7-05")["expl"], "la flexion de la jambe"),
        ("c7-25", _carte("c7-25")["r"], "la flexion de la jambe"),
    ):
        assert "le cours lui donne" in texte, identifiant
        assert action in texte, identifiant
        assert "donc il la fléchit" not in texte and "donc il le fléchit" not in texte, identifiant
    assert "il agit donc aussi sur la cuisse" in _question("q7-01")["expl"]
    assert "il agit donc aussi sur le genou" in _carte("c7-25")["r"]


def test_les_quatre_entrees_a_principe_valide_sont_reformulees_avec_les_mots_du_cours():
    # c7-20, c7-22, pieges du quadriceps et du triceps sural : plus de « pourquoi »
    # ni de « ne franchit que ». Le fait est donne tel que le cours l'ecrit.
    assert not _carte("c7-20")["q"].startswith("Pourquoi")
    assert "le cours lui donne" in _carte("c7-20")["r"]
    quadriceps = _piege("Le quadriceps")
    assert "franchit" not in quadriceps["titre"]
    assert "le cours ne leur donne que l'extension du genou" in quadriceps["texte"]
    sural = _piege("Triceps sural")
    assert "franchit" not in sural["titre"]
    assert "le cours ne lui donne que la flexion plantaire du pied" in sural["texte"]
    for entree in (quadriceps, sural):
        assert "hors_cours" not in entree and slides_de(entree)


def test_q7_05_pose_une_question_d_origine_a_une_seule_bonne_reponse():
    question = _question("q7-05")
    assert not question["q"].startswith("Pourquoi")
    assert question["choix"][question["bonne"]] == (
        "le gastrocnémien s'origine sur le fémur, le soléaire sur le tibia et la fibula"
    )
    assert len(set(question["choix"])) == 4


def test_les_renvois_du_chapitre_7_citent_toutes_les_slides_qui_portent_leur_contenu():
    attendus_cartes = {
        "c7-03": [273, 275],
        "c7-07": [282, 284],
        "c7-08": [288, 289],
        "c7-11": [294, 295],
        "c7-14": [300, 301],
        "c7-19": [310, 311],
        "c7-21": [312, 313, 314, 315],
        "c7-22": [319, 320],
        "c7-23": [309, 316, 320],
        "c7-24": [324, 325],
        "c7-25": [327, 328],
    }
    for identifiant, slides in attendus_cartes.items():
        assert slides_de(_carte(identifiant)) == slides, identifiant
    attendus_questions = {
        "q7-02": [319, 320],  # la terminaison du biceps est en 319, celles des semi- en 320
        "q7-03": [319, 320],
        "q7-04": [309, 316, 320],
        "q7-12": [277, 282],
    }
    for identifiant, slides in attendus_questions.items():
        assert slides_de(_question(identifiant)) == slides, identifiant
    assert slides_de(_piege("Les ischio-jambiers")) == [319, 320]
    assert slides_de(_piege("La patte d'oie")) == [309, 316, 320]
    assert slides_de(_planche("ischio-jambiers-trois-terminaisons")) == [319, 320]
    # Les pastilles n'ont pas de slide propre : le libelle est sur la slide de la planche.
    # « Tibio-fibulaire proximale » n'est ecrit qu'en 288 et 289 (pas en 271) ; « Acétabulum »
    # n'est legende qu'en 279 (pas en 277).
    assert slides_de(_planche("squelette-membre-inferieur-jambe-cheville")) == [289]
    assert slides_de(_planche("os-coxal-trois-parties")) == [277, 279]


def test_la_patte_d_oie_dit_que_le_cours_ne_reunit_jamais_ses_trois_muscles():
    texte = _piege("La patte d'oie")["texte"]
    assert "sur une même slide" in texte
    for muscle_et_slide in ("sartorius à la slide 309", "gracile à la 316", "semi-tendineux à la 320"):
        assert muscle_et_slide in texte


def test_les_qualificatifs_non_sources_sont_retires_du_chapitre_7():
    # « superficiel » / « profond » pour la patte d'oie et le plateau tibial, « (pas
    # rotateur) », « profond, caché sous le droit fémoral », « le piège le plus fréquent ».
    prose = _prose(CHAPITRE_7).lower()
    for expression in (
        "médial, superficiel",
        "médial, profond",
        "médiale superficielle",
        "médiale profonde",
        "plus profondément",
        "pas rotateur",
        "caché sous le droit fémoral",
        "le piège le plus fréquent",
        "voisin du semi-tendineux",
    ):
        assert expression not in prose, expression
    assert "profond" not in json.dumps(CHAPITRE_7["pieges"], ensure_ascii=False)
    assert "superficiel" not in json.dumps(CHAPITRE_7["pieges"], ensure_ascii=False)


def test_les_dix_sept_tables_musculaires_du_chapitre_7_sont_intactes():
    # 68 controles sans defaut a l'audit : les renvois des tables ne bougent pas non plus.
    muscles = {m["nom"]: m for m in CHAPITRE_7["muscles"]}
    assert len(muscles) == 17
    assert muscles["Biceps fémoral"]["origine"] == [
        "chef long : tubérosité ischiatique",
        "chef court : ligne âpre du fémur",
    ]
    assert muscles["Biceps fémoral"]["terminaison"] == ["tête de la fibula"]
    assert muscles["Semi-tendineux"]["terminaison"] == ["patte d'oie"]
    assert muscles["Semi-membraneux"]["terminaison"] == ["plateau tibial"]
    assert muscles["Gastrocnémien"]["actions"] == ["fléchisseur de la jambe", "fléchisseur plantaire du pied"]
    assert muscles["Soléaire"]["actions"] == ["fléchisseur plantaire du pied"]
    assert all(isinstance(m["slide"], int) for m in CHAPITRE_7["muscles"])


def test_q7_08_n_a_plus_de_distracteur_qui_s_elimine_par_addition():
    # 7 + 5 + 15 = 27 pour un pied de 26 os : l'option se refutait sans le cours. Les
    # quatre options totalisent 26, la question se joue sur la repartition.
    question = _question("q7-08")
    for option in question["choix"]:
        chiffres = [int(mot) for mot in option.split() if mot.isdigit()]
        assert sum(chiffres) == 26, option
    assert question["choix"][question["bonne"]] == "7 tarsiens, 5 métatarsiens, 14 phalanges"
