"""
tests/test_heuristics.py
------------------------
Unit tests for heuristics.py: Manhattan distance and Linear Conflict.

Tests verify admissibility (h never exceeds true cost on known instances),
consistency (h decreases by at most 1 per step), and correctness of
conflict detection.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from puzzle import GOAL_STATE, get_neighbors, generate_random_instance
from heuristics import manhattan_distance, linear_conflict


class TestManhattanDistance:
    def test_goal_state_is_zero(self):
        assert manhattan_distance(GOAL_STATE) == 0

    def test_one_move_from_goal_is_one(self):
        for neighbor in get_neighbors(GOAL_STATE):
            assert manhattan_distance(neighbor) == 1

    def test_nonnegative(self):
        for depth in [10, 20, 30, 40]:
            state = generate_random_instance(depth, seed=depth)
            assert manhattan_distance(state) >= 0

    def test_known_value(self):
        # Swap tiles 1 and 2 only (indices 0 and 1): each moves 1 step, MD = 2
        state = (2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)
        assert manhattan_distance(state) == 2

    def test_consistent_across_neighbors(self):
        state = generate_random_instance(30, seed=7)
        h_state = manhattan_distance(state)
        for neighbor in get_neighbors(state):
            h_neighbor = manhattan_distance(neighbor)
            # Consistency: h(s) <= cost(s, s') + h(s') = 1 + h(neighbor)
            assert h_state <= 1 + h_neighbor


class TestLinearConflict:
    def test_goal_state_is_zero(self):
        assert linear_conflict(GOAL_STATE) == 0

    def test_dominates_manhattan(self):
        for depth in [15, 25, 35]:
            state = generate_random_instance(depth, seed=depth)
            assert linear_conflict(state) >= manhattan_distance(state)

    def test_nonnegative(self):
        for depth in [10, 20, 30]:
            state = generate_random_instance(depth, seed=depth + 1)
            assert linear_conflict(state) >= 0

    def test_detects_row_conflict(self):
        # Tiles 1 and 2 in row 0, but swapped: goal says 1 at col 0, 2 at col 1
        # Place tile 2 at col 0 and tile 1 at col 1 => one conflict, penalty = 2
        # State: (2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)
        state = (2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)
        md = manhattan_distance(state)
        lc = linear_conflict(state)
        assert lc == md + 2

    def test_no_row_conflict_but_column_conflict(self):
        # Tile 1 (goal: row 0, col 0) is in row 1 => no ROW conflict.
        # But tile 5 (goal: row 1, col 0) and tile 1 share column 0 in wrong order
        # => one COLUMN conflict, penalty = +2.
        state = (5, 2, 3, 4, 1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)
        md = manhattan_distance(state)
        lc = linear_conflict(state)
        assert lc == md + 2

    def test_consistent_across_neighbors(self):
        state = generate_random_instance(30, seed=13)
        h_state = linear_conflict(state)
        for neighbor in get_neighbors(state):
            h_neighbor = linear_conflict(neighbor)
            assert h_state <= 1 + h_neighbor


class TestHeuristicOrdering:
    def test_lc_never_less_than_md(self):
        """Linear Conflict always dominates Manhattan Distance."""
        for seed in range(20):
            state = generate_random_instance(30, seed=seed)
            assert linear_conflict(state) >= manhattan_distance(state)
