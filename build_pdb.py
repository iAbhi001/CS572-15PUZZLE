"""
build_pdb.py
------------
Standalone script to build and save a Pattern Database for the 15-puzzle.

Usage:
    # Build a small 5-tile PDB for local testing (under 1 minute):
    python build_pdb.py --tiles 1 2 3 4 5 --output results/pdb_5tile.pkl

    # Build a 6-tile PDB for moderate experiments (~3 min, ~800 MB RAM):
    python build_pdb.py --tiles 1 2 3 4 5 6 --output results/pdb_6tile.pkl

    # Build the full 8-tile PDB for Gilbreth cluster (~6 hours, ~4 GB RAM):
    python build_pdb.py --tiles 1 2 3 4 5 6 7 8 --output results/pdb_8tile.pkl

Notes:
    - The 8-tile PDB is intended to be run as a SLURM batch job on Gilbreth.
      See scripts/build_pdb_gilbreth.sh for the SLURM submission script.
    - Memory scales roughly as O(16 * 15 * ... * (17 - n)) bytes for n tiles.
    - The saved .pkl file can be loaded by PatternDatabaseHeuristic.load().
"""

import argparse
import os
import time

from heuristics import PatternDatabaseHeuristic


def main():
    parser = argparse.ArgumentParser(description="Build and save a 15-puzzle Pattern Database")
    parser.add_argument(
        "--tiles", type=int, nargs="+", required=True,
        help="Tile values to include in the pattern (e.g. --tiles 1 2 3 4 5 6)"
    )
    parser.add_argument(
        "--output", type=str, default="results/pdb.pkl",
        help="Output path for the saved PDB file (default: results/pdb.pkl)"
    )
    args = parser.parse_args()

    tiles = tuple(sorted(args.tiles))
    n = len(tiles)

    print(f"Building {n}-tile Pattern Database for tiles: {tiles}")
    print(f"Output: {args.output}")

    # Estimate memory (rough upper bound)
    from math import factorial, perm
    states = perm(16, n)
    est_mb = (states * 1) / (1024 ** 2)  # 1 byte per state in compact encoding
    print(f"Estimated states: {states:,} (~{est_mb:.0f} MB in compact form)")

    start = time.perf_counter()
    pdb = PatternDatabaseHeuristic(pattern_tiles=tiles)
    pdb.build()
    elapsed = time.perf_counter() - start

    print(f"Build complete in {elapsed:.1f}s. Table size: {len(pdb.table):,} entries.")

    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    pdb.save(args.output)
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
