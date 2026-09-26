# Socle technique + chapitre 1 — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire un site de révision fonctionnel de bout en bout sur le seul chapitre 1, pour valider le rendu, l'ergonomie et le moteur d'espacement avant d'écrire les six autres chapitres.

**Architecture :** Un fichier de contenu (`contenu/cours.json`) fait foi. Des scripts Python le valident et en engendrent des pages HTML statiques. Le comportement côté navigateur est découpé en modules ES : le planificateur et la logique d'exercice sont des fonctions pures sans DOM, testées sous Node ; seul `interface.js` touche au DOM.

**Tech Stack :** Python 3.14 + pytest 9.1 (validation et génération) · JavaScript ES modules + `node --test` (logique client) · HTML/CSS sans framework · aucune dépendance installée par paquet.

## Global Constraints

- **Source unique de vérité :** `ANATOMIE _230831_213333.pdf`. Aucune notion extérieure au cours sans marquage `[hors cours]` visible.
- **Traçabilité :** toute carte, question, planche, table musculaire et piège porte un numéro de slide, situé dans la plage du chapitre. Une pastille hérite du numéro de sa planche — on ne lui en demande pas un à elle.
- **Chapitre 1 = slides 7 à 45.**
- **Palette (thème clair) :** papier `#EDEFF2`, carte `#FFFFFF`, encre `#101A22`, encre douce `#4A5A66`, trait `#C9D2D9`, frontal `#C1553A`, sagittal `#1F6F78`, transversal `#B0821F`.
- **Palette (thème sombre) :** papier `#0E1418`, carte `#161F25`, encre `#E6EDF2`, encre douce `#97A7B2`, trait `#2A3841`, frontal `#E07A5F`, sagittal `#3FA3AD`, transversal `#DCA83A`.
- **Typographie :** Saira Condensed (titres de planche) · Public Sans (corps) · IBM Plex Mono (étiquettes, numéros de slide). Pile de repli système obligatoire pour chacune.
- **Contraste :** ≥ 4,5:1 pour le texte, ≥ 3:1 pour les traits porteurs de sens, sur les deux thèmes.
- **Le site s'adapte à tous les écrans, et c'est vérifié, pas supposé.** La cible principale est un
  téléphone, mais aucune largeur ne doit casser. Contrainte : **aucun débordement horizontal de la page**
  entre 320 et 1920 px, et tout contenu intrinsèquement large (planche, tableau de muscles, bloc de code)
  défile dans son propre conteneur, jamais en poussant la page.

  Une planche trop large ne se met pas à l'échelle jusqu'à devenir illisible : elle **se décompose en
  planches autonomes**, que la grille empile en une colonne sur téléphone et aligne côte à côte sur grand
  écran. Chaque planche doit rester lisible seule.

  Vérifié automatiquement par `outils/verifier_mobile.py`, qui rend chaque page dans Chrome sans interface
  aux largeurs **320, 360, 390, 414, 768, 1024, 1280 et 1920 px** et échoue si
  `document.documentElement.scrollWidth > window.innerWidth` à l'une d'elles, ou si un élément dépasse du
  cadre de son parent. Le contrôle fait partie de la recette, il ne se juge pas à l'œil.
- **Ancrage des libelles de pastille :** `ancre` vaut `start`, `end` ou `middle`, et rien d'autre. Le validateur refuse toute autre valeur. La table `DECALAGE_LIBELLE = {"start": (14, 4), "end": (-14, 4), "middle": (0, 24)}` est definie dans `contenu/schema.py` et importee par `outils/construire.py` : une seule definition, pour que ce qui est valide soit exactement ce qui est rendu. Le validateur s'en sert pour refuser un libelle dont le point d'ancrage decale sort du `viewBox`.
- **Indice de saisie :** une pastille peut porter un champ optionnel `indice` (ex. `"nom du plan"`, `"mouvements"`), affiche en texte d'invite du champ en mode muet. Sans lui, une pastille muette ne dit pas ce qu'elle attend.
- **La couleur ne code jamais seule :** tout mouvement teinté porte aussi son libellé de plan en toutes lettres.
- **Aucune requête réseau après le chargement initial**, hors les fontes Google chargées dans `<head>`.
- **Le contenu du cours reste lisible sans JavaScript :** les onglets sont des sections présentes dans le DOM, révélées par JS, jamais injectées par lui.
- **Commits :** la règle de Valentin interdit tout commit non demandé. Les étapes « Commit » de ce plan ne s'exécutent que s'il a donné une autorisation explicite ; une autorisation globale en début d'exécution vaut pour tout le plan. Sans autorisation, sauter ces étapes et continuer.
- **Écart assumé par rapport à la spec §7 :** la spec annonçait « quatre modules dans un seul fichier `app.js` ». Le plan les sépare en quatre fichiers ES (`planificateur.js`, `stockage.js`, `exercices.js`, `interface.js`). Motif : les fonctions pures deviennent testables sous Node sans navigateur, et chaque fichier reste sous 200 lignes. Mettre la spec à jour à la tâche 6.

---

## Structure des fichiers

| Fichier | Responsabilité |
|---|---|
| `contenu/cours.json` | Tout le contenu du cours. Aucun code. |
| `contenu/schema.py` | Valide `cours.json`. Ne génère rien. |
| `outils/planches.py` | Géométrie SVG uniquement : tracés et positions de pastilles. Ne connaît ni HTML ni contenu textuel du cours. |
| `outils/construire.py` | `cours.json` → pages HTML. Ne connaît pas la géométrie. |
| `gabarits/base.html` | Enveloppe commune : `<head>`, thème, pied de page. |
| `gabarits/chapitre.html` | Corps d'une page chapitre et ses onglets. |
| `gabarits/accueil.html` | Corps de l'accueil. |
| `site/assets/style.css` | Système visuel complet. |
| `site/assets/planificateur.js` | Calcul d'échéances et composition de séance. Fonctions pures, zéro DOM. |
| `site/assets/stockage.js` | Lecture/écriture `localStorage`, export/import JSON. |
| `site/assets/exercices.js` | Logique de carte, de quiz et de planche muette. Fonctions pures. |
| `site/assets/interface.js` | Tout le DOM : onglets, thème, raccourcis, rendu. |
| `site/assets/app.js` | Point d'entrée : assemble les quatre modules. |
| `tests/test_schema.py` | Tests du validateur. |
| `tests/test_planches.py` | Tests de la géométrie. |
| `tests/test_construire.py` | Tests du générateur HTML. |
| `tests/test_contraste.py` | Vérifie la palette contre WCAG. |
| `tests/planificateur.test.js` | Tests du planificateur. |
| `tests/stockage.test.js` | Tests du stockage. |
| `tests/exercices.test.js` | Tests de la logique d'exercice. |

---

### Task 1: Dépôt et validateur de contenu

**Files:**
- Create: `contenu/schema.py`
- Create: `tests/test_schema.py`
- Create: `.gitignore`

