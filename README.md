# Othello — Projet IA

Projet universitaire d'IA pour le jeu d'Othello : moteur de règles, évaluations,
recherche Alpha-Bêta, parties humain/IA et IA/IA, interface web légère.
Auteur : **Théo Cornu** (dev A).

---

## 1. Installation

Le projet utilise uniquement la bibliothèque standard Python (3.11+).
Aucune dépendance à installer.

```bash
cd othello
python tests.py
```

---

## 2. Lancer une partie

### Terminal

```bash
# humain contre IA mixte
python cli.py human mixed_ai

# IA positionnelle contre IA mobilité, 5 parties
python cli.py positional_ai mobility_ai 5

# liste des profils disponibles
python cli.py --help
```

### Interface web

```bash
python web/server.py 8000
```

Puis ouvrir http://localhost:8000.

L'interface permet :
- de choisir le profil des joueurs noir et blanc (humain ou IA) ;
- de jouer un coup avec le bouton « Coup IA » ;
- de lancer un auto-play IA contre IA avec bouton « Auto IA vs IA » ;
- de mettre en pause à tout moment avec « Pause » ;
- de voir le coup choisi, l'évaluation, les nœuds, les évals, le temps et la profondeur.

---

## 3. Structure du projet

| Fichier | Rôle |
|---|---|
| `config.py` | Configuration centrale (constantes du jeu et valeurs par défaut). |
| `players_config.json` | Profils de joueurs (humain / IA et leurs paramètres). |
| `engine.py` | Moteur : règles, coups légaux, retournements, passe, fin, hash, perft. |
| `evals.py` | Les 4 stratégies d'évaluation. |
| `agent.py` | Agent de recherche Alpha-Bêta, table de transposition, time-out. |
| `human.py` | Joueur humain au clavier. |
| `players.py` | Fabrique de joueurs à partir des profils JSON. |
| `harness.py` | Déroulement d'une partie et export CSV/TXT. |
| `cli.py` | Ligne de commande pour lancer des parties. |
| `tests.py` | Tests de conformité (perft, symétrie, hash). |
| `web/server.py` | Serveur HTTP léger (API JSON + fichiers statiques). |
| `web/index.html` | Interface web (plateau, panneaux, historique). |
| `CONTRACT.md` | Contrat d'interface entre modules A et B. |
| `Othello_Colab.ipynb` | Notebook pour Google Colab. |

---

## 4. Configuration

### `config.py`

Toutes les valeurs modifiables sont regroupées ici :

- `CONTRACT_VERSION` : version du contrat ;
- `BOARD_SIZE`, `CELL_COUNT` : taille du plateau ;
- `EMPTY`, `BLACK`, `WHITE`, `PASS` : valeurs des cases et du passe ;
- `EVALUATION_BOUND`, `TERMINAL_SCORE_BASE` : bornes d'évaluation ;
- `EARLY_MOVES`, `ENDGAME_EMPTIES` : seuils de la stratégie mixte ;
- `DEFAULT_STRATEGY`, `DEFAULT_ALGO`, `DEFAULT_DEPTH`, `DEFAULT_BUDGET_MS` ;
- `TIME_TOLERANCE` : tolérance du budget temps ;
- `ZOBRIST_SEED` : graine du hash ;
- `OUTPUT_DIR` : dossier des résultats.

### `players_config.json`

Définit les profils utilisables par le CLI et l'interface web :

```json
{
  "default_black": "mixed_ai",
  "default_white": "human",
  "profiles": {
    "human": {"type": "human", "name": "Humain"},
    "mixed_ai": {
      "type": "ai",
      "name": "IA Mixte",
      "strategy": "mixed",
      "algo": "alphabeta",
      "depth": 6,
      "budget_ms": 1000
    }
  }
}
```

Chaque profil IA précise : stratégie, algorithme, profondeur et budget en millisecondes.

---

## 5. Moteur — `engine.py`

### `State`

Objet immuable représentant une position :

- `black` : bitboard des pions noirs ;
- `white` : bitboard des pions blancs ;
- `player` : joueur au trait ;
- `move_number` : nombre de coups posés ;
- `hash` : hash Zobrist de la position.

### `OthelloEngine`

- `initial_state()` : position de départ (blancs commencent) ;
- `legal_moves(state)` : coups légaux, `[PASS]` si seul le passe est possible, `[]` si fin ;
- `apply_move(state, move)` : nouvelle position, lève `ValueError` si le coup est illégal ;
- `is_terminal(state)` : fin de partie ;
- `score(state)` : `(noirs, blancs)` ;
- `mobility(state, player)` : nombre de coups légaux d'un joueur ;
- `board_list(state)` : plateau sous forme de 64 entiers ;
- `to_notation(move)` / `from_notation(text)` : conversion `d3` ↔ index ;
- `perft(state, depth)` : comptage de positions pour valider les règles.

