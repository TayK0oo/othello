# CONTRACT.md — Projet Othello

**Version : 1.1** · Statut : à valider par A et B puis **figer** · Langage : Python 3.11+ (à confirmer avec le sujet)

Source de vérité unique entre le module **A (moteur, évaluations, harnais)** et le module **B (recherche)**.
Toute modification = incrément de version + accord des deux + ligne dans le changelog (§11).

---

## 1. Conventions

| Élément | Convention |
|---|---|
| Cases | 64 cases, index `i = 8*ligne + colonne`, `ligne` et `colonne` dans `0..7` |
| Notation texte | colonne `a..h`, ligne `1..8` : `a1 = 0`, `h1 = 7`, `a8 = 56`, `h8 = 63` |
| Joueurs | `BLACK = 1`, `WHITE = 2`, `opp(p) = 3 - p` |
| Qui commence | **Les blancs** (sujet) → `initial_state().player == WHITE` |
| Position de départ | Fixée par le cours ; **`initial_state()` en est l'unique source de vérité** (standard : blancs en d4 et e5, noirs en d5 et e4, à confirmer avec le cours) |
| Coup | entier `0..63`, ou `PASS = -1` |
| Profondeur | `max_depth` est en **demi-coups (plies)**. Le sujet définit « profondeur 1 = coups du joueur + réponses de l'adversaire » : à convertir et à expliciter dans le rapport |
| Horloge | `time.perf_counter()` (même horloge partout) |

---

## 2. `State`

Objet **immuable** (`@dataclass(frozen=True, slots=True)`), produit uniquement par le moteur.
Les champs ci-dessous sont **publics en lecture seule** ; tout le reste est interne au moteur et interdit aux autres modules.

| Champ | Type | Sens |
|---|---|---|
| `black` | `int` | bitboard des pions noirs, bit `i` = case `i` |
| `white` | `int` | bitboard des pions blancs |
| `player` | `int` | joueur au trait (`BLACK` ou `WHITE`) |
| `move_number` | `int` | nombre de coups **posés** depuis le départ (les passes ne comptent pas) ; `0` au départ |
| `hash` | `int` | hash Zobrist 64 bits, **côté au trait inclus**, calculé incrémentalement par le moteur |

Propriété dérivée : `state.empties = 64 - popcount(black | white)`.

Le moteur possède la table Zobrist (graine fixe dans le code). Les agents ne recalculent jamais le hash.

---

## 3. Moteur — `OthelloEngine` (module A)

```python
BLACK, WHITE, PASS = 1, 2, -1
CONTRACT_VERSION = "1.1"

class OthelloEngine:
    def initial_state(self) -> State
    def legal_moves(self, state) -> list[int]      # voir règle de passe ci-dessous
    def apply_move(self, state, move: int) -> State
    def is_terminal(self, state) -> bool
    def score(self, state) -> tuple[int, int]      # (nb_noirs, nb_blancs)
    def mobility(self, state, player: int) -> int  # nb de coups légaux de `player`, même s'il n'est pas au trait

    # utilitaires (affichage, tests, CLI)
    def to_notation(self, move: int) -> str        # 19 -> "d3", PASS -> "pass"
    def from_notation(self, text: str) -> int
    def board_list(self, state) -> list[int]       # 64 valeurs 0/1/2
    def perft(self, state, depth: int) -> int
```

**Règle de passe (point critique)**
- Si le joueur au trait a au moins un coup : `legal_moves` renvoie ces coups (jamais `PASS`).
- S'il n'en a aucun mais que l'adversaire en a : `legal_moves` renvoie **`[PASS]`**.
- Si aucun des deux joueurs n'a de coup : la partie est terminée, `is_terminal` renvoie `True` et `legal_moves` renvoie **`[]`**.
- `apply_move(state, PASS)` change uniquement le joueur au trait (`move_number` inchangé).
- Un coup illégal passé à `apply_move` lève `ValueError`.

**Garanties**
- `apply_move` ne modifie jamais son argument.
- Déterminisme total : mêmes entrées, mêmes sorties, ordre des coups croissant par index.
- Le hash incrémental est égal au hash recalculé depuis zéro (testé).

---

## 4. Évaluation — `Evaluator` (module A)

