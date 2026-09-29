# Site de révision — UC1 Anatomie

**Date :** 2026-09-18
**Statut :** design validé, prêt pour le plan d'implémentation
**Source unique de vérité :** `ANATOMIE _230831_213333.pdf` (328 slides, cours UC1 — ADJ Robichon)

---

## 1. Objectif

Produire un site statique qui permette à **une personne tierce** (un ami de Valentin) de réviser
le cours UC1 Anatomie et de réussir son évaluation théorique.

Le site est publié sur GitHub Pages depuis un dépôt privé et transmis par lien.
Sept fiches PDF imprimables sont générées à partir des mêmes données.

### Ce que le site n'est pas

Ce n'est pas un résumé illustré du cours. Le résumé, le surlignage et la relecture sont classés
« faible utilité » par la synthèse de référence du domaine (Dunlosky et al., 2013). Construire un
joli condensé à relire produirait une sensation de maîtrise sans la maîtrise.

---

## 2. Utilisateur et contraintes

| | |
|---|---|
| **Utilisateur** | Un ami de Valentin, prépare l'évaluation théorique UC1 |
| **Appareils** | Téléphone en priorité, ordinateur en secours |
| **Réseau** | Connexion requise (site hébergé) ; aucune dépendance réseau au-delà du chargement initial |
| **Compte** | Aucun. Pas de serveur, pas de base, pas d'authentification |
| **Confidentialité** | Dépôt privé, site en `noindex`, URL non listée. Le site reste accessible à qui connaît l'URL — limite assumée et signalée à Valentin |
| **Langue** | Français, terminologie exacte du cours |

---

## 3. Fondements pédagogiques

Chaque règle de conception ci-dessous découle d'un résultat publié. Les sources sont citées pour
que les choix soient contestables, pas pour décorer.

### 3.1 Se tester avant de lire

**Résultat.** Sur dix techniques évaluées, deux seulement obtiennent la mention « haute utilité » :
la pratique du test et la pratique distribuée. Le résumé, le surlignage, la relecture, le mot-clé
mnémonique et l'imagerie mentale obtiennent « faible utilité » (Dunlosky et al., 2013,
*Psychological Science in the Public Interest*).

**Règle de conception.** Rien ne s'affiche avant d'avoir été cherché. Le contenu du cours existe
dans le site, mais replié derrière un onglet dédié, jamais comme écran d'accueil d'un chapitre.

### 3.2 Les visuels, oui — mais pas pour la raison qu'on croit

**Résultat.** L'appariement de l'enseignement au « style d'apprentissage » supposé d'un élève
(visuel, auditif, kinesthésique) n'a pas de support empirique : quatre méta-analyses donnent un
effet moyen d'environ d = 0,04 (Pashler, McDaniel, Rohrer & Bjork ; méta-analyse 2024,
*Frontiers in Psychology*). En revanche, en anatomie précisément, la capacité spatiale influence
réellement la performance (essai randomisé, *Anatomical Sciences Education* / PMC10185657, 2023).

**Règle de conception.** On ne produit pas « une version imagée du texte » au motif que
l'utilisateur se dit visuel. On produit un schéma **là où l'information est spatiale** (os,
insertions, plans, axes, trajets) et du texte **là où elle est verbale** (définitions, listes,
classifications). Un schéma qui ne porte aucune information spatiale est supprimé.

### 3.3 Produire la légende, pas la contempler

**Résultat.** Le rappel actif améliore la rétention à long terme en anatomie, y compris sur des
tâches de légendage (étude quasi-expérimentale, *Medical Science Educator*, PMC8368804).

**Règle de conception.** Toute planche possède un **mode muet** : les noms disparaissent, il reste
des pastilles numérotées à remplir. Le mode légendé sert à la vérification, après tentative.

### 3.4 Espacer, sans sur-construire

**Résultat.** L'intervalle optimal entre deux révisions vaut environ 10 à 20 % du délai qui sépare
l'apprentissage du test, pour des délais de quelques semaines (Cepeda, Vul, Rohrer, Wixted &
Pashler, 2008, *Psychological Science*). Les intervalles croissants ne surpassent pas de manière
significative les intervalles fixes.

