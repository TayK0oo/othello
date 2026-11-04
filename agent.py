# Author: Théo Cornu
import random
import time
from dataclasses import dataclass

from config import BLACK, WHITE, PASS, TERMINAL_SCORE_BASE


@dataclass
class MoveResult:
    move: int
    eval_score: float
    nodes: int
    evals: int
    time_ms: float
    depth_reached: int
    timed_out: bool
    tt_hits: int


class Player:
    name: str

    def new_game(self, color):
        raise NotImplementedError

    def choose_move(self, state):
        raise NotImplementedError


class Agent(Player):
    def __init__(self, engine, evaluator, *, algo="alphabeta", max_depth=6,
                 time_budget_ms=1000, use_tt=True, reuse_tree=True, seed=0, name=None):
        self.engine = engine
        self.evaluator = evaluator
        self.algo = algo
        self.max_depth = max_depth
        self.time_budget_ms = time_budget_ms
        self.use_tt = use_tt
        self.reuse_tree = reuse_tree
        self.seed = seed
        self.name = name or f"Agent({algo})"
        self.random = random.Random(seed)
        self.transposition_table = {}
        self.previous_best = None
        self.nodes = 0
        self.evals = 0
        self.tt_hits = 0
        self.deadline = 0.0

    def new_game(self, color):
        self.transposition_table = {}
        self.previous_best = None
        self.random = random.Random(self.seed)

    def _terminal_score(self, state, player):
        black_score, white_score = self.engine.score(state)
        own = black_score if player == BLACK else white_score
        other = white_score if player == BLACK else black_score
        difference = own - other
        if difference == 0:
            return 0.0
        return (1 if difference > 0 else -1) * (TERMINAL_SCORE_BASE + abs(difference))

    def _order_moves(self, state, moves, tt_move):
        ordered = []
        if tt_move is not None and tt_move in moves:
            ordered.append(tt_move)
        if self.previous_best is not None and self.previous_best in moves and self.previous_best not in ordered:
            ordered.append(self.previous_best)
        corners = {0, 7, 56, 63}
        remaining = sorted(
            [move for move in moves if move not in ordered],
            key=lambda move: (0 if move in corners else 1, move),
        )
        return ordered + remaining

    def _lookup_tt(self, state, depth):
        entry = self.transposition_table.get(state.hash)
        if entry is None:
            return None
        if entry[0] != state.black or entry[1] != state.white or entry[2] != state.player:
            return None
        if entry[3] >= depth:
            self.tt_hits += 1
            return entry[4], entry[5]
        return None, entry[5]

    def _store_tt(self, state, depth, score, move):
        if self.use_tt:
            self.transposition_table[state.hash] = (
                state.black, state.white, state.player, depth, score, move
            )

    def choose_move(self, state):
        moves = self.engine.legal_moves(state)
        if not moves:
            return MoveResult(PASS, 0.0, 0, 0, 0.0, 0, False, 0)
        if len(moves) == 1:
            return MoveResult(moves[0], 0.0, 0, 0, 0.0, 0, False, 0)

        self.nodes = 0
        self.evals = 0
        self.tt_hits = 0
        start = time.perf_counter()
        self.deadline = start + self.time_budget_ms / 1000.0

        best_move = moves[0]
        best_score = None
        depth_reached = 0
        timed_out = False

        for depth in range(1, self.max_depth + 1):
            if time.perf_counter() >= self.deadline:
                break
            score, move, stopped = self._search_root(state, depth)
            if move is not None:
                best_move = move
                best_score = score
                depth_reached = depth
            if stopped:
                timed_out = True
                break
            if time.perf_counter() >= self.deadline:
                break

        elapsed = (time.perf_counter() - start) * 1000
        if best_score is None:
            best_score = self.evaluator(state, state.player)
        self.previous_best = best_move
        return MoveResult(best_move, best_score, self.nodes, self.evals,
                          elapsed, depth_reached, timed_out, self.tt_hits)

    def _search_root(self, state, depth):
        moves = self.engine.legal_moves(state)
        if not moves:
            return self._terminal_score(state, state.player), None, False
        ordered = self._order_moves(state, moves, None)
        best_score = None
        best_move = moves[0]
        alpha = float("-inf")
        beta = float("inf")
        timed_out = False
        for move in ordered:
            if time.perf_counter() > self.deadline:
                timed_out = True
                break
            child = self.engine.apply_move(state, move)
            self.nodes += 1
            score = self._alpha_beta(child, depth - 1, state.player, alpha, beta)
            if best_score is None or score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        self._store_tt(state, depth, best_score, best_move)
        return best_score, best_move, timed_out

    def _alpha_beta(self, state, depth, root_player, alpha, beta):
        if self.engine.is_terminal(state):
            return self._terminal_score(state, root_player)
        moves = self.engine.legal_moves(state)
        if not moves:
            return self._terminal_score(state, root_player)
        if depth == 0:
            self.evals += 1
            return self.evaluator(state, root_player)
        if len(moves) == 1:
            child = self.engine.apply_move(state, moves[0])
            self.nodes += 1
            return self._alpha_beta(child, depth - 1, root_player, alpha, beta)

        tt_move = None
        if self.use_tt:
            cached = self._lookup_tt(state, depth)
            if cached is not None:
                value, tt_move = cached
                if value is not None:
                    return value

        ordered = self._order_moves(state, moves, tt_move)
        maximizing = state.player == root_player
        if maximizing:
            best = float("-inf")
            for move in ordered:
                if time.perf_counter() > self.deadline:
                    return best if best != float("-inf") else self.evaluator(state, root_player)
                child = self.engine.apply_move(state, move)
                self.nodes += 1
                score = self._alpha_beta(child, depth - 1, root_player, alpha, beta)
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            self._store_tt(state, depth, best, None)
            return best

        best = float("inf")
        for move in ordered:
            if time.perf_counter() > self.deadline:
                return best if best != float("inf") else self.evaluator(state, root_player)
            child = self.engine.apply_move(state, move)
            self.nodes += 1
            score = self._alpha_beta(child, depth - 1, root_player, alpha, beta)
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        self._store_tt(state, depth, best, None)
        return best