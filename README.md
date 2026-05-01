# CS 57200 — 15-Puzzle Heuristic Search
**Track B: Optimization and Heuristic Search**
**Final Project Submission — May 2026**

This repository contains the complete implementation for the CS 57200 final project.
The project systematically compares three admissible heuristics — Manhattan Distance,
Linear Conflict, and Pattern Database — under A* and Weighted A* search on the 15-puzzle.

---

## Project Structure

```
cs572_15puzzle_final/
│
├── puzzle.py               State representation, move generation, solvability check
├── heuristics.py           Manhattan distance (h1), Linear Conflict (h2),
│                           Pattern Database heuristic (h3)
├── search.py               A* and Weighted A* search (single unified implementation)
├── experiments.py          CLI benchmark runner — generates instances, runs search,
│                           saves CSV output
├── build_pdb.py            Standalone script to build & save a Pattern Database
├── analyze_results.py      Summarize and plot CSV benchmark output
├── requirements.txt        Python package dependencies
│
├── tests/
│   ├── test_puzzle.py      Unit tests for puzzle.py (14 tests)
│   ├── test_heuristics.py  Unit tests for heuristics.py (12 tests)
│   └── test_search.py      Unit tests for search.py (8 tests)
│
├── scripts/
│   ├── build_pdb_gilbreth.sh       SLURM batch job: build 8-tile PDB on Gilbreth
│   └── run_benchmark_gilbreth.sh   SLURM batch job: 1000-instance benchmark on Gilbreth
│
└── results/
    ├── preliminary/        CSV output from local benchmark runs
    └── gilbreth/           CSV output from Gilbreth cluster experiments
```

---

## Setup

Python 3.11 or later is required. No C extensions or non-standard system libraries needed.

```bash
git clone https://github.com/[your-username]/cs572-15puzzle.git
cd cs572-15puzzle
pip install -r requirements.txt
```

---

## Running Experiments

All experiments are driven by `experiments.py`. The `--heuristic` flag selects between
`md` (Manhattan Distance), `lc` (Linear Conflict), and `pdb` (Pattern Database).

### Experiment 1: Heuristic comparison by difficulty

```bash
# h1: Manhattan Distance, depth tier 20-29
python experiments.py --heuristic md --instances 50 --min_depth 20 --max_depth 29 \
    --seed 42 --output results/preliminary/h1_depth20_29.csv

# h2: Linear Conflict, same depth tier
python experiments.py --heuristic lc --instances 50 --min_depth 20 --max_depth 29 \
    --seed 42 --output results/preliminary/h2_depth20_29.csv

# Repeat for depth tiers 30-39 and 40-50
python experiments.py --heuristic md --instances 50 --min_depth 40 --max_depth 50 \
    --seed 42 --output results/preliminary/h1_depth40_50.csv

python experiments.py --heuristic lc --instances 50 --min_depth 40 --max_depth 50 \
    --seed 42 --output results/preliminary/h2_depth40_50.csv
```

### Experiment 2: Pattern Database

Build a 6-tile PDB for local testing (~3 minutes, ~800 MB RAM):

```bash
python build_pdb.py --tiles 1 2 3 4 5 6 --output results/pdb_6tile.pkl
```

Then benchmark it:

```bash
python experiments.py --heuristic pdb --pdb_path results/pdb_6tile.pkl \
    --instances 50 --min_depth 40 --max_depth 50 \
    --seed 42 --output results/preliminary/h3_pdb6_depth40_50.csv
```

For the 8-tile PDB , use `--tiles 1 2 3 4 5 6 7 8`.

### Experiment 3: Weighted A*

```bash
# Standard A* (w=1.0, optimal)
python experiments.py --heuristic lc --weight 1.0 --instances 50 \
    --min_depth 40 --max_depth 50 --seed 42 \
    --output results/preliminary/h2_w1.0.csv

# Weighted A* at various weights
for W in 1.2 1.5 2.0 3.0; do
    python experiments.py --heuristic lc --weight $W --instances 50 \
        --min_depth 40 --max_depth 50 --seed 42 \
        --output results/preliminary/h2_w${W}.csv
done
```

---

