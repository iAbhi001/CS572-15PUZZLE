"""
tests/test_puzzle.py
--------------------
Unit tests for puzzle.py: state representation, move generation,
solvability checking, and instance generation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from puzzle import (
    GOAL_STATE, get_neighbors, is_solvable,
    generate_random_instance, state_to_grid
)


class TestGoalState:
    def test_goal_state_length(self):
        assert len(GOAL_STATE) == 16

    def test_goal_state_values(self):
        assert set(GOAL_STATE) == set(range(16))

    def test_goal_state_blank_position(self):
        assert GOAL_STATE[-1] == 0


class TestGetNeighbors:
    def test_goal_state_has_two_neighbors(self):
        # Blank is at index 15 (bottom-right corner), can only move up or left
        neighbors = get_neighbors(GOAL_STATE)
        assert len(neighbors) == 2

    def test_center_blank_has_four_neighbors(self):
        # Move blank to index 5 (row 1, col 1)
        state = list(GOAL_STATE)
        blank = state.index(0)
        state[blank], state[5] = state[5], state[blank]
        neighbors = get_neighbors(tuple(state))
        assert len(neighbors) == 4

    def test_neighbor_differs_by_one_move(self):
        for neighbor in get_neighbors(GOAL_STATE):
            diffs = sum(1 for a, b in zip(GOAL_STATE, neighbor) if a != b)
            assert diffs == 2  # blank and one tile swap

    def test_neighbors_are_valid_states(self):
        for neighbor in get_neighbors(GOAL_STATE):
            assert len(neighbor) == 16
            assert set(neighbor) == set(range(16))

    def test_top_left_blank_has_two_neighbors(self):
        state = list(GOAL_STATE)
        blank = state.index(0)
        state[blank], state[0] = state[0], state[blank]
        neighbors = get_neighbors(tuple(state))
        assert len(neighbors) == 2

    def test_edge_blank_has_three_neighbors(self):
        # Index 1 (top row, col 1): up is off-grid, three directions valid
        state = list(GOAL_STATE)
        blank = state.index(0)
        state[blank], state[1] = state[1], state[blank]
        neighbors = get_neighbors(tuple(state))
        assert len(neighbors) == 3


class TestIsSolvable:
    def test_goal_is_solvable(self):
        assert is_solvable(GOAL_STATE) is True

    def test_one_move_from_goal_is_solvable(self):
        for neighbor in get_neighbors(GOAL_STATE):
            assert is_solvable(neighbor) is True

    def test_swap_two_adjacent_tiles_is_unsolvable(self):
        # Swapping tiles 1 and 2 (indices 0 and 1) changes parity
        state = list(GOAL_STATE)
        state[0], state[1] = state[1], state[0]
        assert is_solvable(tuple(state)) is False

    def test_known_solvable_instance(self):
        # Classic textbook solvable instance
        state = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 14, 0)
        assert is_solvable(state) is False  # 15 and 14 swapped = unsolvable

    def test_random_walk_instances_are_solvable(self):
        for depth in [10, 20, 30]:
            state = generate_random_instance(depth, seed=depth)
            assert is_solvable(state) is True


class TestGenerateRandomInstance:
    def test_returns_valid_state(self):
        state = generate_random_instance(20, seed=1)
        assert len(state) == 16
        assert set(state) == set(range(16))

    def test_reproducible_with_seed(self):
        s1 = generate_random_instance(25, seed=99)
        s2 = generate_random_instance(25, seed=99)
        assert s1 == s2

    def test_different_seeds_give_different_states(self):
        s1 = generate_random_instance(25, seed=1)
        s2 = generate_random_instance(25, seed=2)
        assert s1 != s2

    def test_zero_depth_returns_goal(self):
        state = generate_random_instance(0)
        assert state == GOAL_STATE


class TestStateToGrid:
    def test_grid_shape(self):
        grid = state_to_grid(GOAL_STATE)
        assert len(grid) == 4
        assert all(len(row) == 4 for row in grid)

    def test_grid_values_match_state(self):
        grid = state_to_grid(GOAL_STATE)
        flat = [v for row in grid for v in row]
        assert tuple(flat) == GOAL_STATE
