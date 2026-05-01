"""
search.py
---------
A* and Weighted A* search implementations for the 15-puzzle.

Both algorithms accept any admissible heuristic function with the
interface h(state) -> int. For Weighted A*, the effective heuristic
is w * h(state), where w >= 1. Setting w = 1 recovers standard A*.

The search returns a SearchResult namedtuple containing the solution
path, number of nodes expanded, and whether the solution is optimal.
"""

import heapq
from collections import namedtuple
from puzzle import GOAL_STATE, get_neighbors

SearchResult = namedtuple("SearchResult", [
    "path",           # list of states from start to goal (inclusive)
    "nodes_expanded", # number of states popped from the open list
    "solution_length",# number of moves in the solution
    "optimal",        # True if w == 1.0 (optimality guaranteed)
])


def astar(start, heuristic, weight=1.0):
    """
    Run (Weighted) A* search from start to the goal state.

    Args:
        start (tuple): Initial puzzle state of length 16.
        heuristic (callable): Admissible heuristic function h(state) -> int.
        weight (float): Heuristic weight. 1.0 gives standard A*.
            Values greater than 1.0 trade optimality for speed.
            The solution is guaranteed to be within a factor of weight
            of optimal (Likhachev et al., 2003).

    Returns:
        SearchResult: Named tuple with path, nodes_expanded, solution_length,
            and optimal flag. Returns None if the puzzle is unsolvable.

    Complexity:
        Time: O(b^d) in the worst case, where b is the branching factor
              and d is the solution depth. In practice much better with
              a tight heuristic.
        Space: O(b^d) for the open and closed sets.
    """
    if start == GOAL_STATE:
        return SearchResult(path=[start], nodes_expanded=0, solution_length=0, optimal=True)

    # open list entries: (f, g, state, parent_state)
    # Ties in f are broken by g (prefer deeper nodes)
    h0 = heuristic(start)
    open_list = [(weight * h0, 0, start, None)]
    heapq.heapify(open_list)

    # Maps state -> (g_value, parent_state)
    visited = {}
    nodes_expanded = 0

    while open_list:
        f, g, state, parent = heapq.heappop(open_list)

        if state in visited:
            continue

        visited[state] = (g, parent)
        nodes_expanded += 1

        if state == GOAL_STATE:
            path = _reconstruct_path(visited, state)
            return SearchResult(
                path=path,
                nodes_expanded=nodes_expanded,
                solution_length=len(path) - 1,
                optimal=(weight == 1.0),
            )

        for neighbor in get_neighbors(state):
            if neighbor not in visited:
                g_new = g + 1
                h_new = heuristic(neighbor)
                f_new = g_new + weight * h_new
                heapq.heappush(open_list, (f_new, g_new, neighbor, state))

    return None  # Unsolvable (should not occur if is_solvable() was checked)


def _reconstruct_path(visited, goal):
    """
    Reconstruct the solution path by following parent pointers.

    Args:
        visited (dict): Maps state -> (g_value, parent_state).
        goal (tuple): The goal state.

    Returns:
        list[tuple]: States from start to goal, inclusive.
    """
    path = []
    state = goal
    while state is not None:
        path.append(state)
        _, parent = visited[state]
        state = parent
    path.reverse()
    return path
