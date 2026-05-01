"""
heuristics.py
-------------
Admissible heuristic functions for the 15-puzzle.

All heuristics share the same interface:
    h(state) -> int

where state is a tuple of length 16 and the return value is a
non-negative integer representing the estimated cost to the goal.

Implemented heuristics:
    manhattan_distance  (h1) - sum of per-tile taxicab distances
    linear_conflict     (h2) - Manhattan distance + linear conflict penalty
    pdb_lookup          (h3) - pattern database lookup (requires prebuilt table)
"""

from puzzle import GOAL_POS, GRID_SIZE


# ---------------------------------------------------------------------------
# h1: Manhattan Distance
# ---------------------------------------------------------------------------

def manhattan_distance(state):
    """
    Compute the Manhattan distance heuristic for a given puzzle state.

    For each non-blank tile, sum the horizontal and vertical distances
    between its current position and its goal position. This heuristic
    is admissible and consistent.

    Admissibility: each tile requires at least its Manhattan distance
    moves to reach its goal, and tiles cannot share positions, so no
    move can reduce the total Manhattan distance by more than 1.

    Args:
        state (tuple): Puzzle state of length 16.

    Returns:
        int: Sum of Manhattan distances for all non-blank tiles.
    """
    total = 0
    for idx, tile in enumerate(state):
        if tile == 0:
            continue
        goal_idx = GOAL_POS[tile]
        cur_row, cur_col = divmod(idx, GRID_SIZE)
        goal_row, goal_col = divmod(goal_idx, GRID_SIZE)
        total += abs(cur_row - goal_row) + abs(cur_col - goal_col)
    return total


# ---------------------------------------------------------------------------
# h2: Linear Conflict
# ---------------------------------------------------------------------------

def _count_conflicts_in_line(tiles_in_line, goal_positions_in_line):
    """
    Count the number of linear conflict pairs in a single row or column.

    Two tiles t_a and t_b are in linear conflict if:
      - Both tiles are in their goal row/column.
      - The goal position of t_a is to the left/above t_b's goal position.
      - t_a currently sits to the right/below t_b.

    Args:
        tiles_in_line (list[int]): Tile values currently in this row/column,
            filtered to only those whose goal is also in this row/column.
        goal_positions_in_line (list[int]): Corresponding goal positions
            (column index for rows, row index for columns).

    Returns:
        int: Number of conflicting pairs (each costs 2 extra moves).
    """
    conflicts = 0
    n = len(tiles_in_line)
    for i in range(n):
        for j in range(i + 1, n):
            # tiles_in_line[i] appears before tiles_in_line[j] currently
            # but goal of i is after goal of j => conflict
            if goal_positions_in_line[i] > goal_positions_in_line[j]:
                conflicts += 1
    return conflicts


def linear_conflict(state):
    """
    Compute the Linear Conflict heuristic for a given puzzle state.

    Returns Manhattan distance plus 2 for each linear conflict pair
    found across all rows and columns. This heuristic is admissible
    and strictly dominates Manhattan distance.

    Admissibility proof sketch: each identified conflict pair requires
    at least one tile to exit the row or column and re-enter, adding
    a minimum of 2 moves. These extra moves are not counted by Manhattan
    distance (which only tracks displacement within the row/column) and
    are non-overlapping between distinct conflict pairs in the same line.

    Args:
        state (tuple): Puzzle state of length 16.

    Returns:
        int: Manhattan distance + 2 * (number of linear conflict pairs).
    """
    h = manhattan_distance(state)
    penalty = 0

    # Check rows
    for row in range(GRID_SIZE):
        tiles_and_goals = []
        for col in range(GRID_SIZE):
            idx = row * GRID_SIZE + col
            tile = state[idx]
            if tile == 0:
                continue
            goal_idx = GOAL_POS[tile]
            goal_row = goal_idx // GRID_SIZE
            if goal_row == row:
                goal_col = goal_idx % GRID_SIZE
                tiles_and_goals.append(goal_col)
        # tiles_and_goals holds goal columns of tiles currently in their goal row
        # in left-to-right order of current position
        for i in range(len(tiles_and_goals)):
            for j in range(i + 1, len(tiles_and_goals)):
                if tiles_and_goals[i] > tiles_and_goals[j]:
                    penalty += 1

    # Check columns
    for col in range(GRID_SIZE):
        tiles_and_goals = []
        for row in range(GRID_SIZE):
            idx = row * GRID_SIZE + col
            tile = state[idx]
            if tile == 0:
                continue
            goal_idx = GOAL_POS[tile]
            goal_col = goal_idx % GRID_SIZE
            if goal_col == col:
                goal_row = goal_idx // GRID_SIZE
                tiles_and_goals.append(goal_row)
        for i in range(len(tiles_and_goals)):
            for j in range(i + 1, len(tiles_and_goals)):
                if tiles_and_goals[i] > tiles_and_goals[j]:
                    penalty += 1

    return h + 2 * penalty


