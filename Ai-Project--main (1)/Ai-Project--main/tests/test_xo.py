"""Tests for Tic-Tac-Toe (XO) and search guarantees."""
from __future__ import annotations

import pytest

from engine.games.xo import XOGame, XOState, WINNING_LINES
from engine.search import minimax, alphabeta


def test_xo_initial_state():
    game = XOGame()
    state = game.initial_state("human")
    assert game.current_player(state) == "human"
    assert len(game.legal_moves(state)) == 9
    assert not game.is_terminal(state)
    assert game.winner(state) is None
    assert game.winning_cells(state) == []


def test_xo_immutability():
    game = XOGame()
    s0 = game.initial_state("human")
    s1 = game.apply(s0, (1, 1))

    assert s0.board[1][1] is None
    assert s1.board[1][1] == "human"
    assert s0.player == "human"
    assert s1.player == "computer"
    assert s0 is not s1


def test_xo_all_win_lines():
    game = XOGame()
    for line in WINNING_LINES:
        # Build state where 'human' holds this line
        board = [[None for _ in range(3)] for _ in range(3)]
        for r, c in line:
            board[r][c] = "human"
        state = XOState(board=tuple(tuple(r) for r in board), player="computer")
        assert game.is_terminal(state)
        assert game.winner(state) == "human"
        assert set(game.winning_cells(state)) == set(line)
        assert game.utility(state, "human") == 1000.0
        assert game.utility(state, "computer") == -1000.0


def test_xo_draw():
    game = XOGame()
    # Draw configuration:
    # X O X
    # X X O
    # O X O
    draw_board = (
        ("human", "computer", "human"),
        ("human", "human", "computer"),
        ("computer", "human", "computer"),
    )
    state = XOState(board=draw_board, player="human")
    assert game.is_terminal(state)
    assert game.winner(state) == "draw"
    assert game.winning_cells(state) == []
    assert game.utility(state, "computer") == 0.0
    assert game.utility(state, "human") == 0.0


def test_xo_json_serialization():
    game = XOGame()
    s0 = game.initial_state("computer")
    s1 = game.apply(s0, (0, 0))
    data = game.to_json(s1)
    s2 = game.from_json(data)
    assert s1.board == s2.board
    assert s1.player == s2.player


def test_xo_search_minimax_alphabeta_equivalence():
    game = XOGame()
    s0 = game.initial_state("computer")
    s1 = game.apply(s0, (0, 0)) # C
    s2 = game.apply(s1, (1, 1)) # H
    s3 = game.apply(s2, (2, 2)) # C

    res_mm = minimax(game, s3, depth=6)
    res_ab = alphabeta(game, s3, depth=6, use_ordering=False)
    res_abo = alphabeta(game, s3, depth=6, use_ordering=True)

    assert res_mm.score == res_ab.score
    assert res_mm.move == res_ab.move
    assert res_ab.nodes <= res_mm.nodes
    assert res_abo.score == res_mm.score


def test_xo_hard_ai_never_loses_human_first():
    """Exhaustive game-tree check: when Human plays first, hard AI never loses."""
    game = XOGame()

    def play_all(state: XOState):
        if game.is_terminal(state):
            w = game.winner(state)
            assert w in ("computer", "draw"), f"Hard AI lost to human! Winner was {w}"
            return

        if state.player == "human":
            for m in game.legal_moves(state):
                play_all(game.apply(state, m))
        else:
            res = alphabeta(game, state, depth=9, use_ordering=True)
            play_all(game.apply(state, res.move))

    initial = game.initial_state("human")
    play_all(initial)


def test_xo_hard_ai_never_loses_computer_first():
    """Exhaustive game-tree check: when Computer plays first, hard AI never loses."""
    game = XOGame()

    def play_all(state: XOState):
        if game.is_terminal(state):
            w = game.winner(state)
            assert w in ("computer", "draw"), f"Hard AI lost when playing first! Winner was {w}"
            return

        if state.player == "human":
            for m in game.legal_moves(state):
                play_all(game.apply(state, m))
        else:
            res = alphabeta(game, state, depth=9, use_ordering=True)
            play_all(game.apply(state, res.move))

    initial = game.initial_state("computer")
    play_all(initial)
