"""Run the full factorial experiment; save raw data and audited solutions."""

import argparse
import csv
from dataclasses import fields
import json
from pathlib import Path
import statistics

from optimizer import Parameters, genetic_algorithm, random_search
from problem import Problem

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiment.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["runs"] < 20:
        raise ValueError("The lab requires at least 20 independent runs per configuration")
    instance_path = args.config.resolve().parent.parent / config["instance"]
    problem = Problem.load(instance_path)
    args.output.mkdir(parents=True, exist_ok=True)
    common = {field.name: config[field.name] for field in fields(Parameters) if field.name in config}
    runs, trajectories, summaries, solutions = [], [], [], {}
    methods = [{"name": "random_feasible", "constraints": "repair", "mutation": "swap"}] + config["configurations"]
    for method in methods:
        params = Parameters(**common, **{key: method[key] for key in ("constraints", "mutation")})
        method_runs = []
        for run in range(config["runs"]):
            seed = config["base_seed"] + run
            result = (random_search if method["name"] == "random_feasible" else genetic_algorithm)(problem, params, seed)
            checked = problem.evaluate(result.chromosome)  # Audit outside the search budget.
            assert checked.feasible and abs(checked.distance - result.distance) < 1e-9
            assert result.evaluations == config["evaluation_budget"]
            row = {"method": method["name"], "run": run + 1, "seed": seed,
                   "distance": result.distance, "evaluations": result.evaluations,
                   "generations": result.generations, "feasible_evaluations": result.feasible_evaluations,
                   "feasible_fraction": result.feasible_evaluations / result.evaluations,
                   "final_feasible_fraction": result.final_feasible_fraction, "seconds": result.seconds,
                   "chromosome": json.dumps(result.chromosome), "loads": json.dumps(checked.loads)}
            runs.append(row)
            method_runs.append(row)
            trajectories.extend({"method": method["name"], "run": run + 1, "evaluations": count,
                                 "best_feasible_distance": distance} for count, distance in result.history)
            if method["name"] not in solutions or result.distance < solutions[method["name"]]["distance"]:
                solutions[method["name"]] = {"run": run + 1, "seed": seed, "distance": result.distance,
                                             "chromosome": result.chromosome,
                                             "routes": problem.decode(result.chromosome), "loads": checked.loads}
        values = [row["distance"] for row in method_runs]
        summary = {"method": method["name"], "runs": len(values), "best": min(values),
                   "mean": statistics.fmean(values), "median": statistics.median(values),
                   "std": statistics.stdev(values), "worst": max(values),
                   "mean_feasible_fraction": statistics.fmean(row["feasible_fraction"] for row in method_runs),
                   "mean_final_feasible_fraction": statistics.fmean(row["final_feasible_fraction"] for row in method_runs),
                   "mean_seconds": statistics.fmean(row["seconds"] for row in method_runs)}
        summaries.append(summary)
        print(f"{method['name']}: mean={summary['mean']:.3f}, best={summary['best']:.3f}, "
              f"feasible={summary['mean_feasible_fraction']:.1%}", flush=True)
    write_csv(args.output / "runs.csv", runs)
    write_csv(args.output / "trajectories.csv", trajectories)
    write_csv(args.output / "summary.csv", summaries)
    (args.output / "best_solutions.json").write_text(json.dumps(solutions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "experiment_snapshot.json").write_text(json.dumps({"config": config, "instance": problem.data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