# ---------------------------------------------------------------------------
# h3: Pattern Database Lookup
# ---------------------------------------------------------------------------

class PatternDatabaseHeuristic:
    """
    Heuristic based on a precomputed pattern database.

    The pattern database stores the exact number of moves required to
    place a selected subset of tiles correctly, ignoring all other tiles.
    Because it solves a relaxed subproblem exactly, it is admissible by
    construction (Culberson & Schaeffer, 1998).

    Attributes:
        pattern_tiles (tuple): The subset of tile values included in the PDB.
        table (dict): Maps encoded subconfiguration to exact cost.
    """

    def __init__(self, pattern_tiles, table=None):
        """
        Initialize the PDB heuristic.

        Args:
            pattern_tiles (tuple): Tile values to include in the pattern.
            table (dict, optional): Prebuilt lookup table. If None, the
                database must be built by calling build().
        """
        self.pattern_tiles = set(pattern_tiles)
        self.table = table if table is not None else {}

    def _encode(self, state):
        """
        Encode the positions of pattern tiles as a hashable key.

        Args:
            state (tuple): Full puzzle state.

        Returns:
            tuple: Positions of each pattern tile in sorted tile-value order.
        """
        return tuple(state.index(t) for t in sorted(self.pattern_tiles))

    def build(self):
        """
        Build the pattern database via backward BFS from the goal state.

        This explores all states reachable by moving only the pattern tiles
        (treating all other tiles as wildcards that can pass through each
        other). The result is stored in self.table.

        Note: For an 8-tile pattern on the 15-puzzle, this BFS can take
        several hours and requires several GB of RAM. It is intended to be
        run on a computing cluster and the result saved to disk.
        """
        from collections import deque
        from puzzle import GOAL_STATE, get_neighbors

        goal_key = self._encode(GOAL_STATE)
        self.table = {goal_key: 0}
        queue = deque([(GOAL_STATE, 0)])

        while queue:
            state, cost = queue.popleft()
            for neighbor in get_neighbors(state):
                key = self._encode(neighbor)
                if key not in self.table:
                    self.table[key] = cost + 1
                    queue.append((neighbor, cost + 1))

    def save(self, filepath):
        """Save the pattern database table to disk using pickle."""
        import pickle
        with open(filepath, "wb") as f:
            pickle.dump({"pattern_tiles": list(self.pattern_tiles), "table": self.table}, f)

    @classmethod
    def load(cls, filepath):
        """Load a previously saved pattern database from disk."""
        import pickle
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        return cls(tuple(data["pattern_tiles"]), table=data["table"])

    def __call__(self, state):
        """
        Look up the heuristic value for a given state.

        Falls back to 0 if the key is not in the table (should not happen
        for a complete database, but provides a safe default).

        Args:
            state (tuple): Puzzle state of length 16.

        Returns:
            int: Exact cost to place pattern tiles correctly from this state.
        """
        key = self._encode(state)
        return self.table.get(key, 0)
