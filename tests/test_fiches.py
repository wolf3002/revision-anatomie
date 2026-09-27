import html
import json
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.fiches import construire_fiches  # noqa: E402

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRES = COURS["chapitres"]

# Regenere les sept fiches HTML (rapide : pas de Chrome ici, cf. test_construire.py
# pour la meme convention sur les pages du site). Les PDF, eux, sont deja commis
# dans site/pdf/ -- les tests ci-dessous verifient ce livrable existant plutot que
# de rappeler Chrome (outils/pdf.py) a chaque lancement de la suite.
FICHIERS_HTML = construire_fiches(RACINE)


def _page(num: int) -> str:
    return (RACINE / "site" / "pdf" / f"fiche-{num:02d}.html").read_text(
        encoding="utf-8"
    )


def _pdf(num: int) -> Path:
    return RACINE / "site" / "pdf" / f"fiche-{num:02d}.pdf"


def _pages_pdf(chemin: Path) -> int:
    sortie = subprocess.run(
        ["pdfinfo", str(chemin)], check=True, capture_output=True, text=True
    ).stdout
    for ligne in sortie.splitlines():
        if ligne.startswith("Pages:"):
            return int(ligne.split(":")[1].strip())
    raise AssertionError(f"pdfinfo n'a rendu aucun nombre de pages pour {chemin}")


# --- Les sept fiches existent (HTML intermediaire et PDF livre) -----------


def test_les_sept_fiches_html_sont_ecrites():
    assert len(FICHIERS_HTML) == 7
    for num in range(1, 8):
        assert (RACINE / "site" / "pdf" / f"fiche-{num:02d}.html") in FICHIERS_HTML


def test_les_sept_pdf_existent_et_sont_versionnes():
    for num in range(1, 8):
        chemin = _pdf(num)
        assert chemin.exists(), chemin
        # Un gabarit casse produirait un PDF quasi vide (page blanche) ; un
        # vrai chapitre (planches + cartes + quiz + corrige) pese largement
        # plus que quelques ko.
        assert chemin.stat().st_size > 20_000, chemin


def test_le_nombre_de_pages_reste_raisonnable():
    # Bornes larges plutot qu'un chiffre exact par fiche (le contenu du
    # cours peut encore bouger) : on ecarte seulement un gabarit casse
    # (0 ou 1 page, tout tiendrait sur une seule) ou un emballement de mise
    # en page (une planche ou une case qui deborde sur des dizaines de
    # pages vides).
    for num in range(1, 8):
        n = _pages_pdf(_pdf(num))
        assert 6 <= n <= 40, (num, n)


# --- Chaque fiche contient les questions de son chapitre -------------------


def test_chaque_fiche_contient_les_cartes_et_le_quiz_de_son_chapitre():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        for carte in chapitre["cartes"]:
            assert carte["id"] in page, (chapitre["num"], carte["id"])
        for question in chapitre["quiz"]:
            assert question["id"] in page, (chapitre["num"], question["id"])


def test_chaque_fiche_contient_ses_planches_et_ses_pieges():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        for planche in chapitre["planches"]:
            assert planche["id"] in page, (chapitre["num"], planche["id"])
        for piege in chapitre["pieges"]:
            assert html.escape(piege["titre"]) in page, (
                chapitre["num"],
                piege["titre"],
            )


def test_chaque_renvoi_de_slide_est_affiche():
    # Meme intention que tests/test_construire.py : une carte precise porte
    # bien son numero de slide dans le rendu, pas seulement dans cours.json.
    page = _page(1)
    assert "slide 9" in page  # c1-01, "position anatomique"


def test_une_table_musculaire_n_apparait_que_pour_les_chapitres_qui_en_ont():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        a_des_muscles = bool(chapitre.get("muscles"))
        assert ('data-section="muscles"' in page) == a_des_muscles, chapitre["num"]


# --- Rien ne s'affiche avant d'avoir ete cherche ---------------------------


def _avant_et_apres_corrige(page: str) -> tuple[str, str]:
    i = page.index('data-section="corrige"')
    return page[:i], page[i:]


def test_le_corrige_existe_et_vient_en_dernier():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        assert 'data-section="corrige"' in page, chapitre["num"]
        avant, _ = _avant_et_apres_corrige(page)
        # Le corrige est la derniere section : rien de connu (planches,
        # questions, muscles, pieges) ne doit plus apparaitre APRES lui.
        assert page.rindex('data-section="corrige"') > page.rindex(
            'class="fiche-entete"'
        )
        assert avant.count('data-section="corrige"') == 0


