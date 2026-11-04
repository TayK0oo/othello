# Author: Théo Cornu

import time
from agent import MoveResult

class HumanPlayer:  # Théo Cornu
    def __init__(self, engine, name="Human"):  # Théo Cornu
        self.engine=engine; self.name=name
    def new_game(self, color):  # Théo Cornu
        pass
    def choose_move(self, state):  # Théo Cornu
        eng=self.engine
        ms=eng.legal_moves(state)
        if not ms:
            ms=[-1]
        print("Legal moves:", [eng.to_notation(m) for m in ms])
        while True:
            try:
                txt=input("Your move (e.g. d3, or pass): ").strip()
            except EOFError:
                txt="pass"
            try:
                m=eng.from_notation(txt)
            except Exception:
                print("parse error"); continue
            if m in ms:
                break
            print("illegal, try again")
        t0=time.perf_counter()
        elapsed=(time.perf_counter()-t0)*1000
        return MoveResult(m, 0.0, 0, 0, elapsed, 0, False, 0)
