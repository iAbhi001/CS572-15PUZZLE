"""
experiments.py
--------------
Benchmark runner for comparing heuristic search strategies on the 15-puzzle.

Usage:
    python experiments.py --heuristic md --instances 50 --min_depth 20 --max_depth 50
    python experiments.py --heuristic lc --instances 50 --min_depth 40 --max_depth 50
    python experiments.py --heuristic md --weight 1.5 --instances 50

Arguments:
    --heuristic   : md (Manhattan distance), lc (Linear Conflict), pdb (Pattern DB)
    --weight      : Heuristic weight for Weighted A* (default 1.0)
    --instances   : Number of puzzle instances to generate (default 50)
    --min_depth   : Minimum random walk depth for instance generation (default 20)
    --max_depth   : Maximum random walk depth for instance generation (default 50)
    --pdb_path    : Path to saved pattern database file (required if --heuristic pdb)
    --seed        : Base random seed for reproducibility (default 42)
    --output      : Output CSV file path (default results/preliminary/results.csv)
"""

import argparse
import csv
import os
import random
import time

from puzzle import generate_random_instance, is_solvable
from heuristics import manhattan_distance, linear_conflict, PatternDatabaseHeuristic
from search import astar


def run_benchmark(heuristic_fn, weight, instances, min_depth, max_depth, base_seed):
    """
    Run a benchmark of (Weighted) A* with the given heuristic on a set of
    randomly generated puzzle instances.

    Args:
        heuristic_fn (callable): Heuristic function h(state) -> int.
        weight (float): Search weight. 1.0 for optimal A*.
        instances (int): Number of puzzle instances to test.
        min_depth (int): Minimum walk depth for instance generation.
        max_depth (int): Maximum walk depth for instance generation.
        base_seed (int): Base seed for reproducibility.

    Returns:
        list[dict]: One result dictionary per instance with keys:
            instance_id, depth, nodes_expanded, solution_length,
            runtime_ms, optimal.
    """
    results = []
    rng = random.Random(base_seed)

    for i in range(instances):
        depth = rng.randint(min_depth, max_depth)
        seed = rng.randint(0, 10**9)
        state = generate_random_instance(depth, seed=seed)

        if not is_solvable(state):
            # Should not occur given generate_random_instance, but guard anyway
            continue

        start_time = time.perf_counter()
        result = astar(state, heuristic_fn, weight=weight)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if result is None:
            print(f"  Warning: instance {i} returned None (unsolvable?)")
            continue

        results.append({
            "instance_id": i,
            "walk_depth": depth,
            "nodes_expanded": result.nodes_expanded,
            "solution_length": result.solution_length,
            "runtime_ms": round(elapsed_ms, 2),
            "optimal": result.optimal,
        })

        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{instances} instances...")

    return results


def summarize(results):
    """Print mean and standard deviation for key metrics."""
    import statistics
    nodes = [r["nodes_expanded"] for r in results]
    times = [r["runtime_ms"] for r in results]
    lengths = [r["solution_length"] for r in results]
    print(f"  Instances:        {len(results)}")
    print(f"  Nodes expanded:   mean={statistics.mean(nodes):.0f}, sd={statistics.stdev(nodes):.0f}")
    print(f"  Solution length:  mean={statistics.mean(lengths):.1f}, sd={statistics.stdev(lengths):.1f}")
    print(f"  Runtime (ms):     mean={statistics.mean(times):.1f}, sd={statistics.stdev(times):.1f}")


def save_csv(results, filepath):
    """Save benchmark results to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = ["instance_id", "walk_depth", "nodes_expanded", "solution_length", "runtime_ms", "optimal"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"  Results saved to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="15-puzzle heuristic benchmark runner")
    parser.add_argument("--heuristic", choices=["md", "lc", "pdb"], default="md",
                        help="Heuristic to use: md, lc, or pdb")
    parser.add_argument("--weight", type=float, default=1.0,
                        help="A* heuristic weight (default 1.0)")
    parser.add_argument("--instances", type=int, default=50,
                        help="Number of instances to test (default 50)")
    parser.add_argument("--min_depth", type=int, default=20,
                        help="Minimum walk depth for instance generation (default 20)")
    parser.add_argument("--max_depth", type=int, default=50,
                        help="Maximum walk depth for instance generation (default 50)")
    parser.add_argument("--pdb_path", type=str, default=None,
                        help="Path to saved PDB file (required if --heuristic pdb)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Base random seed (default 42)")
    parser.add_argument("--output", type=str, default="results/preliminary/results.csv",
                        help="Output CSV path")
    args = parser.parse_args()

    # Select heuristic
    if args.heuristic == "md":
        h = manhattan_distance
        label = "Manhattan Distance"
    elif args.heuristic == "lc":
        h = linear_conflict
        label = "Linear Conflict"
    elif args.heuristic == "pdb":
        if args.pdb_path is None:
            parser.error("--pdb_path is required when using --heuristic pdb")
        h = PatternDatabaseHeuristic.load(args.pdb_path)
        label = f"Pattern Database ({args.pdb_path})"
    else:
        raise ValueError(f"Unknown heuristic: {args.heuristic}")

    print(f"Running benchmark: {label}, weight={args.weight}")
    print(f"  Instances: {args.instances}, depth range: [{args.min_depth}, {args.max_depth}]")
    print(f"  Seed: {args.seed}")

    results = run_benchmark(h, args.weight, args.instances, args.min_depth, args.max_depth, args.seed)
    summarize(results)
    save_csv(results, args.output)


if __name__ == "__main__":
    main()
