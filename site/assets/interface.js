/**
 * Interface : le seul module autorise a toucher au DOM.
 *
 * Il lit l'etat via `stockage`, calcule via `planificateur` et `exercices`,
 * et n'implemente aucune regle metier lui-meme -- ni echeance, ni verdict de
 * correction, ni tolerance orthographique. Son unique travail : cabler des
 * evenements sur un DOM deja complet (gabarits/chapitre.html + le rendu de
 * outils/construire.py), et ecrire chaque interaction dans le stockage.
 *
 * Contrat de degradation : les cartes, questions et sections vivent deja
 * dans le DOM sans JavaScript (aucun `hidden` pose par le generateur). Ce
 * module REVELE (retire `hidden`/`cachee`) et MASQUE (les pose) ; il n'injecte
 * du contenu neuf que pour des controles purement interactifs qui n'ont pas
 * de sens sans JavaScript (champs de saisie du mode muet, bouton de
 * verification) -- jamais pour du texte de cours, de carte ou de question.
 */

import { intervalleDeBase } from './planificateur.js';
import { creerStockage } from './stockage.js';
import { appliquerAutoEvaluation, corrigerQuestion, verifierPastille, itemsDuCours } from './exercices.js';

const JOUR_MS = 86400000;

function aujourdHuiISO() {
  return new Date().toISOString().slice(0, 10);
}

// Ecart en jours entre deux dates ISO -- simple arithmetique de calendrier,
// pas une regle pedagogique : la regle (15 % du delai, bornee) vit dans
// planificateur.intervalleDeBase, qui recoit ce nombre en parametre.
function joursEntre(depuisIso, jusquaIso) {
  const debut = new Date(`${depuisIso}T00:00:00Z`).getTime();
  const fin = new Date(`${jusquaIso}T00:00:00Z`).getTime();
  return Math.round((fin - debut) / JOUR_MS);
}

function estDansUnChamp(cible) {
  return Boolean(cible) && /^(INPUT|TEXTAREA|SELECT)$/.test(cible.tagName || '');
}

