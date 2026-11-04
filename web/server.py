# Author: Théo Cornu
import http.server
import json
import os
import socketserver
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BLACK, WHITE, PASS
from engine import OthelloEngine
from players import load_player_config, make_profile_player

ENGINE = OthelloEngine()
PLAYER_CONFIG = load_player_config()
GAME = {"state": ENGINE.initial_state()}
PLAYERS = {"black": None, "white": None}


def current_player():
    return PLAYERS["black"] if GAME["state"].player == BLACK else PLAYERS["white"]


def ensure_players():
    if PLAYERS["black"] is None:
        PLAYERS["black"] = make_profile_player(ENGINE, PLAYER_CONFIG["default_black"], PLAYER_CONFIG)
    if PLAYERS["white"] is None:
        PLAYERS["white"] = make_profile_player(ENGINE, PLAYER_CONFIG["default_white"], PLAYER_CONFIG)


def state_payload():
    state = GAME["state"]
    return {
        "board": ENGINE.board_list(state),
        "player": state.player,
        "legal": ENGINE.legal_moves(state),
        "score": list(ENGINE.score(state)),
        "move_number": state.move_number,
        "terminal": ENGINE.is_terminal(state),
    }


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self.send_json(state_payload())
            return
        if self.path == "/api/profiles":
            self.send_json(PLAYER_CONFIG)
            return
        super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        if self.path == "/api/config":
            PLAYERS["black"] = make_profile_player(ENGINE, body.get("black", PLAYER_CONFIG["default_black"]), PLAYER_CONFIG)
            PLAYERS["white"] = make_profile_player(ENGINE, body.get("white", PLAYER_CONFIG["default_white"]), PLAYER_CONFIG)
            self.send_json({"ok": True})
            return

        if self.path == "/api/new":
            ensure_players()
            PLAYERS["black"].new_game(BLACK)
            PLAYERS["white"].new_game(WHITE)
            GAME["state"] = ENGINE.initial_state()
            self.send_json(state_payload())
            return

        if self.path == "/api/move":
            try:
                GAME["state"] = ENGINE.apply_move(GAME["state"], body.get("move"))
            except Exception as error:
                self.send_json({"error": str(error)})
                return
            self.send_json(state_payload())
            return

        if self.path == "/api/ai":
            ensure_players()
            player = current_player()
            if not hasattr(player, "time_budget_ms"):
                self.send_json({"error": "le joueur courant est humain"})
                return
            if "budget_ms" in body:
                player.time_budget_ms = int(body["budget_ms"])
            if "depth" in body:
                player.max_depth = int(body["depth"])
            if "strategy" in body:
                from evals import make_evaluator
                player.evaluator = make_evaluator(body["strategy"], ENGINE)
            result = player.choose_move(GAME["state"])
            try:
                GAME["state"] = ENGINE.apply_move(GAME["state"], result.move)
            except Exception as error:
                self.send_json({"error": str(error)})
                return
            payload = state_payload()
            payload.update({
                "ai_move": result.move,
                "ai_notation": ENGINE.to_notation(result.move),
                "eval_score": result.eval_score,
                "nodes": result.nodes,
                "evals": result.evals,
                "time_ms": round(result.time_ms, 2),
                "depth_reached": result.depth_reached,
                "timed_out": result.timed_out,
            })
            self.send_json(payload)
            return

        self.send_json({"error": "route inconnue"}, 404)

    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    with socketserver.TCPServer(("", port), RequestHandler) as server:
        print(f"http://localhost:{port}")
        server.serve_forever()