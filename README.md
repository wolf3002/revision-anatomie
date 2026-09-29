# UC1 — Anatomie : site de révision

Site statique pour réviser le cours d'anatomie (UC1, ADJ Robichon) avant l'évaluation
théorique : la fiche de chaque chapitre à lire, puis des exercices (cartes de rappel
actif, QCM à distracteurs proches, planches muettes à légender, tables musculaires à
compléter) et une séance du jour composée automatiquement par un planificateur
d'espacement (répétition espacée, ~15 % du délai restant avant l'examen, cf. Cepeda et
al. 2008).

## Contenu

Les **sept chapitres** du cours sont construits :

| Ch. | Titre | Slides |
|---|---|---|
| 1 | Terminologie anatomique | 7–43 |
| 2 | Le système squelettique | 45–70 |
| 3 | Le système articulaire | 72–109 |
| 4 | Le système musculaire | 111–134 |
| 5 | Le tronc | 136–189 |
| 6 | Le membre supérieur | 191–266 |
| 7 | Le membre inférieur | 268–328 |

Volumes réels (`contenu/cours.json`) : **403 items planifiables** — 172 cartes,
81 questions de QCM, 116 pastilles de planche réparties sur 28 planches, et
**34 muscles** (origine/terminaison/action) sur les chapitres 5 à 7 — plus 30 pièges
(mises en garde, hors séance). Le détail par chapitre est dans
`docs/superpowers/plans/2026-09-26-chapitres-2-a-7.md` et les rapports de tâche
correspondants.

## Parcours d'un chapitre : lire d'abord, s'exercer ensuite

Le site repose sur le rappel actif (se tester plutôt que relire), juste pour une
matière **déjà rencontrée** : on ne retrouve pas ce qu'on n'a jamais lu. Une page de
chapitre s'ouvre donc sur la lecture, et les exercices viennent après. Deux onglets,
pas un de plus — on n'a pas à deviner ce que contient chacun ni par où commencer :

| Onglet | Contenu | Règle |
|---|---|---|
| **Fiche** (par défaut) | Tout ce qui se lit, d'un seul tenant : le plan, les sections et leurs points, les planches **légendées** et les pièges à l'endroit où la notion est traitée, et (ch. 5 à 7) la table musculaire en valeurs lisibles. Un lien de fin de fiche mène aux exercices. | Rien n'est masqué. |
| **S'exercer** | Un parcours unique, **un exercice à la fois** : cartes, questions, planches muettes et muscles mélangés. Ouvrir l'onglet suffit : la série démarre. | « Aucune réponse avant tentative » : verso masqué, explication et corrections après la réponse, planche **muette**, muscles à compléter. |

Ce qu'on a perdu, en connaissance de cause : l'accès direct à un seul type d'exercice
(les quatre onglets Planche / Cartes / Quiz / Muscles, l'onglet Pièges). Travailler un
format d'affilée est moins efficace que les mélanger ; le gain de clarté vaut cette
perte. La correction d'une planche ou d'un muscle, qu'on allait chercher avec un bouton
de bascule, s'affiche désormais d'elle-même **après** « Vérifier » (libellés du tracé,
« faux — attendu : … »), champs figés.

**S'exercer réutilise la séance du jour, il n'en réécrit rien.** Le bloc
`gabarits/seance.html` a les mêmes identifiants sur l'accueil et sur chaque page de
chapitre ; `interface.js` le câble une seule fois. Seul l'attribut `data-chapitre` change
ce qu'on en tire : `composerSeance` ne reçoit alors que les items de ce chapitre (mêmes
échéances, même entrelacement des formats, mêmes verdicts, même écriture en stockage,
mêmes anneaux de progression). Les modèles d'exercice sont dans un réservoir caché
(`#reservoir-exercices`) placé **après** la zone d'exercice, que le script clone un à un
(`[data-reservoir]`, `outils/construire.py`, `_rendre_reservoir_exercices`).

La séance du jour (accueil) est le troisième temps : elle fait revenir, espacés dans le
temps, les items déjà vus.

