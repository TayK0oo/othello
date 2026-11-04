# Author: Théo Cornu
# Configuration centrale du projet Othello.
# Modifier ce fichier suffit pour changer les valeurs par défaut.

CONTRACT_VERSION = "1.1"

# --- Plateau et pions ---
BOARD_SIZE = 8
CELL_COUNT = 64
EMPTY = 0
BLACK = 1
WHITE = 2
PASS = -1

# --- Évaluation ---
EVALUATION_BOUND = 1000
TERMINAL_SCORE_BASE = 10000
EARLY_MOVES = 22
ENDGAME_EMPTIES = 12

# --- Recherche ---
DEFAULT_STRATEGY = "mixed"
DEFAULT_ALGO = "alphabeta"
DEFAULT_DEPTH = 6
DEFAULT_BUDGET_MS = 1000
TIME_TOLERANCE = 1.10

# --- Reproductibilité ---
ZOBRIST_SEED = 0xC0FFEE

# --- Sorties ---
OUTPUT_DIR = "runs"