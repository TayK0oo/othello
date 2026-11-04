"""Evaluations v1.1."""
from engine import State, BLACK, WHITE, PASS, OthelloEngine, EVAL_BOUND

W = [
 [100,-20,10,5,5,10,-20,100],
 [-20,-50,-2,-2,-2,-2,-50,-20],
 [10,-2,-1,-1,-1,-1,-2,10],
 [5,-2,-1,-1,-1,-1,-2,5],
 [5,-2,-1,-1,-1,-1,-2,5],
 [10,-2,-1,-1,-1,-1,-2,10],
 [-20,-50,-2,-2,-2,-2,-50,-20],
 [100,-20,10,5,5,10,-20,100],
]
WF = [W[r][c] for r in range(8) for c in range(8)]

def _opp(p): return 3-p

def _board(state): 
    out=[0]*64
    for i in range(64):
        if state.black & (1<<i): out[i]=BLACK
        elif state.white & (1<<i): out[i]=WHITE
    return out

def eval_positional(state, player, engine=None):
    s=0
    for i in range(64):
        if state.black & (1<<i):
            v=WF[i] if player==BLACK else -WF[i]
            s+=v
        elif state.white & (1<<i):
            v=WF[i] if player==WHITE else -WF[i]
            s+=v
    return float(s)

def eval_absolute(state, player, engine=None):
    bc = bin(state.black).count("1"); wc=bin(state.white).count("1")
    pc = bc if player==BLACK else wc
    oc = wc if player==BLACK else bc
    return float(pc-oc)

def eval_mobility(state, player, engine):
    my = engine.mobility(state, player)
    their = engine.mobility(state, _opp(player))
    corners=[0,7,56,63]
    cb=sum(1 for c in corners if (state.black if player==BLACK else state.white)&(1<<c))
    co=sum(1 for c in corners if (state.white if player==BLACK else state.black)&(1<<c))
    bc=bin(state.black).count("1"); wc=bin(state.white).count("1")
    pc = bc if player==BLACK else wc; oc = wc if player==BLACK else bc
    return float((my-their)+10*(cb-co)+(pc-oc))

def eval_mixed(state, player, engine):
    empties = 64 - (bin(state.black|state.white).count("1"))
    if state.move_number < 22:
        return eval_positional(state, player, engine)
    if empties <= 12:
        return eval_absolute(state, player, engine)
    return eval_mobility(state, player, engine)

def make_evaluator(name, engine, **params):
    early = params.get("early_moves", 22)
    endg = params.get("endgame_empties", 12)
    if name=="positional":
        def f(s,p): return eval_positional(s,p,engine)
    elif name=="absolute":
        def f(s,p): return eval_absolute(s,p,engine)
    elif name=="mobility":
        def f(s,p): return eval_mobility(s,p,engine)
    elif name=="mixed":
        def f(s,p):
            empties=64-bin(s.black|s.white).count("1")
            if s.move_number < early: return eval_positional(s,p,engine)
            if empties <= endg: return eval_absolute(s,p,engine)
            return eval_mobility(s,p,engine)
    else:
        raise ValueError(name)
    return f

EVALS_NAMES = ["positional","absolute","mobility","mixed"]