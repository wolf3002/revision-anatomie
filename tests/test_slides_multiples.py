"""Le champ `slide` accepte un entier ou une liste d'entiers : rendu de bout en bout.

tests/test_schema.py couvre la validation, tests/test_construire.py le rendu d'un renvoi
isole. Ici, un vrai cours dont quelques entrees passent en liste est construit dans un
dossier temporaire -- site, fiches imprimables, variante autonome -- pour verifier que
chaque consommateur du champ suit, et que les centaines d'entrees restees a un entier ne
bougent pas d'un octet.
"""

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import slides_de, valider_cours  # noqa: E402
from outils.construire import construire  # noqa: E402
from outils.empaqueter import empaqueter  # noqa: E402
from outils.fiches import construire_fiches  # noqa: E402

# (chapitre, genre, position dans la liste, nouvelle valeur du champ, rendu attendu).
# Les bornes sont celles du cours : chapitre 6 = slides 191-266, chapitre 7 = 268-328.
MODIFICATIONS = [
    (7, "muscles", 0, [319, 320], "slides 319 et 320"),
    (7, "cartes", 0, [309, 316, 320], "slides 309, 316 et 320"),
    (7, "pieges", 0, [300, 301], "slides 300 et 301"),
    (6, "quiz", 0, [230, 229], "slides 229 et 230"),  # saisie non triee : rendu trie
    (6, "planches", 0, [229, 231], "slides 229 et 231"),
    (6, "cartes", 1, [250], "slide 250"),  # liste d'un seul element
]


