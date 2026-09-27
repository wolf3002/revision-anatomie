"""cours.json -> fiches HTML imprimables (une par chapitre).

Ce module ne connait ni la geometrie des planches (outils/planches.py) ni la
mise en page du site interactif (outils/construire.py) : il assemble le
gabarit gabarits/fiche.html a partir des memes donnees, pour un usage
different -- une fiche papier a completer a la main, pas une page web.

Regle absolue reprise du site (site/assets/style.css section 8) : rien ne
s'affiche avant d'avoir ete cherche, et sur papier "cache" veut dire ABSENT du
document, pas seulement masque par CSS -- il n'y a personne pour cliquer un
bouton "reveler" une fois la page imprimee. D'ou une difference deliberee avec
construire.py : la reponse d'une carte, l'explication d'un quiz, le libelle
d'une pastille ou la valeur d'un muscle ne sont jamais ecrits dans le HTML des
sections d'exercice, uniquement dans la section corrige en fin de document.
"""

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Reutilisation directe -- pas de reecriture :
# - _rendre_planche produit exactement le meme SVG que le site (trace +
#   pastilles + libelles) ; le corrige l'appelle tel quel, la version muette
#   lui retire seulement la couche de texte (voir _rendre_planche_muette).
# - _rendre_volet("muscles", ...) produit la table de reference complete,
#   valeurs visibles : exactement ce qu'il faut pour le corrige.
# - _src produit le renvoi "slide N" / "[hors cours]", identique partout.
from outils.construire import _rendre_planche, _rendre_volet, _src  # noqa: E402

# Un <text class="pastille__t" ...>Libelle</text> genere par _rendre_planche.
# html.escape() empeche tout "<" litteral dans Libelle : le "." non-greedy ne
# peut donc pas deborder sur une balise suivante.
_RE_LIBELLE_PASTILLE = re.compile(r'<text class="pastille__t"[^>]*>.*?</text>')


def construire_fiches(racine: Path) -> list[Path]:
    racine = Path(racine)
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))
    gabarit = (racine / "gabarits" / "fiche.html").read_text(encoding="utf-8")

    sortie = racine / "site" / "pdf"
    sortie.mkdir(parents=True, exist_ok=True)

    ecrits = []
    for chapitre in cours["chapitres"]:
        corps = _rendre_fiche(chapitre)
        titre = f"Fiche {chapitre['num']:02d} — {html.escape(chapitre['titre'])}"
        page = gabarit.replace("{{titre}}", titre).replace("{{corps}}", corps)
        chemin = sortie / f"fiche-{chapitre['num']:02d}.html"
        chemin.write_text(page, encoding="utf-8")
        ecrits.append(chemin)
    return ecrits


def _rendre_fiche(chapitre):
    return (
        _rendre_entete(chapitre)
        + _rendre_exercices(chapitre)
        + _rendre_corrige(chapitre)
    )


def _rendre_entete(chapitre):
    num = chapitre["num"]
    titre = html.escape(chapitre["titre"])
    debut, fin = chapitre["slides"]
    return (
        '<header class="fiche-entete">'
        f'<span class="fiche-entete__num">Ch. {num}</span>'
        f"<h1>{titre}</h1>"
        f'<span class="fiche-entete__slides">slides {debut}–{fin}</span>'
        "</header>"
    )


def _section(titre, cle, corps):
    return (
        f'<section class="fiche-section" data-section="{cle}">'
        f"<h2>{html.escape(titre)}</h2>{corps}</section>"
    )


