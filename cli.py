# Author: Théo Cornu
import sys

from config import OUTPUT_DIR
from engine import OthelloEngine
from harness import play_game
from players import load_player_config, make_profile_player


def print_help(config):
    print("Usage : python cli.py <profil_noir> <profil_blanc> [nb_parties]")
    print("Profils disponibles :", ", ".join(config["profiles"].keys()))
    print("Exemples :")
    print("  python cli.py human mixed_ai")
    print("  python cli.py positional_ai mobility_ai 5")


def main():
    config = load_player_config()
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help", "help"):
        print_help(config)
        return

    black_profile = sys.argv[1]
    white_profile = sys.argv[2]
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    engine = OthelloEngine()
    black = make_profile_player(engine, black_profile, config)
    white = make_profile_player(engine, white_profile, config)

    for game_index in range(games):
        result = play_game(
            engine, black, white,
            game_id=f"{black_profile}_vs_{white_profile}_{game_index}",
            out_dir=OUTPUT_DIR,
        )
        print(
            f"Partie {game_index + 1} : gagnant={result.winner} "
            f"score={result.score} coups={len(result.moves)}"
        )


if __name__ == "__main__":
    main()