import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  intervalleDeBase, echeance, estDu, composerSeance, ajouterJours, reinjecterRate,
} from '../site/assets/planificateur.js';

const item = (id, chapitre, statut = 'jamais', derniereVue = null, type = 'carte') =>
  ({ id, chapitre, type, statut, derniereVue, echecs: 0 });

test('l\'intervalle vaut environ 15 % du délai avant l\'examen', () => {
  assert.equal(intervalleDeBase(28), 4);
  assert.equal(intervalleDeBase(14), 2);
});

test('l\'intervalle ne descend jamais sous un jour ni au-dessus de sept', () => {
  assert.equal(intervalleDeBase(2), 1);
  assert.equal(intervalleDeBase(365), 7);
});

test('sans date d\'examen exploitable, l\'intervalle retombe à trois jours', () => {
  assert.equal(intervalleDeBase(0), 3);
  assert.equal(intervalleDeBase(-5), 3);
  assert.equal(intervalleDeBase(NaN), 3);
});

test('un item jamais vu est dû immédiatement', () => {
  assert.equal(estDu(item('a', 1), 4, '2026-09-18'), true);
});

test('un item raté repasse le jour même', () => {
  const rate = item('a', 1, 'rate', '2026-09-18');
  assert.equal(echeance(rate, 4), '2026-09-18');
});

test('un item difficile revient deux fois plus vite qu\'un item su', () => {
  const difficile = item('a', 1, 'difficile', '2026-09-18');
  const su = item('b', 1, 'su', '2026-09-18');
  assert.equal(echeance(difficile, 4), '2026-09-20');
  assert.equal(echeance(su, 4), '2026-09-22');
});

test('un item su n\'est pas dû avant son échéance', () => {
  const su = item('a', 1, 'su', '2026-09-18');
  assert.equal(estDu(su, 4, '2026-09-21'), false);
  assert.equal(estDu(su, 4, '2026-09-22'), true);
});

test('ajouterJours franchit correctement les fins de mois', () => {
  assert.equal(ajouterJours('2026-09-29', 4), '2026-10-03');
  assert.equal(ajouterJours('2026-12-30', 3), '2027-01-02');
});

test('la séance alterne les chapitres plutôt que de les enchaîner', () => {
  const items = [
    item('a1', 1), item('a2', 1), item('a3', 1),
    item('b1', 2), item('b2', 2), item('b3', 2),
  ];
  const seance = composerSeance(items, { intervalle: 4, aujourdHui: '2026-09-18', taille: 6 });
  for (let i = 1; i < seance.length; i += 1) {
    assert.notEqual(seance[i].chapitre, seance[i - 1].chapitre);
  }
});

test('la séance respecte la taille demandée', () => {
  const items = Array.from({ length: 40 }, (_, i) => item(`x${i}`, (i % 3) + 1));
  assert.equal(composerSeance(items, { intervalle: 4, aujourdHui: '2026-09-18', taille: 25 }).length, 25);
});

test('les items fragiles passent en tête de séance', () => {
  const fragile = { ...item('f', 1, 'rate', '2026-09-18'), echecs: 2 };
  const seance = composerSeance([item('a', 2), fragile, item('b', 3)],
    { intervalle: 4, aujourdHui: '2026-09-18', taille: 3 });
  assert.equal(seance[0].id, 'f');
});

test('la séance ne retient que les items dus', () => {
  const su = item('frais', 2, 'su', '2026-09-18');
  const seance = composerSeance([item('a', 1), su],
    { intervalle: 4, aujourdHui: '2026-09-19', taille: 10 });
  assert.deepEqual(seance.map((i) => i.id), ['a']);
});