**Interfaces:**
- Consumes: rien.
- Produces: `valider_cours(cours: dict) -> list[str]` et `valider_planche(planche: dict, bornes: list[int] | None = None) -> list[str]` (publique : les tests de la tâche 3 l'appellent directement, sans `bornes`, pour ne valider que la géométrie ; `valider_cours` la rappelle avec les bornes du chapitre pour contrôler en plus le numéro de slide) — renvoie la liste des messages d'erreur, liste vide si le contenu est conforme. Utilisée par les tâches 2, 3 et 5.

- [ ] **Step 1: Initialiser le dépôt**

```bash
cd "/home/valentin/Téléchargements/revision-anatomie"
git init -b main
printf '__pycache__/\n*.pyc\n.pytest_cache/\nsite/pdf/\n' > .gitignore
```

`git init` ne crée aucun commit — c'est de la mise en place, pas une publication.

- [ ] **Step 2: Écrire le test qui échoue**

Créer `tests/test_schema.py` :

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contenu.schema import valider_cours


def cours_minimal(**remplacements):
    chapitre = {
        "num": 1,
        "titre": "Terminologie anatomique",
        "slides": [7, 45],
        "sections": [{"titre": "Position anatomique", "points": ["Debout"], "slide": 9}],
        "planches": [],
        "cartes": [{"id": "c1-01", "q": "Question ?", "r": "Reponse", "slide": 9}],
        "quiz": [{
            "id": "q1-01",
            "q": "Question ?",
            "choix": ["A", "B", "C"],
            "bonne": 0,
            "expl": "Parce que.",
            "slide": 9,
        }],
        "muscles": [],
        "pieges": [{"titre": "Piege", "texte": "Attention.", "slide": 9}],
    }
    chapitre.update(remplacements)
    return {"meta": {"cours": "UC1", "source": "cours.pdf", "slides": 328},
            "chapitres": [chapitre]}


def test_cours_conforme_ne_produit_aucune_erreur():
    assert valider_cours(cours_minimal()) == []


def test_slide_hors_plage_du_chapitre_est_signalee():
    cours = cours_minimal(cartes=[{"id": "c1-01", "q": "Q ?", "r": "R", "slide": 300}])
    erreurs = valider_cours(cours)
    assert any("300" in e and "c1-01" in e for e in erreurs)


def test_identifiant_duplique_est_signale():
    cours = cours_minimal(cartes=[
        {"id": "c1-01", "q": "Q1 ?", "r": "R1", "slide": 9},
        {"id": "c1-01", "q": "Q2 ?", "r": "R2", "slide": 10},
    ])
    assert any("c1-01" in e and "double" in e for e in valider_cours(cours))


def test_quiz_avec_moins_de_trois_choix_est_signale():
    cours = cours_minimal(quiz=[{
        "id": "q1-01", "q": "Q ?", "choix": ["A", "B"], "bonne": 0,
        "expl": "E", "slide": 9,
    }])
    assert any("q1-01" in e and "choix" in e for e in valider_cours(cours))


def test_bonne_reponse_hors_bornes_est_signalee():
    cours = cours_minimal(quiz=[{
        "id": "q1-01", "q": "Q ?", "choix": ["A", "B", "C"], "bonne": 5,
        "expl": "E", "slide": 9,
    }])
    assert any("q1-01" in e and "bonne" in e for e in valider_cours(cours))


def test_explication_de_quiz_vide_est_signalee():
    cours = cours_minimal(quiz=[{
        "id": "q1-01", "q": "Q ?", "choix": ["A", "B", "C"], "bonne": 0,
        "expl": "", "slide": 9,
    }])
    assert any("q1-01" in e and "explication" in e for e in valider_cours(cours))


def test_planche_contenant_du_texte_dans_le_trace_est_refusee():
    cours = cours_minimal(planches=[{
        "id": "p1", "titre": "T", "vb": "0 0 100 100",
        "dessin": "<g><text x='5' y='5'>Femur</text></g>",
        "pastilles": [{"n": 1, "x": 10, "y": 10, "t": "Femur", "ancre": "start"}],
    }])
    assert any("p1" in e and "text" in e for e in valider_cours(cours))


def test_pastille_hors_du_cadre_est_signalee():
    cours = cours_minimal(planches=[{
        "id": "p1", "titre": "T", "vb": "0 0 100 100",
        "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
        "pastilles": [{"n": 1, "x": 480, "y": 10, "t": "Femur", "ancre": "start"}],
    }])
    assert any("p1" in e and "cadre" in e for e in valider_cours(cours))


def test_numerotation_de_pastilles_non_contigue_est_signalee():
    cours = cours_minimal(planches=[{
        "id": "p1", "titre": "T", "vb": "0 0 100 100",
        "dessin": "<g><circle cx='5' cy='5' r='2'/></g>",
        "pastilles": [
            {"n": 1, "x": 10, "y": 10, "t": "A", "ancre": "start"},
            {"n": 3, "x": 20, "y": 20, "t": "B", "ancre": "start"},
        ],
    }])
    assert any("p1" in e and "numerotation" in e for e in valider_cours(cours))


def test_mention_hors_cours_autorise_une_slide_absente():
    cours = cours_minimal(cartes=[
        {"id": "c1-01", "q": "Q ?", "r": "R", "hors_cours": True},
    ])
    assert valider_cours(cours) == []
```

- [ ] **Step 2b: Lancer le test pour vérifier qu'il échoue**

Run: `cd "/home/valentin/Téléchargements/revision-anatomie" && python3 -m pytest tests/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'contenu.schema'`

- [ ] **Step 3: Écrire l'implémentation minimale**

Créer `contenu/__init__.py` (fichier vide) puis `contenu/schema.py` :

```python
"""Validation du contenu du cours.

Le PDF du cours fait foi. Ce module refuse tout contenu qui ne renvoie pas a
une slide verifiable, et toute planche dont le trace contient deja ses
etiquettes -- ce qui rendrait le mode muet impossible.
"""

CHAMPS_CARTE = ("id", "q", "r")
CHAMPS_QUIZ = ("id", "q", "choix", "bonne", "expl")
CHAMPS_MUSCLE = ("nom", "origine", "terminaison", "actions")


def valider_cours(cours):
    erreurs = []
    vus = set()
    for chapitre in cours.get("chapitres", []):
        erreurs += _valider_chapitre(chapitre, vus)
    return erreurs


def _valider_chapitre(chapitre, vus):
    erreurs = []
    num = chapitre.get("num")
    if not isinstance(num, int) or not 1 <= num <= 7:
        erreurs.append(f"chapitre {num!r} : numero invalide")
    bornes = chapitre.get("slides")
    if not (isinstance(bornes, list) and len(bornes) == 2 and bornes[0] <= bornes[1]):
        erreurs.append(f"chapitre {num} : plage de slides invalide")
        return erreurs

    for carte in chapitre.get("cartes", []):
        erreurs += _valider_entree(carte, CHAMPS_CARTE, bornes, vus, "carte")
    for question in chapitre.get("quiz", []):
        erreurs += _valider_entree(question, CHAMPS_QUIZ, bornes, vus, "quiz")
        erreurs += _valider_quiz(question)
    for muscle in chapitre.get("muscles", []):
        erreurs += _valider_muscle(muscle, bornes)
    for piege in chapitre.get("pieges", []):
        erreurs += _valider_slide(piege, bornes, piege.get("titre", "piege"))
    for planche in chapitre.get("planches", []):
        erreurs += valider_planche(planche)
    return erreurs


def _valider_entree(entree, champs, bornes, vus, genre):
    erreurs = []
    identifiant = entree.get("id", "<sans id>")
    for champ in champs:
        valeur = entree.get(champ)
        if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
            erreurs.append(f"{genre} {identifiant} : champ '{champ}' vide ou absent")
    if identifiant in vus:
        erreurs.append(f"{genre} {identifiant} : identifiant en double")
    vus.add(identifiant)
    erreurs += _valider_slide(entree, bornes, identifiant)
    return erreurs


def _valider_slide(entree, bornes, etiquette):
    if entree.get("hors_cours"):
        return []
    slide = entree.get("slide")
    if not isinstance(slide, int):
        return [f"{etiquette} : numero de slide absent"]
    if not bornes[0] <= slide <= bornes[1]:
        return [f"{etiquette} : slide {slide} hors de la plage {bornes[0]}-{bornes[1]}"]
    return []


def _valider_quiz(question):
    erreurs = []
    identifiant = question.get("id", "<sans id>")
    choix = question.get("choix") or []
    if len(choix) < 3:
        erreurs.append(f"quiz {identifiant} : au moins trois choix sont requis")
    bonne = question.get("bonne")
    if not isinstance(bonne, int) or not 0 <= bonne < len(choix):
        erreurs.append(f"quiz {identifiant} : index 'bonne' hors bornes")
    if not (question.get("expl") or "").strip():
        erreurs.append(f"quiz {identifiant} : explication absente")
    return erreurs


def _valider_muscle(muscle, bornes):
    erreurs = []
    nom = muscle.get("nom", "<sans nom>")
    for champ in CHAMPS_MUSCLE:
        valeur = muscle.get(champ)
        if not valeur:
            erreurs.append(f"muscle {nom} : champ '{champ}' vide ou absent")
    erreurs += _valider_slide(muscle, bornes, f"muscle {nom}")
    return erreurs


def valider_planche(planche):
    erreurs = []
    identifiant = planche.get("id", "<sans id>")
    if "<text" in (planche.get("dessin") or ""):
        erreurs.append(
            f"planche {identifiant} : le trace contient une balise text ; "
            "les etiquettes doivent vivre dans 'pastilles' pour permettre le mode muet"
        )
    try:
        _, _, largeur, hauteur = (float(v) for v in planche["vb"].split())
    except (KeyError, ValueError):
        erreurs.append(f"planche {identifiant} : viewBox invalide")
        return erreurs

    pastilles = planche.get("pastilles") or []
    for pastille in pastilles:
        if not 0 <= pastille.get("x", -1) <= largeur or not 0 <= pastille.get("y", -1) <= hauteur:
            erreurs.append(
                f"planche {identifiant} : pastille {pastille.get('n')} hors du cadre"
            )
        if not (pastille.get("t") or "").strip():
            erreurs.append(f"planche {identifiant} : pastille {pastille.get('n')} sans libelle")
    numeros = sorted(p.get("n") for p in pastilles)
    if numeros and numeros != list(range(1, len(numeros) + 1)):
        erreurs.append(f"planche {identifiant} : numerotation des pastilles non contigue")
    return erreurs
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `python3 -m pytest tests/test_schema.py -v`
Expected: PASS — 10 tests

- [ ] **Step 5: Commit** *(seulement si Valentin a autorisé les commits)*

```bash
git add contenu/ tests/test_schema.py .gitignore
git commit -m "feat: validateur de contenu du cours"
```

---

### Task 2: Contenu du chapitre 1

**Files:**
- Create: `contenu/cours.json`
- Create: `tests/test_contenu_chapitre1.py`

**Interfaces:**
- Consumes: `valider_cours` (tâche 1).
- Produces: `contenu/cours.json` conforme au modèle de la spec §6.4, chapitre 1 renseigné, champ `planches` laissé à `[]` (rempli par la tâche 3).

Le contenu textuel provient des slides 7 à 45, déjà extraites. Les notions à couvrir : position anatomique (slide 9) ; axe du corps, axe main/pied (11-13) ; plan frontal et ses mouvements — abduction, adduction, inclinaison latérale (15-20) ; plan sagittal et ses mouvements — flexion, extension, antépulsion, rétropulsion, antéversion, rétroversion, flexion dorsale, flexion plantaire (21-30) ; plan transversal — rotation, pronation, supination (31-36) ; circumduction (37) ; termes de localisation — crânial/caudal, proximal/distal, médial/latéral, superficiel/profond, antérieur/postérieur (38-45).

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/test_contenu_chapitre1.py` :

```python
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_cours

COURS = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
CHAPITRE_1 = COURS["chapitres"][0]


def test_le_contenu_est_conforme_au_schema():
    assert valider_cours(COURS) == []


def test_le_chapitre_1_couvre_le_volume_cible():
    assert len(CHAPITRE_1["cartes"]) >= 18
    assert len(CHAPITRE_1["quiz"]) >= 8
    assert len(CHAPITRE_1["pieges"]) >= 2


def test_chaque_mouvement_porte_son_plan():
    plans = {"frontal", "sagittal", "transversal"}
    mouvements = [c for c in CHAPITRE_1["cartes"] if c.get("plan")]
    assert mouvements, "aucune carte de mouvement n'est rattachee a un plan"
    assert all(c["plan"] in plans for c in mouvements)


def test_les_trois_plans_sont_tous_representes():
    plans = {c["plan"] for c in CHAPITRE_1["cartes"] if c.get("plan")}
    assert plans == {"frontal", "sagittal", "transversal"}


def test_aucun_distracteur_ne_se_repete_dans_une_question():
    for question in CHAPITRE_1["quiz"]:
        assert len(set(question["choix"])) == len(question["choix"]), question["id"]


def test_les_notions_cles_du_chapitre_sont_couvertes():
    texte = json.dumps(CHAPITRE_1, ensure_ascii=False).lower()
    for notion in ("position anatomique", "abduction", "adduction", "flexion",
                   "extension", "pronation", "supination", "circumduction",
                   "proximal", "distal", "medial", "lateral", "cranial", "caudal"):
        assert notion in texte, f"notion absente du chapitre 1 : {notion}"
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python3 -m pytest tests/test_contenu_chapitre1.py -v`
Expected: FAIL — `FileNotFoundError: contenu/cours.json`

- [ ] **Step 3: Rédiger le contenu**

Créer `contenu/cours.json`. Squelette et premières entrées, à compléter jusqu'aux volumes exigés par le test (≥ 18 cartes, ≥ 8 questions, ≥ 2 pièges) :

```json
{
  "meta": {
    "cours": "UC1 — Anatomie",
    "auteur": "ADJ Robichon",
    "source": "ANATOMIE _230831_213333.pdf",
    "slides": 328
  },
  "chapitres": [
    {
      "num": 1,
      "titre": "Terminologie anatomique",
      "slides": [7, 45],
      "sections": [
        {
          "titre": "La position anatomique",
          "slide": 9,
          "points": [
            "Corps humain, vivant, debout, membres supérieurs allongés le long du corps.",
            "Paume des mains tournée en avant, regard droit et horizontal.",
            "Toutes les descriptions anatomiques se réfèrent à cette position."
          ]
        },
        {
          "titre": "Axes anatomiques",
          "slide": 11,
          "points": [
            "Axe du corps : verticale du vertex au centre de gravité, situé dans le pelvis.",
            "Axe de la main : axe longitudinal passant par le 3e doigt.",
            "Axe du pied : axe longitudinal passant par le 2e orteil."
          ]
        }
      ],
      "planches": [],
      "cartes": [
        {
          "id": "c1-01",
          "q": "Énonce la définition conventionnelle de la position anatomique.",
          "r": "Corps humain, vivant, debout, les membres supérieurs allongés le long du corps, la paume des mains tournée en avant, le regard droit et horizontal.",
          "slide": 9
        },
        {
          "id": "c1-02",
          "q": "Par quels points passe l'axe du corps ?",
          "r": "Par le vertex (sommet du crâne) et par le centre de gravité du corps, situé dans le pelvis.",
          "slide": 11
        },
        {
          "id": "c1-03",
          "q": "Quel doigt porte l'axe de la main ? Quel orteil porte l'axe du pied ?",
          "r": "La main : le 3e doigt. Le pied : le 2e orteil.",
          "slide": 13
        },
        {
          "id": "c1-04",
          "q": "Le plan frontal divise le corps en quoi, et quels mouvements s'y observent ?",
          "r": "En deux faces, antérieure (ventrale) et postérieure (dorsale). Mouvements : abduction, adduction, inclinaison latérale droite ou gauche.",
          "slide": 15,
          "plan": "frontal"
        },
        {
          "id": "c1-05",
          "q": "Abduction ou adduction : lequel écarte le membre de l'axe du corps ?",
          "r": "L'abduction écarte. L'adduction rapproche.",
          "slide": 17,
          "plan": "frontal"
        },
        {
          "id": "c1-06",
          "q": "Définis la flexion en termes d'angle articulaire.",
          "r": "Mouvement de repli qui diminue l'angle de l'articulation et rapproche deux segments osseux l'un de l'autre.",
          "slide": 23,
          "plan": "sagittal"
        },
        {
          "id": "c1-07",
          "q": "Antépulsion et rétropulsion : de quelle articulation s'agit-il, et que font-elles ?",
          "r": "Articulation scapulo-humérale. L'antépulsion ouvre l'angle bras-tronc, la rétropulsion le ferme.",
          "slide": 26,
          "plan": "sagittal"
        },
        {
          "id": "c1-08",
          "q": "Antéversion et rétroversion : quelle articulation, et quel effet sur le dos ?",
          "r": "Articulation coxo-fémorale. L'antéversion amène le bassin vers l'avant (« dos creux »), la rétroversion vers l'arrière (« dos plat »).",
          "slide": 28,
          "plan": "sagittal"
        },
        {
          "id": "c1-09",
          "q": "Que sont la pronation et la supination, et quel os bouge ?",
          "r": "Pronation : rotation médiale de l'avant-bras, le radius croise l'ulna. Supination : rotation latérale, le radius est parallèle à l'ulna. Seul le radius tourne, autour de l'ulna.",
          "slide": 34,
          "plan": "transversal"
        },
        {
          "id": "c1-10",
          "q": "Qu'est-ce que la circumduction ?",
          "r": "Le mouvement au cours duquel le membre décrit un cône dans l'espace.",
          "slide": 37
        }
      ],
      "quiz": [
        {
          "id": "q1-01",
          "q": "Dans quel plan s'effectue une inclinaison latérale du tronc ?",
          "choix": ["Le plan frontal", "Le plan sagittal", "Le plan transversal"],
          "bonne": 0,
          "expl": "Le plan frontal est celui des mouvements visibles de face : abduction, adduction et inclinaison latérale. La rotation du tronc, elle, est transversale.",
          "slide": 15,
          "plan": "frontal"
        },
        {
          "id": "q1-02",
          "q": "La flexion dorsale du pied se situe au niveau de quelle articulation ?",
          "choix": [
            "L'articulation talo-crurale",
            "L'articulation coxo-fémorale",
            "L'articulation scapulo-humérale",
            "L'articulation tibio-fémorale"
          ],
          "bonne": 0,
          "expl": "La talo-crurale est la cheville. La coxo-fémorale porte l'antéversion et la rétroversion, la scapulo-humérale l'antépulsion et la rétropulsion.",
          "slide": 30,
          "plan": "sagittal"
        },
        {
          "id": "q1-03",
          "q": "Pendant une supination, quelle est la position du radius ?",
          "choix": [
            "Parallèle à l'ulna",
            "Croisé par-dessus l'ulna",
            "Croisé sous l'ulna",
            "Immobile, c'est l'ulna qui tourne"
          ],
          "bonne": 0,
          "expl": "En supination le radius est parallèle à l'ulna ; c'est en pronation qu'il le croise. Dans les deux cas, seul le radius tourne.",
          "slide": 34,
          "plan": "transversal"
        }
      ],
      "muscles": [],
      "pieges": [
        {
          "titre": "Le plan sagittal ne coupe pas toujours au milieu",
          "texte": "Un plan sagittal sépare une partie droite d'une partie gauche, sans qu'elles soient forcément égales. Ce n'est que lorsqu'il passe par la ligne médiane, avec deux parties symétriques, qu'on parle de plan sagittal médian.",
          "slide": 21
        },
        {
          "titre": "Flexion plantaire est une extension",
          "texte": "La flexion plantaire du pied correspond anatomiquement à une extension. Le mot « flexion » dans son nom désigne le mouvement vers la plante, pas la fermeture d'un angle.",
          "slide": 30
        },
        {
          "titre": "Rotation droite/gauche contre latérale/médiale",
          "texte": "Pour la tête et le tronc, on dit rotation droite ou gauche. Pour les membres, on dit rotation latérale (externe) ou médiale (interne). Employer l'un pour l'autre est une faute de vocabulaire, pas une approximation.",
          "slide": 32
        }
      ]
    }
  ]
}
```

Compléter jusqu'à atteindre au minimum 18 cartes et 8 questions, en couvrant les notions listées en tête de tâche. Chaque distracteur doit être une confusion réellement possible : un plan voisin, un mouvement antagoniste, une articulation voisine — jamais un terme inventé.

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `python3 -m pytest tests/ -v`
Expected: PASS — tests du schéma et du contenu

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add contenu/cours.json tests/test_contenu_chapitre1.py
git commit -m "feat: contenu du chapitre 1"
```

---

### Task 3: Planches SVG du chapitre 1

**Files:**
- Create: `outils/planches.py`
- Create: `tests/test_planches.py`
- Modify: `contenu/cours.json` (remplir `chapitres[0].planches`)

**Interfaces:**
- Consumes: `valider_cours` (tâche 1).
- Produces: `PLANCHES: dict[str, dict]` indexé par identifiant de planche, chaque valeur au format de la spec §5.5 (`id`, `titre`, `vb`, `dessin`, `pastilles`). Deux planches : `plans-anatomiques` et `termes-localisation`. Consommé par la tâche 5 et par `exercices.js` (tâche 8).

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/test_planches.py` :

```python
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from contenu.schema import valider_planche
from outils.planches import PLANCHES


def test_les_deux_planches_du_chapitre_1_existent():
    assert set(PLANCHES) >= {"plans-anatomiques", "termes-localisation"}


def test_chaque_planche_est_conforme():
    for identifiant, planche in PLANCHES.items():
        assert valider_planche(planche) == [], identifiant


def test_aucun_trace_ne_contient_ses_etiquettes():
    for identifiant, planche in PLANCHES.items():
        assert "<text" not in planche["dessin"], identifiant


def test_les_pastilles_des_plans_portent_leur_plan():
    pastilles = PLANCHES["plans-anatomiques"]["pastilles"]
    plans = {p.get("plan") for p in pastilles if p.get("plan")}
    assert plans == {"frontal", "sagittal", "transversal"}


def test_les_libelles_sont_uniques_dans_une_planche():
    for identifiant, planche in PLANCHES.items():
        libelles = [p["t"] for p in planche["pastilles"]]
        assert len(set(libelles)) == len(libelles), identifiant
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python3 -m pytest tests/test_planches.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'outils.planches'`

- [ ] **Step 3: Écrire l'implémentation**

Créer `outils/__init__.py` (vide) puis `outils/planches.py`. Le module ne contient que de la géométrie : aucun texte de cours, aucune balise `<text>`. Les étiquettes vivent dans `pastilles` pour que le mode muet et le mode légendé sortent de la même définition.

```python
"""Traces SVG des planches.

Contrat : 'dessin' ne contient jamais d'etiquette. Les libelles vivent dans
'pastilles', ce qui permet de produire le mode legende et le mode muet depuis
une seule source, sans risque de divergence.
"""

_SILHOUETTE_FACE = (
    "<g class='corps' fill='none' stroke='currentColor' stroke-width='2'>"
    "<circle cx='160' cy='48' r='26'/>"
    "<path d='M160 74 L160 196'/>"
    "<path d='M160 96 L104 150 M160 96 L216 150'/>"
    "<path d='M160 196 L128 292 M160 196 L192 292'/>"
    "</g>"
)

PLANCHES = {
    "plans-anatomiques": {
        "id": "plans-anatomiques",
        "titre": "Les trois plans anatomiques",
        "vb": "0 0 320 340",
        "dessin": (
            "<g class='plan plan--frontal'>"
            "<path d='M64 26 L256 26 L256 314 L64 314 Z' fill='none' "
            "stroke='currentColor' stroke-dasharray='5 4' stroke-width='1.5'/></g>"
            "<g class='plan plan--sagittal'>"
            "<path d='M160 20 L160 320' stroke='currentColor' "
            "stroke-dasharray='5 4' stroke-width='1.5'/></g>"
            "<g class='plan plan--transversal'>"
            "<path d='M52 176 L268 176' stroke='currentColor' "
            "stroke-dasharray='5 4' stroke-width='1.5'/></g>"
            + _SILHOUETTE_FACE
        ),
        "pastilles": [
            {"n": 1, "x": 258, "y": 40, "t": "Plan frontal", "ancre": "end", "plan": "frontal"},
            {"n": 2, "x": 166, "y": 24, "t": "Plan sagittal", "ancre": "start", "plan": "sagittal"},
            {"n": 3, "x": 56, "y": 170, "t": "Plan transversal", "ancre": "start", "plan": "transversal"},
        ],
    },
    "termes-localisation": {
        "id": "termes-localisation",
        "titre": "Les termes de localisation",
        "vb": "0 0 320 340",
        "dessin": (
            _SILHOUETTE_FACE
            + "<g class='reperes' fill='none' stroke='currentColor' stroke-width='1.5'>"
            "<path d='M286 40 L286 96' marker-end='url(#fleche)'/>"
            "<path d='M286 300 L286 244' marker-end='url(#fleche)'/>"
            "<path d='M96 162 L64 162' marker-end='url(#fleche)'/>"
            "<path d='M224 162 L256 162' marker-end='url(#fleche)'/>"
            "</g>"
        ),
        "pastilles": [
            {"n": 1, "x": 278, "y": 36, "t": "Crânial", "ancre": "end"},
            {"n": 2, "x": 278, "y": 308, "t": "Caudal", "ancre": "end"},
            {"n": 3, "x": 100, "y": 152, "t": "Proximal", "ancre": "start"},
            {"n": 4, "x": 120, "y": 286, "t": "Distal", "ancre": "start"},
            {"n": 5, "x": 168, "y": 162, "t": "Médial", "ancre": "start"},
            {"n": 6, "x": 250, "y": 152, "t": "Latéral", "ancre": "end"},
        ],
    },
}
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `python3 -m pytest tests/test_planches.py -v`
Expected: PASS — 5 tests

- [ ] **Step 5: Injecter les planches dans le contenu**

Renseigner `chapitres[0].planches` dans `contenu/cours.json` avec les deux objets produits par `outils/planches.py`, en ajoutant à chacun son numéro de slide (`"slide": 15` pour les plans, `"slide": 38` pour les termes de localisation).

Run: `python3 -m pytest tests/ -v`
Expected: PASS — l'ensemble de la suite

- [ ] **Step 6: Commit** *(si autorisé)*

```bash
git add outils/ tests/test_planches.py contenu/cours.json
git commit -m "feat: planches SVG du chapitre 1"
```

---

### Task 4: Feuille de style et vérification du contraste

**Files:**
- Create: `site/assets/style.css`
- Create: `tests/test_contraste.py`

**Interfaces:**
- Consumes: rien.
- Produces: les variables CSS `--papier`, `--carte`, `--encre`, `--encre-doux`, `--trait`, `--frontal`, `--sagittal`, `--transversal` sur `:root` et sur `[data-theme="sombre"]`, plus les classes `.plan--frontal`, `.plan--sagittal`, `.plan--transversal`. Consommé par les tâches 5, 9 et 10.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/test_contraste.py` :

```python
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
CSS = RACINE / "site" / "assets" / "style.css"

CLAIR = {
    "papier": "#EDEFF2", "carte": "#FFFFFF", "encre": "#101A22",
    "encre-doux": "#4A5A66", "trait": "#C9D2D9",
    "frontal": "#C1553A", "sagittal": "#1F6F78", "transversal": "#B0821F",
}
SOMBRE = {
    "papier": "#0E1418", "carte": "#161F25", "encre": "#E6EDF2",
    "encre-doux": "#97A7B2", "trait": "#2A3841",
    "frontal": "#E07A5F", "sagittal": "#3FA3AD", "transversal": "#DCA83A",
}


def _canal(valeur):
    valeur /= 255
    return valeur / 12.92 if valeur <= 0.04045 else ((valeur + 0.055) / 1.055) ** 2.4


def luminance(hexa):
    r, v, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _canal(r) + 0.7152 * _canal(v) + 0.0722 * _canal(b)


def contraste(premier, second):
    a, b = sorted((luminance(premier), luminance(second)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def test_le_texte_atteint_le_niveau_AA():
    for palette in (CLAIR, SOMBRE):
        for fond in ("papier", "carte"):
            assert contraste(palette["encre"], palette[fond]) >= 4.5
            assert contraste(palette["encre-doux"], palette[fond]) >= 4.5


def test_les_trois_plans_restent_lisibles_sur_les_deux_fonds():
    for palette in (CLAIR, SOMBRE):
        for plan in ("frontal", "sagittal", "transversal"):
            for fond in ("papier", "carte"):
                assert contraste(palette[plan], palette[fond]) >= 3.0, (plan, fond)


def test_la_feuille_de_style_declare_toutes_les_variables():
    css = CSS.read_text(encoding="utf-8")
    for nom, valeur in CLAIR.items():
        assert f"--{nom}: {valeur}" in css, nom
    for valeur in SOMBRE.values():
        assert valeur in css


def test_le_mouvement_est_desactivable():
    css = CSS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css


def test_les_cibles_tactiles_sont_declarees():
    css = CSS.read_text(encoding="utf-8")
    assert re.search(r"min-height:\s*44px", css)
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python3 -m pytest tests/test_contraste.py -v`
Expected: FAIL — `FileNotFoundError: site/assets/style.css`

- [ ] **Step 3: Écrire la feuille de style**

Créer `site/assets/style.css`. Structure imposée, dans cet ordre : variables des deux thèmes ; réinitialisation ; typographie et échelle ; mise en page (une colonne sous 720 px, deux au-delà) ; composants (en-tête de planche, onglets, carte, quiz, planche SVG, anneau de progression, barre d'actions ancrée en bas sur mobile) ; états de focus ; requête `prefers-reduced-motion`.

Contraintes non négociables, toutes vérifiées par le test :
- les huit variables du thème clair déclarées littéralement sur `:root` ;
- les huit variables du thème sombre sous `[data-theme="sombre"]` **et** sous `@media (prefers-color-scheme: dark)` avec le garde `:root:not([data-theme="clair"])` ;
- `min-height: 44px` sur les boutons d'action ;
- un bloc `@media (prefers-reduced-motion: reduce)` qui ramène `animation-duration` et `transition-duration` à `0.01ms`.

Échelle typographique : 13 / 15 / 17 / 21 / 28 / 44 px. Interlignage 1,55 au corps, 1,1 aux titres. Longueur de ligne plafonnée par `max-width: 68ch` sur les blocs de texte.

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `python3 -m pytest tests/test_contraste.py -v`
Expected: PASS — 5 tests

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add site/assets/style.css tests/test_contraste.py
git commit -m "feat: systeme visuel et verification du contraste"
```

---

### Task 5: Générateur HTML

**Files:**
- Create: `gabarits/base.html`
- Create: `gabarits/chapitre.html`
- Create: `outils/construire.py`
- Create: `tests/test_construire.py`

**Interfaces:**
- Consumes: `contenu/cours.json` (tâche 2), `valider_cours` (tâche 1), `site/assets/style.css` (tâche 4).
- Produces: `construire(racine: Path) -> list[Path]` — écrit les pages dans `site/` et renvoie la liste des fichiers écrits. Écrit aussi `site/assets/cours.json`, copie du contenu consommée par le JavaScript.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/test_construire.py` :

```python
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from outils.construire import construire

FICHIERS = construire(RACINE)
PAGE = (RACINE / "site" / "chapitre-1.html").read_text(encoding="utf-8")


def test_la_page_du_chapitre_1_est_ecrite():
    assert (RACINE / "site" / "chapitre-1.html") in FICHIERS


def test_la_page_interdit_l_indexation():
    assert 'name="robots"' in PAGE and "noindex" in PAGE


def test_toutes_les_cartes_sont_dans_le_dom():
    import json
    cours = json.loads((RACINE / "contenu" / "cours.json").read_text(encoding="utf-8"))
    for carte in cours["chapitres"][0]["cartes"]:
        assert carte["id"] in PAGE, carte["id"]


def test_les_reponses_sont_masquees_par_defaut():
    assert 'data-etat="cachee"' in PAGE


def test_chaque_renvoi_de_slide_est_affiche():
    assert "slide 9" in PAGE


def test_l_onglet_muscles_est_absent_quand_il_n_y_a_pas_de_muscle():
    assert 'data-onglet="muscles"' not in PAGE


def test_le_contenu_du_cours_est_present_sans_javascript():
    assert "Corps humain, vivant, debout" in PAGE


def test_une_copie_du_contenu_est_publiee_pour_le_client():
    assert (RACINE / "site" / "assets" / "cours.json").exists()
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python3 -m pytest tests/test_construire.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'outils.construire'`

- [ ] **Step 3: Écrire les gabarits et le générateur**

`gabarits/base.html` contient l'enveloppe, avec les marqueurs `{{titre}}`, `{{corps}}`, `{{racine}}` :

```html
<!doctype html>
<html lang="fr" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{{titre}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Public+Sans:wght@400;500;700&family=Saira+Condensed:wght@600;700&display=swap">
<link rel="stylesheet" href="{{racine}}assets/style.css">
</head>
<body>
{{corps}}
<script type="module" src="{{racine}}assets/app.js"></script>
</body>
</html>
```

`gabarits/chapitre.html` contient le corps d'une page chapitre : en-tête de planche, barre d'onglets, puis une `<section>` par onglet. Toutes les sections sont écrites dans le HTML ; `interface.js` ne fait que les montrer ou les cacher. Les réponses de carte portent `data-etat="cachee"`.

`outils/construire.py` :

```python
"""cours.json -> pages HTML statiques.

Le generateur ne connait ni la geometrie des planches ni le contenu du cours :
il assemble des gabarits. Toute assertion publiee porte son numero de slide.
"""

import html
import json
import shutil
from pathlib import Path

# La table de decalage vit dans contenu/schema.py, pas ici : le validateur s'en sert
# pour verifier qu'un libelle decale ne sort pas du viewBox. Une seule definition,
# donc aucune derive possible entre ce qui est valide et ce qui est rendu.
from contenu.schema import DECALAGE_LIBELLE

ONGLETS = (
    ("planche", "Planche", "planches"),
    ("cartes", "Cartes", "cartes"),
    ("quiz", "Quiz", "quiz"),
    ("muscles", "Muscles", "muscles"),
    ("cours", "Le cours", "sections"),
)


def construire(racine: Path) -> list[Path]:
    racine = Path(racine)
    cours = json.loads((racine / "contenu" / "cours.json").read_text(encoding="utf-8"))
    base = (racine / "gabarits" / "base.html").read_text(encoding="utf-8")
    gabarit = (racine / "gabarits" / "chapitre.html").read_text(encoding="utf-8")

    sortie = racine / "site"
    (sortie / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(racine / "contenu" / "cours.json", sortie / "assets" / "cours.json")

    ecrits = []
    for chapitre in cours["chapitres"]:
        corps = _rendre_chapitre(gabarit, chapitre)
        page = (base
                .replace("{{titre}}", f"Chapitre {chapitre['num']} — {chapitre['titre']}")
                .replace("{{racine}}", "")
                .replace("{{corps}}", corps))
        chemin = sortie / f"chapitre-{chapitre['num']}.html"
        chemin.write_text(page, encoding="utf-8")
        ecrits.append(chemin)
    return ecrits


def _onglets_actifs(chapitre):
    return [(cle, libelle) for cle, libelle, source in ONGLETS if chapitre.get(source)]


def _rendre_chapitre(gabarit, chapitre):
    barre = "".join(
        f'<button class="onglet" data-onglet="{cle}">{html.escape(libelle)}</button>'
        for cle, libelle in _onglets_actifs(chapitre)
    )
    sections = "".join(
        f'<section class="volet" data-volet="{cle}">{_rendre_volet(cle, chapitre)}</section>'
        for cle, _ in _onglets_actifs(chapitre)
    )
    return (gabarit
            .replace("{{num}}", str(chapitre["num"]))
            .replace("{{titre}}", html.escape(chapitre["titre"]))
            .replace("{{slides}}", f"slides {chapitre['slides'][0]}–{chapitre['slides'][1]}")
            .replace("{{onglets}}", barre)
            .replace("{{volets}}", sections))


def _src(entree):
    if entree.get("hors_cours"):
        return '<span class="src src--hors">[hors cours]</span>'
    return f'<span class="src">slide {entree["slide"]}</span>'


def _rendre_volet(cle, chapitre):
    if cle == "cartes":
        return "".join(
            f'<article class="carte" id="{html.escape(c["id"])}" '
            f'data-plan="{html.escape(c.get("plan", ""))}">'
            f'<p class="carte__q">{html.escape(c["q"])}</p>'
            f'<p class="carte__r" data-etat="cachee">{html.escape(c["r"])}</p>'
            f'{_src(c)}</article>'
            for c in chapitre["cartes"]
        )
    if cle == "quiz":
        return "".join(
            f'<article class="question" id="{html.escape(q["id"])}">'
            f'<p class="question__q">{html.escape(q["q"])}</p>'
            + "".join(
                f'<button class="choix" data-index="{i}">{html.escape(texte)}</button>'
                for i, texte in enumerate(q["choix"])
            )
            + f'<p class="question__expl" data-etat="cachee">{html.escape(q["expl"])}</p>'
            f'{_src(q)}</article>'
            for q in chapitre["quiz"]
        )
    if cle == "cours":
        return "".join(
            f'<section class="notion"><h3>{html.escape(s["titre"])}</h3><ul>'
            + "".join(f"<li>{html.escape(p)}</li>" for p in s["points"])
            + f"</ul>{_src(s)}</section>"
            for s in chapitre["sections"]
        )
    if cle == "planche":
        # Conteneur en grille : les planches s'alignent cote a cote quand la place le
        # permet et s'empilent sur telephone. Sans lui, trois planches autonomes
        # s'empilent aussi sur grand ecran et on perd la comparaison des trois plans.
        return ('<div class="planches">'
                + "".join(_rendre_planche(p) for p in chapitre["planches"])
                + "</div>")
    if cle == "muscles":
        return "".join(
            f'<tr><th>{html.escape(m["nom"])}</th>'
            f'<td>{html.escape(" ; ".join(m["origine"]))}</td>'
            f'<td>{html.escape(" ; ".join(m["terminaison"]))}</td>'
            f'<td>{html.escape(" ; ".join(m["actions"]))}</td></tr>'
            for m in chapitre["muscles"]
        )
    return ""


def _rendre_planche(planche):
    pastilles = ""
    for p in planche["pastilles"]:
        dx, dy = DECALAGE_LIBELLE[p["ancre"]]
        indice = f' data-indice="{html.escape(p["indice"])}"' if p.get("indice") else ""
        pastilles += (
            f'<g class="pastille" data-n="{p["n"]}" data-plan="{p.get("plan", "")}"{indice}>'
            f'<circle cx="{p["x"]}" cy="{p["y"]}" r="9"/>'
            f'<text class="pastille__n" x="{p["x"]}" y="{p["y"] + 4}" '
            f'text-anchor="middle">{p["n"]}</text>'
            f'<text class="pastille__t" x="{p["x"] + dx}" y="{p["y"] + dy}" '
            f'text-anchor="{p["ancre"]}">{html.escape(p["t"])}</text></g>'
        )
    return (
        f'<figure class="planche" id="{html.escape(planche["id"])}" data-mode="legende">'
        f'<figcaption>{html.escape(planche["titre"])} {_src(planche)}</figcaption>'
        f'<svg viewBox="{planche["vb"]}" role="img">{planche["dessin"]}{pastilles}</svg>'
        f'</figure>'
    )


if __name__ == "__main__":
    for chemin in construire(Path(__file__).resolve().parents[1]):
        print(chemin)
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `python3 -m pytest tests/ -v`
Expected: PASS — l'ensemble de la suite

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add gabarits/ outils/construire.py tests/test_construire.py site/
git commit -m "feat: generateur de pages HTML"
```

---

### Task 6: Planificateur d'espacement

**Files:**
- Create: `site/assets/planificateur.js`
- Create: `tests/planificateur.test.js`
- Modify: `docs/superpowers/specs/2026-09-18-site-revision-anatomie-design.md` (§7, acter la séparation en quatre fichiers)

**Interfaces:**
- Consumes: rien. Module pur, sans DOM et sans `localStorage`.
- Produces:
  - `intervalleDeBase(joursAvantExamen: number) -> number`
  - `echeance(item: {derniereVue: string|null, statut: string}, intervalle: number) -> string` — date ISO `AAAA-MM-JJ`
  - `estDu(item, intervalle, aujourdHui: string) -> boolean`
  - `composerSeance(items: Item[], options: {intervalle, aujourdHui, taille}) -> Item[]`
  - `ajouterJours(iso: string, n: number) -> string`
  - Type `Item = {id, chapitre, type, derniereVue, statut, echecs}` avec `statut ∈ {"jamais","rate","difficile","su"}`.

  Consommé par les tâches 7, 8 et 10.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/planificateur.test.js` :

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  intervalleDeBase, echeance, estDu, composerSeance, ajouterJours,
} from '../site/assets/planificateur.js';

const item = (id, chapitre, statut = 'jamais', derniereVue = null, type = 'carte') =>
  ({ id, chapitre, type, statut, derniereVue, echecs: 0 });

test('l’intervalle vaut environ 15 % du délai avant l’examen', () => {
  assert.equal(intervalleDeBase(28), 4);
  assert.equal(intervalleDeBase(14), 2);
});

test('l’intervalle ne descend jamais sous un jour ni au-dessus de sept', () => {
  assert.equal(intervalleDeBase(2), 1);
  assert.equal(intervalleDeBase(365), 7);
});

test('sans date d’examen exploitable, l’intervalle retombe à trois jours', () => {
  assert.equal(intervalleDeBase(0), 3);
  assert.equal(intervalleDeBase(-5), 3);
  assert.equal(intervalleDeBase(NaN), 3);
});

test('un item jamais vu est dû immédiatement', () => {
  assert.equal(estDu(item('a', 1), 4, '2026-09-18'), true);
});

test('un item raté repasse le jour même', () => {
  const rate = item('a', 1, 'rate', '2026-09-18');
  assert.equal(echeance(rate, 4), '2026-09-18');
});

test('un item difficile revient deux fois plus vite qu’un item su', () => {
  const difficile = item('a', 1, 'difficile', '2026-09-18');
  const su = item('b', 1, 'su', '2026-09-18');
  assert.equal(echeance(difficile, 4), '2026-09-20');
  assert.equal(echeance(su, 4), '2026-09-22');
});

test('un item su n’est pas dû avant son échéance', () => {
  const su = item('a', 1, 'su', '2026-09-18');
  assert.equal(estDu(su, 4, '2026-09-21'), false);
  assert.equal(estDu(su, 4, '2026-09-22'), true);
});

test('ajouterJours franchit correctement les fins de mois', () => {
  assert.equal(ajouterJours('2026-09-29', 4), '2026-10-03');
  assert.equal(ajouterJours('2026-12-30', 3), '2027-01-02');
});

test('la séance alterne les chapitres plutôt que de les enchaîner', () => {
  const items = [
    item('a1', 1), item('a2', 1), item('a3', 1),
    item('b1', 2), item('b2', 2), item('b3', 2),
  ];
  const seance = composerSeance(items, { intervalle: 4, aujourdHui: '2026-09-18', taille: 6 });
  for (let i = 1; i < seance.length; i += 1) {
    assert.notEqual(seance[i].chapitre, seance[i - 1].chapitre);
  }
});

test('la séance respecte la taille demandée', () => {
  const items = Array.from({ length: 40 }, (_, i) => item(`x${i}`, (i % 3) + 1));
  assert.equal(composerSeance(items, { intervalle: 4, aujourdHui: '2026-09-18', taille: 25 }).length, 25);
});

test('les items fragiles passent en tête de séance', () => {
  const fragile = { ...item('f', 1, 'rate', '2026-09-18'), echecs: 2 };
  const seance = composerSeance([item('a', 2), fragile, item('b', 3)],
    { intervalle: 4, aujourdHui: '2026-09-18', taille: 3 });
  assert.equal(seance[0].id, 'f');
});

test('la séance ne retient que les items dus', () => {
  const su = item('frais', 2, 'su', '2026-09-18');
  const seance = composerSeance([item('a', 1), su],
    { intervalle: 4, aujourdHui: '2026-09-19', taille: 10 });
  assert.deepEqual(seance.map((i) => i.id), ['a']);
});
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `cd "/home/valentin/Téléchargements/revision-anatomie" && node --test tests/planificateur.test.js`
Expected: FAIL — `Cannot find module .../site/assets/planificateur.js`

- [ ] **Step 3: Écrire l'implémentation**

Créer `site/assets/planificateur.js`. Les dates sont manipulées en chaînes ISO et en jours entiers : aucun fuseau horaire n'intervient, donc les tests restent stables où qu'ils s'exécutent.

```javascript
/**
 * Calcul des echeances de revision et composition de la seance du jour.
 *
 * Module pur : ni DOM, ni localStorage, ni horloge. La date du jour est
 * toujours passee en parametre, ce qui rend chaque fonction testable.
 *
 * L'intervalle suit Cepeda et al. (2008) : environ 15 % du delai restant
 * avant l'examen. Intervalles fixes et non croissants, l'ecart mesure entre
 * les deux n'etant pas significatif.
 */

const JOUR_MS = 86400000;
const INTERVALLE_PAR_DEFAUT = 3;
const INTERVALLE_MAX = 7;

export function ajouterJours(iso, n) {
  const date = new Date(`${iso}T00:00:00Z`);
  return new Date(date.getTime() + n * JOUR_MS).toISOString().slice(0, 10);
}

export function intervalleDeBase(joursAvantExamen) {
  if (!Number.isFinite(joursAvantExamen) || joursAvantExamen <= 0) {
    return INTERVALLE_PAR_DEFAUT;
  }
  return Math.min(INTERVALLE_MAX, Math.max(1, Math.round(0.15 * joursAvantExamen)));
}

export function echeance(item, intervalle) {
  if (!item.derniereVue || item.statut === 'jamais') return '0000-01-01';
  if (item.statut === 'rate') return item.derniereVue;
  const delai = item.statut === 'difficile'
    ? Math.max(1, Math.round(intervalle / 2))
    : intervalle;
  return ajouterJours(item.derniereVue, delai);
}

export function estDu(item, intervalle, aujourdHui) {
  return echeance(item, intervalle) <= aujourdHui;
}

export function composerSeance(items, { intervalle, aujourdHui, taille = 25 }) {
  const dus = items.filter((item) => estDu(item, intervalle, aujourdHui));
  const fragiles = dus.filter((item) => item.echecs >= 2);
  const reste = dus.filter((item) => item.echecs < 2);

  const parChapitre = new Map();
  for (const item of reste) {
    if (!parChapitre.has(item.chapitre)) parChapitre.set(item.chapitre, []);
    parChapitre.get(item.chapitre).push(item);
  }

  // Tourniquet entre chapitres : deux items consecutifs ne partagent pas
  // le meme chapitre tant qu'un autre chapitre a encore des items en attente.
  const entrelaces = [];
  const files = [...parChapitre.values()];
  while (files.some((file) => file.length)) {
    for (const file of files) {
      if (file.length) entrelaces.push(file.shift());
    }
  }

  return [...fragiles, ...entrelaces].slice(0, taille);
}
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `node --test tests/planificateur.test.js`
Expected: PASS — 12 tests

- [ ] **Step 5: Mettre la spec à jour**

Dans `docs/superpowers/specs/2026-09-18-site-revision-anatomie-design.md`, §7, remplacer la phrase annonçant « quatre modules indépendants dans un seul fichier » par la description des quatre fichiers ES séparés, en indiquant le motif : testabilité sous Node sans navigateur.

- [ ] **Step 6: Commit** *(si autorisé)*

```bash
git add site/assets/planificateur.js tests/planificateur.test.js docs/
git commit -m "feat: planificateur d'espacement"
```

---

### Task 7: Stockage de la progression

**Files:**
- Create: `site/assets/stockage.js`
- Create: `tests/stockage.test.js`

**Interfaces:**
- Consumes: rien.
- Produces:
  - `creerStockage(support: Storage) -> Stockage` — `support` est injecté, ce qui permet de tester sans navigateur.
  - `Stockage.lire() -> {dateExamen: string|null, theme: string, items: Record<string, Item>}`
  - `Stockage.ecrireItem(id: string, item: Item) -> void`
  - `Stockage.definirDateExamen(iso: string) -> void`
  - `Stockage.definirTheme(nom: string) -> void`
  - `Stockage.exporter() -> string` (JSON)
  - `Stockage.importer(json: string) -> boolean`
  - `Stockage.reinitialiser() -> void`
  - Constante `CLE = 'uc1-anatomie-v1'`.

  Consommé par les tâches 9 et 10.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/stockage.test.js` :

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { creerStockage, CLE } from '../site/assets/stockage.js';

function supportFactice() {
  const donnees = new Map();
  return {
    getItem: (cle) => (donnees.has(cle) ? donnees.get(cle) : null),
    setItem: (cle, valeur) => donnees.set(cle, String(valeur)),
    removeItem: (cle) => donnees.delete(cle),
  };
}

test('un stockage vierge renvoie un état par défaut exploitable', () => {
  const etat = creerStockage(supportFactice()).lire();
  assert.equal(etat.dateExamen, null);
  assert.equal(etat.theme, 'auto');
  assert.deepEqual(etat.items, {});
});

test('un item écrit est relu à l’identique', () => {
  const stockage = creerStockage(supportFactice());
  const item = { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'su', derniereVue: '2026-09-18', echecs: 0 };
  stockage.ecrireItem('c1-01', item);
  assert.deepEqual(stockage.lire().items['c1-01'], item);
});

test('un contenu corrompu ne fait pas tomber l’application', () => {
  const support = supportFactice();
  support.setItem(CLE, '{ ceci n est pas du json');
  assert.deepEqual(creerStockage(support).lire().items, {});
});

test('la date d’examen et le thème sont conservés', () => {
  const stockage = creerStockage(supportFactice());
  stockage.definirDateExamen('2026-10-19');
  stockage.definirTheme('sombre');
  const etat = stockage.lire();
  assert.equal(etat.dateExamen, '2026-10-19');
  assert.equal(etat.theme, 'sombre');
});

test('un export se réimporte sans perte', () => {
  const source = creerStockage(supportFactice());
  source.definirDateExamen('2026-10-19');
  source.ecrireItem('c1-01', { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'difficile', derniereVue: '2026-09-18', echecs: 1 });

  const cible = creerStockage(supportFactice());
  assert.equal(cible.importer(source.exporter()), true);
  assert.deepEqual(cible.lire(), source.lire());
});

test('un import invalide est refusé sans écraser l’existant', () => {
  const stockage = creerStockage(supportFactice());
  stockage.definirDateExamen('2026-10-19');
  assert.equal(stockage.importer('n importe quoi'), false);
  assert.equal(stockage.lire().dateExamen, '2026-10-19');
});

test('la réinitialisation vide la progression', () => {
  const stockage = creerStockage(supportFactice());
  stockage.ecrireItem('c1-01', { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'su', derniereVue: '2026-09-18', echecs: 0 });
  stockage.reinitialiser();
  assert.deepEqual(stockage.lire().items, {});
});

test('un support indisponible ne fait pas échouer l’écriture', () => {
  const support = { getItem: () => null, setItem: () => { throw new Error('quota'); }, removeItem: () => {} };
  const stockage = creerStockage(support);
  assert.doesNotThrow(() => stockage.definirTheme('sombre'));
});
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `node --test tests/stockage.test.js`
Expected: FAIL — `Cannot find module .../site/assets/stockage.js`

- [ ] **Step 3: Écrire l'implémentation**

Créer `site/assets/stockage.js` :

```javascript
/**
 * Persistance de la progression.
 *
 * Le support est injecte plutot qu'importe depuis window : le module se teste
 * sans navigateur, et un navigateur en navigation privee -- ou un quota plein --
 * degrade l'experience sans casser l'application.
 */

export const CLE = 'uc1-anatomie-v1';

const ETAT_VIERGE = { dateExamen: null, theme: 'auto', items: {} };

function estEtatValide(valeur) {
  return Boolean(valeur)
    && typeof valeur === 'object'
    && typeof valeur.items === 'object'
    && valeur.items !== null
    && !Array.isArray(valeur.items);
}

export function creerStockage(support) {
  function lire() {
    try {
      const brut = support.getItem(CLE);
      if (!brut) return { ...ETAT_VIERGE, items: {} };
      const valeur = JSON.parse(brut);
      return estEtatValide(valeur) ? { ...ETAT_VIERGE, ...valeur } : { ...ETAT_VIERGE, items: {} };
    } catch {
      return { ...ETAT_VIERGE, items: {} };
    }
  }

  function ecrire(etat) {
    try {
      support.setItem(CLE, JSON.stringify(etat));
    } catch {
      // Quota plein ou stockage interdit : la session reste utilisable,
      // seule la memorisation entre visites est perdue.
    }
  }

  function modifier(transformation) {
    const etat = lire();
    transformation(etat);
    ecrire(etat);
  }

  return {
    lire,
    ecrireItem(id, item) { modifier((etat) => { etat.items[id] = item; }); },
    definirDateExamen(iso) { modifier((etat) => { etat.dateExamen = iso; }); },
    definirTheme(nom) { modifier((etat) => { etat.theme = nom; }); },
    exporter() { return JSON.stringify(lire(), null, 2); },
    importer(json) {
      try {
        const valeur = JSON.parse(json);
        if (!estEtatValide(valeur)) return false;
        ecrire({ ...ETAT_VIERGE, ...valeur });
        return true;
      } catch {
        return false;
      }
    },
    reinitialiser() { try { support.removeItem(CLE); } catch { /* sans effet */ } },
  };
}
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `node --test tests/stockage.test.js`
Expected: PASS — 8 tests

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add site/assets/stockage.js tests/stockage.test.js
git commit -m "feat: persistance de la progression"
```

---

### Task 8: Logique d'exercice

**Files:**
- Create: `site/assets/exercices.js`
- Create: `tests/exercices.test.js`

**Interfaces:**
- Consumes: rien. Module pur, autonome, sans DOM.
- Produces:
  - `appliquerAutoEvaluation(item, verdict: 'rate'|'difficile'|'su', aujourdHui) -> Item` — renvoie un nouvel item, sans mutation.
  - `corrigerQuestion(question, indexChoisi) -> {juste: boolean, bonne: number, expl: string}`
  - `normaliser(saisie: string) -> string` — pour comparer une légende saisie au libellé attendu.
  - `verifierPastille(pastille, saisie) -> boolean`
  - `itemsDuCours(cours) -> Item[]` — aplatit cartes, questions et pastilles en items planifiables.

  Consommé par les tâches 9 et 10.

- [ ] **Step 1: Écrire le test qui échoue**

Créer `tests/exercices.test.js` :

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  appliquerAutoEvaluation, corrigerQuestion, normaliser, verifierPastille, itemsDuCours,
} from '../site/assets/exercices.js';

const base = { id: 'c1-01', chapitre: 1, type: 'carte', statut: 'jamais', derniereVue: null, echecs: 0 };

test('un verdict « su » enregistre la date et remet les échecs à zéro', () => {
  const apres = appliquerAutoEvaluation({ ...base, echecs: 2 }, 'su', '2026-09-18');
  assert.equal(apres.statut, 'su');
  assert.equal(apres.derniereVue, '2026-09-18');
  assert.equal(apres.echecs, 0);
});

test('un verdict « raté » incrémente le compteur d’échecs', () => {
  const apres = appliquerAutoEvaluation({ ...base, echecs: 1 }, 'rate', '2026-09-18');
  assert.equal(apres.statut, 'rate');
  assert.equal(apres.echecs, 2);
});

test('l’auto-évaluation ne modifie pas l’item d’origine', () => {
  const avant = { ...base };
  appliquerAutoEvaluation(avant, 'su', '2026-09-18');
  assert.deepEqual(avant, base);
});

test('la correction indique la bonne réponse et son explication', () => {
  const question = { id: 'q1-01', choix: ['A', 'B', 'C'], bonne: 1, expl: 'Parce que B.' };
  assert.deepEqual(corrigerQuestion(question, 1), { juste: true, bonne: 1, expl: 'Parce que B.' });
  assert.deepEqual(corrigerQuestion(question, 0), { juste: false, bonne: 1, expl: 'Parce que B.' });
});

test('la normalisation ignore casse, accents, tirets et espaces', () => {
  assert.equal(normaliser('  Plan Frontal '), normaliser('plan frontal'));
  assert.equal(normaliser('Crânial'), normaliser('cranial'));
  assert.equal(normaliser('scapulo-humérale'), normaliser('scapulo humerale'));
});

test('une légende saisie est acceptée malgré les accents manquants', () => {
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, 'cranial'), true);
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, 'caudal'), false);
});

