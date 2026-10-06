"""Run reproducible GA and random-search experiments for lab 1."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics

from optimizer import GAParameters, GeneticAlgorithm, random_search, salomon


def summary(values: list[float]) -> dict[str, float]:
    return {
        "best": min(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "worst": max(values),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)

    dimension = config["dimension"]
    lower, upper = config["lower_bound"], config["upper_bound"]
    budget, runs, base_seed = config["evaluation_budget"], config["runs"], config["base_seed"]
    result_rows: list[dict] = []
    trajectory_rows: list[dict] = []

    methods = [("random_search", None)] + [(item["name"], item) for item in config["configurations"]]
    for method_index, (method, method_config) in enumerate(methods):
        results = []
        for run in range(runs):
            seed = base_seed + method_index * 10_000 + run
            if method_config is None:
                result = random_search(salomon, dimension, lower, upper, budget, seed)
            else:
                params = GAParameters(
                    population_size=method_config["population_size"], evaluation_budget=budget,
                    crossover_probability=method_config["crossover_probability"],
                    mutation_probability=method_config["mutation_probability"],
                    mutation_sigma=method_config["mutation_sigma"],
                    tournament_size=config["tournament_size"], elitism=config["elitism"],
                )
                result = GeneticAlgorithm(salomon, dimension, lower, upper, params, seed).run()
            results.append(result)
            result_rows.append({
                "method": method, "run": run + 1, "seed": seed, "best_value": result.best_value,
                "best_vector": json.dumps(result.best_vector), "evaluations": result.evaluations,
                "generations": result.generations,
            })
            for step, value in enumerate(result.history):
                trajectory_rows.append({"method": method, "run": run + 1, "step": step, "best_value": value})

        stats = summary([item.best_value for item in results])
        print(f"{method}: best={stats['best']:.6g}, mean={stats['mean']:.6g}, median={stats['median']:.6g}, std={stats['std']:.6g}")

    write_csv(args.output / "runs.csv", list(result_rows[0]), result_rows)
    write_csv(args.output / "trajectories.csv", list(trajectory_rows[0]), trajectory_rows)
    grouped = {}
    for row in result_rows:
        grouped.setdefault(row["method"], []).append(float(row["best_value"]))
    summary_rows = [{"method": method, **summary(values)} for method, values in grouped.items()]
    write_csv(args.output / "summary.csv", list(summary_rows[0]), summary_rows)


if __name__ == "__main__":
    main()
