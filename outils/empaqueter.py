"""site/ -> site-autonome/, une variante utilisable par simple double-clic.

Contexte : le site devait etre publie sur GitHub Pages ; l'utilisateur a
finalement choisi de l'envoyer a un ami sous forme de dossier, pour que rien
ne parte sur Internet. Il doit donc fonctionner ouvert directement en
file:// -- ce que site/ ne fait pas :

  1. gabarits/base.html charge assets/app.js en <script type="module"> ;
     Chrome refuse d'executer un module ES sous l'origine file:// (politique
     d'origine) -- rien du script ne s'execute, aucun bouton ne repond.
  2. Les cinq fichiers de site/assets/ s'importent mutuellement (import/export
     ES), invalides dans un <script> classique.
  3. Deux appels reseau echouent sans serveur : interface.js charge
     assets/cours.json (donnees du quiz, items par defaut) et
     chapitre-N.html (pour cloner le rendu d'un item d'un autre chapitre
     dans la seance du jour).

Ce module ne reecrit ni le contenu ni la logique : il POST-TRAITE la sortie
de outils/construire.py (site/) en trois transformations, chacune documentee
sur sa fonction :
  a) _fondre_modules   -- fond les cinq modules ES en un seul script classique
  b) _donnees_cours    -- embarque contenu/cours.json en variable globale
  c) _rendre_reservoir -- remplace le fetch de chapitre-N.html par un clone
                          local depuis un reservoir cache injecte dans
                          index.html

site/ n'est jamais modifie par ce module (hormis sa regeneration normale par
outils.construire.construire, deja versionnee et sans rapport avec ces trois
transformations) : c'est le dossier de developpement et de test, servi en
http:// ou par un serveur local. Seule site-autonome/ est pensee pour
file://.
"""

import json
import re
import shutil
import sys
from pathlib import Path

# Meme convention que outils/construire.py et outils/fiches.py : permet
# `python3 outils/empaqueter.py` (execution directe) comme
# `python3 -m outils.empaqueter`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Reutilisation directe de _rendre_volet -- pas de reecriture, meme principe
# que outils/fiches.py (qui reutilise _rendre_planche et _rendre_volet pour
# un autre livrable) : le reservoir de la seance (transformation c) doit
# produire EXACTEMENT le meme balisage que chapitre-N.html pour chaque
# carte/question/planche/table musculaire -- l'identite de rendu est garantie
# par l'appel a la meme fonction, jamais par une resynchronisation a la main
# entre deux gabarits.
from outils.construire import EXERCICES, construire, _rendre_volet  # noqa: E402

# Ordre de dependance des modules ES de site/assets/ (verifie par lecture des
# `import` de chaque fichier) : planificateur, stockage et exercices n'ont
# aucune dependance mutuelle ; interface importe les trois ; app importe
# interface. Fondre dans un ordre different casserait "X is not defined" a
# l'execution (une IIFE ne voit que ce qui a ete declare AVANT elle dans le
# script fondu).
ORDRE_MODULES = (
    "planificateur.js",
    "stockage.js",
    "exercices.js",
    "interface.js",
    "app.js",
)

_RE_IMPORT = re.compile(r"^import .*\n", re.MULTILINE)
_RE_EXPORT_ASYNC_FUNCTION = re.compile(r"^export async function (\w+)", re.MULTILINE)
_RE_EXPORT_FUNCTION = re.compile(r"^export function (\w+)", re.MULTILINE)
_RE_EXPORT_CONST = re.compile(r"^export const (\w+)", re.MULTILINE)

# Repere exact pose par gabarits/base.html (identique sur les huit pages :
# {{racine}} vaut toujours "" pour l'accueil et les chapitres, cf.
# outils/construire.py). Si cette balise disparait, un gabarit a change sans
# que ce module ait ete mis a jour -- on prefere planter bruyamment plutot
# que produire un site-autonome silencieusement casse.
BALISE_SCRIPT_MODULE = '<script type="module" src="assets/app.js"></script>'
BALISES_SCRIPT_CLASSIQUES = (
    '<script src="assets/cours-data.js"></script>\n'
    '<script src="assets/app.js"></script>'
)

# Les formats qui produisent des items planifiables (cf. exercices.itemsDuCours)
# sont ceux de construire.EXERCICES -- la fiche et les pieges (les contenus de
# lecture) ne sont jamais tires en seance, donc jamais recherches dans le
# reservoir. Une seule liste, partagee avec le reservoir cache que chaque page
# de chapitre porte deja (construire._rendre_reservoir_exercices).