## Analyzing Results

```bash
# Summarize all CSV files in results/
python analyze_results.py

# Compare two specific CSVs and generate a bar chart
python analyze_results.py \
    --input results/preliminary/h1_depth40_50.csv results/preliminary/h2_depth40_50.csv \
    --labels "h1: Manhattan" "h2: Linear Conflict" \
    --plot results/preliminary/comparison.png
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected: 34 tests collected, all passing.

---

## Building the 8-Tile Pattern Database (Gilbreth Cluster)

The 8-tile PDB requires ~4 GB RAM and ~6 hours of compute.
```bash
# From the Gilbreth login node, with this repo cloned:
sbatch scripts/build_pdb_gilbreth.sh
```

The output is saved to `results/gilbreth/pdb_8tile.pkl`. After building, run the
large-scale 1000-instance benchmark:

```bash
sbatch scripts/run_benchmark_gilbreth.sh
```

---

## Heuristic Summary

| Heuristic              | Admissible | Consistent | Per-node Cost | Notes                                            |
|------------------------|------------|------------|---------------|--------------------------------------------------|
| Manhattan Distance (h1)| Yes        | Yes        | O(1)          | Baseline; ignores tile interactions              |
| Linear Conflict (h2)   | Yes        | Yes        | O(1)          | Adds 2-move penalty per conflict pair; dominates h1 |
| Pattern Database (h3)  | Yes        | Yes        | O(1) lookup   | Requires offline BFS precomputation              |

### Key experimental results (depth 40-50, 50 instances, seed=42)

| Heuristic              | Mean Nodes | Node Reduction vs h1 | Mean Runtime (ms) |
|------------------------|------------|----------------------|-------------------|
| h1: Manhattan Distance | 149,002    | —                    | 3,241             |
| h2: Linear Conflict    | 30,509     | 80%                  | 1,067             |
| h3: PDB (6-tile, local)| 3,847      | 97%                  | 198               |
| h3: PDB (8-tile, cluster)| 412      | 99.7%                | 31                |

### Weighted A* (h2, depth 40-50)

| Weight (w) | Mean Nodes | Speedup vs w=1.0 | Mean Sol. Length | Suboptimality |
|------------|------------|------------------|------------------|---------------|
| 1.0        | 30,509     | 1.0x             | 32.5             | 1.00x         |
| 1.2        | 6,390      | 4.8x             | 32.9             | 1.01x         |
| 1.5        | 2,265      | 13.5x            | 34.1             | 1.05x         |
| 2.0        | 1,135      | 26.9x            | 36.8             | 1.13x         |
| 3.0        | 930        | 32.8x            | 42.0             | 1.29x         |

---

## Reproducibility

All experiments use a fixed `--seed` (default 42). Instance sets are generated
deterministically via random walks from the goal state. Results can be exactly
reproduced by running `experiments.py` with the same `--seed`, `--instances`,
`--min_depth`, and `--max_depth` arguments.

---

## References

Culberson, J. C., and Schaeffer, J. (1998). Pattern databases. *Computational Intelligence*, 14(3), 318-334.

Felner, A., Korf, R. E., and Hanan, S. (2004). Additive pattern database heuristics. *JAIR*, 22, 279-318.

Hansson, O., Mayer, A., and Yung, M. (1992). Criticizing solutions to relaxed models yields powerful admissible heuristics. *Information Sciences*, 63(3), 207-227.

Hart, P. E., Nilsson, N. J., and Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. *IEEE Transactions on Systems Science and Cybernetics*, 4(2), 100-107.

Korf, R. E. (1985). Depth-first iterative-deepening: An optimal admissible tree search. *Artificial Intelligence*, 27(1), 97-109.

Korf, R. E., and Felner, A. (2002). Disjoint pattern database heuristics. *Artificial Intelligence*, 134(1-2), 9-22.

Likhachev, M., Gordon, G., and Thrun, S. (2003). ARA*: Anytime A* with provable bounds on sub-optimality. *NIPS 2003*.

Pearl, J. (1984). *Heuristics: Intelligent Search Strategies for Computer Problem Solving*. Addison-Wesley.

Russell, S., and Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
