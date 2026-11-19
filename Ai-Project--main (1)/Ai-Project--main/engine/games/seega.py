"""Seega board game implementation conforming to Game base class."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.base import Game, normalize_player, opponent
from engine.levels import get_depth

BOARD_SIZE = 5
CENTER = (2, 2)
ORTHOGONAL_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def find_captures(
    board: tuple[tuple[str | None, ...], ...],
    player: str,
    move_to: tuple[int, int]
) -> list[tuple[int, int]]:
    """Determine captured opponent pieces after moving a friendly piece to move_to.

    Capture Rule:
    For each of the 4 orthogonal directions:
      If adjacent square holds an opponent piece AND next square in that same direction
      holds a friendly piece, the opponent piece is captured.
    Exceptions:
      - A piece on the center square (2, 2) is immune and CANNOT be captured.
      - Moving into a position between two opponent pieces is safe (no self-capture).
    """
    opponent = "computer" if player == "human" else "human"
    r, c = move_to
    captured = []

    for dr, dc in ORTHOGONAL_DIRS:
        adj_r, adj_c = r + dr, c + dc
        bey_r, bey_c = r + 2 * dr, c + 2 * dc

        # Check bounds
        if 0 <= adj_r < BOARD_SIZE and 0 <= adj_c < BOARD_SIZE:
            if 0 <= bey_r < BOARD_SIZE and 0 <= bey_c < BOARD_SIZE:
                # Center square is immune to being captured
                if (adj_r, adj_c) == CENTER:
                    continue

                if board[adj_r][adj_c] == opponent and board[bey_r][bey_c] == player:
                    captured.append((adj_r, adj_c))

    return captured


@dataclass(frozen=True)
class SeegaState:
    """Immutable state for Seega game.

    Tracks board, phase, placement counts, player, turn counts, and capture metrics.
    """
    board: tuple[tuple[str | None, ...], ...]
    phase: str  # "placement" or "movement"
    player: str  # "human" or "computer"
    first_placer: str  # player who placed first
    placed_this_turn: int  # 0 or 1 during placement
    human_placed: int  # total pieces placed by human (max 12)
    computer_placed: int  # total pieces placed by computer (max 12)
    no_capture_counter: int  # consecutive moves without capture in movement phase
    human_pieces: int  # current piece count on board
    computer_pieces: int
    last_capture_count: int = 0
    last_captor: str | None = None


class SeegaGame(Game):
    """Seega board game (5x5).

    Human is black, Computer is white.
    Phase 1: Alternate placing 2 pieces at a time (excluding center).
    Phase 2: Movement to adjacent empty squares with orthogonal sandwich captures.
    """

    def initial_state(self, first_player: str = "human") -> SeegaState:
        norm_first = normalize_player(first_player)
        if norm_first not in ("human", "computer"):
            raise ValueError(f"Invalid first_player '{first_player}', must be 'human' or 'computer'")
        empty_board = tuple(tuple(None for _ in range(BOARD_SIZE)) for _ in range(BOARD_SIZE))
        return SeegaState(
            board=empty_board,
            phase="placement",
            player=norm_first,
            first_placer=norm_first,
            placed_this_turn=0,
            human_placed=0,
            computer_placed=0,
            no_capture_counter=0,
            human_pieces=0,
            computer_pieces=0,
            last_capture_count=0,
            last_captor=None,
        )

    def current_player(self, state: SeegaState) -> str:
        return state.player

    def legal_moves(self, state: SeegaState) -> list[Any]:
        if self.is_terminal(state):
            return []

        if state.phase == "placement":
            moves = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if (r, c) != CENTER and state.board[r][c] is None:
                        moves.append((r, c))
            return moves

        # Movement phase
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if state.board[r][c] == state.player:
                    for dr, dc in ORTHOGONAL_DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if state.board[nr][nc] is None:
                                moves.append(((r, c), (nr, nc)))
        return moves

    def apply(self, state: SeegaState, move: Any) -> SeegaState:
        # Handle PASS in movement phase
        if move is None:
            if state.phase == "placement":
                raise ValueError("Cannot pass during placement phase")
            next_player = "computer" if state.player == "human" else "human"
            new_counter = state.no_capture_counter + 1
            return SeegaState(
                board=state.board,
                phase=state.phase,
                player=next_player,
                first_placer=state.first_placer,
                placed_this_turn=0,
                human_placed=state.human_placed,
                computer_placed=state.computer_placed,
                no_capture_counter=new_counter,
                human_pieces=state.human_pieces,
                computer_pieces=state.computer_pieces,
                last_capture_count=0,
                last_captor=None,
            )

        new_board = [list(row) for row in state.board]

        if state.phase == "placement":
            r, c = move[0], move[1]
            if (r, c) == CENTER:
                raise ValueError("Center square (2, 2) cannot be placed on in Phase 1")
            if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                raise ValueError(f"Placement {(r, c)} is out of bounds")
            if state.board[r][c] is not None:
                raise ValueError(f"Square {(r, c)} is already occupied")

            new_board[r][c] = state.player
            h_placed = state.human_placed + (1 if state.player == "human" else 0)
            c_placed = state.computer_placed + (1 if state.player == "computer" else 0)
            h_pieces = state.human_pieces + (1 if state.player == "human" else 0)
            c_pieces = state.computer_pieces + (1 if state.player == "computer" else 0)

            total_placed = h_placed + c_placed

            if total_placed == 24:
                # All 24 pieces placed -> Transition to movement phase
                # Rule: The player who placed SECOND moves first in Phase 2
                second_placer = "computer" if state.first_placer == "human" else "human"
                return SeegaState(
                    board=tuple(tuple(row) for row in new_board),
                    phase="movement",
                    player=second_placer,
                    first_placer=state.first_placer,
                    placed_this_turn=0,
                    human_placed=h_placed,
                    computer_placed=c_placed,
                    no_capture_counter=0,
                    human_pieces=h_pieces,
                    computer_pieces=c_pieces,
                    last_capture_count=0,
                    last_captor=None,
                )

            # Check if this player finished their 2 placements this turn
            new_placed_this_turn = state.placed_this_turn + 1
            if new_placed_this_turn == 2:
                next_player = "computer" if state.player == "human" else "human"
                new_placed_this_turn = 0
            else:
                next_player = state.player

            return SeegaState(
                board=tuple(tuple(row) for row in new_board),
                phase="placement",
                player=next_player,
                first_placer=state.first_placer,
                placed_this_turn=new_placed_this_turn,
                human_placed=h_placed,
                computer_placed=c_placed,
                no_capture_counter=0,
                human_pieces=h_pieces,
                computer_pieces=c_pieces,
                last_capture_count=0,
                last_captor=None,
            )

        # Movement Phase
        (r1, c1), (r2, c2) = move
        if not (0 <= r1 < BOARD_SIZE and 0 <= c1 < BOARD_SIZE and 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE):
            raise ValueError(f"Move {move} is out of bounds")
        if state.board[r1][c1] != state.player:
            raise ValueError(f"No friendly piece at {(r1, c1)} for player {state.player}")
        if state.board[r2][c2] is not None:
            raise ValueError(f"Destination {(r2, c2)} is already occupied")
        if abs(r2 - r1) + abs(c2 - c1) != 1:
            raise ValueError(f"Move from {(r1, c1)} to {(r2, c2)} is not orthogonal 1-step")

        # Execute step
        new_board[r1][c1] = None
        new_board[r2][c2] = state.player
        frozen_interim = tuple(tuple(row) for row in new_board)

        # Check captures
        captured_cells = find_captures(frozen_interim, state.player, (r2, c2))
        for cr, cc in captured_cells:
            new_board[cr][cc] = None

        h_pieces = sum(row.count("human") for row in new_board)
        c_pieces = sum(row.count("computer") for row in new_board)

        if captured_cells:
            new_counter = 0
        else:
            new_counter = state.no_capture_counter + 1

        next_player = "computer" if state.player == "human" else "human"
        return SeegaState(
            board=tuple(tuple(row) for row in new_board),
            phase="movement",
            player=next_player,
            first_placer=state.first_placer,
            placed_this_turn=0,
            human_placed=state.human_placed,
            computer_placed=state.computer_placed,
            no_capture_counter=new_counter,
            human_pieces=h_pieces,
            computer_pieces=c_pieces,
            last_capture_count=len(captured_cells),
            last_captor=state.player if captured_cells else None,
        )

    def winner(self, state: SeegaState) -> str | None:
        if state.phase == "placement":
            return None

        # Elimination win
        if state.human_pieces == 0 and state.computer_pieces > 0:
            return "computer"
        if state.computer_pieces == 0 and state.human_pieces > 0:
            return "human"
        if state.human_pieces == 0 and state.computer_pieces == 0:
            return "draw"

        # 40-move rule with no captures
        if state.no_capture_counter >= 40:
            if state.human_pieces > state.computer_pieces:
                return "human"
            elif state.computer_pieces > state.human_pieces:
                return "computer"
            else:
                return "draw"

        return None

    def winning_cells(self, state: SeegaState) -> list[tuple[int, int]]:
        return []

    def is_terminal(self, state: SeegaState) -> bool:
        return self.winner(state) is not None

    def utility(self, state: SeegaState, player: str) -> float:
        w = self.winner(state)
        p = normalize_player(player)
        opp = opponent(p)
        if w == p:
            return 10000.0
        elif w == opp:
            return -10000.0
        elif w == "draw":
            return 0.0
        return 0.0

    def evaluate(self, state: SeegaState, player: str) -> float:
        r"""Heuristic evaluation for Seega (movement phase).

        Evaluation Formula:
        Score = 10 * (own_pieces - opp_pieces)
              + 1  * (own_mobility - opp_mobility)
              + 3  * center_control_bonus
              + 0.5 * (own_protected_pieces - opp_protected_pieces)

        Where:
        - Piece difference (weight 10): Primary objective of eliminating enemy units.
        - Mobility difference (weight 1): Difference in number of immediate legal moves.
        - Center control bonus (+3): Square (2, 2) grants capture immunity and board dominance.
        - Protection bonus (+0.5 per protected piece): A piece is considered protected if:
            1. It sits on the immune center square (2, 2), OR
            2. It cannot be flanked along its horizontal axis (blocked by edge or friendly piece), OR
            3. It cannot be flanked along its vertical axis.
        """
        w = self.winner(state)
        if w is not None:
            return self.utility(state, player)

        p = normalize_player(player)
        opp = opponent(p)

        # 1. Piece difference (weight 10)
        own_pieces = state.computer_pieces if p == "computer" else state.human_pieces
        opp_pieces = state.human_pieces if p == "computer" else state.computer_pieces
        piece_diff = own_pieces - opp_pieces

        # 2. Mobility difference (weight 1)
        # Compute legal moves for both sides
        own_moves = 0
        opp_moves = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = state.board[r][c]
                if piece is None:
                    continue
                moves_count = 0
                for dr, dc in ORTHOGONAL_DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if state.board[nr][nc] is None:
                            moves_count += 1
                if piece == p:
                    own_moves += moves_count
                elif piece == opp:
                    opp_moves += moves_count

        mobility_diff = own_moves - opp_moves

        # 3. Center control (+3)
        center_owner = state.board[CENTER[0]][CENTER[1]]
        center_bonus = 0.0
        if center_owner == p:
            center_bonus = 3.0
        elif center_owner == opp:
            center_bonus = -3.0

        # 4. Protection bonus (+0.5 per safe piece)
        def piece_protection(r: int, c: int, owner: str) -> float:
            if (r, c) == CENTER:
                return 1.0  # Center is completely immune
            prot = 0.0
            # Horizontal flanking safety: left or right is edge or friendly
            left_safe = (c == 0 or state.board[r][c - 1] == owner)
            right_safe = (c == BOARD_SIZE - 1 or state.board[r][c + 1] == owner)
            if left_safe or right_safe:
                prot += 0.5

            # Vertical flanking safety: top or bottom is edge or friendly
            top_safe = (r == 0 or state.board[r - 1][c] == owner)
            bottom_safe = (r == BOARD_SIZE - 1 or state.board[r + 1][c] == owner)
            if top_safe or bottom_safe:
                prot += 0.5
            return prot

        own_prot = 0.0
        opp_prot = 0.0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = state.board[r][c]
                if piece == p:
                    own_prot += piece_protection(r, c, p)
                elif piece == opp:
                    opp_prot += piece_protection(r, c, opp)

        protection_diff = own_prot - opp_prot

        total_score = (10.0 * piece_diff) + (1.0 * mobility_diff) + center_bonus + (0.5 * protection_diff)
        return total_score

    def order_moves(self, state: SeegaState, moves: list[Any]) -> list[Any]:
        """Order moves best-first: moves towards center and moves producing captures."""
        if state.phase == "placement":
            return moves

        def move_score(m: Any) -> float:
            (r1, c1), (r2, c2) = m
            # Priority to occupying center
            score = 0.0
            if (r2, c2) == CENTER:
                score += 15.0
            # Center proximity
            dist_to_center = abs(r2 - CENTER[0]) + abs(c2 - CENTER[1])
            score += (4 - dist_to_center)

            # Check potential captures
            test_board = [list(row) for row in state.board]
            test_board[r1][c1] = None
            test_board[r2][c2] = state.player
            captures = find_captures(tuple(tuple(row) for row in test_board), state.player, (r2, c2))
            score += len(captures) * 20.0
            return score

        return sorted(moves, key=move_score, reverse=True)

    def depth_for(self, level: str) -> int:
        return get_depth("seega", level)

    def last_capture_message(self, state: SeegaState) -> str:
        """Helper for UI: returns readable capture description."""
        if state.last_capture_count > 0:
            actor = "Computer" if state.last_captor == "computer" else "Human"
            if state.last_capture_count == 1:
                return f"{actor} captured 1 piece!"
            return f"{actor} captured {state.last_capture_count} pieces!"
        return ""

    def pieces_count(self, state: SeegaState) -> dict[str, int]:
        """Return pieces count for both players."""
        return {
            "human": state.human_pieces,
            "computer": state.computer_pieces,
        }

    def to_json(self, state: SeegaState) -> dict[str, Any]:
        return {
            "board": [list(row) for row in state.board],
            "phase": state.phase,
            "player": state.player,
            "first_placer": state.first_placer,
            "placed_this_turn": state.placed_this_turn,
            "human_placed": state.human_placed,
            "computer_placed": state.computer_placed,
            "no_capture_counter": state.no_capture_counter,
            "human_pieces": state.human_pieces,
            "computer_pieces": state.computer_pieces,
            "last_capture_count": state.last_capture_count,
            "last_captor": state.last_captor,
        }

    def from_json(self, data: dict[str, Any]) -> SeegaState:
        board = tuple(tuple(row) for row in data["board"])
        return SeegaState(
            board=board,
            phase=data["phase"],
            player=data["player"],
            first_placer=data["first_placer"],
            placed_this_turn=data["placed_this_turn"],
            human_placed=data["human_placed"],
            computer_placed=data["computer_placed"],
            no_capture_counter=data["no_capture_counter"],
            human_pieces=data["human_pieces"],
            computer_pieces=data["computer_pieces"],
            last_capture_count=data.get("last_capture_count", 0),
            last_captor=data.get("last_captor", None),
        )