_LISEZ_MOI = """\
Site de revision -- Anatomie
=============================

QU'EST-CE QUE C'EST ?
----------------------
Un site pour reviser le cours d'anatomie : la fiche de chaque chapitre a lire,
puis des exercices (cartes, questions, planches a legender, muscles a completer)
et une "seance du jour" qui pioche automatiquement dans ce qui doit etre revu.

PAR OU COMMENCER ?
-------------------
Sur la page d'accueil, chaque chapitre a deux boutons : "Lire la fiche" (le
cours, a lire d'abord) puis "S'exercer" (les exercices du chapitre, un a la
fois). La "seance du jour" te fait ensuite revenir sur ce que tu as deja vu.

COMMENT L'OUVRIR ?
-------------------
Double-clique simplement sur le fichier "index.html" de ce dossier. Il
s'ouvre directement dans ton navigateur (Chrome, Firefox, Edge...) -- pas
d'installation, pas de connexion Internet necessaire.

TA PROGRESSION
---------------
Chaque reponse (carte retournee, question repondue, planche verifiee...) est
memorisee automatiquement DANS CE NAVIGATEUR, sur CET APPAREIL. Consequence
importante :
  - si tu changes d'ordinateur, de telephone ou de navigateur, ta progression
    ne te suivra pas ;
  - si tu vides le cache / les donnees de navigation, elle est perdue.
Le bouton "Exporter la progression", dans les "Reglages" (lien discret en bas
de la page d'accueil),
permet d'en garder une copie de secours dans un fichier, a reimporter plus
tard (meme bouton, "Importer une progression").

LES FICHES PDF
---------------
Le dossier "pdf/" contient une fiche imprimable par chapitre (7 fiches), utile
pour reviser sur papier.

Bonne revision !
"""


def empaqueter(racine: Path) -> list[Path]:
    racine = Path(racine)
    # Source unique : cours.json + gabarits -> site/, toujours frais avant
    # d'en deriver la variante autonome (meme convention que
    # tests/test_construire.py, qui regenere site/ a chaque lancement).
    construire(racine)

    site = racine / "site"
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))

    sortie = racine / "site-autonome"
    if sortie.exists():
        shutil.rmtree(sortie)
    (sortie / "assets").mkdir(parents=True)
    (sortie / "pdf").mkdir(parents=True)

    ecrits: list[Path] = []

    chemin_style = sortie / "assets" / "style.css"
    shutil.copyfile(site / "assets" / "style.css", chemin_style)
    ecrits.append(chemin_style)

    # a. Modules ES -> un seul script classique.
    chemin_app = sortie / "assets" / "app.js"
    chemin_app.write_text(_fondre_modules(site / "assets"), encoding="utf-8")
    ecrits.append(chemin_app)

    # b. cours.json embarque en variable globale.
    chemin_donnees = sortie / "assets" / "cours-data.js"
    chemin_donnees.write_text(_donnees_cours(cours), encoding="utf-8")
    ecrits.append(chemin_donnees)

    # c. Reservoir des items de tous les chapitres (pour la seance, sans fetch).
    reservoir = _rendre_reservoir(cours)

    noms_pages = ["index.html"] + [
        f"chapitre-{c['num']}.html" for c in cours["chapitres"]
    ]
    for nom in noms_pages:
        page = (site / nom).read_text(encoding="utf-8")
        page = _classiciser_scripts(page, nom)
        if nom == "index.html":
            page = _inserer_reservoir(page, reservoir)
        chemin = sortie / nom
        chemin.write_text(page, encoding="utf-8")
        ecrits.append(chemin)

    # Les sept fiches PDF (deja produites/versionnees dans site/pdf/, cf.
    # outils/pdf.py) : simple copie, jamais regenerees ici (pas de Chrome
    # invoque par ce module).
    for pdf in sorted((site / "pdf").glob("*.pdf")):
        chemin = sortie / "pdf" / pdf.name
        shutil.copyfile(pdf, chemin)
        ecrits.append(chemin)

    chemin_lisez_moi = sortie / "LISEZ-MOI.txt"
    chemin_lisez_moi.write_text(_LISEZ_MOI, encoding="utf-8")
    ecrits.append(chemin_lisez_moi)

    return ecrits


