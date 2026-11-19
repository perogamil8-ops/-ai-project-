"""Tests for Connect 4 game engine."""
from __future__ import annotations

import pytest

from engine.games.connect4 import Connect4Game, Connect4State, ROWS, COLS
from engine.search import minimax, alphabeta


def test_connect4_initial_state():
    game = Connect4Game()
    s = game.initial_state("human")
    assert game.current_player(s) == "human"
    assert len(game.legal_moves(s)) == COLS
    assert not game.is_terminal(s)
    assert game.winner(s) is None
    assert game.winning_cells(s) == []


def test_connect4_gravity_and_immutability():
    game = Connect4Game()
    s0 = game.initial_state("human")
    s1 = game.apply(s0, 3)

    # In s0, all empty
    assert all(s0.board[r][3] is None for r in range(ROWS))
    # In s1, lowest cell (row 5) is filled
    assert s1.board[5][3] == "human"
    assert all(s1.board[r][3] is None for r in range(ROWS - 1))

    # Second coin in same column falls to row 4
    s2 = game.apply(s1, 3)
    assert s2.board[4][3] == "computer"
    assert s2.board[5][3] == "human"
    # Ensure s1 not mutated
    assert s1.board[4][3] is None


def test_connect4_full_column_illegal():
    game = Connect4Game()
    s = game.initial_state("human")
    # Fill column 0
    for _ in range(ROWS):
        s = game.apply(s, 0)

    assert 0 not in game.legal_moves(s)
    with pytest.raises(ValueError):
        game.apply(s, 0)


def test_connect4_horizontal_win():
    game = Connect4Game()
    # Alternate drops to create horizontal 4 in row 5 for human (cols 0, 1, 2, 3)
    s = game.initial_state("human")
    moves = [0, 0, 1, 1, 2, 2, 3]  # Human: 0, 1, 2, 3 (row 5)
    for m in moves:
        s = game.apply(s, m)

    assert game.is_terminal(s)
    assert game.winner(s) == "human"
    cells = game.winning_cells(s)
    assert len(cells) == 4
    assert set(cells) == {(5, 0), (5, 1), (5, 2), (5, 3)}


def test_connect4_vertical_win():
    game = Connect4Game()
    s = game.initial_state("human")
    moves = [0, 1, 0, 1, 0, 1, 0]  # Human plays 4 in col 0
    for m in moves:
        s = game.apply(s, m)

    assert game.is_terminal(s)
    assert game.winner(s) == "human"
    cells = game.winning_cells(s)
    assert len(cells) == 4
    assert set(cells) == {(5, 0), (4, 0), (3, 0), (2, 0)}


def test_connect4_diagonal_down_right_win():
    game = Connect4Game()
    # Target diagonal down-right: (2,0), (3,1), (4,2), (5,3)
    # Heights needed in columns:
    # col 0: 4 pieces (human on row 2)
    # col 1: 3 pieces (human on row 3)
    # col 2: 2 pieces (human on row 4)
    # col 3: 1 piece  (human on row 5)
    # Let's craft state directly to test winning logic
    board = [[None for _ in range(COLS)] for _ in range(ROWS)]
    board[2][0] = "human"
    board[3][1] = "human"
    board[4][2] = "human"
    board[5][3] = "human"
    state = Connect4State(board=tuple(tuple(r) for r in board), player="computer")
    assert game.is_terminal(state)
    assert game.winner(state) == "human"
    assert set(game.winning_cells(state)) == {(2, 0), (3, 1), (4, 2), (5, 3)}


def test_connect4_diagonal_up_right_win():
    game = Connect4Game()
    # Target diagonal up-right: (5,0), (4,1), (3,2), (2,3)
    board = [[None for _ in range(COLS)] for _ in range(ROWS)]
    board[5][0] = "computer"
    board[4][1] = "computer"
    board[3][2] = "computer"
    board[2][3] = "computer"
    state = Connect4State(board=tuple(tuple(r) for r in board), player="human")
    assert game.is_terminal(state)
    assert game.winner(state) == "computer"
    assert set(game.winning_cells(state)) == {(5, 0), (4, 1), (3, 2), (2, 3)}


def test_connect4_draw():
    game = Connect4Game()
    draw_board = [
        ['human', 'computer', 'human', 'human', 'computer', 'human', 'computer'],
        ['human', 'human', 'computer', 'computer', 'computer', 'human', 'computer'],
        ['computer', 'computer', 'computer', 'human', 'human', 'computer', 'human'],
        ['computer', 'human', 'human', 'human', 'computer', 'human', 'human'],
        ['human', 'computer', 'computer', 'human', 'computer', 'human', 'computer'],
        ['human', 'human', 'computer', 'computer', 'human', 'computer', 'computer'],
    ]
    s_draw = Connect4State(board=tuple(tuple(r) for r in draw_board), player="human")
    assert game.winner(s_draw) == "draw"
    assert game.is_terminal(s_draw)
    assert game.winning_cells(s_draw) == []
    assert game.utility(s_draw, "human") == 0.0
    assert game.utility(s_draw, "computer") == 0.0


def test_connect4_search_alphabeta_minimax_equivalence():
    game = Connect4Game()
    s = game.initial_state("computer")
    # Drop 2 pieces
    s = game.apply(s, 3)
    s = game.apply(s, 2)

    res_mm = minimax(game, s, depth=3)
    res_ab = alphabeta(game, s, depth=3, use_ordering=False)
    res_abo = alphabeta(game, s, depth=3, use_ordering=True)

    assert res_mm.score == res_ab.score
    assert res_mm.move == res_ab.move
    assert res_ab.nodes <= res_mm.nodes
    assert res_abo.score == res_mm.score
