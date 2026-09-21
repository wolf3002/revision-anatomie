import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_planche
from outils.planches import PLANCHES


def test_les_deux_planches_du_chapitre_1_existent():
    assert set(PLANCHES) >= {"plans-anatomiques", "termes-localisation"}


def test_chaque_planche_est_conforme():
    for identifiant, planche in PLANCHES.items():
        assert valider_planche(planche) == [], identifiant


def test_aucun_trace_ne_contient_ses_etiquettes():
    for identifiant, planche in PLANCHES.items():
        assert "<text" not in planche["dessin"], identifiant


def test_les_pastilles_des_plans_portent_leur_plan():
    pastilles = PLANCHES["plans-anatomiques"]["pastilles"]
    plans = {p.get("plan") for p in pastilles if p.get("plan")}
    assert plans == {"frontal", "sagittal", "transversal"}


def test_les_libelles_sont_uniques_dans_une_planche():
    for identifiant, planche in PLANCHES.items():
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), identifiant