Le hash Zobrist est calculé à partir de la graine `ZOBRIST_SEED`, ce qui rend
les parties reproductibles.

---

## 6. Évaluations — `evals.py`

Une évaluation est une fonction `eval(state, player) -> float` :

- positive si la position est favorable à `player` ;
- zéro-somme : `eval(state, 1) == -eval(state, 2)` ;
- bornée par `EVALUATION_BOUND`.

### Les quatre stratégies

1. **Positionnelle** : somme des poids statiques du plateau.
   Les coins valent 100, les cases instables sont pénalisées.
2. **Absolue** : différence du nombre de pions.
3. **Mobilité** : différence de coups possibles, bonus pour les coins, différence de pions.
4. **Mixte** : positionnelle en début de partie, mobilité au milieu, absolue en fin de partie.

`make_evaluator(name, engine)` renvoie l'évaluation demandée.
Les noms valides sont dans `EVALUATION_NAMES`.

---

## 7. Recherche — `agent.py`

### `MoveResult`

Résultat d'un coup :

- `move`, `eval_score`, `nodes`, `evals`, `time_ms`,
  `depth_reached`, `timed_out`, `tt_hits`.

### `Agent`

- `choose_move(state)` : choisit un coup légal ;
- `new_game(color)` : vide le cache et réinitialise la graine ;
- utilise un approfondissement itératif avec Alpha-Bêta ;
- respecte `time_budget_ms` ;
- réutilise le meilleur coup précédent pour l'ordre des coups ;
- possède sa propre table de transposition : deux agents ne partagent rien.

Valeurs terminales : `signe(diff) * (TERMINAL_SCORE_BASE + |diff|)`.

---

## 8. Joueur humain — `human.py`

`HumanPlayer` :

- affiche les coups légaux en notation `d3` ;
- lit le coup au clavier ;
- redemande en cas de saisie illégale ;
- renvoie un `MoveResult` avec `nodes = evals = 0`.

---

## 9. Fabrique de joueurs — `players.py`

- `load_player_config()` : lit `players_config.json` ;
- `make_ai(...)` : construit un agent ;
- `make_human(...)` : construit un joueur humain ;
- `make_player(engine, profile)` : construit depuis un profil ;
- `make_profile_player(engine, name, config)` : construit depuis un nom de profil.

C'est le point d'entrée utilisé par le CLI et le serveur web.

---

## 10. Harnais — `harness.py`

`play_game(engine, black, white, game_id, out_dir)` :

- appelle `new_game` sur les deux joueurs ;
- applique les passes automatiquement ;
- vérifie la légalité des coups ;
- écrit les résultats.

### Sorties

- `runs/moves.csv` : un coup par ligne ;
- `runs/matches.csv` : une partie par ligne ;
- `runs/games/<game_id>.txt` : rejeu de la partie avec scores d'évaluation.

---

## 11. CLI — `cli.py`

```bash
python cli.py <profil_noir> <profil_blanc> [nb_parties]
```

Les profils sont lus dans `players_config.json`.
Le script construit les joueurs, lance les parties et affiche le gagnant,
le score final et le nombre de coups.

---

## 12. Interface web — `web/`

### `web/server.py`

Serveur HTTP basé sur `http.server` :

- `GET /api/state` : état courant ;
- `GET /api/profiles` : profils disponibles ;
- `POST /api/config` : choisit les profils noir/blanc ;
- `POST /api/new` : nouvelle partie ;
- `POST /api/move` : joue un coup humain ;
- `POST /api/ai` : fait jouer l'IA courante.

### `web/index.html`

Page unique sans dépendance :

- plateau 8×8 cliquable ;
- surlignage des coups légaux ;
- panneau de score et d'informations ;
- sélection des profils ;
- auto-play et pause ;
- historique des coups.

---

## 13. Tests — `tests.py`

```bash
python tests.py
```

Contenu :

- `test_perft` : profondeurs 1 à 6 → 4, 12, 56, 244, 1396, 8200 ;
- `test_symmetry_and_bounds` : antisymétrie et bornes des évaluations ;
- `test_hash_consistency` : hash recalculé identique au hash stocké.

---

## 14. Contrat — `CONTRACT.md`

Le contrat décrit les interfaces entre :

- module A : moteur, évaluations, humain, harnais ;
- module B : agent de recherche.

Toute modification doit être répercutée dans `CONTRACT.md` et acceptée par les deux parties.

---

## 15. Google Colab

1. Ouvrir `Othello_Colab.ipynb`.
2. Uploader les fichiers `.py` et `players_config.json` dans `/content`.
3. Exécuter les cellules : tests, IA vs IA, humain vs IA, campagnes.

---

## 16. Reproductibilité

- graine Zobrist fixe ;
- profils et paramètres dans des fichiers de configuration ;
- résultats horodatés par `game_id` ;
- aucune dépendance externe.
