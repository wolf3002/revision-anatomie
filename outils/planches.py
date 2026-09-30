"""Traces SVG des planches.

Contrat : 'dessin' ne contient jamais d'etiquette. Les libelles vivent dans
'pastilles', ce qui permet de produire le mode legende et le mode muet depuis
une seule source, sans risque de divergence.
"""

_SILHOUETTE_FACE = (
    "<g class='corps' fill='none' stroke='currentColor' stroke-width='2'>"
    "<circle cx='160' cy='48' r='26'/>"
    "<path d='M160 74 L160 196'/>"
    "<path d='M160 96 L104 150 M160 96 L216 150'/>"
    "<path d='M160 196 L128 292 M160 196 L192 292'/>"
    "</g>"
)

# Marqueur de flèche partagé par les tracés qui l'utilisent (marker-end='url(#fleche)').
# Un <defs> est autorisé dans 'dessin' : ce n'est pas une étiquette, valider_planche ne
# rejette que les balises <text>.
_DEFS_FLECHE = (
    "<defs><marker id='fleche' viewBox='0 0 10 10' refX='9' refY='5' "
    "markerWidth='6' markerHeight='6' orient='auto'>"
    "<path d='M0 0 L10 5 L0 10 Z' fill='currentColor'/></marker></defs>"
)

# Decalage d'un trace tel quel, sans en toucher une coordonnee : enveloppe <g transform>.
# Sert a redonner de la place a des libelles qui debordaient du viewBox (voir
# contenu/schema.py, emprise du texte) sans redessiner : on decale le trace ET les
# pastilles de la meme quantite, et on elargit le viewBox de ce qui manquait.
def _translater(dessin, dx, dy=0):
    return f"<g transform='translate({dx} {dy})'>{dessin}</g>"


# Les trois plans (ronde de correction 1, puis éclatés en planches séparées en ronde de
# correction 4) : une seule vue de face avec trois traits tiretés superposés se lisait
# comme "trois lignes identiques" et faisait chevaucher les libellés. Puis un unique
# viewBox large (720 px, trois panneaux côte à côte) débordait sur mobile — trois
# panneaux ne peuvent pas tenir à la fois lisibles et dans un écran de 320-390 px.
# Chaque plan est donc sa propre planche autonome (vb ~240x360, une seule silhouette),
# chacune avec l'orientation où son plan se voit vraiment de face :
#   - frontal   : silhouette de face, le plan en surface verticale traversant le corps,
#                 flèche d'abduction du bras (mouvement caractéristique du plan frontal).
#   - sagittal  : silhouette DE PROFIL (le plan est alors dans le plan de la page),
#                 flèche de flexion du genou.
#   - transversal : silhouette de face, le plan en ellipse horizontale (la perspective
#                 suggère mieux l'horizontale qu'un simple segment), flèche de rotation.
# Les tracés eux-mêmes sont inchangés (validés en ronde 1) : seul cx change, puisque
# chaque planche recentre sa silhouette dans son propre viewBox de 240 px de large.
_CX = 70


def _panel_frontal(cx):
    corps = (
        "<g class='corps' fill='none' stroke='currentColor' stroke-width='2'>"
        f"<circle cx='{cx}' cy='40' r='20'/>"
        f"<path d='M{cx} 60 L{cx} 160'/>"
        f"<path d='M{cx} 78 L{cx - 38} 122 M{cx} 78 L{cx + 38} 122'/>"
        f"<path d='M{cx} 160 L{cx - 30} 248 M{cx} 160 L{cx + 30} 248'/>"
        "</g>"
    )
    plan = (
        "<g class='plan plan--frontal' fill='none' stroke='currentColor'>"
        f"<path d='M{cx - 45} 15 L{cx + 45} 15 L{cx + 45} 255 L{cx - 45} 255 Z' "
        "stroke-dasharray='5 4' stroke-width='1.5'/>"
        f"<path d='M{cx + 38} 122 Q{cx + 66} 96 {cx + 60} 74' stroke-width='2' "
        "marker-end='url(#fleche)'/></g>"
    )
    return corps + plan


def _panel_sagittal(cx):
    corps = (
        "<g class='corps' fill='none' stroke='currentColor' stroke-width='2'>"
        f"<circle cx='{cx}' cy='40' r='18'/>"
        f"<path d='M{cx} 58 L{cx} 150'/>"
        f"<path d='M{cx} 80 L{cx + 28} 118'/>"
        f"<path d='M{cx} 150 L{cx + 12} 205 L{cx - 15} 232'/>"
        "</g>"
    )
    plan = (
        "<g class='plan plan--sagittal' fill='none' stroke='currentColor'>"
        f"<path d='M{cx - 25} 15 L{cx + 42} 15 L{cx + 42} 255 L{cx - 25} 255 Z' "
        "stroke-dasharray='5 4' stroke-width='1.5'/>"
        f"<path d='M{cx + 20} 197 Q{cx + 38} 215 {cx + 14} 233' stroke-width='2' "
        "marker-end='url(#fleche)'/></g>"
    )
    return corps + plan


def _panel_transversal(cx):
    corps = (
        "<g class='corps' fill='none' stroke='currentColor' stroke-width='2'>"
        f"<circle cx='{cx}' cy='40' r='20'/>"
        f"<path d='M{cx} 60 L{cx} 160'/>"
        f"<path d='M{cx} 78 L{cx - 38} 122 M{cx} 78 L{cx + 38} 122'/>"
        f"<path d='M{cx} 160 L{cx - 30} 248 M{cx} 160 L{cx + 30} 248'/>"
        "</g>"
    )
    plan = (
        "<g class='plan plan--transversal' fill='none' stroke='currentColor'>"
        f"<ellipse cx='{cx}' cy='112' rx='55' ry='16' stroke-dasharray='5 4' "
        "stroke-width='1.5'/>"
        f"<path d='M{cx + 40} 106 A44 15 0 0 1 {cx - 40} 106' stroke-width='2' "
        "marker-end='url(#fleche)'/></g>"
    )
    return corps + plan


# Pastilles des plans (audit de verification exhaustive, 2026-09-30).
#
# Deux defauts corriges ensemble.
#
# 1. Ce qu'on demande doit etre ce qu'on accepte. La pastille « mouvements » attendait
#    « Abduction, adduction » (ou « Flexion, extension »...) alors que le cours donne
#    TROIS mouvements au plan frontal (slide 18, avec l'inclinaison laterale) et QUATRE
#    couples au plan sagittal (slide 23) : verifierPastille compare par egalite exacte
#    apres normalisation, si bien qu'une reponse complete et juste etait notee fausse.
#    Une liste de trois a huit termes ne se retape de toute facon pas a l'identique
#    (ordre, virgules), et elle ne tiendrait pas dans le cadre. La pastille designe donc
#    UN seul mouvement, celui que la fleche du trace dessine -- indice « le mouvement
#    fleche » -- et attend son nom : « Abduction » (bras, plan frontal), « Flexion »
#    (genou, plan sagittal), « Rotation » (plan transversal). Les listes completes
#    restent au programme des cartes c1-05, c1-09 et c1-16.
#
# 2. Elle est posee contre sa fleche. Les deux pastilles etaient empilees sous les
#    pieds du personnage, a ~200 unites de la fleche qu'elles designaient. La silhouette
#    est decalee vers la gauche (_CX) pour laisser a droite la place du libelle le plus
#    long (« Abduction », ~70 unites) sans elargir le viewBox ; la pastille du nom du plan
#    reste sous le cadre du plan. Le viewBox perd la hauteur qu'il gardait pour la
#    seconde pastille empilee (360 -> 312).
_Y_NOM = 268
_VB_PLAN = "0 0 240 312"
_INDICE_MOUVEMENT = "le mouvement fléché"

