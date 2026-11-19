"""Comprehensive test suite verifying Minimax vs Alpha-Beta equivalence across 100+ positions per game."""
from __future__ import annotations

import random
import pytest

from engine.games.xo import XOGame
from engine.games.connect4 import Connect4Game
from engine.games.seega import SeegaGame
from engine.search import minimax, alphabeta
from engine.benchmark import _sample_midgame_states


@pytest.mark.parametrize("depth", [2, 3])
def test_search_equivalence_xo_100_positions(depth: int):
    """Verify alphabeta score == minimax score and move == minimax move on 100 positions in XO."""
    game = XOGame()
    states = _sample_midgame_states(game, n_positions=100, seed=123)

    for state in states:
        res_mm = minimax(game, state, depth)
        res_ab = alphabeta(game, state, depth, use_ordering=False)

        assert res_ab.score == res_mm.score, f"Scores differed: AB={res_ab.score}, MM={res_mm.score}"
        assert res_ab.move == res_mm.move, f"Moves differed: AB={res_ab.move}, MM={res_mm.move}"
        assert res_ab.nodes <= res_mm.nodes, f"Pruning failed to reduce or match nodes: AB={res_ab.nodes}, MM={res_mm.nodes}"


def test_search_equivalence_connect4_100_positions():
    """Verify alphabeta score == minimax score and move == minimax move on 100 positions in Connect 4."""
    game = Connect4Game()
    states = _sample_midgame_states(game, n_positions=100, seed=456)

    for state in states:
        res_mm = minimax(game, state, depth=2)
        res_ab = alphabeta(game, state, depth=2, use_ordering=False)

        assert res_ab.score == res_mm.score, f"Scores differed: AB={res_ab.score}, MM={res_mm.score}"
        assert res_ab.move == res_mm.move, f"Moves differed: AB={res_ab.move}, MM={res_mm.move}"
        assert res_ab.nodes <= res_mm.nodes, f"Pruning failed to reduce nodes: AB={res_ab.nodes}, MM={res_mm.nodes}"


def test_search_equivalence_seega_100_positions():
    """Verify alphabeta score == minimax score and move == minimax move on 100 positions in Seega."""
    game = SeegaGame()
    states = _sample_midgame_states(game, n_positions=100, seed=789)

    for state in states:
        res_mm = minimax(game, state, depth=2)
        res_ab = alphabeta(game, state, depth=2, use_ordering=False)

        assert res_ab.score == res_mm.score, f"Scores differed: AB={res_ab.score}, MM={res_mm.score}"
        assert res_ab.move == res_mm.move, f"Moves differed: AB={res_ab.move}, MM={res_mm.move}"
        assert res_ab.nodes <= res_mm.nodes, f"Pruning failed to reduce nodes: AB={res_ab.nodes}, MM={res_mm.nodes}"
