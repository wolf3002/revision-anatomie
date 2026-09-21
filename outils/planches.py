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

# plans-anatomiques (ronde de correction 1) : une seule vue de face avec trois traits
# tiretés superposés se lisait comme "trois lignes identiques" et faisait chevaucher les
# libellés. Refait en trois panneaux côte à côte, un par plan, chacun avec l'orientation
# où ce plan se voit vraiment de face :
#   - frontal   : silhouette de face, le plan en surface verticale traversant le corps,
#                 flèche d'abduction du bras (mouvement caractéristique du plan frontal).
#   - sagittal  : silhouette DE PROFIL (le plan est alors dans le plan de la page),
#                 flèche de flexion du genou.
#   - transversal : silhouette de face, le plan en ellipse horizontale (la perspective
#                 suggère mieux l'horizontale qu'un simple segment), flèche de rotation.
_PANEL_CX = {"frontal": 120, "sagittal": 360, "transversal": 600}


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


PLANCHES = {
    "plans-anatomiques": {
        "id": "plans-anatomiques",
        "titre": "Les trois plans anatomiques",
        "vb": "0 0 720 320",
        "dessin": (
            _DEFS_FLECHE
            + _panel_frontal(_PANEL_CX["frontal"])
            + _panel_sagittal(_PANEL_CX["sagittal"])
            + _panel_transversal(_PANEL_CX["transversal"])
        ),
        "pastilles": [
            {
                "n": 1,
                "x": _PANEL_CX["frontal"],
                "y": 272,
                "t": "Plan frontal",
                "ancre": "middle",
                "plan": "frontal",
            },
            {
                "n": 2,
                "x": _PANEL_CX["frontal"],
                "y": 294,
                "t": "Abduction, adduction",
                "ancre": "middle",
                "plan": "frontal",
            },
            {
                "n": 3,
                "x": _PANEL_CX["sagittal"],
                "y": 272,
                "t": "Plan sagittal",
                "ancre": "middle",
                "plan": "sagittal",
            },
            {
                "n": 4,
                "x": _PANEL_CX["sagittal"],
                "y": 294,
                "t": "Flexion, extension",
                "ancre": "middle",
                "plan": "sagittal",
            },
            {
                "n": 5,
                "x": _PANEL_CX["transversal"],
                "y": 272,
                "t": "Plan transversal",
                "ancre": "middle",
                "plan": "transversal",
            },
            {
                "n": 6,
                "x": _PANEL_CX["transversal"],
                "y": 294,
                "t": "Rotation, pronation, supination",
                "ancre": "middle",
                "plan": "transversal",
            },
        ],
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
