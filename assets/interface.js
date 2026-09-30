/**
 * Interface : le seul module autorise a toucher au DOM.
 *
 * Il lit l'etat via `stockage`, calcule via `planificateur` et `exercices`,
 * et n'implemente aucune regle metier lui-meme -- ni echeance, ni verdict de
 * correction, ni tolerance orthographique. Son unique travail : cabler des
 * evenements sur un DOM deja complet (gabarits/ + le rendu de
 * outils/construire.py), et ecrire chaque interaction dans le stockage.
 *
 * Contrat de degradation : la fiche (le cours a lire) vit deja dans le DOM,
 * sans JavaScript, sans rien de masque. Ce module REVELE (retire `hidden`) et
 * MASQUE (le pose) ; il n'injecte du contenu neuf que pour des controles
 * purement interactifs qui n'ont pas de sens sans JavaScript (champs de saisie
 * des planches muettes et des muscles, bouton de verification) -- jamais pour
 * du texte de cours, de carte ou de question.
 *
 * Un seul mecanisme d'exercice : le deroule d'une seance (composerSeance,
 * un item a la fois, verdicts, ecriture en stockage). Il sert
 *   - la seance du jour, sur l'accueil : tous les chapitres ;
 *   - l'onglet « S'exercer » d'une page de chapitre : ce chapitre seul
 *     (attribut data-chapitre du bloc .seance).
 * Il ne redefinit aucun gabarit de carte/question/planche/muscle : il CLONE
 * l'element deja rendu par outils/construire.py -- dans le reservoir cache de
 * la page ([data-reservoir]) quand elle en porte un (page de chapitre,
 * accueil de la variante autonome), sinon dans la page du chapitre concerne,
 * recuperee par fetch -- et le rejoue avec les memes fonctions. Un item de
 * seance est donc, litteralement, le meme DOM que celui que la page contient.
 */

