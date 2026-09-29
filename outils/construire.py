"""cours.json -> pages HTML statiques.

Le generateur ne connait ni la geometrie des planches ni le contenu du cours :
il assemble des gabarits. Toute assertion publiee porte son numero de slide.
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

# Permet `python3 outils/construire.py` (execution directe, sys.path[0] =
# outils/) comme `python3 -m outils.construire` (racine deja sur le path) :
# sans cette ligne, seule la seconde forme resout l'import ci-dessous.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# La table de decalage vit dans contenu/schema.py, pas ici : le validateur s'en sert
# pour verifier qu'un libelle decale ne sort pas du viewBox. Une seule definition,
# donc aucune derive possible entre ce qui est valide et ce qui est rendu.
from contenu.schema import DECALAGE_LIBELLE  # noqa: E402

# Deux groupes, dans l'ordre ou on les traverse : on ne peut pas retrouver en
# memoire ce qu'on n'y a jamais mis, donc on LIT d'abord (Apprendre), on se
# TESTE ensuite (Se tester). Le premier onglet du premier groupe est celui qui
# s'ouvre : c'est la fiche, jamais un exercice.
#
# - Apprendre : rien n'y est masque. La fiche est le cours a lire, avec ses
#   planches deja legendees et (ch. 5 a 7) la table musculaire en valeurs
#   lisibles. Les pieges sont deja lus DANS la fiche, au moment ou la notion
#   est traitee ; leur onglet les regroupe pour une relecture avant de se
#   tester. Un piege n'est pas un exercice : contrairement a une carte ou a
#   une explication de quiz, son contenu est affiche d'emblee, jamais masque
#   -- lire un piege avant de se tromper a un sens, le "cacher" derriere une
#   tentative n'en aurait aucun.
# - Se tester : c'est la, et seulement la, que « aucune reponse avant
#   tentative » s'applique (cartes, quiz, planches muettes, muscles a
#   completer). L'ordre relatif de ces quatre exercices est celui d'avant.
GROUPES = (
    (
        "apprendre",
        "Apprendre",
        (
            ("fiche", "Fiche", "sections"),
            ("pieges", "Pièges", "pieges"),
        ),
    ),
    (
        "tester",
        "Se tester",
        (
            ("planche", "Planche", "planches"),
            ("cartes", "Cartes", "cartes"),
            ("quiz", "Quiz", "quiz"),
            ("muscles", "Muscles", "muscles"),
        ),
    ),
)

# Vue a plat des onglets, dans l'ordre d'affichage (cle, libelle, source) :
# derivee de GROUPES, jamais redefinie a la main.
ONGLETS = tuple(onglet for _, _, onglets in GROUPES for onglet in onglets)

# Au-dela, le plan de la fiche est replie a la construction : 27 ou 44 entrees
# ouvertes repoussent la premiere section d'un ecran entier.
PLAN_OUVERT_JUSQU_A = 12


def construire(racine: Path) -> list[Path]:
    racine = Path(racine)
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))
    base = (racine / "gabarits" / "base.html").read_text(encoding="utf-8")
    gabarit = (racine / "gabarits" / "chapitre.html").read_text(encoding="utf-8")
    gabarit_accueil = (racine / "gabarits" / "accueil.html").read_text(encoding="utf-8")

    sortie = racine / "site"
    (sortie / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(racine / "contenu" / "cours.json", sortie / "assets" / "cours.json")

    ecrits = []

    corps_accueil = _rendre_accueil(gabarit_accueil, cours)
    page_accueil = (
        base.replace("{{titre}}", html.escape(cours["meta"]["cours"]))
        .replace("{{racine}}", "")
        .replace("{{corps}}", corps_accueil)
    )
    chemin_accueil = sortie / "index.html"
    chemin_accueil.write_text(page_accueil, encoding="utf-8")
    ecrits.append(chemin_accueil)

    for chapitre in cours["chapitres"]:
        corps = _rendre_chapitre(gabarit, chapitre)
        page = (
            base.replace(
                "{{titre}}",
                f"Chapitre {chapitre['num']} — {html.escape(chapitre['titre'])}",
            )
            .replace("{{racine}}", "")
            .replace("{{corps}}", corps)
        )
        chemin = sortie / f"chapitre-{chapitre['num']}.html"
        chemin.write_text(page, encoding="utf-8")
        ecrits.append(chemin)
    return ecrits


def _rendre_accueil(gabarit, cours):
    chapitres = cours["chapitres"]
    progression = "".join(_rendre_anneau(c) for c in chapitres)
    liste = "".join(_rendre_lien_chapitre(c) for c in chapitres)
    # Le titre annonce le compte REEL de chapitres publies dans cours.json,
    # jamais "les sept" en dur : tant que les chapitres 2 a 7 ne sont pas
    # ecrits (et leurs bornes de slides verifiees dans le PDF -- cf. l'audit
    # du chapitre 1, qui a corrige [7,45] en [7,43]), un titre qui promettrait
    # sept entrees pour une seule affichee se lirait comme un bug.
    titre_chapitres = (
        "Chapitre disponible"
        if len(chapitres) == 1
        else f"Les {len(chapitres)} chapitres disponibles"
    )
    return (
        gabarit.replace("{{cours}}", html.escape(cours["meta"]["cours"]))
        .replace("{{titre_chapitres}}", titre_chapitres)
        .replace("{{progression}}", progression)
        .replace("{{chapitres}}", liste)
    )


def _rendre_anneau(chapitre):
    # Valeurs par defaut cote build : "jamais ouvert" (part=0, dashed). La
    # vraie proportion depend du localStorage -- interface.js la recalcule au
    # chargement et a chaque verdict, en ciblant ce <li> par data-chapitre.
    num = chapitre["num"]
    titre = html.escape(chapitre["titre"])
    return (
        f'<li data-chapitre="{num}" data-etat="vide">'
        '<svg class="anneau" style="--part: 0" viewBox="0 0 48 48" role="img" '
        f'aria-label="Chapitre {num}, {titre} : jamais ouvert">'
        '<circle class="anneau__fond" cx="24" cy="24" r="20" pathLength="100"/>'
        '<circle class="anneau__part" cx="24" cy="24" r="20" pathLength="100"/>'
        "</svg>"
        f'<span class="progression__titre">Ch. {num}</span>'
        '<span class="anneau__valeur mono">jamais ouvert</span>'
        "</li>"
    )


def _rendre_lien_chapitre(chapitre):
    num = chapitre["num"]
    titre = html.escape(chapitre["titre"])
    debut, fin = chapitre["slides"]
    return (
        "<li>"
        f'<a class="chapitre-lien" href="chapitre-{num}.html">'
        f'<span class="chapitre-lien__num mono">{num}</span>'
        f'<span class="chapitre-lien__titre">{titre}</span>'
        f'<span class="chapitre-lien__slides mono">slides {debut}–{fin}</span>'
        "</a></li>"
    )


def _onglets_actifs(chapitre):
    return [(cle, libelle) for cle, libelle, source in ONGLETS if chapitre.get(source)]


def _rendre_barre_onglets(chapitre):
    """Les onglets, en groupes numerotes (1 Apprendre, 2 Se tester).

    Un groupe sans onglet actif n'est pas affiche, et la numerotation suit ce
    qui reste : « 1 » est toujours le premier groupe visible.
    """
    rendu = ""
    rang = 0
    for cle_groupe, libelle_groupe, onglets in GROUPES:
        actifs = [(cle, lib) for cle, lib, source in onglets if chapitre.get(source)]
        if not actifs:
            continue
        rang += 1
        identifiant = f"onglets-{cle_groupe}"
        boutons = "".join(
            f'<button class="onglet" data-onglet="{cle}">{html.escape(libelle)}</button>'
            for cle, libelle in actifs
        )
        rendu += (
            f'<div class="onglets__groupe" data-groupe="{cle_groupe}" role="group" '
            f'aria-labelledby="{identifiant}">'
            f'<span class="onglets__etiquette" id="{identifiant}">'
            f'<span class="onglets__rang mono">{rang}</span>'
            f"{html.escape(libelle_groupe)}</span>"
            f"{boutons}</div>"
        )
    return rendu


def _rendre_volet_titre(cle, libelle):
    """Titre du volet, visible SEULEMENT quand le script n'a pas tourne.

    Sans JavaScript (ou script qui echoue, ex. site/ ouvert en file:// : les
    modules ES n'y sont pas executes), tous les volets se suivent dans la page
    sans que la barre d'onglets, inerte, dise lequel est lequel. Le titre nomme
    chaque section ; interface.js pose la classe `js` sur <html> et le masque, la
    barre d'onglets faisant alors ce travail (voir style.css, §5.2a)."""
    groupe = next(g for _, g, onglets in GROUPES if any(c == cle for c, _, _ in onglets))
    return f'<h2 class="volet__titre">{html.escape(groupe)} · {html.escape(libelle)}</h2>'


def _rendre_chapitre(gabarit, chapitre):
    sections = "".join(
        f'<section class="volet" data-volet="{cle}">'
        f"{_rendre_volet_titre(cle, libelle)}{_rendre_volet(cle, chapitre)}</section>"
        for cle, libelle in _onglets_actifs(chapitre)
    )
    return (
        gabarit.replace("{{num}}", str(chapitre["num"]))
        .replace("{{titre}}", html.escape(chapitre["titre"]))
        .replace(
            "{{slides}}", f"slides {chapitre['slides'][0]}–{chapitre['slides'][1]}"
        )
        .replace("{{onglets}}", _rendre_barre_onglets(chapitre))
        .replace("{{volets}}", sections)
    )


def _src(entree):
    if entree.get("hors_cours"):
        return '<span class="src src--hors">[hors cours]</span>'
    return f'<span class="src">slide {entree["slide"]}</span>'


def _rendre_volet(cle, chapitre):
    if cle == "cartes":
        return "".join(
            f'<article class="carte" id="{html.escape(c["id"])}" '
            f'data-plan="{html.escape(c.get("plan", ""))}">'
            f'<p class="carte__q">{html.escape(c["q"])}</p>'
            f'<p class="carte__r" data-etat="cachee">{html.escape(c["r"])}</p>'
            f"{_src(c)}</article>"
            for c in chapitre["cartes"]
        )
    if cle == "quiz":
        return "".join(
            f'<article class="question" id="{html.escape(q["id"])}">'
            f'<p class="question__q">{html.escape(q["q"])}</p>'
            + "".join(
                f'<button class="choix" data-index="{i}">{html.escape(texte)}</button>'
                for i, texte in enumerate(q["choix"])
            )
            + f'<p class="question__expl" data-etat="cachee">{html.escape(q["expl"])}</p>'
            f"{_src(q)}</article>"
            for q in chapitre["quiz"]
        )
    if cle == "fiche":
        return _rendre_fiche(chapitre)
    if cle == "planche":
        # Conteneur en grille : les planches s'alignent cote a cote quand la place le
        # permet et s'empilent sur telephone. Sans lui, trois planches autonomes
        # s'empilent aussi sur grand ecran et on perd la comparaison des trois plans.
        return (
            '<div class="planches">'
            + "".join(_rendre_planche(p) for p in chapitre["planches"])
            + "</div>"
        )
    if cle == "muscles":
        # style.css (§5.8) attend une <table class="muscles"> complete : caption +
        # thead nommant les 4 colonnes + tbody -- sans eux, la bascule en fiches sous
        # 720px (.muscles tr / .muscles td::before) ne s'applique jamais, et les <tr>
        # nus rendus hors de tout <table> sont du HTML invalide. Le renvoi de slide
        # vit dans ce <th> du nom, pas dans une 4e colonne : la bascule mobile mappe
        # .muscles td:nth-of-type(1/2/3) sur les trois <td> ci-dessous, une colonne
        # de plus la casserait.
        #
        # Defaut Critical corrige ici : origine/terminaison/action vivaient en texte
        # brut, sans aucun mecanisme de masquage ni de saisie -- ouvrir l'onglet
        # exposait toutes les reponses (voir docs/superpowers/plans/2026-09-26-
        # chapitres-2-a-7.md, tache 1). Chaque valeur est desormais enveloppee dans
        # un <span class="muscle__valeur"> : le texte reste present et lisible tel
        # quel (aucun attribut de masquage pose ICI, a la difference du verso d'une
        # carte) -- si le script echoue, la table degrade en simple table de
        # reference. C'est interface.js qui, une fois charge, bascule la table en
        # mode="champs" par defaut : il lit alors le texte de chaque span comme
        # reponse attendue, l'y masque via l'attribut data-mode du <table> (pas du
        # <span>) et injecte un champ de saisie a la place -- jamais l'inverse, sinon
        # la table resterait aveugle sans JavaScript.
        #
        # Le data-id du <tr> porte l'identifiant planifiable {chapitre}#muscle#{nom}
        # (meme formule que celle d'exercices.itemsDuCours, cote JS) : un nom de
        # muscle contient des espaces, invalides dans un attribut id, d'ou data-id
        # plutot que id.
        lignes = "".join(
            f'<tr data-id="{html.escape(f"{chapitre["num"]}#muscle#{m["nom"]}")}">'
            f"<th>{html.escape(m['nom'])} {_src(m)}</th>"
            f'<td><span class="muscle__valeur">{html.escape(" ; ".join(m["origine"]))}</span></td>'
            f'<td><span class="muscle__valeur">{html.escape(" ; ".join(m["terminaison"]))}</span></td>'
            f'<td><span class="muscle__valeur">{html.escape(" ; ".join(m["actions"]))}</span></td></tr>'
            for m in chapitre["muscles"]
        )
        return (
            '<table class="muscles">'
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
    if cle == "pieges":
        return "".join(_rendre_piege(p) for p in chapitre["pieges"])
    return ""


def _rendre_piege(piege):
    return (
        '<article class="piege">'
        '<span class="piege__etiquette">Piège</span>'
        f'<p class="piege__titre">{html.escape(piege["titre"])}</p>'
        f"<p>{html.escape(piege['texte'])}</p>"
        f"{_src(piege)}</article>"
    )


def _isoler_ids(dessin, prefixe):
    """Prefixe chaque id du trace et ses references (url(#id), href="#id").

    Les traces portent un <marker id="fleche"> (pointe de fleche), reference par
    url(#fleche). Deux copies d'une meme planche dans une page -- la fiche et
    l'onglet Planche -- donneraient deux id identiques, et url(#fleche) se
    resout sur le PREMIER du document : celui de la fiche, qui est display:none
    quand on est sur un onglet de test. Le navigateur ne rend pas un marqueur
    defini dans un sous-arbre masque : les pointes de fleche des planches a
    legender disparaissaient (constate par pilotage). Chaque copie a donc ses
    propres id."""
    for identifiant in set(re.findall(r"""\bid=['"]([^'"]+)['"]""", dessin)):
        cible = re.escape(identifiant)
        dessin = re.sub(
            rf"""(\bid=['"]){cible}(['"])""", rf"\g<1>{prefixe}{identifiant}\g<2>", dessin
        )
        dessin = re.sub(
            rf"url\(\s*#{cible}\s*\)", f"url(#{prefixe}{identifiant})", dessin
        )
        dessin = re.sub(
            rf"""(href=['"])#{cible}(['"])""", rf"\g<1>#{prefixe}{identifiant}\g<2>", dessin
        )
    return dessin


def _svg_planche(planche, prefixe_id=""):
    """Le trace et ses pastilles legendees : partage par l'onglet Planche, la
    fiche de lecture et les fiches PDF (outils/fiches.py), qui n'en different
    que par l'enveloppe. Une seule production du SVG, donc aucune derive
    possible entre ce qu'on lit et ce qu'on doit ensuite legender.

    `prefixe_id` isole les id du trace (voir _isoler_ids) : vide pour l'onglet
    Planche et les PDF, dont le rendu reste octet pour octet celui d'avant."""
    pastilles = ""
    for p in planche["pastilles"]:
        dx, dy = DECALAGE_LIBELLE[p["ancre"]]
        indice = f' data-indice="{html.escape(p["indice"])}"' if p.get("indice") else ""
        pastilles += (
            f'<g class="pastille" data-n="{p["n"]}" '
            f'data-plan="{html.escape(p.get("plan", ""))}"{indice}>'
            f'<circle cx="{p["x"]}" cy="{p["y"]}" r="9"/>'
            f'<text class="pastille__n" x="{p["x"]}" y="{p["y"] + 4}" '
            f'text-anchor="middle">{p["n"]}</text>'
            f'<text class="pastille__t" x="{p["x"] + dx}" y="{p["y"] + dy}" '
            f'text-anchor="{p["ancre"]}">{html.escape(p["t"])}</text></g>'
        )
    dessin = _isoler_ids(planche["dessin"], prefixe_id) if prefixe_id else planche["dessin"]
    return f'<svg viewBox="{planche["vb"]}" role="img">{dessin}{pastilles}</svg>'


def _rendre_planche(planche):
    return (
        f'<figure class="planche" id="{html.escape(planche["id"])}" data-mode="legende">'
        f"<figcaption>{html.escape(planche['titre'])} {_src(planche)}</figcaption>"
        f"{_svg_planche(planche)}"
        f"</figure>"
    )


# --- La fiche : le cours a lire, rien de masque --------------------------------
#
# Contrairement aux onglets de test, la fiche n'a AUCUN mecanisme de masquage
# et ne partage avec eux aucun identifiant ni aucune classe qu'interface.js
# equipe :
#   - ses figures sont des .planche-fiche (pas des .planche) : interface.js n'y
#     cree ni champ de saisie ni bouton, la bascule muet/legende ne les touche
#     pas, et la seance du jour ne peut pas cloner la mauvaise ;
#   - ses figures n'ont pas d'id, et sa table de muscles (.table-ref, pas
#     .muscles) pas de data-id : page.getElementById / tr[data-id], que la
#     seance du jour utilise pour retrouver un item dans la page d'un
#     chapitre, ne tombent jamais dessus -- la fiche est le PREMIER volet du
#     DOM, elle gagnerait toujours sur un id en double.
# Ce qui s'y trouve est donc, par construction, en lecture seule.


def _section_pour(sections, slide):
    """Indice de la section qui traite `slide` : la derniere dont le slide est
    inferieur ou egal ; a defaut (entree anterieure a la premiere section), la
    premiere. Une entree sans slide ([hors cours]) va a la derniere."""
    if not isinstance(slide, int):
        return len(sections) - 1
    candidats = [(s["slide"], i) for i, s in enumerate(sections) if s["slide"] <= slide]
    return max(candidats)[1] if candidats else 0


def _rendre_figure_fiche(planche, numero):
    # Numero explicite (rang dans chapitre["planches"]) et non un compteur CSS :
    # la fiche range les figures par section, dans l'ordre du cours, qui n'est
    # pas toujours celui de la liste -- « Pl. 02 » doit designer la meme planche
    # ici et dans l'onglet Planche.
    return (
        '<figure class="planche-fiche">'
        f'<figcaption data-num="{numero:02d}">'
        f"{html.escape(planche['titre'])} {_src(planche)}</figcaption>"
        f"{_svg_planche(planche, prefixe_id=f'fiche-pl{numero:02d}-')}"
        "</figure>"
    )


def _rendre_section_fiche(numero, section, figures, pieges):
    identifiant = f"fiche-s{numero}"
    corps = "".join(f"<li>{html.escape(pt)}</li>" for pt in section["points"])
    return (
        f'<section class="fiche-section" id="{identifiant}" '
        f'aria-labelledby="{identifiant}-titre">'
        '<header class="fiche-section__tete">'
        f'<h2 id="{identifiant}-titre">'
        f'<span class="fiche-section__n mono">{numero:02d}</span>'
        f'{html.escape(section["titre"])}</h2>'
        f"{_src(section)}</header>"
        f'<ul class="fiche-points">{corps}</ul>'
        + (f'<div class="fiche-figures">{"".join(figures)}</div>' if figures else "")
        + "".join(pieges)
        + "</section>"
    )


def _rendre_table_reference(chapitre):
    # Valeurs en clair, jamais de champ : c'est la table de lecture. Meme
    # structure que la table a completer (caption remplacee par un titre de
    # section, meme ordre des colonnes) pour que la bascule en fiches sous
    # 720 px, qui mappe td:nth-of-type(1/2/3), s'applique a l'identique.
    identifiant = "fiche-muscles"
    numero = len(chapitre["sections"]) + 1
    lignes = "".join(
        f"<tr><th>{html.escape(m['nom'])} {_src(m)}</th>"
        f"<td>{html.escape(' ; '.join(m['origine']))}</td>"
        f"<td>{html.escape(' ; '.join(m['terminaison']))}</td>"
        f"<td>{html.escape(' ; '.join(m['actions']))}</td></tr>"
        for m in chapitre["muscles"]
    )
    return (
        f'<section class="fiche-section" id="{identifiant}" '
        f'aria-labelledby="{identifiant}-titre">'
        '<header class="fiche-section__tete">'
        f'<h2 id="{identifiant}-titre">'
        f'<span class="fiche-section__n mono">{numero:02d}</span>'
        "Table musculaire</h2></header>"
        f'<table class="table-ref" aria-labelledby="{identifiant}-titre">'
        "<thead><tr>"
        '<th scope="col">Muscle</th>'
        '<th scope="col">Origine</th>'
        '<th scope="col">Terminaison</th>'
        '<th scope="col">Action</th>'
        "</tr></thead>"
        f"<tbody>{lignes}</tbody>"
        "</table></section>"
    )


def _rendre_plan(chapitre):
    sections = chapitre["sections"]
    entrees = [
        (f"fiche-s{i}", f"{i:02d}", s["titre"]) for i, s in enumerate(sections, 1)
    ]
    if chapitre.get("muscles"):
        entrees.append(("fiche-muscles", f"{len(sections) + 1:02d}", "Table musculaire"))
    liste = "".join(
        f'<li><a href="#{cible}"><span class="mono">{n}</span>{html.escape(titre)}</a></li>'
        for cible, n, titre in entrees
    )
    ouvert = " open" if len(entrees) <= PLAN_OUVERT_JUSQU_A else ""
    return (
        f'<details class="plan"{ouvert}>'
        f'<summary>Plan du chapitre <span class="mono">{len(entrees)} sections</span></summary>'
        f'<ol class="plan__liste">{liste}</ol>'
        "</details>"
    )


def _rendre_fiche(chapitre):
    """Le cours a lire : plan, puis chaque section avec ses points, la (ou les)
    planche(s) legendee(s) et les pieges de la notion la ou elle est traitee,
    puis (ch. 5 a 7) la table musculaire en reference.

    Le rattachement d'une planche ou d'un piege a sa section ne repose sur
    aucune donnee de plus dans cours.json : chacun porte deja son slide, et la
    section qui le traite est la derniere dont le slide ne le depasse pas.
    """
    sections = chapitre["sections"]
    figures = {}
    for numero, planche in enumerate(chapitre.get("planches", []), 1):
        indice = _section_pour(sections, planche.get("slide"))
        figures.setdefault(indice, []).append(_rendre_figure_fiche(planche, numero))
    pieges = {}
    for piege in chapitre.get("pieges", []):
        indice = _section_pour(sections, piege.get("slide"))
        pieges.setdefault(indice, []).append(_rendre_piege(piege))

    rendu = _rendre_plan(chapitre)
    for indice, section in enumerate(sections):
        rendu += _rendre_section_fiche(
            indice + 1, section, figures.get(indice, []), pieges.get(indice, [])
        )
    if chapitre.get("muscles"):
        rendu += _rendre_table_reference(chapitre)
    return rendu


if __name__ == "__main__":
    for chemin in construire(Path(__file__).resolve().parents[1]):
        print(chemin)
