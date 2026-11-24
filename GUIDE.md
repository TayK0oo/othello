# Guide complet — Projet Othello

Ce guide explique le projet de bout en bout, pour pouvoir le présenter à l'oral.

---

## 1. Le but du projet

Faire une IA qui joue à Othello :

- contre un humain ;
- contre une autre IA.

Et comparer plusieurs façons d'évaluer une position et plusieurs algorithmes
de recherche, avec des mesures (temps, nœuds, profondeur).

---

## 2. Rappel des règles d'Othello

- Plateau 8×8, 64 cases.
- Deux joueurs : noirs et blancs.
- Les blancs commencent.
- Un coup est valide s'il **encadre** au moins un pion adverse entre le pion
  posé et un pion de sa couleur.
- Les pions encadrés sont **retournés**.
- Si un joueur n'a aucun coup, il **passe**.
- La partie se termine quand le plateau est plein ou quand aucun des deux
  joueurs ne peut jouer.
- Le gagnant est celui qui a le plus de pions.

---

## 3. Vue d'ensemble des fichiers

| Fichier | Rôle |
|---|---|
| `config.py` | Toutes les constantes et valeurs par défaut. |
| `players_config.json` | Profils de joueurs (humain, IA mixte, etc.). |
| `engine.py` | Règles du jeu : coups légaux, retournements, passe, score. |
| `evals.py` | Les 4 stratégies d'évaluation. |
| `agent.py` | L'IA : recherche Alpha-Bêta, cache, time-out. |
| `human.py` | Le joueur humain au clavier. |
| `players.py` | Fabrique de joueurs à partir des profils. |
| `harness.py` | Déroule une partie et écrit les résultats. |
| `cli.py` | Lance des parties en terminal. |
| `campaigns.py` | Lance des tournois entre stratégies. |
| `tests.py` | Tests de conformité. |
| `web/server.py` + `web/index.html` | Interface web pour jouer et voir les infos. |
| `RAPPORT.md/.docx/.pdf` | Rapport du projet. |

---

## 4. Le moteur (`engine.py`)

### Représentation du plateau

Chaque joueur a un **bitboard** : un entier de 64 bits.

- bit `i` à 1 = il y a un pion sur la case `i`.

Exemple : `black = 0b...` signifie que certaines cases ont un pion noir.

Avantages :

- tester une case = une opération bit à bit ;
- retourner des pions = opérations rapides ;
- peu de mémoire.

### L'état `State`

Un état contient :

- `black` : bitboard noir ;
- `white` : bitboard blanc ;
- `player` : joueur au trait (1 noir, 2 blanc) ;
- `move_number` : nombre de coups posés ;
- `hash` : identifiant unique de la position (Zobrist).

L'état est **immuable** : on ne le modifie jamais, on en crée un nouveau.

### Les fonctions importantes

- `initial_state()` : position de départ (blancs commencent).
- `legal_moves(state)` : liste des coups valides.
  - `[]` = fin de partie ;
  - `[PASS]` = le joueur doit passer.
- `apply_move(state, move)` : applique le coup et retourne un nouvel état.
  - lève une erreur si le coup est illégal ;
  - `PASS` change seulement le joueur.
- `is_terminal(state)` : vrai si la partie est finie.
- `score(state)` : `(nombre de noirs, nombre de blancs)`.
- `mobility(state, player)` : nombre de coups possibles d'un joueur.
- `perft(state, depth)` : compte les positions atteignables.
  - sert à vérifier que les règles sont correctes.

### Le hash Zobrist

On associe un nombre aléatoire à chaque couple (case, couleur), plus un pour
le joueur au trait. Le hash de la position est le XOR de ces nombres.

Cela donne un identifiant rapide de la position, utilisé par le cache de l'IA.

---

## 5. Les évaluations (`evals.py`)

Une évaluation donne un score à une position pour un joueur :

```python
eval(state, player) -> float
```