def _fondre_modules(dossier_assets: Path) -> str:
    """(a) Fond les cinq modules ES en un seul script classique.

    Chaque module est enveloppe dans sa propre IIFE (portee privee) : sans
    elle, deux `const JOUR_MS` identiques mais jamais exportes
    (planificateur.js et interface.js -- aucune collision en modules ES,
    chacun dans son propre scope de module) se retrouveraient dans le MEME
    scope global une fois concatenes tels quels, et leveraient une
    SyntaxError ("Identifier 'JOUR_MS' has already been declared") au
    chargement. Seuls les noms EXPORTES (verifies uniques entre les cinq
    fichiers) sont hisses au scope global, par une destructuration, dans
    l'ordre de dependance ci-dessus (ORDRE_MODULES).
    """
    morceaux = [
        _envelopper_module(nom, (dossier_assets / nom).read_text(encoding="utf-8"))
        for nom in ORDRE_MODULES
    ]
    return "\n".join(morceaux) + "\n"


def _envelopper_module(nom: str, source: str) -> str:
    corps = _RE_IMPORT.sub("", source)
    noms_exportes: list[str] = []

    def _capter_fonction_async(m):
        noms_exportes.append(m.group(1))
        return f"async function {m.group(1)}"

    def _capter_fonction(m):
        noms_exportes.append(m.group(1))
        return f"function {m.group(1)}"

    def _capter_const(m):
        noms_exportes.append(m.group(1))
        return f"const {m.group(1)}"

    corps = _RE_EXPORT_ASYNC_FUNCTION.sub(_capter_fonction_async, corps)
    corps = _RE_EXPORT_FUNCTION.sub(_capter_fonction, corps)
    corps = _RE_EXPORT_CONST.sub(_capter_const, corps)

    if nom == "interface.js":
        corps = _adapter_interface(corps)

    if nom == "app.js":
        # app.js n'exporte rien : simple point d'entree
        # (demarrer(document, window.localStorage)) -- pas d'IIFE, execute
        # directement au niveau global, apres tous les autres.
        return corps.rstrip() + "\n"

    espace = "__module_" + nom[: -len(".js")].replace("-", "_")
    liste = ", ".join(noms_exportes)
    return (
        f"const {espace} = (function () {{\n"
        f"{corps}"
        f"  return {{ {liste} }};\n"
        f"}})();\n"
        f"const {{ {liste} }} = {espace};\n"
    )


# Bornes des deux blocs de interface.js que (b) et (c) doivent remplacer.
# Regex non gourmandes plutot que de longues chaines litterales : moins
# fragile a une reindentation ou un commentaire retouche dans interface.js,
# et une seule occurrence attendue est verifiee explicitement (_RE_IMPORT
# et les remplacements ci-dessous levent sinon une erreur explicite plutot
# que de produire un site-autonome silencieusement casse).
_RE_CHARGER_COURS = re.compile(
    # Englobe aussi le commentaire qui precede la fonction (il decrit le
    # chemin relatif utilise par le fetch qu'on retire -- le laisser tel
    # quel decrirait un mecanisme qui n'existe plus dans ce fichier).
    r"// Chemin relatif a la page.*?function chargerCours\(surSucces\) \{.*?\n\}",
    re.DOTALL,
)
# La recuperation d'une page de chapitre par fetch (accueil de site/ seulement) :
# de `const pagesChapitre` a la fin de `chargerPageChapitre`.
_RE_PAGE_CHAPITRE = re.compile(
    r"    const pagesChapitre = new Map\(\);.*?return pagesChapitre\.get\(numero\);\n    \}\n",
    re.DOTALL,
)

_NOUVEAU_CHARGER_COURS = """\
function chargerCours(surSucces) {
  // Variante autonome (outils/empaqueter.py) : plus de requete reseau --
  // assets/cours-data.js, charge juste avant ce script (cf.
  // _classiciser_scripts), affecte deja le contenu du cours a
  // window.COURS_JSON. Meme contrat que la version reseau qu'il remplace :
  // asynchrone, tolerant a l'absence de la variable (le quiz se degrade
  // sans correction automatique ; cartes et pastilles restent
  // fonctionnelles, elles ne dependent pas de cette donnee).
  return Promise.resolve().then(() => {
    if (window.COURS_JSON) surSucces(window.COURS_JSON);
  });
}"""