# --- Chapitre 2 : l'os long en coupe (slides 65-66) ---------------------
#
# Silhouette schematique d'un os long (type humerus, slide 66 "Exemple
# humerus") : deux epiphyses (ellipses), deux metaphyses (trapezes de
# transition), une diaphyse (rectangle exterieur = os compact, deux traits
# interieurs = parois du canal medullaire). Le perioste est une ligne
# pointillee juste a l'exterieur de la diaphyse ; l'os spongieux est une
# semis de points a l'interieur de chaque epiphyse ; le cartilage articulaire
# est un arc plus epais a la pointe de chaque epiphyse.
#
# Chaque structure est unique dans la planche (une seule pastille par nom,
# meme quand la structure existe deux fois -- ex. les deux metaphyses -- pour
# respecter l'unicite des libelles, testee par test_planches.py).
# Le canevas doit etre assez large pour que CHAQUE libelle, une fois decale
# par son ancre (start/end, cf. DECALAGE_LIBELLE), tienne entier dans le
# viewBox : un <svg> rogne tout ce qui depasse (overflow initial = hidden),
# contrairement au reste de la page. Verifie par rendu reel (Playwright,
# capture de la planche en mode legende ET muet) apres une premiere version
# a viewBox 220 ou "Cartilage articulaire" et "Os spongieux" se faisaient
# tronquer en plein milieu du mot. Marge calculee sur le libelle le plus
# long de chaque colonne (~7px/caractere a l'echelle 1:1 de ce viewBox).
_DESSIN_OS_LONG = (
    "<g class='os-long' fill='none' stroke='currentColor' stroke-width='2'>"
    # Epiphyse proximale + cartilage articulaire (arc plus epais a la pointe).
    "<ellipse cx='170' cy='65' rx='42' ry='32'/>"
    "<path d='M143 42 Q170 24 197 42' stroke-width='4'/>"
    # Metaphyse proximale (trapeze de transition).
    "<path d='M138 92 L202 92 L188 122 L152 122 Z'/>"
    # Perioste (pointille) le long de la diaphyse.
    "<path d='M144 124 L144 330' stroke-dasharray='4 3'/>"
    "<path d='M196 124 L196 330' stroke-dasharray='4 3'/>"
    # Diaphyse : contour exterieur (os compact) + parois du canal medullaire.
    "<rect x='150' y='122' width='40' height='210'/>"
    "<path d='M160 132 L160 322'/>"
    "<path d='M180 132 L180 322'/>"
    # Metaphyse distale (trapeze de transition, symetrique).
    "<path d='M152 332 L188 332 L202 362 L138 362 Z'/>"
    # Epiphyse distale + cartilage articulaire.
    "<ellipse cx='170' cy='395' rx='42' ry='32'/>"
    "<path d='M143 418 Q170 436 197 418' stroke-width='4'/>"
    "</g>"
    # Os spongieux : semis de points dans chaque epiphyse (pastille sur le
    # semis distal seulement, pour ne pas encombrer le cote proximal deja
    # charge par les pastilles cartilage/epiphyse/metaphyse).
    "<g class='os-spongieux' fill='currentColor' stroke='none'>"
    "<circle cx='145' cy='55' r='2.2'/><circle cx='155' cy='45' r='2.2'/>"
    "<circle cx='170' cy='40' r='2.2'/><circle cx='185' cy='45' r='2.2'/>"
    "<circle cx='195' cy='55' r='2.2'/><circle cx='150' cy='75' r='2.2'/>"
    "<circle cx='165' cy='80' r='2.2'/><circle cx='175' cy='80' r='2.2'/>"
    "<circle cx='190' cy='75' r='2.2'/>"
    "<circle cx='145' cy='385' r='2.2'/><circle cx='155' cy='375' r='2.2'/>"
    "<circle cx='170' cy='370' r='2.2'/><circle cx='185' cy='375' r='2.2'/>"
    "<circle cx='195' cy='385' r='2.2'/><circle cx='150' cy='405' r='2.2'/>"
    "<circle cx='165' cy='410' r='2.2'/><circle cx='175' cy='410' r='2.2'/>"
    "<circle cx='190' cy='405' r='2.2'/>"
    "</g>"
    # Reperes (fleches) reliant chaque structure a sa pastille en marge.
    "<g class='reperes' fill='none' stroke='currentColor' stroke-width='1.5'>"
    "<path d='M197 42 L222 24' marker-end='url(#fleche)'/>"
    "<path d='M212 65 L222 73' marker-end='url(#fleche)'/>"
    "<path d='M144 150 L118 115' marker-end='url(#fleche)'/>"
    "<path d='M197 107 L222 124' marker-end='url(#fleche)'/>"
    "<path d='M155 205 L118 205' marker-end='url(#fleche)'/>"
    "<path d='M170 200 L222 200' marker-end='url(#fleche)'/>"
    "<path d='M148 390 L118 392' marker-end='url(#fleche)'/>"
    "<path d='M212 395 L222 393' marker-end='url(#fleche)'/>"
    "</g>"
)

_PASTILLES_OS_LONG = [
    {
        "n": 1,
        "x": 235,
        "y": 20,
        "t": "Cartilage articulaire",
        "ancre": "start",
        "indice": "au bout de chaque épiphyse",
    },
    {
        "n": 2,
        "x": 235,
        "y": 75,
        "t": "Épiphyse proximale",
        "ancre": "start",
        "indice": "extrémité proche du tronc",
    },
    {
        "n": 3,
        "x": 110,
        "y": 110,
        "t": "Périoste",
        "ancre": "end",
        "indice": "membrane qui enveloppe l'os",
    },
    {
        "n": 4,
        "x": 235,
        "y": 130,
        "t": "Métaphyse",
        "ancre": "start",
        "indice": "jonction diaphyse / épiphyse",
    },
    {
        "n": 5,
        "x": 110,
        "y": 200,
        "t": "Os compact",
        "ancre": "end",
        "indice": "juste sous le périoste",
    },
    {
        "n": 6,
        "x": 235,
        "y": 200,
        "t": "Canal médullaire",
        "ancre": "start",
        "indice": "cavité centrale de la diaphyse",
    },
    {
        "n": 7,
        "x": 110,
        "y": 390,
        "t": "Os spongieux",
        "ancre": "end",
        "indice": "sous l'os compact, aux épiphyses",
    },
    {
        "n": 8,
        "x": 235,
        "y": 395,
        "t": "Épiphyse distale",
        "ancre": "start",
        "indice": "extrémité distale, loin du tronc",
    },
]

# --- Chapitre 2 : squelette axial contre squelette appendiculaire -------
#
# Une seule silhouette (slide 56 : "le squelette appendiculaire se fixe sur
# le squelette axial"), avec deux grammaires de trait pour opposer les deux
# groupes sans recourir a la couleur (le trace n'utilise que currentColor) :
# trait plein = squelette axial (tete, colonne, thorax) ; trait pointille =
# squelette appendiculaire (ceintures + membres). Le sternum, plus large que
# le trait de la colonne, se distingue de celle-ci par son epaisseur plutot
# que par sa position (les deux se projettent au centre en vue de face).
# Meme contrainte de marge que l'os long ci-dessus (libelle entier dans le
# viewBox une fois decale par son ancre). "Squelette thoracique" et "Colonne
# vertébrale" sont les libelles les plus longs et dimensionnent chaque cote.
#
# Bras et jambes en un seul segment (meme grammaire que _SILHOUETTE_FACE,
# tache 1) : une premiere version a 2 segments (epaule-coude-main) dessinait
# une boucle hexagonale collee au thorax, illisible comme "bras" au rendu
# reel -- corrige par un simple trait epaule/hanche -> main/pied.
_DESSIN_SQUELETTE = (
    "<g class='axial' fill='none' stroke='currentColor' stroke-width='2'>"
    "<circle cx='300' cy='45' r='22'/>"
    "<path d='M300 67 L300 90'/>"
    "<ellipse cx='300' cy='140' rx='40' ry='50'/>"
    "<path d='M300 95 L300 175' stroke-width='6'/>"
    "<path d='M300 190 L300 265'/>"
    "</g>"
    "<g class='appendiculaire' fill='none' stroke='currentColor' "
    "stroke-width='2' stroke-dasharray='5 4'>"
    "<path d='M265 265 L335 265 L348 298 L252 298 Z'/>"
    "<path d='M340 95 L385 175'/>"
    "<path d='M260 95 L215 175'/>"
    "<path d='M335 298 L375 383'/>"
    "<path d='M265 298 L225 383'/>"
    "</g>"
    "<g class='reperes' fill='none' stroke='currentColor' stroke-width='1.5'>"
    "<path d='M322 40 L385 26' marker-end='url(#fleche)'/>"
    "<path d='M340 140 L385 138' marker-end='url(#fleche)'/>"
    "<path d='M237 135 L210 138' marker-end='url(#fleche)'/>"
    "<path d='M300 238 L210 240' marker-end='url(#fleche)'/>"
    "<path d='M245 340 L210 345' marker-end='url(#fleche)'/>"
    "</g>"
)

_PASTILLES_SQUELETTE = [
    {
        "n": 1,
        "x": 405,
        "y": 25,
        "t": "Os de la tête",
        "ancre": "start",
        "indice": "crâne + face",
    },
    {
        "n": 2,
        "x": 405,
        "y": 138,
        "t": "Squelette thoracique",
        "ancre": "start",
        "indice": "côtes + sternum",
    },
    {
        "n": 3,
        "x": 195,
        "y": 138,
        "t": "Membre supérieur",
        "ancre": "end",
        "indice": "ceinture scapulaire + partie libre",
    },
    {
        "n": 4,
        "x": 195,
        "y": 240,
        "t": "Colonne vertébrale",
        "ancre": "end",
        "indice": "vertèbres mobiles puis soudées",
    },
    {
        "n": 5,
        "x": 195,
        "y": 345,
        "t": "Membre inférieur",
        "ancre": "end",
        "indice": "ceinture pelvienne + partie libre",
    },
]

