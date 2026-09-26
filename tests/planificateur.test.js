import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  intervalleDeBase, echeance, estDu, composerSeance, ajouterJours,
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
