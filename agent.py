"""Agent wrapper (Dev B) with own TT/cache."""
import time
from engine import State, legal_moves, apply_move
from search import iterative_deepening

class Agent:
    def __init__(self, evaluator, max_depth=4, time_budget_ms=1000, algo="alphabeta"):
        self.evaluator=evaluator; self.max_depth=max_depth
        self.time_budget_ms=time_budget_ms; self.algo=algo
        self.tt={}; self.prev_best=None; self.nodes=0

    def choose_move(self, state, legal_moves_list):
        root_player=state.player
        move,score,depth,elapsed=iterative_deepening(
            state, root_player, self.evaluator, self.algo,
            self.time_budget_ms, max_depth=self.max_depth, tt=self.tt, prev_best=self.prev_best)
        self.prev_best=move
        # count nodes approximated: not tracked; set 0
        res={"move":move,"eval_score":score,"nodes":0,"time_ms":elapsed,"depth_reached":depth}
        return res