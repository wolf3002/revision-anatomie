import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

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
