# Author: Théo Cornu
"""Lightweight web server (stdlib only) exposing Othello engine + AI."""
import json, os, sys, http.server, socketserver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import OthelloEngine, BLACK, WHITE, PASS
from evals import make_evaluator
from agent import Agent
from human import HumanPlayer
from cli import build as build_player, parse_side

engine = OthelloEngine()
state = {"s": engine.initial_state()}
players = {"black": None, "white": None}

def ensure_players():  # Théo Cornu
    if players["black"] is None:
        players["black"] = build_player(engine, "ai:mixed")
    if players["white"] is None:
        players["white"] = build_player(engine, "human")

def cur_player_obj():  # Théo Cornu
    s = state["s"]
    return players["black"] if s.player == BLACK else players["white"]

def st():  # Théo Cornu
    s = state["s"]
    return {
        "board": engine.board_list(s),
        "player": s.player,
        "legal": engine.legal_moves(s),
        "score": list(engine.score(s)),
        "move_number": s.move_number,
        "terminal": engine.is_terminal(s),
    }

class H(http.server.SimpleHTTPRequestHandler):  # Théo Cornu
    def __init__(self, *a, **k):  # Théo Cornu
        super().__init__(*a, directory=os.path.dirname(os.path.abspath(__file__)), **k)
    def do_GET(self):  # Théo Cornu
        if self.path == "/api/state":
            self._json(st()); return
        return super().do_GET()
    def do_POST(self):  # Théo Cornu
        n=int(self.headers.get("Content-Length",0))
        body=json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/config":
            bspec = body.get("black","ai:mixed")
            wspec = body.get("white","human")
            players["black"] = build_player(engine, bspec)
            players["white"] = build_player(engine, wspec)
            self._json({"ok": True}); return
        if self.path == "/api/new":
            ensure_players()
            players["black"].new_game(BLACK) if hasattr(players["black"],"new_game") else None
            players["white"].new_game(WHITE) if hasattr(players["white"],"new_game") else None
            state["s"] = engine.initial_state()
            self._json(st()); return
        if self.path == "/api/move":
            mv = body.get("move")
            try:
                s = engine.apply_move(state["s"], mv)
            except Exception as e:
                self._json({"error": str(e)}); return
            state["s"] = s
            self._json(st()); return
        if self.path == "/api/ai":
            ensure_players()
            p = cur_player_obj()
            if not hasattr(p, "choose_move") or not hasattr(p, "time_budget_ms"):
                self._json({"error": "current player is human"}); return
            # apply budget/depth/strategy overrides
            if "budget" in body: p.time_budget_ms = int(body["budget"])
            if "depth" in body: p.max_depth = int(body["depth"])
            if "strategy" in body:
                # rebuild eval
                from evals import make_evaluator
                p.evaluator = make_evaluator(body["strategy"], engine)
            r = p.choose_move(state["s"])
            try:
                s = engine.apply_move(state["s"], r.move)
            except Exception as e:
                self._json({"error": str(e)}); return
            state["s"] = s
            out = st()
            out.update({"ai_move": r.move, "ai_notation": engine.to_notation(r.move),
                        "eval_score": r.eval_score, "nodes": r.nodes, "evals": r.evals,
                        "time_ms": round(r.time_ms, 2), "depth_reached": r.depth_reached,
                        "timed_out": r.timed_out})
            self._json(out); return
        self._json({"error": "unknown"}, 404)
    def _json(self, obj, code=200):  # Théo Cornu
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    with socketserver.TCPServer(("", port), H) as httpd:
        print("Serving on http://localhost:" + str(port))
        httpd.serve_forever()
