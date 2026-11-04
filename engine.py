"""Othello engine v1.1 (bitboards, Zobrist)."""
import time, random
from dataclasses import dataclass, field

BLACK, WHITE, PASS = 1, 2, -1
CONTRACT_VERSION = "1.1"
EVAL_BOUND = 1000
TERMINAL_BASE = 10000

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

@dataclass(frozen=True, slots=True)
class State:
    black: int
    white: int
    player: int
    move_number: int
    hash: int

def _popcount(x): return bin(x).count("1")

class OthelloEngine:
    def __init__(self, seed=0xC0FFEE):
        rng = random.Random(seed)
        self.Z = [[rng.getrandbits(64) for _ in range(3)] for _ in range(64)]  # [cell][piece 0/1/2], piece 0 unused
        self.Z_SIDE = rng.getrandbits(64)

    def _hash(self, black, white, player):
        h = 0
        bb = black
        while bb:
            i = (bb & -bb).bit_length()-1
            h ^= self.Z[i][BLACK]; bb &= bb-1
        ww = white
        while ww:
            i = (ww & -ww).bit_length()-1
            h ^= self.Z[i][WHITE]; ww &= ww-1
        if player == WHITE:
            h ^= self.Z_SIDE
        return h

    def initial_state(self) -> State:
        black = (1<<(3*8+4)) | (1<<(4*8+3))
        white = (1<<(3*8+3)) | (1<<(4*8+4))
        return State(black, white, WHITE, 0, self._hash(black, white, WHITE))

    def _player_bb(self, state, p):
        return state.black if p==BLACK else state.white
    def _opp_bb(self, state, p):
        return state.white if p==BLACK else state.black

    def legal_moves(self, state) -> list[int]:
        p = state.player; opp = 3-p
        own = self._player_bb(state, p); other = self._player_bb(state, opp)
        occupied = state.black | state.white
        # any move?
        res = []
        for idx in range(64):
            if occupied & (1<<idx): continue
            r,c = divmod(idx,8)
            ok=False
            for dr,dc in DIRS:
                nr,nc = r+dr, c+dc
                seen=False
                while 0<=nr<8 and 0<=nc<8:
                    bit = 1<<(nr*8+nc)
                    if other & bit:
                        seen=True; nr+=dr; nc+=dc; continue
                    if own & bit and seen:
                        ok=True
                    break
                if ok: break
            if ok:
                res.append(idx)
        if res:
            return sorted(res)
        # pass?
        opp_state = State(state.black, state.white, opp, state.move_number, state.hash ^ self.Z_SIDE)  # hash flip side (approx)
        # recompute legal for opp
        opp_moves = self.legal_moves_raw(state.black, state.white, opp)
        if opp_moves:
            return [PASS]
        return []

    def legal_moves_raw(self, black, white, p):
        own = black if p==BLACK else white
        other = white if p==BLACK else black
        occupied = black | white
        res=[]
        for idx in range(64):
            if occupied & (1<<idx): continue
            r,c=divmod(idx,8)
            ok=False
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc; seen=False
                while 0<=nr<8 and 0<=nc<8:
                    bit=1<<(nr*8+nc)
                    if other & bit:
                        seen=True; nr+=dr; nc+=dc; continue
                    if own & bit and seen:
                        ok=True
                    break
                if ok: break
            if ok: res.append(idx)
        return sorted(res)

    def apply_move(self, state, move: int) -> State:
        if move == PASS:
            # validate pass allowed
            if self.legal_moves(state) != [PASS]:
                # pass allowed only when no moves for player but opp has
                if PASS not in self.legal_moves(state):
                    raise ValueError("illegal pass")
            p = 3 - state.player
            new_hash = state.hash ^ self.Z_SIDE
            return State(state.black, state.white, p, state.move_number, new_hash)
        # validate
        if move not in self.legal_moves(state):
            raise ValueError(f"illegal move {move}")
        p = state.player; opp = 3-p
        own = self._player_bb(state, p)
        other = self._player_bb(state, opp)
        idx = move
        r,c = divmod(idx,8)
        new_own = own | (1<<idx)
        new_other = other
        for dr,dc in DIRS:
            nr,nc = r+dr, c+dc
            path=[]
            while 0<=nr<8 and 0<=nc<8:
                bit=1<<(nr*8+nc)
                if other & bit:
                    path.append((nr,nc)); nr+=dr; nc+=dc; continue
                if own & bit and path:
                    for (rr,cc) in path:
                        new_other &= ~(1<<(rr*8+cc))
                        new_own |= (1<<(rr*8+cc))
                break
        if p==BLACK:
            new_black, new_white = new_own, new_other
        else:
            new_black, new_white = new_other, new_own
        new_move_number = state.move_number + 1
        new_player = opp
        new_hash = self._hash(new_black, new_white, new_player)
        return State(new_black, new_white, new_player, new_move_number, new_hash)

    def is_terminal(self, state) -> bool:
        if state.black | state.white == (1<<64)-1:
            return True
        if self.legal_moves(state):
            return False
        opp = 3-state.player
        if self.legal_moves_raw(state.black, state.white, opp):
            return False
        return True

    def score(self, state) -> tuple[int,int]:
        return _popcount(state.black), _popcount(state.white)

    def mobility(self, state, player) -> int:
        return len(self.legal_moves_raw(state.black, state.white, player))

    def board_list(self, state) -> list[int]:
        out=[0]*64
        for i in range(64):
            if state.black & (1<<i): out[i]=BLACK
            elif state.white & (1<<i): out[i]=WHITE
        return out

    def to_notation(self, move: int) -> str:
        if move == PASS: return "pass"
        r,c = divmod(move,8)
        return f"{chr(ord('a')+c)}{r+1}"

    def from_notation(self, text: str) -> int:
        t=text.strip().lower()
        if t=="pass": return PASS
        c=ord(t[0])-ord('a'); r=int(t[1:])-1
        return r*8+c

    def perft(self, state, depth: int) -> int:
        if depth==0: return 1
        ms = self.legal_moves(state)
        if not ms:
            if self.is_terminal(state): return 1
            ms=[PASS]
        total=0
        for m in ms:
            total += self.perft(self.apply_move(state,m), depth-1)
        return total

ENGINE = OthelloEngine()