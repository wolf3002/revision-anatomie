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
_CX = 120


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


# Correction ronde 2 : le rendu du site decale un libelle "middle" de (0, +24) --
# il est pose SOUS la pastille, pas centre dessus (formule DECALAGE_LIBELLE du front).
# Les deux pastilles empilees sous chaque panneau doivent donc laisser 24 px plus la
# hauteur du texte entre elles, et le viewBox doit laisser cette place sous la seconde.
# D'ou une hauteur de viewBox agrandie (320 -> 360) et des pastilles remontees.
_Y_NOM = 268
_Y_MOUVEMENTS = 308

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
        "vb": "0 0 240 360",
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
                "x": _CX,
                "y": _Y_MOUVEMENTS,
                "t": "Abduction, adduction",
                "ancre": "middle",
                "plan": "frontal",
                "indice": "mouvements de ce plan",
            },
        ],
    },
    "plan-sagittal": {
        "id": "plan-sagittal",
        "titre": "Le plan sagittal",
        "vb": "0 0 240 360",
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
                "x": _CX,
                "y": _Y_MOUVEMENTS,
                "t": "Flexion, extension",
                "ancre": "middle",
                "plan": "sagittal",
                "indice": "mouvements de ce plan",
            },
        ],
    },
    "plan-transversal": {
        "id": "plan-transversal",
        "titre": "Le plan transversal",
        "vb": "0 0 240 360",
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
                "x": _CX,
                "y": _Y_MOUVEMENTS,
                "t": "Rotation, pronation, supination",
                "ancre": "middle",
                "plan": "transversal",
                "indice": "mouvements de ce plan",
            },
        ],
    },
    "os-long-coupe": {
        "id": "os-long-coupe",
        "titre": "L'os long en coupe",
        "vb": "0 0 420 460",
        "dessin": _DEFS_FLECHE + _DESSIN_OS_LONG,
        "pastilles": _PASTILLES_OS_LONG,
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
            # Crânial / Caudal : axe vertical proche du corps (correction ronde 1 : l'axe
            # flottait trop loin à gauche, sans rapport visuel avec le tronc). Chaque
            # flèche pointe vers le pôle qu'elle nomme, pas vers le centre du corps.
            "<path d='M112 90 L112 34' marker-end='url(#fleche)'/>"
            "<path d='M112 250 L112 304' marker-end='url(#fleche)'/>"
            # Proximal / Distal : le long de la jambe droite (décalé pour rester lisible),
            # la flèche proximale pointe vers le tronc (la hanche), la flèche distale
            # pointe vers l'extrémité du membre (le pied) — donc loin du tronc.
            "<path d='M193 244 L180 205' marker-end='url(#fleche)'/>"
            "<path d='M194 249 L206 282' marker-end='url(#fleche)'/>"
            # Médial / Latéral : décalées verticalement (correction ronde 1 : à la même
            # hauteur, les deux flèches se lisaient comme une seule flèche continue), et
            # toutes deux logées entre les bras et les hanches pour ne toucher ni les bras
            # ni la jambe droite. La flèche médiale pointe vers le plan médian, la
            # latérale s'en éloigne.
            "<path d='M120 158 L152 158' marker-end='url(#fleche)'/>"
            "<path d='M170 183 L202 183' marker-end='url(#fleche)'/>"
            "</g>"
        ),
        "pastilles": [
            {"n": 1, "x": 108, "y": 24, "t": "Crânial", "ancre": "end"},
            {"n": 2, "x": 108, "y": 316, "t": "Caudal", "ancre": "end"},
            {"n": 3, "x": 196, "y": 215, "t": "Proximal", "ancre": "start"},
            {"n": 4, "x": 214, "y": 270, "t": "Distal", "ancre": "start"},
            {"n": 5, "x": 150, "y": 178, "t": "Médial", "ancre": "end"},
            {"n": 6, "x": 204, "y": 167, "t": "Latéral", "ancre": "start"},
        ],
    },
}
