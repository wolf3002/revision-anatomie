"""cours.json -> pages HTML statiques.

Le generateur ne connait ni la geometrie des planches ni le contenu du cours :
il assemble des gabarits. Toute assertion publiee porte son numero de slide.
"""

import html
import json
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

ONGLETS = (
    ("planche", "Planche", "planches"),
    ("cartes", "Cartes", "cartes"),
    ("quiz", "Quiz", "quiz"),
    # Piege = mise en garde, pas un exercice : place apres le quiz (on vient
    # de se tester) et avant les volets de reference (Muscles, Le cours).
    # Contrairement a une carte ou une explication de quiz, son contenu est
    # affiche d'emblee, jamais masque -- lire un piege avant de se tromper a
    # un sens, le "cacher" derriere une tentative n'en aurait aucun.
    ("pieges", "Pièges", "pieges"),
    ("muscles", "Muscles", "muscles"),
    ("cours", "Le cours", "sections"),
)


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


def _rendre_chapitre(gabarit, chapitre):
    barre = "".join(
        f'<button class="onglet" data-onglet="{cle}">{html.escape(libelle)}</button>'
        for cle, libelle in _onglets_actifs(chapitre)
    )
    sections = "".join(
        f'<section class="volet" data-volet="{cle}">{_rendre_volet(cle, chapitre)}</section>'
        for cle, _ in _onglets_actifs(chapitre)
    )
    return (
        gabarit.replace("{{num}}", str(chapitre["num"]))
        .replace("{{titre}}", html.escape(chapitre["titre"]))
        .replace(
            "{{slides}}", f"slides {chapitre['slides'][0]}–{chapitre['slides'][1]}"
        )
        .replace("{{onglets}}", barre)
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
    if cle == "cours":
        return "".join(
            f'<section class="notion"><h3>{html.escape(s["titre"])}</h3><ul>'
            + "".join(f"<li>{html.escape(p)}</li>" for p in s["points"])
            + f"</ul>{_src(s)}</section>"
            for s in chapitre["sections"]
        )
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
        lignes = "".join(
            f"<tr><th>{html.escape(m['nom'])} {_src(m)}</th>"
            f"<td>{html.escape(' ; '.join(m['origine']))}</td>"
            f"<td>{html.escape(' ; '.join(m['terminaison']))}</td>"
            f"<td>{html.escape(' ; '.join(m['actions']))}</td></tr>"
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
        return "".join(
            '<article class="piege">'
            '<span class="piege__etiquette">Piège</span>'
            f'<p class="piege__titre">{html.escape(p["titre"])}</p>'
            f'<p>{html.escape(p["texte"])}</p>'
            f"{_src(p)}</article>"
            for p in chapitre["pieges"]
        )
    return ""


def _rendre_planche(planche):
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
    return (
        f'<figure class="planche" id="{html.escape(planche["id"])}" data-mode="legende">'
        f"<figcaption>{html.escape(planche['titre'])} {_src(planche)}</figcaption>"
        f'<svg viewBox="{planche["vb"]}" role="img">{planche["dessin"]}{pastilles}</svg>'
        f"</figure>"
    )


if __name__ == "__main__":
    for chemin in construire(Path(__file__).resolve().parents[1]):
        print(chemin)