export function demarrer(document, support) {
  const stockage = creerStockage(support);

  // Donnees brutes du cours (bonne reponse de quiz, forme canonique d'un
  // item neuf). Chargees de facon asynchrone et non bloquante : le reste de
  // l'interface doit rester utilisable meme si cette requete echoue (reseau
  // absent, page ouverte en file://).
  let coursItemsParDefaut = new Map();
  let coursQuiz = new Map();
  chargerCours((cours) => {
    for (const item of itemsDuCours(cours)) coursItemsParDefaut.set(item.id, item);
    for (const chapitre of cours.chapitres) {
      for (const q of chapitre.quiz || []) coursQuiz.set(q.id, q);
    }
  });

  let carteActive = null;

  function itemParDefaut(id) {
    return coursItemsParDefaut.get(id) || { echecs: 0 };
  }

  function enregistrerVerdict(id, verdict) {
    const etat = stockage.lire();
    const itemExistant = etat.items[id] || itemParDefaut(id);
    const itemMisAJour = appliquerAutoEvaluation(itemExistant, verdict, aujourdHuiISO());
    stockage.ecrireItem(id, itemMisAJour);
    return itemMisAJour;
  }

  // --- Onglets ------------------------------------------------------------

  const boutonsOnglet = Array.from(document.querySelectorAll('.onglet'));
  const volets = Array.from(document.querySelectorAll('.volet'));
  const barreCarte = document.getElementById('actions-carte');

  function activerOnglet(cle, { focus = false } = {}) {
    for (const bouton of boutonsOnglet) {
      bouton.setAttribute('aria-selected', bouton.dataset.onglet === cle ? 'true' : 'false');
    }
    for (const volet of volets) {
      volet.hidden = volet.dataset.volet !== cle;
    }
    if (cle !== 'cartes') {
      carteActive = null;
      if (barreCarte) barreCarte.hidden = true;
    }
    if (focus) {
      boutonsOnglet.find((b) => b.dataset.onglet === cle)?.focus();
    }
  }

  function ongletVoisin(delta) {
    if (!boutonsOnglet.length) return;
    const index = boutonsOnglet.findIndex((b) => b.getAttribute('aria-selected') === 'true');
    const suivant = (index + delta + boutonsOnglet.length) % boutonsOnglet.length;
    activerOnglet(boutonsOnglet[suivant].dataset.onglet, { focus: true });
  }

  for (const bouton of boutonsOnglet) {
    bouton.addEventListener('click', () => activerOnglet(bouton.dataset.onglet));
  }
  if (boutonsOnglet.length) activerOnglet(boutonsOnglet[0].dataset.onglet);

  // --- Cartes --------------------------------------------------------------

  function carteParDefaut() {
    const voletCourant = document.querySelector('.volet[data-volet="cartes"]:not([hidden])');
    return voletCourant ? voletCourant.querySelector('.carte') : null;
  }

  function reveler(carte) {
    const verso = carte.querySelector('.carte__r');
    if (verso && verso.dataset.etat === 'cachee') delete verso.dataset.etat;
  }

  function basculerFace(carte) {
    const verso = carte.querySelector('.carte__r');
    if (!verso) return;
    if (verso.dataset.etat === 'cachee') delete verso.dataset.etat;
    else verso.dataset.etat = 'cachee';
  }

  function activerCarte(carte) {
    carteActive = carte;
    reveler(carte);
    if (barreCarte) barreCarte.hidden = false;
  }

  function basculerCarteCourante() {
    const carte = carteActive || carteParDefaut();
    if (!carte) return;
    carteActive = carte;
    basculerFace(carte);
    if (barreCarte) barreCarte.hidden = false;
  }

  function appliquerVerdictCourant(verdict) {
    const carte = carteActive;
    if (!carte || !carte.id) return;
    enregistrerVerdict(carte.id, verdict);
    carte.dataset.dernierVerdict = verdict;
    if (barreCarte) barreCarte.hidden = true;
  }

  const zoneCartes = document.querySelector('.volet[data-volet="cartes"]');
  if (zoneCartes) {
    for (const carte of zoneCartes.querySelectorAll('.carte')) {
      carte.tabIndex = 0;
      carte.addEventListener('click', () => activerCarte(carte));
      carte.addEventListener('focus', () => { carteActive = carte; });
    }
  }
  if (barreCarte) {
    barreCarte.querySelector('[data-action="retourner"]')
      ?.addEventListener('click', () => basculerCarteCourante());
    for (const bouton of barreCarte.querySelectorAll('[data-verdict]')) {
      bouton.addEventListener('click', () => appliquerVerdictCourant(bouton.dataset.verdict));
    }
  }

  // --- Quiz ------------------------------------------------------------------

  const zoneQuiz = document.querySelector('.volet[data-volet="quiz"]');
  if (zoneQuiz) {
    zoneQuiz.addEventListener('click', (evenement) => {
      const bouton = evenement.target.closest('.choix');
      if (!bouton) return;
      const question = bouton.closest('.question');
      if (!question || question.dataset.repondue === 'oui') return;
      const donnees = coursQuiz.get(question.id);
      if (!donnees) return; // cours.json pas encore charge : rien a corriger, on ne casse rien

      const correction = corrigerQuestion(donnees, Number(bouton.dataset.index));
      for (const choix of question.querySelectorAll('.choix')) {
        const index = Number(choix.dataset.index);
        if (index === correction.bonne) choix.dataset.verdict = 'bon';
        else if (choix === bouton) choix.dataset.verdict = 'mauvais';
      }
      const explication = question.querySelector('.question__expl');
      if (explication) delete explication.dataset.etat;
      question.dataset.repondue = 'oui';

      enregistrerVerdict(question.id, correction.juste ? 'su' : 'rate');
    });
  }

  // --- Planches (legende / muet) ---------------------------------------------

  const planches = Array.from(document.querySelectorAll('.planche'));

  function construireLegende(planche) {
    const pastilles = Array.from(planche.querySelectorAll('.pastille'));
    if (!pastilles.length) return;

    const liste = document.createElement('ul');
    liste.className = 'legendes';
    liste.hidden = true;

    for (const pastille of pastilles) {
      const n = pastille.dataset.n;
      const attendu = pastille.querySelector('.pastille__t')?.textContent.trim() || '';
      const indice = pastille.dataset.indice || '';

      const item = document.createElement('li');
      const champ = document.createElement('input');
      champ.type = 'text';
      champ.className = 'champ';
      champ.autocomplete = 'off';
      champ.dataset.pastilleN = n;
      champ.dataset.attendu = attendu;
      if (indice) champ.placeholder = indice;
      champ.setAttribute('aria-label', indice ? `Pastille ${n} — ${indice}` : `Pastille ${n}`);
      item.appendChild(champ);
      liste.appendChild(item);
    }

    const boutonVerifier = document.createElement('button');
    boutonVerifier.type = 'button';
    boutonVerifier.className = 'action';
    boutonVerifier.textContent = 'Vérifier';
    boutonVerifier.hidden = true;
    boutonVerifier.addEventListener('click', () => verifierPlanche(planche));

    planche.append(liste, boutonVerifier);
  }

  function verifierPlanche(planche) {
    const liste = planche.querySelector('.legendes');
    if (!liste) return;
    const aujourdhui = aujourdHuiISO();

    for (const champ of liste.querySelectorAll('input')) {
      const correct = verifierPastille({ t: champ.dataset.attendu }, champ.value);
      champ.dataset.verdict = correct ? 'bon' : 'mauvais';

      let etatSpan = champ.parentElement.querySelector('.legendes__etat');
      if (!etatSpan) {
        etatSpan = document.createElement('span');
        etatSpan.className = 'legendes__etat mono';
        champ.parentElement.appendChild(etatSpan);
      }
      etatSpan.textContent = correct ? 'juste' : 'faux';

      enregistrerVerdict(`${planche.id}#${champ.dataset.pastilleN}`, correct ? 'su' : 'rate');
    }
  }

  function etatModePlanches() {
    return planches[0]?.dataset.mode === 'muet' ? 'muet' : 'legende';
  }

  function actualiserBoutonMode() {
    const bouton = document.querySelector('[data-action="mode-planches"]');
    if (!bouton) return;
    const mode = etatModePlanches();
    bouton.setAttribute('aria-pressed', mode === 'muet' ? 'true' : 'false');
    const etat = bouton.querySelector('.mode-planches__etat');
    if (etat) etat.textContent = mode === 'muet' ? 'mode muet' : 'mode légendé';
  }

  function basculerModePlanches() {
    const nouveauMode = etatModePlanches() === 'muet' ? 'legende' : 'muet';
    for (const planche of planches) {
      planche.dataset.mode = nouveauMode;
      const liste = planche.querySelector('.legendes');
      const bouton = planche.querySelector(':scope > button.action');
      if (liste) liste.hidden = nouveauMode !== 'muet';
      if (bouton) bouton.hidden = nouveauMode !== 'muet';
    }
    actualiserBoutonMode();
  }

  if (planches.length) {
    for (const planche of planches) construireLegende(planche);
    actualiserBoutonMode();
    const boutonMode = document.querySelector('[data-action="mode-planches"]');
    if (boutonMode) {
      boutonMode.hidden = false;
      boutonMode.addEventListener('click', () => basculerModePlanches());
    }
  }

  // --- Reglages : theme, date d'examen, export / import -----------------------

  const etatInitial = stockage.lire();
  document.documentElement.dataset.theme = etatInitial.theme || 'auto';

  const boutonReglagesBascule = document.querySelector('[data-action="reglages-bascule"]');
  const panneauReglages = document.getElementById('reglages-panneau');
  if (boutonReglagesBascule && panneauReglages) {
    boutonReglagesBascule.hidden = false;
    boutonReglagesBascule.addEventListener('click', () => {
      const vaOuvrir = panneauReglages.hidden;
      panneauReglages.hidden = !vaOuvrir;
      boutonReglagesBascule.setAttribute('aria-expanded', String(vaOuvrir));
    });
  }

  const boutonsTheme = Array.from(document.querySelectorAll('[data-theme-choix]'));
  function marquerTheme(nom) {
    for (const bouton of boutonsTheme) {
      bouton.setAttribute('aria-pressed', bouton.dataset.themeChoix === nom ? 'true' : 'false');
    }
  }
  marquerTheme(etatInitial.theme || 'auto');
  for (const bouton of boutonsTheme) {
    bouton.addEventListener('click', () => {
      const nom = bouton.dataset.themeChoix;
      document.documentElement.dataset.theme = nom;
      stockage.definirTheme(nom);
      marquerTheme(nom);
    });
  }

  const champDateExamen = document.getElementById('reglages-date-examen');
  const affichageIntervalle = document.getElementById('reglages-intervalle');
  function actualiserIntervalle(iso) {
    if (!affichageIntervalle) return;
    affichageIntervalle.textContent = iso
      ? `intervalle actuel : ${intervalleDeBase(joursEntre(aujourdHuiISO(), iso))} j`
      : '';
  }
  if (champDateExamen) {
    if (etatInitial.dateExamen) champDateExamen.value = etatInitial.dateExamen;
    actualiserIntervalle(etatInitial.dateExamen);
    champDateExamen.addEventListener('change', () => {
      stockage.definirDateExamen(champDateExamen.value || null);
      actualiserIntervalle(champDateExamen.value);
    });
  }

  document.querySelector('[data-action="exporter"]')?.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([stockage.exporter()], { type: 'application/json' }));
    const lien = document.createElement('a');
    lien.href = url;
    lien.download = 'progression-anatomie.json';
    lien.click();
    URL.revokeObjectURL(url);
  });

  const champImport = document.getElementById('reglages-import');
  const statutImport = document.getElementById('reglages-statut');
  champImport?.addEventListener('change', () => {
    const fichier = champImport.files && champImport.files[0];
    if (!fichier) return;
    const lecteur = new FileReader();
    lecteur.onload = () => {
      const ok = stockage.importer(String(lecteur.result || ''));
      if (statutImport) statutImport.textContent = ok ? 'Import réussi.' : 'Fichier invalide, import ignoré.';
      if (ok) window.location.reload();
    };
    lecteur.readAsText(fichier);
  });

  // --- Raccourcis clavier ------------------------------------------------------

  document.addEventListener('keydown', (evenement) => {
    if (estDansUnChamp(evenement.target)) return;

    switch (evenement.key) {
      case ' ':
      case 'Spacebar':
        evenement.preventDefault();
        basculerCarteCourante();
        break;
      case '1':
        appliquerVerdictCourant('rate');
        break;
      case '2':
        appliquerVerdictCourant('difficile');
        break;
      case '3':
        appliquerVerdictCourant('su');
        break;
      case 'ArrowLeft':
        evenement.preventDefault();
        ongletVoisin(-1);
        break;
      case 'ArrowRight':
        evenement.preventDefault();
        ongletVoisin(1);
        break;
      case 'm':
      case 'M':
        if (planches.length) basculerModePlanches();
        break;
      default:
        break;
    }
  });
}

// Chemin relatif a la page (chapitre-N.html vit directement dans site/,
// comme assets/cours.json) : pas de calcul de base, la resolution native du
// navigateur suffit. Asynchrone et tolerant a l'echec -- reseau absent, page
// ouverte en file:// -- pour ne jamais bloquer le reste de l'interface.
function chargerCours(surSucces) {
  fetch('assets/cours.json')
    .then((reponse) => (reponse.ok ? reponse.json() : null))
    .then((cours) => {
      if (cours) surSucces(cours);
    })
    .catch(() => {
      // Le quiz se degrade sans correction automatique ; cartes et
      // pastilles restent fonctionnelles, elles ne dependent pas de cours.json.
    });
}
