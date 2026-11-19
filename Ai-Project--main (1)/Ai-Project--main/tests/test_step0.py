"""Tests for Step 0: Player perspective and score_all_moves."""
from __future__ import annotations

import pytest
from engine.base import P1, P2, normalize_player, opponent
from engine.games.xo import XOGame
from engine.games.connect4 import Connect4Game
from engine.games.seega import SeegaGame
from engine.search import minimax, alphabeta, best_move, score_all_moves


def test_player_normalization():
    assert normalize_player("p1") == "human"
    assert normalize_player("P1") == "human"
    assert normalize_player("player 1") == "human"
    assert normalize_player(0) == "human"
    assert normalize_player("human") == "human"

    assert normalize_player("p2") == "computer"
    assert normalize_player("P2") == "computer"
    assert normalize_player("player 2") == "computer"
    assert normalize_player(1) == "computer"
    assert normalize_player("computer") == "computer"

    assert opponent("p1") == "computer"
    assert opponent("p2") == "human"


def test_perspective_symmetry_xo():
    game = XOGame()
    s = game.initial_state("human")
    s1 = game.apply(s, (1, 1))  # Human center

    # Utility symmetry on win/loss
    res_p1 = alphabeta(game, s1, depth=3, perspective="human")
    res_p2 = alphabeta(game, s1, depth=3, perspective="computer")
    assert res_p1.score == -res_p2.score

    # Evaluate symmetry
    assert game.evaluate(s1, "human") == -game.evaluate(s1, "computer")
    assert game.evaluate(s1, "p1") == -game.evaluate(s1, "p2")


def test_perspective_symmetry_connect4():
    game = Connect4Game()
    s = game.initial_state("human")
    s1 = game.apply(s, 3)

    assert game.evaluate(s1, "human") == -game.evaluate(s1, "computer")
    assert game.evaluate(s1, "p1") == -game.evaluate(s1, "p2")

    res_p1 = alphabeta(game, s1, depth=2, perspective="human")
    res_p2 = alphabeta(game, s1, depth=2, perspective="computer")
    assert res_p1.score == -res_p2.score


def test_score_all_moves_best_equals_best_move_xo():
    game = XOGame()
    s0 = game.initial_state("human")
    # Human plays center
    s1 = game.apply(s0, (1, 1))

    # Next is computer to move
    scores = score_all_moves(game, s1, depth=4, perspective=None)
    bm = best_move(game, s1, algorithm="alphabeta", depth=4, perspective=None)

    best_from_scores = max(scores.items(), key=lambda item: item[1])[0]
    assert bm.move == best_from_scores
    assert scores[best_from_scores] == bm.score


def test_score_all_moves_best_equals_best_move_connect4():
    game = Connect4Game()
    s0 = game.initial_state("human")
    s1 = game.apply(s0, 3)

    scores = score_all_moves(game, s1, depth=3, perspective=None)
    bm = best_move(game, s1, algorithm="alphabeta", depth=3, perspective=None)

    best_from_scores = max(scores.items(), key=lambda item: item[1])[0]
    assert bm.move == best_from_scores
    assert scores[best_from_scores] == bm.score


def test_score_all_moves_for_human_perspective():
    game = XOGame()
    s0 = game.initial_state("human")
    scores = score_all_moves(game, s0, depth=3, perspective="human")
    bm = best_move(game, s0, algorithm="alphabeta", depth=3, perspective="human")

    best_from_scores = max(scores.items(), key=lambda item: item[1])[0]
    assert bm.move == best_from_scores
