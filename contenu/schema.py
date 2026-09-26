"""Validation du contenu du cours.

Le PDF du cours fait foi. Ce module refuse tout contenu qui ne renvoie pas a
une slide verifiable, et toute planche dont le trace contient deja ses
etiquettes -- ce qui rendrait le mode muet impossible.
"""

CHAMPS_CARTE = ("id", "q", "r")
CHAMPS_QUIZ = ("id", "q", "choix", "bonne", "expl")
CHAMPS_MUSCLE = ("nom", "origine", "terminaison", "actions")

# Decalage du libelle par rapport a sa pastille, selon l'ancrage.
# 'middle' pose le texte SOUS la pastille : le decaler horizontalement le ferait
# passer par-dessus, le texte etant centre sur son point d'ancrage.
DECALAGE_LIBELLE = {"start": (14, 4), "end": (-14, 4), "middle": (0, 24)}
ANCRES_VALIDES = set(DECALAGE_LIBELLE)

# Les trois seules teintes du site (regle CSS section 1) ; une pastille sans
# plan (chaine vide, ex. termes-localisation) reste valide -- elle ne porte
# simplement aucune teinte.
PLANS_VALIDES = {"", "frontal", "sagittal", "transversal"}


def valider_cours(cours):
    erreurs = []
    vus = set()
    for chapitre in cours.get("chapitres", []):
        erreurs += _valider_chapitre(chapitre, vus)
    return erreurs


def _valider_chapitre(chapitre, vus):
    erreurs = []
    num = chapitre.get("num")
    if not isinstance(num, int) or not 1 <= num <= 7:
        erreurs.append(f"chapitre {num!r} : numero invalide")
    bornes = chapitre.get("slides")
    if not (isinstance(bornes, list) and len(bornes) == 2 and bornes[0] <= bornes[1]):
        erreurs.append(f"chapitre {num} : plage de slides invalide")
        return erreurs

    for carte in chapitre.get("cartes", []):
        erreurs += _valider_entree(carte, CHAMPS_CARTE, bornes, vus, "carte")
    for question in chapitre.get("quiz", []):
        erreurs += _valider_entree(question, CHAMPS_QUIZ, bornes, vus, "quiz")
        erreurs += _valider_quiz(question)
    for muscle in chapitre.get("muscles", []):
        erreurs += _valider_muscle(muscle, bornes)
    for piege in chapitre.get("pieges", []):
        erreurs += _valider_slide(piege, bornes, piege.get("titre", "piege"))
    for planche in chapitre.get("planches", []):
        erreurs += valider_planche(planche, bornes)
    return erreurs


def _valider_entree(entree, champs, bornes, vus, genre):
    erreurs = []
    identifiant = entree.get("id", "<sans id>")
    for champ in champs:
        valeur = entree.get(champ)
        if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
            erreurs.append(f"{genre} {identifiant} : champ '{champ}' vide ou absent")
    if identifiant in vus:
        erreurs.append(f"{genre} {identifiant} : identifiant en double")
    vus.add(identifiant)
    erreurs += _valider_slide(entree, bornes, identifiant)
    return erreurs


def _valider_slide(entree, bornes, etiquette):
    if entree.get("hors_cours"):
        return []
    slide = entree.get("slide")
    if not isinstance(slide, int):
        return [f"{etiquette} : numero de slide absent"]
    if not bornes[0] <= slide <= bornes[1]:
        return [f"{etiquette} : slide {slide} hors de la plage {bornes[0]}-{bornes[1]}"]
    return []


def _valider_quiz(question):
    erreurs = []
    identifiant = question.get("id", "<sans id>")
    choix = question.get("choix") or []
    if len(choix) < 3:
        erreurs.append(f"quiz {identifiant} : au moins trois choix sont requis")
    bonne = question.get("bonne")
    if not isinstance(bonne, int) or not 0 <= bonne < len(choix):
        erreurs.append(f"quiz {identifiant} : index 'bonne' hors bornes")
    if not (question.get("expl") or "").strip():
        erreurs.append(f"quiz {identifiant} : explication absente")
    return erreurs


def _valider_muscle(muscle, bornes):
    erreurs = []
    nom = muscle.get("nom", "<sans nom>")
    for champ in CHAMPS_MUSCLE:
        valeur = muscle.get(champ)
        if not valeur:
            erreurs.append(f"muscle {nom} : champ '{champ}' vide ou absent")
    erreurs += _valider_slide(muscle, bornes, f"muscle {nom}")
    return erreurs


def valider_planche(planche, bornes=None):
    erreurs = []
    identifiant = planche.get("id", "<sans id>")
    if "<text" in (planche.get("dessin") or ""):
        erreurs.append(
            f"planche {identifiant} : le trace contient une balise text ; "
            "les etiquettes doivent vivre dans 'pastilles' pour permettre le mode muet"
        )
    try:
        _, _, largeur, hauteur = (float(v) for v in planche["vb"].split())
    except (KeyError, ValueError):
        erreurs.append(f"planche {identifiant} : viewBox invalide")
        return erreurs

    pastilles = planche.get("pastilles") or []
    for pastille in pastilles:
        if (
            not 0 <= pastille.get("x", -1) <= largeur
            or not 0 <= pastille.get("y", -1) <= hauteur
        ):
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} hors du cadre"
            )
        if not (pastille.get("t") or "").strip():
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} sans libelle"
            )
        plan = pastille.get("plan", "")
        if plan not in PLANS_VALIDES:
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} a un plan "
                f"invalide ({plan!r}) ; attendu frontal, sagittal, transversal ou vide"
            )
        ancre = pastille.get("ancre")
        if ancre not in ANCRES_VALIDES:
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} a une ancre "
                f"invalide ({ancre!r}) ; attendu start, end ou middle"
            )
        else:
            dx, dy = DECALAGE_LIBELLE[ancre]
            lx, ly = pastille.get("x", -1) + dx, pastille.get("y", -1) + dy
            if not 0 <= lx <= largeur or not 0 <= ly <= hauteur:
                erreurs.append(
                    f"planche {identifiant} : pastille {pastille.get('n')} a un "
                    "libelle qui sort du cadre une fois decale selon son ancre"
                )
        if "indice" in pastille and not (pastille.get("indice") or "").strip():
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} a un indice vide"
            )
    numeros = sorted(p.get("n") for p in pastilles)
    if numeros and numeros != list(range(1, len(numeros) + 1)):
        erreurs.append(
            f"planche {identifiant} : numerotation des pastilles non contigue"
        )
    if bornes is not None:
        erreurs += _valider_slide(planche, bornes, f"planche {identifiant}")
    return erreurs
