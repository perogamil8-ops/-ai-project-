"""Benchmark and comparison suite for search algorithms and AI-vs-AI games."""
from __future__ import annotations

import csv
import json
import os
import random
from typing import Any

from engine.base import Game
from engine.search import minimax, alphabeta


def _game_name(game: Game) -> str:
    name = game.__class__.__name__.lower()
    for suffix in ("game", "engine"):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name


def compare(game: Game, state: Any, depth: int) -> dict[str, Any]:
    """Compare Minimax, Alpha-Beta, and Alpha-Beta with Move Ordering on a single state."""
    res_mm = minimax(game, state, depth)
    res_ab = alphabeta(game, state, depth, use_ordering=False)
    res_abo = alphabeta(game, state, depth, use_ordering=True)

    return {
        "minimax": {
            "move": res_mm.move,
            "score": res_mm.score,
            "nodes": res_mm.nodes,
            "time_ms": res_mm.time_ms,
        },
        "alphabeta": {
            "move": res_ab.move,
            "score": res_ab.score,
            "nodes": res_ab.nodes,
            "time_ms": res_ab.time_ms,
        },
        "alphabeta_ordered": {
            "move": res_abo.move,
            "score": res_abo.score,
            "nodes": res_abo.nodes,
            "time_ms": res_abo.time_ms,
        },
        "same_move": res_mm.move == res_ab.move,
        "same_score": res_mm.score == res_ab.score,
    }


def _sample_midgame_states(game: Game, n_positions: int, seed: int = 0) -> list[Any]:
    """Generate diverse valid mid-game states for benchmarking."""
    rng = random.Random(seed)
    states = []
    gname = _game_name(game)

    # Move count ranges for sampling mid-game positions
    if gname == "xo":
        move_range = (1, 4)
    elif gname == "connect4":
        move_range = (2, 8)
    elif gname == "seega":
        move_range = (2, 10)
    else:
        move_range = (2, 6)

    attempts = 0
    while len(states) < n_positions and attempts < n_positions * 30:
        attempts += 1
        s = game.initial_state(rng.choice(["human", "computer"]))
        num_plies = rng.randint(move_range[0], move_range[1])

        # If Seega, let it initialize through placement if needed
        if gname == "seega" and hasattr(s, "phase") and s.phase == "placement":
            # Fast placement to reach movement phase for movement search benchmarks
            while hasattr(s, "phase") and s.phase == "placement" and not game.is_terminal(s):
                moves = game.legal_moves(s)
                if not moves:
                    break
                s = game.apply(s, rng.choice(moves))

        for _ in range(num_plies):
            if game.is_terminal(s):
                break
            moves = game.legal_moves(s)
            if not moves:
                break
            s = game.apply(s, rng.choice(moves))

        if not game.is_terminal(s) and game.legal_moves(s):
            # Avoid duplicate states
            s_json = json.dumps(game.to_json(s), sort_keys=True)
            if not any(json.dumps(game.to_json(existing), sort_keys=True) == s_json for existing in states):
                states.append(s)

    # If could not sample enough, pad with initial state variations
    if not states:
        states.append(game.initial_state("computer"))

    while len(states) < n_positions:
        states.append(states[len(states) % len(states)])

    return states[:n_positions]


