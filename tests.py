# Author: Théo Cornu

from engine import OthelloEngine, BLACK, WHITE, PASS
from evals import make_evaluator, EVALS_NAMES

def test_perft():  # Théo Cornu
    eng=OthelloEngine()
    s=eng.initial_state()
    expected={1:4,2:12,3:56,4:244,5:1396,6:8200}
    for d,exp in expected.items():
        got=eng.perft(s,d)
        print(d, got, exp)
        assert got==exp, (d,got,exp)
    print("perft OK")

def test_symmetry():  # Théo Cornu
    eng=OthelloEngine()
    s=eng.initial_state()
    for name in EVALS_NAMES:
        ev=make_evaluator(name, eng)
        v1=ev(s,1); v2=ev(s,2)
        assert abs(v1+v2)<1e-9, (name,v1,v2)
        assert abs(v1)<1000
    print("symmetry+bounds OK")

def test_hash_incremental():  # Théo Cornu
    eng=OthelloEngine()
    s=eng.initial_state()
    ms=eng.legal_moves(s)
    s2=eng.apply_move(s, ms[0])
    assert s2.hash == eng._hash(s2.black, s2.white, s2.player)
    print("hash OK")

if __name__=="__main__":
    test_perft()
    test_symmetry()
    test_hash_incremental()
    print("ALL OK")
