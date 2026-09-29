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

# Emprise du texte d'un libelle, estimee -- le validateur n'a pas de navigateur.
#
# Defaut releve au pilotage (tache fiche, suite) : valider_planche ne verifiait que le
# POINT D'ANCRAGE du libelle, pas la place que prend son texte. Douze libelles de
# trois planches du chapitre 7 depassaient du viewBox -- « Tete de la fibula »
# coupee a 77 % -- et l'element <svg> racine rogne ce qui deborde : la personne
# apprenait un mot tronque. Le defaut avait passe trois revues et un audit.
#
# TAILLE_POLICE_LIBELLE : le libelle est en var(--t-s) = 0,9375 rem = 15 px
#   (site/assets/style.css, .pastille__t), et les unites du viewBox suivent la
#   mise a l'echelle de la planche : 15 unites, a toute largeur d'ecran.
#
# LARGEUR_CARACTERE_EM : largeur d'un caractere, en em, par classe. Origine : largeur
#   getBBox() de chacun des 116 libelles des 27 planches d'alors, mesuree dans Chrome
#   avec la police du site (Public Sans), puis ajustee aux moindres carres sur cinq
#   classes (0,32 ; 0,89 ; 0,64 ; 0,37 ; 0,55 em) et arrondie vers le HAUT (ci-dessous) :
#   l'estimation tombe entre 0,97 et 1,08 fois la mesure. Une seule largeur moyenne
#   (0,43 a 0,59 em selon le mot, moyenne 0,49) ne suffit pas : prise assez large pour
#   couvrir « Endomysium » (0,59), elle refuse seize planches dont onze tiennent
#   largement (« Rotation, pronation, supination » dans 240 unites, avec 9 d'aisance)
#   -- un controle qui crie au loup finit par etre contourne.
# SECURITE_LARGEUR : facteur applique par-dessus. Laisse a 1,0 sur un argument mesure,
#   pas pour faire passer les planches : a 1,08 (essaye d'abord, pour couvrir les
#   polices de repli) le controle refusait 10 planches sur 27, dont cinq (
#   « Articulation plane (arthrodie) », « Courbure sacro-coccygienne », « 3 axes : tous
#   les mouvements », « Membrane synoviale », « Sterno-claviculaire ») ou le libelle
#   reel tenait avec 4 a 13 unites d'aisance. Or les polices de repli du site,
#   mesurees sur les memes 116 libelles, ne sont pas plus larges que Public Sans :
#   Liberation Sans 0,93 a 1,00, DejaVu Sans 0,83 a 0,95, Noto Sans 0,96 a 1,06
#   (moyenne 1,01) -- au pire +6 %, et seulement pour Noto Sans. Ce qui reste hors de
#   portee du controle : un libelle qui deborderait de moins de ~6 % de sa propre
#   largeur avec une police de repli ; a 1,0 il attrape en revanche toute
#   amputation notable (les douze libelles rognes du chapitre 7, de 11 a 77 %, et
#   les deux libelles reels a moins de 2 unites du bord).
# MARGE_LIBELLE : distance minimale entre l'emprise estimee et le bord du viewBox.
# ASCENDANT / DESCENDANT : hauteur d'une lettre au-dessus et en dessous de la ligne
#   de base (0,75 em et 0,22 em : boite de glyphes, hors accents hauts).
TAILLE_POLICE_LIBELLE = 15
LARGEUR_CARACTERE_EM = {
    "etroit": 0.33,
    "large": 0.90,
    "majuscule": 0.65,
    "chiffre": 0.38,
    "courant": 0.56,
}
CARACTERES_ETROITS = frozenset("iIjl.,;:'’!|()[]/ -tfr")
CARACTERES_LARGES = frozenset("mwMW%")
SECURITE_LARGEUR = 1.0
MARGE_LIBELLE = 2
ASCENDANT_LIBELLE = 0.75 * TAILLE_POLICE_LIBELLE
DESCENDANT_LIBELLE = 0.22 * TAILLE_POLICE_LIBELLE

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


def largeur_estimee_libelle(texte):
    """Largeur estimee du texte, en unites du viewBox (voir les constantes plus haut)."""
    em = 0.0
    for caractere in texte:
        if caractere in CARACTERES_ETROITS:
            em += LARGEUR_CARACTERE_EM["etroit"]
        elif caractere in CARACTERES_LARGES:
            em += LARGEUR_CARACTERE_EM["large"]
        elif caractere.isupper():
            em += LARGEUR_CARACTERE_EM["majuscule"]
        elif caractere.isdigit():
            em += LARGEUR_CARACTERE_EM["chiffre"]
        else:
            em += LARGEUR_CARACTERE_EM["courant"]
    return em * TAILLE_POLICE_LIBELLE * SECURITE_LARGEUR


def _emprise_libelle(texte, ancre, lx, ly):
    """(gauche, droite, haut, bas) estimes du texte d'un libelle, en unites du
    viewBox. `lx`, `ly` : point d'ancrage deja decale (DECALAGE_LIBELLE)."""
    largeur_texte = largeur_estimee_libelle(texte)
    if ancre == "start":
        gauche, droite = lx, lx + largeur_texte
    elif ancre == "end":
        gauche, droite = lx - largeur_texte, lx
    else:  # middle
        gauche, droite = lx - largeur_texte / 2, lx + largeur_texte / 2
    return gauche, droite, ly - ASCENDANT_LIBELLE, ly + DESCENDANT_LIBELLE


def _valider_emprise_libelle(identifiant, pastille, lx, ly, largeur, hauteur):
    gauche, droite, haut, bas = _emprise_libelle(
        (pastille.get("t") or "").strip(), pastille.get("ancre"), lx, ly
    )
    erreurs = []
    if gauche < MARGE_LIBELLE or droite > largeur - MARGE_LIBELLE:
        cote = "gauche" if gauche < MARGE_LIBELLE else "droite"
        erreurs.append(
            f"planche {identifiant} : pastille {pastille.get('n')} "
            f"(« {pastille.get('t')} ») : le texte estime deborde du viewBox a {cote} "
            f"(de {gauche:.0f} a {droite:.0f} pour une largeur de {largeur:.0f}) ; "
            "le SVG rogne ce qui depasse -- elargir le viewBox ou deplacer l'ancre"
        )
    if haut < MARGE_LIBELLE or bas > hauteur - MARGE_LIBELLE:
        erreurs.append(
            f"planche {identifiant} : pastille {pastille.get('n')} "
            f"(« {pastille.get('t')} ») : le texte estime deborde du viewBox en "
            f"hauteur (de {haut:.0f} a {bas:.0f} pour une hauteur de {hauteur:.0f})"
        )
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
            else:
                erreurs += _valider_emprise_libelle(
                    identifiant, pastille, lx, ly, largeur, hauteur
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