_NOUVEAU_PAGE_CHAPITRE = """\
    // Variante autonome (outils/empaqueter.py) : plus de page de chapitre a
    // recuperer (impossible en file://). Les modeles d'exercice sont TOUJOURS
    // dans un reservoir local ([data-reservoir]) : celui de la page d'un chapitre,
    // ou #reservoir-seance sur l'accueil, depose a la construction avec
    // EXACTEMENT le balisage que outils/construire.py (_rendre_volet) produit.
    // Meme fonctions de rendu : l'identite entre un item de seance et sa page de
    // chapitre reste garantie par construction, pas par une copie a resynchroniser.
    function chargerPageChapitre() {
      return Promise.resolve(null);
    }
"""


def _adapter_interface(corps: str) -> str:
    """(b) et (c), appliquees au module interface.js (deja depouille de ses
    import/export par _envelopper_module -- les deux blocs cibles n'en
    portaient de toute facon aucun)."""
    corps, n = _RE_CHARGER_COURS.subn(_NOUVEAU_CHARGER_COURS, corps, count=1)
    if n != 1:
        raise ValueError(
            "empaqueter.py : fonction chargerCours introuvable dans interface.js "
            "-- le fichier source a change, ce module doit etre mis a jour."
        )

    corps, n = _RE_PAGE_CHAPITRE.subn(_NOUVEAU_PAGE_CHAPITRE, corps, count=1)
    if n != 1:
        raise ValueError(
            "empaqueter.py : bloc chargerPageChapitre introuvable dans "
            "interface.js -- le fichier source a change, ce module doit "
            "etre mis a jour."
        )

    return corps


def _donnees_cours(cours: dict) -> str:
    """(b) contenu/cours.json, embarque en variable globale.

    ensure_ascii=True : ce fichier est charge comme script CLASSIQUE, sans
    metadonnee d'encodage propre (a la difference d'un document HTML, qui
    porte <meta charset="utf-8">) -- echapper les caracteres non-ASCII en
    \\uXXXX evite toute ambiguite de charset a l'ouverture en file://.
    """
    return f"window.COURS_JSON = {json.dumps(cours, ensure_ascii=True)};\n"


def _rendre_reservoir(cours: dict) -> str:
    """(c) Balisage de tous les items de tous les chapitres, pour que la
    seance du jour puisse s'y cloner sans telecharger chapitre-N.html.

    hidden + aria-hidden="true" : `[hidden] { display: none !important; }`
    (site/assets/style.css, section 2) le masque a l'ecran ET a l'impression
    quel que soit le media -- regle globale, !important, deja en place pour
    tout le reste du site. Un element display:none n'entre jamais dans le
    controle de debordement (outils/verifier_mobile.py ignore tout ce dont
    getComputedStyle().display === 'none', et un element de largeur/hauteur
    nulle est egalement ignore par ses autres controles).
    """
    morceaux = []
    for chapitre in cours["chapitres"]:
        for cle, source in EXERCICES:
            if chapitre.get(source):
                morceaux.append(_rendre_volet(cle, chapitre))
    return (
        '<div id="reservoir-seance" data-reservoir hidden aria-hidden="true">'
        + "".join(morceaux)
        + "</div>"
    )


def _classiciser_scripts(page: str, nom: str) -> str:
    """(a) Remplace <script type="module" src="assets/app.js"> par deux
    <script> classiques (cours-data.js d'abord, app.js ensuite -- l'ordre
    des balises garantit que window.COURS_JSON existe deja quand app.js
    s'execute, les scripts classiques s'executant dans l'ordre du document)."""
    n = page.count(BALISE_SCRIPT_MODULE)
    if n != 1:
        raise ValueError(
            f"{nom} : {n} occurrence(s) de {BALISE_SCRIPT_MODULE!r} (1 attendue) -- "
            "gabarits/base.html a-t-il change sans mise a jour de ce module ?"
        )
    return page.replace(BALISE_SCRIPT_MODULE, BALISES_SCRIPT_CLASSIQUES, 1)


def _inserer_reservoir(page: str, reservoir: str) -> str:
    """(c) Depose le reservoir juste avant les <script>, donc deja present
    dans le DOM quand ils s'executent (comme le reste du corps de la page)."""
    n = page.count(BALISES_SCRIPT_CLASSIQUES)
    if n != 1:
        raise ValueError(
            f"index.html : {n} occurrence(s) des balises classiques (1 attendue) -- "
            "appeler _classiciser_scripts avant _inserer_reservoir."
        )
    return page.replace(
        BALISES_SCRIPT_CLASSIQUES, reservoir + "\n" + BALISES_SCRIPT_CLASSIQUES, 1
    )


if __name__ == "__main__":
    for chemin in empaqueter(Path(__file__).resolve().parents[1]):
        print(chemin)