def _rendre_exercices(chapitre):
    sections = ""
    if chapitre.get("planches"):
        corps = "".join(_rendre_planche_muette(p) for p in chapitre["planches"])
        sections += _section("Planches (mode muet)", "planches", corps)
    if chapitre.get("cartes") or chapitre.get("quiz"):
        corps = "".join(_rendre_carte_recto(c) for c in chapitre.get("cartes", []))
        corps += "".join(_rendre_quiz_enonce(q) for q in chapitre.get("quiz", []))
        sections += _section("Questions", "questions", corps)
    if chapitre.get("muscles"):
        corps = _rendre_table_muscles_vide(chapitre["muscles"])
        sections += _section("Table musculaire à compléter", "muscles", corps)
    if chapitre.get("pieges"):
        corps = "".join(_rendre_piege(p) for p in chapitre["pieges"])
        sections += _section("Pièges", "pieges", corps)
    return sections


# --- 1. Planches en mode muet ------------------------------------------


def _largeur_figure_mm(planche, hauteur_mm=68):
    # Le viewBox fixe le rapport largeur/hauteur (contenu/schema.py valide son
    # format) ; on en deduit une largeur pour une hauteur cible commune, avec
    # des bornes pour qu'une planche tres large (ex. 620x460) ne deborde pas
    # la largeur imprimable et qu'une planche tres etroite (ex. 260x620)
    # garde une taille lisible.
    _, _, largeur, hauteur = (float(v) for v in planche["vb"].split())
    return min(150, max(45, round(hauteur_mm * largeur / hauteur)))


def _rendre_planche_muette(planche):
    # Meme trace, memes pastilles que le site (appel direct, non modifie) ;
    # seule la couche <text> du libelle est retiree, cf. docstring du module.
    svg = _RE_LIBELLE_PASTILLE.sub("", _rendre_planche(planche))
    svg = svg.replace('data-mode="legende"', 'data-mode="muet"')
    legende = "".join(_rendre_case_legende(p) for p in planche["pastilles"])
    largeur = _largeur_figure_mm(planche)
    return (
        '<div class="fiche-planche">'
        f'<div class="fiche-planche__figure" style="width:{largeur}mm">{svg}</div>'
        f'<ol class="fiche-legende">{legende}</ol>'
        "</div>"
    )


def _rendre_case_legende(pastille):
    indice = (
        f'<span class="fiche-legende__indice">({html.escape(pastille["indice"])})</span>'
        if pastille.get("indice")
        else ""
    )
    return (
        f'<li><span class="fiche-legende__n">{pastille["n"]}.</span>'
        f"{indice}"
        '<span class="fiche-legende__trait"></span></li>'
    )


# --- 2. Questions : recto des cartes et enonces de QCM -------------------


def _rendre_plan_texte(plan):
    if not plan:
        return ""
    return f'<span class="fiche-plan">plan {html.escape(plan)}</span>'


def _rendre_carte_recto(carte):
    return (
        f'<article class="fiche-carte" id="{html.escape(carte["id"])}">'
        f'<p class="fiche-carte__q">{html.escape(carte["q"])}</p>'
        f"{_rendre_plan_texte(carte.get('plan'))}"
        f"{_src(carte)}"
        '<div class="fiche-carte__reponse-trait"></div>'
        "</article>"
    )


def _rendre_quiz_enonce(question):
    choix = "".join(f"<li>{html.escape(t)}</li>" for t in question["choix"])
    return (
        f'<article class="fiche-quiz" id="{html.escape(question["id"])}">'
        f'<p class="fiche-quiz__q">{html.escape(question["q"])}</p>'
        f'<ol class="fiche-quiz__choix" type="A">{choix}</ol>'
        f"{_rendre_plan_texte(question.get('plan'))}"
        f"{_src(question)}"
        "</article>"
    )


# --- 3. Table musculaire a completer -------------------------------------


