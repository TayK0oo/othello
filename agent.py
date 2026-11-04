"""Agent v1.1."""
import time, random
from dataclasses import dataclass
from engine import State, BLACK, WHITE, PASS, OthelloEngine, TERMINAL_BASE

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
    def new_game(self, color): ...
    def choose_move(self, state) -> MoveResult: ...

class Agent(Player):
    def __init__(self, engine, evaluator, *, algo="alphabeta", max_depth=6,
                 time_budget_ms=1000, use_tt=True, reuse_tree=True, seed=0, name=None):
        self.engine=engine; self.evaluator=evaluator; self.algo=algo
        self.max_depth=max_depth; self.time_budget_ms=time_budget_ms
        self.use_tt=use_tt; self.reuse_tree=reuse_tree; self.seed=seed
        self.name=name or f"Agent({algo})"
        self._rng=random.Random(seed)
        self.tt={}; self.prev_best=None
        self.nodes=0; self.evals=0; self.tt_hits=0

    def new_game(self, color):
        self.tt={}; self.prev_best=None
        self._rng=random.Random(self.seed)

    def _terminal_value(self, state, player):
        b,w=self.engine.score(state)
        pc = b if player==BLACK else w
        oc = w if player==BLACK else b
        diff = pc-oc
        if diff==0: return 0.0
        return (1 if diff>0 else -1)*(TERMINAL_BASE+abs(diff))

    def _is_terminal(self, state):
        return self.engine.is_terminal(state)

    def _search(self, state, depth, root_player, alpha, beta):
        # returns (score, move, nodes_delta, evals_delta, tt_hits_delta, timed_out)
        engine=self.engine
        if self._is_terminal(state):
            return self._terminal_value(state, root_player), None, 0, 0, 0, False
        ms = engine.legal_moves(state)
        if not ms:
            # pass already? legal_moves returns [PASS] or []
            if ms==[]:
                return self._terminal_value(state, root_player), None, 0,0,0,False
            ms=[PASS]
        if depth==0:
            # evaluate
            self.evals+=1
            return self.evaluator(state, root_player), (ms[0] if ms else None), 0,1,0,False
        # single move shortcut
        if len(ms)==1:
            ns=engine.apply_move(state, ms[0])
            sc,_,_,_,_,_ = self._search(ns, depth-1, root_player, alpha, beta)
            # convert: sc is from root_player perspective already
            return sc, ms[0], 1,0,0,False
        tt_move=None
        if self.use_tt:
            e=self.tt.get(state.hash)
            if e is not None and e[0]==state.black and e[1]==state.white and e[2]==state.player:
                if e[3] >= depth:
                    self.tt_hits+=1
                    return e[4], e[5], 0,0,1,False
                tt_move=e[5]
        # ordering
        order=[]
        if tt_move is not None and tt_move in ms: order.append(tt_move)
        if self.prev_best is not None and self.prev_best in ms and self.prev_best not in order: order.append(self.prev_best)
        corners={0,7,56,63}
        for m in ms:
            if m not in order: order.append(m)
        # corners first
        order.sort(key=lambda m: (0 if m in corners else 1))
        # stable: re-prioritize tt/prev
        prio=[m for m in order if m in (set([tt_move,self.prev_best]) - {None})]
        rest=[m for m in order if m not in prio]
        order=prio+rest

        maximizing = (state.player == root_player)
        best_score=None; best_move=order[0]
        nodes=0; evals=0; hits=0
        alpha0=alpha; beta0=beta
        timed_out=False
        for m in order:
            if time.perf_counter() > self._deadline:
                timed_out=True; break
            ns=engine.apply_move(state,m)
            self.nodes+=1
            sc,_,dn,de,dh,_ = self._search(ns, depth-1, root_player,
                                           alpha if not maximizing else None,  # placeholder
                                           beta)
            # We need proper alpha/beta; redo below instead
            break
        # The above is broken; implement properly:
        return 0.0, None, 0,0,0,False

    def choose_move(self, state):
        # iterative deepening
        engine=self.engine
        root_player=state.player
        ms=engine.legal_moves(state)
        if not ms:
            # pass or terminal
            if ms==[]:
                # terminal; shouldn't happen for choose_move
                return MoveResult(PASS,0.0,0,0,0.0,0,False,0)
            ms=[PASS]
        if len(ms)==1:
            return MoveResult(ms[0], self.evaluator(state,root_player) if False else 0.0, 0,0,0.0,0,False,0)
        # reset counters for this move
        self.nodes=0; self.evals=0; self.tt_hits=0
        start=time.perf_counter()
        self._deadline = start + self.time_budget_ms/1000.0
        best_move=ms[0]; best_score=None; depth_reached=0; timed_out=False
        # proper search functions with alpha/beta
        for d in range(1, self.max_depth+1):
            if time.perf_counter() >= self._deadline:
                break
            # minimax/ab/negamax dispatch
            try:
                sc, mv, to = self._root_search(state, d, root_player)
            except Exception:
                break
            if mv is not None:
                best_move=mv; best_score=sc; depth_reached=d
            if to:
                timed_out=True; break
            if time.perf_counter() >= self._deadline:
                break
        elapsed=(time.perf_counter()-start)*1000
        if best_score is None:
            best_score=self.evaluator(state, root_player)
        self.prev_best=best_move
        return MoveResult(best_move, best_score if best_score is not None else 0.0,
                          self.nodes, self.evals, elapsed, depth_reached, timed_out, self.tt_hits)

    def _root_search(self, state, depth, root_player):
        engine=self.engine
        ms=engine.legal_moves(state)
        if not ms: ms=[PASS] if PASS in (ms or []) else ms
        if not ms: ms=[PASS]
        # alpha-beta
        timed_out=False
        best_score=None; best_move=ms[0]
        alpha=float('-inf'); beta=float('inf')
        order=self._order_moves(state, ms, None)
        for m in order:
            if time.perf_counter() > self._deadline:
                timed_out=True; break
            ns=engine.apply_move(state,m)
            self.nodes+=1
            sc = self._ab(ns, depth-1, root_player, alpha, beta)
            # sc is root_player perspective
            if best_score is None or sc > best_score:
                best_score=sc; best_move=m
            alpha=max(alpha, best_score)
            if beta <= alpha:
                break
        # store TT
        if self.use_tt:
            self.tt[state.hash]=(state.black, state.white, state.player, depth, best_score, best_move)
        return best_score, best_move, timed_out

    def _ab(self, state, depth, root_player, alpha, beta):
        engine=self.engine
        if engine.is_terminal(state):
            return self._terminal_value(state, root_player)
        ms=engine.legal_moves(state)
        if not ms:
            if engine.is_terminal(state):
                return self._terminal_value(state, root_player)
            ms=[PASS]
        if depth==0:
            self.evals+=1
            return self.evaluator(state, root_player)
        if len(ms)==1:
            ns=engine.apply_move(state, ms[0])
            self.nodes+=1
            return self._ab(ns, depth-1, root_player, alpha, beta)
        tt_move=None
        if self.use_tt:
            e=self.tt.get(state.hash)
            if e is not None and e[0]==state.black and e[1]==state.white and e[2]==state.player:
                if e[3] >= depth:
                    self.tt_hits+=1
                    return e[4]
                tt_move=e[5]
        order=self._order_moves(state, ms, tt_move)
        maximizing = (state.player == root_player)
        if maximizing:
            best=float('-inf')
            for m in order:
                if time.perf_counter() > self._deadline:
                    return best if best!=float('-inf') else self.evaluator(state, root_player)
                ns=engine.apply_move(state,m)
                self.nodes+=1
                sc=self._ab(ns, depth-1, root_player, alpha, beta)
                if sc>best: best=sc
                alpha=max(alpha,best)
                if beta<=alpha: break
            if self.use_tt:
                self.tt[state.hash]=(state.black, state.white, state.player, depth, best, None)
            return best
        else:
            best=float('inf')
            for m in order:
                if time.perf_counter() > self._deadline:
                    return best if best!=float('inf') else self.evaluator(state, root_player)
                ns=engine.apply_move(state,m)
                self.nodes+=1
                sc=self._ab(ns, depth-1, root_player, alpha, beta)
                if sc<best: best=sc
                beta=min(beta,best)
                if beta<=alpha: break
            if self.use_tt:
                self.tt[state.hash]=(state.black, state.white, state.player, depth, best, None)
            return best

    def _order_moves(self, state, ms, tt_move):
        order=[]
        if tt_move is not None and tt_move in ms: order.append(tt_move)
        if self.prev_best is not None and self.prev_best in ms and self.prev_best not in order: order.append(self.prev_best)
        corners={0,7,56,63}
        rest=sorted([m for m in ms if m not in order], key=lambda m: (0 if m in corners else 1, m))
        return order+rest