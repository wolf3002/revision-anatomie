# SDD ledger — plan: docs/superpowers/plans/2026-09-18-socle-technique-et-chapitre-1.md

Branche: construction (merge-base main = a63379d)
Commits locaux autorisés, push interdit.

Task 1: implémenté (commit 34f7336, 10 tests verts)
Task 1: revue — spec ✅ ; qualité approuvée avec 1 Important : valider_planche ne contrôle jamais le slide, alors que la contrainte globale l'exige. Conflit plan-contre-plan (contrainte vs code fourni) ; tranché par le contrôleur en faveur de la contrainte globale. Plan corrigé : signature valider_planche(planche, bornes=None), et une pastille hérite du slide de sa planche.
Task 1: fix round 1/5 en cours — implémenteur ab584e3 relancé
Task 1: fix round 1/5 (1 addressed, 0 open ; commits 34f7336..7029404)
Task 1: complete (commits a63379d..7029404, review clean, 13 tests)
Task 2: implémenté (commit 0d4450b, 19 tests verts) — 25 cartes, 12 QCM, 6 pièges
Task 2: ATTENTION TRANSVERSE — les numéros de slide du brief étaient faux (10/15). Vérifié par le contrôleur : exact. Les briefs des chapitres 2 à 7 ne doivent PAS porter de numéros de slide devinés ; l'implémenteur doit les relever dans le PDF.
Task 2: fix round 1/5 (1 addressed, 0 open ; commits 0d4450b..7af8f09) — contrôle négatif fourni, test discriminant
Task 2: complete (commits 7029404..7af8f09, review clean, 19 tests)
Task 2: minor (deferred): ruff E402 sur tests/*.py (import après sys.path.insert) — aucun lint configuré dans le dépôt
Task 3: fix round 1/5 — refonte plans-anatomiques en 3 panneaux (commit 9a052b1) ; contrôle visuel contrôleur : mode muet lisible, test d'acceptation passé
Task 3: fix round 2/5 — ancrage middle + champ indice (commit e4b9ac6)
Task 3: fix round 3/5 — DECALAGE_LIBELLE source unique dans schema.py + contrôle de débordement (commit 921cc23)
Task 3: complete (commits 7af8f09..921cc23, review clean, 28 tests) — slides 15 et 37 vérifiées indépendamment sur le PDF
Task 3: minor (deferred): duplication entre _panel_frontal et _panel_transversal dans outils/planches.py
Task 3: fix round 4/5 — éclatement en plan-frontal/sagittal/transversal pour le responsive (commit 66af118) ; vérifié par le contrôleur à 320 et 1280 px
Task 4: implémenté (commit 523312b, 33 tests) — style.css 1107 lignes ; revue de tâche PAS ENCORE dispatchée, à faire
AUDIT chapitre 1 : 56 entrées vérifiées une par une contre le PDF (slides rendues en image). 0 critique, 0 important, 0 manque examinable. Verdict : apte.
AUDIT — À CORRIGER : les bornes du chapitre 1 sont déclarées [7,45] mais le contenu s'arrête slide 43 (44 = sommaire, 45 = début du chapitre 2). Slide max réellement citée : 42. Corriger en [7,43].
AUDIT — LEÇON TRANSVERSE : les bornes de chapitre doivent être relevées dans le PDF, pas héritées du comptage automatique. Vaut pour les chapitres 2 à 7.

=== TEST MANUEL EN NAVIGATEUR (26/09) ===
CONSTAT 1 : /tmp/demo.html est PERIMEE — elle contient encore viewBox="0 0 720 360",
  l'ancienne planche unique, ecrite 12 min avant le decoupage (commit 66af118).
  Le « aucun defaut » du script portait donc sur un artefact obsolete. Aucune vraie
  page n'a jamais ete controlee, puisqu'aucune n'existe.
CONSTAT 2 (defaut reel) : style.css n'a AUCUN conteneur de grille pour plusieurs planches.
  Les .planche sont stylees une par une ; rien ne les aligne cote a cote. Avec le decoupage
  en 3 planches, le rendu desktop les empilera au lieu de les aligner — on perd la
  comparaison des trois plans validee plus tot.
  A corriger en tache 5 : envelopper les planches dans un conteneur .planches en grille.
CONSTAT 3 (a reexaminer) : .planche { overflow-x: auto } sous 719px. Avec des planches de
  240px il devient inutile ET dangereux : il ferait passer silencieusement une planche trop
  large en la rendant defilante, au lieu de la signaler.
VERIFIE OK : barre d'actions a 320px — 4 boutons 70x44, aucun texte tronque, rappels de
  raccourci masques. Le correctif du bouton tient.
Task 5: implémenté — générateur HTML (gabarits/base.html, gabarits/chapitre.html,
  outils/construire.py), 8 tests neufs (52/52 au total). Corrigé CONSTAT 2 (.planches en grille
  auto-fit minmax(210px,1fr)) et CONSTAT 3 (overflow-x:auto sous 719px retiré, pas restreint : il
  aurait masqué un vrai débordement de ~31px sur la planche termes-localisation à 320px).
  verifier_mobile.py sur la vraie page (chapitre-1.html) : aucun défaut aux 8 largeurs — premier
  contrôle du projet sur une page réelle, pas une démo. Revue visuelle (390/1280/320px) OK.
  Fix collatéral : sys.path.insert ajouté dans construire.py pour que `python3
  outils/construire.py` (exécution directe documentée) résolve l'import contenu.schema.
  Réserve signalée (non corrigée, hors périmètre) : le rendu 'muscles' du générateur produit des
  <tr> nus sans <table> englobante — sans effet sur le chapitre 1 (muscles vide), à surveiller
  aux chapitres 5-7.
Task 5: implémenté (commit c78833a) ; revue : spec ✅, 3 Important + 1 test non discriminant
Task 5: fix round 1/5 (4 addressed ; commit 36a2ad9) — 56 tests Python, contrôleur 8 largeurs OK
Task 5: PARKED — pas de renvoi de slide par ligne de muscle. L'implémenteur a préféré préserver la
  bascule CSS mobile (nth-of-type 1..3) plutôt qu'ajouter un 4e <td>. Or la contrainte globale de
  traçabilité exige qu'une table musculaire porte son slide. À TRANCHER avant les chapitres 5-7 :
  soit le slide va dans la <caption> ou un attribut data-, soit le CSS s'adapte.
Task 6: complete (commit e60647f, 12 tests JS) — intervalles et entrelacement vérifiés par le contrôleur
Task 7: complete (commit 9591f2f, 8 tests JS)
Task 8: complete (commit 8a04277, 8 tests JS) — 28 tests JS au total
Task 5: fix round 1 re-revue — 4/4 ADDRESSED, tests discriminants confirmés
Task 9: implémenté (commit 0907f4b) — PILOTAGE RÉEL PAR LE CONTRÔLEUR (navigateur, serveur local) :
  onglets OK, carte retournée au clic et à Espace, verdict 1/2/3 écrit et persistant après rechargement,
  flèches OK, M bascule les 4 planches, quiz corrigé (mauvais/bon + explication révélée),
  tolérance aux accents CONFIRMÉE : "cranial" accepté pour "Crânial", "CAUDAL" pour "Caudal".
  10 items mémorisés en fin de parcours. Aucune réponse visible à l'ouverture (25/25 cachées).
Task 9: complete (commit 0907f4b) — interface pilotée et vérifiée par le contrôleur
Task 10: implémenté (commit 65065c2) — 3 bugs trouvés par pilotage réel (réponse révélée d'emblée,
  séance dégénérée en 25 cartes d'affilée sans mélange de formats, race condition sur le message de fin)
Task 10: fix round 1/5 (3 addressed ; commit 6f70ed6) — règle de mélange DESCENDUE dans planificateur.js
  avec test discriminant ; liens habillés ; titre rendu exact. Entrelacement vérifié par le contrôleur :
  carte quiz pastille carte quiz pastille
Task 10: écart assumé — pas de teinte d'accent d'interface ajoutée : les 3 couleurs du site restent
  réservées aux plans anatomiques. Décision de l'implémenteur, motivée, que je valide.
Task 10: fix round 2/5 (2 addressed ; commit 3ef2816) — compteur honnête (révisés/passés), Suivant rendu
  discret, aria-label de l'anneau mis à jour. Scénario de triche : "0 révisé, 21 passés", stockage vide.
Task 10: complete (commits 65065c2..3ef2816)
Task 11: complete (commit 03dab86) — recette adversariale + README. 12/12 QCM tiennent.
Task 11: DIFFÉRÉ — séance estimée 13-14 min contre 20 visées. Calibrage fait pour 7 chapitres, mesuré
  sur 1/7. À revalider avec les chapitres 2-7, idéalement par chronométrage humain.
Task 11: minor (deferred) — comptage révisé/passé non couvert par un test automatisé (pilotage seul) ;
  numéro "Pl. 01" recalculé dans la séance ; pas de confirmation avant d'écraser une pastille remplie.

=== REVUE FINALE DE BRANCHE (25 commits) ===
CRITICAL 1 : onglet Muscles = table statique, AUCUNE mécanique de rappel actif, expose toutes les
  réponses. Invisible aujourd'hui (chapitre 1 sans muscles) mais BLOQUANT avant les chapitres 5-7.
  => chantier de socle à mener dans le plan 2, pas un détail de contenu.
CRITICAL 2 : les 6 pièges n'étaient rendus NULLE PART. Contrat rompu entre cours.json (produit),
  schema.py (valide) et construire.py (ne consomme pas). Erreur de conception du plan, invisible
  pour toute revue tâche par tâche. CORRIGÉ commit 38fe10d.
IMPORTANT 3 : slide manquant sur les lignes de muscle. CORRIGÉ (dans le <th>, pas une 4e colonne,
  pour ne pas casser le nth-of-type de la bascule mobile).
IMPORTANT 4 : un item "raté" ne repasse pas en fin de la séance EN COURS (seulement au jour suivant).
  La spec §4.3 l'annonce pourtant. Non corrigé — à traiter dans la prochaine itération du planificateur.
IMPORTANT 5 : le rendu réel d'une table musculaire n'a jamais traversé verifier_mobile.py.
  À faire sur un mini-chapitre de test avec de vrais noms longs avant d'attaquer le chapitre 5.
DÉCISION : les pièges ne sont PAS des items de séance (itemsDuCours ne les inclut pas). Un piège est
  une mise en garde à lire, pas un exercice à tenter — l'exclure de la séance est volontaire.
