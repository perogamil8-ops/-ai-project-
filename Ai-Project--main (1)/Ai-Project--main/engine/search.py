"""Game-agnostic search algorithms: Minimax, Alpha-Beta Pruning, and Move Scoring."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from engine.base import Game, normalize_player


@dataclass(frozen=True)
class SearchResult:
    """Result of a game tree search."""
    move: Any
    score: float
    nodes: int
    time_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "move": self.move,
            "score": self.score,
            "nodes": self.nodes,
            "time_ms": self.time_ms,
        }


def minimax(game: Game, state: Any, depth: int, perspective: str | None = "computer") -> SearchResult:
    """Minimax search algorithm (pure DFS without pruning).

    Scores from the perspective of `perspective` (defaults to 'computer' for backwards compatibility;
    pass None for the player to move at the root state).
    Deterministic tie-breaking: retains the first best move encountered.
    """
    start_time = time.perf_counter()
    nodes = 0
    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))

    def _minimax(s: Any, d: int) -> tuple[Any, float]:
        nonlocal nodes
        nodes += 1

        if game.is_terminal(s):
            return None, float(game.utility(s, target_perspective))
        if d == 0:
            return None, float(game.evaluate(s, target_perspective))

        moves = game.legal_moves(s)
        player = normalize_player(game.current_player(s))
        is_max = (player == target_perspective)

        # Pass handling: if legal_moves is empty in non-terminal state
        if not moves:
            next_state = game.apply(s, None)
            _, score = _minimax(next_state, d - 1)
            return None, score

        if is_max:
            best_score = -float("inf")
            best_move_cand = moves[0]
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _minimax(next_state, d - 1)
                if score > best_score:
                    best_score = score
                    best_move_cand = m
            return best_move_cand, best_score
        else:
            best_score = float("inf")
            best_move_cand = moves[0]
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _minimax(next_state, d - 1)
                if score < best_score:
                    best_score = score
                    best_move_cand = m
            return best_move_cand, best_score

    best_move_res, best_score_res = _minimax(state, depth)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    return SearchResult(move=best_move_res, score=best_score_res, nodes=nodes, time_ms=elapsed_ms)


def alphabeta(
    game: Game,
    state: Any,
    depth: int,
    use_ordering: bool = False,
    perspective: str | None = "computer",
) -> SearchResult:
    """Alpha-Beta Pruning search algorithm.

    Scores from the perspective of `perspective` (defaults to 'computer' for backwards compatibility;
    pass None for the player to move at the root state).
    Deterministic tie-breaking: retains the first best move encountered.
    """
    start_time = time.perf_counter()
    nodes = 0
    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))

    def _alphabeta(s: Any, d: int, alpha: float, beta: float) -> tuple[Any, float]:
        nonlocal nodes
        nodes += 1

        if game.is_terminal(s):
            return None, float(game.utility(s, target_perspective))
        if d == 0:
            return None, float(game.evaluate(s, target_perspective))

        moves = game.legal_moves(s)
        player = normalize_player(game.current_player(s))
        is_max = (player == target_perspective)

        # Pass handling: if legal_moves is empty in non-terminal state
        if not moves:
            next_state = game.apply(s, None)
            _, score = _alphabeta(next_state, d - 1, alpha, beta)
            return None, score

        if use_ordering:
            moves = game.order_moves(s, moves)

        if is_max:
            best_score = -float("inf")
            best_move_cand = moves[0]
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _alphabeta(next_state, d - 1, alpha, beta)
                if score > best_score:
                    best_score = score
                    best_move_cand = m
                if best_score >= beta:
                    break  # Beta cutoff
                if best_score > alpha:
                    alpha = best_score
            return best_move_cand, best_score
        else:
            best_score = float("inf")
            best_move_cand = moves[0]
            for m in moves:
                next_state = game.apply(s, m)
                _, score = _alphabeta(next_state, d - 1, alpha, beta)
                if score < best_score:
                    best_score = score
                    best_move_cand = m
                if best_score <= alpha:
                    break  # Alpha cutoff
                if best_score < beta:
                    beta = best_score
            return best_move_cand, best_score

    best_move_res, best_score_res = _alphabeta(state, depth, -float("inf"), float("inf"))
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    return SearchResult(move=best_move_res, score=best_score_res, nodes=nodes, time_ms=elapsed_ms)


def best_move(
    game: Game,
    state: Any,
    algorithm: str = "alphabeta",
    depth: int = 1,
    perspective: str | None = None,
    use_ordering: bool = False,
) -> SearchResult:
    """Find the best move for state from `perspective` (defaults to current player to move)."""
    algo = algorithm.lower().replace("-", "").replace("_", "")
    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))

    if algo == "minimax":
        return minimax(game, state, depth, perspective=target_perspective)
    return alphabeta(game, state, depth, use_ordering=use_ordering, perspective=target_perspective)


def score_all_moves(
    game: Game,
    state: Any,
    depth: int,
    perspective: str | None = None,
) -> dict[Any, float]:
    """Score every legal move from state using a full search window per root child.

    Scores are computed from the perspective of `perspective` (defaults to player to move).
    Because a full (-inf, +inf) window is used for each root move, all moves receive
    an exact evaluation rather than a pruned bound.
    """
    moves = game.legal_moves(state)
    if not moves:
        return {}

    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))

    scores: dict[Any, float] = {}
    for m in moves:
        next_s = game.apply(state, m)
        if game.is_terminal(next_s):
            scores[m] = float(game.utility(next_s, target_perspective))
        elif depth <= 1:
            scores[m] = float(game.evaluate(next_s, target_perspective))
        else:
            # Full window search for exact value of this branch
            res = alphabeta(game, next_s, depth - 1, use_ordering=False, perspective=target_perspective)
            scores[m] = res.score

    return scores


def iterative_deepening(
    game: Game,
    state: Any,
    max_time_ms: float = 400.0,
    max_depth: int = 10,
    perspective: str | None = None,
) -> SearchResult:
    """Iterative Deepening search (for 'Expert' mode). Searches d=1,2,3... until time limit."""
    start = time.perf_counter()
    best_res: SearchResult | None = None
    total_nodes = 0

    target_perspective = normalize_player(perspective) if perspective is not None else normalize_player(game.current_player(state))

    for d in range(1, max_depth + 1):
        elapsed = (time.perf_counter() - start) * 1000.0
        if elapsed >= max_time_ms and best_res is not None:
            break
        res = alphabeta(game, state, depth=d, use_ordering=True, perspective=target_perspective)
        total_nodes += res.nodes
        best_res = res
        # If forced win detected, stop deepening
        if abs(res.score) >= 900.0:
            break

    total_time = round((time.perf_counter() - start) * 1000.0, 2)
    return SearchResult(
        move=best_res.move if best_res else None,
        score=best_res.score if best_res else 0.0,
        nodes=total_nodes,
        time_ms=total_time,
    )
