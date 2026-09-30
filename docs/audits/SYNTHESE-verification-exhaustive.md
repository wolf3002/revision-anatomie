# Synthèse — vérification exhaustive des 602 entrées

**Date :** 2026-09-30
**Méthode :** sept auditeurs indépendants, un par chapitre, chacun sur la **totalité** de son
chapitre. Les 328 slides du PDF ont été **rendues en image et lues une par une** — l'extraction de
texte manque les légendes de figures, ce qui a déjà causé deux erreurs de conclusion.

## Résultat global

| Ch. | Entrées | Erreurs de fond |
|---|---|---|
| 1 — Terminologie | 64 | 7 |
| 2 — Squelettique | 68 | 6 |
| 3 — Articulaire | 87 | 7 |
| 4 — Musculaire | 62 | 2 |
| 5 — Tronc | 85 | 2 |
| 6 — Membre supérieur | 117 | 2 |
| 7 — Membre inférieur | 119 | 4 |
| **Total** | **602** | **30** |

**Taux de fidélité : 95 %.**

## Ce qui est sûr

**Les 34 tables musculaires sont parfaites.** Chapitre 5 (6 muscles), chapitre 6 (11), chapitre 7
(17) : origine, terminaison, action et renvoi de slide contrôlés colonne par colonne. **Zéro
défaut sur plus de 130 contrôles.** C'est le contenu le plus dense et le plus interrogeable.

Aucune inversion sur les trois pièges classiques : l'orientation des fibres abdominales, les
terminaisons des ischio-jambiers, la composition de la coiffe des rotateurs.

Les chiffres sont exacts partout — 206 os, 21 = 8 + 13, 24 vertèbres = 7 + 12 + 5, 27 os de la
main, 26 du pied, 23 disques.

## Les défauts, par nature

### 1. Le biais de position des QCM — le plus coûteux

| Ch. | A | B | C | D |
|---|---|---|---|---|
| 1 | 3 | 3 | 4 | 2 |
| 2 | 3 | 6 | 2 | 0 |
| 3 | **8** | 3 | 0 | 0 |
| 4 | 2 | 6 | 4 | 0 |
| 5 | **10** | 1 | 1 | 0 |
| 6 | **12** | 0 | 0 | 0 |
| 7 | **12** | 0 | 0 | 0 |
| **Tot** | **50** | 19 | 11 | 2 |

Cocher A sans rien lire donne **61 %** de bonnes réponses (25 % attendus au hasard), et **100 %
sur les chapitres 6 et 7**. Le générateur ne mélange jamais l'ordre des choix.

Ce n'est pas qu'une question de triche : le cerveau repère le motif sans intention, et l'on
répond juste **sans récupérer l'information en mémoire** — ce qui annule le bénéfice du QCM tout
en donnant l'illusion de savoir.

### 2. Le site punit celui qui sait (4 cas)

- **Pastilles « mouvements » des plans** — attendent « Abduction, adduction » alors que le cours
  en donne trois (avec l'inclinaison latérale). Une réponse **complète et correcte** est notée
  fausse.
- **Piège contre QCM, chapitre 1** — le piège enseigne une glose ; le QCM propose exactement
  cette phrase comme distracteur et la corrige comme fausse.
- **`q1-04`** — nie que le cours définisse l'abduction par rapport à l'axe du pied, alors que **la
  figure de la slide citée porte ce libellé**.
- **`q1-09`** — corrige « supérieure » comme faux, quand le cours dit « on utilise également
  supérieur et inférieur ».

### 3. Des corrections silencieuses du cours (2 cas)

- **Chapitre 4, myofibrille.** La slide 119 dit « la cellule musculaire s'appelle myofibrille »,
  ce qui est faux, et les slides 117 et 120 du même cours disent l'inverse. Notre section
  **réécrit** la phrase en version correcte tout en gardant le renvoi « slide 119 », et le piège
  ne montre que la moitié du conflit. Si l'examinateur reprend sa slide, l'élève répond « fibre »
  et perd des points **en ayant raison**.
- **Chapitre 3, ligament.** Une pastille enseigne que le ligament est « hors de la capsule », alors
  que le cours distingue explicitement intracapsulaires et extracapsulaires.

### 4. Des affirmations fausses présentées comme du cours (4 cas)

- **Chapitre 6** — la radio-ulnaire proximale décrite comme « formée par l'olécrane et l'incisure
  trochléaire » : c'est l'incisure **radiale**.
- **Chapitre 6** — « **seule** la radio-ulnaire proximale permet la prono-supination » : la distale
  y participe aussi.
- **Chapitre 7** — « l'acétabulum **et le foramen obturé** sont à la jonction des 3 parties ».
- **Chapitre 7** — les ischio-jambiers « partagent la même origine et les mêmes actions ».

### 5. Un raisonnement invalide répété (chapitre 7)

Sept entrées expliquent une action par « un muscle agit sur les articulations qu'il franchit ».
Le cours ne l'énonce jamais. Trois s'en servent pour déduire le **sens** de l'action — invalide :
les ischio-jambiers franchissent la hanche et l'**étendent**, le droit fémoral la fléchit.

### 6. Renvois de slide (~35) et ajouts non sourcés (~40)

Répartis sur les sept chapitres, détaillés dans chaque rapport. Cause structurelle récurrente : le
champ `slide` n'accepte **qu'un seul entier**, alors que beaucoup d'entrées sont à cheval sur deux
ou trois slides. Un champ à valeurs multiples réglerait une vingtaine de cas d'un coup.

## Deux audits précédents contredits

`audit-chapitre-1.md` concluait « aucun défaut ». Sept erreurs y sont démontrées.
`audit-chapitres-2-a-7.md` affirmait « aucune notion inventée » et « aucun distracteur
éliminable ». Les deux sont faux.

**Ce n'est pas une question de sérieux mais de méthode.** Ces audits vérifiaient chaque entrée
*contre le cours*. Celui-ci vérifie en plus les entrées **entre elles**, et simule ce que le site
répond quand on saisit une réponse. Les incohérences internes et les règles de notation ne se
voient pas autrement.

## Erreurs du cours — à ne PAS corriger

Le contenu les reproduit fidèlement, et c'est volontaire : l'examen porte sur ce support.

21 os de la tête là où l'anatomie en compte 22 · « vraies côtes 1 à 10 » au lieu de 1 à 7 · la
moelle jaune présentée comme remplaçant l'os spongieux · « tubérosité radiale » pour « tête
radiale » · « processus xyphoïde » · origine et terminaison inversées pour deux muscles du tronc ·
« la cellule musculaire s'appelle myofibrille ».

**Les signaler est utile ; les corriger ferait perdre des points.**

## Verdict

**Apte sous réserve.** 95 % du contenu est fidèle, et la partie la plus interrogeable — les
tables musculaires — est irréprochable.

Priorité de correction :
1. Le biais de position des QCM (affecte tout le site).
2. Les quatre cas où le site punit la bonne réponse.
3. Les deux corrections silencieuses du cours.
4. Les quatre affirmations fausses.
5. Le raisonnement « franchit ».
6. Les renvois de slide et les ajouts non sourcés.
