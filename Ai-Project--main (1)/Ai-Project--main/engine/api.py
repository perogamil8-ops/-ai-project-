"""Stateless API entry points for the backend and UI."""
from __future__ import annotations

import random
from typing import Any

from engine.base import Game, normalize_player
from engine.games.xo import XOGame
from engine.games.connect4 import Connect4Game
from engine.games.seega import SeegaGame
from engine.search import minimax, alphabeta, best_move, score_all_moves
from engine import analysis

GAMES: dict[str, type[Game]] = {
    "xo": XOGame,
    "connect4": Connect4Game,
    "seega": SeegaGame,
}


def get_game_instance(game: str | Game) -> tuple[str, Game]:
    """Resolve a game string or instance to (canonical_name, GameInstance)."""
    if isinstance(game, Game):
        name = game.__class__.__name__.lower()
        for suffix in ("game", "engine"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name, game

    key = str(game).lower().replace(" ", "").replace("-", "").replace("_", "")
    if key in ("xo", "tictactoe"):
        return "xo", XOGame()
    elif key in ("connect4", "c4"):
        return "connect4", Connect4Game()
    elif key == "seega":
        return "seega", SeegaGame()
    else:
        raise ValueError(f"Unknown game '{game}'. Expected one of {list(GAMES.keys())}")


def _normalize_move(gname: str, move: Any) -> Any:
    """Normalize JSON move payloads to native game move tuples."""
    if move is None:
        return None
    if gname == "xo":
        if isinstance(move, (list, tuple)) and len(move) == 2:
            return (int(move[0]), int(move[1]))
        raise ValueError(f"Invalid XO move format {move}. Expected [row, col]")
    elif gname == "connect4":
        return int(move)
    elif gname == "seega":
        if isinstance(move, (list, tuple)):
            # Placement move [r, c]
            if len(move) == 2 and isinstance(move[0], (int, float)) and isinstance(move[1], (int, float)):
                return (int(move[0]), int(move[1]))
            # Movement move [[r1, c1], [r2, c2]]
            if len(move) == 2 and isinstance(move[0], (list, tuple)) and isinstance(move[1], (list, tuple)):
                return ((int(move[0][0]), int(move[0][1])), (int(move[1][0]), int(move[1][1])))
        raise ValueError(f"Invalid Seega move format {move}")
    return move


def new_game(
    game: str | Game,
    first_player: str = "human",
    mode: str = "human_vs_computer",
) -> dict[str, Any]:
    """Start a new game session.

    mode: 'human_vs_computer' (PvE) or 'friends' (hot-seat PvP) or 'ai_vs_ai'
    """
    gname, game_inst = get_game_instance(game)
    norm_first = normalize_player(first_player)
    if norm_first not in ("human", "computer"):
        raise ValueError(f"Invalid first_player '{first_player}'. Must be 'human' or 'computer'.")

    state = game_inst.initial_state(norm_first)
    legal = game_inst.legal_moves(state)

    is_friends = mode in ("friends", "pvp", "hotseat")
    labels = {
        "human": "Player 1" if is_friends else "Human",
        "computer": "Player 2" if is_friends else "Computer",
    }

    return {
        "game": gname,
        "mode": "friends" if is_friends else "human_vs_computer",
        "state": game_inst.to_json(state),
        "status": "ongoing",
        "current_player": game_inst.current_player(state),
        "player_labels": labels,
        "legal_moves": legal,
        "winner": None,
        "winning_cells": [],
        "message": f"Game started. {labels[norm_first]} plays first.",
    }


def get_legal_moves(game: str | Game, state: dict[str, Any] | Any) -> list[Any]:
    """Get legal moves for the given state."""
    _, game_inst = get_game_instance(game)
    if isinstance(state, dict):
        state_obj = game_inst.from_json(state)
    else:
        state_obj = state
    return game_inst.legal_moves(state_obj)


def apply_human_move(
    game: str | Game,
    state: dict[str, Any] | Any,
    move: Any,
    mode: str = "human_vs_computer",
    player: str | None = None,
) -> dict[str, Any]:
    """Apply a move by the human player (or either player in friends mode)."""
    gname, game_inst = get_game_instance(game)
    if isinstance(state, dict):
        state_obj = game_inst.from_json(state)
    else:
        state_obj = state

    if game_inst.is_terminal(state_obj):
        raise ValueError("Game is already finished.")

    current = game_inst.current_player(state_obj)
    is_friends = mode in ("friends", "pvp", "hotseat")

    if not is_friends and current != "human":
        raise ValueError(f"Cannot apply human move when current player is '{current}'.")

    if player is not None:
        norm_p = normalize_player(player)
        if norm_p != normalize_player(current):
            raise ValueError(f"It is not {player}'s turn. Current turn: {current}")

    norm_move = _normalize_move(gname, move)
    legal = game_inst.legal_moves(state_obj)

    # Validate legality
    if norm_move is not None and norm_move not in legal:
        raise ValueError(f"Illegal move {move}. Legal moves: {legal}")
    if norm_move is None and len(legal) > 0:
        raise ValueError("Cannot pass when legal moves are available.")

    new_state = game_inst.apply(state_obj, norm_move)
    is_term = game_inst.is_terminal(new_state)
    w = game_inst.winner(new_state)
    cells = game_inst.winning_cells(new_state)

    msg = ""
    if gname == "seega" and hasattr(game_inst, "last_capture_message"):
        msg = game_inst.last_capture_message(new_state)

    labels = {
        "human": "Player 1" if is_friends else "Human",
        "computer": "Player 2" if is_friends else "Computer",
    }

    if is_term:
        status = "terminal"
        if w in ("human", "computer"):
            end_msg = f"{labels[w]} wins!"
        else:
            end_msg = "Game ended in a draw!"
        msg = f"{msg} {end_msg}".strip()
    else:
        status = "ongoing"
        if not msg:
            next_p = game_inst.current_player(new_state)
            msg = f"{labels.get(next_p, next_p.capitalize())}'s turn."

    return {
        "state": game_inst.to_json(new_state),
        "status": status,
        "winner": w,
        "winning_cells": cells,
        "message": msg,
        "current_player": game_inst.current_player(new_state),
        "legal_moves": game_inst.legal_moves(new_state),
    }


def ai_move(
    game: str | Game,
    state: dict[str, Any] | Any,
    algorithm: str = "alphabeta",
    level: str = "hard",
    seed: int | None = None,
) -> dict[str, Any]:
    """Calculate and apply the AI's move."""
    gname, game_inst = get_game_instance(game)
    if isinstance(state, dict):
        state_obj = game_inst.from_json(state)
    else:
        state_obj = state

    if game_inst.is_terminal(state_obj):
        raise ValueError("Game is already finished.")

    current = game_inst.current_player(state_obj)
    if current != "computer":
        raise ValueError(f"Cannot request AI move when current player is '{current}'.")

    algo_clean = algorithm.lower().replace("-", "").replace("_", "")
    if algo_clean not in ("minimax", "alphabeta"):
        raise ValueError(f"Invalid algorithm '{algorithm}'. Must be 'minimax' or 'alphabeta'.")

    level_clean = level.lower()
    if level_clean not in ("easy", "medium", "hard", "expert"):
        raise ValueError(f"Invalid level '{level}'. Must be 'easy', 'medium', or 'hard'.")

    rng = random.Random(seed)
    legal = game_inst.legal_moves(state_obj)

    # 1. Handle PASS when blocked
    if not legal:
        new_state = game_inst.apply(state_obj, None)
        is_term = game_inst.is_terminal(new_state)
        w = game_inst.winner(new_state)
        return {
            "move": None,
            "nodes": 1,
            "time_ms": 0.0,
            "state": game_inst.to_json(new_state),
            "status": "terminal" if is_term else "ongoing",
            "winner": w,
            "winning_cells": [],
            "message": "Computer has no legal moves and passes.",
            "current_player": game_inst.current_player(new_state),
            "legal_moves": game_inst.legal_moves(new_state),
        }

    # 2. Seega Placement Phase: random selection
    if gname == "seega" and hasattr(state_obj, "phase") and state_obj.phase == "placement":
        chosen_move = rng.choice(legal)
        nodes = 1
        time_ms = 0.0
    # 3. XO Easy Level: random selection
    elif gname == "xo" and level_clean == "easy":
        chosen_move = rng.choice(legal)
        nodes = 1
        time_ms = 0.0
    # 4. Standard Search
    else:
        depth = game_inst.depth_for(level_clean)
        search_res = best_move(game_inst, state_obj, algorithm=algo_clean, depth=depth, perspective="computer", use_ordering=True)
        chosen_move = search_res.move
        nodes = search_res.nodes
        time_ms = search_res.time_ms

    new_state = game_inst.apply(state_obj, chosen_move)
    is_term = game_inst.is_terminal(new_state)
    w = game_inst.winner(new_state)
    cells = game_inst.winning_cells(new_state)

    msg = ""
    if gname == "seega" and hasattr(game_inst, "last_capture_message"):
        msg = game_inst.last_capture_message(new_state)

    if is_term:
        status = "terminal"
        if w in ("human", "computer"):
            end_msg = f"{w.capitalize()} wins!"
        else:
            end_msg = "Game ended in a draw!"
        msg = f"{msg} {end_msg}".strip()
    else:
        status = "ongoing"
        if not msg:
            msg = f"{new_state.player.capitalize()}'s turn."

    return {
        "move": chosen_move,
        "nodes": nodes,
        "time_ms": time_ms,
        "state": game_inst.to_json(new_state),
        "status": status,
        "winner": w,
        "winning_cells": cells,
        "message": msg,
        "current_player": game_inst.current_player(new_state),
        "legal_moves": game_inst.legal_moves(new_state),
    }


def hint(
    game: str | Game,
    state: dict[str, Any] | Any,
    algorithm: str = "alphabeta",
    depth: int | None = None,
) -> dict[str, Any]:
    """Calculate the best move hint and candidate scores for the player to move."""
    gname, game_inst = get_game_instance(game)
    if isinstance(state, dict):
        state_obj = game_inst.from_json(state)
    else:
        state_obj = state

    if game_inst.is_terminal(state_obj):
        raise ValueError("Game is already finished.")

    # Seega placement phase check
    if gname == "seega" and hasattr(state_obj, "phase") and state_obj.phase == "placement":
        return {
            "best_move": None,
            "scores_per_move": {},
            "scores_list": [],
            "nodes": 0,
            "time_ms": 0.0,
            "message": "Hints are available in the movement phase.",
        }

    mover = game_inst.current_player(state_obj)
    if depth is None:
        if gname == "xo":
            depth = 9
        elif gname == "connect4":
            depth = 4
        elif gname == "seega":
            depth = 3
        else:
            depth = 2

    # Compute best move with ordering
    bm_res = best_move(game_inst, state_obj, algorithm=algorithm, depth=depth, perspective=mover, use_ordering=True)

    # Score all moves with modest depth for UI heatmap
    eval_depth = min(depth, 3 if gname == "connect4" else depth)
    all_scores = score_all_moves(game_inst, state_obj, depth=eval_depth, perspective=mover)

    scores_list = [{"move": m, "score": round(s, 1)} for m, s in all_scores.items()]
    scores_dict = {str(m): round(s, 1) for m, s in all_scores.items()}

    return {
        "best_move": bm_res.move,
        "scores_per_move": scores_dict,
        "scores_list": scores_list,
        "nodes": bm_res.nodes,
        "time_ms": bm_res.time_ms,
        "message": f"Suggested move: {bm_res.move}",
    }


def analyze_game_match(
    game: str | Game,
    first_player: str,
    moves: list[Any],
    mode: str = "human_vs_computer",
    depth_override: int | None = None,
) -> dict[str, Any]:
    """Perform post-game analysis on a completed game."""
    _, game_inst = get_game_instance(game)
    normalized_moves = []
    gname, _ = get_game_instance(game)
    for m in moves:
        normalized_moves.append(_normalize_move(gname, m))

    return analysis.analyze_game(
        game=game_inst,
        first_player=first_player,
        moves=normalized_moves,
        mode=mode,
        depth_override=depth_override,
    )


def eval_position(game: str | Game, state: dict[str, Any] | Any) -> dict[str, Any]:
    """Calculate live evaluation from Player 1's perspective for the live eval bar."""
    gname, game_inst = get_game_instance(game)
    if isinstance(state, dict):
        state_obj = game_inst.from_json(state)
    else:
        state_obj = state

    if game_inst.is_terminal(state_obj):
        raw_score = float(game_inst.utility(state_obj, "human"))
    else:
        raw_score = float(game_inst.evaluate(state_obj, "human"))

    prob = analysis.win_probability(raw_score, gname)
    eval_norm = round((2.0 * prob) - 1.0, 3)  # Range [-1.0, +1.0]

    return {
        "score": round(raw_score, 1),
        "eval_normalized": eval_norm,
        "p1_win_prob": round(prob, 3),
        "mover": game_inst.current_player(state_obj),
    }