PLANCHES = {
    "plan-frontal": {
        "id": "plan-frontal",
        "titre": "Le plan frontal",
        "vb": _VB_PLAN,
        "dessin": _DEFS_FLECHE + _panel_frontal(_CX),
        "pastilles": [
            {
                "n": 1,
                "x": _CX,
                "y": _Y_NOM,
                "t": "Plan frontal",
                "ancre": "middle",
                "plan": "frontal",
                "indice": "nom du plan",
            },
            {
                "n": 2,
                "x": _CX + 76,
                "y": 92,
                "t": "Abduction",
                "ancre": "start",
                "plan": "frontal",
                "indice": _INDICE_MOUVEMENT,
            },
        ],
    },
    "plan-sagittal": {
        "id": "plan-sagittal",
        "titre": "Le plan sagittal",
        "vb": _VB_PLAN,
        "dessin": _DEFS_FLECHE + _panel_sagittal(_CX),
        "pastilles": [
            {
                "n": 1,
                "x": _CX,
                "y": _Y_NOM,
                "t": "Plan sagittal",
                "ancre": "middle",
                "plan": "sagittal",
                "indice": "nom du plan",
            },
            {
                "n": 2,
                "x": _CX + 58,
                "y": 214,
                "t": "Flexion",
                "ancre": "start",
                "plan": "sagittal",
                "indice": _INDICE_MOUVEMENT,
            },
        ],
    },
    "plan-transversal": {
        "id": "plan-transversal",
        "titre": "Le plan transversal",
        "vb": _VB_PLAN,
        "dessin": _DEFS_FLECHE + _panel_transversal(_CX),
        "pastilles": [
            {
                "n": 1,
                "x": _CX,
                "y": _Y_NOM,
                "t": "Plan transversal",
                "ancre": "middle",
                "plan": "transversal",
                "indice": "nom du plan",
            },
            {
                "n": 2,
                "x": _CX + 72,
                "y": 108,
                "t": "Rotation",
                "ancre": "start",
                "plan": "transversal",
                "indice": _INDICE_MOUVEMENT,
            },
        ],
    },
    "os-long-coupe": {
        "id": "os-long-coupe",
        "titre": "L'os long en coupe",
        "vb": "0 0 430 460",
        # Decale de 10 unites vers la droite : « Os spongieux » (pastille 7, ancre
        # « end ») butait a 1,6 unite du bord gauche du viewBox.
        "dessin": _DEFS_FLECHE + _translater(_DESSIN_OS_LONG, 10),
        "pastilles": [{**q, "x": q["x"] + 10} for q in _PASTILLES_OS_LONG],
    },
    "squelette-axial-appendiculaire": {
        "id": "squelette-axial-appendiculaire",
        "titre": "Squelette axial et squelette appendiculaire",
        "vb": "0 0 600 420",
        "dessin": _DEFS_FLECHE + _DESSIN_SQUELETTE,
        "pastilles": _PASTILLES_SQUELETTE,
    },
    "termes-localisation": {
        "id": "termes-localisation",
        "titre": "Les termes de localisation",
        "vb": "0 0 320 340",
        "dessin": (
            _DEFS_FLECHE
            + _SILHOUETTE_FACE
            + "<g class='reperes' fill='none' stroke='currentColor' stroke-width='1.5'>"
            # Crânial / Caudal (audit de verification exhaustive, 2026-09-30) : le cours dit
            # « extremite superieure / inferieure DU TRONC » (slide 38). La fleche caudale
            # longeait la jambe -- la meme region que « distal », ce qui rendait les deux
            # indiscernables en mode muet. Les deux fleches sont a present a gauche du tronc
            # (x = 160), l'une en haut (epaules, cou), l'autre en bas (bassin) ; chacune
            # pointe vers le pole qu'elle nomme. Elles sont placees hors de l'aisselle : le
            # bras gauche coupe x = 128 vers y = 127 et se termine en (104, 150).
            "<path d='M128 112 L128 76' marker-end='url(#fleche)'/>"
            "<path d='M134 152 L134 198' marker-end='url(#fleche)'/>"
            # Proximal / Distal : le long de la jambe droite (décalé pour rester lisible),
            # la flèche proximale pointe vers le tronc (la hanche), la flèche distale
            # pointe vers l'extrémité du membre (le pied) — donc loin du tronc.
            "<path d='M193 244 L180 205' marker-end='url(#fleche)'/>"
            "<path d='M194 249 L206 282' marker-end='url(#fleche)'/>"
            # Médial / Latéral : décalées verticalement (correction ronde 1 : à la même
            # hauteur, les deux flèches se lisaient comme une seule flèche continue), et
            # toutes deux logées à droite du tronc, entre le bras et la hanche (la gauche est
            # a present prise par les fleches cranio-caudales). La flèche médiale pointe vers
            # le plan médian, la latérale s'en éloigne.
            "<path d='M194 163 L168 163' marker-end='url(#fleche)'/>"
            "<path d='M170 188 L202 188' marker-end='url(#fleche)'/>"
            "</g>"
        ),
        "pastilles": [
            {"n": 1, "x": 114, "y": 94, "t": "Crânial", "ancre": "end"},
            {"n": 2, "x": 120, "y": 176, "t": "Caudal", "ancre": "end"},
            {"n": 3, "x": 196, "y": 215, "t": "Proximal", "ancre": "start"},
            {"n": 4, "x": 214, "y": 270, "t": "Distal", "ancre": "start"},
            {"n": 5, "x": 208, "y": 163, "t": "Médial", "ancre": "start"},
            {"n": 6, "x": 216, "y": 188, "t": "Latéral", "ancre": "start"},
        ],
    },
}

# --- Chapitre 3 : les sept diarthroses (slides 81-94) --------------------
#
# "C'est la géométrie des surfaces qui les distingue, donc un schéma y est plus
# juste qu'une liste" (plan de la tâche 3). Chaque type est donc une planche
# AUTONOME et minuscule (vb 220x345, une seule paire de formes emboîtées),
# jamais une planche unique à 7 panneaux : une planche large ne tient pas dans
# 320 px (cf. les plans anatomiques du chapitre 1, éclatés pour la même
# raison). Le test du mode muet porte ici sur la GEOMETRIE seule : sphère
# pleine dans sphère creuse, ellipse dans ellipse, surface ondulée en selle,
# charnière à goupille, tige tournant dans un anneau, deux condyles sur un
# plateau (le cours dit « une paire de condyles plane », slide 92), deux plans qui
# glissent — sept silhouettes volontai-
# rement DIFFERENTES entre elles (pas de recyclage de la même paire de
# cercles pour deux types), vérifiées une à une en rendant chaque planche
# sans ses pastilles (rsvg-convert) avant d'écrire ce module.
#
# Absence volontaire de "plan" sur les pastilles : contrairement aux 3 plans
# anatomiques du chapitre 1, ces planches ne portent pas sur le plan frontal/
# sagittal/transversal mais sur la forme des surfaces ; forcer un mouvement à
# 2 axes (ellipsoïde, selle) dans un seul plan aurait été inexact.
#
# L'ellipsoïde a bien un exemple : la légende de la figure de la slide 84 dit
# « Articulation ellipsoïdale entre l'extrémité distale du radius, le scaphoïde et le
# semi-lunaire du carpe (poignet) ». C'est du texte DANS l'image, invisible à
# pdftotext : un audit précédent avait conclu à tort que le cours n'en donnait pas
# (rectifié par la vérification exhaustive du 2026-09-30, slides rendues en image).
# Sa planche porte donc quatre pastilles (type, deux axes, exemple), comme la selle,
# et le même viewBox haut de 380. Le libellé reprend le mot du cours, « le poignet » :
# le cours n'emploie pas « radio-carpienne » ici.
_VB_DIARTHROSE = "0 0 220 345"
_Y_TYPE = 245
_Y_AXES = 278
_Y_EXEMPLE = 311