```python
Evaluator = Callable[[State, int], float]    # evaluate(state, player)

def make_evaluator(name: str, engine, **params) -> Evaluator
# name ∈ {"positional", "absolute", "mobility", "mixed"}
```

**Convention de signe** : `evaluate(state, player)` est **positif quand la position est favorable à `player`**, quel que soit `state.player`.
Pour les 4 stratégies (zéro-somme) : `evaluate(s, p) == -evaluate(s, opp(p))` (testé).

**Bornes** : `|evaluate| < EVAL_BOUND = 1000`.

**Positions terminales** : ce n'est **pas** le rôle de l'évaluateur. L'agent les traite lui-même (§5) avec :
`valeur = signe(diff) * (TERMINAL_BASE + |diff|)`, `TERMINAL_BASE = 10_000`, `diff = pions(player) - pions(opp(player))`, `0` en cas d'égalité.

**Accès au moteur** : un évaluateur peut utiliser l'API publique du §3 (par exemple `engine.mobility`) et les champs publics de `State`. Rien d'autre.

**Paramètres par défaut de la stratégie mixte** (réglables) :
- début de partie (positionnelle) tant que `move_number < early_moves = 22` (sujet : 20 à 25 premiers coups) ;
- fin de partie (absolue) dès que `empties <= endgame_empties = 12` (sujet : 10 à 16 derniers coups) ;
- entre les deux : mobilité.

---

## 5. Agent — module B

```python
@dataclass(frozen=True)
class MoveResult:
    move: int            # coup choisi (0..63 ou PASS)
    eval_score: float    # valeur de la racine, du point de vue du joueur au trait
    nodes: int           # nœuds GÉNÉRÉS pendant CE coup (= nb d'appels à apply_move faits par la recherche)
    evals: int           # nb d'appels à l'évaluateur pendant CE coup
    time_ms: float       # temps de calcul de CE coup
    depth_reached: int   # plus grande profondeur (en plies) entièrement terminée
    timed_out: bool      # True si la recherche a été coupée par le budget temps
    tt_hits: int         # nb de succès dans la table de transposition pendant CE coup

class Player(Protocol):             # interface commune IA et humain
    name: str
    def new_game(self, color: int) -> None
    def choose_move(self, state) -> MoveResult

class Agent(Player):
    def __init__(self, engine, evaluator, *, algo="alphabeta", max_depth=6,
                 time_budget_ms=1000, use_tt=True, reuse_tree=True,
                 seed=0, name=None): ...
# algo ∈ {"minimax", "alphabeta", "negamax", "negamax_ab"}
```

**Règles**
1. **Un `Agent` = un cache à lui** (table de transposition, arbre précédent, compteurs). Aucun état partagé : ni variable globale, ni attribut de classe mutable. Deux agents ne partagent **jamais** de cache (exigence du sujet).
2. **Vie du cache** : il persiste entre les appels de `choose_move` au sein d'une partie (réutilisation de l'analyse du tour précédent). `new_game(color)` le **vide** et réinitialise le générateur aléatoire avec `seed`.
3. **Retrouver sa position** : l'agent retrouve l'état courant par `state.hash`. Il ne dépend pas de l'historique et fonctionne même après une passe de l'adversaire.
4. **Collisions** : chaque entrée de la table stocke aussi `(black, white, player)` ; une discordance est comptée et traitée comme un échec de lecture.
5. **Temps** :
   - `time_budget_ms` est **par coup**, mesuré avec `time.perf_counter()` ;
   - l'agent se surveille lui-même (approfondissement itératif, vérification de l'horloge dans la recherche) ;
   - il renvoie **toujours** un coup légal : le meilleur de la dernière profondeur terminée, ou à défaut le premier coup légal ;
   - tolérance du harnais : `time_ms <= 1.10 * time_budget_ms`, sinon violation loggée.
6. **Appels** : le harnais n'appelle **jamais** `choose_move` quand `legal_moves == [PASS]` (passe appliquée automatiquement). Si un seul coup est légal, l'agent le renvoie sans chercher.
7. **Égalités** : départagées de façon déterministe par `seed`.
8. **Accès** : l'agent n'utilise que l'API publique du §3 et les champs publics du §2.
9. **Comparabilité** : `nodes` se compte de la même façon pour les 4 algorithmes, pour que les comparaisons du rapport soient valides.