Règles :

- positif = bon pour `player` ;
- négatif = mauvais ;
- zéro-somme : `eval(s, 1) = -eval(s, 2)` ;
- borné entre -1000 et 1000.

### Positionnelle

On donne un poids à chaque case :

- coins = +100 (jamais retournés) ;
- cases proches des coins = négatif (donnent des coups à l'adversaire) ;
- centre = faible.

Score = somme des poids de mes pions - somme des poids adverses.

### Absolue

Score = mes pions - pions adverses.

Simple, mais pertinente seulement en fin de partie.

### Mobilité

Score =

- mes coups possibles - coups adverses ;
- + bonus pour les coins ;
- + différence de pions.

Idée : priver l'adversaire de coups est souvent plus important que retourner
des pions.

### Mixte

Trois phases :

1. début (`move_number < 22`) → positionnelle ;
2. milieu → mobilité ;
3. fin (`empties <= 12`) → absolue.

C'est la stratégie qui adapte l'évaluation au moment de la partie.

---

## 6. L'IA (`agent.py`)

### Le principe

L'IA ne connaît pas le calcul de l'évaluation : elle reçoit une fonction
`evaluator` en paramètre. C'est l'interface entre le module A (évaluations)
et le module B (recherche).

### Alpha-Bêta

On explore l'arbre des coups :

- je maximise mon score ;
- l'adversaire minimise le mien.

Alpha-Bêta coupe les branches inutiles :

- `alpha` = meilleur score déjà garanti pour moi ;
- `beta` = meilleur score déjà garanti pour l'adversaire ;
- si `beta <= alpha`, on arrête d'explorer cette branche.

Résultat : même coup que Min-Max, mais beaucoup moins de nœuds.

### Approfondissement itératif

On cherche d'abord à profondeur 1, puis 2, puis 3, etc.

- si le temps manque, on garde le meilleur coup de la dernière profondeur
  terminée ;
- on a toujours un coup légal à jouer.

### Table de transposition

Un cache `hash -> (position, profondeur, score, coup)`.

Si on retombe sur une position déjà analysée, on réutilise le résultat.

Chaque agent a **son propre cache** : deux IA ne partagent rien.

### Time-out

`time_budget_ms` est le temps maximum par coup.

- l'agent vérifie l'horloge pendant la recherche ;
- il renvoie toujours un coup légal ;
- le harnais tolère 10 % de dépassement.

### `MoveResult`

Contient :

- `move` : coup choisi ;
- `eval_score` : score de la racine ;
- `nodes` : nœuds générés ;
- `evals` : appels à l'évaluation ;
- `time_ms` : temps de calcul ;
- `depth_reached` : profondeur atteinte ;
- `timed_out` : coup coupé par le temps ;
- `tt_hits` : succès du cache.

---

## 7. Le déroulement d'une partie (`harness.py`)

`play_game(engine, black, white, game_id)` :

1. appelle `new_game()` sur les deux joueurs ;
2. tant que la partie n'est pas finie :
   - récupère les coups légaux ;
   - applique les passes automatiquement ;
   - demande un coup au joueur courant ;
   - vérifie la légalité ;
   - applique le coup ;
3. calcule le gagnant ;
4. écrit les résultats.

### Sorties

- `runs/moves.csv` : un coup par ligne ;
- `runs/matches.csv` : une partie par ligne ;
- `runs/games/<id>.txt` : rejeu de la partie avec scores d'évaluation.

---

## 8. Les joueurs (`players.py`, `human.py`)

- `HumanPlayer` : lit un coup au clavier (`d3` ou `pass`).
- `Agent` : IA.
- `players.py` : construit un joueur à partir d'un profil JSON.

Exemple de profil :

```json
"mixed_ai": {
  "type": "ai",
  "strategy": "mixed",
  "algo": "alphabeta",
  "depth": 6,
  "budget_ms": 1000
}
```

---

## 9. Le CLI (`cli.py`)

```bash
python cli.py human mixed_ai
python cli.py positional_ai mobility_ai 5
```

- argument 1 = profil des noirs ;
- argument 2 = profil des blancs ;
- argument 3 = nombre de parties.

---

## 10. Les campagnes (`campaigns.py`)

```bash
python campaigns.py
```

Chaque stratégie affronte les autres, couleurs alternées.

Résultats obtenus (24 parties, profondeur 3, 100 ms) :

| Stratégie | Victoires | Défaites | Nulles |
|---|---|---|---|
| Positionnelle | 10 | 2 | 0 |
| Absolue | 1 | 11 | 0 |
| Mobilité | 9 | 3 | 0 |
| Mixte | 4 | 8 | 0 |

Conclusion : la positionnelle et la mobilité dominent ; l'absolue est la plus
faible car elle privilégie le nombre de pions trop tôt.

---

## 11. L'interface web (`web/`)

```bash
python web/server.py 8000
```

Puis http://localhost:8000.

- plateau cliquable ;
- coups légaux surlignés ;
- choix des profils noir/blanc ;
- bouton « Coup IA » ;
- auto-play IA vs IA ;
- bouton « Pause » ;
- infos : coup, évaluation, nœuds, évals, temps, profondeur.

---

## 12. Les tests (`tests.py`)

```bash
python tests.py
```

### Perft

Compte les positions atteignables :

| Profondeur | Attendu |
|---|---|
| 1 | 4 |
| 2 | 12 |
| 3 | 56 |
| 4 | 244 |
| 5 | 1396 |
| 6 | 8200 |

Si les nombres correspondent, les règles de base sont correctes.

### Autres tests

- symétrie : `eval(s,1) = -eval(s,2)` ;
- bornes : `|eval| < 1000` ;
- hash : recalculé identique.

---

## 13. Le contrat (`CONTRACT.md`)

Il définit les interfaces entre :

- **module A** (Théo) : moteur, évaluations, humain, harnais ;
- **module B** (binôme) : recherche.

Point clé : une seule fonction `eval(state, player)` relie les deux.

Règles :

- un agent = un cache propre ;
- l'agent n'accède qu'à l'API publique du moteur ;
- toute modification du contrat = accord des deux.

---

## 14. Ce qu'il faut savoir dire à l'oral

### « Pourquoi des bitboards ? »

Parce que les opérations sur les bits sont rapides et compactes : tester une
case, retourner des pions, calculer un hash.

### « Pourquoi Alpha-Bêta ? »

Il donne le même résultat que Min-Max mais coupe les branches inutiles, donc
il va plus profond dans le même temps.

### « Pourquoi une table de transposition ? »

Pour éviter de réanalyser une position déjà vue. Elle change la vitesse, pas
le résultat.

### « Pourquoi l'approfondissement itératif ? »

Pour respecter le temps : on garde toujours le meilleur coup de la dernière
profondeur terminée.

### « Pourquoi quatre évaluations ? »

Pour comparer objectivement plusieurs hypothèses de jeu : matériel, position,
mobilité, et une combinaison adaptée aux phases.

### « Les deux IA sont-elles indépendantes ? »

Oui : chaque `Agent` a sa propre table de transposition et son propre
historique. Aucun état partagé.

### « Quelles sont les limites ? »

- profondeur limitée par le temps ;
- pas d'apprentissage ;
- pas de livre d'ouverture ;
- réutilisation de l'arbre partielle (meilleur coup précédent).

### « Quelles perspectives ? »

- apprentissage par renforcement ;
- meilleure réutilisation de l'arbre ;
- élagage plus avancé ;
- ouverture précalculée.

---

## 15. Démonstration rapide

```bash
cd othello
python tests.py
python cli.py human mixed_ai
python campaigns.py
python web/server.py 8000
```

Puis montrer l'interface web et une partie IA vs IA avec pause.
