"""Tests for Seega game rules, edge cases, and search integration."""
from __future__ import annotations

import pytest

from engine.games.seega import SeegaGame, SeegaState, CENTER, find_captures
from engine.search import minimax, alphabeta


def test_seega_initial_state():
    game = SeegaGame()
    s = game.initial_state("human")
    assert s.phase == "placement"
    assert s.player == "human"
    assert s.placed_this_turn == 0
    assert s.human_placed == 0
    assert s.computer_placed == 0
    assert not game.is_terminal(s)


def test_seega_center_forbidden_in_placement():
    game = SeegaGame()
    s = game.initial_state("human")
    # Center (2, 2) is never legal in placement
    assert CENTER not in game.legal_moves(s)
    with pytest.raises(ValueError):
        game.apply(s, CENTER)


def test_seega_placement_two_at_a_time():
    game = SeegaGame()
    s0 = game.initial_state("human")
    # First placement by human
    s1 = game.apply(s0, (0, 0))
    assert s1.player == "human"  # Still human's turn!
    assert s1.placed_this_turn == 1
    assert s1.human_placed == 1
    assert s0.board[0][0] is None  # Immutability
    assert s1.board[0][0] == "human"

    # Second placement by human
    s2 = game.apply(s1, (0, 1))
    assert s2.player == "computer"  # Now turn passes to computer!
    assert s2.placed_this_turn == 0
    assert s2.human_placed == 2

    # First placement by computer
    s3 = game.apply(s2, (0, 2))
    assert s3.player == "computer"  # Still computer's turn!
    assert s3.placed_this_turn == 1
    assert s3.computer_placed == 1

    # Second placement by computer
    s4 = game.apply(s3, (0, 3))
    assert s4.player == "human"  # Passes back to human
    assert s4.placed_this_turn == 0


def test_seega_who_moves_first_in_phase_2():
    game = SeegaGame()
    # Case A: Human places first -> Computer must move first in Phase 2
    s = game.initial_state("human")
    assert s.first_placer == "human"
    all_non_center = [(r, c) for r in range(5) for c in range(5) if (r, c) != CENTER]

    for m in all_non_center:
        s = game.apply(s, m)

    assert s.phase == "movement"
    assert s.human_placed == 12
    assert s.computer_placed == 12
    assert s.player == "computer"  # Computer placed second, moves first!

    # Case B: Computer places first -> Human must move first in Phase 2
    s_comp = game.initial_state("computer")
    assert s_comp.first_placer == "computer"
    for m in all_non_center:
        s_comp = game.apply(s_comp, m)

    assert s_comp.phase == "movement"
    assert s_comp.player == "human"  # Human placed second, moves first!


def test_seega_single_and_multi_capture():
    game = SeegaGame()
    # Construct a movement state
    # Target: move piece to (2, 2)
    # Opponents at: (2, 1) and (1, 2)
    # Friendly anchors at: (2, 0) and (0, 2)
    # After moving to (2, 2), both (2, 1) and (1, 2) should be captured!
    board = [[None for _ in range(5)] for _ in range(5)]
    board[2][3] = "computer"  # The piece that will move to (2, 2)
    board[2][1] = "human"     # Opponent 1
    board[2][0] = "computer"  # Friendly anchor 1
    board[1][2] = "human"     # Opponent 2
    board[0][2] = "computer"  # Friendly anchor 2

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="computer",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=0,
        human_pieces=2,
        computer_pieces=3,
    )

    next_state = game.apply(state, ((2, 3), (2, 2)))
    # Both opponents captured!
    assert next_state.board[2][1] is None
    assert next_state.board[1][2] is None
    assert next_state.board[2][2] == "computer"
    assert next_state.last_capture_count == 2
    assert next_state.last_captor == "computer"
    assert "Computer captured 2 pieces!" in game.last_capture_message(next_state)
    assert next_state.no_capture_counter == 0
    assert next_state.human_pieces == 0  # Both human pieces eliminated


def test_seega_center_piece_immune_from_capture():
    game = SeegaGame()
    # Opponent stands on center square (2, 2)
    # Friendly pieces at (2, 1) and (2, 3) (sandwiching center)
    # Piece moves into (2, 3)
    board = [[None for _ in range(5)] for _ in range(5)]
    board[2][4] = "computer"  # Moves to (2, 3)
    board[2][2] = "human"     # Opponent on center
    board[2][1] = "computer"  # Friendly piece

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="computer",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=0,
        human_pieces=1,
        computer_pieces=2,
    )

    next_state = game.apply(state, ((2, 4), (2, 3)))
    # Center piece must NOT be captured!
    assert next_state.board[2][2] == "human"
    assert next_state.last_capture_count == 0


def test_seega_safe_move_between_two_enemies():
    game = SeegaGame()
    # Enemies at (2, 1) and (2, 3).
    # Friendly piece moves to (2, 2) between them.
    # Moving into a sandwich does NOT capture self!
    board = [[None for _ in range(5)] for _ in range(5)]
    board[1][2] = "computer"  # Moves to (2, 2)
    board[2][1] = "human"     # Opponent 1
    board[2][3] = "human"     # Opponent 2

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="computer",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=0,
        human_pieces=2,
        computer_pieces=1,
    )

    next_state = game.apply(state, ((1, 2), (2, 2)))
    assert next_state.board[2][2] == "computer"
    assert next_state.last_capture_count == 0
    assert next_state.computer_pieces == 1


def test_seega_pass_and_blocked():
    game = SeegaGame()
    # Construct state where current player (human) has NO legal moves
    # Human piece surrounded completely by computer pieces
    board = [[None for _ in range(5)] for _ in range(5)]
    board[0][0] = "human"
    board[0][1] = "computer"
    board[1][0] = "computer"
    # Computer piece has an open move
    board[4][4] = "computer"

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="human",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=5,
        human_pieces=1,
        computer_pieces=3,
    )

    assert game.legal_moves(state) == []  # Blocked!
    # Applying pass
    next_state = game.apply(state, None)
    assert next_state.player == "computer"
    assert next_state.no_capture_counter == 6


def test_seega_40_move_rule():
    game = SeegaGame()
    board = [[None for _ in range(5)] for _ in range(5)]
    board[0][0] = "human"
    board[4][4] = "computer"

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="human",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=40,
        human_pieces=2,
        computer_pieces=1,
    )

    assert game.is_terminal(state)
    assert game.winner(state) == "human"  # Human had more pieces

    # Draw if equal pieces
    state_draw = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="human",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=40,
        human_pieces=2,
        computer_pieces=2,
    )
    assert game.is_terminal(state_draw)
    assert game.winner(state_draw) == "draw"


def test_seega_search_pass_consumes_depth():
    game = SeegaGame()
    # State where human is blocked, passes to computer
    board = [[None for _ in range(5)] for _ in range(5)]
    board[0][0] = "human"
    board[0][1] = "computer"
    board[1][0] = "computer"
    board[4][3] = "computer"

    state = SeegaState(
        board=tuple(tuple(r) for r in board),
        phase="movement",
        player="human",
        first_placer="human",
        placed_this_turn=0,
        human_placed=12,
        computer_placed=12,
        no_capture_counter=0,
        human_pieces=1,
        computer_pieces=3,
    )

    # Human has no moves, search should continue with computer, consuming 1 depth
    res_mm = minimax(game, state, depth=2)
    res_ab = alphabeta(game, state, depth=2, use_ordering=False)
    assert res_mm.score == res_ab.score
    assert res_ab.nodes <= res_mm.nodes
