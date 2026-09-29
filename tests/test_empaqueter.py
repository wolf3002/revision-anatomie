"""outils/empaqueter.py -> site-autonome/, la variante utilisable en file://.

Meme convention que tests/test_construire.py et tests/test_fiches.py :
regeneration au niveau du module (rapide -- aucun Chrome invoque ici, a la
difference de tests/test_verifier_mobile.py), puis assertions sur le
resultat ecrit sur disque. Le pilotage reel en file:// (console, seance qui
melange les sept chapitres et les formats, persistance...) est fait a la
main avec Playwright -- voir le rapport de tache -- et n'est pas repete ici :
ces tests-ci verifient la FORME du livrable (pas de module ES, pas de fetch,
pas d'import/export, contenu embarque complet), pas son comportement en
direct dans un navigateur.
"""

import html
import json
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.empaqueter import empaqueter  # noqa: E402

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
FICHIERS = empaqueter(RACINE)
SORTIE = RACINE / "site-autonome"

INDEX = (SORTIE / "index.html").read_text(encoding="utf-8")
APP_JS = (SORTIE / "assets" / "app.js").read_text(encoding="utf-8")
COURS_DATA_JS = (SORTIE / "assets" / "cours-data.js").read_text(encoding="utf-8")

# Les memes regex que le controle final demande (pas de module ES, pas de
# fetch, pas d'import/export dans le JS) -- ancrees en debut de ligne pour
# ignorer les commentaires/textes qui contiennent le mot sans etre le mot-cle
# ("export / import" dans un libelle de bouton, "statutImport" en variable).
_RE_EXPORT_STATEMENT = re.compile(
    r"^\s*export\s+(function|async function|const|let|var|default|\{)", re.MULTILINE
)
_RE_IMPORT_STATEMENT = re.compile(r"^\s*import\s", re.MULTILINE)


# --- Le dossier est ecrit, avec la structure attendue -----------------------


def test_le_dossier_site_autonome_est_ecrit():
    assert SORTIE.is_dir()
    assert (SORTIE / "index.html") in FICHIERS
    for chapitre in COURS["chapitres"]:
        assert (SORTIE / f"chapitre-{chapitre['num']}.html") in FICHIERS


def test_les_sept_fiches_pdf_sont_copiees():
    for num in range(1, 8):
        chemin = SORTIE / "pdf" / f"fiche-{num:02d}.pdf"
        assert chemin.exists(), chemin
        assert chemin.stat().st_size > 20_000, chemin


def test_le_lisez_moi_existe_et_reste_accessible_a_un_non_technicien():
    lisez_moi = (SORTIE / "LISEZ-MOI.txt").read_text(encoding="utf-8")
    assert "index.html" in lisez_moi
    # Dit explicitement comment ouvrir le site (double-clic), que la
    # progression est locale au navigateur/appareil, et ou sont les PDF.
    assert "double-clique" in lisez_moi.lower()
    assert "navigateur" in lisez_moi.lower()
    assert "pdf" in lisez_moi.lower()


def test_le_dossier_site_reste_le_dossier_de_developpement():
    # empaqueter() regenere site/ (via outils.construire.construire) mais ne
    # doit jamais en changer la NATURE : il reste sur les modules ES, servis
    # en http:// -- seule site-autonome/ est pensee pour file://.
    accueil_site = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'type="module"' in accueil_site
    assert (RACINE / "site" / "assets" / "app.js").exists()
    assert (RACINE / "site" / "assets" / "interface.js").exists()


# --- a. Modules ES fondus en un script classique ----------------------------


def test_aucune_page_ne_charge_un_module_es():
    for nom in ["index.html"] + [
        f"chapitre-{c['num']}.html" for c in COURS["chapitres"]
    ]:
        page = (SORTIE / nom).read_text(encoding="utf-8")
        assert 'type="module"' not in page, nom
        assert '<script src="assets/app.js"></script>' in page, nom


def test_le_script_fondu_ne_contient_plus_ni_module_ni_fetch_ni_import_export():
    # Le controle final demande explicitement ces trois absences.
    assert 'type="module"' not in APP_JS
    assert "fetch(" not in APP_JS
    assert not _RE_IMPORT_STATEMENT.search(APP_JS), "instruction import residuelle"
    assert not _RE_EXPORT_STATEMENT.search(APP_JS), "instruction export residuelle"


def test_le_script_fondu_est_syntaxiquement_valide():
    # node --check compile sans executer : verifie a la fois l'absence
    # d'erreur de syntaxe ET l'absence de collision de nom au meme niveau de
    # portee (ex. `const JOUR_MS` declare deux fois dans le meme scope,
    # planificateur.js et interface.js -- IIFE separees sinon SyntaxError).
    resultat = subprocess.run(
        ["node", "--check", str(SORTIE / "assets" / "app.js")],
        capture_output=True,
        text=True,
    )
    assert resultat.returncode == 0, resultat.stderr


def test_les_fonctions_exportees_restent_toutes_disponibles():
    # Les noms que planificateur/stockage/exercices/interface exportaient en
    # ES doivent rester appelables depuis le scope global du script fondu.
    for nom in (
        "intervalleDeBase",
        "composerSeance",
        "reinjecterRate",
        "creerStockage",
        "itemsDuCours",
        "verifierPastille",
        "demarrer",
    ):
        assert re.search(rf"\bconst\s*\{{[^}}]*\b{nom}\b", APP_JS) or re.search(
            rf"\bfunction\s+{nom}\b", APP_JS
        ), nom