PLANCHES.update(
    {
        "diarthrose-spheroide": {
            "id": "diarthrose-spheroide",
            "titre": "La sphéroïde (énarthrose)",
            "vb": _VB_DIARTHROSE,
            # Sphère pleine (le "ballon", cercle plein) qui s'emboîte dans une
            # sphère creuse (le "creux", grand arc concentrique presque fermé,
            # ouvert seulement au sommet -- juste assez pour laisser passer le
            # col qui relie la tête à sa diaphyse, comme la tête fémorale dans
            # l'acétabulum). Nesting CONCENTRIQUE (même centre, rayons
            # différents) : la seule ouverture est l'échancrure du haut, pas un
            # décalage de centre -- ce qui distingue ce pictogramme, au premier
            # coup d'oeil, de la charnière ou du pivot qui suivent.
            "dessin": (
                "<path d='M88.8,91.7 A62,62 0 1,0 131.2,91.7' "
                "fill='none' stroke='currentColor' stroke-width='2.2'/>"
                "<circle cx='110' cy='150' r='40' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M110,110 L110,55' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M90,35 L130,35 L130,55 L90,55 Z' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Sphéroïde (énarthrose)",
                    "ancre": "middle",
                    "indice": "sphère pleine dans une sphère creuse",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "3 axes : tous les mouvements",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Ex : la hanche",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-ellipsoide": {
            "id": "diarthrose-ellipsoide",
            "titre": "L'ellipsoïde (condylienne)",
            "vb": "0 0 220 380",
            # Meme grammaire que la sphéroïde (nesting concentrique, col qui
            # sort par le sommet) mais avec des ELLIPSES, nettement plus
            # larges que hautes : la silhouette entière est plus plate et plus
            # évasée que le cercle de la sphéroïde -- c'est ce contraste de
            # forme (ronde contre aplatie), pas une étiquette, qui doit
            # permettre de ne pas confondre les deux au premier coup d'oeil.
            "dessin": (
                "<path d='M85.4,101.1 A72,52 0 1,0 134.6,101.1' "
                "fill='none' stroke='currentColor' stroke-width='2.2'/>"
                "<ellipse cx='110' cy='150' rx='46' ry='30' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M110,120 L110,55' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M90,35 L130,35 L130,55 L90,55 Z' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Ellipsoïde (condylienne)",
                    "ancre": "middle",
                    "indice": "ellipse convexe dans une ellipse concave",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "Flexion, extension",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Abduction, adduction",
                    "ancre": "middle",
                },
                {
                    "n": 4,
                    "x": 110,
                    "y": _Y_EXEMPLE + 33,
                    "t": "Ex : le poignet",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-selle": {
            "id": "diarthrose-selle",
            "titre": "L'articulation en selle",
            # Vb propre, plus haut que les six autres : cette planche est la
            # seule a devoir loger 4 lignes de libelle (nom + 2 axes distincts
            # + exemple) plutot que 3.
            "vb": "0 0 220 380",
            # Deux courbes en S paralleles (concave dans un sens, convexe dans
            # l'autre -- la selle de cheval) au lieu d'un nesting fermé : c'est
            # la SEULE des sept planches sans forme emboitée en anneau, ce qui
            # la rend immédiatement différente des sphéroïde/ellipsoïde
            # voisines malgré les mêmes 2 axes de mouvement. Une tige rejoint
            # chaque courbe à l'endroit où SA face est convexe (l'autre y étant
            # alors concave), pour suggérer que les deux pièces sont bien
            # inversement conformées.
            "dessin": (
                "<path d='M50,120 Q80,90 110,120 Q140,150 170,120' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M50,132 Q80,102 110,132 Q140,162 170,132' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M80,90 L80,45' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M60,25 L100,25 L100,45 L60,45 Z' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M140,162 L140,205' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M120,205 L160,205 L160,225 L120,225 Z' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": 235,
                    "t": "Articulation en selle",
                    "ancre": "middle",
                    "indice": "surface concave dans un sens, convexe dans l'autre",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": 268,
                    "t": "Flexion, extension",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": 301,
                    "t": "Abduction, adduction",
                    "ancre": "middle",
                },
                {
                    "n": 4,
                    "x": 110,
                    "y": 334,
                    "t": "Ex : sterno-claviculaire",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-ginglyme": {
            "id": "diarthrose-ginglyme",
            "titre": "La ginglyme (trochléenne)",
            "vb": _VB_DIARTHROSE,
            # Le cours nomme lui-meme cette diarthrose une "charniere" (slide
            # 88) : le pictogramme reprend donc l'icone universelle de la
            # charniere (deux barres traversees par une goupille), pas une
            # tentative de dessiner la trochlee/cochlee anatomique -- bien
            # plus surement identifiable sans etiquette, et fidele au mot du
            # cours. La fleche courbe (1 sens) marque l'axe UNIQUE, contre les
            # deux fleches opposees du pivot ci-dessous.
            "dessin": _DEFS_FLECHE
            + (
                "<path d='M95,35 L95,92' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M55,92 L135,92' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<circle cx='95' cy='100' r='9' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M55,108 L135,108' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M95,108 L95,195' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M187.5,120.6 A32,32 0 1,1 138.5,120.6' fill='none' "
                "stroke='currentColor' stroke-width='1.8' "
                "marker-end='url(#fleche)'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Ginglyme (trochléenne)",
                    "ancre": "middle",
                    "indice": "une trochlée s'emboîte dans une cochlée : une charnière",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "1 axe : flexion-extension",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Ex : huméro-ulnaire",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-trochoide": {
            "id": "diarthrose-trochoide",
            "titre": "La trochoïde",
            "vb": _VB_DIARTHROSE,
            # Une tige verticale continue traverse un anneau (cylindre convexe
            # dans cylindre concave) : contrairement a la charniere (deux
            # barres qui s'arretent a la goupille), ici la tige NE S'INTERROMPT
            # PAS -- elle tourne SUR son axe, elle ne bascule pas autour de lui.
            # Deux fleches courbes opposees (au lieu d'une seule pour la
            # ginglyme) rendent visible que la rotation se fait dans les deux
            # sens (pronation ET supination).
            "dessin": _DEFS_FLECHE
            + (
                "<path d='M110,30 L110,210' fill='none' stroke='currentColor' "
                "stroke-width='2.6'/>"
                "<ellipse cx='110' cy='115' rx='46' ry='20' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M157.5,97.0 A62,28 0 0,1 157.5,133.0' fill='none' "
                "stroke='currentColor' stroke-width='1.8' "
                "marker-end='url(#fleche)'/>"
                "<path d='M62.5,97.0 A62,28 0 0,0 62.5,133.0' fill='none' "
                "stroke='currentColor' stroke-width='1.8' "
                "marker-end='url(#fleche)'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Trochoïde",
                    "ancre": "middle",
                    "indice": "cylindre convexe dans un cylindre concave",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "1 axe : pronation-supination",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Ex : radio-ulnaire proximale",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-bicondylienne": {
            "id": "diarthrose-bicondylienne",
            "titre": "La bicondylienne",
            "vb": _VB_DIARTHROSE,
            # Seule planche a deux bosses SEPAREES (une tige qui se separe en
            # deux, chacune vers son propre condyle) posees sur un unique
            # plateau (le cours : « une paire de condyles plane ») : le compte ("deux" ronds, pas un ni deux
            # anneaux) est ce qui la distingue sans ambiguite de la sphéroïde/
            # ellipsoïde (une seule piece emboitee) et de la plane ci-dessous
            # (aucune bosse).
            "dessin": (
                "<path d='M110,25 L110,70' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M110,70 L78,95' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M110,70 L142,95' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<circle cx='78' cy='120' r='26' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<circle cx='142' cy='120' r='26' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M40,168 A300,300 0 0,0 180,168' fill='none' "
                "stroke='currentColor' stroke-width='2.2'/>"
                "<path d='M110,168 L110,210' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Bicondylienne",
                    "ancre": "middle",
                    "indice": "une paire de condyles convexes face à une paire de condyles plane",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "1 axe : flexion/extension",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Ex : tibio-fémorale",
                    "ancre": "middle",
                },
            ],
        },
        "diarthrose-plane": {
            "id": "diarthrose-plane",
            "titre": "L'articulation plane (arthrodie)",
            "vb": _VB_DIARTHROSE,
            # Deux barres droites paralleles, sans aucune courbe ni bosse : la
            # seule planche entierement rectiligne des sept -- ce qui la rend
            # instantanement differente de toutes les autres, qui portent
            # chacune au moins une courbe. La fleche horizontale double
            # souligne que le seul mouvement possible est un glissement, pas
            # une rotation autour d'un axe (contrairement aux six autres).
            "dessin": _DEFS_FLECHE
            + (
                "<path d='M110,30 L110,92' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M50,92 L170,92' fill='none' stroke='currentColor' "
                "stroke-width='2.4'/>"
                "<path d='M50,112 L170,112' fill='none' stroke='currentColor' "
                "stroke-width='2.4'/>"
                "<path d='M110,112 L110,205' fill='none' stroke='currentColor' "
                "stroke-width='2.2'/>"
                "<path d='M45,102 L175,102' fill='none' stroke='currentColor' "
                "stroke-width='1.8' marker-start='url(#fleche)' "
                "marker-end='url(#fleche)'/>"
            ),
            "pastilles": [
                {
                    "n": 1,
                    "x": 110,
                    "y": _Y_TYPE,
                    "t": "Articulation plane (arthrodie)",
                    "ancre": "middle",
                    "indice": "deux surfaces planes qui s'opposent",
                },
                {
                    "n": 2,
                    "x": 110,
                    "y": _Y_AXES,
                    "t": "Glissement uniquement",
                    "ancre": "middle",
                },
                {
                    "n": 3,
                    "x": 110,
                    "y": _Y_EXEMPLE,
                    "t": "Ex : le carpe",
                    "ancre": "middle",
                },
            ],
        },
    }
)

# --- Chapitre 3 : l'articulation synoviale type, en coupe (slides 77-104) -
#
# Correction (audit de fidelite, 2026-09-27) : le slide cite dans cours.json
# etait 77, qui sous-titre bien son propre schema "Schema d'une articulation
# synoviale type" -- mais celui-ci n'a que 4 reperes (membrane synoviale,
# surface articulaire, membrane fibreuse, cavite articulaire), sans menisque
# ni ligament. Le schema qui porte reellement 5 des 6 reperes de CETTE
# planche (membrane fibreuse, membrane synoviale, cartilage articulaire,
# cavite articulaire, menisque) est celui de la slide 102, "Menisque
# articulaire (coupe longitudinale d'une articulation)". Le ligament (le 6e
# repere) n'y figure pas, mais il a bien un schema : la slide 100 montre le
# « ligament articulaire » de l'articulation mobile, et la slide 104 le definit
# (correction de l'audit exhaustif du 2026-09-30 : l'affirmation precedente,
# « aucun schema », etait fausse). Les elements dessines
# rassemblent des faits repartis sur plusieurs slides (77 : sur-
# faces + cavite + capsule a deux membranes ; 99 : cartilage ; 102 : menisque ;
# 100 et 104 : ligament), verifies un a un contre le texte extrait (pdftotext) et
# contre les schemas-images du cours (slides 100, 102 et 109, rendus en PNG
# et lus) avant d'etre traduits en traits. Deux os en vis-a-vis (rectangles),
# chacun coiffe d'un arc plus epais (cartilage articulaire) ; entre eux, la
# cavite articulaire (l'espace vide central, ou loge le liquide synovial) et
# le menisque (un anneau de fibrocartilage, ici vu en coupe, ancre a la capsule
# interne cote gauche, conformement au texte "face adherente a la capsule") ;
# autour, DEUX enveloppes en poin-
# tilles concentriques (la capsule : fibreuse=exterieure, synoviale=interieu-
# re) ; a l'exterieur de la capsule, un trait plein continu : un ligament
# EXTRACAPSULAIRE (comme les lateraux du genou, slide 104). Ce n'est qu'une des
# deux sortes de ligaments : le cours distingue aussi les ligaments
# INTRACAPSULAIRES (les croises du genou), a l'interieur de la capsule -- d'ou le
# libelle « Ligament extracapsulaire », qui dit ce que le trace montre.
#
# Viewbox large (620x460) et libelles courts (~22 caracteres, meme plafond
# que "Cartilage articulaire" sur os-long-coupe ; « Ligament extracapsulaire » en
# compte 24 mais tient : ~180 unites estimees pour 214 disponibles a droite de
# l'ancre) : une premiere version avec
# "Capsule : membrane fibreuse" et "Cavité articulaire (liquide synovial)"
# debordait du cadre une fois decalee par son ancre (~7 px/caractere a cette
# echelle, cf. le calcul de marge d'os-long-coupe) -- verifie par rendu reel
# (rsvg-convert) avant d'etre corrige ici. Chaque libelle rejoint sa structure
# par un repere (fleche fine), le point de depart choisi du cote ou la
# structure est reellement visible (fibreuse/synoviale/menisque a gauche,
# cartilage/cavite/ligament a droite).
_DESSIN_ARTICULATION_SYNOVIALE = (
    "<rect x='260' y='20' width='40' height='150' fill='none' "
    "stroke='currentColor' stroke-width='2'/>"
    "<path d='M248,178 Q280,215 312,178' fill='none' stroke='currentColor' "
    "stroke-width='4'/>"
    "<rect x='260' y='290' width='40' height='150' fill='none' "
    "stroke='currentColor' stroke-width='2'/>"
    "<path d='M248,282 Q280,245 312,282' fill='none' stroke='currentColor' "
    "stroke-width='4'/>"
    "<path d='M230,196 Q223,230 230,264 Q250,240 262,230 Q250,220 230,196 Z' "
    "fill='none' stroke='currentColor' stroke-width='2'/>"
    "<path d='M260,150 Q205,225 260,300' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-dasharray='6 4'/>"
    "<path d='M300,150 Q355,225 300,300' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-dasharray='6 4'/>"
    "<path d='M260,158 Q222,225 260,292' fill='none' stroke='currentColor' "
    "stroke-width='1.2' stroke-dasharray='3 3'/>"
    "<path d='M300,158 Q338,225 300,292' fill='none' stroke='currentColor' "
    "stroke-width='1.2' stroke-dasharray='3 3'/>"
    "<path d='M300,120 Q385,225 300,330' fill='none' stroke='currentColor' "
    "stroke-width='3'/>"
    + _DEFS_FLECHE
    + "<g class='reperes' fill='none' stroke='currentColor' stroke-width='1.2'>"
    "<path d='M245,165 L188,150' marker-end='url(#fleche)'/>"
    "<path d='M234,230 L188,230' marker-end='url(#fleche)'/>"
    "<path d='M254,268 L188,318' marker-end='url(#fleche)'/>"
    "<path d='M303,182 L372,150' marker-end='url(#fleche)'/>"
    "<path d='M290,228 L372,230' marker-end='url(#fleche)'/>"
    "<path d='M335,270 L372,318' marker-end='url(#fleche)'/>"
    "</g>"
)

_PASTILLES_ARTICULATION_SYNOVIALE = [
    {
        "n": 1,
        "x": 170,
        "y": 150,
        "t": "Membrane fibreuse",
        "ancre": "end",
        "indice": "couche externe de la capsule, résistante, peu élastique",
    },
    {
        "n": 2,
        "x": 170,
        "y": 230,
        "t": "Ménisque",
        "ancre": "end",
        "indice": "anneau de fibrocartilage, adhérent à la capsule",
    },
    {
        "n": 3,
        "x": 170,
        "y": 320,
        "t": "Membrane synoviale",
        "ancre": "end",
        "indice": "couche interne de la capsule, sécrète le liquide synovial",
    },
    {
        "n": 4,
        "x": 390,
        "y": 150,
        "t": "Cartilage articulaire",
        "ancre": "start",
        "indice": "coiffe l'extrémité de chaque os",
    },
    {
        "n": 5,
        "x": 390,
        "y": 230,
        "t": "Cavité articulaire",
        "ancre": "start",
        "indice": "espace entre les deux surfaces, où loge le liquide synovial",
    },
    {
        "n": 6,
        "x": 390,
        "y": 320,
        "t": "Ligament extracapsulaire",
        "ancre": "start",
        "indice": "relie les deux os, ici hors de la capsule",
    },
]

PLANCHES["articulation-synoviale-coupe"] = {
    "id": "articulation-synoviale-coupe",
    "titre": "L'articulation synoviale type, en coupe",
    "vb": "0 0 620 460",
    "dessin": _DESSIN_ARTICULATION_SYNOVIALE,
    "pastilles": _PASTILLES_ARTICULATION_SYNOVIALE,
}

# --- Chapitre 4 : les enveloppes du muscle, en coupe (slide 117) --------
#
# Slide 117 ("A- STRUCTURE MACROSCOPIQUE") donne le texte (epimysium /
# perimysium / endomysium / sarcolemme) ; la photo qui l'accompagne (meme
# slide, rendue en PNG et lue) confirme l'emboitement : muscle entier, coupe
# ouverte sur un faisceau de fibres, coupe ouverte sur une fibre (sarcoplasme
# + sarcolemme + myofibrille + noyau).
#
# Ce chapitre est le plus conceptuel du cours : presque rien a situer dans
# l'espace, beaucoup a definir avec precision -- l'emboitement de structure
# est la seule notion assez spatiale pour un schema. Choix de forme : une
# bullseye (cercles concentriques centres en un seul point), pas une coupe
# "photo-realiste" -- ce qui compte pour le mode muet n'est PAS que chaque
# cercle "ressemble" a son enveloppe (impossible : ce sont 4 emboitements du
# meme genre de chose, a des echelles differentes), mais que les 4 niveaux
# soient GEOMETRIQUEMENT distincts, pas seulement numerotes. D'ou 4 rayons
# nettement etages ET 4 grammaires de trait differentes (epais continu /
# tirets larges / tirets fins / fin continu) : la profondeur ET le style de
# trait portent l'information, independamment du numero de pastille.
#
# Endomysium et sarcolemme sont volontairement les deux plus proches (44 et
# 36, un ecart de 8 seulement) : le texte du cours les presente lui-meme
# comme "colles" (l'endomysium "elle-meme recouverte par une deuxieme
# membrane, le sarcolemme") -- cet ecart resserre visuellement traduit le
# piege le plus attendu (enveloppe de la fibre contre deuxieme membrane de la
# fibre), sans les rendre indiscernables (trait continu contre tirets fins).
#
# Semis de points au centre (r<32, sous le cercle du sarcolemme) : matiere
# de la fibre elle-meme (sarcoplasme/myofibrilles), pour que le coeur de la
# bullseye ne se lise pas comme un simple disque vide -- coordonnees fixes
# (pas de generateur aleatoire), sur le meme principe que le semis de
# l'os spongieux (chapitre 2, os-long-coupe).
#
# 4 pastilles seulement (les enveloppes) : la fibre/myofibrille/sarcomere
# emboitees a l'interieur sont une notion distincte, portee par la planche
# suivante (sarcomere-stries-z), pas par celle-ci.
_CX_ENV, _CY_ENV = 150, 140

_POINTS_SARCOPLASME = (
    "<circle cx='138' cy='128' r='1.6'/><circle cx='150' cy='122' r='1.6'/>"
    "<circle cx='162' cy='128' r='1.6'/><circle cx='144' cy='140' r='1.6'/>"
    "<circle cx='156' cy='140' r='1.6'/><circle cx='168' cy='138' r='1.6'/>"
    "<circle cx='132' cy='148' r='1.6'/><circle cx='150' cy='152' r='1.6'/>"
    "<circle cx='168' cy='150' r='1.6'/><circle cx='140' cy='162' r='1.6'/>"
    "<circle cx='158' cy='164' r='1.6'/><circle cx='126' cy='138' r='1.6'/>"
    "<circle cx='174' cy='144' r='1.6'/><circle cx='146' cy='116' r='1.6'/>"
)

_DESSIN_ENVELOPPES_MUSCLE = (
    f"<circle cx='{_CX_ENV}' cy='{_CY_ENV}' r='115' fill='none' "
    "stroke='currentColor' stroke-width='3'/>"
    f"<circle cx='{_CX_ENV}' cy='{_CY_ENV}' r='78' fill='none' "
    "stroke='currentColor' stroke-width='2' stroke-dasharray='8 5'/>"
    f"<circle cx='{_CX_ENV}' cy='{_CY_ENV}' r='44' fill='none' "
    "stroke='currentColor' stroke-width='1.4' stroke-dasharray='3 3'/>"
    f"<circle cx='{_CX_ENV}' cy='{_CY_ENV}' r='36' fill='none' "
    "stroke='currentColor' stroke-width='1.6'/>"
    f"<g fill='currentColor' stroke='none'>{_POINTS_SARCOPLASME}</g>"
)

_PASTILLES_ENVELOPPES_MUSCLE = [
    {
        "n": 1,
        "x": 222,
        "y": 50,
        "t": "Épimysium",
        "ancre": "start",
        "indice": "gaine externe, autour du muscle entier",
    },
    {
        "n": 2,
        "x": 205,
        "y": 195,
        "t": "Périmysium",
        "ancre": "start",
        "indice": "autour d'un faisceau musculaire",
    },
    {
        "n": 3,
        "x": 119,
        "y": 171,
        "t": "Endomysium",
        "ancre": "end",
        "indice": "autour d'une fibre musculaire",
    },
    {
        "n": 4,
        "x": 125,
        "y": 115,
        "t": "Sarcolemme",
        "ancre": "end",
        "indice": "deuxième membrane qui recouvre la fibre",
    },
]

PLANCHES["enveloppes-muscle-coupe"] = {
    "id": "enveloppes-muscle-coupe",
    "titre": "Les enveloppes du muscle, en coupe",
    "vb": "0 0 320 280",
    "dessin": _DESSIN_ENVELOPPES_MUSCLE,
    "pastilles": _PASTILLES_ENVELOPPES_MUSCLE,
}

# --- Chapitre 4 : le sarcomere, entre deux stries Z (slides 119-120) ----
#
# Texte (slide 119) : la myofibrille est composee de sarcomeres, delimites
# par des stries Z ; la contraction s'y deroule via 2 myofilaments, la
# myosine (filament epais) et l'actine (filament fin). Le schema-image de
# la slide 120 (rendu en PNG et lu) confirme la disposition : dans un
# sarcomere, l'actine part de CHAQUE strie Z vers le centre, la myosine
# occupe la portion centrale, les deux filaments se chevauchant.
#
# 4 rangees paralleles (l'aspect "faisceau de myofilaments" de la
# myofibrille) plutot qu'une seule ligne : une seule rangee se serait lue
# comme "une fibre", pas comme l'empilement reel. Chaque rangee suit le
# meme schema fin-epais-fin (epaisseur de trait 1.6 puis 7 puis 1.6) : le
# contraste d'EPAISSEUR est le seul signal necessaire pour distinguer
# myosine et actine en mode muet, sans avoir besoin de texture ou de
# couleur (le trace n'utilise que currentColor, regle CSS section 1).
#
# Reperes courts (deux traits verticaux de 14 unites) dans les BLANCS entre
# deux rangees : sans eux, le libelle d'une pastille posee directement sur
# une rangee chevaucherait le trace de cette meme rangee (verifie par rendu
# reel -- rsvg-convert -- avant correction ; une premiere version sans repere
# faisait passer "Myosine (épais)" en travers de la rangee qu'elle designe).
_Z_GAUCHE, _Z_DROITE = 25, 275
_Z_HAUT, _Z_BAS = 45, 155
_RANGEES_SARCOMERE = (65, 90, 115, 140)

_rangees_svg = []
for _y in _RANGEES_SARCOMERE:
    _rangees_svg.append(
        f"<path d='M{_Z_GAUCHE},{_y} L140,{_y}' stroke-width='1.6'/>"
        f"<path d='M110,{_y} L190,{_y}' stroke-width='7'/>"
        f"<path d='M160,{_y} L{_Z_DROITE},{_y}' stroke-width='1.6'/>"
    )
_RANGEES_SARCOMERE_SVG = "".join(_rangees_svg)

_DESSIN_SARCOMERE = (
    "<g fill='none' stroke='currentColor' stroke-linecap='round'>"
    f"{_RANGEES_SARCOMERE_SVG}</g>"
    f"<path d='M{_Z_GAUCHE},{_Z_HAUT} L{_Z_GAUCHE},{_Z_BAS}' "
    "stroke='currentColor' stroke-width='5' fill='none'/>"
    f"<path d='M{_Z_DROITE},{_Z_HAUT} L{_Z_DROITE},{_Z_BAS}' "
    "stroke='currentColor' stroke-width='5' fill='none'/>"
    # Accolade du sarcomere (deux petites chutes verticales + un trait
    # horizontal), au-dessus des deux stries Z.
    f"<path d='M{_Z_GAUCHE},35 L{_Z_GAUCHE},45 M{_Z_GAUCHE},35 L{_Z_DROITE},35 "
    f"M{_Z_DROITE},35 L{_Z_DROITE},45' stroke='currentColor' stroke-width='1.2' "
    "fill='none'/>"
    # Reperes courts, dans les blancs entre deux rangees (cf. note ci-dessus).
    "<g stroke='currentColor' stroke-width='1.2' fill='none'>"
    "<path d='M70,66 L70,80'/>"
    "<path d='M150,91 L150,102'/>"
    "</g>"
)

_PASTILLES_SARCOMERE = [
    {
        "n": 1,
        "x": 150,
        "y": 35,
        "t": "Sarcomère",
        "ancre": "start",
        "indice": "segment de myofibrille entre deux stries Z",
    },
    {
        "n": 2,
        "x": _Z_GAUCHE,
        "y": 50,
        "t": "Strie Z",
        "ancre": "start",
        "indice": "ligne qui délimite chaque sarcomère",
    },
    {
        "n": 3,
        "x": 150,
        "y": 102,
        "t": "Myosine (épais)",
        "ancre": "end",
        "indice": "au centre du sarcomère",
    },
    {
        "n": 4,
        "x": 70,
        "y": 80,
        "t": "Actine (filament fin)",
        "ancre": "start",
        "indice": "part de chaque strie Z vers le centre",
    },
]

PLANCHES["sarcomere-stries-z"] = {
    "id": "sarcomere-stries-z",
    "titre": "Le sarcomère, entre deux stries Z",
    "vb": "0 0 300 180",
    "dessin": _DESSIN_SARCOMERE,
    "pastilles": _PASTILLES_SARCOMERE,
}


# --- Chapitre 5 : le tronc (rachis, thorax, myologie du tronc) ---------
PLANCHES["rachis-courbures-regions"] = {
    "id": "rachis-courbures-regions",
    "titre": "Les 4 courbures du rachis, de haut en bas",
    "vb": "0 0 280 560",
    "dessin": "<g fill='none' stroke='currentColor'><circle cx='140' cy='18' r='7' stroke-width='2'/><path d='M140,25 C180,55 180,120 140,150 C100,180 100,245 140,275 C180,305 180,370 140,400 C100,430 100,495 122,525 L127,543' stroke-width='5' stroke-linecap='round'/><path d='M40,150 L235,150 M40,275 L235,275 M40,400 L235,400' stroke-width='1' stroke-dasharray='4 4'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 172,
            "y": 90,
            "t": "Lordose cervicale",
            "ancre": "middle",
            "indice": "1re courbure, en haut",
        },
        {
            "n": 2,
            "x": 108,
            "y": 215,
            "t": "Cyphose dorsale",
            "ancre": "middle",
            "indice": "2e courbure",
        },
        {
            "n": 3,
            "x": 172,
            "y": 340,
            "t": "Lordose lombaire",
            "ancre": "middle",
            "indice": "3e courbure",
        },
        {
            "n": 4,
            "x": 108,
            "y": 465,
            "t": "Courbure sacro-coccygienne",
            "ancre": "middle",
            "indice": "4e courbure ; sacrum et coccyx soudés",
        },
    ],
}
PLANCHES["vertebre-vue-superieure"] = {
    "id": "vertebre-vue-superieure",
    "titre": "La vertèbre type, vue de dessus",
    "vb": "0 0 320 330",
    "dessin": "<g fill='none' stroke='currentColor' stroke-width='2.4' stroke-linecap='round'><circle cx='160' cy='55' r='38'/><path d='M135,88 L110,145'/><path d='M185,88 L210,145'/><path d='M110,145 Q120,190 160,220'/><path d='M210,145 Q200,190 160,220'/><path d='M160,220 L160,270'/><path d='M112,142 L35,175'/><path d='M208,142 L285,175'/></g><circle cx='160' cy='180' r='32' fill='none' stroke='currentColor' stroke-width='1.2' stroke-dasharray='3 3'/>",
    "pastilles": [
        {
            "n": 1,
            "x": 160,
            "y": 55,
            "t": "Corps vertébral",
            "ancre": "middle",
            "indice": "partie antérieure, cylindrique",
        },
        {
            "n": 2,
            "x": 130,
            "y": 100,
            "t": "Pédicule",
            "ancre": "end",
            "indice": "×2 ; passage des nerfs rachidiens",
        },
        {
            "n": 3,
            "x": 35,
            "y": 175,
            "t": "Processus transverse",
            "ancre": "start",
            "indice": "×2, latéral",
        },
        {
            "n": 4,
            "x": 160,
            "y": 200,
            "t": "Canal rachidien",
            "ancre": "middle",
            "indice": "passage de la moelle épinière",
        },
        {
            "n": 5,
            "x": 160,
            "y": 270,
            "t": "Processus épineux",
            "ancre": "middle",
            "indice": "×1, médian postérieur",
        },
    ],
}
PLANCHES["fibres-abdominales-orientation"] = {
    "id": "fibres-abdominales-orientation",
    "titre": "Orientation des fibres des 4 muscles abdominaux",
    "vb": "0 0 300 700",
    "dessin": "<g fill='none' stroke='currentColor' stroke-width='2'><rect x='30' y='20' width='240' height='100' rx='6'/><path d='M45,35 L255,35'/><path d='M45,52 L255,52'/><path d='M45,69 L255,69'/><path d='M45,86 L255,86'/><path d='M45,103 L255,103'/></g><g fill='none' stroke='currentColor' stroke-width='2'><rect x='30' y='190' width='240' height='100' rx='6'/><path d='M150,290 L60,190'/><path d='M150,290 L90,190'/><path d='M150,290 L120,190'/><path d='M150,290 L150,190'/><path d='M150,290 L180,190'/><path d='M150,290 L210,190'/><path d='M150,290 L240,190'/></g><g fill='none' stroke='currentColor' stroke-width='2'><rect x='30' y='360' width='240' height='100' rx='6'/><path d='M70,360 L30,460'/><path d='M105,360 L65,460'/><path d='M140,360 L100,460'/><path d='M175,360 L135,460'/><path d='M210,360 L170,460'/><path d='M245,360 L205,460'/></g><g fill='none' stroke='currentColor' stroke-width='2'><rect x='30' y='530' width='240' height='100' rx='6'/><path d='M80,540 L80,620'/><path d='M100,540 L100,620'/><path d='M120,540 L120,620'/><path d='M180,540 L180,620'/><path d='M200,540 L200,620'/><path d='M220,540 L220,620'/><path d='M75,560 L125,560 M175,560 L225,560'/><path d='M75,590 L125,590 M175,590 L225,590'/><path d='M150,528 L150,632' stroke-dasharray='3 3'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 150,
            "y": 138,
            "t": "Transverse de l'abdomen",
            "ancre": "middle",
            "indice": "le plus profond ; fibres transversales",
        },
        {
            "n": 2,
            "x": 150,
            "y": 308,
            "t": "Oblique interne",
            "ancre": "middle",
            "indice": "fibres en éventail vers le haut",
        },
        {
            "n": 3,
            "x": 150,
            "y": 478,
            "t": "Oblique externe",
            "ancre": "middle",
            "indice": "fibres obliques vers le bas",
        },
        {
            "n": 4,
            "x": 150,
            "y": 648,
            "t": "Droit de l'abdomen",
            "ancre": "middle",
            "indice": "de part et d'autre de la ligne blanche ; fibres verticales",
        },
    ],
}


# --- Chapitre 6 : le membre supérieur (squelette, scapula, deltoïde, coiffe) ---
PLANCHES["squelette-membre-superieur-articulations"] = {
    "id": "squelette-membre-superieur-articulations",
    "titre": "Le squelette du membre supérieur et ses articulations",
    "vb": "0 0 300 640",
    "dessin": "<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M70,45 Q105,32 150,58' stroke-width='6' stroke-linecap='round'/><path d='M150,58 L150,140'/><path d='M150,145 L150,325' stroke-width='11' stroke-linecap='round'/><path d='M150,325 L70,345'/><path d='M150,325 L230,345'/><path d='M70,350 L92,515' stroke-width='8' stroke-linecap='round'/><path d='M230,350 L198,540' stroke-width='8' stroke-linecap='round'/><path d='M78,522 L142,540 L128,600 Q108,612 88,598 Z' stroke-width='2'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 70,
            "y": 45,
            "t": "Sterno-claviculaire",
            "ancre": "middle",
            "indice": "extrémité médiale (sternale) de la clavicule",
        },
        {
            "n": 2,
            "x": 150,
            "y": 58,
            "t": "Acromio-claviculaire",
            "ancre": "middle",
            "indice": "extrémité latérale (acromiale) de la clavicule",
        },
        {
            "n": 3,
            "x": 150,
            "y": 143,
            "t": "Scapulo-humérale",
            "ancre": "middle",
            "indice": "cavité glénoïdale + tête humérale",
        },
        {
            "n": 4,
            "x": 70,
            "y": 345,
            "t": "Huméro-ulnaire",
            "ancre": "middle",
            "indice": "coude, côté médial (ulna)",
        },
        {
            "n": 5,
            "x": 230,
            "y": 345,
            "t": "Huméro-radiale",
            "ancre": "middle",
            "indice": "coude, côté latéral (radius)",
        },
        {
            "n": 6,
            "x": 150,
            "y": 395,
            "t": "Radio-ulnaire proximale",
            "ancre": "middle",
            "indice": "entre radius et ulna, juste sous le coude",
        },
        {
            "n": 7,
            "x": 198,
            "y": 545,
            "t": "Radio-carpienne",
            "ancre": "middle",
            "indice": "poignet ; radius + scaphoïde + lunatum",
        },
        {
            "n": 8,
            "x": 92,
            "y": 515,
            "t": "Radio-ulnaire distale",
            "ancre": "middle",
            "indice": "entre radius et ulna, côté médial du poignet",
        },
    ],
}
PLANCHES["scapula-reperes"] = {
    "id": "scapula-reperes",
    "titre": "La scapula, vue postérieure : ses repères",
    "vb": "0 0 300 320",
    "dessin": "<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M75,55 L215,92 L108,300 Z'/><path d='M92,92 L202,113' stroke-width='4'/><path d='M202,113 Q223,100 228,78' stroke-width='4' stroke-linecap='round'/><path d='M192,78 Q183,50 206,44' stroke-width='4' stroke-linecap='round'/><ellipse cx='207' cy='122' rx='15' ry='11'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 202,
            "y": 47,
            "t": "Processus coracoïde",
            "ancre": "middle",
            "indice": "crochet à l'avant, lieu d'insertions musculaires",
        },
        {
            "n": 2,
            "x": 140,
            "y": 100,
            "t": "Épine",
            "ancre": "middle",
            "indice": "crête qui traverse la face postérieure",
        },
        {
            "n": 3,
            "x": 228,
            "y": 78,
            "t": "Acromion",
            "ancre": "middle",
            "indice": "extrémité latérale de l'épine ; articulation acromio-claviculaire",
        },
        {
            "n": 4,
            "x": 207,
            "y": 122,
            "t": "Cavité glénoïdale",
            "ancre": "middle",
            "indice": "reçoit la tête humérale",
        },
    ],
}
PLANCHES["deltoide-trois-faisceaux"] = {
    "id": "deltoide-trois-faisceaux",
    "titre": "Le deltoïde, vue latérale : ses 3 faisceaux",
    "vb": "0 0 300 300",
    "dessin": "<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M65,40 Q105,26 148,46'/><path d='M152,46 Q195,42 235,58'/><circle cx='150' cy='46' r='4' fill='currentColor' stroke='none'/><path d='M150,88 L150,335' stroke-width='11' stroke-linecap='round'/></g><g class='faisceau' fill='none' stroke='currentColor' stroke-width='1.4'><path d='M65,40 L128,180'/><path d='M65,40 L140,196'/><path d='M65,40 L150,212'/><path d='M150,46 L144,180'/><path d='M150,46 L150,196'/><path d='M150,46 L156,212'/><path d='M235,58 L172,180'/><path d='M235,58 L160,196'/><path d='M235,58 L150,212'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 78,
            "y": 100,
            "t": "Claviculaire",
            "ancre": "middle",
            "indice": "faisceau antérieur, origine sur la clavicule",
        },
        {
            "n": 2,
            "x": 150,
            "y": 56,
            "t": "Acromial",
            "ancre": "middle",
            "indice": "faisceau intermédiaire, origine sur l'acromion",
        },
        {
            "n": 3,
            "x": 222,
            "y": 100,
            "t": "Épineux",
            "ancre": "middle",
            "indice": "faisceau postérieur, origine sur l'épine de la scapula",
        },
        {
            "n": 4,
            "x": 150,
            "y": 228,
            "t": "Tubérosité deltoïdienne",
            "ancre": "middle",
            "indice": "insertion commune des 3 faisceaux, sur l'humérus",
        },
    ],
}
PLANCHES["coiffe-rotateurs-vue-postero-laterale"] = {
    "id": "coiffe-rotateurs-vue-postero-laterale",
    "titre": "La coiffe des rotateurs, vue postéro-latérale",
    "vb": "0 0 300 340",
    "dessin": "<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M100,40 L240,90 L130,340 Z'/><path d='M115,95 L225,115' stroke-width='3'/><path d='M225,115 Q245,100 250,80' stroke-width='3' stroke-linecap='round'/><circle cx='255' cy='150' r='26'/></g><g class='muscle' fill='none' stroke='currentColor' stroke-width='1.3'><path d='M130,60 L235,128'/><path d='M150,70 L238,138'/><path d='M170,80 L236,148'/><path d='M130,150 L232,158'/><path d='M140,190 L228,165'/><path d='M150,230 L224,172'/><path d='M150,260 L220,180'/><path d='M155,285 L216,186'/><path d='M150,300 L214,192' stroke-dasharray='3 3'/><path d='M155,320 L212,198' stroke-dasharray='3 3'/></g>",
    "pastilles": [
        {
            "n": 1,
            "x": 150,
            "y": 68,
            "t": "Supra-épineux",
            "ancre": "middle",
            "indice": "au-dessus de l'épine ; le plus fragile de la coiffe",
        },
        {
            "n": 2,
            "x": 165,
            "y": 180,
            "t": "Infra-épineux",
            "ancre": "middle",
            "indice": "sous l'épine",
        },
        {
            "n": 3,
            "x": 158,
            "y": 268,
            "t": "Petit rond",
            "ancre": "middle",
            "indice": "bord latéral, sous l'infra-épineux",
        },
        {
            "n": 4,
            "x": 152,
            "y": 308,
            "t": "Subscapulaire",
            "ancre": "middle",
            "indice": "face antérieure ; non visible de dos, figuré en pointillé",
        },
    ],
}
# --- Chapitre 7 : le membre inferieur ----------------------------------------------
#
# Reprise « emprise du texte » (contenu/schema.py) : douze libelles de trois planches
# depassaient du viewBox et etaient rognes -- « Tete de la fibula » a 77 %. Les
# planches gardent leur trace ; on leur redonne de la place, sans jamais depasser
# 310 unites de large (regle du chapitre, 320 au plus : le libelle reste a ~12 px
# sur un telephone de 320 px, alors qu'a 352 unites il tomberait a ~10 px).
#
# - quadriceps, ischio-jambiers : trace decale (_translater), viewBox elargi a 300 / 310.
#   Les ancres qui ne tenaient pas meme ainsi changent de place ou de cote (voir
#   chaque planche).
# - squelette du membre inferieur : deux libelles ne peuvent pas cohabiter dans
#   300 unites avec le genou entre eux (« Tibio-femorale » a gauche, 102 unites ;
#   « Tibio-fibulaire proximale » a droite, 170 unites : il faudrait 352). La
#   planche est donc DECOUPEE en deux, comme les trois plans (ch. 1) et les sept
#   diarthroses (ch. 3) : bassin-hanche-genou d'un cote, jambe-cheville de l'autre.
#   Le nombre total de pastilles (6) est inchange.

