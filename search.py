"""Search algorithms (Dev B)."""
import time, random
from engine import State, legal_moves, apply_move, is_terminal, score

# Zobrist
random.seed(42)
ZOBRIST = [[[random.getrandbits(64) for _ in range(3)] for _ in range(64)] for _ in range(1)]  # [cell][piece]
# side to move
SIDE = random.getrandbits(64)

def hash_state(state: State) -> int:
    h = 0
    for i,v in enumerate(state.board):
        if v:
            h ^= ZOBRIST[0][i][v]
    if state.player == 2:
        h ^= SIDE
    return h

def _moves_ordered(state, tt_move=None, prev_best=None):
    ms = legal_moves(state)
    if not ms:
        return [-1] if not is_terminal(state) else []
    order = []
    if tt_move is not None and tt_move in ms:
        order.append(tt_move)
    if prev_best is not None and prev_best in ms and prev_best not in order:
        order.append(prev_best)
    for m in ms:
        if m not in order:
            order.append(m)
    # corners first heuristic
    corners={0,7,56,63}
    order.sort(key=lambda m: (0 if m in corners else 1, m not in order))
    # keep priority: re-sort stable keeping priority first
    prio=[m for m in order if m in (set([tt_move,prev_best]) if False else set())]
    return order

def _eval_for(state, player, evaluator):
    return evaluator(state, player)

def minimax_root(state, depth, root_player, evaluator):
    ms = legal_moves(state)
    if not ms:
        if is_terminal(state): 
            return evaluator(state, root_player), -1
        ms = [-1]
    if depth==0:
        return evaluator(state, root_player), (ms[0] if ms else -1)
    best_score = None; best_move = ms[0]
    for m in ms:
        ns = apply_move(state, m)
        sc = _minimax(ns, depth-1, root_player, evaluator)
        if best_score is None or sc > best_score:
            best_score = sc; best_move = m
    return best_score, best_move

def _minimax(state, depth, root_player, evaluator):
    if depth==0 or is_terminal(state):
        return evaluator(state, root_player)
    ms = legal_moves(state)
    if not ms:
        if is_terminal(state):
            return evaluator(state, root_player)
        ms = [-1]
    # if state.player == root_player -> maximize else minimize
    if state.player == root_player:
        best = None
        for m in ms:
            ns = apply_move(state, m)
            sc = _minimax(ns, depth-1, root_player, evaluator)
            if best is None or sc > best:
                best = sc
        return best if best is not None else evaluator(state, root_player)
    else:
        best = None
        for m in ms:
            ns = apply_move(state, m)
            sc = _minimax(ns, depth-1, root_player, evaluator)
            if best is None or sc < best:
                best = sc
        return best if best is not None else evaluator(state, root_player)

def alphabeta_root(state, depth, root_player, evaluator, tt=None, prev_best=None):
    ms = legal_moves(state)
    if not ms:
        if is_terminal(state):
            return evaluator(state, root_player), -1
        ms=[-1]
    if depth==0:
        return evaluator(state, root_player), (ms[0] if ms else -1)
    tt_move=None
    if tt is not None:
        e=tt.get(hash_state(state))
        if e and e[0]>=depth:
            return e[1], (e[3] if e[3] is not None else ms[0])
        if e: tt_move=e[3]
    best_score=None; best_move=ms[0]; alpha=float('-inf'); beta=float('inf')
    for m in _moves_ordered(state, tt_move, prev_best):
        if m==-1 and is_terminal(state): 
            continue
        ns=apply_move(state,m)
        sc=_alphabeta(ns, depth-1, root_player, evaluator, alpha, beta, tt)
        if best_score is None or sc>best_score:
            best_score=sc; best_move=m
        alpha=max(alpha, best_score)
        if beta<=alpha: break
    if tt is not None:
        tt[hash_state(state)] = (depth, best_score, 0, best_move)
    return best_score, best_move

def _alphabeta(state, depth, root_player, evaluator, alpha, beta, tt):
    if depth==0 or is_terminal(state):
        return evaluator(state, root_player)
    ms=legal_moves(state)
    if not ms:
        if is_terminal(state):
            return evaluator(state, root_player)
        ms=[-1]
    tt_move=None
    if tt is not None:
        e=tt.get(hash_state(state))
        if e and e[0]>=depth:
            return e[1]
        if e: tt_move=e[3]
    if state.player==root_player:  # maximize
        best=float('-inf')
        for m in _moves_ordered(state, tt_move, None):
            ns=apply_move(state,m)
            sc=_alphabeta(ns, depth-1, root_player, evaluator, alpha, beta, tt)
            if sc>best: best=sc
            alpha=max(alpha,best)
            if beta<=alpha: break
        return best
    else:
        best=float('inf')
        for m in _moves_ordered(state, tt_move, None):
            ns=apply_move(state,m)
            sc=_alphabeta(ns, depth-1, root_player, evaluator, alpha, beta, tt)
            if sc<best: best=sc
            beta=min(beta,best)
            if beta<=alpha: break
        return best

