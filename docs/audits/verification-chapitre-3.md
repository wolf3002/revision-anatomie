# Vérification exhaustive — chapitre 3, Le système articulaire

**Date :** 2026-09-30 · **Portée :** les 87 entrées (27 cartes, 11 questions, 4 pièges, 17 sections, 28 pastilles)
**Source :** `ANATOMIE _230831_213333.pdf`, slides 72 à 109, les 38 lues une par une en rendu image.
Positions des flèches vérifiées **par calcul** sur les équations des chemins SVG, pas à l'œil.

## Décompte

| | |
|---|---|
| Entrées vérifiées | **87 / 87** |
| Exactes | 77 (dont 12 avec réserve mineure) |
| Renvois de slide à corriger | 4 entrées, 2 causes |
| **Erreurs de fond** | **7** (1 importante, 6 mineures) |
| Notions inventées majeures | 0 (6 ajouts mineurs) |

**Le cœur du chapitre est juste.** Les 7 types de diarthroses — forme, axes, mouvements,
exemples — les 3 familles et les 5 catégories de structures sont fidèles. Les dessins des 7
diarthroses sont distincts et corrects : aucune confusion sphéroïde/ellipsoïde ni
ginglyme/trochoïde.

## L'erreur importante : une pastille contredit le cours

**Planche de l'articulation synoviale, pastille « Ligament ».** Notre indice dit « hors de la
capsule, relie les deux os », et un commentaire du code affirme « le ligament n'est PAS à
l'intérieur de la capsule ».

**Le cours dit le contraire.** La slide 104 distingue explicitement les ligaments
**intracapsulaires** (croisés du genou) des **extracapsulaires** (latéraux), et la slide 100
montre le ligament articulaire *à l'intérieur* de la capsule.

Quelqu'un qui apprend cette planche retiendra que tout ligament est extracapsulaire — ce qui
contredit deux autres entrées du même chapitre, justes celles-là.

Deux défauts s'ajoutent sur la même pastille : la flèche part de la capsule, pas du ligament, et
la slide citée (102) ne montre aucun ligament.

## L'exemple de l'ellipsoïde existe — on avait conclu le contraire

Un audit précédent avait relevé que le cours ne donne pas d'exemple pour l'articulation
ellipsoïde, et l'agent avait eu raison de ne pas en inventer. **Mais la conclusion était fausse.**

La légende de la figure, slide 84 : « Articulation ellipsoïdale entre l'extrémité distale du
radius, le scaphoïde et le semi-lunaire du carpe (**le poignet**) ».

C'est du texte **dans l'image**, invisible à l'extraction — exactement le piège qu'on avait
identifié. À ajouter, en citant la légende, sans employer le terme « radio-carpienne » que le
cours n'utilise pas ici.

## Renvois à corriger

**L'exemple de la sphéroïde (la hanche) est en slide 82, pas 81.** La slide 81 ne porte que la
forme et les trois axes. Touche trois entrées, dont une carte qui demande explicitement l'exemple.

## Six ajouts mineurs non sourcés

« Quasi plane » pour la bicondylienne (le cours dit « paire de condyles plane ») · « usure ou
inflammation » et « luxation congénitale » · un lien de cause à effet entre cavité et mobilité ·
« lubrifie mal » et l'explication de l'échauffement par la fluidité de la synovie · l'opposition
maintien/protection d'un piège, alors que le cours range la membrane fibreuse dans les deux ·
« coin » de fibrocartilage au lieu d'« anneau ».

## Lacunes de couverture

- **Les 5 catégories de structures n'apparaissent jamais en liste.** Les sections existent, mais
  aucune carte ne demande de les citer. Le cours range le cartilage et la synovie dans deux
  catégories chacun — rien sur le site ne le dit.
- **Aucune carte ne compare les 3 familles** côte à côte (mobilité / cartilage / cavité /
  exemple), ni ne demande de citer les 7 types.
- **Slide 100 jamais citée** : c'est elle qui porte « bourse séreuse » et le ligament intracapsulaire.
- La slide 109 n'est que partiellement exploitée.

## Incohérences du cours — à ne PAS corriger

Le titre de la slide 92 dit « LA BICONDYLAIRE » alors que le plan dit « bicondyliennes ». La
slide 109 porte une coquille (« CARTILACE »). Le ménisque est décrit comme un « anneau », ce qui
est une simplification. **Aucune erreur anatomique franche dans le cours pour ce chapitre** — les
sept défauts relevés sont tous dans notre contenu.

## Verdict

**Apte sous réserve.** Fidélité à 88 %.

À corriger avant diffusion : le ligament, l'exemple de la hanche (slide 82), l'exemple de
l'ellipsoïde, « quasi plane ». Puis les quatre questions et pièges. Puis ajouter la carte des
5 catégories et celle des 3 familles.

Quatre commentaires de `outils/planches.py` sont factuellement faux et doivent être corrigés
en même temps (lignes 481, 491-493, 868-869, 880-882).
