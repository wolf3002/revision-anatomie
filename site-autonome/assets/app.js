const __module_planificateur = (function () {
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

function ajouterJours(iso, n) {
  const date = new Date(`${iso}T00:00:00Z`);
  return new Date(date.getTime() + n * JOUR_MS).toISOString().slice(0, 10);
}

function intervalleDeBase(joursAvantExamen) {
  if (!Number.isFinite(joursAvantExamen) || joursAvantExamen <= 0) {
    return INTERVALLE_PAR_DEFAUT;
  }
  return Math.min(INTERVALLE_MAX, Math.max(1, Math.round(0.15 * joursAvantExamen)));
}

function echeance(item, intervalle) {
  if (!item.derniereVue || item.statut === 'jamais') return '0000-01-01';
  if (item.statut === 'rate') return item.derniereVue;
  const delai = item.statut === 'difficile'
    ? Math.max(1, Math.round(intervalle / 2))
    : intervalle;
  return ajouterJours(item.derniereVue, delai);
}

function estDu(item, intervalle, aujourdHui) {
  return echeance(item, intervalle) <= aujourdHui;
}

function composerSeance(items, { intervalle, aujourdHui, taille = 25 }) {
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
function reinjecterRate(file, itemMisAJour) {
  if (!itemMisAJour || itemMisAJour.statut !== 'rate') return file;
  return [...file, itemMisAJour];
}
  return { ajouterJours, intervalleDeBase, echeance, estDu, composerSeance, reinjecterRate };
})();
const { ajouterJours, intervalleDeBase, echeance, estDu, composerSeance, reinjecterRate } = __module_planificateur;

const __module_stockage = (function () {
/**
 * Persistance de la progression.
 *
 * Le support est injecte plutot qu'importe depuis window : le module se teste
 * sans navigateur, et un navigateur en navigation privee -- ou un quota plein --
 * degrade l'experience sans casser l'application.
 */

const CLE = 'uc1-anatomie-v1';

const ETAT_VIERGE = { dateExamen: null, theme: 'auto', items: {} };

function estEtatValide(valeur) {
  return Boolean(valeur)
    && typeof valeur === 'object'
    && typeof valeur.items === 'object'
    && valeur.items !== null
    && !Array.isArray(valeur.items);
}

function creerStockage(support) {
  function lire() {
    try {
      const brut = support.getItem(CLE);
      if (!brut) return { ...ETAT_VIERGE, items: {} };
      const valeur = JSON.parse(brut);
      return estEtatValide(valeur) ? { ...ETAT_VIERGE, ...valeur } : { ...ETAT_VIERGE, items: {} };
    } catch {
      return { ...ETAT_VIERGE, items: {} };
    }
  }

  function ecrire(etat) {
    try {
      support.setItem(CLE, JSON.stringify(etat));
    } catch {
      // Quota plein ou stockage interdit : la session reste utilisable,
      // seule la memorisation entre visites est perdue.
    }
  }

  function modifier(transformation) {
    const etat = lire();
    transformation(etat);
    ecrire(etat);
  }

  return {
    lire,
    ecrireItem(id, item) { modifier((etat) => { etat.items[id] = item; }); },
    definirDateExamen(iso) { modifier((etat) => { etat.dateExamen = iso; }); },
    definirTheme(nom) { modifier((etat) => { etat.theme = nom; }); },
    exporter() { return JSON.stringify(lire(), null, 2); },
    importer(json) {
      try {
        const valeur = JSON.parse(json);
        if (!estEtatValide(valeur)) return false;
        ecrire({ ...ETAT_VIERGE, ...valeur });
        return true;
      } catch {
        return false;
      }
    },
    reinitialiser() { try { support.removeItem(CLE); } catch { /* sans effet */ } },
  };
}
  return { creerStockage, CLE };
})();
const { creerStockage, CLE } = __module_stockage;

const __module_exercices = (function () {
/**
 * Logique des trois exercices : carte, question, pastille muette.
 *
 * Fonctions pures : elles prennent un etat et en renvoient un nouveau, sans
 * toucher au DOM et sans muter leurs arguments. Le rendu vit dans interface.js.
 */

const VERDICTS = new Set(['rate', 'difficile', 'su']);

function appliquerAutoEvaluation(item, verdict, aujourdHui) {
  if (!VERDICTS.has(verdict)) return item;
  return {
    ...item,
    statut: verdict,
    derniereVue: aujourdHui,
    echecs: verdict === 'rate' ? item.echecs + 1 : 0,
  };
}

function corrigerQuestion(question, indexChoisi) {
  return {
    juste: indexChoisi === question.bonne,
    bonne: question.bonne,
    expl: question.expl,
  };
}

function normaliser(saisie) {
  return (saisie || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[-'']/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function verifierPastille(pastille, saisie) {
  const attendu = normaliser(pastille.t);
  const propose = normaliser(saisie);
  return propose.length > 0 && propose === attendu;
}

function itemsDuCours(cours) {
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
    // Meme formule d'identifiant que le data-id pose par outils/construire.py
    // sur le <tr> correspondant (§ _rendre_volet, cle "muscles") : une seule
    // definition en Python, une seule en JS, jamais partagee -- une derive
    // entre les deux casserait silencieusement enregistrerVerdict (l'item ne
    // retrouverait jamais sa ligne).
    for (const muscle of chapitre.muscles || []) {
      items.push(neuf(`${chapitre.num}#muscle#${muscle.nom}`, 'muscle'));
    }
  }
  return items;
}
  return { appliquerAutoEvaluation, corrigerQuestion, normaliser, verifierPastille, itemsDuCours };
})();
const { appliquerAutoEvaluation, corrigerQuestion, normaliser, verifierPastille, itemsDuCours } = __module_exercices;

const __module_interface = (function () {
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
 * concerne -- clone depuis #reservoir-seance, injecte dans index.html par outils/empaqueter.py dans cette variante autonome -- et le rejoue avec les memes
 * fonctions que ci-dessous. Un item de seance est donc, litteralement, le
 * meme DOM que dans sa page de chapitre -- pas une imitation.
 */


// Types que la seance du jour sait effectivement rendre et evaluer (voir
// elementPourItem, itemEvalue et le branchement dans afficherEtapeCourante,
// plus bas). Defaut Critical corrige ici (revue du plan chapitres-2-a-7,
// tache 1bis) : exercices.itemsDuCours exposait deja les items de muscle --
// donc le planificateur leur calculait une echeance et les anneaux de
// progression les comptaient -- mais aucune branche de la seance ne savait
// les afficher : tires en seance, ils disparaissaient sans un mot, alors que
// le compteur affirmait le contraire. Exporte (module sans DOM au chargement,
// importable par node --test) pour que tests/interface.test.js verifie
// mecaniquement que tout type produit par itemsDuCours figure ici -- pas
// seulement pour les muscles, pour tout futur type.
const TYPES_RENDUS_EN_SEANCE = ['carte', 'quiz', 'pastille', 'muscle'];

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

function demarrer(document, support) {
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

  // Hook pose par le bloc "Seance du jour" plus bas (accueil uniquement) pour
  // reinjecter en fin de file un item note "rate" PENDANT la seance en cours
  // (spec §4.3). Reste a `null` sur une page de chapitre, qui n'a pas de
  // notion de file de seance -- enregistrerVerdict y fonctionne exactement
  // comme avant.
  let surVerdictPendantSeance = null;

  function itemParDefaut(id) {
    return coursItemsParDefaut.get(id) || { echecs: 0 };
  }

  function enregistrerVerdict(id, verdict) {
    const etat = stockage.lire();
    const itemExistant = etat.items[id] || itemParDefaut(id);
    const itemMisAJour = appliquerAutoEvaluation(itemExistant, verdict, aujourdHuiISO());
    stockage.ecrireItem(id, itemMisAJour);
    actualiserProgression();
    if (surVerdictPendantSeance) surVerdictPendantSeance(itemMisAJour);
    return itemMisAJour;
  }

  // --- Onglets ------------------------------------------------------------

  const boutonsOnglet = Array.from(document.querySelectorAll('.onglet'));
  const volets = Array.from(document.querySelectorAll('.volet'));
  const barreCarte = document.getElementById('actions-carte');

  // Le premier onglet est toujours la fiche (outils/construire.py, GROUPES) :
  // un chapitre s'ouvre sur le cours a lire, pas sur un exercice.
  //
  // Boutons de mode (planches, muscles) : ils pilotent un onglet de TEST et
  // n'ont de sens que sur lui. Sur la fiche, les planches et la table sont en
  // lecture seule, sans mode : un bouton qui n'y change rien serait un piege.
  // `data-pret` est pose par la section qui equipe le bouton -- un bouton non
  // equipe (page sans planche, sans table) reste cache quel que soit l'onglet.
  const boutonsMode = Array.from(document.querySelectorAll('[data-visible-sur]'));
  let ongletCourant = null;

  function actualiserBoutonsMode() {
    for (const bouton of boutonsMode) {
      bouton.hidden = !(bouton.dataset.pret === 'oui'
        && bouton.dataset.visibleSur === ongletCourant);
    }
  }

  function activerOnglet(cle, { focus = false } = {}) {
    ongletCourant = cle;
    for (const bouton of boutonsOnglet) {
      bouton.setAttribute('aria-selected', bouton.dataset.onglet === cle ? 'true' : 'false');
    }
    for (const volet of volets) {
      volet.hidden = volet.dataset.volet !== cle;
    }
    actualiserBoutonsMode();
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

  // Au clic (pas au chargement) : si on a lu la fiche jusqu'en bas, le contenu
  // du nouvel onglet doit commencer a l'ecran, pas quelque part au milieu. Sur
  // telephone la barre d'onglets est au-dessus du contenu : on s'arrete sur elle
  // pour pouvoir rechanger d'onglet ; a partir de 720 px elle est collee a gauche
  // (sticky), c'est le contenu qu'on ramene en haut.
  function revenirEnHautDuContenu() {
    const large = window.matchMedia('(min-width: 720px)').matches;
    const cible = document.querySelector(large ? '.volets' : '.onglets');
    if (cible && cible.getBoundingClientRect().top < 0) cible.scrollIntoView({ block: 'start' });
  }

  for (const bouton of boutonsOnglet) {
    bouton.addEventListener('click', () => {
      activerOnglet(bouton.dataset.onglet);
      revenirEnHautDuContenu();
    });
  }
  if (boutonsOnglet.length) activerOnglet(boutonsOnglet[0].dataset.onglet);

  // Plan de la fiche : ouvert a la construction quand il est court (voir
  // outils/construire.py, PLAN_OUVERT_JUSQU_A) ; sur telephone, meme un plan court
  // repousserait la premiere section hors de l'ecran -- on le replie, un appui
  // le rouvre. Sans JavaScript il reste tel que construit, donc lisible.
  const planFiche = document.querySelector('.plan');
  if (planFiche && window.matchMedia('(max-width: 719px)').matches) planFiche.open = false;

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

  function appliquerModePlanches(nouveauMode) {
    for (const planche of planches) {
      planche.dataset.mode = nouveauMode;
      const liste = planche.querySelector('.legendes');
      const bouton = planche.querySelector(':scope > button.action');
      if (liste) liste.hidden = nouveauMode !== 'muet';
      if (bouton) bouton.hidden = nouveauMode !== 'muet';
    }
    actualiserBoutonMode();
  }

  function basculerModePlanches() {
    appliquerModePlanches(etatModePlanches() === 'muet' ? 'legende' : 'muet');
  }

  if (planches.length) {
    for (const planche of planches) construireLegende(planche);
    actualiserBoutonMode();
    const boutonMode = document.querySelector('[data-action="mode-planches"]');
    if (boutonMode) {
      boutonMode.dataset.pret = 'oui';
      boutonMode.addEventListener('click', () => basculerModePlanches());
      // L'onglet Planche est un onglet de test : il s'ouvre MUET (pastilles a
      // remplir), la version legendee vivant desormais dans la fiche. La bascule
      // reste la pour verifier apres tentative. Sans JavaScript, ce code ne
      // tourne pas : les planches restent legendees, donc lisibles. Uniquement
      // ou le bouton de mode existe (page de chapitre) : sur l'accueil de la
      // variante autonome, les planches du reservoir de seance ne sont pas un
      // onglet, la seance les met en muet elle-meme.
      appliquerModePlanches('muet');
      actualiserBoutonsMode();
    }
  }

  // --- Muscles (reference / champs) -------------------------------------------
  //
  // Defaut Critical corrige ici (plan chapitres-2-a-7, tache 1) : la table
  // n'avait ni masquage ni champ de saisie -- ouvrir l'onglet exposait toutes
  // les reponses. Meme grammaire que le mode muet des planches ci-dessus,
  // appliquee ligne par ligne : la verite attendue vient du DOM (le texte
  // deja rendu par outils/construire.py dans .muscle__valeur), jamais de
  // cours.json -- comme verifierPastille pour une legende de planche.
  //
  // A la difference des planches (par defaut "legende", donc lisible, tant
  // qu'on n'a pas explicitement demande le mode muet), le mode par defaut ici
  // est "champs" : c'est la table de reference (valeurs visibles) qui est
  // l'etat secondaire, atteint par bascule. Sans JavaScript, aucun .muscle__champ
  // n'est jamais cree : la table reste sur son unique etat construit -- valeurs
  // visibles -- ce qui satisfait la degradation sans script.

  function construireChampsMuscles(table) {
    for (const ligne of table.querySelectorAll(':scope > tbody > tr')) {
      for (const cellule of ligne.querySelectorAll(':scope > td')) {
        const valeur = cellule.querySelector('.muscle__valeur');
        if (!valeur) continue;
        const attendu = valeur.textContent.trim();
        const libelle = ['Origine', 'Terminaison', 'Action'][cellule.cellIndex - 1] || 'Réponse';

        const enveloppe = document.createElement('span');
        enveloppe.className = 'muscle__champ';

        const champ = document.createElement('input');
        champ.type = 'text';
        champ.className = 'champ';
        champ.autocomplete = 'off';
        champ.dataset.attendu = attendu;
        champ.setAttribute('aria-label', `${libelle} — ${ligne.dataset.id || ''}`);

        const etat = document.createElement('span');
        etat.className = 'muscle__etat mono';

        enveloppe.append(champ, etat);
        cellule.appendChild(enveloppe);
      }
    }
  }

  // Verifie TOUTES les lignes de la table en un seul geste, comme
  // verifierPlanche pour toutes les pastilles d'une planche : "ligne par
  // ligne" (spec §4.2) decrit la granularite du verdict -- un par muscle --
  // pas un bouton distinct par ligne.
  function verifierMuscles(table) {
    for (const ligne of table.querySelectorAll(':scope > tbody > tr')) {
      const champs = Array.from(ligne.querySelectorAll('.muscle__champ input'));
      if (!champs.length) continue;
      let toutCorrect = true;
      for (const champ of champs) {
        const correct = verifierPastille({ t: champ.dataset.attendu }, champ.value);
        champ.dataset.verdict = correct ? 'bon' : 'mauvais';
        const etatSpan = champ.parentElement.querySelector('.muscle__etat');
        if (etatSpan) etatSpan.textContent = correct ? 'juste' : 'faux';
        if (!correct) toutCorrect = false;
      }
      const id = ligne.dataset.id;
      if (id) enregistrerVerdict(id, toutCorrect ? 'su' : 'rate');
      ligne.dataset.verifie = 'oui';
    }
  }

  function etatModeMuscles(table) {
    return table.dataset.mode === 'reference' ? 'reference' : 'champs';
  }

  function actualiserBoutonModeMuscles(table, bouton) {
    if (!bouton) return;
    const mode = etatModeMuscles(table);
    bouton.setAttribute('aria-pressed', mode === 'champs' ? 'true' : 'false');
    const etat = bouton.querySelector('.mode-muscles__etat');
    if (etat) etat.textContent = mode === 'champs' ? 'mode champs' : 'mode référence';
  }

  // Comme basculerModePlanches : le bouton Verifier n'a de sens qu'en mode
  // champs -- en reference, rien n'est masque a verifier.
  function basculerModeMuscles(table, boutonMode, boutonVerifier) {
    const nouveauMode = etatModeMuscles(table) === 'champs' ? 'reference' : 'champs';
    table.dataset.mode = nouveauMode;
    if (boutonVerifier) boutonVerifier.hidden = nouveauMode !== 'champs';
    actualiserBoutonModeMuscles(table, boutonMode);
  }

  // Construit les champs, force le mode par defaut et pose le bouton
  // Verifier -- partage entre la page de chapitre (une table, toutes ses
  // lignes) et la seance du jour (une table clonee, une seule ligne : voir
  // elementPourItem plus bas). Une seule definition : la seance affiche
  // litteralement le meme mecanisme que l'onglet Muscles, jamais une
  // seconde grammaire pour la meme table.
  function activerPresentationMuscles(table) {
    construireChampsMuscles(table);
    table.dataset.mode = 'champs';

    const boutonVerifier = document.createElement('button');
    boutonVerifier.type = 'button';
    boutonVerifier.className = 'action';
    boutonVerifier.textContent = 'Vérifier';
    boutonVerifier.addEventListener('click', () => verifierMuscles(table));
    table.after(boutonVerifier);
    return boutonVerifier;
  }

  const tablesMuscles = Array.from(document.querySelectorAll('.muscles'));
  if (tablesMuscles.length) {
    // Une seule table par page de chapitre (l'onglet Muscles n'apparait que
    // si le chapitre en a) : la boucle documente qu'aucune limite n'est
    // supposee, sans en tirer de complexite supplementaire.
    for (const table of tablesMuscles) {
      const boutonVerifier = activerPresentationMuscles(table);

      const boutonMode = document.querySelector('[data-action="mode-muscles"]');
      actualiserBoutonModeMuscles(table, boutonMode);
      if (boutonMode) {
        boutonMode.dataset.pret = 'oui';
        actualiserBoutonsMode();
        boutonMode.addEventListener('click', () => basculerModeMuscles(table, boutonMode, boutonVerifier));
      }
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
    const zoneMuscleSeance = document.getElementById('seance-muscle');
    const boutonSuivant = document.getElementById('seance-suivant');
    const boutonQuitter = document.getElementById('seance-quitter');

    // Une page de chapitre par numero, recuperee une seule fois et reutilisee
    // pour toute la seance -- c'est elle qui porte le vrai rendu d'une carte,
    // d'une question ou d'une planche (voir l'exception documentee en tete
    // de fichier).
    // Variante autonome (outils/empaqueter.py) : plus de fetch de
    // chapitre-N.html (impossible en file://) -- clone depuis
    // #reservoir-seance, depose dans index.html a la construction avec
    // EXACTEMENT le balisage que outils/construire.py (_rendre_volet) met
    // dans chapitre-N.html pour ce meme chapitre. Meme fonctions de rendu :
    // l'identite entre un item de seance et sa page de chapitre reste
    // garantie par construction, pas par une copie a resynchroniser.
    function reservoirSeance() {
      return document.getElementById('reservoir-seance');
    }

    async function elementPourItem(item) {
      const page = reservoirSeance();
      if (!page) return null;

      // Un item "muscle" designe une ligne (data-id, pas un id DOM -- un nom
      // de muscle contient des espaces). A la difference d'une pastille, sa
      // granularite d'affichage est LA LIGNE, pas toute la table (avis du
      // relecteur, tache 1bis) : on clone la table entiere pour garder sa
      // presentation exacte (caption, thead, structure a trois <td>), puis on
      // retire toutes les lignes sauf la sienne -- jamais une seconde
      // grammaire pour la meme table.
      if (item.type === 'muscle') {
        const ligneSource = Array.from(page.querySelectorAll('tr[data-id]'))
          .find((tr) => tr.dataset.id === item.id);
        const tableSource = ligneSource?.closest('table.muscles');
        if (!tableSource) return null;
        const clone = document.importNode(tableSource, true);
        for (const tr of clone.querySelectorAll('tbody tr')) {
          if (tr.dataset.id !== item.id) tr.remove();
        }
        return clone;
      }

      // Un item "pastille" designe une legende individuelle, mais la seule
      // unite affichable et verifiable est la planche entiere (verifierPlanche
      // corrige toutes ses pastilles a la fois, comme en page de chapitre).
      const idSource = item.type === 'pastille' ? item.id.split('#')[0] : item.id;
      const source = page.querySelector(`#${idSource}`);
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

    // Cable le hook defini plus haut : chaque verdict enregistre PENDANT la
    // seance (carte, quiz, planche, muscle -- enregistrerVerdict est le seul
    // point de passage commun) passe ici. `file.length` vaut 0 hors seance
    // (avant "Commencer", ou apres terminerSeance) : reinjecterRate n'agit
    // donc jamais en dehors d'une seance reellement en cours. Pousser en fin
    // de TABLEAU, quelle que soit la position courante, est exactement "fin
    // de la seance en cours" (spec §4.3) -- pas besoin de connaitre la
    // position pour ca.
    surVerdictPendantSeance = (itemMisAJour) => {
      if (!file.length) return;
      file = reinjecterRate(file, itemMisAJour);
      if (compteSeance) compteSeance.textContent = `${position + 1} / ${file.length}`;
    };

    // Un item est "revise" s'il porte la trace laissee par une vraie
    // evaluation -- pas seulement affiche. Cartes et quiz marquent deja le
    // DOM (dernierVerdict, repondue) pour leurs propres besoins ; verifierPlanche
    // pose desormais le meme genre de marqueur pour une planche.
    function itemEvalue(item, element) {
      if (!item || !element) return false;
      if (item.type === 'carte') return Boolean(element.dataset.dernierVerdict);
      if (item.type === 'quiz') return element.dataset.repondue === 'oui';
      if (item.type === 'pastille') return element.dataset.verifie === 'oui';
      // element est ici la table clonee a une seule ligne (voir
      // elementPourItem) : verifierMuscles pose dataset.verifie='oui' sur
      // cette ligne, comme verifierPlanche le fait pour une pastille.
      // querySelector('tr') seul aurait cible le <tr> du thead (Muscle /
      // Origine / Terminaison / Action, sans data-verifie) plutot que la
      // ligne de donnees -- piege releve par pilotage reel avant ce correctif.
      if (item.type === 'muscle') return element.querySelector('tbody tr')?.dataset.verifie === 'oui';
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
      if (zoneMuscleSeance) { zoneMuscleSeance.hidden = true; zoneMuscleSeance.innerHTML = ''; }
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
      } else if (item.type === 'muscle' && zoneMuscleSeance) {
        // element est la table clonee a une seule ligne (elementPourItem) :
        // meme presentation, memes champs, meme verification que l'onglet
        // Muscles de la page de chapitre -- activerPresentationMuscles est
        // la MEME fonction que celle qui equipe la table complete, juste
        // appliquee ici a un clone d'une seule ligne.
        zoneMuscleSeance.hidden = false;
        zoneMuscleSeance.appendChild(element);
        activerPresentationMuscles(element);
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

  // Invite a saisir la date d'examen (accueil uniquement) : la seule
  // information que le site demande (spec S3.4), visible tant qu'elle n'est
  // pas connue -- sans elle, l'intervalle retombe a 3 jours au lieu d'etre
  // calcule sur le delai reel (planificateur.intervalleDeBase). Ni obstacle
  // ni etape obligatoire : le bouton "Demarrer la seance du jour" reste
  // cliquable sans qu'on y touche.
  const inviteDateExamen = document.getElementById('invite-date-examen');
  const champInviteDateExamen = document.getElementById('invite-date-examen-saisie');
  if (inviteDateExamen) inviteDateExamen.hidden = Boolean(etatInitial.dateExamen);

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
      // Renseignee depuis les reglages plutot que depuis l'invite (chemin
      // rare mais possible) : l'invite n'a plus lieu d'etre, meme logique
      // que le chemin normal ci-dessous.
      if (inviteDateExamen) inviteDateExamen.hidden = Boolean(champDateExamen.value);
    });
  }

  if (champInviteDateExamen) {
    champInviteDateExamen.addEventListener('change', () => {
      const valeur = champInviteDateExamen.value || null;
      stockage.definirDateExamen(valeur);
      // Reglages tenus a jour tout de suite : rouvrir le panneau plus tard
      // doit montrer la meme date, pas un champ vide.
      if (champDateExamen) champDateExamen.value = valeur || '';
      actualiserIntervalle(valeur);
      if (inviteDateExamen) inviteDateExamen.hidden = Boolean(valeur);
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
        // Seulement sur l'onglet Planche : sur la fiche ou ailleurs, la bascule
        // changerait l'etat d'un onglet qu'on ne voit pas.
        if (planches.length && ongletCourant === 'planche') basculerModePlanches();
        break;
      default:
        break;
    }
  });
}

function chargerCours(surSucces) {
  // Variante autonome (outils/empaqueter.py) : plus de requete reseau --
  // assets/cours-data.js, charge juste avant ce script (cf.
  // _classiciser_scripts), affecte deja le contenu du cours a
  // window.COURS_JSON. Meme contrat que la version reseau qu'il remplace :
  // asynchrone, tolerant a l'absence de la variable (le quiz se degrade
  // sans correction automatique ; cartes et pastilles restent
  // fonctionnelles, elles ne dependent pas de cette donnee).
  return Promise.resolve().then(() => {
    if (window.COURS_JSON) surSucces(window.COURS_JSON);
  });
}
  return { demarrer, TYPES_RENDUS_EN_SEANCE };
})();
const { demarrer, TYPES_RENDUS_EN_SEANCE } = __module_interface;


demarrer(document, window.localStorage);

