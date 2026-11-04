"""Lightweight web server (stdlib only) exposing Othello engine + AI."""
import json, os, sys, http.server, socketserver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import OthelloEngine, BLACK, WHITE, PASS
from evals import make_evaluator
from agent import Agent

engine = OthelloEngine()
state = {"s": engine.initial_state()}
ai = {"a": None}

def st():
    s = state["s"]
    return {
        "board": engine.board_list(s),
        "player": s.player,
        "legal": engine.legal_moves(s),
        "score": list(engine.score(s)),
        "move_number": s.move_number,
        "terminal": engine.is_terminal(s),
        "empties": 64 - (bin(s.black|s.white).count("1")),
    }

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.dirname(os.path.abspath(__file__)), **k)
    def do_GET(self):
        if self.path == "/api/state":
            self._json(st()); return
        return super().do_GET()
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        body=json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/new":
            state["s"]=engine.initial_state()
            ai["a"]=None
            self._json(st()); return
        if self.path == "/api/move":
            mv=body.get("move")
            try:
                s=engine.apply_move(state["s"], mv)
            except Exception as e:
                self._json({"error":str(e)}); return
            state["s"]=s
            self._json(st()); return
        if self.path == "/api/ai":
            strat=body.get("strategy","mixed")
            budget=int(body.get("budget",1000))
            depth=int(body.get("depth",6))
            algo=body.get("algo","alphabeta")
            if ai["a"] is None:
                ev=make_evaluator(strat, engine)
                ai["a"]=Agent(engine, ev, algo=algo, max_depth=depth, time_budget_ms=budget, name="AI")
                ai["a"].new_game(state["s"].player)
            a=ai["a"]
            r=a.choose_move(state["s"])
            try:
                s=engine.apply_move(state["s"], r.move)
            except Exception as e:
                self._json({"error":str(e)}); return
            state["s"]=s
            out=st()
            out["ai_move"]=r.move
            out["ai_notation"]=engine.to_notation(r.move)
            out["eval_score"]=r.eval_score
            out["nodes"]=r.nodes
            out["evals"]=r.evals
            out["time_ms"]=round(r.time_ms,2)
            out["depth_reached"]=r.depth_reached
            out["timed_out"]=r.timed_out
            self._json(out); return
        self._json({"error":"unknown"},404)
    def _json(self, obj, code=200):
        data=json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__=="__main__":
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8000
    with socketserver.TCPServer(("",port),H) as httpd:
        print("Serving on http://localhost:"+str(port))
        httpd.serve_forever()