def test_aucun_libelle_de_pastille_n_apparait_avant_le_corrige():
    # _rendre_planche_muette (outils/fiches.py) retire la balise <text
    # class="pastille__t"> du mode muet -- elle ne doit donc jamais
    # apparaitre avant le corrige (le seul endroit ou construire._rendre_
    # planche est rappele sans modification). On cherche la balise elle
    # meme, pas le mot "pastille__t" tout court : il apparait aussi une
    # fois par page dans la regle CSS partagee, dans <head>, avant la toute
    # premiere section -- un simple comptage de mot s'y tromperait.
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        avant, apres = _avant_et_apres_corrige(page)
        assert '<text class="pastille__t"' not in avant, chapitre["num"]
        if chapitre.get("planches"):
            assert '<text class="pastille__t"' in apres, chapitre["num"]


def test_aucune_reponse_de_carte_ou_de_quiz_n_apparait_avant_le_corrige():
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        avant, apres = _avant_et_apres_corrige(page)
        for carte in chapitre["cartes"]:
            reponse = html.escape(carte["r"])
            assert reponse not in avant, (chapitre["num"], carte["id"])
            assert reponse in apres, (chapitre["num"], carte["id"])
        for question in chapitre["quiz"]:
            explication = html.escape(question["expl"])
            assert explication not in avant, (chapitre["num"], question["id"])
            assert explication in apres, (chapitre["num"], question["id"])
            # L'index de la bonne reponse n'est jamais marque avant le
            # corrige. On cherche l'usage de la classe sur un element
            # (class="...fiche-corrige__bonne...") et pas le mot tout
            # court : lui aussi vit dans la regle CSS partagee de <head>,
            # avant la premiere section, comme pastille__t plus haut.
            assert 'class="fiche-corrige__bonne"' not in avant


def test_les_cases_musculaires_sont_vides_avant_le_corrige():
    # Verification structurelle plutot que textuelle (une valeur de muscle
    # peut legitimement reapparaitre dans le texte d'un piege affiche en
    # clair -- ex. chapitre 5, Ilio-psoas -- donc un simple "valeur pas dans
    # la page" produirait de faux positifs). La vraie garantie : la cellule
    # elle-meme est litteralement vide dans la section d'exercice.
    for chapitre in CHAPITRES:
        if not chapitre.get("muscles"):
            continue
        page = _page(chapitre["num"])
        avant, apres = _avant_et_apres_corrige(page)
        cases_vides = re.findall(r'<td class="fiche-muscle__case">(.*?)</td>', avant)
        assert len(cases_vides) == 3 * len(chapitre["muscles"])
        assert all(case == "" for case in cases_vides)
        # Le corrige, lui, reutilise construire._rendre_volet : les valeurs
        # y sont visibles (span muscle__valeur), jamais une case vide.
        assert "muscle__valeur" in apres


# --- Mise en forme imprimable ------------------------------------------


def test_le_gabarit_evite_les_sauts_de_page_dans_une_question_ou_une_planche():
    gabarit = (RACINE / "gabarits" / "fiche.html").read_text(encoding="utf-8")
    for regle in (".fiche-carte", ".fiche-quiz", ".fiche-planche"):
        motif = re.escape(regle) + r"[^{]*\{[^}]*break-inside:\s*avoid"
        assert re.search(motif, gabarit), regle


def test_le_gabarit_est_au_format_a4_sans_police_distante():
    gabarit = (RACINE / "gabarits" / "fiche.html").read_text(encoding="utf-8")
    assert "size: A4" in gabarit
    assert "fonts.googleapis.com" not in gabarit
    assert "fonts.gstatic.com" not in gabarit


def test_le_plan_anatomique_est_toujours_ecrit_en_toutes_lettres():
    # Regle absolue du projet (site/assets/style.css section 8) : une carte
    # ou un quiz rattache a un plan porte ce plan en texte, jamais par une
    # simple teinte -- la fiche etant pensee pour un rendu noir et blanc,
    # elle ne s'appuie sur aucune couleur du tout.
    trouve = False
    for chapitre in CHAPITRES:
        page = _page(chapitre["num"])
        for carte in chapitre["cartes"]:
            if carte.get("plan"):
                trouve = True
                assert f"plan {carte['plan']}" in page, carte["id"]
    assert trouve, "aucune carte porteuse d'un plan n'a ete rencontree"
