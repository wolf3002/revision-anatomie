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

PLANCHES = {
    "plans-anatomiques": {
        "id": "plans-anatomiques",
        "titre": "Les trois plans anatomiques",
        "vb": "0 0 320 340",
        "dessin": (
            "<g class='plan plan--frontal'>"
            "<path d='M64 26 L256 26 L256 314 L64 314 Z' fill='none' "
            "stroke='currentColor' stroke-dasharray='5 4' stroke-width='1.5'/></g>"
            "<g class='plan plan--sagittal'>"
            "<path d='M160 20 L160 320' stroke='currentColor' "
            "stroke-dasharray='5 4' stroke-width='1.5'/></g>"
            "<g class='plan plan--transversal'>"
            "<path d='M52 176 L268 176' stroke='currentColor' "
            "stroke-dasharray='5 4' stroke-width='1.5'/></g>" + _SILHOUETTE_FACE
        ),
        "pastilles": [
            {
                "n": 1,
                "x": 258,
                "y": 170,
                "t": "Plan frontal",
                "ancre": "end",
                "plan": "frontal",
            },
            {
                "n": 2,
                "x": 166,
                "y": 24,
                "t": "Plan sagittal",
                "ancre": "start",
                "plan": "sagittal",
            },
            {
                "n": 3,
                "x": 56,
                "y": 170,
                "t": "Plan transversal",
                "ancre": "start",
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
            # Crânial / Caudal : axe vertical à gauche du corps, chaque flèche pointe
            # vers le pôle qu'elle nomme (vers le haut = vers le crâne, vers le bas =
            # vers les pieds), et non vers le centre du corps.
            "<path d='M40 90 L40 34' marker-end='url(#fleche)'/>"
            "<path d='M40 250 L40 304' marker-end='url(#fleche)'/>"
            # Proximal / Distal : le long de la jambe droite (décalé pour rester lisible),
            # la flèche proximale pointe vers le tronc (la hanche), la flèche distale
            # pointe vers l'extrémité du membre (le pied) — donc loin du tronc.
            "<path d='M193 244 L180 205' marker-end='url(#fleche)'/>"
            "<path d='M194 249 L206 282' marker-end='url(#fleche)'/>"
            # Médial / Latéral : au niveau du tronc, la flèche médiale pointe vers le
            # plan médian (l'axe vertical central), la flèche latérale s'en éloigne.
            "<path d='M120 168 L152 168' marker-end='url(#fleche)'/>"
            "<path d='M170 168 L202 168' marker-end='url(#fleche)'/>"
            "</g>"
        ),
        "pastilles": [
            {"n": 1, "x": 46, "y": 30, "t": "Crânial", "ancre": "start"},
            {"n": 2, "x": 46, "y": 306, "t": "Caudal", "ancre": "start"},
            {"n": 3, "x": 184, "y": 201, "t": "Proximal", "ancre": "start"},
            {"n": 4, "x": 210, "y": 280, "t": "Distal", "ancre": "start"},
            {"n": 5, "x": 148, "y": 160, "t": "Médial", "ancre": "end"},
            {"n": 6, "x": 206, "y": 168, "t": "Latéral", "ancre": "start"},
        ],
    },
}
