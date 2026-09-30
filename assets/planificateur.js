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

  // Regroupe par (chapitre, format) et non par le seul chapitre : un chapitre
  // entier de cartes avant le premier quiz produirait le meme bloc monotone
  // qu'un chapitre entier avant le suivant (§3.6 -- reviser un bloc d'affilee
  // gonfle la maitrise ressentie et l'effondre a l'examen). Avec un seul
  // chapitre charge, regrouper par chapitre seul degenererait meme en file
  // plate, sans aucun entrelacement : verifie par un test discriminant.
  const parGroupe = new Map();
  for (const item of reste) {
    const cle = `${item.chapitre}:${item.type}`;
    if (!parGroupe.has(cle)) parGroupe.set(cle, []);
    parGroupe.get(cle).push(item);
  }

  // Tourniquet entre chapitres ET formats : deux items consecutifs ne
  // partagent ni le meme chapitre ni le meme format tant qu'un autre groupe a
  // encore des items en attente.
  const entrelaces = [];
  const files = [...parGroupe.values()];
  while (files.some((file) => file.length)) {
    for (const file of files) {
      if (file.length) entrelaces.push(file.shift());
    }
  }

  return [...fragiles, ...entrelaces].slice(0, taille);
}

/**
 * Reinjecte un item note "rate" en fin de la file de seance EN COURS.
 *
 * La spec (§4.3) annonce qu'un item rate "repasse en fin de la séance en
 * cours" -- pas seulement le lendemain, une fois la nouvelle echeance (le
 * jour meme) recalculee par `echeance`. Sans cet appel, composerSeance ne
 * construit sa file qu'une fois au demarrage : un item rate n'y revient
 * jamais avant la prochaine ouverture de la seance. Fonction pure comme le
 * reste du module : ne mute jamais `file`, renvoie la meme reference si rien
 * ne doit changer (item absent, ou verdict autre que "rate").
 */
export function reinjecterRate(file, itemMisAJour) {
  if (!itemMisAJour || itemMisAJour.statut !== 'rate') return file;
  return [...file, itemMisAJour];
}
