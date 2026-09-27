import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  appliquerAutoEvaluation, corrigerQuestion, normaliser, verifierPastille, itemsDuCours,
} from '../site/assets/exercices.js';

const base = { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'jamais', derniereVue: null, echecs: 0 };

test('un verdict "su" enregistre la date et remet les échecs à zéro', () => {
  const apres = appliquerAutoEvaluation({ ...base, echecs: 2 }, 'su', '2026-09-18');
  assert.equal(apres.statut, 'su');
  assert.equal(apres.derniereVue, '2026-09-18');
  assert.equal(apres.echecs, 0);
});

test('un verdict "raté" incrémente le compteur d\'échecs', () => {
  const apres = appliquerAutoEvaluation({ ...base, echecs: 1 }, 'rate', '2026-09-18');
  assert.equal(apres.statut, 'rate');
  assert.equal(apres.echecs, 2);
});

test('l\'auto-évaluation ne modifie pas l\'item d\'origine', () => {
  const avant = { ...base };
  appliquerAutoEvaluation(avant, 'su', '2026-09-18');
  assert.deepEqual(avant, base);
});

test('la correction indique la bonne réponse et son explication', () => {
  const question = { id: 'q1-01', choix: ['A', 'B', 'C'], bonne: 1, expl: 'Parce que B.' };
  assert.deepEqual(corrigerQuestion(question, 1), { juste: true, bonne: 1, expl: 'Parce que B.' });
  assert.deepEqual(corrigerQuestion(question, 0), { juste: false, bonne: 1, expl: 'Parce que B.' });
});

test('la normalisation ignore casse, accents, tirets et espaces', () => {
  assert.equal(normaliser('  Plan Frontal '), normaliser('plan frontal'));
  assert.equal(normaliser('Crânial'), normaliser('cranial'));
  assert.equal(normaliser('scapulo-humérale'), normaliser('scapulo humerale'));
});

test('une légende saisie est acceptée malgré les accents manquants', () => {
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, 'cranial'), true);
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, 'caudal'), false);
});

test('une saisie vide est refusée', () => {
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, '   '), false);
});

test('le cours est aplati en items planifiables', () => {
  const cours = {
    chapitres: [{
      num: 1,
      cartes: [{ id: 'c1-01' }],
      quiz: [{ id: 'q1-01' }],
      planches: [{ id: 'p1', pastilles: [{ n: 1, t: 'A' }, { n: 2, t: 'B' }] }],
      muscles: [],
    }],
  };
  const items = itemsDuCours(cours);
  assert.deepEqual(items.map((i) => i.id), ['c1-01', 'q1-01', 'p1#1', 'p1#2']);
  assert.deepEqual([...new Set(items.map((i) => i.type))], ['carte', 'quiz', 'pastille']);
  assert.ok(items.every((i) => i.chapitre === 1 && i.statut === 'jamais'));
});

test('une ligne de muscle devient un item planifiable identifié {chapitre}#muscle#{nom}', () => {
  const cours = {
    chapitres: [{
      num: 5,
      cartes: [],
      quiz: [],
      planches: [],
      muscles: [
        { nom: 'Grand rhomboïde', origine: ['O'], terminaison: ['T'], actions: ['A'], slide: 150 },
        { nom: "Long fléchisseur de l'hallux", origine: ['O'], terminaison: ['T'], actions: ['A'], slide: 151 },
      ],
    }],
  };
  const items = itemsDuCours(cours);
  assert.deepEqual(items.map((i) => i.id), [
    '5#muscle#Grand rhomboïde',
    "5#muscle#Long fléchisseur de l'hallux",
  ]);
  assert.ok(items.every((i) => i.type === 'muscle' && i.chapitre === 5 && i.statut === 'jamais'));
});