---

## 6. Humain (module A)

`HumanPlayer` implémente `Player` : il lit un coup au clavier (notation `d3`), re-demande en cas de saisie illégale, et renvoie un `MoveResult` avec `time_ms` mesuré et `nodes = evals = 0`. Le harnais traite donc humain et IA de la même façon.

---

## 7. Harnais (module A)

```python
def play_game(engine, black: Player, white: Player, *, game_id: str,
              out_dir: str | None = None) -> GameResult
```

- Appelle `new_game(color)` sur chaque joueur au début.
- Applique les passes automatiquement.
- Vérifie la légalité : un joueur qui renvoie un coup illégal **perd par forfait** (loggé).
- `GameResult` : `winner` (`BLACK`, `WHITE` ou `0`), `score`, `moves` (liste d'entiers, passes incluses), `move_results` (un `MoveResult` par coup).

---

## 8. Formats de sortie

**`moves.csv`**, une ligne par coup joué par un joueur (passes automatiques exclues) :
`contract_version, game_id, ply, player, player_name, move, eval_score, nodes, evals, time_ms, depth_reached, timed_out, tt_hits`

**`matches.csv`**, une ligne par partie :
`contract_version, game_id, seed, black_name, white_name, black_algo, white_algo, black_eval, white_eval, max_depth, time_budget_ms, black_score, white_score, winner, n_plies, timeout_violations`

**`games/<game_id>.txt`** (extension « rejouer la partie » et score d'évaluation demandés par le sujet) :
ligne d'en-tête `# game_id=... seed=... contract=1.1`, puis une ligne par coup : `ply;joueur;coup;eval_score`.
Les coups sont en notation `d3` ; une passe automatique est notée `pass;-`.

Les séparateurs CSV sont des virgules ; les flottants ont au plus 3 décimales.

---

## 9. Tests de conformité (à mettre dans `tests/contract/`)

| Test | Module | Attendu |
|---|---|---|
| `perft` depuis le départ, profondeurs 1 à 6 | A | 4, 12, 56, 244, 1396, 8200 |
| Passe, fin de partie, retournements multi-directions | A | positions de référence écrites à la main |
| Hash incrémental = hash recalculé | A | égalité sur 1000 parties aléatoires |
| Antisymétrie des 4 évaluations | A | `eval(s,p) == -eval(s,opp(p))` |
| Bornes des évaluations | A | `abs(eval) < 1000` |
| Alpha-Bêta = Min-Max | B | mêmes valeur et coup à profondeur égale (100 positions) |
| NegaMax = Min-Max | B | idem |
| Table de transposition activée ou non | B | même `eval_score`, seuls `nodes` et `time_ms` changent |
| Respect du temps | B | `time_ms <= 1.10 * budget` et coup légal renvoyé, y compris avec un budget minuscule |
| Deux agents indépendants | B | l'un joue, le cache de l'autre reste vide |
| `new_game` | B | cache vidé, résultats identiques pour une même `seed` |

---

## 10. Qui fait quoi

| Bloc | Responsable | Relecteur |
|---|---|---|
| §2, §3, §4, §6, §7, §8 (code et tests) | A | B |
| §5 (code et tests) | B | A |
| §1, §9, ce fichier | A et B ensemble | — |

---

## 11. Changelog

| Version | Changements |
|---|---|
| 1.0 | Première ébauche |
| 1.1 | `State` défini ; règle de passe explicite (`PASS`, `[PASS]` vs `[]`) ; moteur passé à l'agent et à l'évaluateur (API publique seulement) ; convention de signe et bornes des évaluations ; valeurs terminales ; budget temps par coup et tolérance ; `new_game` ; propriétaire du hash Zobrist ; définition des nœuds ; interface `Player` commune IA et humain ; harnais ; formats CSV et `.txt` ; tests de conformité |

---

## 12. Points à confirmer avec le cours / le sujet

- Position de départ exacte et couleur qui commence.
- Définition exacte de la « profondeur » (1 = 1 ply ou 2 plies ?) pour la convertir dans le rapport.
- Langage imposé ou conseillé, et nombre de membres du groupe.
