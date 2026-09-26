"""Controle de mise en page mobile.

La cible principale du site est un telephone, mais il doit tenir sur toutes les
largeurs. Ce module rend une page HTML locale a huit largeurs de reference et
signale tout defaut de mise en page : debordement horizontal de la page,
element qui depasse le cadre de son parent, texte tronque, cible tactile trop
petite sous 768 px.

Pilotage de Chrome -- choix retenu et pourquoi :
Playwright (paquet Python deja installe sur la machine), qui pilote le binaire
'google-chrome' installe via channel='chrome'. Verifie empiriquement avant de
choisir : 'google-chrome --headless=new --dump-dom --window-size=320,900' ne
donne PAS un viewport de 320 px -- window.innerWidth mesurait 500 sur cette
machine avec cette commande, --window-size pilotant la fenetre externe et pas
la zone de rendu de facon fiable en tete. Le contrat de ce module ('a huit
largeurs precises') exige un viewport exact ; page.evaluate() de Playwright le
garantit (verifie : innerWidth mesure = largeur demandee, exactement) et
renvoie des valeurs Python deja typees, sans devoir embarquer du JSON dans le
titre du document puis le reparser depuis un --dump-dom.

Le navigateur est lance une seule fois par processus (module-level, ferme a la
sortie via atexit) : lancer Chrome a chaque appel de verifier_page() est ce qui
rendrait la suite de tests lente.

Dependance : Playwright n'est pas dans la bibliotheque standard. Installation :

    pip install -r requirements-dev.txt
    python3 -m playwright install chrome   # au cas ou channel="chrome" ne
                                            # trouve pas de google-chrome systeme

Sur cette machine, google-chrome est deja installe et Playwright le pilote
directement (channel="chrome") : la seconde commande n'est pas necessaire ici,
mais le reste sans elle sur une machine qui n'a pas Chrome. Si le paquet
'playwright' est absent, verifier_page() leve un RuntimeError explicite -- pas
une trace d'import.
"""

from __future__ import annotations

import atexit
import sys
from pathlib import Path
from typing import Sequence

try:
    from playwright.sync_api import sync_playwright
except ImportError as _erreur_import_playwright:
    sync_playwright = None
else:
    _erreur_import_playwright = None

LARGEURS = (320, 360, 390, 414, 768, 1024, 1280, 1920)

_HAUTEUR_VIEWPORT = 900
_LARGEUR_CIBLE_TACTILE_MAX = 768
_CIBLE_TACTILE_MIN_PX = 44

# Script execute DANS la page (Playwright), appele avec un seul argument
# {cibleMin, largeurMax} -- CES DEUX SEUILS N'ONT PAS D'AUTRE DEFINITION : ils
# viennent des parametres de verifier_page(), jamais recodes en dur ici, pour
# qu'une seule source existe (piege releve en revue : les anciennes constantes
# _CIBLE_TACTILE_MIN_PX / _LARGEUR_CIBLE_TACTILE_MAX etaient mortes, le seuil
# reel etait ecrit en dur plus bas dans cette chaine). Renvoie une liste de
# dicts {type, selecteur, detail} -- le prefixe "[Nxxpx] fichier" est ajoute
# cote Python, qui ignore tout ce qui se passe dans la page.
_SCRIPT_ANALYSE = r"""
(config) => {
  const TOLERANCE = 1;          // arrondi sous-pixel
  const SEUIL_TRONCATURE = 4;   // "nettement" : au-dela du bruit d'arrondi
  const CIBLE_MIN = config.cibleMin;
  const LARGEUR_MAX_CIBLE = config.largeurMax;

  function identifiant(el) {
    if (el.id) return '#' + el.id;
    let sel = el.tagName.toLowerCase();
    if (typeof el.className === 'string' && el.className.trim()) {
      sel += '.' + el.className.trim().split(/\s+/)[0];
    }
    const texte = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    if (texte) sel += ` "${texte}"`;
    return sel;
  }

  function aAncetreDefilant(el) {
    let n = el.parentElement;
    while (n) {
      const cs = getComputedStyle(n);
      if (cs.overflowX === 'auto' || cs.overflowX === 'scroll') return true;
      n = n.parentElement;
    }
    return false;
  }

  const NS_SVG = 'http://www.w3.org/2000/svg';
  const defauts = [];

  // 1. Debordement horizontal de la page -- le defaut principal : il oblige
  // a faire defiler la page entiere lateralement.
  const scrollWidth = document.documentElement.scrollWidth;
  const innerWidth = window.innerWidth;
  if (scrollWidth > innerWidth + TOLERANCE) {
    defauts.push({
      type: 'debordement_page',
      selecteur: 'html',
      detail: `page.scrollWidth=${scrollWidth}px > fenetre=${innerWidth}px`,
    });
  }

  const tous = document.querySelectorAll('body *');
  for (const el of tous) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    // Les descendants d'un <svg> vivent dans le systeme de coordonnees du
    // viewBox, pas dans le flux CSS : "depasser le cadre de son parent" ou
    // "texte tronque" n'y ont pas de sens. Le <svg> racine lui-meme reste
    // controle : un <svg> intrinsequement large qui deborde de son
    // conteneur est un vrai defaut mobile.
    const dansSvg = el.namespaceURI === NS_SVG && el.tagName.toLowerCase() !== 'svg';
    if (dansSvg) continue;

    // 2. Element qui depasse le cadre de son parent. Un element ancre au
    // viewport (position fixed/sticky) n'a pas son parent DOM comme cadre
    // visuel de reference : on l'exclut plutot que de produire un faux
    // positif (ex. barre d'actions ancree en bas d'ecran).
    const ancreAuViewport = cs.position === 'fixed' || cs.position === 'sticky';
    if (!ancreAuViewport && el.parentElement && !aAncetreDefilant(el)) {
      const parent = el.parentElement;
      const rp = parent.getBoundingClientRect();
      if (rect.right > rp.right + TOLERANCE) {
        defauts.push({
          type: 'element_hors_cadre',
          selecteur: identifiant(el),
          detail: `depasse le cadre de son parent (${identifiant(parent)}) `
            + `de ${(rect.right - rp.right).toFixed(0)}px a droite`,
        });
      } else if (rect.left < rp.left - TOLERANCE) {
        defauts.push({
          type: 'element_hors_cadre',
          selecteur: identifiant(el),
          detail: `depasse le cadre de son parent (${identifiant(parent)}) `
            + `de ${(rp.left - rect.left).toFixed(0)}px a gauche`,
        });
      }
    }

    // 3. Texte tronque : ecart net entre le contenu et la boite visible,
    // sur un element qui porte lui-meme du texte (pas un simple conteneur
    // dont un enfant depasse -- deja signale par le cas 2 ci-dessus).
    const aDuTexteDirect = Array.from(el.childNodes).some(
      (n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0
    );
    if (aDuTexteDirect && !aAncetreDefilant(el)) {
      const ecart = el.scrollWidth - el.clientWidth;
      if (ecart > SEUIL_TRONCATURE) {
        defauts.push({
          type: 'texte_tronque',
          selecteur: identifiant(el),
          detail: `scrollWidth=${el.scrollWidth}px > clientWidth=${el.clientWidth}px `
            + `(ecart ${ecart}px)`,
        });
      }
    }
  }

  // 4. Cible tactile trop petite -- exigence d'ergonomie du projet, sous
  // LARGEUR_MAX_CIBLE de large seulement.
  if (window.innerWidth < LARGEUR_MAX_CIBLE) {
    const cibles = document.querySelectorAll('button, a[href]');
    for (const el of cibles) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      if (rect.height < CIBLE_MIN - 0.5) {
        defauts.push({
          type: 'cible_tactile_trop_petite',
          selecteur: identifiant(el),
          detail: `hauteur=${rect.height.toFixed(1)}px < ${CIBLE_MIN}px`,
        });
      }
    }
  }

  return defauts;
}
"""

