# Author: Théo Cornu
from config import BLACK, WHITE, EVALUATION_BOUND, EARLY_MOVES, ENDGAME_EMPTIES

POSITION_WEIGHTS = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100],
]

POSITION_WEIGHTS_FLAT = [
    POSITION_WEIGHTS[row][col] for row in range(8) for col in range(8)
]

CORNER_INDICES = (0, 7, 56, 63)
EVALUATION_NAMES = ["positional", "absolute", "mobility", "mixed"]


def opponent_of(player):
    return 3 - player


def _piece_count(bits):
    return bin(bits).count("1")


def eval_positional(state, player, engine=None):
    score = 0
    for index in range(64):
        if state.black & (1 << index):
            score += POSITION_WEIGHTS_FLAT[index] if player == BLACK else -POSITION_WEIGHTS_FLAT[index]
        elif state.white & (1 << index):
            score += POSITION_WEIGHTS_FLAT[index] if player == WHITE else -POSITION_WEIGHTS_FLAT[index]
    return float(score)


def eval_absolute(state, player, engine=None):
    black_count = _piece_count(state.black)
    white_count = _piece_count(state.white)
    own = black_count if player == BLACK else white_count
    other = white_count if player == BLACK else black_count
    return float(own - other)


def eval_mobility(state, player, engine):
    own_moves = engine.mobility(state, player)
    other_moves = engine.mobility(state, opponent_of(player))
    own_bits = state.black if player == BLACK else state.white
    other_bits = state.white if player == BLACK else state.black
    own_corners = sum(1 for index in CORNER_INDICES if own_bits & (1 << index))
    other_corners = sum(1 for index in CORNER_INDICES if other_bits & (1 << index))
    own_pieces = _piece_count(own_bits)
    other_pieces = _piece_count(other_bits)
    return float((own_moves - other_moves) + 10 * (own_corners - other_corners) + (own_pieces - other_pieces))


def eval_mixed(state, player, engine):
    empties = 64 - _piece_count(state.black | state.white)
    if state.move_number < EARLY_MOVES:
        return eval_positional(state, player, engine)
    if empties <= ENDGAME_EMPTIES:
        return eval_absolute(state, player, engine)
    return eval_mobility(state, player, engine)


def make_evaluator(name, engine):
    evaluators = {
        "positional": lambda state, player: eval_positional(state, player, engine),
        "absolute": lambda state, player: eval_absolute(state, player, engine),
        "mobility": lambda state, player: eval_mobility(state, player, engine),
        "mixed": lambda state, player: eval_mixed(state, player, engine),
    }
    if name not in evaluators:
        raise ValueError(f"stratégie inconnue : {name}")
    return evaluators[name]