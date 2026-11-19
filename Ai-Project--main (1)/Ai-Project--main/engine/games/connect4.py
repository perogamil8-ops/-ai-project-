"""Connect 4 implementation conforming to Game base class."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.base import Game, normalize_player, opponent
from engine.levels import get_depth

ROWS = 6
COLS = 7
MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]

# Precompute all 69 windows of 4 cells
WINDOWS: list[tuple[tuple[int, int], ...]] = []

# Horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))

# Vertical
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))

# Diagonal down-right (\)
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))

# Diagonal up-right (/)
for r in range(3, ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))


@dataclass(frozen=True)
class Connect4State:
    """Immutable state for Connect 4.

    Board is a 6x7 tuple of tuples (row 0 is top, row 5 is bottom).
    """
    board: tuple[tuple[str | None, ...], ...]
    player: str  # "human" or "computer"


class Connect4Game(Game):
    """Connect 4 (6 rows x 7 columns).

    Human is red, computer is yellow.
    Move is an integer column (0 to 6).
    """

    def initial_state(self, first_player: str = "human") -> Connect4State:
        norm_first = normalize_player(first_player)
        if norm_first not in ("human", "computer"):
            raise ValueError(f"Invalid first_player '{first_player}', must be 'human' or 'computer'")
        empty_board = tuple(tuple(None for _ in range(COLS)) for _ in range(ROWS))
        return Connect4State(board=empty_board, player=norm_first)

    def current_player(self, state: Connect4State) -> str:
        return state.player

    def legal_moves(self, state: Connect4State) -> list[int]:
        if self.is_terminal(state):
            return []
        moves = []
        for c in range(COLS):
            if state.board[0][c] is None:
                moves.append(c)
        return moves

    def apply(self, state: Connect4State, move: int | None) -> Connect4State:
        if move is None:
            next_player = "computer" if state.player == "human" else "human"
            return Connect4State(board=state.board, player=next_player)

        col = int(move)
        if not (0 <= col < COLS):
            raise ValueError(f"Column {col} is out of bounds (0..{COLS - 1})")
        if state.board[0][col] is not None:
            raise ValueError(f"Column {col} is full")

        # Fall to lowest empty cell (largest row index)
        target_row = -1
        for r in range(ROWS - 1, -1, -1):
            if state.board[r][col] is None:
                target_row = r
                break

        new_board = [list(row) for row in state.board]
        new_board[target_row][col] = state.player
        frozen_board = tuple(tuple(row) for row in new_board)
        next_player = "computer" if state.player == "human" else "human"
        return Connect4State(board=frozen_board, player=next_player)

    def winner(self, state: Connect4State) -> str | None:
        for window in WINDOWS:
            p0 = state.board[window[0][0]][window[0][1]]
            p1 = state.board[window[1][0]][window[1][1]]
            p2 = state.board[window[2][0]][window[2][1]]
            p3 = state.board[window[3][0]][window[3][1]]
            if p0 is not None and p0 == p1 == p2 == p3:
                return p0

        # Check full board (draw)
        is_full = all(state.board[0][c] is not None for c in range(COLS))
        if is_full:
            return "draw"

        return None

    def winning_cells(self, state: Connect4State) -> list[tuple[int, int]]:
        for window in WINDOWS:
            p0 = state.board[window[0][0]][window[0][1]]
            p1 = state.board[window[1][0]][window[1][1]]
            p2 = state.board[window[2][0]][window[2][1]]
            p3 = state.board[window[3][0]][window[3][1]]
            if p0 is not None and p0 == p1 == p2 == p3:
                return list(window)
        return []

    def is_terminal(self, state: Connect4State) -> bool:
        return self.winner(state) is not None

    def utility(self, state: Connect4State, player: str) -> float:
        w = self.winner(state)
        p = normalize_player(player)
        opp = opponent(p)
        if w == p:
            return 100000.0
        elif w == opp:
            return -100000.0
        elif w == "draw":
            return 0.0
        return 0.0

    def evaluate(self, state: Connect4State, player: str) -> float:
        r"""Heuristic evaluation for Connect 4.

        Evaluation Formula:
        For every 4-cell window on the 6x7 board:
          - 4 own pieces                  : +100,000 (win-level)
          - 4 opponent pieces             : -100,000 (loss-level)
          - 3 own pieces + 1 empty cell   : +50
          - 2 own pieces + 2 empty cells  : +5
          - 3 opponent pieces + 1 empty   : -80 (blocking priority)
          - 2 opponent pieces + 2 empty   : -5

        Center Column Bonus:
          - +3 for each own piece in column 3 (center)
          - -3 for each opponent piece in column 3 (center)

        Total Score = \sum_{windows} Score(window) + CenterBonus
        """
        w = self.winner(state)
        if w is not None:
            return self.utility(state, player)

        p = normalize_player(player)
        opp = opponent(p)
        score = 0.0

        for window in WINDOWS:
            cells = [state.board[r][c] for r, c in window]
            p_count = cells.count(p)
            o_count = cells.count(opp)
            empty_count = cells.count(None)

            if p_count == 4:
                return 100000.0
            elif o_count == 4:
                return -100000.0
            elif p_count == 3 and empty_count == 1:
                score += 50.0
            elif p_count == 2 and empty_count == 2:
                score += 5.0
            elif o_count == 3 and empty_count == 1:
                score -= 80.0
            elif o_count == 2 and empty_count == 2:
                score -= 5.0

        # Center column bonus (column index 3)
        center_col = 3
        for r in range(ROWS):
            cell = state.board[r][center_col]
            if cell == p:
                score += 3.0
            elif cell == opp:
                score -= 3.0

        return score

    def order_moves(self, state: Connect4State, moves: list[int]) -> list[int]:
        """Order moves according to center-out priority: 3, 2, 4, 1, 5, 0, 6."""
        priority_map = {col: idx for idx, col in enumerate(MOVE_ORDER)}
        return sorted(moves, key=lambda c: priority_map.get(c, 99))

    def depth_for(self, level: str) -> int:
        return get_depth("connect4", level)

    def to_json(self, state: Connect4State) -> dict[str, Any]:
        return {
            "board": [list(row) for row in state.board],
            "player": state.player,
        }

    def from_json(self, data: dict[str, Any]) -> Connect4State:
        board = tuple(tuple(row) for row in data["board"])
        return Connect4State(board=board, player=data["player"])
