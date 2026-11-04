"""CLI: launch games by type."""
import sys
from engine import OthelloEngine, BLACK, WHITE
from evals import make_evaluator
from agent import Agent
from human import HumanPlayer
from harness import play_game

def ai(engine, strategy="mixed", algo="alphabeta", depth=4, budget=1000, name=None):
    ev = make_evaluator(strategy, engine)
    return Agent(engine, ev, algo=algo, max_depth=depth, time_budget_ms=budget,
                name=name or f"AI({strategy})")

def human(engine, name="Human"):
    return HumanPlayer(engine, name)

def parse_side(spec):
    # spec: "human" or "ai:strat:algo:depth:budget"
    if spec == "human":
        return "human", {}
    parts = spec.split(":")
    kind = parts[0]
    cfg = {"strategy": parts[1] if len(parts)>1 else "mixed",
           "algo": parts[2] if len(parts)>2 else "alphabeta",
           "depth": int(parts[3]) if len(parts)>3 else 4,
           "budget": int(parts[4]) if len(parts)>4 else 1000}
    return kind, cfg

def build(engine, spec):
    kind, cfg = parse_side(spec)
    if kind == "human":
        return human(engine)
    return ai(engine, name=kind.upper(), **cfg)

def main():
    # usage: python cli.py <black_spec> <white_spec> [games]
    # spec examples: human | ai | ai:mixed | ai:positional:alphabeta:5:2000
    if len(sys.argv) < 3:
        print("Usage: python cli.py <black> <white> [games]")
        print("  black/white: human | ai[:strat[:algo[:depth[:budget]]]]")
        print("  e.g. python cli.py human ai:mixed")
        print("       python cli.py ai:positional ai:mobility 5")
        sys.exit(1)
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    engine = OthelloEngine()
    bp = build(engine, sys.argv[1])
    wp = build(engine, sys.argv[2])
    for g in range(games):
        res = play_game(engine, bp, wp, game_id=f"g{g}", out_dir="runs" if games>1 else None)
        print(f"Game {g}: winner={res.winner} score={res.score} plies={len(res.moves)}")

if __name__ == "__main__":
    main()