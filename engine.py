# Author: Théo Cornu
from dataclasses import dataclass
import random

from config import (
    BLACK, WHITE, PASS, CELL_COUNT, BOARD_SIZE,
    ZOBRIST_SEED,
)

DIRECTIONS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]


@dataclass(frozen=True, slots=True)
class State:
    black: int
    white: int
    player: int
    move_number: int
    hash: int


def _popcount(bits):
    return bin(bits).count("1")


class OthelloEngine:
    def __init__(self, seed=ZOBRIST_SEED):
        generator = random.Random(seed)
        self.zobrist_table = [[generator.getrandbits(64) for _ in range(3)] for _ in range(CELL_COUNT)]
        self.zobrist_side_key = generator.getrandbits(64)

    def _hash(self, black, white, player):
        value = 0
        black_bits = black
        while black_bits:
            index = (black_bits & -black_bits).bit_length() - 1
            value ^= self.zobrist_table[index][BLACK]
            black_bits &= black_bits - 1
        white_bits = white
        while white_bits:
            index = (white_bits & -white_bits).bit_length() - 1
            value ^= self.zobrist_table[index][WHITE]
            white_bits &= white_bits - 1
        if player == WHITE:
            value ^= self.zobrist_side_key
        return value

    def initial_state(self):
        black = (1 << (3 * BOARD_SIZE + 4)) | (1 << (4 * BOARD_SIZE + 3))
        white = (1 << (3 * BOARD_SIZE + 3)) | (1 << (4 * BOARD_SIZE + 4))
        return State(black, white, WHITE, 0, self._hash(black, white, WHITE))

    def _bits_of(self, state, player):
        return state.black if player == BLACK else state.white

    def _legal_moves_for(self, black, white, player):
        own = black if player == BLACK else white
        other = white if player == BLACK else black
        occupied = black | white
        moves = []
        for index in range(CELL_COUNT):
            if occupied & (1 << index):
                continue
            row, col = divmod(index, BOARD_SIZE)
            found = False
            for delta_row, delta_col in DIRECTIONS:
                next_row, next_col = row + delta_row, col + delta_col
                seen_other = False
                while 0 <= next_row < BOARD_SIZE and 0 <= next_col < BOARD_SIZE:
                    bit = 1 << (next_row * BOARD_SIZE + next_col)
                    if other & bit:
                        seen_other = True
                        next_row += delta_row
                        next_col += delta_col
                        continue
                    if own & bit and seen_other:
                        found = True
                    break
                if found:
                    break
            if found:
                moves.append(index)
        return sorted(moves)

    def legal_moves(self, state):
        moves = self._legal_moves_for(state.black, state.white, state.player)
        if moves:
            return moves
        opponent_moves = self._legal_moves_for(state.black, state.white, 3 - state.player)
        if opponent_moves:
            return [PASS]
        return []

    def apply_move(self, state, move):
        if move == PASS:
            if self.legal_moves(state) != [PASS]:
                raise ValueError("coup de passe illégal")
            next_player = 3 - state.player
            return State(state.black, state.white, next_player, state.move_number,
                         state.hash ^ self.zobrist_side_key)
        if move not in self.legal_moves(state):
            raise ValueError("coup illégal")
        player = state.player
        opponent = 3 - player
        own = self._bits_of(state, player)
        other = self._bits_of(state, opponent)
        row, col = divmod(move, BOARD_SIZE)
        new_own = own | (1 << move)
        new_other = other
        for delta_row, delta_col in DIRECTIONS:
            next_row, next_col = row + delta_row, col + delta_col
            path = []
            while 0 <= next_row < BOARD_SIZE and 0 <= next_col < BOARD_SIZE:
                bit = 1 << (next_row * BOARD_SIZE + next_col)
                if other & bit:
                    path.append((next_row, next_col))
                    next_row += delta_row
                    next_col += delta_col
                    continue
                if own & bit and path:
                    for cell_row, cell_col in path:
                        new_other &= ~(1 << (cell_row * BOARD_SIZE + cell_col))
                        new_own |= (1 << (cell_row * BOARD_SIZE + cell_col))
                break
        if player == BLACK:
            new_black, new_white = new_own, new_other
        else:
            new_black, new_white = new_other, new_own
        next_player = opponent
        return State(new_black, new_white, next_player, state.move_number + 1,
                     self._hash(new_black, new_white, next_player))

    def is_terminal(self, state):
        if (state.black | state.white) == (1 << CELL_COUNT) - 1:
            return True
        if self.legal_moves(state):
            return False
        return not self._legal_moves_for(state.black, state.white, 3 - state.player)

    def score(self, state):
        return _popcount(state.black), _popcount(state.white)

    def mobility(self, state, player):
        return len(self._legal_moves_for(state.black, state.white, player))

    def board_list(self, state):
        cells = [0] * CELL_COUNT
        for index in range(CELL_COUNT):
            if state.black & (1 << index):
                cells[index] = BLACK
            elif state.white & (1 << index):
                cells[index] = WHITE
        return cells

    def to_notation(self, move):
        if move == PASS:
            return "pass"
        row, col = divmod(move, BOARD_SIZE)
        return f"{chr(ord('a') + col)}{row + 1}"

    def from_notation(self, text):
        value = text.strip().lower()
        if value == "pass":
            return PASS
        col = ord(value[0]) - ord("a")
        row = int(value[1:]) - 1
        return row * BOARD_SIZE + col

    def perft(self, state, depth):
        if depth == 0:
            return 1
        moves = self.legal_moves(state)
        if not moves:
            if self.is_terminal(state):
                return 1
            moves = [PASS]
        total = 0
        for move in moves:
            total += self.perft(self.apply_move(state, move), depth - 1)
        return total


ENGINE = OthelloEngine()