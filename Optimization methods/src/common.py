"""HiGHS interface and file helpers. All models minimize; verifiers never use HiGHS."""
from pathlib import Path
import csv
import json
import time
import numpy as np
import highspy

TOL = 1e-7
SEED = 10107

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False,
                               default=lambda v: v.item() if isinstance(v,np.generic) else v.tolist()), encoding='utf-8')

def csvout(path, rows):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with path.open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

class Model:
    def __init__(self):
        self.names, self.c, self.lb, self.ub, self.integer = [], [], [], [], []
        self.rows, self.lo, self.hi, self.rnames = [], [], [], []

    def var(self, name, cost=0., lower=0., upper=np.inf, integer=False):
        j = len(self.c)
        self.names.append(name)
        self.c.append(float(cost)); self.lb.append(float(lower)); self.ub.append(float(upper))
        self.integer.append(bool(integer))
        return j

    def row(self, terms, lower=-np.inf, upper=np.inf, name=''):
        self.rows.append(dict(terms)); self.lo.append(float(lower)); self.hi.append(float(upper))
        self.rnames.append(name or f'r{len(self.rows)}')

    def solve(self, log, relax=False, method='simplex', time_limit=30.):
        log = Path(log); log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists(): log.unlink()
        h = highspy.Highs()
        options = dict(output_flag=True, log_to_console=False, log_file=str(log),
                       presolve='on', threads=1, random_seed=SEED, time_limit=time_limit,
                       primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-9,
                       mip_feasibility_tolerance=1e-9, mip_rel_gap=0.,simplex_strategy=1)
        if relax or not any(self.integer): options['solver'] = method
        for k,v in options.items():
            if h.setOptionValue(k,v) != highspy.HighsStatus.kOk:
                raise RuntimeError(f'HiGHS rejected option {k}={v}')
        lp = highspy.HighsLp()
        lp.num_col_, lp.num_row_ = len(self.c), len(self.rows)
        lp.col_cost_, lp.col_lower_, lp.col_upper_ = self.c, self.lb, self.ub
        lp.row_lower_, lp.row_upper_ = self.lo, self.hi
        lp.col_names_, lp.row_names_ = self.names, self.rnames
        start, index, value = [0], [], []
        for row in self.rows:
            for j, v in sorted(row.items()):
                if v: index.append(j); value.append(v)
            start.append(len(index))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = start, index, value
        if any(self.integer) and not relax:
            lp.integrality_ = [highspy.HighsVarType.kInteger if b else highspy.HighsVarType.kContinuous for b in self.integer]
        if h.passModel(lp) != highspy.HighsStatus.kOk: raise RuntimeError('Model rejected')
        t = time.perf_counter(); run_status = h.run(); seconds = time.perf_counter()-t
        if run_status == highspy.HighsStatus.kError: raise RuntimeError('HiGHS error; see '+str(log))
        status = h.modelStatusToString(h.getModelStatus())
        info, sol = h.getInfo(), h.getSolution()
        valid = bool(sol.value_valid) and info.primal_solution_status == highspy.SolutionStatus.kSolutionStatusFeasible
        result = dict(status=status, seconds=seconds, variables=len(self.c), constraints=len(self.rows),
                      simplex_iterations=int(info.simplex_iteration_count), ipm_iterations=int(info.ipm_iteration_count),
                      nodes=int(info.mip_node_count) if any(self.integer) and not relax else 0,
                      objective=float(info.objective_function_value) if valid else None,
                      x=list(sol.col_value) if valid else None,
                      row_dual=list(sol.row_dual) if sol.dual_valid else None,
                      col_dual=list(sol.col_dual) if sol.dual_valid else None,
                      mip_gap=float(info.mip_gap) if valid and any(self.integer) and not relax else None,
                      dual_bound=float(info.mip_dual_bound) if valid and any(self.integer) and not relax else None)
        return result

def require_optimal(r):
    if r['status'] != 'Optimal': raise RuntimeError(f"Expected optimum, obtained {r['status']}")

def mdtable(rows, digits=5):
    if not rows: return ''
    fields = list(rows[0])
    def fmt(x):
        if isinstance(x, (float,np.floating)): return f'{x:.{digits}g}'
        return str(x)
    return '\n'.join(['| '+' | '.join(fields)+' |', '| '+' | '.join(['---']*len(fields))+' |']+
                     ['| '+' | '.join(fmt(r[k]) for k in fields)+' |' for r in rows])

def write_md(path, text):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip()+'\n', encoding='utf-8')