**Règle de conception.** Le site demande **une seule information à la première ouverture : la date
de l'examen**, et en déduit un intervalle fixe d'environ 15 % du délai restant. Pas de courbe
d'oubli simulée, pas d'algorithme SM-2 : le gain marginal ne justifie pas la complexité.

### 3.5 Des QCM à distracteurs proches

**Résultat.** Un QCM n'enclenche de récupération utile que si ses mauvaises réponses sont
plausibles et concurrentes : le bénéfice vient de l'effort fourni pour établir pourquoi les autres
options sont fausses (Little, Bjork, Bjork & Angello, 2012, *Psychological Science*).

**Règle de conception.** Chaque distracteur est une confusion réellement attestée dans le cours
(terme voisin, muscle antagoniste, plan voisin). Les distracteurs de remplissage sont interdits.
Chaque question porte une explication et un renvoi au numéro de slide.

### 3.6 Mélanger les sujets

**Résultat.** La pratique entrelacée fait partie des techniques à utilité modérée retenues par
Dunlosky et al. ; réviser un chapitre entier d'affilée gonfle la performance en séance et la
dégrade au test différé.

**Règle de conception.** La séance du jour pioche dans **tous** les chapitres dus et alterne les
formats. L'accès libre par chapitre reste disponible — l'utilisateur garde la main, mais le
réglage par défaut est le bon.

### 3.7 Charge cognitive

**Résultat.** Principes de signalisation, de cohérence, de contiguïté spatiale et de segmentation
(Mayer, *Cognitive Theory of Multimedia Learning*).

**Règles de conception.**
- **Contiguïté** : l'étiquette est collée à l'objet qu'elle nomme, jamais renvoyée à une légende
  numérotée en bas de page.
- **Cohérence** : aucune illustration décorative, aucun aplat de couleur sans fonction.
- **Segmentation** : une seule tâche visible à l'écran pendant les cartes et le quiz.
- **Signalisation** : la couleur encode le plan anatomique du mouvement (voir §5.2).

---

## 4. Architecture fonctionnelle

### 4.1 Accueil

Trois blocs, dans cet ordre :

1. **La séance du jour.** Bouton unique. L'appli compose une séance d'environ 20 minutes
   (≈ 25 items) en piochant dans les chapitres dus, mélangeant cartes, QCM et planches muettes.
   Si rien n'est dû, elle propose une séance de consolidation sur les items les plus fragiles.
2. **La progression.** Sept anneaux, un par chapitre, remplis selon la proportion d'items marqués
   « su » lors du dernier passage. Un chapitre jamais ouvert est visiblement vide, pas gris-neutre.
3. **Les sept chapitres.** Accès direct, pour bachoter un point précis.

Un réglage discret permet de changer la date d'examen et de réinitialiser la progression.

### 4.2 Page chapitre

En-tête de planche : numéro du chapitre, titre, plage de slides source.
Puis cinq onglets.

| Onglet | Contenu | Interaction |
|---|---|---|
| **Planche** | Schémas SVG du chapitre | Bascule légendé ↔ muet ; en mode muet, saisie libre par pastille, vérification à la demande |
| **Cartes** | Recto/verso | Retourner, puis auto-évaluation *Raté / Difficile / Su* |
| **Quiz** | QCM à distracteurs proches | Réponse → correction immédiate, explication, renvoi au slide |
| **Muscles** | Origine / Terminaison / Action | Un champ par colonne, vérification ligne par ligne |
| **Le cours** | Contenu source structuré | Replié par défaut, avec numéros de slide |

L'onglet **Muscles** n'apparaît que pour les chapitres qui contiennent des tables musculaires
(chapitres 5, 6 et 7). Les onglets ne sont pas affichés vides.

