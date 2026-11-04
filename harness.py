# Author: Théo Cornu
import csv
import os
from dataclasses import dataclass

from config import BLACK, WHITE, PASS, CONTRACT_VERSION, TIME_TOLERANCE, OUTPUT_DIR


@dataclass
class GameResult:
    winner: int
    score: tuple
    moves: list
    move_results: list


def _player_name(player):
    return getattr(player, "name", player.__class__.__name__)


def _player_algo(player):
    return getattr(player, "algo", "human")


def _player_depth(player):
    return getattr(player, "max_depth", "")


def _player_budget(player):
    return getattr(player, "time_budget_ms", "")


def _write_outputs(engine, game_id, black, white, result, out_dir):
    os.makedirs(os.path.join(out_dir, "games"), exist_ok=True)

    with open(os.path.join(out_dir, "moves.csv"), "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for index, move_result in enumerate(result.move_results):
            writer.writerow([
                CONTRACT_VERSION, game_id, index, move_result.move,
                move_result.eval_score, move_result.nodes, move_result.evals,
                round(move_result.time_ms, 3), move_result.depth_reached,
                move_result.timed_out, move_result.tt_hits,
            ])

    with open(os.path.join(out_dir, "games", f"{game_id}.txt"), "w", encoding="utf-8") as file:
        file.write(f"# game_id={game_id} contract={CONTRACT_VERSION}\n")
        for index, move in enumerate(result.moves):
            score = result.move_results[index].eval_score if index < len(result.move_results) else "-"
            file.write(f"{index};{engine.to_notation(move)};{score}\n")

    with open(os.path.join(out_dir, "matches.csv"), "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            CONTRACT_VERSION, game_id, _player_name(black), _player_name(white),
            _player_algo(black), _player_algo(white),
            _player_depth(black), _player_budget(black),
            result.score[0], result.score[1], result.winner,
            len(result.moves),
        ])


def play_game(engine, black, white, *, game_id="game", out_dir=OUTPUT_DIR):
    black.new_game(BLACK)
    white.new_game(WHITE)
    state = engine.initial_state()
    moves = []
    move_results = []

    while not engine.is_terminal(state):
        legal = engine.legal_moves(state)
        if not legal:
            break
        if legal == [PASS]:
            state = engine.apply_move(state, PASS)
            moves.append(PASS)
            continue

        player = black if state.player == BLACK else white
        move_result = player.choose_move(state)
        move = move_result.move
        if move not in legal:
            winner = WHITE if state.player == BLACK else BLACK
            result = GameResult(winner, engine.score(state), moves, move_results)
            _write_outputs(engine, game_id, black, white, result, out_dir)
            return result

        budget = getattr(player, "time_budget_ms", 1000) or 1000
        if move_result.time_ms > TIME_TOLERANCE * budget:
            move_result.timed_out = True

        state = engine.apply_move(state, move)
        moves.append(move)
        move_results.append(move_result)

    final_score = engine.score(state)
    winner = BLACK if final_score[0] > final_score[1] else (
        WHITE if final_score[1] > final_score[0] else 0
    )
    result = GameResult(winner, final_score, moves, move_results)
    _write_outputs(engine, game_id, black, white, result, out_dir)
    return result