test('une saisie vide est refusée', () => {
  assert.equal(verifierPastille({ n: 1, t: 'Crânial' }, '   '), false);
});

test('le cours est aplati en items planifiables', () => {
  const cours = {
    chapitres: [{
      num: 1,
      cartes: [{ id: 'c1-01' }],
      quiz: [{ id: 'q1-01' }],
      planches: [{ id: 'p1', pastilles: [{ n: 1, t: 'A' }, { n: 2, t: 'B' }] }],
      muscles: [],
    }],
  };
  const items = itemsDuCours(cours);
  assert.deepEqual(items.map((i) => i.id), ['c1-01', 'q1-01', 'p1#1', 'p1#2']);
  assert.deepEqual([...new Set(items.map((i) => i.type))], ['carte', 'quiz', 'pastille']);
  assert.ok(items.every((i) => i.chapitre === 1 && i.statut === 'jamais'));
});
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `node --test tests/exercices.test.js`
Expected: FAIL — `Cannot find module .../site/assets/exercices.js`

- [ ] **Step 3: Écrire l'implémentation**

Créer `site/assets/exercices.js` :

```javascript
/**
 * Logique des trois exercices : carte, question, pastille muette.
 *
 * Fonctions pures : elles prennent un etat et en renvoient un nouveau, sans
 * toucher au DOM et sans muter leurs arguments. Le rendu vit dans interface.js.
 */

const VERDICTS = new Set(['rate', 'difficile', 'su']);

export function appliquerAutoEvaluation(item, verdict, aujourdHui) {
  if (!VERDICTS.has(verdict)) return item;
  return {
    ...item,
    statut: verdict,
    derniereVue: aujourdHui,
    echecs: verdict === 'rate' ? item.echecs + 1 : 0,
  };
}

export function corrigerQuestion(question, indexChoisi) {
  return {
    juste: indexChoisi === question.bonne,
    bonne: question.bonne,
    expl: question.expl,
  };
}

export function normaliser(saisie) {
  return (saisie || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[-'’]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function verifierPastille(pastille, saisie) {
  const attendu = normaliser(pastille.t);
  const propose = normaliser(saisie);
  return propose.length > 0 && propose === attendu;
}

export function itemsDuCours(cours) {
  const items = [];
  for (const chapitre of cours.chapitres) {
    const neuf = (id, type) => ({
      id, type, chapitre: chapitre.num, statut: 'jamais', derniereVue: null, echecs: 0,
    });
    for (const carte of chapitre.cartes || []) items.push(neuf(carte.id, 'carte'));
    for (const question of chapitre.quiz || []) items.push(neuf(question.id, 'quiz'));
    for (const planche of chapitre.planches || []) {
      for (const pastille of planche.pastilles || []) {
        items.push(neuf(`${planche.id}#${pastille.n}`, 'pastille'));
      }
    }
  }
  return items;
}
```

- [ ] **Step 4: Lancer les tests pour vérifier qu'ils passent**

Run: `node --test tests/*.test.js`
Expected: PASS — planificateur, stockage et exercices

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add site/assets/exercices.js tests/exercices.test.js
git commit -m "feat: logique des exercices"
```

---

### Task 9: Interface

**Files:**
- Create: `site/assets/interface.js`
- Create: `site/assets/app.js`
- Modify: `gabarits/chapitre.html` (barre d'actions, bascule de mode, réglages)

**Interfaces:**
- Consumes: `planificateur.js`, `stockage.js`, `exercices.js` (tâches 6, 7, 8).
- Produits: `demarrer(document, support) -> void`, appelé par `app.js`. Seul module autorisé à toucher au DOM.

Comportements à câbler :

| Élément | Comportement |
|---|---|
| Onglets | Clic ou flèches ←/→ : bascule `hidden` sur les `.volet`. `aria-selected` tenu à jour. |
| Carte | Clic ou `Espace` : retire `data-etat="cachee"` de `.carte__r`, puis affiche les trois boutons de verdict. |
| Verdict | Clic ou touches `1` `2` `3` : `appliquerAutoEvaluation`, puis `ecrireItem`. |
| Quiz | Clic sur `.choix` : `corrigerQuestion`, marque le bon et le mauvais choix, révèle l'explication. |
| Planche | Touche `M` ou bouton : bascule `data-mode` entre `legende` et `muet`. En mode muet, un champ par pastille et un bouton de vérification. |
| Thème | Bouton à trois positions : auto, clair, sombre. Écrit `data-theme` sur `<html>` et persiste via `definirTheme`. |
| Date d'examen | `<input type="date">` dans les réglages ; alimente `intervalleDeBase`. |
| Export / import | Bouton d'export (téléchargement du JSON) et champ d'import. |

- [ ] **Step 1: Écrire le gabarit et le module**

Ajouter à `gabarits/chapitre.html` la barre d'actions ancrée (`<div class="actions">` avec les trois boutons de verdict), le bouton de bascule de planche et le panneau de réglages.

Écrire `site/assets/interface.js` en respectant la séparation : il lit l'état via `stockage`, calcule via `planificateur` et `exercices`, et n'implémente aucune règle métier lui-même. Tout gestionnaire d'événement se termine par une écriture dans le stockage.

Écrire `site/assets/app.js` :

```javascript
import { demarrer } from './interface.js';

demarrer(document, window.localStorage);
```

- [ ] **Step 2: Vérifier le rendu réel**

```bash
cd "/home/valentin/Téléchargements/revision-anatomie" && python3 outils/construire.py && python3 -m http.server 8765 --directory site
```

Ouvrir `http://localhost:8765/chapitre-1.html`. Contrôler, dans l'ordre : aucune réponse visible à l'ouverture ; `Espace` retourne la carte ; `1` `2` `3` enregistrent un verdict ; le rechargement conserve la progression ; `M` bascule la planche en mode muet ; les flèches changent d'onglet ; le focus clavier est visible partout.

- [ ] **Step 3: Vérifier la dégradation sans JavaScript**

Désactiver JavaScript dans le navigateur, recharger. Attendu : le contenu du cours et les questions restent lisibles, les onglets s'affichent tous empilés. Rien ne disparaît.

- [ ] **Step 4: Commit** *(si autorisé)*

```bash
git add site/assets/interface.js site/assets/app.js gabarits/chapitre.html
git commit -m "feat: interface et interactions"
```

---

### Task 10: Accueil et séance du jour

**Files:**
- Create: `gabarits/accueil.html`
- Modify: `outils/construire.py` (rendre l'accueil)
- Modify: `site/assets/interface.js` (composer et dérouler la séance)
- Modify: `tests/test_construire.py` (couvrir l'accueil)

**Interfaces:**
- Consumes: `composerSeance` (tâche 6), `itemsDuCours` (tâche 8), `stockage` (tâche 7).
- Produces: `site/index.html`.

- [ ] **Step 1: Étendre le test**

Ajouter à `tests/test_construire.py` :

```python
def test_l_accueil_est_ecrit():
    assert (RACINE / "site" / "index.html").exists()


def test_l_accueil_propose_la_seance_du_jour():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'id="seance"' in accueil


def test_l_accueil_liste_les_chapitres_disponibles():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert "chapitre-1.html" in accueil


def test_l_accueil_demande_la_date_d_examen():
    accueil = (RACINE / "site" / "index.html").read_text(encoding="utf-8")
    assert 'type="date"' in accueil
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `python3 -m pytest tests/test_construire.py -v`
Expected: FAIL — `site/index.html` absent

- [ ] **Step 3: Écrire l'accueil**

`gabarits/accueil.html` : trois blocs dans l'ordre de la spec §4.1 — la séance du jour (bouton unique, `id="seance"`), la progression (un anneau SVG par chapitre), la liste des chapitres. Puis les réglages : `<input type="date">` pour l'examen, bascule de thème, export, import, réinitialisation.

Étendre `construire()` d'une fonction `_rendre_accueil(gabarit, cours)` et écrire `site/index.html`.

Dans `interface.js`, câbler le bouton de séance : lire l'état, fusionner avec `itemsDuCours` (les items inconnus du stockage démarrent à `jamais`), calculer `intervalleDeBase` depuis la date d'examen, appeler `composerSeance`, puis dérouler les items un par un en réutilisant les mêmes rendus que dans les pages chapitre.

- [ ] **Step 4: Lancer la suite complète**

Run: `python3 -m pytest tests/ -v && node --test tests/*.test.js`
Expected: PASS — Python et JavaScript

- [ ] **Step 5: Commit** *(si autorisé)*

```bash
git add gabarits/accueil.html outils/construire.py site/assets/interface.js tests/test_construire.py site/index.html
git commit -m "feat: accueil et seance du jour"
```

---

### Task 11: Recette

**Files:**
- Create: `README.md`
- Modify: aucun code, sauf correctifs issus de la recette.

- [ ] **Step 1: Lancer toute la suite**

```bash
cd "/home/valentin/Téléchargements/revision-anatomie"
python3 -m pytest tests/ -v && node --test tests/*.test.js
```

Expected: PASS des deux côtés.

- [ ] **Step 2: Recette visuelle**

Servir le site, puis contrôler dans un navigateur, en notant chaque écart :

| Contrôle | Attendu |
|---|---|
| Largeur 360 px | Une colonne, aucun débordement horizontal, actions atteignables au pouce |
| Largeur 1280 px | Deux colonnes, longueur de ligne ≤ 68 caractères |
| Thème clair et thème sombre | Les deux lisibles, bascule persistée après rechargement |
| Mouvement réduit activé | Aucune animation |
| Navigation au clavier seul | Tout atteignable, focus toujours visible |
| Première ouverture d'un chapitre | Aucune réponse visible avant tentative |
| Impression de la page (aperçu) | Lisible en noir et blanc, plans distingués par libellé |
| Relecture des distracteurs | Chaque mauvaise réponse est une confusion réellement présente dans le cours (plan voisin, mouvement antagoniste, articulation voisine) — aucun terme inventé |
| Séance du jour chronométrée | Une séance complète se termine en 20 minutes environ ; ajuster `taille` dans `composerSeance` si l'écart dépasse 5 minutes |

- [ ] **Step 3: Écrire le README**

`README.md` : ce qu'est le projet, la règle de fidélité au PDF source, comment régénérer le site (`python3 outils/construire.py`), comment lancer les tests, où vivent la spec et les plans, et la limite de confidentialité de GitHub Pages.

- [ ] **Step 4: Commit** *(si autorisé)*

```bash
git add README.md
git commit -m "docs: README du projet"
```

---

## Ce que ce plan ne couvre pas

- **Chapitres 2 à 7** — plan suivant, une fois le rendu du chapitre 1 validé par Valentin.
- **Génération des PDF** (`outils/fiches.py`, `outils/pdf.py`) — troisième plan.
- **Déploiement GitHub Pages** (dépôt privé, branche `gh-pages`, `robots.txt`) — troisième plan.
