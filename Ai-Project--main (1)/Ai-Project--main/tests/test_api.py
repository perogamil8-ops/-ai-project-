"""Tests for the stateless engine API."""
from __future__ import annotations

import pytest

from engine.api import new_game, apply_human_move, ai_move, get_legal_moves


def test_api_new_game():
    for gname in ("xo", "connect4", "seega"):
        res = new_game(gname, "human")
        assert res["game"] == gname
        assert res["status"] == "ongoing"
        assert res["current_player"] == "human"
        assert len(res["legal_moves"]) > 0

    with pytest.raises(ValueError):
        new_game("invalid_game")

    with pytest.raises(ValueError):
        new_game("xo", "alien")


def test_api_human_move_and_ai_move_xo():
    res0 = new_game("xo", "human")
    # Human plays center (1, 1)
    res1 = apply_human_move("xo", res0["state"], [1, 1])
    assert res1["status"] == "ongoing"
    assert res1["current_player"] == "computer"

    # Human tries to play again when it's computer's turn
    with pytest.raises(ValueError):
        apply_human_move("xo", res1["state"], [0, 0])

    # Computer plays AI move
    res2 = ai_move("xo", res1["state"], algorithm="alphabeta", level="hard")
    assert res2["current_player"] == "human"
    assert res2["nodes"] > 0
    assert res2["move"] is not None


def test_api_illegal_moves_raise_errors():
    res0 = new_game("connect4", "human")
    # Illegal column index 9
    with pytest.raises(ValueError):
        apply_human_move("connect4", res0["state"], 9)

    # Fill col 0 manually in state to test full column validation
    board = [list(r) for r in res0["state"]["board"]]
    for r in range(6):
        board[r][0] = "human" if r % 2 == 0 else "computer"
    full_col_state = {"board": board, "player": "human"}

    # Now col 0 is full; human playing col 0 must raise ValueError
    with pytest.raises(ValueError):
        apply_human_move("connect4", full_col_state, 0)


def test_api_seega_flow():
    res0 = new_game("seega", "human")
    # Human places first piece
    res1 = apply_human_move("seega", res0["state"], [0, 0])
    assert res1["current_player"] == "human"  # 2 per turn!
    # Human places second piece
    res2 = apply_human_move("seega", res1["state"], [0, 1])
    assert res2["current_player"] == "computer"

    # Computer AI move 1
    res3 = ai_move("seega", res2["state"], "alphabeta", "medium")
    assert res3["current_player"] == "computer"
    # Computer AI move 2
    res4 = ai_move("seega", res3["state"], "alphabeta", "medium")
    assert res4["current_player"] == "human"
