# Projet Othello — Rapport

**Auteur principal (dev A) : Théo Cornu**
**Binôme (dev B) : [NOM — À COMPLÉTER]**

**Date de rendu : [À COMPLÉTER]**
**Langage : Python 3**
**Version du contrat : 1.1**

---

## Sommaire

1. Introduction
2. Analyse
   1. Modélisation du jeu
   2. Structures de données
   3. Moteur de règles
   4. Fonctions d'évaluation
   5. Algorithmes de recherche
3. Validation expérimentale
   1. Protocole et critères
   2. Tests de conformité
   3. Comparaison des algorithmes
   4. Comparaison des stratégies
   5. Humain contre IA
4. Discussion
5. Conclusion
6. Bibliographie
7. Annexes

---

## 1. Introduction

Othello est un jeu de plateau à deux joueurs, à information parfaite et à somme nulle.
Le projet consiste à développer une intelligence artificielle capable de jouer :

- contre un joueur humain ;
- contre une autre IA.

Le travail est découpé en deux modules :

- **module A** (Théo Cornu) : moteur de règles, fonctions d'évaluation, harnais de matchs, interface ;
- **module B** ([NOM — À COMPLÉTER]) : algorithmes de recherche et optimisation.

L'objectif est de comparer plusieurs stratégies d'évaluation et plusieurs algorithmes
de recherche sur des critères numériques (temps, nœuds, profondeur).

---

## 2. Analyse

### 2.1 Modélisation du jeu

Le plateau est un damier de 64 cases, indexées de 0 à 63 selon
`index = 8 * ligne + colonne`. Chaque case contient :

- `0` : vide ;
- `1` : pion noir ;
- `2` : pion blanc.

Convention de notation : colonnes `a` à `h`, lignes `1` à `8`.
Ainsi `a1 = 0`, `h8 = 63`.

Les blancs commencent la partie, conformément au sujet.
La position de départ est fixée : quatre pions au centre.

### 2.2 Structures de données

**Plateau.** Le plateau est représenté par deux entiers (bitboards) :

- `black` : bit `i` à 1 si la case `i` contient un pion noir ;
- `white` : bit `i` à 1 si la case `i` contient un pion blanc.

Cette représentation permet des tests de présence et des retournements rapides
à l'aide d'opérations bit à bit.

**État.** `State` est un objet immuable contenant :

| Champ | Type | Rôle |
|---|---|---|
| `black` | `int` | bitboard des noirs |
| `white` | `int` | bitboard des blancs |
| `player` | `int` | joueur au trait |
| `move_number` | `int` | nombre de coups posés |
| `hash` | `int` | hash Zobrist de la position |

L'immuabilité garantit qu'un état n'est jamais modifié par accident : chaque
coup produit un nouvel état.

**Hash Zobrist.** Une table de nombres aléatoires associe une valeur à chaque
couple (case, couleur), plus une clé pour le joueur au trait. Le hash permet
d'identifier une position dans la table de transposition.

### 2.3 Moteur de règles (module A)

Le moteur `OthelloEngine` fournit :

- `initial_state()` : position de départ ;
- `legal_moves(state)` : coups légaux, `[PASS]` si le joueur doit passer,
  `[]` si la partie est terminée ;
- `apply_move(state, move)` : applique un coup et retourne un nouvel état ;
- `is_terminal(state)` : détecte la fin de partie ;
- `score(state)` : retourne `(noirs, blancs)` ;
- `mobility(state, player)` : nombre de coups légaux d'un joueur ;
- `perft(state, depth)` : comptage de positions pour valider les règles.

**Retournements.** Pour chaque direction (8 directions), le moteur parcourt les
pions adverses consécutifs et retourne la ligne si elle se termine par un pion
du joueur.

**Passe.** Si le joueur au trait n'a aucun coup mais que l'adversaire en a un,
`legal_moves` renvoie `[PASS]`. Si aucun des deux ne peut jouer, la partie est
terminée.

### 2.4 Fonctions d'évaluation (module A)

Une évaluation est une fonction `eval(state, player) -> float` :

- positive si la position est favorable à `player` ;
- zéro-somme : `eval(s, 1) = -eval(s, 2)` ;
- bornée : `|eval| < 1000`.

Les positions terminales sont traitées par l'agent, pas par l'évaluateur.

#### Stratégie positionnelle

Elle utilise une grille de poids statiques :

- les coins valent **+100** : ils ne peuvent jamais être retournés ;
- les cases adjacentes aux coins ont des poids négatifs, car elles offrent
  des coups à l'adversaire ;
