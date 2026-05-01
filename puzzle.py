"""
puzzle.py
---------
State representation, move generation, and solvability checking
for the 15-puzzle (4x4 sliding tile puzzle).

State encoding: a Python tuple of length 16.
  - Values 1-15 represent tiles.
  - Value 0 represents the blank tile.
  - Index 0 is top-left, index 15 is bottom-right.

Goal state: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)
"""

GOAL_STATE = tuple(list(range(1, 16)) + [0])
GRID_SIZE = 4

# Precompute goal positions for fast heuristic lookup
GOAL_POS = {tile: idx for idx, tile in enumerate(GOAL_STATE)}


def get_neighbors(state):
    """
    Return a list of successor states reachable by one legal move.

    A move slides a tile adjacent to the blank into the blank position.
    Equivalently, the blank moves up, down, left, or right.

    Args:
        state (tuple): Current puzzle state of length 16.

    Returns:
        list[tuple]: List of successor states.
    """
    blank = state.index(0)
    row, col = divmod(blank, GRID_SIZE)
    neighbors = []

    # (delta_row, delta_col) for each direction
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE:
            new_blank = new_row * GRID_SIZE + new_col
            lst = list(state)
            lst[blank], lst[new_blank] = lst[new_blank], lst[blank]
            neighbors.append(tuple(lst))

    return neighbors


def is_solvable(state):
    """
    Determine whether a puzzle configuration is reachable from the goal.

    A state is solvable if and only if:
        (parity of permutation) XOR (taxicab distance of blank from goal) is even.

    Args:
        state (tuple): Puzzle state of length 16.

    Returns:
        bool: True if the puzzle is solvable, False otherwise.
    """
    tiles = [t for t in state if t != 0]
    inversions = 0
    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i] > tiles[j]:
                inversions += 1

    blank_idx = state.index(0)
    blank_row = blank_idx // GRID_SIZE
    # Goal blank is at index 15, row 3
    blank_dist = abs(blank_row - 3)

    return (inversions + blank_dist) % 2 == 0


def generate_random_instance(depth, seed=None):
    """
    Generate a solvable puzzle instance by performing a random walk
    of the given number of steps from the goal state.

    Args:
        depth (int): Number of random moves to apply from the goal.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        tuple: A solvable puzzle state approximately 'depth' moves from the goal.
    """
    import random
    if seed is not None:
        random.seed(seed)

    state = GOAL_STATE
    prev = None
    for _ in range(depth):
        neighbors = get_neighbors(state)
        # Avoid immediately reversing the last move
        choices = [n for n in neighbors if n != prev]
        prev = state
        state = random.choice(choices)
    return state


def state_to_grid(state):
    """
    Convert a flat tuple state to a 4x4 list of lists for display.

    Args:
        state (tuple): Puzzle state of length 16.

    Returns:
        list[list[int]]: 4x4 grid representation.
    """
    return [list(state[i * GRID_SIZE:(i + 1) * GRID_SIZE]) for i in range(GRID_SIZE)]


def print_state(state):
    """Pretty-print a puzzle state to stdout."""
    grid = state_to_grid(state)
    for row in grid:
        print(" ".join(f"{v:2d}" if v != 0 else "  " for v in row))
    print()
