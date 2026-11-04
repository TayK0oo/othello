
import csv, os, time
from engine import State, BLACK, WHITE, PASS, OthelloEngine, CONTRACT_VERSION
from agent import MoveResult
from dataclasses import dataclass

@dataclass
class GameResult:
    winner: int
    score: tuple
    moves: list
    move_results: list

def play_game(engine, black, white, *, game_id="g", out_dir=None):
    black.new_game(BLACK); white.new_game(WHITE)
    state=engine.initial_state()
    moves=[]; mrs=[]
    nplies=0; timeout_violations=0
    while not engine.is_terminal(state):
        ms=engine.legal_moves(state)
        if ms==[]:
            break
        if ms==[PASS]:
            state=engine.apply_move(state, PASS); moves.append(PASS); nplies+=1; continue
        player = black if state.player==BLACK else white
        mr = player.choose_move(state)
        m = mr.move
        if m not in ms:
            winner = WHITE if state.player==BLACK else BLACK
            return GameResult(winner, engine.score(state), moves, mrs)
        if mr.time_ms > 1.10* (getattr(player,'time_budget_ms',1000) or 1000):
            timeout_violations+=1
        state=engine.apply_move(state, m)
        moves.append(m); mrs.append(mr); nplies+=1
    sc=engine.score(state)
    winner = BLACK if sc[0]>sc[1] else (WHITE if sc[1]>sc[0] else 0)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(os.path.join(out_dir,"games"), exist_ok=True)
        with open(os.path.join(out_dir,"moves.csv"),"a",newline="") as f:
            w=csv.writer(f)
            for i,mr in enumerate(mrs):
                w.writerow([CONTRACT_VERSION, game_id, i, "B" if (moves[i] is not None) else "", "", moves[i], mr.eval_score, mr.nodes, mr.evals, round(mr.time_ms,3), mr.depth_reached, mr.timed_out, mr.tt_hits])
        with open(os.path.join(out_dir,"games",f"{game_id}.txt"),"w") as f:
            f.write(f"# game_id={game_id} contract={CONTRACT_VERSION}\n")
            for i,m in enumerate(moves):
                es = mrs[i].eval_score if i < len(mrs) else "-"
                f.write(f"{i};{'B' if (i%2==0) else 'W'};{engine.to_notation(m)};{es}\n")
        with open(os.path.join(out_dir,"matches.csv"),"a",newline="") as f:
            w=csv.writer(f)
            w.writerow([CONTRACT_VERSION, game_id, 0, black.name, white.name, getattr(black,'algo','human'), getattr(white,'algo','human'), "", "", getattr(black,'max_depth',''), getattr(black,'time_budget_ms',''), sc[0], sc[1], winner, nplies, timeout_violations])
    return GameResult(winner, sc, moves, mrs)