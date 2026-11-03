"""Measure 30 runs per algorithm and export executable branch witnesses."""
import argparse
import ast
import csv
import itertools
import json
from pathlib import Path
import platform
import statistics
from time import perf_counter

from instrumentation import Subject
from optimizer import Recorder, genetic_search, random_search

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
    source = ROOT/'data/target_program.py'
    subject = Subject(source)
    args.output.mkdir(parents=True, exist_ok=True)
    constants = {-100, 0, 100}
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, (ast.Constant, ast.UnaryOp)):
            try:
                value = ast.literal_eval(node)
                if type(value) is int and -100 <= value <= 100:
                    constants.add(value)
            except (ValueError, TypeError):
                pass
    constants = sorted(constants)
    # A calibration grid establishes reachability, never seeds search populations.
    witnesses, calibration_evaluations = {}, 0
    for selector in range(len(subject.functions)):
        for arguments in itertools.product(cfg['calibration_grid'], repeat=3):
            execution = subject.execute((selector, *arguments))
            calibration_evaluations += 1
            for goal in execution.covered:
                witnesses.setdefault(goal, execution.genome)
    if set(witnesses) != set(subject.goals):
        raise RuntimeError(f'Calibration misses branches: {set(subject.goals)-set(witnesses)}')
    (args.output/'branch_map.json').write_text(json.dumps(dict(metadata=subject.metadata, goals=subject.goals,
              witnesses=witnesses, calibration_evaluations=calibration_evaluations), indent=2)+'\n')
    runs, trajectories, summaries, suites = [], [], [], []
    for method in ['random_search', 'coverage_ga', 'directed_ga']:
        method_rows = []
        for run in range(cfg['runs']):
            seed = cfg['base_seed']+run
            record = Recorder(subject, cfg['evaluation_budget'], track_distances=method == 'directed_ga')
            start = perf_counter()
            if method == 'random_search':
                random_search(subject, cfg, seed, record, constants)
            else:
                genetic_search(subject, cfg, seed, record, constants, directed=method == 'directed_ga')
            seconds = perf_counter()-start
            suite = record.minimized_suite()
            replayed = set()
            for item in suite:
                execution = subject.execute(item['genome'])
                if execution.covered != set(item['covers']):
                    raise RuntimeError('Witness replay differs from measured trace')
                replayed |= execution.covered
            if replayed != set(record.archive) or record.count != cfg['evaluation_budget']:
                raise RuntimeError('Coverage archive or evaluation budget mismatch')
            row = dict(method=method, run=run+1, seed=seed, evaluations=record.count,
                       covered=len(record.archive), total=len(subject.goals), coverage=len(record.archive)/len(subject.goals),
                       suite_size=len(suite), first_full_evaluation=record.first_full or '', seconds=seconds)
            runs.append(row)
            method_rows.append(row)
            trajectories.extend(dict(method=method, run=run+1, evaluations=n, covered=c, total=len(subject.goals))
                                for n, c in record.history)
            suites.append(dict(method=method, run=run+1, seed=seed, covered=sorted(record.archive),
                               missing=sorted(set(subject.goals)-set(record.archive)), suite=suite))
        summary = dict(method=method, runs=len(method_rows),
                       full_runs=sum(row['covered'] == len(subject.goals) for row in method_rows))
        for key in ['coverage', 'suite_size', 'seconds']:
            values = [row[key] for row in method_rows]
            summary.update({key+'_mean': statistics.fmean(values), key+'_median': statistics.median(values),
                            key+'_std': statistics.stdev(values), key+'_min': min(values), key+'_max': max(values)})
        completed = [row['first_full_evaluation'] for row in method_rows if row['first_full_evaluation'] != '']
        summary['first_full_median_conditional'] = statistics.median(completed) if completed else ''
        summaries.append(summary)
        print(f"{method}: coverage={summary['coverage_mean']:.2%}, full={summary['full_runs']}/30", flush=True)
    write_csv(args.output/'runs.csv', runs)
    write_csv(args.output/'summary.csv', summaries)
    write_csv(args.output/'trajectories.csv', trajectories)
    branch_rates = [dict(method=method, branch=goal, covered_runs=sum(goal in s['covered'] for s in suites if s['method'] == method))
                    for method in ['random_search', 'coverage_ga', 'directed_ga'] for goal in subject.goals]
    write_csv(args.output/'branch_rates.csv', branch_rates)
    (args.output/'suites.json').write_text(json.dumps(suites, indent=2)+'\n')
    (args.output/'experiment_snapshot.json').write_text(json.dumps(dict(config=cfg, python=platform.python_version(),
                       mutation_constants=constants, source=source.read_text()), indent=2)+'\n')


if __name__ == '__main__':
    main()
