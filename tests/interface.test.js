import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TYPES_RENDUS_EN_SEANCE } from '../site/assets/interface.js';
import { itemsDuCours } from '../site/assets/exercices.js';

// Defaut Critical (revue du plan chapitres-2-a-7, tache 1bis) : itemsDuCours
// exposait deja des items de muscle -- planifies, comptes par la
// progression -- mais aucune branche de la seance du jour ne savait les
// afficher : tires en seance, ils disparaissaient sans un mot, alors que le
// compteur affirmait le contraire. Ce test garantit MECANIQUEMENT que tout
// type produit par itemsDuCours a sa place dans TYPES_RENDUS_EN_SEANCE (donc
// une branche dans elementPourItem/itemEvalue/afficherEtapeCourante, dans
// interface.js) -- pas seulement pour les muscles : pour tout type futur.
// Un cours synthetique qui couvre les quatre formats connus a ce jour.
const coursTousFormats = {
  chapitres: [{
    num: 1,
    cartes: [{ id: 'c1-01' }],
    quiz: [{ id: 'q1-01' }],
    planches: [{ id: 'p1', pastilles: [{ n: 1, t: 'A' }] }],
    muscles: [
      { nom: 'Muscle test', origine: ['O'], terminaison: ['T'], actions: ['A'], slide: 1 },
    ],
  }],
};

test('la séance sait rendre tous les types que produit itemsDuCours', () => {
  const types = new Set(itemsDuCours(coursTousFormats).map((item) => item.type));
  assert.ok(types.size > 0, 'le cours synthetique doit produire au moins un type');
  for (const type of types) {
    assert.ok(
      TYPES_RENDUS_EN_SEANCE.includes(type),
      `type "${type}" produit par itemsDuCours mais absent de TYPES_RENDUS_EN_SEANCE `
        + '(interface.js) -- un item de ce type disparaitrait silencieusement d\'une séance qui le tire',
    );
  }
});

test('les quatre formats connus (carte, quiz, pastille, muscle) sont couverts', () => {
  // Verrou explicite : si un format disparaissait de TYPES_RENDUS_EN_SEANCE
  // sans que personne ne l'ait retire d'itemsDuCours, le test precedent ne
  // le verrait pas (il ne teste qu'un sens). Celui-ci fixe la liste connue.
  assert.deepEqual([...TYPES_RENDUS_EN_SEANCE].sort(), ['carte', 'muscle', 'pastille', 'quiz']);
});
