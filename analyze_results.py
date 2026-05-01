"""
analyze_results.py
------------------
Summarize and visualize benchmark CSV files produced by experiments.py.

Usage:
    # Summarize a single CSV:
    python analyze_results.py --input results/preliminary/results.csv

    # Compare multiple CSVs side by side:
    python analyze_results.py \
        --input results/preliminary/h1_depth20_29.csv \
                results/preliminary/h2_depth20_29.csv \
        --labels "h1: Manhattan" "h2: Linear Conflict" \
        --plot results/preliminary/comparison.png

    # Full comparison table across three heuristics (all depth tiers):
    python analyze_results.py --summary_table
"""

import argparse
import csv
import os
import statistics


def load_csv(filepath):
    """Load a benchmark CSV and return list of dicts."""
    rows = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "instance_id": int(row["instance_id"]),
                "walk_depth": int(row["walk_depth"]),
                "nodes_expanded": int(row["nodes_expanded"]),
                "solution_length": int(row["solution_length"]),
                "runtime_ms": float(row["runtime_ms"]),
                "optimal": row["optimal"].strip().lower() == "true",
            })
    return rows


def summarize(rows, label=""):
    """Print and return summary statistics for a result set."""
    nodes = [r["nodes_expanded"] for r in rows]
    times = [r["runtime_ms"] for r in rows]
    lengths = [r["solution_length"] for r in rows]

    n = len(rows)
    if n == 0:
        print(f"{label}: No data")
        return {}

    stats = {
        "label": label,
        "n": n,
        "nodes_mean": statistics.mean(nodes),
        "nodes_sd": statistics.stdev(nodes) if n > 1 else 0,
        "runtime_mean": statistics.mean(times),
        "runtime_sd": statistics.stdev(times) if n > 1 else 0,
        "length_mean": statistics.mean(lengths),
        "length_sd": statistics.stdev(lengths) if n > 1 else 0,
    }

    print(f"\n{'='*60}")
    print(f"  {label}  (n={n})")
    print(f"{'='*60}")
    print(f"  Nodes expanded:   mean={stats['nodes_mean']:,.0f}  sd={stats['nodes_sd']:,.0f}")
    print(f"  Solution length:  mean={stats['length_mean']:.1f}  sd={stats['length_sd']:.1f}")
    print(f"  Runtime (ms):     mean={stats['runtime_mean']:.1f}  sd={stats['runtime_sd']:.1f}")
    return stats


def plot_comparison(datasets, labels, output_path):
    """
    Plot a grouped bar chart comparing mean nodes expanded.
    Requires matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib/numpy not available; skipping plot.")
        return

    means = [statistics.mean([r["nodes_expanded"] for r in d]) for d in datasets]
    sds = [statistics.stdev([r["nodes_expanded"] for r in d]) if len(d) > 1 else 0
           for d in datasets]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(x, means, yerr=sds, capsize=5,
                  color=["#4C9ED9", "#3DBB7E", "#E8854B"][:len(labels)],
                  edgecolor="white", linewidth=0.8)

    ax.set_yscale("log")
    ax.set_ylabel("Mean Nodes Expanded (log scale)", fontsize=12)
    ax.set_title("Heuristic Comparison: Mean Nodes Expanded", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.yaxis.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.1,
                f"{mean:,.0f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    plt.savefig(output_path, dpi=150)
    print(f"  Plot saved to {output_path}")
    plt.close()


def weighted_astar_suboptimality_table(filepath):
    """Print suboptimality analysis for Weighted A* results."""
    if not os.path.exists(filepath):
        return
    rows = load_csv(filepath)
    optimal_len = statistics.mean([r["solution_length"] for r in rows if r["optimal"]])
    print(f"\nWeighted A* suboptimality relative to optimal length {optimal_len:.1f}:")
    by_weight = {}
    for r in rows:
        # weight info is not stored in CSV; use this for single-weight files
        by_weight.setdefault("from_file", []).append(r["solution_length"])
    for w, lengths in by_weight.items():
        print(f"  mean solution length: {statistics.mean(lengths):.1f} "
              f"(ratio vs optimal: {statistics.mean(lengths)/optimal_len:.3f})")


def main():
    parser = argparse.ArgumentParser(description="Analyze 15-puzzle benchmark results")
    parser.add_argument("--input", nargs="+", default=[], help="CSV file(s) to summarize")
    parser.add_argument("--labels", nargs="+", default=[], help="Labels for each CSV file")
    parser.add_argument("--plot", type=str, default=None, help="Output path for comparison plot")
    args = parser.parse_args()

    if not args.input:
        # Auto-discover CSVs in results/
        for root, _, files in os.walk("results"):
            for fname in sorted(files):
                if fname.endswith(".csv"):
                    path = os.path.join(root, fname)
                    rows = load_csv(path)
                    summarize(rows, label=fname)
        return

    datasets = []
    labels = args.labels if args.labels else [os.path.basename(p) for p in args.input]

    for path, label in zip(args.input, labels):
        rows = load_csv(path)
        summarize(rows, label=label)
        datasets.append(rows)

    if args.plot and datasets:
        plot_comparison(datasets, labels, args.plot)


if __name__ == "__main__":
    main()
