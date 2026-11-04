
import sys
from engine import OthelloEngine, BLACK, WHITE, PASS
from evals import make_evaluator
from agent import Agent
from human import HumanPlayer
from harness import play_game

def main():
    strat = sys.argv[1] if len(sys.argv)>1 else "mixed"
    budget = int(sys.argv[2]) if len(sys.argv)>2 else 1000
    engine = OthelloEngine()
    ev = make_evaluator(strat, engine)
    human = HumanPlayer(engine, "Human")
    ai = Agent(engine, ev, algo="alphabeta", max_depth=6, time_budget_ms=budget, name="AI")
    res = play_game(engine, ai, human, game_id="cli", out_dir=None)
    print("Final score (black, white):", res.score)
    print("Winner:", res.winner, "(0 draw)")
    print("Moves:")
    for i,m in enumerate(res.moves):
        print(i, engine.to_notation(m))

if __name__=="__main__":
    main()