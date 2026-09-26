# UC1 — Anatomie : site de révision

Site statique pour réviser le cours d'anatomie (UC1, ADJ Robichon) avant l'évaluation
théorique. Cartes de rappel actif, QCM à distracteurs proches, planches muettes à
légender, et une séance du jour composée automatiquement par un planificateur
d'espacement (répétition espacée, ~15 % du délai restant avant l'examen, cf.
Cepeda et al. 2008).

Un seul chapitre est construit à ce jour : **Chapitre 1 — Terminologie anatomique**
(slides 7–45). Les chapitres 2 à 7 (squelettique, articulaire, musculaire, tronc,
membre supérieur, membre inférieur) suivront le même gabarit une fois celui-ci validé.

## Règle de fidélité au PDF source

Le PDF du cours (`ANATOMIE _230831_213333.pdf`, 328 slides — non versionné dans ce
dépôt) fait foi. Aucune notion extérieure n'est ajoutée : l'évaluation porte sur ce
support, pas sur l'anatomie générale. Un complément jugé indispensable à la
compréhension serait marqué `[hors cours]` de façon visible — à ce jour, aucun n'a
été nécessaire dans le chapitre 1.

Chaque carte, question de QCM, pastille de planche et piège porte son numéro de
slide (`contenu/cours.json`), pour pouvoir vérifier sans avoir à croire le site sur
parole. Les slides purement iconographiques, dont le texte n'est pas extractible,
sont recensées ; leur contenu n'est jamais deviné.

## Où vivent la spec et les plans

- **Spec de conception** : `docs/superpowers/specs/2026-09-18-site-revision-anatomie-design.md`
  — pédagogie visée, structure des données, règles de fidélité, charte visuelle.
- **Plan d'implémentation** : `docs/superpowers/plans/2026-09-18-socle-technique-et-chapitre-1.md`
  — découpage en tâches du socle technique et du chapitre 1.
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

Régénère `site/index.html` et `site/chapitre-N.html` à partir des gabarits
(`gabarits/`) et de `contenu/cours.json`. Le résultat est versionné dans `site/`
(pas de build côté serveur : GitHub Pages sert des fichiers statiques déjà
générés).

Contrôle de mise en page mobile (8 largeurs, avec Chrome piloté par Playwright) :

```bash
python3 outils/verifier_mobile.py site/index.html site/chapitre-1.html
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

Le déploiement (branche `gh-pages`, `robots.txt`) fait l'objet d'un plan séparé et
n'est pas encore en place. Point à garder à l'esprit pour ce moment-là :

**Un dépôt GitHub privé ne rend pas le site publié privé.** GitHub Pages sert le
contenu d'une branche sur une URL publique dès que l'option est activée, quelle
que soit la visibilité du dépôt source — un dépôt privé peut très bien alimenter
une page publique accessible à qui a l'URL. La seule protection réelle, en l'absence
d'authentification, est que l'URL ne soit **pas indexée et pas diffusée** :
`robots.txt` + `<meta name="robots" content="noindex, nofollow">` (déjà posé dans
`gabarits/base.html`) dissuadent les moteurs de recherche, mais n'empêchent
personne connaissant l'URL exacte d'y accéder. Ne pas publier ce lien
publiquement (réseaux sociaux, dépôts publics, etc.) si le contenu doit rester
entre les mains de son seul destinataire.
