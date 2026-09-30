# Vérification exhaustive — chapitre 1, Terminologie anatomique

**Date :** 2026-09-30 · **Portée :** les 64 entrées (25 cartes, 12 questions, 6 pièges, 9 sections, 12 pastilles)
**Source :** `ANATOMIE _230831_213333.pdf`, slides 7 à 43, les 37 lues une par une en rendu image.

> **Ce rapport contredit `audit-chapitre-1.md`**, qui concluait « aucun défaut, verdict apte ».
> Sept erreurs réelles sont ici démontrées. Le premier audit avait examiné les mêmes entrées ;
> il n'avait pas confronté les entrées **entre elles**, ni simulé la notation du mode muet.

## Décompte

| | |
|---|---|
| Entrées vérifiées | **64 / 64** |
| Exactes | 56 (39 sans réserve, 17 avec) |
| Renvois de slide faux | 3 (+ 7 partiels) |
| **Erreurs de fond** | **7** |
| Notions ajoutées non marquées | 2 substantielles, 5 mineures |

**Aucune carte ni section n'énonce un fait anatomique faux.** Les 25 cartes et les 9 sections
reprennent le cours sans l'altérer. Les sept défauts sont ailleurs.

## Le défaut le plus coûteux : le site punit la bonne réponse

**Pastilles « mouvements » des plans frontal et sagittal.** L'indice affiché est « mouvements de
ce plan », et le libellé attendu est « Abduction, adduction ».

Or le cours donne **trois** mouvements au plan frontal (abduction, adduction, **inclinaison
latérale** — slide 18) et **quatre couples** au plan sagittal (slide 23).

La vérification compare par égalité exacte après normalisation. Conséquence : quelqu'un qui
répond « abduction, adduction, inclinaison latérale » — c'est-à-dire **complètement et
correctement** — est noté **faux**. Il doit aussi retaper la virgule au bon endroit.

Pire, la position de ces pastilles est à ~200 unités de la flèche qu'elles sont censées
désigner : elles pointent sous les pieds du personnage.

## Deux entrées qui se contredisent — et le site tranche contre lui-même

Le **piège sur la flexion plantaire** affirme que « le mot flexion désigne le mouvement vers la
plante, pas la fermeture d'un angle ». Cette glose est **absente du cours**.

Le **distracteur D de `q1-06`** dit exactement la même chose — et le site le corrige comme
**faux**, en expliquant qu'il « redéfinit le mot flexion, ce que le cours ne fait pas ».

Quelqu'un qui a lu le piège coche D et se fait sanctionner par le site qui le lui a enseigné.

## Deux QCM dont la bonne réponse est contestable

**`q1-04`** — « par rapport à quel repère le cours définit-il l'abduction et l'adduction ? ». Le
distracteur « axe de la main ou du pied » est noté faux. Mais **la figure de la slide 13 porte
elle-même les libellés « abduction / adduction » autour de l'axe de M2**. L'explication affirme le
contraire de ce que montre la slide qu'elle cite.

**`q1-09`** — « supérieure » est noté faux pour l'extrémité de l'humérus. Or le cours dit lui-même
« on utilise également supérieur et inférieur », et l'énoncé ne précise pas « selon le cours ».

Dans les deux cas, **c'est l'élève qui connaît le mieux le cours qui est pénalisé.**

## Deux défauts de contenu

**Piège crânial/proximal** — « les deux couples disent vers le haut et vers le bas » est inexact :
proximal/distal se définissent par la distance au tronc, jamais par la hauteur. Le piège se
contredit d'ailleurs à la phrase suivante.

**Planche des termes de localisation** — la flèche « caudal » est dessinée le long de la jambe,
alors que le cours dit « extrémité inférieure **du tronc** ». Elle occupe la même région que
« distal », ce qui rend les deux indiscernables en mode muet — d'autant qu'aucune pastille de
cette planche ne porte d'indice.

## Trois renvois faux, sept partiels

Les pastilles « mouvements » des trois plans citent la slide 15, qui ne porte que les **noms** des
plans. Les mouvements sont en 18, 23 et 31.

Sept autres entrées citent une slide qui ne porte qu'une partie de leur contenu — limite
structurelle : le champ `slide` n'accepte qu'un entier, jamais une plage.

## Erreurs du cours — à ne PAS corriger

« Processus **xyphoïde** » (graphie standard : xiphoïde) · antépulsion définie par
« ouverture/fermeture bras-tronc » là où la définition usuelle est directionnelle · « pronation et
supination ne désignent **que** des mouvements du radius », alors qu'elles s'emploient aussi pour
le pied · l'accentuation incohérente du support, déjà signalée par un piège.

## Lacunes de couverture

Les trois axes de la slide 15 (vertical, sagittal, transversal) n'ont ni carte ni question.
L'exemple du gastrocnémien (slide 43) n'est repris nulle part. La figure de l'abduction des
orteils (slide 13) non plus.

## Verdict

**Apte sous réserve.** Le cœur est fidèle ; ce sont les pièges, deux QCM et trois pastilles qui
posent problème — et dans quatre cas sur sept, le défaut **pénalise l'élève qui sait**.

À corriger : la contradiction piège/QCM, les deux QCM à distracteur défendable, les libellés de
pastille et leur notation, le piège crânial/proximal, la flèche caudale, les trois renvois.
