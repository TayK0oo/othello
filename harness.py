"""Match harness: N games, seeds, CSV."""
import csv, time, random
from engine import initial_state, apply_move, is_terminal, legal_moves, score
from agent import Agent

def play_game(agent_black, agent_white, max_moves=120):
    # black=1, white=2; white starts per subject
    state=initial_state()
    moves=[]
    t0=time.time()
    n=0
    while not is_terminal(state) and n<max_moves:
        ms=legal_moves(state)
        if not ms:
            state=apply_move(state,-1); moves.append(-1); n+=1; continue
        agent = agent_white if state.player==2 else agent_black
        r=agent.choose_move(state,ms)
        m=r["move"]
        if m not in ms and m!=-1:
            m=ms[0]
        state=apply_move(state,m); moves.append(m); n+=1
    b,w=score(state)
    winner = 1 if b>w else (2 if w>b else 0)
    return {"winner":winner,"black":b,"white":w,"moves":moves,"time_s":time.time()-t0}

def run_campaign(agentA_factory, agentB_factory, n_games=10, csv_path="results.csv"):
    rows=[]
    for g in range(n_games):
        # alternate sides
        if g%2==0:
            ab=agentA_factory(); aw=agentB_factory()
            sideA="black"
        else:
            ab=agentB_factory(); aw=agentA_factory()
            sideA="white"
        res=play_game(ab,aw)
        a_score = res["black"] if sideA=="black" else res["white"]
        b_score = res["white"] if sideA=="black" else res["black"]
        a_win = (res["winner"]==1 and sideA=="black") or (res["winner"]==2 and sideA=="white")
        rows.append({"game":g,"sideA":sideA,"A_score":a_score,"B_score":b_score,
                     "A_win":int(a_win),"draw":int(res["winner"]==0)})
    with open(csv_path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return rows