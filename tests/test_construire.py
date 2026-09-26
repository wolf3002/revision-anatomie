import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import construire

FICHIERS = construire(RACINE)
PAGE = (RACINE / "site" / "chapitre-1.html").read_text(encoding="utf-8")


def test_la_page_du_chapitre_1_est_ecrite():
    assert (RACINE / "site" / "chapitre-1.html") in FICHIERS


def test_la_page_interdit_l_indexation():
    assert 'name="robots"' in PAGE and "noindex" in PAGE


def test_toutes_les_cartes_sont_dans_le_dom():
    import json

    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    for carte in cours["chapitres"][0]["cartes"]:
        assert carte["id"] in PAGE, carte["id"]


def test_les_reponses_sont_masquees_par_defaut():
    assert 'data-etat="cachee"' in PAGE


def test_chaque_renvoi_de_slide_est_affiche():
    assert "slide 9" in PAGE


def test_l_onglet_muscles_est_absent_quand_il_n_y_a_pas_de_muscle():
    assert 'data-onglet="muscles"' not in PAGE


def test_le_contenu_du_cours_est_present_sans_javascript():
    assert "Corps humain, vivant, debout" in PAGE


def test_une_copie_du_contenu_est_publiee_pour_le_client():
    assert (RACINE / "site" / "assets" / "cours.json").exists()
