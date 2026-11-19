"""Zobrist Hashing and Transposition Table for Connect 4."""
from __future__ import annotations

import random
from typing import Any
from engine.base import Game, normalize_player

# Generate deterministic 64-bit Zobrist table for Connect 4 (6 rows x 7 cols x 2 players)
_rng = random.Random(20261118)
ZOBRIST_TABLE: dict[tuple[int, int, str], int] = {}
for r in range(6):
    for c in range(7):
        for p in ("human", "computer"):
            ZOBRIST_TABLE[(r, c, p)] = _rng.getrandbits(64)

ZOBRIST_TURN = _rng.getrandbits(64)


def compute_zobrist_hash(board: tuple[tuple[str | None, ...], ...], current_player: str) -> int:
    """Compute 64-bit Zobrist hash for Connect 4 board."""
    h = 0
    for r in range(6):
        for c in range(7):
            piece = board[r][c]
            if piece is not None:
                h ^= ZOBRIST_TABLE[(r, c, normalize_player(piece))]
    if normalize_player(current_player) == "computer":
        h ^= ZOBRIST_TURN
    return h


class TranspositionTable:
    """Transposition Table for caching previously computed game subtree evaluations."""

    def __init__(self, max_size: int = 500_000):
        self.table: dict[int, tuple[int, int, float, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.lookups = 0

    def lookup(self, key: int, depth: int, alpha: float, beta: float) -> tuple[bool, float | None, Any]:
        """Look up key in TT. Returns (hit, score, best_move)."""
        self.lookups += 1
        entry = self.table.get(key)
        if entry is None:
            return False, None, None

        entry_depth, flag, value, best_m = entry
        if entry_depth >= depth:
            if flag == 0:  # EXACT
                self.hits += 1
                return True, value, best_m
            elif flag == 1 and value <= alpha:  # UPPERBOUND
                self.hits += 1
                return True, value, best_m
            elif flag == 2 and value >= beta:  # LOWERBOUND
                self.hits += 1
                return True, value, best_m

        return False, None, best_m

    def store(self, key: int, depth: int, flag: int, value: float, best_move: Any):
        if len(self.table) >= self.max_size:
            self.table.clear()
        self.table[key] = (depth, flag, value, best_move)


def alphabeta_with_tt(
    game: Game,
    state: Any,
    depth: int,
    tt: TranspositionTable,
    perspective: str = "computer",
) -> tuple[Any, float, int]:
    """Alpha-beta search accelerated with a Zobrist Transposition Table."""
    nodes = 0
    target_perspective = normalize_player(perspective)

    def _search(s: Any, d: int, alpha: float, beta: float) -> tuple[Any, float]:
        nonlocal nodes
        nodes += 1

        if game.is_terminal(s):
            return None, float(game.utility(s, target_perspective))
        if d == 0:
            return None, float(game.evaluate(s, target_perspective))

        mover = normalize_player(game.current_player(s))
        is_max = (mover == target_perspective)

        # TT Lookup
        state_key = compute_zobrist_hash(s.board, mover)
        hit, tt_val, tt_move = tt.lookup(state_key, d, alpha, beta)
        if hit and tt_val is not None:
            return tt_move, tt_val

        moves = game.legal_moves(s)
        if not moves:
            next_state = game.apply(s, None)
            _, score = _search(next_state, d - 1, alpha, beta)
            return None, score

        # Order moves with TT move first if available
        if tt_move in moves:
            moves = [tt_move] + [m for m in moves if m != tt_move]
        else:
            moves = game.order_moves(s, moves)

        orig_alpha = alpha
        best_cand = moves[0]

        if is_max:
            best_score = -float("inf")
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _search(next_state, d - 1, alpha, beta)
                if score > best_score:
                    best_score = score
                    best_cand = m
                if best_score >= beta:
                    break
                if best_score > alpha:
                    alpha = best_score

            flag = 0  # EXACT
            if best_score <= orig_alpha:
                flag = 1  # UPPERBOUND
            elif best_score >= beta:
                flag = 2  # LOWERBOUND
            tt.store(state_key, d, flag, best_score, best_cand)
            return best_cand, best_score
        else:
            best_score = float("inf")
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _search(next_state, d - 1, alpha, beta)
                if score < best_score:
                    best_score = score
                    best_cand = m
                if best_score <= alpha:
                    break
                if best_score < beta:
                    beta = best_score

            flag = 0
            if best_score <= alpha:
                flag = 1
            elif best_score >= beta:
                flag = 2
            tt.store(state_key, d, flag, best_score, best_cand)
            return best_cand, best_score

    best_m, best_sc = _search(state, depth, -float("inf"), float("inf"))
    return best_m, best_sc, nodes
