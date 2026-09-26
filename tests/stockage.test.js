import { test } from 'node:test';
import assert from 'node:assert/strict';
import { creerStockage, CLE } from '../site/assets/stockage.js';

function supportFactice() {
  const donnees = new Map();
  return {
    getItem: (cle) => (donnees.has(cle) ? donnees.get(cle) : null),
    setItem: (cle, valeur) => donnees.set(cle, String(valeur)),
    removeItem: (cle) => donnees.delete(cle),
  };
}

test('un stockage vierge renvoie un état par défaut exploitable', () => {
  const etat = creerStockage(supportFactice()).lire();
  assert.equal(etat.dateExamen, null);
  assert.equal(etat.theme, 'auto');
  assert.deepEqual(etat.items, {});
});

test('un item écrit est relu à l\'identique', () => {
  const stockage = creerStockage(supportFactice());
  const item = { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'su', derniereVue: '2026-09-18', echecs: 0 };
  stockage.ecrireItem('c1-01', item);
  assert.deepEqual(stockage.lire().items['c1-01'], item);
});

test('un contenu corrompu ne fait pas tomber l\'application', () => {
  const support = supportFactice();
  support.setItem(CLE, '{ ceci n est pas du json');
  assert.deepEqual(creerStockage(support).lire().items, {});
});

test('la date d\'examen et le thème sont conservés', () => {
  const stockage = creerStockage(supportFactice());
  stockage.definirDateExamen('2026-10-19');
  stockage.definirTheme('sombre');
  const etat = stockage.lire();
  assert.equal(etat.dateExamen, '2026-10-19');
  assert.equal(etat.theme, 'sombre');
});

test('un export se réimporte sans perte', () => {
  const source = creerStockage(supportFactice());
  source.definirDateExamen('2026-10-19');
  source.ecrireItem('c1-01', { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'difficile', derniereVue: '2026-09-18', echecs: 1 });

  const cible = creerStockage(supportFactice());
  assert.equal(cible.importer(source.exporter()), true);
  assert.deepEqual(cible.lire(), source.lire());
});

test('un import invalide est refusé sans écraser l\'existant', () => {
  const stockage = creerStockage(supportFactice());
  stockage.definirDateExamen('2026-10-19');
  assert.equal(stockage.importer('n importe quoi'), false);
  assert.equal(stockage.lire().dateExamen, '2026-10-19');
});

test('la réinitialisation vide la progression', () => {
  const stockage = creerStockage(supportFactice());
  stockage.ecrireItem('c1-01', { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'su', derniereVue: '2026-09-18', echecs: 0 });
  stockage.reinitialiser();
  assert.deepEqual(stockage.lire().items, {});
});

test('un support indisponible ne fait pas échouer l\'écriture', () => {
  const support = { getItem: () => null, setItem: () => { throw new Error('quota'); }, removeItem: () => {} };
  const stockage = creerStockage(support);
  assert.doesNotThrow(() => stockage.definirTheme('sombre'));
});
