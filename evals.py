"""Evaluation strategies (Dev A). Evaluator = Callable[[State,int],float], zero-sum."""
from engine import State, BLACK, WHITE, legal_moves

WEIGHTS = [
 [100,-20,10,5,5,10,-20,100],
 [-20,-50,-2,-2,-2,-2,-50,-20],
 [10,-2,-1,-1,-1,-1,-2,10],
 [5,-2,-1,-1,-1,-1,-2,5],
 [5,-2,-1,-1,-1,-1,-2,5],
 [10,-2,-1,-1,-1,-1,-2,10],
 [-20,-50,-2,-2,-2,-2,-50,-20],
 [100,-20,10,5,5,10,-20,100],
]
WFLAT = [WEIGHTS[r][c] for r in range(8) for c in range(8)]

def _opp(p): return 3-p
def _counts(state, player):
    b=state.board; opp=_opp(player)
    return b.count(player), b.count(opp)

def eval_positional(state, player):
    b=state.board; opp=_opp(player)
    s=0
    for i,v in enumerate(b):
        if v==player: s+=WFLAT[i]
        elif v==opp: s-=WFLAT[i]
    # terminal bonus
    if all(x!=0 for x in b):
        pc,oc=_counts(state,player); s += (pc-oc)*1000
    return float(s)

def eval_absolute(state, player):
    pc,oc=_counts(state,player)
    if all(x!=0 for x in state.board) or (not legal_moves(state) and not legal_moves(State(state.board,_opp(player)))):
        return float((pc-oc)*1000)
    return float(pc-oc)

def eval_mobility(state, player):
    opp=_opp(player)
    my=len(legal_moves(State(state.board,player)))
    their=len(legal_moves(State(state.board,opp)))
    # corners
    corners=[0,7,56,63]
    cb=sum(1 for c in corners if state.board[c]==player)
    co=sum(1 for c in corners if state.board[c]==opp)
    pc,oc=_counts(state,player)
    score = (my-their) + 10*(cb-co) + (pc-oc)
    # terminal
    if all(x!=0 for x in state.board):
        score = (pc-oc)*1000
    return float(score)

def eval_mixed(state, player):
    filled=sum(1 for x in state.board if x!=0)
    if filled < 24:
        return eval_positional(state,player)
    if filled > 48:
        return eval_absolute(state,player)
    return eval_mobility(state,player)

EVALS = {
 "positional": eval_positional,
 "absolute": eval_absolute,
 "mobility": eval_mobility,
 "mixed": eval_mixed,
}