test('la séance entrelace aussi les formats à l\'intérieur d\'un même chapitre', () => {
  // Un seul chapitre, mais trois formats : sans entrelacement par format, le
  // tourniquet degenere en une seule file (bloc de cartes, puis bloc de quiz,
  // puis bloc de pastilles) faute d'un second chapitre pour alterner avec.
  const items = [
    item('c1', 1, 'jamais', null, 'carte'),
    item('c2', 1, 'jamais', null, 'carte'),
    item('q1', 1, 'jamais', null, 'quiz'),
    item('q2', 1, 'jamais', null, 'quiz'),
    item('p1', 1, 'jamais', null, 'pastille'),
    item('p2', 1, 'jamais', null, 'pastille'),
  ];
  const seance = composerSeance(items, { intervalle: 4, aujourdHui: '2026-09-18', taille: 6 });
  const types = seance.map((i) => i.type);
  assert.deepEqual(types, ['carte', 'quiz', 'pastille', 'carte', 'quiz', 'pastille']);
});

// Spec §4.3 : un item note "rate" "repasse en fin de la séance en cours" --
// pas seulement le lendemain une fois sa nouvelle echeance (le jour meme)
// calculee. composerSeance ne construit sa file qu'une fois au demarrage ;
// c'est reinjecterRate qui porte ce comportement, appele par interface.js a
// chaque verdict enregistre pendant une seance (voir enregistrerVerdict /
// surVerdictPendantSeance dans site/assets/interface.js).
test('un item rate pendant la seance repasse en fin de la file en cours', () => {
  const enCours = [item('b', 2), item('c', 3)];
  const rate = { ...item('a', 1, 'rate', '2026-09-18'), echecs: 1 };
  const file = reinjecterRate(enCours, rate);
  assert.deepEqual(file.map((i) => i.id), ['b', 'c', 'a']);
  assert.equal(file[2], rate, 'l\'item reinjecte est bien celui fourni (meme reference, verdict a jour)');
});

test('un item su ou difficile ne repasse pas dans la seance en cours', () => {
  const enCours = [item('b', 2)];
  const su = item('a', 1, 'su', '2026-09-18');
  const difficile = item('c', 1, 'difficile', '2026-09-18');
  assert.equal(reinjecterRate(enCours, su), enCours);
  assert.equal(reinjecterRate(enCours, difficile), enCours);
});

test('reinjecterRate ne mute jamais la file recue', () => {
  const enCours = [item('b', 2)];
  const original = [...enCours];
  reinjecterRate(enCours, { ...item('a', 1, 'rate', '2026-09-18') });
  assert.deepEqual(enCours, original);
});

test('sans item a reinjecter, la file en cours ne change pas', () => {
  const enCours = [item('b', 2)];
  assert.equal(reinjecterRate(enCours, null), enCours);
  assert.equal(reinjecterRate(enCours, undefined), enCours);
});

// S'exercer (page de chapitre) ne réécrit aucun planificateur : il passe à
// composerSeance les seuls items du chapitre. Ces deux tests fixent ce que ce
// filtrage garantit, sur la même fonction que la séance du jour.
test('composerSeance filtrée sur un chapitre ne renvoie que ce chapitre', () => {
  const tous = [
    item('c1-01', 1), item('c1-02', 1), item('q1-01', 1, 'jamais', null, 'quiz'),
    item('c2-01', 2), item('c2-02', 2), item('q2-01', 2, 'jamais', null, 'quiz'),
  ];
  const duChapitre = tous.filter((i) => i.chapitre === 2);
  const seance = composerSeance(duChapitre, { intervalle: 3, aujourdHui: '2026-09-18' });
  assert.equal(seance.length, 3);
  assert.ok(seance.every((i) => i.chapitre === 2));
});

test('sur un seul chapitre, la séance entrelace quand même les formats', () => {
  const items = [
    ...['a', 'b', 'c'].map((id) => item(`c-${id}`, 5, 'jamais', null, 'carte')),
    ...['a', 'b', 'c'].map((id) => item(`q-${id}`, 5, 'jamais', null, 'quiz')),
    ...['a', 'b', 'c'].map((id) => item(`m-${id}`, 5, 'jamais', null, 'muscle')),
  ];
  const types = composerSeance(items, { intervalle: 3, aujourdHui: '2026-09-18' })
    .map((i) => i.type);
  for (let k = 1; k < types.length; k += 1) {
    assert.notEqual(types[k], types[k - 1], `deux ${types[k]} d'affilée : ${types}`);
  }
});
