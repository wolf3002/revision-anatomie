# Vérification exhaustive — chapitre 5, Le tronc

**Date :** 2026-09-30 · **Portée :** les 85 entrées (23 cartes, 12 questions, 4 pièges, 27 sections, 6 muscles, 13 pastilles)
**Source :** `ANATOMIE _230831_213333.pdf`, slides 136 à 189, les 54 lues une par une en rendu image —
y compris les 9 sans texte extractible, toutes déchiffrées.

## Décompte

| | |
|---|---|
| Entrées vérifiées | **85 / 85** |
| Exactes | 75 (60 sans réserve, 15 avec) |
| Renvois de slide à corriger | 8 (5 faux, 3 incomplets) |
| **Erreurs de fond** | **2** |
| Ajouts vrais mais non sourcés | 11 |

## La table musculaire est parfaite

**18 colonnes sur 18 exactes, 6 renvois de slide sur 6 justes, aucun terme ajouté.** Carré des
lombes, ilio-psoas, transverse, oblique interne, oblique externe, droit de l'abdomen : origine,
terminaison et action correspondent au cours mot pour mot.

**Aucune inversion de l'orientation des fibres**, contrôlée aux quinze endroits où elle apparaît :
transversale, en éventail vers le haut, oblique vers le bas, verticale. Le sens de rotation —
oblique interne du côté contracté, oblique externe du côté opposé — est juste partout, y compris
dans le dessin de la planche.

C'était le risque principal du chapitre. Il est écarté.

Les chiffres du rachis sont conformes (7-12-5, 5 sacrées, 4 coccygiennes, 23 disques, épaisseurs
3/5/9 mm), les courbures et déformations aussi, le mécanisme de la hernie aussi.

## Les deux erreurs de fond

**`q5-08`** — l'explication invente « les 24 interlignes du rachis mobile » et le calcul se
contredit lui-même. Pire, le distracteur « entre l'atlas et l'axis » est **anatomiquement correct**
lui aussi : il n'y a pas davantage de disque à ce niveau. Quelqu'un qui connaît vraiment
l'anatomie sera piégé par la bonne réponse.

**Piège sur l'ilio-psoas** — affirme que terminaison et action « concernent spécifiquement le
grand psoas, pas le faisceau iliaque ». **C'est faux et absent du cours.** La slide 180 attribue
les deux à l'ilio-psoas entier. Seule l'*origine* listée est celle du grand psoas.

## Huit renvois à corriger

Cinq pastilles citent une slide qui ne porte pas leur libellé : « corps vertébral » et « canal
rachidien » sont nommés en 145, pas en 147 ; les orientations de fibres sont en 186, 187 et 188,
pas toutes en 185.

**Cause structurelle** : le champ `slide` d'une planche n'accepte qu'un seul entier, alors que
certaines planches synthétisent plusieurs slides. Il faudrait un champ à valeurs multiples.

## Erreurs du cours — à ne PAS corriger

- **Les côtes.** Le cours dit « vraies côtes 1 à 10 ». La nomenclature standard est : vraies 1 à 7,
  fausses 8 à 10, flottantes 11 et 12. Le site suit le cours, ce qui est correct pour l'examen —
  mais le piège devrait signaler l'écart au lieu de le minimiser.
- **Les disques.** « 23 sauf entre l'occiput et l'atlas » : le nombre est juste, l'exception est
  incomplète (il n'y a pas non plus de disque entre atlas et axis).
- **Origine et terminaison inversées** pour le carré des lombes et le droit de l'abdomen par
  rapport aux manuels de référence. La convention du cours n'est pas homogène d'un muscle à
  l'autre : à apprendre telle quelle.

## Verdict

**Apte sur les muscles, l'orientation des fibres et les chiffres du rachis dès maintenant.**
À corriger avant livraison : les deux erreurs de fond, les huit renvois, et le biais de position
des réponses (10 bonnes réponses sur 12 en position A dans ce chapitre).
