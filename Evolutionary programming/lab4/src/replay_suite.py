"""Replay the saved input suite and display measured branch coverage."""
import argparse
import json
from pathlib import Path
from instrumentation import Subject

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--suite',type=Path,default=ROOT/'results/best_suite.json')
    args=parser.parse_args()
    saved=json.loads(args.suite.read_text())
    subject=Subject(ROOT/'data/target_program.py')
    covered=set()
    for row in saved['suite']:
        execution=subject.execute(tuple(row['genome']))
        covered |= execution.covered
        selector,*arguments=execution.genome
        print(f"{subject.functions[selector]}{tuple(arguments)} -> {execution.output}; {', '.join(sorted(execution.covered))}")
    print(f'Coverage: {len(covered)}/{len(subject.goals)} ({len(covered)/len(subject.goals):.2%})')
    if covered != set(saved['covered']):
        raise RuntimeError('Replayed coverage differs from the saved archive')


if __name__=='__main__':
    main()
