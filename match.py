# Author: Théo Cornu
"""Match launcher helpers: configurable players."""
from engine import OthelloEngine, BLACK, WHITE
from evals import make_evaluator
from agent import Agent
from human import HumanPlayer

def make_ai(engine, strategy="mixed", algo="alphabeta", depth=4, budget=1000, name=None):  # Théo Cornu
    ev = make_evaluator(strategy, engine)
    return Agent(engine, ev, algo=algo, max_depth=depth, time_budget_ms=budget,
                name=name or f"AI({strategy})")

def make_player(engine, kind, **kw):  # Théo Cornu
    kind = kind.lower()
    if kind in ("human","h"):
        return HumanPlayer(engine, kw.get("name","Human"))
    if kind in ("ai","ia"):
        return make_ai(engine, kw.get("strategy","mixed"), kw.get("algo","alphabeta"),
                      kw.get("depth",4), kw.get("budget",1000), kw.get("name"))
    raise ValueError(kind)

def run_match(black_kind, white_kind, **kw):  # Théo Cornu
    engine = OthelloEngine()
    bp = make_player(engine, black_kind, **{k: v for k,v in kw.items() if k.startswith("black_") or k in ("strategy","algo","depth","budget")})
    # simpler: pass configs
    return engine, bp, None
