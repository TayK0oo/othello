# CONTRACT.md

```python
# plateau = 64 cases, 0 vide / 1 noir / 2 blanc, index = 8*ligne + colonne
# Les blancs commencent

class OthelloEngine:   # A
    def initial_state() -> State
    def legal_moves(state) -> list[int]   # [] = passe
    def apply_move(state, move) -> State  # immuable; move=-1 passe
    def is_terminal(state) -> bool
    def score(state) -> tuple[int,int]

Evaluator = Callable[[State,int], float]   # A

class Agent:   # B
    def __init__(self, evaluator, max_depth, time_budget_ms, algo="alphabeta")
    def choose_move(state, legal_moves) -> MoveResult

MoveResult = {move, eval_score, nodes, time_ms, depth_reached}
```
Une instance Agent = un cache propre. L'IA ne touche pas aux internes du moteur. Toute modif du contrat = accord des deux.