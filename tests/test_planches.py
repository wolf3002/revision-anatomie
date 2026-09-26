import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_planche
from outils.planches import PLANCHES


def test_les_quatre_planches_du_chapitre_1_existent():
    # plans-anatomiques a ete eclatee en trois planches autonomes (ronde de
    # correction 4) : un viewBox large a trois panneaux ne tient pas sur mobile.
    assert set(PLANCHES) >= {
        "plan-frontal",
        "plan-sagittal",
        "plan-transversal",
        "termes-localisation",
    }


def test_chaque_planche_est_conforme():
    for identifiant, planche in PLANCHES.items():
        assert valider_planche(planche) == [], identifiant


def test_aucun_trace_ne_contient_ses_etiquettes():
    for identifiant, planche in PLANCHES.items():
        assert "<text" not in planche["dessin"], identifiant


def test_les_pastilles_des_plans_portent_leur_plan():
    # Les trois plans sont a present trois planches distinctes ; le champ 'plan'
    # doit malgre tout couvrir les trois valeurs a travers l'ensemble des pastilles.
    pastilles = [
        p
        for planche_id in ("plan-frontal", "plan-sagittal", "plan-transversal")
        for p in PLANCHES[planche_id]["pastilles"]
    ]
    plans = {p.get("plan") for p in pastilles if p.get("plan")}
    assert plans == {"frontal", "sagittal", "transversal"}


def test_les_libelles_sont_uniques_dans_une_planche():
    for identifiant, planche in PLANCHES.items():
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), identifiant