- les cases centrales ont des poids faibles.

L'évaluation est la différence entre la somme des poids des pions du joueur
et celle des pions adverses.

**Justification.** Contrôler les coins est un principe fondamental d'Othello :
un coin ne peut pas être repris. À l'inverse, occuper les cases voisines d'un
coin donne à l'adversaire l'occasion de prendre ce coin.

#### Stratégie absolue

Elle calcule simplement la différence du nombre de pions :

`eval = pions(player) - pions(adversaire)`.

**Justification.** En fin de partie, le nombre de pions est le critère réel de
victoire. Cette stratégie est donc pertinente dans les derniers coups.

#### Stratégie de mobilité

Elle combine :

- la différence du nombre de coups légaux ;
- un bonus pour les coins ;
- la différence du nombre de pions.

**Justification.** À Othello, réduire les options de l'adversaire est souvent
plus important que retourner des pions. Un joueur avec peu de coups est
contraint de jouer là où il ne le souhaite pas.

#### Stratégie mixte

Le jeu est divisé en trois phases :

1. **Début de partie** (`move_number < 22`) : évaluation positionnelle ;
2. **Milieu de partie** : évaluation de mobilité ;
3. **Fin de partie** (`empties <= 12`) : évaluation absolue.

**Justification.** Les priorités changent au cours d'une partie : la structure
positionnelle domine au début, la mobilité au milieu, et le nombre final de
pions à la fin. La stratégie mixte adapte l'évaluation à la phase.

### 2.5 Algorithmes de recherche (module B)

> **[DEV B — À COMPLÉTER]**
> Décrire ici : Min-Max, Alpha-Bêta, NegaMax, table de transposition,
> approfondissement itératif, gestion du time-out, réutilisation de l'arbre.

L'agent reçoit une fonction d'évaluation en paramètre. Il ne connaît pas son
implémentation interne : c'est l'interface entre les modules A et B.

**Interface.**

```python
class Agent:
    def __init__(self, engine, evaluator, *, algo="alphabeta",
                 max_depth=6, time_budget_ms=1000, ...)
    def choose_move(self, state) -> MoveResult
```

`MoveResult` contient : `move`, `eval_score`, `nodes`, `evals`, `time_ms`,
`depth_reached`, `timed_out`, `tt_hits`.

**Indépendance des agents.** Chaque instance possède sa propre table de
transposition et son propre historique. Deux IA qui s'affrontent ont donc des
arbres de raisonnement distincts, comme exigé par le sujet.

---

## 3. Validation expérimentale

### 3.1 Protocole et critères

Les critères retenus sont :

- **temps de calcul** par coup (ms) ;
- **nombre de nœuds générés** ;
- **profondeur atteinte** ;
- **nombre d'évaluations** ;
- **score final** et **vainqueur**.

Ces critères sont mesurés dans les mêmes conditions : même profondeur maximale,
même budget temps, même moteur. Les couleurs sont alternées pour éviter un biais.

### 3.2 Tests de conformité

| Test | Résultat attendu | Résultat obtenu |
|---|---|---|
| Perft profondeur 1 | 4 | 4 |
| Perft profondeur 2 | 12 | 12 |
| Perft profondeur 3 | 56 | 56 |
| Perft profondeur 4 | 244 | 244 |
| Perft profondeur 5 | 1396 | 1396 |
| Perft profondeur 6 | 8200 | 8200 |
| Antisymétrie des évaluations | `eval(s,1) = -eval(s,2)` | OK |
| Bornes | `|eval| < 1000` | OK |
| Hash recalculé | identique | OK |

> **[DEV B — À COMPLÉTER]** Alpha-Bêta = Min-Max, NegaMax = Min-Max,
> TT activée/désactivée, respect du time-out.

### 3.3 Comparaison des algorithmes (module B)

> **[DEV B — À COMPLÉTER]**
> Remplir avec les mesures : Min-Max vs Alpha-Bêta vs NegaMax.
> Mêmes positions, même profondeur, même évaluation.

| Algorithme | Temps moyen (ms) | Nœuds moyens | Profondeur |
|---|---|---|---|
| Min-Max | | | |
| Alpha-Bêta | | | |
| NegaMax | | | |

### 3.4 Comparaison des stratégies (module A)

Protocole : chaque stratégie affronte les trois autres, deux parties par
confrontation (couleurs alternées), profondeur 3, budget 100 ms, soit 24 parties.