def _copier_le_projet(tmp_path):
    racine = tmp_path / "revision-anatomie"
    for dossier in ("contenu", "gabarits"):
        shutil.copytree(
            RACINE / dossier,
            racine / dossier,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    shutil.copytree(
        RACINE / "site", racine / "site", ignore=shutil.ignore_patterns("pdf")
    )
    return racine


def _ecrire_cours(racine, cours):
    (racine / "contenu" / "cours.json").write_text(
        json.dumps(cours, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _copie_modifiee(tmp_path):
    racine = _copier_le_projet(tmp_path)
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))
    for num, genre, rang, valeur, _ in MODIFICATIONS:
        chapitre = next(c for c in cours["chapitres"] if c["num"] == num)
        chapitre[genre][rang]["slide"] = valeur
    # Une section a cheval sur deux slides, la premiere restant celle d'origine : la
    # fiche range planches et pieges d'apres la premiere slide de chaque section.
    section = next(c for c in cours["chapitres"] if c["num"] == 7)["sections"][0]
    section["slide"] = [section["slide"], section["slide"] + 1]
    _ecrire_cours(racine, cours)
    return racine, cours


@pytest.fixture(scope="module")
def cours_a_slides_multiples(tmp_path_factory):
    racine, cours = _copie_modifiee(tmp_path_factory.mktemp("slides"))
    construire(racine)
    construire_fiches(racine)
    empaqueter(racine)
    return racine, cours


def _lire(racine, *chemin):
    return (racine.joinpath(*chemin)).read_text(encoding="utf-8")


def test_le_cours_modifie_est_valide(cours_a_slides_multiples):
    _, cours = cours_a_slides_multiples
    assert valider_cours(cours) == []


def test_le_site_affiche_les_slides_de_chaque_entree_modifiee(cours_a_slides_multiples):
    racine, _ = cours_a_slides_multiples
    pages = {
        7: _lire(racine, "site", "chapitre-7.html"),
        6: _lire(racine, "site", "chapitre-6.html"),
    }
    for num, genre, _, _, attendu in MODIFICATIONS:
        assert f'<span class="src">{attendu}</span>' in pages[num], (
            num,
            genre,
            attendu,
        )


def test_la_table_musculaire_montre_les_slides_dans_l_en_tete_du_muscle(
    cours_a_slides_multiples,
):
    racine, cours = cours_a_slides_multiples
    nom = next(c for c in cours["chapitres"] if c["num"] == 7)["muscles"][0]["nom"]
    page = _lire(racine, "site", "chapitre-7.html")
    # Une fois dans la fiche (table de lecture), une fois dans les exercices (table a
    # completer) : les deux tables lisent le meme champ.
    assert (
        len(
            re.findall(
                rf"<th>[^<]*{re.escape(nom)}[^<]*<span class=\"src\">slides 319 et 320</span></th>",
                page,
            )
        )
        == 2
    )


def test_la_fiche_imprimable_affiche_les_slides(cours_a_slides_multiples):
    racine, _ = cours_a_slides_multiples
    fiche7 = _lire(racine, "site", "pdf", "fiche-07.html")
    fiche6 = _lire(racine, "site", "pdf", "fiche-06.html")
    assert (
        "slides 319 et 320" in fiche7
    )  # muscle, en tete de la table et dans le corrige
    assert "slides 309, 316 et 320" in fiche7  # carte
    assert "slides 300 et 301" in fiche7  # piege
    assert "slides 229 et 230" in fiche6  # quiz
    assert "slide 250" in fiche6


def test_la_variante_autonome_affiche_les_slides(cours_a_slides_multiples):
    racine, _ = cours_a_slides_multiples
    accueil = _lire(racine, "site-autonome", "index.html")  # reservoir de la seance
    for num, genre, _, _, attendu in MODIFICATIONS:
        page = _lire(racine, "site-autonome", f"chapitre-{num}.html")
        assert f'<span class="src">{attendu}</span>' in page, (num, genre)
        if genre != "pieges":  # les pieges ne sont pas des exercices : pas de reservoir
            assert f'<span class="src">{attendu}</span>' in accueil, (num, genre)


def test_le_cours_publie_garde_la_liste_telle_quelle(cours_a_slides_multiples):
    # interface.js ne lit jamais `slide` ; le champ voyage tel quel dans les donnees.
    racine, _ = cours_a_slides_multiples
    publie = json.loads(_lire(racine, "site", "assets", "cours.json"))
    chapitre7 = next(c for c in publie["chapitres"] if c["num"] == 7)
    assert chapitre7["muscles"][0]["slide"] == [319, 320]
    assert chapitre7["cartes"][0]["slide"] == [309, 316, 320]
    donnees = _lire(racine, "site-autonome", "assets", "cours-data.js")
    assert "[319, 320]" in donnees


def test_la_section_a_cheval_sur_deux_slides_est_rendue_et_range_ses_figures(
    cours_a_slides_multiples,
):
    racine, cours = cours_a_slides_multiples
    section = next(c for c in cours["chapitres"] if c["num"] == 7)["sections"][0]
    a, b = section["slide"]
    page = _lire(racine, "site", "chapitre-7.html")
    assert f'<span class="src">slides {a} et {b}</span>' in page


def test_les_pages_dont_aucune_entree_n_a_change_sont_identiques_octet_pour_octet(
    cours_a_slides_multiples,
):
    # Retrocompatibilite : les centaines d'entrees a un entier rendent exactement ce
    # qu'elles rendaient. Les chapitres 1 a 5 n'ont aucune entree modifiee ; leurs
    # pages (site, fiches, autonome) sont celles de la construction de reference.
    racine, _ = cours_a_slides_multiples
    empaqueter(RACINE)  # regenere site/ et site-autonome/ depuis le vrai contenu
    construire_fiches(RACINE)
    for num in range(1, 6):
        for chemin in (
            ("site", f"chapitre-{num}.html"),
            ("site", "pdf", f"fiche-{num:02d}.html"),
            ("site-autonome", f"chapitre-{num}.html"),
        ):
            assert _lire(racine, *chemin) == _lire(RACINE, *chemin), chemin


@pytest.mark.slow
def test_trois_slides_partout_ne_font_deborder_aucune_page(tmp_path):
    """« slides 309, 316 et 320 » est plus long que « slide 319 » : dans la cellule
    d'un muscle (colonne fixe d'un quart de table), il debordait de ~22 px a 768 px et
    plus tant que .src etait insecable (site/assets/style.css §5.8). On donne trois
    slides a toutes les entrees des chapitres 5 a 7 -- le pire cas -- et le controleur
    de mise en page ne doit rien signaler, aux huit largeurs."""
    from outils.verifier_mobile import verifier_page

    racine = _copier_le_projet(tmp_path)
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))
    for chapitre in cours["chapitres"]:
        if chapitre["num"] not in (5, 6, 7):
            continue
        _, fin = chapitre["slides"]
        for genre in ("cartes", "quiz", "muscles", "pieges", "planches"):
            for entree in chapitre[genre]:
                # Une entree deja a cheval sur plusieurs slides (liste) part de sa premiere.
                s = min(slides_de(entree))
                entree["slide"] = [s, s + 1, s + 2] if s + 2 <= fin else [s - 2, s - 1, s]
        for section in chapitre["sections"]:
            s = min(slides_de(section))
            if s + 2 <= fin:
                section["slide"] = [s, s + 1, s + 2]
    assert valider_cours(cours) == []
    _ecrire_cours(racine, cours)
    construire(racine)
    defauts = []
    for nom in ("chapitre-5.html", "chapitre-6.html", "chapitre-7.html"):
        defauts += verifier_page(racine / "site" / nom)
    assert defauts == []