import { intervalleDeBase, composerSeance, reinjecterRate } from './planificateur.js';
import { creerStockage } from './stockage.js';
import { appliquerAutoEvaluation, corrigerQuestion, verifierPastille, itemsDuCours } from './exercices.js';

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
export const TYPES_RENDUS_EN_SEANCE = ['carte', 'quiz', 'pastille', 'muscle'];

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
  // Premiere instruction : tant qu'elle n'a pas tourne, la page est dans son etat
  // sans JavaScript (la fiche seule, une ligne qui dit que les exercices ont
  // besoin du script -- style.css §5.2a). Un module qui ne se charge pas
  // (file://) la laisse donc absente, ce qui est voulu.
  document.documentElement.classList.add('js');

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

  // Hook pose par le bloc "Seance" plus bas pour reinjecter en fin de file un
  // item note "rate" PENDANT la seance en cours (spec §4.3). Reste a `null`
  // hors d'une seance (page de chapitre sur la fiche) : enregistrerVerdict y
  // fonctionne exactement comme avant.
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

  // --- Onglets : Fiche / S'exercer ---------------------------------------------

  const boutonsOnglet = Array.from(document.querySelectorAll('.onglet'));
  const panneaux = Array.from(document.querySelectorAll('.panneau'));
  const barreCarte = document.getElementById('actions-carte');

  // Page de chapitre : deux onglets, un chapitre s'ouvre sur la fiche (le cours a
  // lire), jamais sur un exercice. Sur l'accueil il n'y en a pas : `ongletCourant`
  // reste null, et un exercice de la seance est donc toujours « a l'ecran ».
  let ongletCourant = null;

  // Hook pose par le bloc "Seance" : la premiere ouverture de S'exercer lance la
  // serie, sans second clic. Une serie en cours n'est jamais relancee par un
  // simple aller-retour entre les deux onglets.
  let surPremiereOuvertureExercer = null;
  let exercerDejaOuvert = false;

  // Une carte retournee attend son verdict tant qu'on ne l'a pas juge : la barre
  // ancree en bas d'ecran ne doit pourtant se voir que sur S'exercer, pas sur la
  // fiche qu'on lit.
  function carteAttendUnVerdict() {
    if (!carteActive || !carteActive.isConnected) return false;
    if (carteActive.dataset.dernierVerdict) return false;
    return !carteActive.querySelector('.carte__r')?.dataset.etat;
  }

  function exerciceAffiche() {
    return ongletCourant === null || ongletCourant === 'exercer';
  }

  function activerOnglet(cle, { focus = false, majUrl = true } = {}) {
    ongletCourant = cle;
    for (const bouton of boutonsOnglet) {
      bouton.setAttribute('aria-selected', bouton.dataset.onglet === cle ? 'true' : 'false');
    }
    for (const panneau of panneaux) {
      panneau.hidden = panneau.dataset.panneau !== cle;
    }
    if (barreCarte) barreCarte.hidden = !(cle === 'exercer' && carteAttendUnVerdict());
    if (focus) {
      boutonsOnglet.find((b) => b.dataset.onglet === cle)?.focus();
    }
    if (majUrl) {
      try {
        // L'onglet ouvert survit a un rechargement ; l'accueil le vise par #exercer.
        window.history.replaceState(
          null, '',
          cle === 'exercer' ? '#exercer' : window.location.pathname + window.location.search,
        );
      } catch { /* file:// strict, iframe : sans effet */ }
    }
    if (cle === 'exercer' && !exercerDejaOuvert) {
      exercerDejaOuvert = true;
      if (surPremiereOuvertureExercer) surPremiereOuvertureExercer();
    }
  }

  function ongletVoisin(delta) {
    if (!boutonsOnglet.length) return;
    const index = boutonsOnglet.findIndex((b) => b.getAttribute('aria-selected') === 'true');
    const suivant = (index + delta + boutonsOnglet.length) % boutonsOnglet.length;
    activerOnglet(boutonsOnglet[suivant].dataset.onglet, { focus: true });
  }

  // Au clic (pas au chargement) : si on a lu la fiche jusqu'en bas, le contenu du
  // nouvel onglet doit commencer a l'ecran, pas quelque part au milieu. On s'arrete
  // sur la barre d'onglets -- on peut ainsi rechanger d'onglet d'un geste.
  function revenirAuxOnglets() {
    const barre = document.querySelector('.onglets');
    if (barre && barre.getBoundingClientRect().top < 0) barre.scrollIntoView({ block: 'start' });
  }

  for (const bouton of boutonsOnglet) {
    bouton.addEventListener('click', () => {
      activerOnglet(bouton.dataset.onglet);
      revenirAuxOnglets();
    });
  }

  // Lien de fin de fiche : « tout lu ? » -> S'exercer. Un lien (pas un bouton) : sans
  // JavaScript il ne fait rien et le gabarit le masque.
  for (const lien of document.querySelectorAll('[data-aller]')) {
    lien.addEventListener('click', (evenement) => {
      evenement.preventDefault();
      activerOnglet(lien.dataset.aller);
      revenirAuxOnglets();
    });
  }

  // Plan de la fiche : ouvert a la construction quand il est court (voir
  // outils/construire.py, PLAN_OUVERT_JUSQU_A) ; sur telephone, meme un plan court
  // repousserait la premiere section hors de l'ecran -- on le replie, un appui
  // le rouvre. Sans JavaScript il reste tel que construit, donc lisible.
  const planFiche = document.querySelector('.plan');
  if (planFiche && window.matchMedia('(max-width: 719px)').matches) planFiche.open = false;

  // --- Cartes --------------------------------------------------------------

  // Les cartes n'existent a l'ecran que dans le deroule d'une seance (elles sont
  // clonees depuis le reservoir, voir plus bas) : le volet est celui de la zone
  // de seance, jamais un onglet.
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

  if (barreCarte) {
    barreCarte.querySelector('[data-action="retourner"]')
      ?.addEventListener('click', () => basculerCarteCourante());
    for (const bouton of barreCarte.querySelectorAll('[data-verdict]')) {
      bouton.addEventListener('click', () => appliquerVerdictCourant(bouton.dataset.verdict));
    }
  }

  // --- Quiz ------------------------------------------------------------------

  // Meme remarque : le volet est celui de la zone de seance.
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

  // --- Planches muettes --------------------------------------------------------

  // Le reservoir ([data-reservoir]) tient dans le DOM la place de la page du
  // chapitre : ce sont des MODELES a cloner, pas des exercices affiches. Les
  // equiper au chargement les ferait cloner deja equipes -- un second jeu de
  // champs (muscles) ou un bouton Verifier sans ecouteur (planches : importNode
  // ne copie pas les ecouteurs), donc mort. Un modele reste nu ; la seance
  // equipe le CLONE au moment de l'inserer (voir afficherEtapeCourante).
  const reservoirLocal = document.querySelector('[data-reservoir]');

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

  // Apres la tentative -- et seulement apres --, la correction se montre : les
  // libelles reapparaissent sur le trace et chaque erreur dit ce qu'on attendait.
  // Les champs se figent : on ne « corrige » pas sa reponse en recopiant la bonne.
  function verifierPlanche(planche) {
    const liste = planche.querySelector('.legendes');
    if (!liste) return;

    for (const champ of liste.querySelectorAll('input')) {
      const correct = verifierPastille({ t: champ.dataset.attendu }, champ.value);
      champ.dataset.verdict = correct ? 'bon' : 'mauvais';
      champ.readOnly = true;

      let etatSpan = champ.parentElement.querySelector('.legendes__etat');
      if (!etatSpan) {
        etatSpan = document.createElement('span');
        etatSpan.className = 'legendes__etat mono';
        champ.parentElement.appendChild(etatSpan);
      }
      etatSpan.textContent = correct ? 'juste' : `faux — attendu : ${champ.dataset.attendu}`;

      enregistrerVerdict(`${planche.id}#${champ.dataset.pastilleN}`, correct ? 'su' : 'rate');
    }
    planche.dataset.mode = 'legende';
    const boutonVerifier = planche.querySelector(':scope > button.action');
    if (boutonVerifier) boutonVerifier.hidden = true;
    // Marqueur reutilise par la seance pour distinguer une planche reellement
    // verifiee d'une planche seulement affichee puis passee.
    planche.dataset.verifie = 'oui';
  }

  // --- Muscles a completer ------------------------------------------------------
  //
  // Meme grammaire que la planche muette, ligne par ligne : la verite attendue
  // vient du DOM (le texte deja rendu par outils/construire.py dans
  // .muscle__valeur), jamais de cours.json. La table clonee en seance est en mode
  // "champs" : valeurs masquees (style.css §5.8a), un champ par colonne.

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
  // pas un bouton distinct par ligne. Comme pour la planche, la correction se
  // montre APRES la tentative : ce qu'on attendait, sous chaque erreur.
  function verifierMuscles(table, boutonVerifier) {
    for (const ligne of table.querySelectorAll(':scope > tbody > tr')) {
      const champs = Array.from(ligne.querySelectorAll('.muscle__champ input'));
      if (!champs.length) continue;
      let toutCorrect = true;
      for (const champ of champs) {
        const correct = verifierPastille({ t: champ.dataset.attendu }, champ.value);
        champ.dataset.verdict = correct ? 'bon' : 'mauvais';
        champ.readOnly = true;
        const etatSpan = champ.parentElement.querySelector('.muscle__etat');
        if (etatSpan) {
          etatSpan.textContent = correct ? 'juste' : `faux — attendu : ${champ.dataset.attendu}`;
        }
        if (!correct) toutCorrect = false;
      }
      const id = ligne.dataset.id;
      if (id) enregistrerVerdict(id, toutCorrect ? 'su' : 'rate');
      ligne.dataset.verifie = 'oui';
    }
    if (boutonVerifier) boutonVerifier.hidden = true;
  }

  // Construit les champs, force le mode "champs" et pose le bouton Verifier --
  // applique par la seance a la table clonee (une seule ligne : voir
  // elementPourItem plus bas).
  function activerPresentationMuscles(table) {
    construireChampsMuscles(table);
    table.dataset.mode = 'champs';

    const boutonVerifier = document.createElement('button');
    boutonVerifier.type = 'button';
    boutonVerifier.className = 'action';
    boutonVerifier.textContent = 'Vérifier';
    boutonVerifier.addEventListener('click', () => verifierMuscles(table, boutonVerifier));
    table.after(boutonVerifier);
    return boutonVerifier;
  }

  // --- Progression (accueil) --------------------------------------------------

  // Un chapitre pas commence doit se voir vide, pas gris-neutre (spec §4.1) :
  // data-etat="vide" (pose par defaut au build) distingue "aucun item touche"
  // de "items touches, 0 % su", que le seul pourcentage confondrait. L'anneau
  // est celui de la ligne du chapitre (son numero est au centre).
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
      const etatTexte = touche ? `${part} % su` : 'pas commencé';
      li.dataset.etat = touche ? 'touche' : 'vide';
      if (anneau) {
        anneau.style.setProperty('--part', String(part));
        // Sans cette ligne, un lecteur d'ecran annoncait toujours "pas
        // commence" (valeur figee au build) meme apres des verdicts reels --
        // l'anneau mentait silencieusement a qui ne voit pas son remplissage.
        const titre = titresParChapitre.get(numero) || '';
        anneau.setAttribute('aria-label', `Chapitre ${numero}, ${titre} : ${etatTexte}`);
      }
      if (valeur) valeur.textContent = etatTexte;
    }
  }

  // --- Le deroule : seance du jour (accueil) et S'exercer (page de chapitre) ----
  //
  // UN seul mecanisme pour les deux. Le bloc .seance (gabarits/seance.html) a les
  // memes identifiants partout ; seul son attribut data-chapitre change ce qu'on
  // en tire : absent (accueil), la seance melange tous les chapitres dus ;
  // present (page de chapitre), composerSeance ne recoit que les items de ce
  // chapitre. Meme composition, meme deroule, memes verdicts, meme ecriture en
  // stockage -- rien n'est reecrit pour le chapitre.

  const boutonSeance = document.getElementById('seance');
  if (boutonSeance) {
    const blocSeance = boutonSeance.closest('.seance');
    const chapitreSeance = blocSeance?.dataset.chapitre ? Number(blocSeance.dataset.chapitre) : null;
    const debutSeance = boutonSeance.closest('[data-seance-debut]') || boutonSeance;
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
    // d'une question ou d'une planche. Ce chemin ne sert que sur l'accueil de
    // site/ : une page de chapitre, et l'accueil de la variante autonome, ont
    // deja leurs modeles dans un reservoir local (reservoirLocal).
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
      const page = reservoirLocal || await chargerPageChapitre(item.chapitre);
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
      // Selecteur d'attribut plutot que getElementById : `page` est tantot un
      // document (page de chapitre recuperee), tantot un element (reservoir).
      const idSource = item.type === 'pastille' ? item.id.split('#')[0] : item.id;
      const source = page.querySelector(`[id="${idSource}"]`);
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
      // Le bouton de depart revient : sur une page de chapitre, c'est pour la
      // serie suivante (les items encore dus, puis la consolidation).
      debutSeance.hidden = false;
      if (chapitreSeance !== null) boutonSeance.textContent = 'Continuer';
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
      // Un exercice long (quiz, table) laisse la page defilee : le suivant doit
      // commencer a l'ecran, pas quelque part au-dessus.
      if (zoneSeance && zoneSeance.getBoundingClientRect().top < 0) {
        zoneSeance.scrollIntoView({ block: 'start' });
      }
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
        // Sauf si l'on vient de choisir l'onglet au clavier : le focus y reste,
        // les fleches continuent de changer d'onglet.
        if (!document.activeElement?.closest?.('.onglet')) element.focus();
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
          if (messageSeance) messageSeance.textContent = '';
        }
        if (!coursDonnees) {
          if (messageSeance) messageSeance.textContent = 'Contenu indisponible pour le moment.';
          return;
        }

        // Fusion stockage + items par defaut : un item inconnu du stockage
        // demarre a "jamais", donc du immediatement (spec §4.3/§4.4).
        // Sur une page de chapitre, seuls les items de CE chapitre entrent dans
        // composerSeance : c'est tout ce qui distingue S'exercer de la seance du jour.
        const etat = stockage.lire();
        const items = itemsDuCours(coursDonnees)
          .filter((item) => chapitreSeance === null || item.chapitre === chapitreSeance)
          .map((item) => etat.items[item.id] || item);
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
        // Le depart s'efface pendant la serie : « Terminer » en est la seule sortie.
        debutSeance.hidden = true;
        if (zoneSeance) zoneSeance.hidden = false;
        await afficherEtapeCourante();
        if (chapitreSeance === null) zoneSeance?.scrollIntoView({ block: 'start' });
      } finally {
        enTransition = false;
      }
    }

    boutonSeance.addEventListener('click', () => { demarrerSeance(); });
    // Page de chapitre : ouvrir S'exercer, c'est deja commencer.
    surPremiereOuvertureExercer = () => { demarrerSeance(); };
  }

  // Onglet d'ouverture : la fiche, sauf si l'on arrive par un lien « S'exercer »
  // (#exercer). Apres le bloc ci-dessus : l'ouverture de S'exercer lance la serie,
  // dont le hook vient d'etre pose.
  if (boutonsOnglet.length) {
    const demande = window.location.hash === '#exercer'
      && boutonsOnglet.some((b) => b.dataset.onglet === 'exercer');
    // Sur la fiche a l'ouverture, l'adresse est laissee telle quelle : une ancre
    // (#fiche-s12, un lien du plan) doit survivre a un rechargement.
    activerOnglet(demande ? 'exercer' : 'fiche', { majUrl: false });
    if (demande) window.scrollTo(0, 0);
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
        // Espace ne retourne la carte que s'il y a une carte a l'ecran : sur la
        // fiche, il garde son sens natif (faire defiler la page), et sur un
        // bouton ou un lien il l'active.
        if (!exerciceAffiche() || evenement.target.closest?.('button, a, summary')) break;
        if (!(carteActive || carteParDefaut())) break;
        evenement.preventDefault();
        basculerCarteCourante();
        break;
      case '1':
        if (exerciceAffiche()) appliquerVerdictCourant('rate');
        break;
      case '2':
        if (exerciceAffiche()) appliquerVerdictCourant('difficile');
        break;
      case '3':
        if (exerciceAffiche()) appliquerVerdictCourant('su');
        break;
      case 'ArrowLeft':
      case 'ArrowRight':
        // Fleches : d'un onglet a l'autre, quand un onglet a le focus (schema
        // habituel des onglets) -- pas partout, elles servent aussi a lire.
        if (evenement.target.closest?.('.onglet')) {
          evenement.preventDefault();
          ongletVoisin(evenement.key === 'ArrowLeft' ? -1 : 1);
        }
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