# --- b. cours.json embarque -------------------------------------------------


def test_les_pages_chargent_les_donnees_du_cours_avant_le_script():
    for nom in ["index.html"] + [
        f"chapitre-{c['num']}.html" for c in COURS["chapitres"]
    ]:
        page = (SORTIE / nom).read_text(encoding="utf-8")
        pos_donnees = page.index('<script src="assets/cours-data.js"></script>')
        pos_app = page.index('<script src="assets/app.js"></script>')
        assert pos_donnees < pos_app, nom


def test_les_donnees_du_cours_sont_completes_et_fideles():
    m = re.search(r"window\.COURS_JSON = (.*);\s*$", COURS_DATA_JS, re.DOTALL)
    assert m, "assets/cours-data.js ne pose pas window.COURS_JSON"
    cours_embarque = json.loads(m.group(1))
    assert cours_embarque == COURS
    assert len(cours_embarque["chapitres"]) == 7


def test_l_appel_reseau_vers_cours_json_a_disparu():
    assert "assets/cours.json" not in APP_JS
    assert "'cours.json'" not in APP_JS


# --- c. Reservoir pour la seance, plus de fetch de page de chapitre --------


def test_aucune_page_ne_fetch_une_page_de_chapitre():
    assert "fetch(" not in APP_JS
    assert "chapitre-${" not in APP_JS
    assert "DOMParser" not in APP_JS


def test_l_accueil_porte_un_reservoir_cache_avec_tous_les_chapitres():
    m = re.search(
        r'<div id="reservoir-seance"([^>]*)>(.*)</div>\s*<script', INDEX, re.DOTALL
    )
    assert m, "reservoir #reservoir-seance introuvable juste avant les <script>"
    attributs, contenu = m.group(1), m.group(2)
    assert "hidden" in attributs

    for chapitre in COURS["chapitres"]:
        for carte in chapitre["cartes"]:
            assert f'id="{carte["id"]}"' in contenu, carte["id"]
        for question in chapitre["quiz"]:
            assert f'id="{question["id"]}"' in contenu, question["id"]
        for planche in chapitre["planches"]:
            assert f'id="{planche["id"]}"' in contenu, planche["id"]
        for muscle in chapitre["muscles"]:
            # data-id passe par html.escape() cote generateur (une apostrophe
            # de nom de muscle, ex. "Transverse de l'abdomen", y devient
            # &#x27; -- meme echappement attendu ici).
            attendu = html.escape(f"{chapitre['num']}#muscle#{muscle['nom']}")
            assert attendu in contenu, attendu


def test_les_pages_de_chapitre_portent_leur_propre_reservoir_et_pas_celui_du_cours():
    # Le reservoir de l'accueil (#reservoir-seance) tient tous les chapitres pour
    # la seance du jour. Une page de chapitre, elle, porte SEULEMENT les modeles de
    # son chapitre (#reservoir-exercices) : S'exercer les clone sur place, sans
    # rien recuperer -- c'est ce qui le fait marcher en file://.
    for chapitre in COURS["chapitres"]:
        page = (SORTIE / f"chapitre-{chapitre['num']}.html").read_text(encoding="utf-8")
        assert 'id="reservoir-seance"' not in page
        m = re.search(
            r'<div id="reservoir-exercices" data-reservoir hidden aria-hidden="true">(.*?)</div>\s*'
            r'<div class="actions"',
            page,
            re.DOTALL,
        )
        assert m, chapitre["num"]
        contenu = m.group(1)
        assert contenu.count('class="carte"') == len(chapitre["cartes"])
        assert contenu.count('class="question"') == len(chapitre["quiz"])
        assert contenu.count('class="planche"') == len(chapitre["planches"])


def test_le_reservoir_de_l_accueil_se_reconnait_au_script_comme_reservoir_local():
    # interface.js cherche [data-reservoir] : les deux reservoirs le portent.
    assert re.search(r'<div id="reservoir-seance" data-reservoir hidden', INDEX)


def test_le_reservoir_est_masque_a_l_ecran_et_a_l_impression():
    # [hidden] { display: none !important; } (site/assets/style.css, section
    # 2) est une regle globale sans condition de media : elle s'applique a
    # l'ecran comme a l'impression, et !important l'emporte sur toute regle
    # de composant qui poserait display:grid/flex sur ce meme element.
    style = (SORTIE / "assets" / "style.css").read_text(encoding="utf-8")
    assert re.search(r"\[hidden\]\s*\{\s*display:\s*none\s*!important;", style)


def test_le_nombre_d_items_dans_le_reservoir_correspond_au_cours():
    nb_cartes = sum(len(c["cartes"]) for c in COURS["chapitres"])
    nb_quiz = sum(len(c["quiz"]) for c in COURS["chapitres"])
    nb_planches = sum(len(c["planches"]) for c in COURS["chapitres"])

    m = re.search(
        r'<div id="reservoir-seance"[^>]*>(.*)</div>\s*<script', INDEX, re.DOTALL
    )
    contenu = m.group(1)
    assert contenu.count('class="carte"') == nb_cartes
    assert contenu.count('class="question"') == nb_quiz
    assert contenu.count('class="planche"') == nb_planches


# --- Empaqueter est idempotent (rejouable sans effet de bord) --------------


def test_empaqueter_est_idempotent():
    avant = (SORTIE / "index.html").read_text(encoding="utf-8")
    empaqueter(RACINE)
    apres = (SORTIE / "index.html").read_text(encoding="utf-8")
    assert avant == apres