Commande : `python campaigns.py`.

| Stratégie | Victoires | Défaites | Nulles |
|---|---|---|---|
| Positionnelle | 10 | 2 | 0 |
| Absolue | 1 | 11 | 0 |
| Mobilité | 9 | 3 | 0 |
| Mixte | 4 | 8 | 0 |

**Tableau des confrontations directes** (score de la stratégie en ligne)

| Noir \ Blanc | Positionnelle | Absolue | Mobilité | Mixte |
|---|---|---|---|---|
| Positionnelle | — | 1-1 | 1-1 | 2-0 |
| Absolue | 0-2 | — | 0-2 | 0-2 |
| Mobilité | 0-2 | 2-0 | — | 2-0 |
| Mixte | 0-2 | 2-0 | 0-2 | — |

**Lecture.** Les stratégies positionnelle et de mobilité dominent, la stratégie
absolue est clairement la plus faible sur des parties complètes : privilégier
le nombre de pions trop tôt est contre-productif. La stratégie mixte est
compétitive mais perd ses confrontations directes contre la positionnelle.

### 3.5 Humain contre IA

> **[À COMPLÉTER]**
> Faire jouer un humain contre chaque stratégie, noter le résultat et le
> ressenti (difficulté perçue, coups surprenants).

| Stratégie IA | Résultat humain | Score | Commentaire |
|---|---|---|---|
| Positionnelle | | | |
| Absolue | | | |
| Mobilité | | | |
| Mixte | | | |

**Figure 1.** Évolution du score d'évaluation au cours d'une partie humain vs IA.
> Insérer ici la figure générée à partir de `runs/games/<id>.txt`.

---

## 4. Discussion

> **[ENSEMBLE — À COMPLÉTER]**

Points à traiter :

- efficacité comparée des stratégies ;
- apport de la mobilité et des coins ;
- position du joueur humain parmi les stratégies ;
- apport de l'élagage Alpha-Bêta ;
- limites : profondeur, temps, absence d'apprentissage ;
- perspectives : apprentissage par renforcement, ouverture, meilleure
  réutilisation de l'arbre.

---

## 5. Conclusion

> **[ENSEMBLE — À COMPLÉTER]**

Rappeler :

- les objectifs du projet ;
- ce qui a été réalisé ;
- les résultats principaux ;
- les limites et perspectives.

---

## 6. Bibliographie

1. Rosenbloom, P. S. (1982). *A world-championship-level Othello program.*
   Artificial Intelligence, 19(3), 279–320.
2. Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern
   Approach* (4th ed.). Pearson.
3. Knuth, D. E., & Moore, R. W. (1975). *An analysis of alpha-beta pruning.*
   Artificial Intelligence, 6(4), 293–326.
4. Zobrist, A. L. (1970). *A new hashing method with application for game
   playing.* Technical Report, University of Wisconsin.
5. Allis, L. V. (1994). *Searching for Solutions in Games and Artificial
   Intelligence.* PhD thesis, University of Limburg.

---

## 7. Annexes

### Annexe A — Code du module A

- `config.py`
- `engine.py`
- `evals.py`
- `human.py`
- `players.py`
- `harness.py`
- `cli.py`
- `tests.py`
- `web/server.py`
- `web/index.html`

### Annexe B — Code du module B

- `agent.py`

> **[DEV B — À COMPLÉTER]** Ajouter les fichiers ou extraits supplémentaires.

### Annexe C — Exemples de sorties

- `runs/moves.csv`
- `runs/matches.csv`
- `runs/games/<game_id>.txt`

---

## Liste des figures

| Figure | Description |
|---|---|
| Figure 1 | Score d'évaluation au cours d'une partie humain vs IA |
| Figure 2 | [À COMPLÉTER] Comparaison temps/nœuds des algorithmes |
| Figure 3 | [À COMPLÉTER] Résultats des stratégies |

---

## Répartition du travail

| Partie | Rédacteur | Relecteur |
|---|---|---|
| Introduction, règles, modélisation, moteur | Théo Cornu | [DEV B] |
| Évaluations (4 stratégies) | Théo Cornu | [DEV B] |
| Recherche (Min-Max, Alpha-Bêta, NegaMax, TT) | [DEV B] | Théo Cornu |
| Validation algorithmes | [DEV B] | Théo Cornu |
| Validation stratégies, humain vs IA | Théo Cornu | [DEV B] |
| Discussion, conclusion | Ensemble | — |
| Annexe code, bibliographie, figures | Chacun | — |
