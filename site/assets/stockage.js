/**
 * Persistance de la progression.
 *
 * Le support est injecte plutot qu'importe depuis window : le module se teste
 * sans navigateur, et un navigateur en navigation privee -- ou un quota plein --
 * degrade l'experience sans casser l'application.
 */

export const CLE = 'uc1-anatomie-v1';

const ETAT_VIERGE = { dateExamen: null, theme: 'auto', items: {} };

function estEtatValide(valeur) {
  return Boolean(valeur)
    && typeof valeur === 'object'
    && typeof valeur.items === 'object'
    && valeur.items !== null
    && !Array.isArray(valeur.items);
}

export function creerStockage(support) {
  function lire() {
    try {
      const brut = support.getItem(CLE);
      if (!brut) return { ...ETAT_VIERGE, items: {} };
      const valeur = JSON.parse(brut);
      return estEtatValide(valeur) ? { ...ETAT_VIERGE, ...valeur } : { ...ETAT_VIERGE, items: {} };
    } catch {
      return { ...ETAT_VIERGE, items: {} };
    }
  }

  function ecrire(etat) {
    try {
      support.setItem(CLE, JSON.stringify(etat));
    } catch {
      // Quota plein ou stockage interdit : la session reste utilisable,
      // seule la memorisation entre visites est perdue.
    }
  }

  function modifier(transformation) {
    const etat = lire();
    transformation(etat);
    ecrire(etat);
  }

  return {
    lire,
    ecrireItem(id, item) { modifier((etat) => { etat.items[id] = item; }); },
    definirDateExamen(iso) { modifier((etat) => { etat.dateExamen = iso; }); },
    definirTheme(nom) { modifier((etat) => { etat.theme = nom; }); },
    exporter() { return JSON.stringify(lire(), null, 2); },
    importer(json) {
      try {
        const valeur = JSON.parse(json);
        if (!estEtatValide(valeur)) return false;
        ecrire({ ...ETAT_VIERGE, ...valeur });
        return true;
      } catch {
        return false;
      }
    },
    reinitialiser() { try { support.removeItem(CLE); } catch { /* sans effet */ } },
  };
}
