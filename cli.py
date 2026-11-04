"""CLI: human vs AI, replay, export eval scores."""
import sys
from engine import initial_state, apply_move, legal_moves, is_terminal, score
from agent import Agent

def human_vs_ai(evaluator, algo="alphabeta", depth=4, budget=1000):
    agent=Agent(evaluator,max_depth=depth,time_budget_ms=budget,algo=algo)
    state=initial_state()
    eval_log=[]
    while not is_terminal(state):
        ms=legal_moves(state)
        if not ms:
            print("Pass")
            state=apply_move(state,-1); continue
        print("Board:", state.board)
        print("Player:", state.player, "legal:", ms)
        if state.player==2:  # human plays white
            try:
                m=int(input("Your move (index or -1 pass): "))
            except EOFError:
                m=ms[0]
        else:
            r=agent.choose_move(state,ms)
            m=r["move"]
            print("AI move", m, r)
        if m not in ms and m!=-1:
            print("illegal, using first"); m=ms[0]
        eval_log.append((state.player, m))
        state=apply_move(state,m)
    b,w=score(state)
    print("Final", b, w)
    with open("eval_scores.txt","w") as f:
        for p,m in eval_log:
            f.write(f"player={p} move={m}\n")
    print("exported eval_scores.txt")

if __name__=="__main__":
    from evals import EVALS
    strat=sys.argv[1] if len(sys.argv)>1 else "mixed"
    human_vs_ai(EVALS[strat])