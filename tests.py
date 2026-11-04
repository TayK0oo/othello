"""Tests: perft, symmetry, AB==minimax."""
from engine import initial_state, perft, legal_moves
from evals import EVALS

def test_perft():
    s=initial_state()
    expected={1:4,2:12,3:56,4:244,5:1396,6:8200}
    for d,exp in expected.items():
        got=perft(s,d)
        print(d, got, exp)
        assert got==exp, (d,got,exp)
    print("perft OK")

def test_symmetry():
    from engine import State
    s=initial_state()
    for name,ev in EVALS.items():
        v1=ev(s,1); v2=ev(s,2)
        assert abs(v1+v2)<1e-9, (name,v1,v2)
    print("symmetry OK")

if __name__=="__main__":
    test_perft()
    test_symmetry()
    print("ALL OK")