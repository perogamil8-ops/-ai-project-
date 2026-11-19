"""Difficulty levels and search depths for all games."""
from __future__ import annotations

# Depth mappings per game
LEVEL_DEPTHS = {
    "xo": {
        "easy": 0,       # XO easy plays random moves; depth 0 if searched
        "medium": 2,
        "hard": 9,       # Full search on 3x3 board
        "expert": 9,     # Iterative deepening
    },
    "connect4": {
        "easy": 1,
        "medium": 3,
        "hard": 5,
        "expert": 6,
    },
    "seega": {
        "easy": 1,
        "medium": 2,
        "hard": 4,       # Movement phase only
        "expert": 5,
    },
}


def get_depth(game_name: str, level: str) -> int:
    """Return the search depth for the specified game and level."""
    game_key = game_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    if game_key in ("tictactoe", "xo"):
        game_key = "xo"
    elif game_key in ("connect4", "c4"):
        game_key = "connect4"
    elif game_key == "seega":
        game_key = "seega"
    else:
        raise ValueError(f"Unknown game: {game_name}")

    level_key = level.lower()
    if level_key not in LEVEL_DEPTHS[game_key]:
        raise ValueError(f"Unknown level '{level}' for game '{game_name}'. Expected one of {list(LEVEL_DEPTHS[game_key].keys())}")

    return LEVEL_DEPTHS[game_key][level_key]
