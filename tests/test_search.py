"""
tests/test_search.py
--------------------
Unit tests for search.py: A* and Weighted A* correctness.

Tests verify that A* returns optimal solutions on known instances,
that all returned paths are valid (consecutive states differ by one move),
and that Weighted A* solutions are within the expected suboptimality bound.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from puzzle import GOAL_STATE, get_neighbors, generate_random_instance, is_solvable
from heuristics import manhattan_distance, linear_conflict
from search import astar


def path_is_valid(path):
    """Check that every consecutive pair in a path differs by exactly one move."""
    for i in range(len(path) - 1):
        neighbors = get_neighbors(path[i])
        if path[i + 1] not in neighbors:
            return False
    return True


class TestAStarBaseline:
    def test_already_solved(self):
        result = astar(GOAL_STATE, manhattan_distance)
        assert result is not None
        assert result.solution_length == 0
        assert result.path == [GOAL_STATE]

    def test_one_move_solution(self):
        neighbor = get_neighbors(GOAL_STATE)[0]
        result = astar(neighbor, manhattan_distance)
        assert result is not None
        assert result.solution_length == 1
        assert result.path[-1] == GOAL_STATE

    def test_path_ends_at_goal(self):
        state = generate_random_instance(20, seed=1)
        result = astar(state, manhattan_distance)
        assert result.path[-1] == GOAL_STATE

    def test_path_starts_at_start(self):
        state = generate_random_instance(20, seed=2)
        result = astar(state, manhattan_distance)
        assert result.path[0] == state

    def test_path_is_valid(self):
        state = generate_random_instance(20, seed=3)
        result = astar(state, manhattan_distance)
        assert path_is_valid(result.path)

    def test_optimal_flag_set(self):
        state = generate_random_instance(15, seed=4)
        result = astar(state, manhattan_distance, weight=1.0)
        assert result.optimal is True


class TestAStarWithLinearConflict:
    def test_same_solution_length_as_md(self):
        """Both heuristics should find the same optimal solution length."""
        for seed in range(5):
            state = generate_random_instance(20, seed=seed)
            r_md = astar(state, manhattan_distance)
            r_lc = astar(state, linear_conflict)
            assert r_md.solution_length == r_lc.solution_length

    def test_lc_expands_fewer_nodes(self):
        """Linear Conflict should expand no more nodes than Manhattan Distance."""
        wins = 0
        for seed in range(10):
            state = generate_random_instance(30, seed=seed)
            r_md = astar(state, manhattan_distance)
            r_lc = astar(state, linear_conflict)
            if r_lc.nodes_expanded <= r_md.nodes_expanded:
                wins += 1
        # Should win on the vast majority of instances
        assert wins >= 8

    def test_path_valid_with_lc(self):
        state = generate_random_instance(25, seed=5)
        result = astar(state, linear_conflict)
        assert path_is_valid(result.path)


class TestWeightedAStar:
    def test_weighted_solution_within_bound(self):
        """Weighted A* solution must be <= w * optimal length."""
        state = generate_random_instance(30, seed=10)
        optimal = astar(state, manhattan_distance, weight=1.0)
        for w in [1.2, 1.5, 2.0]:
            result = astar(state, manhattan_distance, weight=w)
            assert result.solution_length <= w * optimal.solution_length + 1  # +1 for rounding

    def test_weighted_optimal_flag_false(self):
        state = generate_random_instance(20, seed=6)
        result = astar(state, manhattan_distance, weight=1.5)
        assert result.optimal is False

    def test_weight_one_is_optimal(self):
        state = generate_random_instance(20, seed=7)
        result = astar(state, manhattan_distance, weight=1.0)
        assert result.optimal is True

    def test_higher_weight_fewer_nodes(self):
        state = generate_random_instance(35, seed=8)
        r1 = astar(state, manhattan_distance, weight=1.0)
        r2 = astar(state, manhattan_distance, weight=2.0)
        assert r2.nodes_expanded <= r1.nodes_expanded
