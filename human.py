# Author: Théo Cornu
import time

from agent import MoveResult, Player
from config import PASS


class HumanPlayer(Player):
    def __init__(self, engine, name="Humain"):
        self.engine = engine
        self.name = name

    def new_game(self, color):
        return None

    def choose_move(self, state):
        legal = self.engine.legal_moves(state)
        if not legal:
            legal = [PASS]
        print("Coups légaux :", [self.engine.to_notation(move) for move in legal])
        while True:
            try:
                text = input("Votre coup (ex: d3, pass) : ").strip()
            except EOFError:
                text = "pass"
            try:
                move = self.engine.from_notation(text)
            except Exception:
                print("Format invalide, réessayez.")
                continue
            if move in legal:
                break
            print("Coup illégal, réessayez.")
        start = time.perf_counter()
        elapsed = (time.perf_counter() - start) * 1000
        return MoveResult(move, 0.0, 0, 0, elapsed, 0, False, 0)