def negamax_root(state, depth, root_player, evaluator, tt=None, prev_best=None):
    # negamax from perspective of side to move; convert to root_player
    # We'll implement negamax returning score for player to move at node.
    ms=legal_moves(state)
    if not ms:
        if is_terminal(state): 
            # score for root_player
            return evaluator(state, root_player), -1
        ms=[-1]
    if depth==0:
        return evaluator(state, root_player), (ms[0] if ms else -1)
    best_score=None; best_move=ms[0]; alpha=float('-inf'); beta=float('inf')
    for m in _moves_ordered(state, None, prev_best):
        ns=apply_move(state,m)
        # score for the side to move at ns = opposite; negamax returns for player to move
        sc = -_negamax(ns, depth-1, evaluator, -beta, -alpha, tt)
        # sc is from root_player? negamax returns for side to move at node (ns.player). Need convert to root_player.
        # Actually negamax(s, depth) returns best score for s.player. For root, we want root_player perspective.
        # Convert: if root_player != state.player, flip. Let's instead make negamax return for a fixed player? 
        pass
    return None,None

# Clean negamax: standard negamax returns value for player to move. Convert at root.
def negamax_value(state, depth, evaluator, alpha, beta, tt):
    if depth==0 or is_terminal(state):
        # value for player to move at state
        return evaluator(state, state.player)
    ms=legal_moves(state)
    if not ms:
        if is_terminal(state):
            return evaluator(state, state.player)
        ms=[-1]
    tt_move=None
    if tt is not None:
        e=tt.get(hash_state(state))
        if e and e[0]>=depth:
            return e[1]
        if e: tt_move=e[3]
    best=float('-inf')
    for m in _moves_ordered(state, tt_move, None):
        ns=apply_move(state,m)
        val = -negamax_value(ns, depth-1, evaluator, -beta, -alpha, tt)
        if val>best: best=val
        alpha=max(alpha,best)
        if alpha>=beta: break
    if tt is not None:
        tt[hash_state(state)] = (depth, best, 0, None)
    return best

def negamax_root(state, depth, root_player, evaluator, tt=None, prev_best=None):
    ms=legal_moves(state)
    if not ms:
        if is_terminal(state):
            return evaluator(state, root_player), -1
        ms=[-1]
    if depth==0:
        return evaluator(state, root_player), (ms[0] if ms else -1)
    best_score=None; best_move=ms[0]
    # negamax returns for side to move; convert to root_player
    for m in _moves_ordered(state, None, prev_best):
        ns=apply_move(state,m)
        val = -negamax_value(ns, depth-1, evaluator, float('-inf'), float('inf'), tt)
        # val is for state.player (root side to move at root) since root state.player==root? not always. Convert:
        if state.player != root_player:
            val = -val
        if best_score is None or val>best_score:
            best_score=val; best_move=m
    return best_score, best_move

def iterative_deepening(state, root_player, evaluator, algo, time_budget_ms, max_depth=20, tt=None, prev_best=None):
    start=time.monotonic()
    deadline=start + time_budget_ms/1000.0
    best_move=None; best_score=None; depth_reached=0; nodes=[0]
    # simple node counter via closure not tracked in algorithms above; skip precise for now
    for d in range(1, max_depth+1):
        if time.monotonic() >= deadline:
            break
        try:
            if algo=="minimax":
                sc,mv = minimax_root(state, d, root_player, evaluator)
            elif algo=="alphabeta":
                sc,mv = alphabeta_root(state, d, root_player, evaluator, tt, prev_best)
            elif algo=="negamax":
                sc,mv = negamax_root(state, d, root_player, evaluator, tt, prev_best)
            else:
                sc,mv = alphabeta_root(state, d, root_player, evaluator, tt, prev_best)
        except Exception:
            break
        if mv is not None:
            best_move=mv; best_score=sc; depth_reached=d
        if time.monotonic() >= deadline:
            break
    if best_move is None:
        ms=legal_moves(state)
        best_move = ms[0] if ms else -1
        best_score = evaluator(state, root_player)
    elapsed=(time.monotonic()-start)*1000
    return best_move, best_score, depth_reached, elapsed