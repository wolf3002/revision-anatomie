# Audit de fidélité et de couverture — chapitre 1

**Date :** 2026-09-26
**Portée :** `contenu/cours.json` (chapitre 1) et `outils/planches.py`
**Source de référence :** `ANATOMIE _230831_213333.pdf`, slides 7 à 45
**Méthode :** les slides étant des images PowerPoint sans texte extractible fiable, les 39 pages
ont été rendues en image et lues une par une, puis confrontées entrée par entrée au contenu.

## 1. Exactitude — 56 entrées vérifiées, aucun défaut

25 cartes (`c1-01` à `c1-25`), 12 questions (`q1-01` à `q1-12`), 6 pièges, 9 sections et
4 planches, toutes contrôlées individuellement. Chaque citation, chaque numéro de slide et
chaque exemple correspond au support : abduction d'épaule, adduction de hanche, flexion du
poignet, extension de hanche, antéversion « dos creux », rétroversion « dos plat », tibia
médial / fibula latéral, sternum et ses trois parties, épiphyses de l'humérus, peau et muscle.

**Le numéro de slide cité est le bon dans les 43 entrées qui en portent un.**

Le piège 6 (accentuation variable de « médial / latéral / crânial ») a été vérifié jusqu'au
détail typographique : les slides 31 et 33 écrivent bien « LATERALE » et « MEDIALE » sans
accent, les slides 32, 38 et 40 les accentuent.

### Imprécision structurelle, non factuelle
Trois sections — « Le plan frontal » (slide 17), « Le plan sagittal » (22), « Le plan
transversal » (30) — agrègent sous un seul numéro d'ancrage du contenu réparti sur trois à
cinq slides. Chaque sous-point reste exact, et la carte correspondante porte de toute façon
son propre numéro. À savoir si l'on cherche une correspondance stricte « une section = une
slide ».

## 2. Couverture — aucun manque examinable

Tout le contenu enseignable des slides 9 à 42 est repris : position anatomique, axes, les
trois plans avec leurs mouvements et leurs articulations, circumduction, les cinq couples de
termes de localisation.

### Découpage à corriger pour la suite
**Les slides 44 et 45 n'appartiennent pas au chapitre 1.** La slide 44 est un sommaire
général avec le chapitre 2 surligné, la slide 45 est la première du chapitre 2 (« Le système
squelettique »). Le contenu réel de « Terminologie anatomique » s'arrête **slide 43**.

Le découpage `[7, 45]` vient du plan, pas du contenu : aucune entrée ne pointe vers 44 ou 45,
donc rien de faux n'a été produit. Mais la leçon vaut pour les six chapitres suivants — les
bornes doivent être relevées dans le PDF, pas héritées d'un comptage automatique.

### Observation mineure
Le nommage des trois axes (vertical, sagittal, transversal — slide 15) figure en section mais
n'est interrogé par aucune carte ni aucun QCM dédié.

## 3. Anatomie — aucune erreur

Aucune affirmation anatomiquement fausse, ni dans le cours ni dans le contenu produit. Les
points sensibles ont été contrôlés spécifiquement : flexion plantaire = extension du pied ;
pronation = le radius croise l'ulna ; tibia médial, fibula latérale ; antéversion = dos creux.
Tous conformes à la nomenclature française standard et cohérents entre eux.

## 4. Qualité des QCM — 12 sur 12 valides

Chaque question a une réponse unique et défendable ; aucun distracteur injuste.

Deux cas demandent une lecture attentive mais restent corrects, parce que le cours les tranche
lui-même : `q1-09` (proximal contre supérieur, pour l'humérus) et `q1-11` (ventral contre
antérieur, pour le sternum). Le cours précise « essentiellement le tronc » et « plus spécifique
pour le tronc », ce qui lève l'ambiguïté.

## 5. Planches — conventions respectées

Les quatre planches vérifiées coordonnée par coordonnée : proximal vers le tronc et distal
loin de lui, médial vers le plan médian et latéral à l'opposé, crânial vers la tête et caudal
vers les pieds. Les libellés attendus en mode muet emploient l'orthographe de référence du
cours.

## 6. Verdict d'aptitude

**Apte.** Quelqu'un qui maîtrise parfaitement ce contenu est prêt pour une évaluation portant
sur les slides 7 à 43.

Défauts critiques : 0. Défauts importants : 0. Manques de couverture examinables : 0.
