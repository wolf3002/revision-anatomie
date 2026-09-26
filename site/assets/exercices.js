/**
 * Logique des trois exercices : carte, question, pastille muette.
 *
 * Fonctions pures : elles prennent un etat et en renvoient un nouveau, sans
 * toucher au DOM et sans muter leurs arguments. Le rendu vit dans interface.js.
 */

const VERDICTS = new Set(['rate', 'difficile', 'su']);

export function appliquerAutoEvaluation(item, verdict, aujourdHui) {
  if (!VERDICTS.has(verdict)) return item;
  return {
    ...item,
    statut: verdict,
    derniereVue: aujourdHui,
    echecs: verdict === 'rate' ? item.echecs + 1 : 0,
  };
}

export function corrigerQuestion(question, indexChoisi) {
  return {
    juste: indexChoisi === question.bonne,
    bonne: question.bonne,
    expl: question.expl,
  };
}

export function normaliser(saisie) {
  return (saisie || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[-'']/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function verifierPastille(pastille, saisie) {
  const attendu = normaliser(pastille.t);
  const propose = normaliser(saisie);
  return propose.length > 0 && propose === attendu;
}

export function itemsDuCours(cours) {
  const items = [];
  for (const chapitre of cours.chapitres) {
    const neuf = (id, type) => ({
      id, type, chapitre: chapitre.num, statut: 'jamais', derniereVue: null, echecs: 0,
    });
    for (const carte of chapitre.cartes || []) items.push(neuf(carte.id, 'carte'));
    for (const question of chapitre.quiz || []) items.push(neuf(question.id, 'quiz'));
    for (const planche of chapitre.planches || []) {
      for (const pastille of planche.pastilles || []) {
        items.push(neuf(`${planche.id}#${pastille.n}`, 'pastille'));
      }
    }
  }
  return items;
}