_playwright = None
_navigateur = None


def _obtenir_navigateur():
    global _playwright, _navigateur
    if _navigateur is None:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright n'est pas installe. Installer avec :\n"
                "  pip install -r requirements-dev.txt\n"
                "  python3 -m playwright install chrome\n"
                f"(erreur d'import d'origine : {_erreur_import_playwright})"
            ) from _erreur_import_playwright
        _playwright = sync_playwright().start()
        _navigateur = _playwright.chromium.launch(channel="chrome", headless=True)
        atexit.register(_fermer_navigateur)
    return _navigateur


def _fermer_navigateur():
    global _playwright, _navigateur
    if _navigateur is not None:
        _navigateur.close()
        _navigateur = None
    if _playwright is not None:
        _playwright.stop()
        _playwright = None


def _bloquer_reseau(page):
    # Les pages du site chargent les polices Google Fonts par une requete
    # reseau (voir demo.html) ; ce controle porte sur la mise en page, pas sur
    # les polices, et doit rester utilisable hors ligne / en CI. On coupe donc
    # tout ce qui n'est pas un fichier local : la page finit de charger tout
    # de suite (les requetes bloquees se terminent en echec sans attente).
    page.route("https://**", lambda route: route.abort())
    page.route("http://**", lambda route: route.abort())


def verifier_page(
    chemin_html: Path,
    largeurs: Sequence[int] = LARGEURS,
    *,
    cible_tactile_min_px: int = _CIBLE_TACTILE_MIN_PX,
    largeur_cible_tactile_max: int = _LARGEUR_CIBLE_TACTILE_MAX,
) -> list[str]:
    """Renvoie la liste des defauts constates. Liste vide = la page est saine.

    cible_tactile_min_px et largeur_cible_tactile_max pilotent le controle
    n°4 (cible tactile) : hauteur minimale exigee, et largeur de viewport
    au-dela de laquelle le controle ne s'applique plus (le desktop n'a pas de
    contrainte de pouce).
    """
    chemin_html = Path(chemin_html)
    if not chemin_html.exists():
        return [f"{chemin_html} : fichier introuvable"]

    chemin_html = chemin_html.resolve()
    url = chemin_html.as_uri()
    navigateur = _obtenir_navigateur()
    config = {"cibleMin": cible_tactile_min_px, "largeurMax": largeur_cible_tactile_max}
    defauts: list[str] = []

    for largeur in largeurs:
        page = navigateur.new_page(
            viewport={"width": largeur, "height": _HAUTEUR_VIEWPORT}
        )
        try:
            _bloquer_reseau(page)
            page.goto(url, wait_until="load")
            bruts = page.evaluate(_SCRIPT_ANALYSE, config)
        finally:
            page.close()

        for d in bruts:
            defauts.append(
                f"[{largeur}px] {chemin_html.name} — {d['selecteur']} : {d['detail']}"
            )

    return defauts


if __name__ == "__main__":
    chemins = sys.argv[1:]
    if not chemins:
        print("Usage : python3 verifier_mobile.py <page.html> [...]", file=sys.stderr)
        raise SystemExit(2)

    tous_defauts: list[str] = []
    try:
        for chemin in chemins:
            tous_defauts += verifier_page(Path(chemin))
    except RuntimeError as erreur:
        print(erreur, file=sys.stderr)
        raise SystemExit(1) from erreur

    if tous_defauts:
        for defaut in tous_defauts:
            print(defaut)
        raise SystemExit(1)

    print("Aucun defaut constate.")
