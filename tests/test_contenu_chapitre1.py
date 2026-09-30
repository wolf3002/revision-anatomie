import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_1 = COURS["chapitres"][0]


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_1_couvre_le_volume_cible():
    assert len(CHAPITRE_1["cartes"]) >= 18
    assert len(CHAPITRE_1["quiz"]) >= 8
    assert len(CHAPITRE_1["pieges"]) >= 2


def test_chaque_mouvement_porte_son_plan():
    plans = {"frontal", "sagittal", "transversal"}
    mouvements = [c for c in CHAPITRE_1["cartes"] if c.get("plan")]
    assert mouvements, "aucune carte de mouvement n'est rattachee a un plan"
    assert all(c["plan"] in plans for c in mouvements)


def test_les_trois_plans_sont_tous_representes():
    plans = {c["plan"] for c in CHAPITRE_1["cartes"] if c.get("plan")}
    assert plans == {"frontal", "sagittal", "transversal"}


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_1["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_1, ensure_ascii=False).lower()
    for notion in (
        "position anatomique",
        "abduction",
        "adduction",
        "flexion",
        "extension",
        "pronation",
        "supination",
        "circumduction",
        "proximal",
        "distal",
        "médial",
        "latéral",
        "crânial",
        "caudal",
    ):
        assert notion in texte, f"notion absente du chapitre 1 : {notion}"


# --- Corrections de l'audit de verification exhaustive (2026-09-30) ---------------------
import math
import re


def _planche(planche_id):
    return next(p for p in CHAPITRE_1["planches"] if p["id"] == planche_id)


def _extremites_des_fleches(dessin):
    """(depart, arrivee) de chaque trace portant une pointe de fleche."""
    resultat = []
    for d in re.findall(r"<path d='([^']+)'[^>]*marker-end", dessin):
        nombres = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
        resultat.append(((nombres[0], nombres[1]), (nombres[-2], nombres[-1])))
    return resultat


MOUVEMENT_FLECHE = {
    "plan-frontal": ("Abduction", 18),
    "plan-sagittal": ("Flexion", 23),
    "plan-transversal": ("Rotation", 31),
}


def test_la_pastille_mouvement_demande_un_seul_mouvement_et_accepte_celui_qu_on_demande():
    # verifierPastille compare par egalite exacte : demander « les mouvements de ce plan »
    # (trois au frontal, quatre couples au sagittal) et n'accepter qu'une liste de deux
    # termes notait fausse une reponse complete. La pastille designe le mouvement fleche
    # et n'attend que son nom.
    for planche_id, (attendu, _) in MOUVEMENT_FLECHE.items():
        pastille = _planche(planche_id)["pastilles"][1]
        assert pastille["t"] == attendu, planche_id
        assert "," not in pastille["t"], planche_id
        assert "fléché" in pastille["indice"], planche_id


def test_la_pastille_mouvement_est_posee_contre_sa_fleche():
    # Elle etait a ~200 unites de la fleche, sous les pieds du personnage.
    for planche_id in MOUVEMENT_FLECHE:
        planche = _planche(planche_id)
        pastille = planche["pastilles"][1]
        distance = min(
            math.dist((pastille["x"], pastille["y"]), point)
            for extremites in _extremites_des_fleches(planche["dessin"])
            for point in extremites
        )
        assert distance <= 50, (planche_id, distance)


def test_les_pastilles_mouvement_citent_les_slides_des_mouvements():
    # La slide 15 ne porte que les NOMS des plans ; les mouvements sont en 18, 23 et 31.
    for planche_id, (_, slide_mouvements) in MOUVEMENT_FLECHE.items():
        assert slides_de(_planche(planche_id)) == [15, slide_mouvements], planche_id


def test_la_fleche_caudale_ne_longe_pas_la_jambe():
    # Le cours : « extremite inferieure DU TRONC ». Le tronc de la silhouette va de
    # y = 74 a y = 196 ; les jambes commencent en y = 196. Une fleche caudale qui
    # finit plus bas occupe la region de « distal » (indiscernables en mode muet).
    planche = _planche("termes-localisation")
    fleches = _extremites_des_fleches(planche["dessin"])
    # Les deux fleches verticales situees a gauche du tronc (x < 160).
    verticales = [
        (a, b) for a, b in fleches if a[0] == b[0] and a[0] < 160
    ]
    cranial = [f for f in verticales if f[1][1] < f[0][1]]
    caudal = [f for f in verticales if f[1][1] > f[0][1]]
    assert len(cranial) == 1 and len(caudal) == 1
    assert 74 <= cranial[0][1][1] <= 120 and 74 <= cranial[0][0][1] <= 130
    assert 140 <= caudal[0][0][1] and caudal[0][1][1] <= 200


def test_aucun_ajout_non_source_dans_le_chapitre_1():
    # Ajouts releves par l'audit : absents du cours, ils enseignaient des choses
    # que le support ne dit pas ou creaient une contradiction avec un QCM.
    texte = json.dumps(CHAPITRE_1, ensure_ascii=False)
    for expression in (
        "Vitruve",
        "la plus fréquente",
        "faute de vocabulaire",
        "coûtent des points",
        "-pulsion pour l'épaule",
        "désigne le mouvement vers la plante",
        "disent « vers le haut » et « vers le bas »",
    ):
        assert expression not in texte, expression


def test_le_distracteur_de_q1_04_ne_nie_pas_la_figure_de_la_slide_13():
    # La figure de la slide 13 legende « abduction / adduction » autour de l'axe de M2 :
    # « axe de la main ou du pied » ne peut plus etre corrige comme faux.
    question = next(q for q in CHAPITRE_1["quiz"] if q["id"] == "q1-04")
    assert not any("axe de la main" in c for c in question["choix"])
    assert 13 in slides_de(question) and 19 in slides_de(question)
    assert question["q"].startswith("Pour un membre")


def test_q1_09_ne_corrige_pas_comme_faux_ce_que_le_cours_autorise():
    # Slide 38 : « on utilise egalement superieur et inferieur ». « Superieure » reste un
    # distracteur, mais l'enonce doit poser le couple que le cours associe aux membres.
    question = next(q for q in CHAPITRE_1["quiz"] if q["id"] == "q1-09")
    assert "associe aux membres" in question["q"]
    assert slides_de(question) == [38, 39]


def _prose(chapitre):
    """Texte lisible du chapitre, hors trace SVG."""
    donnees = {cle: chapitre[cle] for cle in ("sections", "cartes", "quiz", "pieges")}
    donnees["pastilles"] = [p["pastilles"] for p in chapitre["planches"]]
    return json.dumps(donnees, ensure_ascii=False).lower()


# Ni le cours ni aucune source ne dit quelle confusion est la plus courante chez les eleves :
# une affirmation de frequence donne au site une autorite qu'il n'a pas. « On inverse
# facilement » ou « confusion classique » decrivent un risque sans pretendre le mesurer.
FORMULES_DE_FREQUENCE = ("fréquen", "le plus souvent", "la plupart", "généralement")


def test_aucune_affirmation_de_frequence_n_est_laissee_au_chapitre_1():
    prose = _prose(CHAPITRE_1)
    for formule in FORMULES_DE_FREQUENCE:
        assert formule not in prose, formule