def _rendre_table_muscles_vide(muscles):
    lignes = "".join(
        "<tr>"
        f"<th>{html.escape(m['nom'])} {_src(m)}</th>"
        '<td class="fiche-muscle__case"></td>'
        '<td class="fiche-muscle__case"></td>'
        '<td class="fiche-muscle__case"></td>'
        "</tr>"
        for m in muscles
    )
    return (
        '<table class="fiche-muscles">'
        "<caption>Table musculaire</caption>"
        "<thead><tr>"
        '<th scope="col">Muscle</th>'
        '<th scope="col">Origine</th>'
        '<th scope="col">Terminaison</th>'
        '<th scope="col">Action</th>'
        "</tr></thead>"
        f"<tbody>{lignes}</tbody>"
        "</table>"
    )


# --- 4. Pieges : affiches en clair ----------------------------------------


def _rendre_piege(piege):
    return (
        '<article class="fiche-piege">'
        '<span class="fiche-piege__etiquette">Piège</span>'
        f'<p class="fiche-piege__titre">{html.escape(piege["titre"])}</p>'
        f"<p>{html.escape(piege['texte'])}</p>"
        f"{_src(piege)}"
        "</article>"
    )


# --- 5. Corrige : en fin de document, jamais en regard --------------------


def _rendre_corrige(chapitre):
    blocs = ""
    if chapitre.get("planches"):
        # Pas de colonne de legende ici (la reponse est deja ecrite sur le
        # dessin) : chaque planche n'occupe que sa propre largeur, plusieurs
        # cote a cote quand elles sont etroites, au lieu d'etirer une boite
        # pleine largeur autour d'une petite image (ce que ferait .fiche-
        # planche, pense pour la paire figure+legende du mode muet).
        figures = "".join(
            '<div class="fiche-corrige__planche" '
            f'style="width:{_largeur_figure_mm(p, hauteur_mm=95)}mm">'
            f"{_rendre_planche(p)}</div>"
            for p in chapitre["planches"]
        )
        blocs += (
            f'<h3>Planches</h3><div class="fiche-corrige__planches">{figures}</div>'
        )
    if chapitre.get("cartes"):
        blocs += "<h3>Cartes</h3>" + "".join(
            _rendre_corrige_carte(c) for c in chapitre["cartes"]
        )
    if chapitre.get("quiz"):
        blocs += "<h3>Quiz</h3>" + "".join(
            _rendre_corrige_quiz(q) for q in chapitre["quiz"]
        )
    if chapitre.get("muscles"):
        # Pas de <h3> ici : la <caption> du tableau reutilise (construire.
        # _rendre_volet) porte deja "Table musculaire", un second titre
        # identique juste au-dessus serait une repetition sans valeur.
        blocs += _rendre_volet(
            "muscles", {"num": chapitre["num"], "muscles": chapitre["muscles"]}
        )
    return (
        '<section class="fiche-corrige" data-section="corrige">'
        '<h2 class="fiche-corrige__titre">Corrigé</h2>'
        f"{blocs}</section>"
    )


def _rendre_corrige_carte(carte):
    return (
        '<article class="fiche-corrige__carte">'
        f'<p class="fiche-corrige__q">{html.escape(carte["q"])}</p>'
        f'<p class="fiche-corrige__r">{html.escape(carte["r"])}</p>'
        f"{_rendre_plan_texte(carte.get('plan'))}"
        f"{_src(carte)}"
        "</article>"
    )


def _rendre_corrige_quiz(question):
    choix = "".join(
        f'<li class="fiche-corrige__bonne">{html.escape(t)}</li>'
        if i == question["bonne"]
        else f"<li>{html.escape(t)}</li>"
        for i, t in enumerate(question["choix"])
    )
    return (
        '<article class="fiche-corrige__quiz">'
        f'<p class="fiche-corrige__q">{html.escape(question["q"])}</p>'
        f'<ol type="A">{choix}</ol>'
        f'<p class="fiche-corrige__expl">{html.escape(question["expl"])}</p>'
        f"{_rendre_plan_texte(question.get('plan'))}"
        f"{_src(question)}"
        "</article>"
    )


if __name__ == "__main__":
    for chemin in construire_fiches(Path(__file__).resolve().parents[1]):
        print(chemin)
