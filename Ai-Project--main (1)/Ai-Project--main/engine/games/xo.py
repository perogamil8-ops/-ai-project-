"""Tic-Tac-Toe (XO) implementation conforming to Game base class."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.base import Game, normalize_player, opponent
from engine.levels import get_depth

WINNING_LINES = [
    # Rows
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    # Columns
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    # Diagonals
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
]

MOVE_PRIORITY = {
    (1, 1): 3,  # Center
    (0, 0): 2,  # Corners
    (0, 2): 2,
    (2, 0): 2,
    (2, 2): 2,
    (0, 1): 1,  # Edges
    (1, 0): 1,
    (1, 2): 1,
    (2, 1): 1,
}


@dataclass(frozen=True)
class XOState:
    """Immutable state for Tic-Tac-Toe."""
    board: tuple[tuple[str | None, ...], ...]
    player: str  # "human" or "computer"


class XOGame(Game):
    """3x3 Tic-Tac-Toe game engine."""

    def initial_state(self, first_player: str = "human") -> XOState:
        norm_first = normalize_player(first_player)
        if norm_first not in ("human", "computer"):
            raise ValueError(f"Invalid first_player '{first_player}', must be 'human' or 'computer'")
        empty_board = tuple(tuple(None for _ in range(3)) for _ in range(3))
        return XOState(board=empty_board, player=norm_first)

    def current_player(self, state: XOState) -> str:
        return state.player

    def legal_moves(self, state: XOState) -> list[tuple[int, int]]:
        if self.is_terminal(state):
            return []
        moves = []
        for r in range(3):
            for c in range(3):
                if state.board[r][c] is None:
                    moves.append((r, c))
        return moves

    def apply(self, state: XOState, move: tuple[int, int] | list[int] | None) -> XOState:
        if move is None:
            # Handle pass if applicable
            next_player = "computer" if state.player == "human" else "human"
            return XOState(board=state.board, player=next_player)

        r, c = move[0], move[1]
        if not (0 <= r < 3 and 0 <= c < 3):
            raise ValueError(f"Move {(r, c)} is out of bounds for 3x3 board")
        if state.board[r][c] is not None:
            raise ValueError(f"Cell {(r, c)} is already occupied")

        new_board = [list(row) for row in state.board]
        new_board[r][c] = state.player
        frozen_board = tuple(tuple(row) for row in new_board)
        next_player = "computer" if state.player == "human" else "human"
        return XOState(board=frozen_board, player=next_player)

    def winner(self, state: XOState) -> str | None:
        for line in WINNING_LINES:
            p0 = state.board[line[0][0]][line[0][1]]
            p1 = state.board[line[1][0]][line[1][1]]
            p2 = state.board[line[2][0]][line[2][1]]
            if p0 is not None and p0 == p1 == p2:
                return p0

        # Check for draw
        is_full = all(state.board[r][c] is not None for r in range(3) for c in range(3))
        if is_full:
            return "draw"

        return None

    def winning_cells(self, state: XOState) -> list[tuple[int, int]]:
        for line in WINNING_LINES:
            p0 = state.board[line[0][0]][line[0][1]]
            p1 = state.board[line[1][0]][line[1][1]]
            p2 = state.board[line[2][0]][line[2][1]]
            if p0 is not None and p0 == p1 == p2:
                return list(line)
        return []

    def is_terminal(self, state: XOState) -> bool:
        return self.winner(state) is not None

    def utility(self, state: XOState, player: str) -> float:
        w = self.winner(state)
        p = normalize_player(player)
        opp = opponent(p)
        if w == p:
            return 1000.0
        elif w == opp:
            return -1000.0
        elif w == "draw":
            return 0.0
        return 0.0

    def evaluate(self, state: XOState, player: str) -> float:
        """Heuristic evaluation of state for player.

        Counts two-in-a-row (+10/-10) and one-in-a-row (+1/-1) open lines, plus center bonus.
        """
        w = self.winner(state)
        if w is not None:
            return self.utility(state, player)

        p = normalize_player(player)
        opp = opponent(p)
        score = 0.0

        for line in WINNING_LINES:
            cells = [state.board[r][c] for r, c in line]
            p_count = cells.count(p)
            o_count = cells.count(opp)

            if p_count > 0 and o_count > 0:
                continue  # Blocked line
            if p_count == 2 and o_count == 0:
                score += 10.0
            elif p_count == 1 and o_count == 0:
                score += 1.0
            elif o_count == 2 and p_count == 0:
                score -= 10.0
            elif o_count == 1 and p_count == 0:
                score -= 1.0

        # Center control
        center = state.board[1][1]
        if center == p:
            score += 3.0
        elif center == opp:
            score -= 3.0

        return score

    def order_moves(self, state: XOState, moves: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Order moves best-first: center, corners, edges."""
        return sorted(moves, key=lambda m: MOVE_PRIORITY.get((m[0], m[1]), 0), reverse=True)

    def depth_for(self, level: str) -> int:
        return get_depth("xo", level)

    def to_json(self, state: XOState) -> dict[str, Any]:
        return {
            "board": [list(row) for row in state.board],
            "player": state.player,
        }

    def from_json(self, data: dict[str, Any]) -> XOState:
        board = tuple(tuple(row) for row in data["board"])
        return XOState(board=board, player=data["player"])
