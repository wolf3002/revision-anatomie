/**
 * Calcul des echeances de revision et composition de la seance du jour.
 *
 * Module pur : ni DOM, ni localStorage, ni horloge. La date du jour est
 * toujours passee en parametre, ce qui rend chaque fonction testable.
 *
 * L'intervalle suit Cepeda et al. (2008) : environ 15 % du delai restant
 * avant l'examen. Intervalles fixes et non croissants, l'ecart mesure entre
 * les deux n'etant pas significatif.
 */

const JOUR_MS = 86400000;
const INTERVALLE_PAR_DEFAUT = 3;
const INTERVALLE_MAX = 7;

export function ajouterJours(iso, n) {
  const date = new Date(`${iso}T00:00:00Z`);
  return new Date(date.getTime() + n * JOUR_MS).toISOString().slice(0, 10);
}

export function intervalleDeBase(joursAvantExamen) {
  if (!Number.isFinite(joursAvantExamen) || joursAvantExamen <= 0) {
    return INTERVALLE_PAR_DEFAUT;
  }
  return Math.min(INTERVALLE_MAX, Math.max(1, Math.round(0.15 * joursAvantExamen)));
}

export function echeance(item, intervalle) {
  if (!item.derniereVue || item.statut === 'jamais') return '0000-01-01';
  if (item.statut === 'rate') return item.derniereVue;
  const delai = item.statut === 'difficile'
    ? Math.max(1, Math.round(intervalle / 2))
    : intervalle;
  return ajouterJours(item.derniereVue, delai);
}

export function estDu(item, intervalle, aujourdHui) {
  return echeance(item, intervalle) <= aujourdHui;
}

export function composerSeance(items, { intervalle, aujourdHui, taille = 25 }) {
  const dus = items.filter((item) => estDu(item, intervalle, aujourdHui));
  const fragiles = dus.filter((item) => item.echecs >= 2);
  const reste = dus.filter((item) => item.echecs < 2);

  const parChapitre = new Map();
  for (const item of reste) {
    if (!parChapitre.has(item.chapitre)) parChapitre.set(item.chapitre, []);
    parChapitre.get(item.chapitre).push(item);
  }

  // Tourniquet entre chapitres : deux items consecutifs ne partagent pas
  // le meme chapitre tant qu'un autre chapitre a encore des items en attente.
  const entrelaces = [];
  const files = [...parChapitre.values()];
  while (files.some((file) => file.length)) {
    for (const file of files) {
      if (file.length) entrelaces.push(file.shift());
    }
  }

  return [...fragiles, ...entrelaces].slice(0, taille);
}
