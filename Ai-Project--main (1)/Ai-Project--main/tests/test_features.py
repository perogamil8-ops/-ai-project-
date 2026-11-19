"""Tests for Bonus Features: Friends mode, Hint, Post-Game Analysis, Tree Viz, and Zobrist TT."""
from __future__ import annotations

import pytest

from engine.api import new_game, apply_human_move, ai_move, hint, analyze_game_match, eval_position
from engine.games.xo import XOGame
from engine.games.connect4 import Connect4Game
from engine.games.seega import SeegaGame
from engine.tree_viz import build_search_tree
from engine.zobrist import TranspositionTable, alphabeta_with_tt
from engine.search import iterative_deepening


def test_friends_mode_xo():
    """Test hot-seat Friends mode alternating between Player 1 and Player 2."""
    g = new_game("xo", "human", mode="friends")
    assert g["mode"] == "friends"
    assert g["player_labels"]["human"] == "Player 1"
    assert g["player_labels"]["computer"] == "Player 2"

    # Player 1 plays (0, 0)
    g1 = apply_human_move("xo", g["state"], [0, 0], mode="friends")
    assert g1["current_player"] == "computer"  # Next is Player 2
    assert "Player 2" in g1["message"]

    # Player 2 plays (1, 1) using apply_human_move!
    g2 = apply_human_move("xo", g1["state"], [1, 1], mode="friends")
    assert g2["current_player"] == "human"  # Back to Player 1


def test_friends_mode_seega_placement():
    """Test Seega placement in Friends mode: both players place 2 pieces manually."""
    g0 = new_game("seega", "human", mode="friends")
    assert g0["current_player"] == "human"

    # P1 places piece 1
    g1 = apply_human_move("seega", g0["state"], [0, 0], mode="friends")
    assert g1["current_player"] == "human"  # Still P1

    # P1 places piece 2
    g2 = apply_human_move("seega", g1["state"], [0, 1], mode="friends")
    assert g2["current_player"] == "computer"  # Now P2

    # P2 places piece 1 manually (no random computer placement)
    g3 = apply_human_move("seega", g2["state"], [0, 2], mode="friends")
    assert g3["current_player"] == "computer"  # Still P2

    # P2 places piece 2 manually
    g4 = apply_human_move("seega", g3["state"], [0, 3], mode="friends")
    assert g4["current_player"] == "human"  # Passes back to P1


def test_hint_xo():
    """Test hint generation for XO."""
    g0 = new_game("xo", "human")
    # Human center
    g1 = apply_human_move("xo", g0["state"], [1, 1])

    h = hint("xo", g1["state"])
    assert h["best_move"] is not None
    assert len(h["scores_per_move"]) > 0
    assert len(h["scores_list"]) > 0
    assert h["nodes"] > 0


def test_hint_seega_placement():
    """Test that hint during Seega placement informs the user it is only available in movement phase."""
    g0 = new_game("seega", "human")
    h = hint("seega", g0["state"])
    assert h["best_move"] is None
    assert "movement phase" in h["message"]


def test_analysis_scripted_xo_blunder():
    """Scripted XO match with a known blunder: Human threatens win, Computer fails to block."""
    # Move 1: Human (0, 0)
    # Move 2: Computer (1, 1)
    # Move 3: Human (0, 1) -> Human now threatens [0, 2]!
    # Move 4: Computer plays [2, 2] instead of blocking at [0, 2] -> BLUNDER!
    # Move 5: Human plays [0, 2] and wins!
    moves = [[0, 0], [1, 1], [0, 1], [2, 2], [0, 2]]
    report = analyze_game_match("xo", first_player="human", moves=moves)

    assert report["total_moves"] == 5
    # Move 4 by Computer (index 3) must be classified as Blunder
    step_4 = report["steps"][3]
    assert step_4["player"] == "computer"
    assert step_4["played"] == (2, 2)
    assert step_4["best"] == (0, 2)  # Correct best move was blocking at (0, 2)
    assert step_4["classification"] == "Blunder"

    # Critical moment must point to Move 4
    assert report["critical_moment"] is not None
    assert report["critical_moment"]["move_no"] == 4
    assert report["critical_moment"]["classification"] == "Blunder"


def test_analysis_xo_perfect_play():
    """Exhaustive check: a match with optimal play must classify all moves Best."""
    # A known optimal draw game in XO:
    # 1. H: (1, 1) Center
    # 2. C: (0, 0) Corner
    # 3. H: (0, 2) Corner
    # 4. C: (2, 0) Block
    # 5. H: (1, 0)
    # 6. C: (1, 2) Block
    # 7. H: (0, 1)
    # 8. C: (2, 1) Block
    # 9. H: (2, 2) Draw
    moves = [(1, 1), (0, 0), (0, 2), (2, 0), (1, 0), (1, 2), (0, 1), (2, 1), (2, 2)]
    report = analyze_game_match("xo", first_player="human", moves=moves)

    assert report["total_moves"] == 9
    for s in report["steps"]:
        assert s["classification"] == "Best", f"Move {s['move_no']} by {s['player']} was {s['classification']} instead of Best!"
    assert report["player1"]["accuracy"] == 100.0
    assert report["player2"]["accuracy"] == 100.0


def test_search_tree_visualizer():
    """Verify Search Tree Visualizer produces tree with alpha, beta, value, and pruned flags."""
    game = XOGame()
    s = game.initial_state("human")
    s1 = game.apply(s, (1, 1))

    tree = build_search_tree(game, s1, depth=2)
    assert "alpha_in" in tree
    assert "beta_in" in tree
    assert "value" in tree
    assert "children" in tree
    assert len(tree["children"]) > 0

    # Verify at least one branch or leaf exists
    child = tree["children"][0]
    assert "pruned" in child


def test_connect4_zobrist_transposition_table():
    """Verify Connect 4 Zobrist Transposition Table functions properly and accelerates search."""
    game = Connect4Game()
    s = game.initial_state("computer")
    s = game.apply(s, 3)
    s = game.apply(s, 3)

    tt = TranspositionTable()
    best_m, val, nodes = alphabeta_with_tt(game, s, depth=3, tt=tt, perspective="computer")
    assert best_m in game.legal_moves(s)
    assert nodes > 0
    # Second search should hit TT
    best_m2, val2, nodes2 = alphabeta_with_tt(game, s, depth=3, tt=tt, perspective="computer")
    assert best_m2 == best_m
    assert val2 == val
    assert tt.hits > 0


def test_iterative_deepening():
    """Verify iterative deepening returns valid move within time budget."""
    game = XOGame()
    s = game.initial_state("computer")
    res = iterative_deepening(game, s, max_time_ms=100.0, max_depth=9)
    assert res.move is not None
    assert res.nodes > 0


def test_live_eval_position():
    """Verify live evaluation returns normalized evaluation in [-1.0, 1.0]."""
    res = eval_position("xo", {"board": [[None, None, None], [None, None, None], [None, None, None]], "player": "human"})
    assert "eval_normalized" in res
    assert -1.0 <= res["eval_normalized"] <= 1.0
