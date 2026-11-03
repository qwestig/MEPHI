"""Reproducible comparison with an exhaustively known Pareto front."""
import argparse
import csv
import json
import math
from pathlib import Path
import platform
import statistics
from time import perf_counter

from problem import Problem
from optimizer import Recorder, hypervolume, nondominated, nsga2, random_search, weighted_ga

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT/'configs/experiment.json')
    parser.add_argument('--output', type=Path, default=ROOT/'results')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    problem = Problem(json.loads((ROOT/'data/catalogue.json').read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    exact = nondominated(problem.objectives.items())
    exact_objectives = {v for _, v in exact}
    exact_norm = [problem.normalize(v) for _, v in exact]
    exact_hv = hypervolume(exact_norm, cfg['hypervolume_reference'])
    reference = dict(total_configurations=len(problem.genomes), front_size=len(exact), hypervolume=exact_hv,
                     ideal=problem.ideal, nadir=problem.nadir,
                     solutions=[dict(genome=g, objectives=v) for g, v in exact])
    (args.output/'reference_front.json').write_text(json.dumps(reference, indent=2)+'\n')
    all_runs, all_trajectory, saved_fronts, summaries = [], [], [], []
    for method, algorithm in [('nsga2', nsga2), ('weighted_sum', weighted_ga), ('random_search', random_search)]:
        method_runs = []
        for run in range(cfg['runs']):
            seed = cfg['base_seed']+run
            record = Recorder(problem, cfg['evaluation_budget'], cfg['hypervolume_reference'])
            started = perf_counter()
            algorithm(problem, cfg, seed, record)
            front = nondominated(record.seen.items())
            normalized = [problem.normalize(v) for _, v in front]
            hv = hypervolume(normalized, cfg['hypervolume_reference'])
            igd = statistics.fmean(min(math.dist(p, q) for q in normalized) for p in exact_norm)
            row = dict(method=method, run=run+1, seed=seed, evaluations=record.count,
                       hypervolume=hv, hv_ratio=hv/exact_hv, igd=igd,
                       exact_recall=len({v for _, v in front}&exact_objectives)/len(exact),
                       archive_size=len(front), unique_evaluated=len(record.seen), seconds=perf_counter()-started)
            if record.count != cfg['evaluation_budget']:
                raise RuntimeError('Evaluation budget mismatch')
            all_runs.append(row)
            method_runs.append(row)
            all_trajectory.extend(dict(method=method, run=run+1, evaluations=n, hypervolume=v, archive_size=s)
                                  for n, v, s in record.history)
            saved_fronts.extend(dict(method=method, run=run+1, seed=seed, genome=g, objectives=v) for g, v in front)
        summary = dict(method=method, runs=len(method_runs))
        for key in ['hv_ratio', 'igd', 'exact_recall', 'archive_size', 'seconds']:
            values = [r[key] for r in method_runs]
            summary.update({f'{key}_mean': statistics.fmean(values), f'{key}_median': statistics.median(values),
                            f'{key}_std': statistics.stdev(values), f'{key}_min': min(values), f'{key}_max': max(values)})
        summaries.append(summary)
        print(f"{method}: HV={summary['hv_ratio_mean']:.4%}, recall={summary['exact_recall_mean']:.2%}, "
              f"IGD={summary['igd_mean']:.5f}", flush=True)
    write_csv(args.output/'runs.csv', all_runs)
    write_csv(args.output/'summary.csv', summaries)
    write_csv(args.output/'trajectories.csv', all_trajectory)
    (args.output/'fronts.json').write_text(json.dumps(saved_fronts, indent=2)+'\n')
    (args.output/'experiment_snapshot.json').write_text(json.dumps(dict(config=cfg, catalogue=problem.data,
                    python=platform.python_version()), indent=2)+'\n')


if __name__ == '__main__':
    main()
