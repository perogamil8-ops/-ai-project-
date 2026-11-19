"""Search Tree Visualizer for game-tree exploration and educational visualization."""
from __future__ import annotations

from typing import Any
from engine.base import Game, normalize_player


def build_search_tree(
    game: Game,
    state: Any,
    depth: int = 2,
    alpha: float = -float("inf"),
    beta: float = float("inf"),
    perspective: str | None = None,
    move_taken: Any = None,
) -> dict[str, Any]:
    """Generate an annotated Alpha-Beta search tree as a recursive dictionary.

    Each node records: move, player, depth, alpha, beta, value, pruned status, and children.
    """
    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))
    mover = normalize_player(game.current_player(state))
    is_max = (mover == target_perspective)

    node: dict[str, Any] = {
        "move": move_taken,
        "player": mover,
        "depth": depth,
        "alpha_in": round(alpha, 1) if abs(alpha) < 1e8 else ("-inf" if alpha < 0 else "+inf"),
        "beta_in": round(beta, 1) if abs(beta) < 1e8 else ("-inf" if beta < 0 else "+inf"),
        "value": None,
        "pruned": False,
        "children": [],
    }

    if game.is_terminal(state):
        node["value"] = float(game.utility(state, target_perspective))
        return node
    if depth == 0:
        node["value"] = float(game.evaluate(state, target_perspective))
        return node

    moves = game.legal_moves(state)
    if not moves:
        # Pass
        next_state = game.apply(state, None)
        child_node = build_search_tree(game, next_state, depth - 1, alpha, beta, target_perspective, move_taken=None)
        node["children"].append(child_node)
        node["value"] = child_node["value"]
        return node

    curr_alpha = alpha
    curr_beta = beta

    if is_max:
        best_val = -float("inf")
        cutoff_occurred = False
        for idx, m in enumerate(moves):
            if cutoff_occurred:
                # Sibling was pruned
                node["children"].append({
                    "move": m,
                    "player": mover,
                    "depth": depth - 1,
                    "alpha_in": round(curr_alpha, 1) if abs(curr_alpha) < 1e8 else str(curr_alpha),
                    "beta_in": round(curr_beta, 1) if abs(curr_beta) < 1e8 else str(curr_beta),
                    "value": None,
                    "pruned": True,
                    "children": [],
                })
                continue

            next_state = game.apply(state, m)
            child_node = build_search_tree(game, next_state, depth - 1, curr_alpha, curr_beta, target_perspective, move_taken=m)
            node["children"].append(child_node)

            val = child_node["value"]
            if val is not None and val > best_val:
                best_val = val
            if best_val >= curr_beta:
                cutoff_occurred = True
            if best_val > curr_alpha:
                curr_alpha = best_val

        node["value"] = best_val
    else:
        best_val = float("inf")
        cutoff_occurred = False
        for idx, m in enumerate(moves):
            if cutoff_occurred:
                node["children"].append({
                    "move": m,
                    "player": mover,
                    "depth": depth - 1,
                    "alpha_in": round(curr_alpha, 1) if abs(curr_alpha) < 1e8 else str(curr_alpha),
                    "beta_in": round(curr_beta, 1) if abs(curr_beta) < 1e8 else str(curr_beta),
                    "value": None,
                    "pruned": True,
                    "children": [],
                })
                continue

            next_state = game.apply(state, m)
            child_node = build_search_tree(game, next_state, depth - 1, curr_alpha, curr_beta, target_perspective, move_taken=m)
            node["children"].append(child_node)

            val = child_node["value"]
            if val is not None and val < best_val:
                best_val = val
            if best_val <= curr_alpha:
                cutoff_occurred = True
            if best_val < curr_beta:
                curr_beta = best_val

        node["value"] = best_val

    return node
