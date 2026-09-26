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
 *
 * Exception assumee : la seance du jour (accueil). Sa composition depend du
 * localStorage, donc ne peut pas etre figee au moment du build. Elle ne
 * redefinit pour autant aucun gabarit de carte/question/planche -- elle CLONE
 * l'element deja rendu par outils/construire.py dans la page du chapitre
 * concerne (chapitre-N.html, recuperee par fetch) et le rejoue avec les memes
 * fonctions que ci-dessous. Un item de seance est donc, litteralement, le
 * meme DOM que dans sa page de chapitre -- pas une imitation.
 */

import { intervalleDeBase, composerSeance } from './planificateur.js';
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
  // item neuf, liste des chapitres pour la seance et la progression).
  // Chargees de facon asynchrone et non bloquante : le reste de l'interface
  // doit rester utilisable meme si cette requete echoue (reseau absent, page
  // ouverte en file://).
  let coursDonnees = null;
  let coursItemsParDefaut = new Map();
  let coursQuiz = new Map();
  const coursPret = chargerCours((cours) => {
    coursDonnees = cours;
    for (const item of itemsDuCours(cours)) coursItemsParDefaut.set(item.id, item);
    for (const chapitre of cours.chapitres) {
      for (const q of chapitre.quiz || []) coursQuiz.set(q.id, q);
    }
    actualiserProgression();
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
    actualiserProgression();
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
    // Marqueur reutilise par la seance du jour pour distinguer une planche
    // reellement verifiee d'une planche seulement affichee puis passee.
    planche.dataset.verifie = 'oui';
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

  // --- Progression (accueil) --------------------------------------------------

  // Un chapitre jamais ouvert doit se voir vide, pas gris-neutre (spec §4.1) :
  // data-etat="vide" (pose par defaut au build) distingue "aucun item touche"
  // de "items touches, 0 % su", que le seul pourcentage confondrait.
  function actualiserProgression() {
    if (!coursDonnees) return;
    const etat = stockage.lire();
    const titresParChapitre = new Map(coursDonnees.chapitres.map((c) => [c.num, c.titre]));
    const parChapitre = new Map();
    for (const item of itemsDuCours(coursDonnees)) {
      if (!parChapitre.has(item.chapitre)) parChapitre.set(item.chapitre, []);
      parChapitre.get(item.chapitre).push(item);
    }
    for (const [numero, items] of parChapitre) {
      const li = document.querySelector(`.progression li[data-chapitre="${numero}"]`);
      if (!li || !items.length) continue;
      let touche = false;
      let su = 0;
      for (const item of items) {
        const enregistre = etat.items[item.id];
        if (enregistre) {
          touche = true;
          if (enregistre.statut === 'su') su += 1;
        }
      }
      const anneau = li.querySelector('.anneau');
      const valeur = li.querySelector('.anneau__valeur');
      const part = touche ? Math.round((su / items.length) * 100) : 0;
      const etatTexte = touche ? `${part} % su` : 'jamais ouvert';
      li.dataset.etat = touche ? 'touche' : 'vide';
      if (anneau) {
        anneau.style.setProperty('--part', String(part));
        // Sans cette ligne, un lecteur d'ecran annoncait toujours "jamais
        // ouvert" (valeur figee au build) meme apres des verdicts reels --
        // l'anneau mentait silencieusement a qui ne voit pas son remplissage.
        const titre = titresParChapitre.get(numero) || '';
        anneau.setAttribute('aria-label', `Chapitre ${numero}, ${titre} : ${etatTexte}`);
      }
      if (valeur) valeur.textContent = etatTexte;
    }
  }

  // --- Seance du jour (accueil) ------------------------------------------------

  const boutonSeance = document.getElementById('seance');
  if (boutonSeance) {
    const zoneSeance = document.getElementById('seance-zone');
    const messageSeance = document.getElementById('seance-message');
    const compteSeance = document.getElementById('seance-compte');
    const bandeauConsolidation = document.getElementById('seance-consolidation');
    const voletCartesSeance = zoneSeance?.querySelector('.volet[data-volet="cartes"]');
    const voletQuizSeance = zoneSeance?.querySelector('.volet[data-volet="quiz"]');
    const zonePlancheSeance = document.getElementById('seance-planche');
    const boutonSuivant = document.getElementById('seance-suivant');
    const boutonQuitter = document.getElementById('seance-quitter');

    // Une page de chapitre par numero, recuperee une seule fois et reutilisee
    // pour toute la seance -- c'est elle qui porte le vrai rendu d'une carte,
    // d'une question ou d'une planche (voir l'exception documentee en tete
    // de fichier).
    const pagesChapitre = new Map();
    function chargerPageChapitre(numero) {
      if (!pagesChapitre.has(numero)) {
        pagesChapitre.set(
          numero,
          fetch(`chapitre-${numero}.html`)
            .then((reponse) => (reponse.ok ? reponse.text() : null))
            .then((texte) => (texte ? new DOMParser().parseFromString(texte, 'text/html') : null))
            .catch(() => null),
        );
      }
      return pagesChapitre.get(numero);
    }

    async function elementPourItem(item) {
      const page = await chargerPageChapitre(item.chapitre);
      if (!page) return null;
      // Un item "pastille" designe une legende individuelle, mais la seule
      // unite affichable et verifiable est la planche entiere (verifierPlanche
      // corrige toutes ses pastilles a la fois, comme en page de chapitre).
      const idSource = item.type === 'pastille' ? item.id.split('#')[0] : item.id;
      const source = page.getElementById(idSource);
      return source ? document.importNode(source, true) : null;
    }

    let file = [];
    let position = 0;
    let planchesAffichees = new Set();
    // L'item et son element actuellement affiches -- necessaires pour savoir,
    // au moment de passer au suivant, si CET item a reellement ete evalue
    // (voir itemEvalue) avant de le comptabiliser.
    let itemCourant = null;
    let elementCourant = null;
    let nbRevises = 0;
    let nbPasses = 0;
    // Verrou anti-double-declenchement : afficherEtapeCourante() est
    // asynchrone (fetch de la page de chapitre) ; deux clics rapprochés sur
    // Suivant sans lui laisseraient deux appels se chevaucher et corrompre
    // position/file (constate par pilotage -- "Suivant" clique en rafale).
    let enTransition = false;

    // Un item est "revise" s'il porte la trace laissee par une vraie
    // evaluation -- pas seulement affiche. Cartes et quiz marquent deja le
    // DOM (dernierVerdict, repondue) pour leurs propres besoins ; verifierPlanche
    // pose desormais le meme genre de marqueur pour une planche.
    function itemEvalue(item, element) {
      if (!item || !element) return false;
      if (item.type === 'carte') return Boolean(element.dataset.dernierVerdict);
      if (item.type === 'quiz') return element.dataset.repondue === 'oui';
      if (item.type === 'pastille') return element.dataset.verifie === 'oui';
      return false;
    }

    // Comptabilise l'item actuellement affiche (revise ou passe) puis oublie
    // sa reference -- idempotent : sans item courant, ne fait rien. Appelee
    // une seule fois par item reellement montre, que la seance continue ou
    // s'arrete ici.
    function comptabiliserEtapeCourante() {
      if (!itemCourant || !elementCourant) return;
      if (itemEvalue(itemCourant, elementCourant)) nbRevises += 1;
      else nbPasses += 1;
      itemCourant = null;
      elementCourant = null;
    }

    function viderZoneSeance() {
      if (voletCartesSeance) { voletCartesSeance.hidden = true; voletCartesSeance.innerHTML = ''; }
      if (voletQuizSeance) { voletQuizSeance.hidden = true; voletQuizSeance.innerHTML = ''; }
      if (zonePlancheSeance) { zonePlancheSeance.hidden = true; zonePlancheSeance.innerHTML = ''; }
      if (barreCarte) barreCarte.hidden = true;
      carteActive = null;
    }

    // Le bilan dit ce qui a reellement ete fait, pas ce qui a ete affiche :
    // un item juste "passe" au clic de Suivant, sans verdict ni reponse, ne
    // compte pas comme revise -- sinon le compteur flatte au lieu d'informer.
    function bilanSeance() {
      const revises = `${nbRevises} item(s) révisé(s)`;
      return nbPasses ? `${revises}, ${nbPasses} passé(s).` : `${revises}.`;
    }

    function terminerSeance(motif) {
      comptabiliserEtapeCourante();
      const bilan = bilanSeance();
      viderZoneSeance();
      if (zoneSeance) zoneSeance.hidden = true;
      if (messageSeance) {
        messageSeance.textContent = motif === 'interrompue'
          ? `Séance interrompue — ${bilan}`
          : `Séance terminée — ${bilan}`;
      }
      file = [];
      position = 0;
      nbRevises = 0;
      nbPasses = 0;
    }

    async function afficherEtapeCourante() {
      if (position >= file.length) {
        terminerSeance('fin');
        return;
      }
      viderZoneSeance();
      const item = file[position];

      // Deux items "pastille" de la meme planche affichent la meme planche :
      // verifier la premiere occurrence verifie deja toutes ses pastilles, la
      // seconde n'apporterait rien de plus a revoir. Jamais affichee, elle
      // n'entre dans aucun des deux compteurs.
      if (item.type === 'pastille') {
        const plancheId = item.id.split('#')[0];
        if (planchesAffichees.has(plancheId)) {
          position += 1;
          await afficherEtapeCourante();
          return;
        }
        planchesAffichees.add(plancheId);
      }

      if (compteSeance) compteSeance.textContent = `${position + 1} / ${file.length}`;
      const element = await elementPourItem(item);
      if (!element) {
        // Page de chapitre introuvable ou id absent : on saute l'etape sans
        // bloquer le reste de la seance ; jamais affichee, non comptabilisee.
        position += 1;
        await afficherEtapeCourante();
        return;
      }

      if (item.type === 'carte' && voletCartesSeance) {
        voletCartesSeance.hidden = false;
        voletCartesSeance.appendChild(element);
        element.tabIndex = 0;
        element.addEventListener('click', () => activerCarte(element));
        element.addEventListener('focus', () => { carteActive = element; });
        // Selectionne la carte SANS la reveler (equivalent du tabulateur en
        // page de chapitre) : reveler exige un geste explicite (clic ou
        // Espace), sinon la reponse s'affiche avant toute tentative de rappel.
        carteActive = element;
        element.focus();
      } else if (item.type === 'quiz' && voletQuizSeance) {
        voletQuizSeance.hidden = false;
        voletQuizSeance.appendChild(element);
      } else if (item.type === 'pastille' && zonePlancheSeance) {
        zonePlancheSeance.hidden = false;
        zonePlancheSeance.appendChild(element);
        element.dataset.mode = 'muet';
        construireLegende(element);
        const liste = element.querySelector('.legendes');
        const bouton = element.querySelector(':scope > button.action');
        if (liste) liste.hidden = false;
        if (bouton) bouton.hidden = false;
      }

      itemCourant = item;
      elementCourant = element;
    }

    boutonSuivant?.addEventListener('click', async () => {
      // !file.length : la seance est deja terminee (file videe par
      // terminerSeance) -- un clic en trop, encore en file d'attente au
      // moment ou #seance-zone a disparu, ne doit pas rejouer la fin.
      if (enTransition || !file.length) return;
      enTransition = true;
      // Comptabilise l'item qu'on quitte AVANT de passer au suivant : lui
      // seul sait s'il a ete evalue (verdict, reponse, verification) ou
      // seulement affiche.
      comptabiliserEtapeCourante();
      position += 1;
      try {
        await afficherEtapeCourante();
      } finally {
        enTransition = false;
      }
    });
    boutonQuitter?.addEventListener('click', () => {
      enTransition = false;
      terminerSeance('interrompue');
    });

    async function demarrerSeance() {
      if (enTransition) return;
      enTransition = true;
      try {
        if (messageSeance) messageSeance.textContent = '';
        if (!coursDonnees) {
          if (messageSeance) messageSeance.textContent = 'Chargement du contenu…';
          await coursPret;
        }
        if (!coursDonnees) {
          if (messageSeance) messageSeance.textContent = 'Contenu indisponible pour le moment.';
          return;
        }

        // Fusion stockage + items par defaut : un item inconnu du stockage
        // demarre a "jamais", donc du immediatement (spec §4.3/§4.4).
        const etat = stockage.lire();
        const items = itemsDuCours(coursDonnees).map((item) => etat.items[item.id] || item);
        const aujourdhui = aujourdHuiISO();
        const joursAvantExamen = etat.dateExamen ? joursEntre(aujourdhui, etat.dateExamen) : NaN;
        const intervalle = intervalleDeBase(joursAvantExamen);

        let composee = composerSeance(items, { intervalle, aujourdHui: aujourdhui, taille: 25 });
        let consolidation = false;
        if (!composee.length) {
          // Rien de du : consolidation sur les items les plus fragiles. Meme
          // composerSeance (fragiles d'abord, puis entrelacement des chapitres
          // et des formats), juste avec une echeance forcee tres loin pour que
          // tout soit "du".
          consolidation = true;
          composee = composerSeance(items, { intervalle, aujourdHui: '9999-12-31', taille: 25 });
        }
        if (!composee.length) {
          if (messageSeance) messageSeance.textContent = 'Rien à réviser pour le moment.';
          return;
        }

        file = composee;
        position = 0;
        planchesAffichees = new Set();
        itemCourant = null;
        elementCourant = null;
        nbRevises = 0;
        nbPasses = 0;
        if (bandeauConsolidation) bandeauConsolidation.hidden = !consolidation;
        if (zoneSeance) zoneSeance.hidden = false;
        await afficherEtapeCourante();
        zoneSeance?.scrollIntoView({ block: 'start' });
      } finally {
        enTransition = false;
      }
    }

    boutonSeance.addEventListener('click', () => { demarrerSeance(); });
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

  document.querySelector('[data-action="reinitialiser"]')?.addEventListener('click', () => {
    const confirme = window.confirm(
      'Réinitialiser toute la progression ? Cette action est irréversible.',
    );
    if (!confirme) return;
    stockage.reinitialiser();
    window.location.reload();
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
  return fetch('assets/cours.json')
    .then((reponse) => (reponse.ok ? reponse.json() : null))
    .then((cours) => {
      if (cours) surSucces(cours);
    })
    .catch(() => {
      // Le quiz se degrade sans correction automatique ; cartes et
      // pastilles restent fonctionnelles, elles ne dependent pas de cours.json.
    });
}
