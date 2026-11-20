# Author: Théo Cornu
import contextlib

import io
from itertools import permutations

from config import BLACK, WHITE, OUTPUT_DIR
from engine import OthelloEngine
from harness import play_game
from players import make_ai

DEFAULT_STRATEGIES = ["positional", "absolute", "mobility", "mixed"]

def run_pairing(engine, first, second, games=2, depth=4, budget_ms=300):
    results = {first: 0, second: 0, "draw": 0}
    for game_index in range(games):
        if game_index % 2 == 0:
            black_name, white_name = first, second
        else:
            black_name, white_name = second, first
        black = make_ai(engine, black_name, depth=depth, budget_ms=budget_ms, name=black_name)
        white = make_ai(engine, white_name, depth=depth, budget_ms=budget_ms, name=white_name)
        with contextlib.redirect_stdout(io.StringIO()):
            result = play_game(
                engine, black, white,
                game_id=f"camp_{first}_vs_{second}_{game_index}",
                out_dir=OUTPUT_DIR,
            )
        if result.winner == 0:
            results["draw"] += 1
        elif (result.winner == BLACK and black_name == first) or (result.winner == WHITE and white_name == first):
            results[first] += 1
        else:
            results[second] += 1
    return results

def round_robin(strategies=None, games=2, depth=4, budget_ms=300):
    strategies = strategies or DEFAULT_STRATEGIES
    engine = OthelloEngine()
    totals = {name: {"wins": 0, "losses": 0, "draws": 0} for name in strategies}
    direct = {}
    for first, second in permutations(strategies, 2):
        result = run_pairing(engine, first, second, games, depth, budget_ms)
        direct[(first, second)] = result
        totals[first]["wins"] += result[first]
        totals[first]["losses"] += result[second]
        totals[first]["draws"] += result["draw"]
        totals[second]["wins"] += result[second]
        totals[second]["losses"] += result[first]
        totals[second]["draws"] += result["draw"]
    return totals, direct

def print_report(totals, direct):
    print("| Stratégie | Victoires | Défaites | Nulles |")
    print("|---|---|---|---|")
    for name, values in totals.items():
        print(f"| {name} | {values['wins']} | {values['losses']} | {values['draws']} |")
    print()
    names = list(totals.keys())
    print("| Noir \\ Blanc | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for first in names:
        cells = []
        for second in names:
            if first == second:
                cells.append("—")
            else:
                result = direct.get((first, second))
                cells.append(f"{result[first]}-{result[second]}" if result else "")
        print(f"| {first} | " + " | ".join(cells) + " |")

if __name__ == "__main__":
    totals, direct = round_robin(games=2, depth=3, budget_ms=100)
    print_report(totals, direct)