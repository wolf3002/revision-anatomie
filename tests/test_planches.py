import json
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


def test_cours_json_reprend_exactement_les_planches_de_planches_py():
    # Les planches vivent a deux endroits : outils/planches.py (source de
    # travail) et contenu/cours.json (ce que le site lit). Corriger l'une sans
    # l'autre les fait diverger sans aucun signal -- ce test en est un.
    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    dans_cours = {p["id"]: p for chapitre in cours["chapitres"] for p in chapitre["planches"]}
    assert set(dans_cours) == set(PLANCHES)
    for identifiant, source in PLANCHES.items():
        for cle in ("titre", "vb", "dessin", "pastilles"):
            assert dans_cours[identifiant][cle] == source[cle], (identifiant, cle)


def test_les_libelles_tiennent_dans_le_cadre_des_planches_du_site():
    # Le controle d'emprise du validateur, applique a chaque planche publiee.
    # Sous-ensemble strict de test_chaque_planche_est_conforme, mais nomme : c'est
    # celui qui a manque douze libelles rognes du chapitre 7 pendant trois revues.
    for identifiant, planche in PLANCHES.items():
        erreurs = [e for e in valider_planche(planche) if "deborde" in e]
        assert erreurs == [], identifiant
