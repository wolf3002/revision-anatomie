# UC1 — Anatomie : site de révision

Site statique pour réviser le cours d'anatomie (UC1, ADJ Robichon) avant l'évaluation
théorique. Cartes de rappel actif, QCM à distracteurs proches, planches muettes à
légender, tables musculaires à compléter, et une séance du jour composée
automatiquement par un planificateur d'espacement (répétition espacée, ~15 % du
délai restant avant l'examen, cf. Cepeda et al. 2008).

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

## Parcours d'un chapitre : lire d'abord, se tester ensuite

Le site repose sur le rappel actif (se tester plutôt que relire), juste pour une
matière **déjà rencontrée** : on ne retrouve pas ce qu'on n'a jamais lu. Une page de
chapitre s'ouvre donc sur la lecture, et les exercices viennent après. Deux groupes
d'onglets numérotés, dans cet ordre :

| Groupe | Onglets | Règle |
|---|---|---|
| **1 Apprendre** | Fiche · Pièges | Rien n'est masqué. La fiche est le cours à lire : plan, sections et points, planches **légendées** à l'endroit où la notion est traitée, pièges de la notion, et (ch. 5 à 7) la table musculaire en valeurs lisibles. |
| **2 Se tester** | Planche · Cartes · Quiz · Muscles | « Aucune réponse avant tentative » : verso masqué, explication après réponse, planche **muette** à l'ouverture, muscles à compléter. |

La séance du jour (accueil) est le troisième temps : elle fait revenir, espacés dans le
temps, les items déjà vus. Une ligne en tête de la page d'accueil et de chaque chapitre
le dit.

La fiche ne repose sur aucune donnée de plus dans `cours.json` : planches et pièges
sont rattachés à la dernière section dont le slide ne les dépasse pas
(`outils/construire.py`, `_section_pour`). Elle ne partage avec les onglets de test ni
classe ni identifiant qu'`interface.js` équipe (`.planche-fiche` et `.table-ref`, pas
`.planche` et `.muscles`) : c'est ce qui la garde en lecture seule et évite que la
séance du jour ne clone la fiche à la place d'un exercice. `tests/test_fiche_lecture.py`
et `tests/test_parcours_navigateur.py` verrouillent ces deux points.

Sans JavaScript (ou si le script ne s'exécute pas, ex. `site/` ouvert en `file://`), tous
les volets se suivent et la barre d'onglets est inerte : chaque volet porte alors un titre
(« Se tester · Cartes »), et Pièges, Planche et Muscles, qui ne feraient que répéter la
fiche, sont retirés (`style.css` §5.2a ; `interface.js` pose la classe `js` sur `<html>`
dès qu'il tourne). Fiche, Cartes et Quiz restent lisibles, chacun à un seul endroit.

La variante autonome (`site-autonome/`, `outils/empaqueter.py`) ne cherche pas les pages de
chapitre par `fetch` : la séance clone des modèles cachés (`#reservoir-seance`).
`interface.js` ne les équipe donc jamais au chargement (`horsReservoir`) : seul le clone,
au moment de son insertion en séance, reçoit champs, boutons et écouteurs.
`tests/test_autonome_navigateur.py` le pilote en `file://`.

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
sur les huit pages :

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
