"""Run from any directory: python main.py --generate. Results remain in this folder."""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'optimization_mpl_config'))
import argparse
import platform
import json
import numpy as np
import highspy
import matplotlib
from src.common import dump
from src.data import generate,load
from src import lab1,lab2,lab3

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--generate',action='store_true',help='Regenerate the documented synthetic variant data')
    p.add_argument('--repeats',type=int,default=3,help='Paired MILP timing repetitions (default 3)')
    args=p.parse_args(); root=Path(__file__).resolve().parent
    if args.repeats<1: p.error('--repeats must be positive')
    if args.generate: generate(root)
    dump(root/'results'/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),
        processor=platform.processor(),numpy=np.__version__,highs=highspy.Highs().version(),matplotlib=matplotlib.__version__,
        seed=10107,threads=1,lp_algorithm='dual/revised simplex (HiGHS simplex)',presolve='on',mip_rel_gap=0.,time_limit_seconds=30.))
    results=[]
    for k,mod in enumerate([lab1,lab2,lab3],1):
        print(f'Lab {k}: solving and independently checking...',flush=True)
        kw={'repeats':args.repeats} if k==3 else {}
        results.append(mod.run(load(root,f'lab{k}'),root/'results'/f'lab{k}',**kw))
    from check_results import run as audit_saved_plans
    audit_saved_plans()
    from src.reporting import reports
    reports(root,*results)
    print('Done: reports/ and results/. Every saved feasible solution passed the independent checks.',flush=True)

if __name__=='__main__': main()
