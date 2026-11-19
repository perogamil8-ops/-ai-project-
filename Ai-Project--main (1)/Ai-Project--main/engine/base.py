"""Abstract base class for all board games."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Canonical player identifiers
P1 = "human"      # Player 1 default slot (human in PvE, Player 1 in PvP)
P2 = "computer"   # Player 2 default slot (computer in PvE, Player 2 in PvP)

PLAYER_1_ALIASES = {"human", "p1", "player1", "player 1", "0", 0, "x", "black", "red"}
PLAYER_2_ALIASES = {"computer", "p2", "player2", "player 2", "1", 1, "o", "white", "yellow"}


def normalize_player(player: Any) -> str:
    """Normalize any player representation (p1/p2, 0/1, human/computer) to canonical 'human' or 'computer'."""
    if isinstance(player, str):
        low = player.strip().lower()
        if low in PLAYER_1_ALIASES:
            return P1
        if low in PLAYER_2_ALIASES:
            return P2
        return low
    if player in PLAYER_1_ALIASES:
        return P1
    if player in PLAYER_2_ALIASES:
        return P2
    return str(player).lower()


def opponent(player: Any) -> str:
    """Return the opponent of the given player."""
    norm = normalize_player(player)
    return P2 if norm == P1 else P1


class Game(ABC):
    """Abstract game interface.

    States must be immutable (e.g. frozen dataclass or tuples) and JSON-serializable.
    Players map to canonical P1 ('human') and P2 ('computer') with aliases supported.
    """

    @abstractmethod
    def initial_state(self, first_player: str = "human") -> Any:
        """Return the initial game state with the given starting player."""
        pass

    @abstractmethod
    def current_player(self, state: Any) -> str:
        """Return the current player ('human' or 'computer')."""
        pass

    @abstractmethod
    def legal_moves(self, state: Any) -> list[Any]:
        """Return a list of legal moves available in the given state."""
        pass

    @abstractmethod
    def apply(self, state: Any, move: Any) -> Any:
        """Apply a move to the state and return a brand new state without mutating the old one."""
        pass

    @abstractmethod
    def is_terminal(self, state: Any) -> bool:
        """Return True if the game has ended, False otherwise."""
        pass

    @abstractmethod
    def winner(self, state: Any) -> str | None:
        """Return 'human', 'computer', 'draw', or None if the game is still ongoing."""
        pass

    @abstractmethod
    def winning_cells(self, state: Any) -> list[Any]:
        """Return the list of cell coordinates forming the winning combination, or [] if none."""
        pass

    @abstractmethod
    def utility(self, state: Any, player: str) -> float:
        """Return terminal utility for the given player (+win, -loss, 0 draw)."""
        pass

    @abstractmethod
    def evaluate(self, state: Any, player: str) -> float:
        """Heuristic evaluation of a non-terminal state from the perspective of player."""
        pass

    @abstractmethod
    def order_moves(self, state: Any, moves: list[Any]) -> list[Any]:
        """Return moves ordered best-first for alpha-beta pruning."""
        pass

    @abstractmethod
    def depth_for(self, level: str) -> int:
        """Map difficulty level ('easy', 'medium', 'hard') to search depth."""
        pass

    @abstractmethod
    def to_json(self, state: Any) -> dict[str, Any]:
        """Serialize state to a JSON-compatible dictionary."""
        pass

    @abstractmethod
    def from_json(self, data: dict[str, Any]) -> Any:
        """Deserialize a JSON dictionary back into an immutable state."""
        pass
