# Author: Théo Cornu
from config import EVALUATION_BOUND
from engine import OthelloEngine
from evals import make_evaluator, EVALUATION_NAMES


def test_perft():
    engine = OthelloEngine()
    state = engine.initial_state()
    expected = {1: 4, 2: 12, 3: 56, 4: 244, 5: 1396, 6: 8200}
    for depth, count in expected.items():
        result = engine.perft(state, depth)
        print(depth, result, count)
        assert result == count
    print("perft OK")


def test_symmetry_and_bounds():
    engine = OthelloEngine()
    state = engine.initial_state()
    for name in EVALUATION_NAMES:
        evaluator = make_evaluator(name, engine)
        for player in (1, 2):
            value = evaluator(state, player)
            assert abs(value) < EVALUATION_BOUND
        assert abs(evaluator(state, 1) + evaluator(state, 2)) < 1e-9
    print("symétrie + bornes OK")


def test_hash_consistency():
    engine = OthelloEngine()
    state = engine.initial_state()
    move = engine.legal_moves(state)[0]
    next_state = engine.apply_move(state, move)
    assert next_state.hash == engine._hash(next_state.black, next_state.white, next_state.player)
    print("hash OK")


if __name__ == "__main__":
    test_perft()
    test_symmetry_and_bounds()
    test_hash_consistency()
    print("TOUT EST OK")