# Tracé commun aux deux moities du squelette du membre inferieur (coordonnees de
# la planche d'origine ; chaque moitie le decale et le rogne a sa fenetre).
_OS_MEMBRE_INFERIEUR_HAUT = (
    "<g class='os' fill='none' stroke='currentColor' stroke-width='2'>"
    "<path d='M90,20 L190,20 L175,95 L105,95 Z'/>"
    "<circle cx='140' cy='95' r='7'/>"
    "<path d='M120,85 Q140,72 160,85' stroke-width='2'/>"
    "<path d='M140,95 L128,380' stroke-width='11' stroke-linecap='round'/>"
    "<circle cx='128' cy='390' r='9'/>"
    # Amorces du tibia et de la fibula : la planche s'arrete sous le genou.
    "<path d='M128,400 L126,430' stroke-width='9' stroke-linecap='round'/>"
    "<path d='M150,405 L149,430' stroke-width='5' stroke-linecap='round'/>"
    "</g>"
)
_OS_MEMBRE_INFERIEUR_BAS = (
    "<g class='os' fill='none' stroke='currentColor' stroke-width='2'>"
    # Amorce du femur et genou, au ras du bord haut : repere pour situer la jambe.
    "<path d='M129,372 L128,381' stroke-width='11' stroke-linecap='round'/>"
    "<circle cx='128' cy='390' r='9'/>"
    "<path d='M128,400 L120,560' stroke-width='9' stroke-linecap='round'/>"
    "<path d='M150,405 L145,555' stroke-width='5' stroke-linecap='round'/>"
    "<path d='M120,560 L80,585 L135,598 Z'/>"
    "</g>"
)