> **Révision du 2026-09-29 (remplace l'ordre et « Le cours » ci-dessus).** L'ordre d'origine
> (Planche, Cartes, Quiz, Muscles, Le cours) mettait l'exercice avant la lecture : on ne peut pas
> récupérer en mémoire ce qu'on n'y a jamais mis (§3.3 vaut pour une matière déjà rencontrée). Les
> onglets sont désormais en deux groupes : **1 Apprendre** (Fiche, Pièges : rien n'y est masqué)
> puis **2 Se tester** (Planche, Cartes, Quiz, Muscles : aucune réponse avant tentative). « Le
> cours » devient la **Fiche**, premier onglet et onglet ouvert par défaut : plan, sections, planches
> légendées à l'endroit où la notion est traitée, pièges, table musculaire en référence. L'onglet
> Planche s'ouvre **muet** (le mode légendé est dans la fiche ; la bascule reste pour vérifier après
> tentative), conformément à §3.3. Voir le README, « Parcours d'un chapitre ».

> **Révision du 2026-09-29 (simplification, remplace les deux tableaux d'onglets ci-dessus).**
> Six onglets demandaient de comprendre ce que chacun contenait avant de commencer. Il n'en
> reste que deux : **Fiche** (par défaut ; tout ce qui se lit, y compris les pièges) et
> **S'exercer** (un parcours unique, un exercice à la fois, qui mélange cartes, questions,
> planches muettes et muscles). S'exercer est la séance du jour restreinte à un chapitre
> (`composerSeance` filtré, même dérouleur, mêmes verdicts) — aucun second mécanisme.
> L'accueil se réduit à une phrase, au bouton de séance et aux sept chapitres (deux actions
> chacun : Lire la fiche, S'exercer) ; les réglages sont derrière un lien discret. Perte
> assumée : l'accès direct à un seul type d'exercice. Raccourcis : `←` `→` changent d'onglet
> quand un onglet a le focus, `M` n'existe plus (la correction d'une planche ou d'un muscle
> s'affiche après « Vérifier »). Voir le README, « Parcours d'un chapitre ».

### 4.3 Moteur de planification

État par item : `{ id, chapitre, type, derniereVue, statut, echecs }` avec
`statut ∈ { jamais, rate, difficile, su }`.

Intervalle de base `I = max(1, round(0.15 × joursAvantExamen))`, borné à 7 jours.
Date de prochaine échéance :

| Statut | Prochaine échéance |
|---|---|
| `jamais` | immédiate |
| `rate` | le jour même (repasse en fin de séance) |
| `difficile` | `derniereVue + max(1, I/2)` |
| `su` | `derniereVue + I` |

Un item échoué deux fois de suite est marqué fragile et remonte en tête de la séance suivante.
Quand la date d'examen est passée ou absente, `I = 3` jours.

### 4.4 Stockage

`localStorage`, une clé unique `uc1-anatomie-v1` contenant un objet JSON :
date d'examen, thème choisi, état de tous les items.

Écriture au fil de l'eau, lecture au chargement. Aucune donnée ne quitte l'appareil.
Un bouton **Exporter ma progression** produit un fichier JSON, et **Importer** le relit :
c'est la réponse minimale au changement d'appareil, sans serveur.

---

## 5. Système visuel et ergonomie

### 5.1 Principe directeur

Le système visuel dérive du cours lui-même : **une planche d'atlas anatomique**. Numérotation des
planches, pastilles de légende, étiquettes en caractères techniques, trait fin. Rien d'ornemental.

### 5.2 Couleur — la couleur porte une information

Le cours structure tout le mouvement humain autour de trois plans. Ces trois plans deviennent les
trois couleurs du site, et **elles ne servent qu'à ça** : partout où un mouvement est nommé, il est
teinté du plan dans lequel il s'effectue. Un apprenant qui voit « abduction » toujours en rouille
finit par savoir sans effort qu'elle est frontale.

```
Plan frontal       #C1553A   (rouille)    abduction, adduction, inclinaison latérale
Plan sagittal      #1F6F78   (bleu-vert)  flexion, extension, antépulsion, rétropulsion…
Plan transversal   #B0821F   (ocre)       rotations, pronation, supination
```

Neutres, thème clair : papier `#EDEFF2`, carte `#FFFFFF`, encre `#101A22`,
encre douce `#4A5A66`, trait `#C9D2D9`.
Neutres, thème sombre : papier `#0E1418`, carte `#161F25`, encre `#E6EDF2`,
encre douce `#97A7B2`, trait `#2A3841`. Les trois teintes sont éclaircies en conséquence
(`#E07A5F`, `#3FA3AD`, `#DCA83A`).

Contrainte vérifiée à la construction : contraste ≥ 4,5:1 pour tout texte, ≥ 3:1 pour les traits
porteurs de sens. La couleur ne code jamais seule : un mouvement porte aussi son libellé de plan.

### 5.3 Typographie

Trois rôles, trois familles (Google Fonts, avec pile de repli système) :

- **Saira Condensed** — numéros et titres de planche. Condensé, technique, registre signalétique.
- **Public Sans** — corps, questions, interface. Institutionnel, très lisible, sobre.
- **IBM Plex Mono** — étiquettes de schéma, numéros de pastille, renvois « slide 212 ».

Échelle : 13 / 15 / 17 / 21 / 28 / 44 px. Interlignage 1,55 pour le corps, 1,1 pour les titres.
Longueur de ligne plafonnée à 68 caractères.

### 5.4 Grille et densité

Mobile d'abord. Une colonne sous 720 px, deux au-delà (rail de navigation + contenu).
Pendant une carte ou une question de quiz, **une seule tâche est visible** : pas de barre latérale,
pas de contenu suivant en amorce.

Les actions principales (*Retourner*, *Raté / Difficile / Su*, *Valider*) sont ancrées en bas
d'écran sur mobile, dans la zone atteignable au pouce. Cibles tactiles ≥ 44 px.

### 5.5 Les planches SVG

Modèle de données d'une planche :

```json
{
  "id": "plans-anatomiques",
  "titre": "Les trois plans",
  "vb": "0 0 640 360",
  "dessin": "<g>…tracé SVG sans aucune étiquette…</g>",
  "pastilles": [
    { "n": 1, "x": 214, "y": 96, "t": "Plan frontal", "ancre": "start", "plan": "frontal" }
  ]
}
```

Le tracé et les étiquettes sont séparés. Le rendu produit les deux modes depuis la même source :

- **Légendé** — pastille + libellé, relié à l'objet, contiguïté respectée.
- **Muet** — pastille numérotée seule, plus un champ de saisie par numéro sous le schéma.

Un seul jeu de données, deux usages : aucune image dupliquée, aucune désynchronisation possible.

Planches prévues, une à trois par chapitre : les trois plans et les termes de localisation (ch. 1) ;
os long en coupe et squelette axial/appendiculaire (ch. 2) ; articulation synoviale type et les sept
diarthroses (ch. 3) ; enveloppes du muscle et sarcomère (ch. 4) ; colonne et courbures, vertèbre
type, orientation des fibres abdominales (ch. 5) ; squelette du membre supérieur et coiffe des
rotateurs (ch. 6) ; squelette du membre inférieur, quadriceps et ischio-jambiers (ch. 7).

### 5.6 Mouvement

Trois animations, pas une de plus : retournement de carte (180°, 220 ms), fondu des étiquettes à la
bascule muet/légendé (120 ms), remplissage de l'anneau de progression au chargement.
`prefers-reduced-motion: reduce` les supprime toutes.

### 5.7 Socle de qualité

- Responsive vérifié jusqu'à 360 px de large.
- Focus clavier visible sur tout élément interactif.
- Raccourcis : `Espace` retourne la carte, `1` `2` `3` auto-évaluent, `←` `→` naviguent,
  `M` bascule le mode muet.
- Thème clair/sombre : `prefers-color-scheme` par défaut, bascule manuelle mémorisée.
- Le contenu du cours reste lisible si JavaScript échoue : les onglets sont des sections présentes
  dans le DOM, révélées par JS, pas injectées par lui.
- Zéro requête réseau après le chargement initial.

---

## 6. Contenu

### 6.1 Périmètre

Les sept chapitres en entier.

| Ch. | Titre | Slides |
|---|---|---|
| 1 | Terminologie anatomique | 7–45 |
| 2 | Le système squelettique | 46–71 |
| 3 | Le système articulaire | 72–110 |
| 4 | Le système musculaire | 111–135 |
| 5 | Le tronc | 136–190 |
| 6 | Le membre supérieur | 191–267 |
| 7 | Le membre inférieur | 268–328 |

### 6.2 Règle de fidélité

Le PDF du cours fait foi. Aucune notion extérieure n'est ajoutée : l'évaluation porte sur **ce**
support, pas sur l'anatomie générale. Si un complément s'avère indispensable à la compréhension, il
est marqué `[hors cours]` de façon visible.

Chaque carte, question, pastille et piège porte son numéro de slide, pour que l'utilisateur puisse
vérifier sans nous croire sur parole.

Les slides purement iconographiques, dont le texte n'est pas extractible, sont recensées ; leur
contenu n'est jamais deviné.

### 6.3 Volume cible

Par chapitre : 18 à 25 cartes, 8 à 12 questions de QCM, 1 à 3 planches, 2 à 4 pièges.
Chapitres 5 à 7 : plus les tables musculaires (origine / terminaison / action), une ligne par
muscle nommé dans le cours.

### 6.4 Modèle de données

Un fichier `contenu/cours.json` :

```json
{
  "meta": { "cours": "UC1 — Anatomie", "source": "ANATOMIE _230831_213333.pdf", "slides": 328 },
  "chapitres": [{
    "num": 1,
    "titre": "Terminologie anatomique",
    "slides": [7, 45],
    "sections":  [{ "titre": "…", "points": ["…"], "slide": 12 }],
    "planches":  [ /* voir §5.5 */ ],
    "cartes":    [{ "id": "c1-04", "q": "…", "r": "…", "slide": 20, "plan": "frontal" }],
    "quiz":      [{ "id": "q1-02", "q": "…", "choix": ["…"], "bonne": 2, "expl": "…", "slide": 28 }],
    "muscles":   [{ "nom": "…", "origine": ["…"], "terminaison": ["…"], "actions": ["…"], "slide": 240 }],
    "pieges":    [{ "titre": "…", "texte": "…", "slide": 33 }]
  }]
}
```

---

## 7. Architecture technique

Site statique, sans framework, sans étape de compilation côté client.

```
revision-anatomie/
├── contenu/cours.json          source unique de vérité
├── outils/
│   ├── construire.py           cours.json  ->  pages HTML + assets
│   ├── planches.py             tracés SVG (Python -> fragments injectés)
│   ├── fiches.py               cours.json  ->  HTML imprimable
│   └── pdf.py                  HTML imprimable -> PDF (Chrome headless)
├── gabarits/                   gabarits HTML (accueil, chapitre, fiche)
├── site/                       SORTIE — c'est ce qui est publié
│   ├── index.html
│   ├── chapitre-1.html … chapitre-7.html
│   ├── assets/{style.css, app.js, cours.json}
│   ├── pdf/fiche-01.pdf … fiche-07.pdf
│   └── .nojekyll
├── docs/superpowers/specs/     spécifications (non publiées)
└── README.md
```

**Séparation des responsabilités.** `planches.py` ne connaît que la géométrie. `construire.py` ne
connaît que le rendu HTML. `fiches.py` et `pdf.py` ne servent que l'impression. Aucun des quatre ne
contient de contenu de cours : tout vit dans `cours.json`.

**Côté client**, quatre modules ES séparés (`planificateur.js`, `stockage.js`, `exercices.js`,
`interface.js`) pour la testabilité : les fonctions pures du planificateur deviennent testables
sous Node sans navigateur, et chaque fichier reste court. Responsabilités :
`planificateur` (calcul des échéances, §4.3, fonctions pures), `stockage` (localStorage, import/export),
`exercices` (cartes, quiz, planches muettes, tables musculaires), `interface` (onglets, thème,
raccourcis). Le planificateur ne touche pas au DOM ; l'interface ne calcule pas d'échéance.

---

## 8. Fiches PDF

Sept fiches, une par chapitre, générées depuis `cours.json` :
planche muette, puis questions, puis tables musculaires à compléter — **et le corrigé en fin de
document**, jamais en regard. Format A4, imprimable en noir et blanc sans perte d'information
(les trois plans sont alors distingués par libellé, pas par teinte seule).

Génération : `google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf`.

---

## 9. Déploiement

Dépôt **privé** sur le compte GitHub `wolf3002`.
Sources sur `main`. Le contenu de `site/` est publié sur la branche `gh-pages`
(`git subtree push --prefix site origin gh-pages`), et GitHub Pages sert cette branche.

Chaque page porte `<meta name="robots" content="noindex, nofollow">`.
Un `robots.txt` interdit l'indexation.

Aucun commit et aucune publication ne sont effectués sans demande explicite de Valentin.

---

## 10. Hors périmètre

Comptes utilisateurs, serveur, base de données, synchronisation entre appareils, modèles 3D,
audio, mode multijoueur, statistiques avancées, application native, algorithme SM-2.

---

## 11. Limites assumées

1. **La progression est liée au navigateur.** Changement d'appareil ou vidage du cache = repartir de
   zéro, sauf export/import manuel du fichier JSON.
2. **Le lien reste devinable.** GitHub Pages ne propose pas de contrôle d'accès hors offre
   Enterprise. Un dépôt privé ne rend pas le site privé.
3. **Le contenu est plafonné par la source.** De nombreuses slides sont des images sans texte
   extractible ; ce qui n'est pas lisible n'est pas transcrit, et c'est signalé plutôt que comblé.
4. **La date d'examen est saisie par l'utilisateur.** Sans elle, le planificateur retombe sur un
   intervalle fixe de 3 jours, correct mais non optimisé.

---

## 12. Critères de recette

- [ ] Toute affirmation du site renvoie à un numéro de slide vérifiable.
- [ ] Aucun contenu extérieur au cours n'est présent sans marquage `[hors cours]`.
- [ ] Un chapitre ouvert pour la première fois ne montre aucune réponse avant une tentative.
- [ ] Chaque distracteur de QCM correspond à une confusion réellement présente dans le cours.
- [ ] Chaque planche fonctionne dans les deux modes depuis une seule définition de données.
- [ ] Contraste AA vérifié sur les deux thèmes.
- [ ] Utilisable à 360 px de large, actions principales atteignables au pouce.
- [ ] `prefers-reduced-motion` supprime toutes les animations.
- [ ] Le cours reste lisible avec JavaScript désactivé.
- [ ] Une séance du jour complète tient en 20 minutes environ.
- [ ] Les sept PDF s'impriment en noir et blanc sans perte d'information.

---

## Sources

- Dunlosky, Rawson, Marsh, Nathan & Willingham (2013). *Improving Students' Learning With Effective
  Learning Techniques.* Psychological Science in the Public Interest, 14(1), 4–58.
- Pashler, McDaniel, Rohrer & Bjork (2008), et méta-analyse 2024, *Frontiers in Psychology* —
  hypothèse d'appariement aux styles d'apprentissage.
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008). *Spacing Effects in Learning: A Temporal Ridgeline
  of Optimal Retention.* Psychological Science, 19(11).
- Little, Bjork, Bjork & Angello (2012). *Multiple-Choice Tests Exonerated, at Least of Some
  Charges.* Psychological Science, 23(11).
- Retrieval Practice for Improving Long-Term Retention in Anatomical Education.
  Medical Science Educator (PMC8368804).
- Spatial ability and 3D model colour-coding affect anatomy performance (PMC10185657, 2023).
- Mayer, R. *Cognitive Theory of Multimedia Learning* — signalisation, cohérence, contiguïté,
  segmentation.