L'accueil tient en une phrase (« Lis la fiche d'un chapitre, puis exerce-toi. »), le
bouton de la séance du jour, et les chapitres : chacun a deux actions explicites
(**Lire la fiche**, **S'exercer**). La date d'examen reste visible tant qu'elle n'est pas
renseignée (elle commande l'espacement) ; ensuite, comme le thème, l'export, l'import et
la réinitialisation, elle vit derrière un seul lien discret, « Réglages ». Une page de
chapitre n'a pas de réglages : on y lit. La progression n'est plus un bloc à part de sept
anneaux : chaque ligne de chapitre porte un petit anneau dont le centre est le numéro du
chapitre, et une indication en toutes lettres (« 12 % su », « pas commencé »).

La fiche ne repose sur aucune donnée de plus dans `cours.json` : planches et pièges
sont rattachés à la dernière section dont le slide ne les dépasse pas
(`outils/construire.py`, `_section_pour`). Elle ne partage avec les exercices ni
classe ni identifiant qu'`interface.js` équipe (`.planche-fiche` et `.table-ref`, pas
`.planche` et `.muscles`) : c'est ce qui la garde en lecture seule et évite que la
séance ne clone la fiche à la place d'un exercice. `tests/test_fiche_lecture.py`
et `tests/test_parcours_navigateur.py` verrouillent ces deux points.

Sans JavaScript (ou si le script ne s'exécute pas, ex. `site/` ouvert en `file://`), la
**fiche se lit telle quelle**, entière et sans rien de masqué. Les exercices ont besoin du
script (révéler, corriger, mémoriser) : leur onglet, la barre d'onglets et les liens qui y
mènent sont retirés, et une ligne le dit (`style.css` §5.2a ; `interface.js` pose la classe
`js` sur `<html>` dès qu'il tourne).

La variante autonome (`site-autonome/`, `outils/empaqueter.py`) n'a pas de serveur : la
page d'un chapitre porte déjà ses modèles, et l'accueil (séance du jour) un réservoir de
tous les chapitres (`#reservoir-seance`). Aucune page n'est récupérée par `fetch`.
`interface.js` n'équipe jamais un modèle du réservoir : seul le clone, au moment de son
insertion, reçoit champs, boutons et écouteurs. `tests/test_autonome_navigateur.py` le
pilote en `file://`.

**Lecture.** La fiche est le contenu le plus long : une colonne centrée de 46 rem à toutes
les largeurs (plus de rail latéral), une ligne bornée à ~70 caractères, des points en
liste à puce carrée avec retrait suspendu, des titres de section à 24 px avec de l'air
entre les sections, et Espace y fait défiler la page (il ne retourne une carte que s'il y
en a une à l'écran).

## Règle de fidélité au PDF source

Le PDF du cours (`ANATOMIE _230831_213333.pdf`, 328 slides — non versionné dans ce
dépôt) fait foi. Aucune notion extérieure n'est ajoutée : l'évaluation porte sur ce
support, pas sur l'anatomie générale. Un complément jugé indispensable à la
compréhension serait marqué `[hors cours]` de façon visible — à ce jour, aucun n'a
été nécessaire sur les sept chapitres.

Chaque carte, question de QCM, pastille de planche, ligne de muscle et piège porte
son numéro de slide (`contenu/cours.json`), pour pouvoir vérifier sans avoir à
croire le site sur parole. Les slides purement iconographiques, dont le texte n'est
pas extractible, sont recensées ; leur contenu n'est jamais deviné.

## Où vivent la spec et les plans

- **Spec de conception** : `docs/superpowers/specs/2026-09-18-site-revision-anatomie-design.md`
  — pédagogie visée, structure des données, règles de fidélité, charte visuelle.
- **Plans d'implémentation** :
  `docs/superpowers/plans/2026-09-18-socle-technique-et-chapitre-1.md` (socle
  technique + chapitre 1) et `docs/superpowers/plans/2026-09-26-chapitres-2-a-7.md`
  (chapitres 2 à 7 + onglet Muscles interactif).
- **Contenu du cours** : `contenu/cours.json` (validé par `contenu/schema.py`) —
  seule source de vérité pour ce que le site affiche ; `outils/construire.py` ne
  connaît ni la géométrie des planches ni le contenu pédagogique, il assemble des
  gabarits autour de ce JSON.
- Le suivi de tâches au jour le jour (`.superpowers/sdd/…`, briefs et rapports de
  recette) est volontairement exclu du dépôt (`.gitignore`) : c'est un espace de
  travail local, pas une référence durable.

## Régénérer le site

```bash
python3 outils/construire.py
```

Régénère `site/index.html` et les sept `site/chapitre-1.html` … `chapitre-7.html`
à partir des gabarits (`gabarits/`) et de `contenu/cours.json` — un seul passage
reconstruit tout le site. Le résultat est versionné dans `site/` (pas de build
côté serveur : GitHub Pages sert des fichiers statiques déjà générés).

Contrôle de mise en page mobile (8 largeurs, avec Chrome piloté par Playwright),
sur les huit pages (sans script : la fiche et l'accueil ; les exercices, eux, sont
contrôlés de 320 à 1920 px par `tests/test_parcours_navigateur.py`) :

```bash
python3 outils/verifier_mobile.py site/index.html site/chapitre-*.html
```

## Lancer les tests

```bash
python3 -m pytest tests/ -q     # logique Python : construction, schéma, contraste, planches
node --test tests/*.test.js     # logique JS : planificateur, exercices, stockage
```

Dépendances de test (`requirements-dev.txt`, notamment Playwright pour
`verifier_mobile.py`) :

```bash
pip install -r requirements-dev.txt
python3 -m playwright install chrome   # seulement si google-chrome système absent
```

## Servir le site en local

```bash
python3 -m http.server 8781 --directory site
```

Puis ouvrir `http://127.0.0.1:8781/index.html`.

## Confidentialité et GitHub Pages

Le déploiement (branche `gh-pages`, fiches PDF imprimables) fait l'objet d'un
troisième plan et n'est pas encore en place. Point à garder à l'esprit pour ce
moment-là, à ne jamais perdre de vue :

**Un dépôt GitHub privé ne rend pas le site publié privé.** GitHub Pages sert le
contenu d'une branche sur une URL publique dès que l'option est activée, quelle
que soit la visibilité du dépôt source — un dépôt privé peut très bien alimenter
une page publique accessible à qui a l'URL. La seule protection réelle, en l'absence
d'authentification (hors offre GitHub Enterprise), est que l'URL ne soit **pas
indexée et pas diffusée** : `<meta name="robots" content="noindex, nofollow">` est
déjà posé dans `gabarits/base.html` (donc sur les huit pages générées), mais un
`robots.txt` à la racine du site publié reste à ajouter au moment du déploiement —
il ne l'est pas aujourd'hui, `site/` n'en contient pas encore. Ni l'un ni l'autre
n'empêchent quelqu'un connaissant l'URL exacte d'y accéder : ils dissuadent
seulement l'indexation par les moteurs de recherche. Ne pas publier ce lien
publiquement (réseaux sociaux, dépôts publics, etc.) si le contenu doit rester
entre les mains de son seul destinataire.