def run_suite(game: Game, n_positions: int = 50, seed: int = 0, depth: int | None = None) -> dict[str, Any]:
    """Run benchmark comparison suite across multiple positions and export results."""
    gname = _game_name(game)
    if depth is None:
        depth = game.depth_for("medium")

    states = _sample_midgame_states(game, n_positions, seed)
    rows = []

    for idx, s in enumerate(states):
        comp = compare(game, s, depth)
        mm_nodes = comp["minimax"]["nodes"]
        ab_nodes = comp["alphabeta"]["nodes"]
        abo_nodes = comp["alphabeta_ordered"]["nodes"]

        red_pct = round(((mm_nodes - ab_nodes) / mm_nodes) * 100.0, 1) if mm_nodes > 0 else 0.0
        ord_red_pct = round(((mm_nodes - abo_nodes) / mm_nodes) * 100.0, 1) if mm_nodes > 0 else 0.0

        row = {
            "position": idx + 1,
            "minimax_nodes": mm_nodes,
            "minimax_time_ms": comp["minimax"]["time_ms"],
            "alphabeta_nodes": ab_nodes,
            "alphabeta_time_ms": comp["alphabeta"]["time_ms"],
            "alphabeta_ordered_nodes": abo_nodes,
            "alphabeta_ordered_time_ms": comp["alphabeta_ordered"]["time_ms"],
            "same_move": comp["same_move"],
            "reduction_pct": red_pct,
            "ordered_reduction_pct": ord_red_pct,
        }
        rows.append(row)

    total_positions = len(rows)
    avg_mm_nodes = round(sum(r["minimax_nodes"] for r in rows) / total_positions, 1)
    avg_mm_time = round(sum(r["minimax_time_ms"] for r in rows) / total_positions, 2)
    avg_ab_nodes = round(sum(r["alphabeta_nodes"] for r in rows) / total_positions, 1)
    avg_ab_time = round(sum(r["alphabeta_time_ms"] for r in rows) / total_positions, 2)
    avg_abo_nodes = round(sum(r["alphabeta_ordered_nodes"] for r in rows) / total_positions, 1)
    avg_abo_time = round(sum(r["alphabeta_ordered_time_ms"] for r in rows) / total_positions, 2)

    avg_red_pct = round(((avg_mm_nodes - avg_ab_nodes) / avg_mm_nodes) * 100.0, 1) if avg_mm_nodes > 0 else 0.0
    avg_ord_red_pct = round(((avg_mm_nodes - avg_abo_nodes) / avg_mm_nodes) * 100.0, 1) if avg_mm_nodes > 0 else 0.0

    averages = {
        "avg_minimax_nodes": avg_mm_nodes,
        "avg_minimax_time_ms": avg_mm_time,
        "avg_alphabeta_nodes": avg_ab_nodes,
        "avg_alphabeta_time_ms": avg_ab_time,
        "avg_alphabeta_ordered_nodes": avg_abo_nodes,
        "avg_alphabeta_ordered_time_ms": avg_abo_time,
        "avg_reduction_pct": avg_red_pct,
        "avg_ordered_reduction_pct": avg_ord_red_pct,
    }

    result = {
        "game": gname,
        "depth": depth,
        "n_positions": total_positions,
        "averages": averages,
        "rows": rows,
    }

    # Save JSON and CSV to results/
    os.makedirs("results", exist_ok=True)
    json_path = os.path.join("results", f"benchmark_{gname}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    csv_path = os.path.join("results", f"benchmark_{gname}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "position", "minimax_nodes", "minimax_time_ms",
            "alphabeta_nodes", "alphabeta_time_ms",
            "alphabeta_ordered_nodes", "alphabeta_ordered_time_ms",
            "reduction_pct", "ordered_reduction_pct", "same_move"
        ])
        for r in rows:
            writer.writerow([
                r["position"], r["minimax_nodes"], r["minimax_time_ms"],
                r["alphabeta_nodes"], r["alphabeta_time_ms"],
                r["alphabeta_ordered_nodes"], r["alphabeta_ordered_time_ms"],
                r["reduction_pct"], r["ordered_reduction_pct"], r["same_move"]
            ])

    return result


def ai_vs_ai(
    game: Game,
    algo_a: str,
    level_a: str,
    algo_b: str,
    level_b: str,
    seed: int = 0,
    max_moves: int = 100,
) -> dict[str, Any]:
    """Run an AI vs AI simulation and record step-by-step progress."""
    rng = random.Random(seed)
    state = game.initial_state("human")  # Player A is 'human' role, Player B is 'computer' role
    history = []
    step = 0

    gname = _game_name(game)

    while not game.is_terminal(state) and step < max_moves:
        current = game.current_player(state)
        # Check Seega placement phase: random empty square
        if gname == "seega" and hasattr(state, "phase") and state.phase == "placement":
            moves = game.legal_moves(state)
            if not moves:
                break
            move = rng.choice(moves)
            state = game.apply(state, move)
            step += 1
            history.append({
                "step": step,
                "player": current,
                "move": move,
                "nodes": 1,
                "time_ms": 0.0,
                "score": 0.0,
                "state": game.to_json(state),
            })
            continue

        algo = algo_a if current == "human" else algo_b
        level = level_a if current == "human" else level_b
        depth = game.depth_for(level)

        legal = game.legal_moves(state)
        if not legal:
            # Pass move
            state = game.apply(state, None)
            step += 1
            history.append({
                "step": step,
                "player": current,
                "move": None,
                "nodes": 1,
                "time_ms": 0.0,
                "score": 0.0,
                "state": game.to_json(state),
            })
            continue

        # XO easy: random move
        if gname == "xo" and level == "easy":
            move = rng.choice(legal)
            nodes = 1
            time_ms = 0.0
            score = 0.0
        else:
            if algo == "minimax":
                search_res = minimax(game, state, depth)
            else:
                search_res = alphabeta(game, state, depth, use_ordering=True)
            move = search_res.move
            nodes = search_res.nodes
            time_ms = search_res.time_ms
            score = search_res.score

        state = game.apply(state, move)
        step += 1
        history.append({
            "step": step,
            "player": current,
            "move": move,
            "nodes": nodes,
            "time_ms": time_ms,
            "score": score,
            "state": game.to_json(state),
        })

    return {
        "game": gname,
        "winner": game.winner(state),
        "winning_cells": game.winning_cells(state),
        "total_moves": len(history),
        "history": history,
        "final_state": game.to_json(state),
    }
