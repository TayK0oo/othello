"""Othello engine: rules, moves, terminal, scoring. Dev A owns this."""
from dataclasses import dataclass
from typing import List, Tuple

EMPTY, BLACK, WHITE = 0, 1, 2
DIRS = (-9, -8, -7, -1, 1, 7, 8, 9)  # row/col aware via bounds check

@dataclass(frozen=True)
class State:
    board: Tuple[int, ...]   # length 64
    player: int              # player to move: 1 black or 2 white

def initial_state() -> State:
    b = [EMPTY]*64
    b[3*8+3] = WHITE
    b[3*8+4] = BLACK
    b[4*8+3] = BLACK
    b[4*8+4] = WHITE
    return State(tuple(b), WHITE)  # whites start

def _neighbors(idx):
    r, c = divmod(idx, 8)
    out = []
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr==0 and dc==0: continue
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                out.append((nr*8+nc, dr, dc))
    return out

def legal_moves(state: State) -> List[int]:
    b = state.board; p = state.player; opp = 3-p
    moves = []
    for idx in range(64):
        if b[idx] != EMPTY: continue
        ok = False
        r, c = divmod(idx, 8)
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==0 and dc==0: continue
                nr, nc = r+dr, c+dc
                # walk
                seen = False
                while 0 <= nr < 8 and 0 <= nc < 8:
                    v = b[nr*8+nc]
                    if v == opp:
                        seen = True
                        nr += dr; nc += dc
                        continue
                    if v == p and seen:
                        ok = True
                    break
                if ok: break
            if ok: break
        if ok:
            moves.append(idx)
    return moves

def apply_move(state: State, move: int) -> State:
    # move == -1 means pass
    if move == -1:
        return State(state.board, 3-state.player)
    b = list(state.board); p = state.player; opp = 3-p
    r, c = divmod(move, 8)
    b[move] = p
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr==0 and dc==0: continue
            nr, nc = r+dr, c+dc
            path = []
            while 0 <= nr < 8 and 0 <= nc < 8 and b[nr*8+nc] == opp:
                path.append((nr, nc))
                nr += dr; nc += dc
            if path and 0 <= nr < 8 and 0 <= nc < 8 and b[nr*8+nc] == p:
                for (rr, cc) in path:
                    b[rr*8+cc] = p
    return State(tuple(b), opp)

def is_terminal(state: State) -> bool:
    if EMPTY not in state.board:
        return True
    if legal_moves(state):
        return False
    # opponent also no moves?
    opp_state = State(state.board, 3-state.player)
    return not legal_moves(opp_state)

def score(state: State) -> Tuple[int, int]:
    b = state.board
    black = b.count(BLACK)
    white = b.count(WHITE)
    return black, white

def perft(state: State, depth: int) -> int:
    if depth == 0:
        return 1
    moves = legal_moves(state)
    if not moves:
        if is_terminal(state):
            return 1
        moves = [-1]
    total = 0
    for m in moves:
        total += perft(apply_move(state, m), depth-1)
    return total
def count_pieces(board, player):
    return board.count(player)