PLANCHES["squelette-membre-inferieur-articulations"] = {
    "id": "squelette-membre-inferieur-articulations",
    "titre": "Le squelette du membre inférieur : bassin, hanche et genou",
    # Decale de 14 : « Tibio-femorale » (ancre « end », a gauche du genou) butait sur
    # le bord gauche ; « Femoro-patellaire » (a droite) borne la largeur a 290.
    "vb": "0 0 290 445",
    "dessin": _translater(_OS_MEMBRE_INFERIEUR_HAUT, 14),
    "pastilles": [
        {
            "n": 1,
            "x": 164,
            "y": 30,
            "t": "Sacro-iliaque",
            "ancre": "middle",
            "indice": "où le sacrum rejoint l'ilium, en haut de la ceinture pelvienne",
        },
        {
            "n": 2,
            "x": 154,
            "y": 95,
            "t": "Coxo-fémorale",
            "ancre": "middle",
            "indice": "hanche ; acétabulum + tête fémorale",
        },
        {
            "n": 3,
            "x": 142,
            "y": 390,
            "t": "Fémoro-patellaire",
            "ancre": "start",
            "indice": "la patella, en avant du genou",
        },
        {
            "n": 4,
            "x": 124,
            "y": 398,
            "t": "Tibio-fémorale",
            "ancre": "end",
            "indice": "genou ; entre les 2 os longs",
        },
    ],
}
PLANCHES["squelette-membre-inferieur-jambe-cheville"] = {
    "id": "squelette-membre-inferieur-jambe-cheville",
    "titre": "Le squelette du membre inférieur : jambe et cheville",
    # Fenetre sur le bas du meme trace (decalage -48 en x, -376 en y) : la fibula est
    # a droite du tibia, et « Tibio-fibulaire proximale » (170 unites) s'etend vers la
    # droite ; le trace est pousse a gauche pour que cela tienne dans 296.
    "vb": "0 0 296 236",
    "dessin": _translater(_OS_MEMBRE_INFERIEUR_BAS, -48, -376),
    "pastilles": [
        {
            "n": 1,
            "x": 102,
            "y": 32,
            "t": "Tibio-fibulaire proximale",
            "ancre": "start",
            "indice": "juste sous le genou, côté fibula",
        },
        {
            "n": 2,
            "x": 74,
            "y": 184,
            "t": "Talo-crurale",
            "ancre": "middle",
            "indice": "cheville ; tibia + fibula + talus",
        },
    ],
}
PLANCHES["os-coxal-trois-parties"] = {
    "id": "os-coxal-trois-parties",
    "titre": "L'os coxal, vue latérale : ses 3 parties",
    # Decale de 10 : l'etiquette « Acetabulum » passe a gauche de l'anneau (pastille
    # sur son bord gauche, ancre « end »). Sous l'anneau, elle recouvrait a 19 % le
    # contour de l'anneau et le haut de l'ischium et du pubis.
    "vb": "0 0 230 300",
    "dessin": _translater("<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M115,130 Q60,40 90,15 Q160,5 175,55 Q170,100 145,132 Z'/><path d='M112,168 Q60,190 55,240 Q65,270 100,260 Q130,240 128,175 Z'/><path d='M148,168 Q195,185 200,225 Q195,255 160,250 Q132,235 132,175 Z'/><circle cx='130' cy='150' r='22'/></g>", 10),
    "pastilles": [
        {
            "n": 1,
            "x": 130,
            "y": 40,
            "t": "Ilium",
            "ancre": "middle",
            "indice": "partie supérieure, la plus large",
        },
        {
            "n": 2,
            "x": 118,
            "y": 150,
            "t": "Acétabulum",
            "ancre": "end",
            "indice": "anneau central ; reçoit la tête fémorale (coxo-fémorale)",
        },
        {
            "n": 3,
            "x": 90,
            "y": 245,
            "t": "Ischium",
            "ancre": "middle",
            "indice": "partie postéro-inférieure",
        },
        {
            "n": 4,
            "x": 185,
            "y": 235,
            "t": "Pubis",
            "ancre": "middle",
            "indice": "partie antéro-inférieure",
        },
    ],
}
PLANCHES["quadriceps-quatre-chefs"] = {
    "id": "quadriceps-quatre-chefs",
    "titre": "Le quadriceps fémoral : ses 4 chefs, une terminaison commune",
    # Trace decale de 17, viewBox 220 -> 300 : « Droit femoral » (a gauche) et « Vaste
    # intermediaire » (a droite, 135 unites) depassaient chacun d'un cote.
    "vb": "0 0 300 400",
    "dessin": _translater("<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M118,22 L118,300' stroke-width='9' stroke-linecap='round'/><circle cx='75' cy='16' r='6'/><circle cx='118' cy='308' r='10'/><path d='M118,318 L112,360' stroke-width='6' stroke-linecap='round'/><path d='M112,360 L108,390' stroke-width='8' stroke-linecap='round'/></g><g class='muscle' fill='none' stroke='currentColor' stroke-width='1.6'><path d='M75,18 L118,306'/><path d='M85,160 L118,306'/><path d='M155,190 L118,306'/><path d='M126,88 L126,298' stroke-dasharray='4 3'/></g>", 17),
    "pastilles": [
        {
            "n": 1,
            "x": 113,
            "y": 162,
            "t": "Droit fémoral",
            "ancre": "end",
            "indice": "seul chef dont l'origine est détachée du fémur, plus haut (os coxal)",
        },
        {
            "n": 2,
            "x": 118,
            "y": 233,
            "t": "Vaste latéral",
            "ancre": "end",
            "indice": "origine sur le bord latéral du fémur, côté gauche du schéma",
        },
        {
            "n": 3,
            "x": 153,
            "y": 248,
            "t": "Vaste médial",
            "ancre": "start",
            "indice": "seul chef dont l'origine arrive du côté droit du schéma",
        },
        {
            "n": 4,
            "x": 143,
            "y": 88,
            "t": "Vaste intermédiaire",
            "ancre": "start",
            "indice": "trait pointillé, tout contre le fémur ; origine : face antérieure du fémur",
        },
        {
            "n": 5,
            "x": 131,
            "y": 335,
            "t": "Ligament patellaire",
            "ancre": "middle",
            "indice": "terminaison commune des 4 chefs, sous la patella",
        },
    ],
}
PLANCHES["ischio-jambiers-trois-terminaisons"] = {
    "id": "ischio-jambiers-trois-terminaisons",
    "titre": "Les ischio-jambiers : 3 terminaisons différentes",
    # Trace decale de 43, viewBox 220 -> 310, et des ancres deplacees : les libelles
    # de 90 a 130 unites ne tenaient d'aucun cote d'un trace de 120 unites de large.
    # Chaque pastille reste sur SON trajet, a au moins 11 unites des deux autres
    # (le muet doit rester lisible sans libelle) :
    #   - Biceps femoral : remonte de y=170 a y=95 sur son trajet (il croisait le
    #     libelle du semi-tendineux, 12 unites plus bas) ;
    #   - Semi-membraneux : descendu a y=128 sur son trajet, ou les trois trajets sont
    #     assez ecartes, et libelle a gauche (ancre « end ») : 133 unites de texte
    #     n'ont de place que la, decalage de 43 compris ;
    #   - Tete de la fibula : libelle SOUS la pastille (ancre « middle ») ;
    #   - Plateau tibial : pastille sur l'extremite gauche de la barre, pour que le
    #     libelle (a gauche, ancre « end ») ne recouvre pas la barre.
    "vb": "0 0 310 400",
    "dessin": _translater("<g class='os' fill='none' stroke='currentColor' stroke-width='2'><path d='M130,28 L122,280' stroke-width='2' stroke-dasharray='2 3'/><circle cx='130' cy='20' r='8'/><circle cx='180' cy='320' r='7'/><circle cx='100' cy='345' r='7'/><path d='M65,280 L95,280' stroke-width='4' stroke-linecap='round'/></g><g class='muscle' fill='none' stroke='currentColor' stroke-width='1.6'><path d='M130,20 L180,320'/><path d='M130,20 L100,345'/><path d='M130,20 L80,280'/></g>", 43),
    "pastilles": [
        {
            "n": 1,
            "x": 173,
            "y": 20,
            "t": "Tubérosité ischiatique",
            "ancre": "middle",
            "indice": "origine du semi-tendineux, du semi-membraneux et du chef long du biceps, en haut",
        },
        {
            "n": 2,
            "x": 185,
            "y": 95,
            "t": "Biceps fémoral",
            "ancre": "start",
            "indice": "le trajet le plus latéral (vers la droite) ; tracé du chef long",
        },
        {
            "n": 3,
            "x": 158,
            "y": 182,
            "t": "Semi-tendineux",
            "ancre": "start",
            "indice": "trajet médial, le plus long (le plus bas)",
        },
        {
            "n": 4,
            "x": 152,
            "y": 128,
            "t": "Semi-membraneux",
            "ancre": "end",
            "indice": "trajet médial, le plus court (s'arrête au niveau du genou)",
        },
        {
            "n": 5,
            "x": 223,
            "y": 320,
            "t": "Tête de la fibula",
            "ancre": "middle",
            "indice": "terminaison latérale, du biceps fémoral",
        },
        {
            "n": 6,
            "x": 143,
            "y": 345,
            "t": "Patte d'oie",
            "ancre": "middle",
            "indice": "terminaison médiale, du semi-tendineux",
        },
        {
            "n": 7,
            "x": 112,
            "y": 280,
            "t": "Plateau tibial",
            "ancre": "end",
            "indice": "terminaison médiale, du semi-membraneux, au niveau du genou",
        },
    ],
}
