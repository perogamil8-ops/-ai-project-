"""Post-game analysis engine (chess-engine style game review)."""
from __future__ import annotations

import math
from typing import Any

from engine.base import Game, normalize_player, opponent
from engine.search import score_all_moves, alphabeta

# Win-probability scaling constant k per game: p = 1 / (1 + exp(-score / k))
K_SCALING = {
    "xo": 10.0,
    "connect4": 50.0,
    "seega": 15.0,
}

# Classification thresholds on win-probability loss (Delta p in [0.0, 1.0])
# Documented code constants as required by project specification
THRESH_BEST = 0.005       # Delta p <= 0.005 or identical move
THRESH_GOOD = 0.05        # Delta p <= 0.05
THRESH_INACCURACY = 0.12  # Delta p <= 0.12
THRESH_MISTAKE = 0.25     # Delta p <= 0.25
# Above 0.25 is classified as "Blunder"


def win_probability(score: float, game_name: str) -> float:
    """Map evaluation score to win probability in [0.0, 1.0] using logistic sigmoid."""
    k = K_SCALING.get(game_name.lower(), 20.0)

    # Forced win/loss saturation
    if score >= 900.0:
        return 1.0
    if score <= -900.0:
        return 0.0

    try:
        return 1.0 / (1.0 + math.exp(-score / k))
    except OverflowError:
        return 1.0 if score > 0 else 0.0


def classify_loss(loss_prob: float, is_same_move: bool = False) -> str:
    """Classify move quality based on win-probability loss."""
    if is_same_move or loss_prob <= THRESH_BEST:
        return "Best"
    if loss_prob <= THRESH_GOOD:
        return "Good"
    if loss_prob <= THRESH_INACCURACY:
        return "Inaccuracy"
    if loss_prob <= THRESH_MISTAKE:
        return "Mistake"
    return "Blunder"


def analyze_game(
    game: Game,
    first_player: str,
    moves: list[Any],
    mode: str = "human_vs_computer",
    depth_override: int | None = None,
) -> dict[str, Any]:
    """Replay and evaluate an entire match move-by-move.

    Returns move-by-move accuracy, evaluations, classifications, and critical moments.
    """
    gname = game.__class__.__name__.lower().replace("game", "").replace("engine", "")

    # Default review depth per game specification
    if depth_override is not None:
        eval_depth = depth_override
    elif gname == "xo":
        eval_depth = 9  # Full search for Tic-Tac-Toe
    elif gname == "connect4":
        eval_depth = 5
    elif gname == "seega":
        eval_depth = 4
    else:
        eval_depth = 3

    current_state = game.initial_state(first_player)
    analysis_steps = []
    p1_losses = []
    p2_losses = []
    p1_counts = {"Best": 0, "Good": 0, "Inaccuracy": 0, "Mistake": 0, "Blunder": 0}
    p2_counts = {"Best": 0, "Good": 0, "Inaccuracy": 0, "Mistake": 0, "Blunder": 0}

    max_loss = -1.0
    critical_moment: dict[str, Any] | None = None

    for idx, move in enumerate(moves):
        mover = game.current_player(current_state)
        norm_mover = normalize_player(mover)
        is_p1 = (norm_mover == "human")

        # Seega placement phase moves are not analyzed with search
        if gname == "seega" and hasattr(current_state, "phase") and current_state.phase == "placement":
            next_state = game.apply(current_state, move)
            analysis_steps.append({
                "move_no": idx + 1,
                "player": mover,
                "played": move,
                "best": None,
                "played_score": 0.0,
                "best_score": 0.0,
                "classification": "Not Analyzed",
                "loss": 0.0,
                "eval_after": 0.0,
                "state_after": game.to_json(next_state),
                "comment": "Placement phase move",
            })
            current_state = next_state
            continue

        # Score all candidate moves from mover's perspective
        move_scores = score_all_moves(game, current_state, depth=eval_depth, perspective=mover)

        if not move_scores:
            # Player was blocked and passed
            next_state = game.apply(current_state, move)
            analysis_steps.append({
                "move_no": idx + 1,
                "player": mover,
                "played": None,
                "best": None,
                "played_score": 0.0,
                "best_score": 0.0,
                "classification": "Best",
                "loss": 0.0,
                "eval_after": 0.0,
                "state_after": game.to_json(next_state),
                "comment": "Pass move (forced)",
            })
            current_state = next_state
            continue

        # Normalization of played move representation for matching
        best_cand, best_raw_score = max(move_scores.items(), key=lambda x: x[1])

        # Match played move to score
        played_raw_score = move_scores.get(move)
        if played_raw_score is None:
            # Try tuple/list conversions
            for cand_m, cand_sc in move_scores.items():
                if cand_m == move or str(cand_m) == str(move):
                    played_raw_score = cand_sc
                    break
        if played_raw_score is None:
            played_raw_score = best_raw_score  # Fallback if move missing

        best_p = win_probability(best_raw_score, gname)
        played_p = win_probability(played_raw_score, gname)
        prob_loss = max(0.0, best_p - played_p)

        is_same = (move == best_cand or str(move) == str(best_cand))
        classification = classify_loss(prob_loss, is_same_move=is_same)

        if is_p1:
            p1_losses.append(prob_loss)
            p1_counts[classification] += 1
        else:
            p2_losses.append(prob_loss)
            p2_counts[classification] += 1

        next_state = game.apply(current_state, move)

        # Eval after move from P1's view in [-1.0, 1.0]
        # P1 score at next_state
        if game.is_terminal(next_state):
            score_p1 = float(game.utility(next_state, "human"))
        else:
            score_p1 = float(game.evaluate(next_state, "human"))

        p1_prob = win_probability(score_p1, gname)
        eval_after_p1 = round((2.0 * p1_prob) - 1.0, 3)

        step_info = {
            "move_no": idx + 1,
            "player": mover,
            "played": move,
            "best": best_cand,
            "played_score": round(played_raw_score, 1),
            "best_score": round(best_raw_score, 1),
            "classification": classification,
            "loss": round(prob_loss, 3),
            "eval_after": eval_after_p1,
            "state_after": game.to_json(next_state),
        }
        analysis_steps.append(step_info)

        if prob_loss > max_loss and classification in ("Mistake", "Blunder"):
            max_loss = prob_loss
            critical_moment = {
                "move_no": idx + 1,
                "player": mover,
                "played": move,
                "best": best_cand,
                "loss": round(prob_loss, 3),
                "classification": classification,
            }

        current_state = next_state

    # Accuracy percentage = 100 * (1 - avg_loss)
    p1_avg_loss = (sum(p1_losses) / len(p1_losses)) if p1_losses else 0.0
    p2_avg_loss = (sum(p2_losses) / len(p2_losses)) if p2_losses else 0.0
    p1_acc = round(max(0.0, min(100.0, 100.0 * (1.0 - p1_avg_loss))), 1)
    p2_acc = round(max(0.0, min(100.0, 100.0 * (1.0 - p2_avg_loss))), 1)

    labels = {
        "p1": "Player 1" if mode == "friends" else "Human",
        "p2": "Player 2" if mode == "friends" else "Computer",
    }

    return {
        "game": gname,
        "mode": mode,
        "eval_depth": eval_depth,
        "total_moves": len(moves),
        "steps": analysis_steps,
        "player1": {
            "label": labels["p1"],
            "accuracy": p1_acc,
            "counts": p1_counts,
        },
        "player2": {
            "label": labels["p2"],
            "accuracy": p2_acc,
            "counts": p2_counts,
        },
        "critical_moment": critical_moment,
    }
