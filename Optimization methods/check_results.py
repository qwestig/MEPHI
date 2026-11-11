"""Recheck saved numerical plans using NumPy; this entry point never imports a solver."""
from pathlib import Path
import csv,json,copy
import numpy as np
from src import verify

ROOT=Path(__file__).resolve().parent
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def run():
    results=[]
    def record(name,check):
        if not check['passed']: raise AssertionError(f'{name}: {check}')
        results.append(dict(plan=name,**check))
    for name in ['base','deficit','stress']:
        d=read(ROOT/f'results/lab1/scenarios/{name}.json')
        x=[float(r['loan_million']) for r in rows(ROOT/f'results/lab1/solution_{name}.csv')]
        rec=read(ROOT/'results/lab1/results.json')['solutions'][name]
        record('lab1/'+name,verify.credit(d,x,-rec['objective']))
    for name in ['base','overload','failure']:
        d=read(ROOT/f'results/lab2/scenarios/{name}.json')
        f=np.zeros((3,4,4));iw=np.zeros((3,4));ir=np.zeros((4,4))
        for r in rows(ROOT/f'results/lab2/solution_{name}.csv'):
            f[int(r['warehouse'][1:])-1,int(r['store'][1:])-1,int(r['period'])-1]=float(r['flow'])
        for r in rows(ROOT/f'results/lab2/inventory_{name}.csv'):
            (iw if r['node'][0]=='W' else ir)[int(r['node'][1:])-1,int(r['period'])-1]=float(r['inventory'])
        obj=read(ROOT/'results/lab2/results.json')['solutions'][name]['objective']
        record('lab2/'+name,verify.network(d,f,iw,ir,obj))
    for name in ['growth','stress']:
        d=read(ROOT/f'results/lab2/scenarios/{name}.json');p=read(ROOT/f'results/lab2/elastic_plan_{name}.json')
        d['demand']=(np.array(d['demand'])-p['unmet']).tolist()
        record('lab2/elastic_'+name,verify.network(d,p['flow'],p['wh_inventory'],p['store_inventory']))
    for name in ['base','deficit','stress']:
        d=read(ROOT/f'results/lab3/scenarios/{name}.json');q=np.zeros((5,4,3));z=np.zeros((5,3))
        for r in rows(ROOT/f'results/lab3/solution_{name}.csv'):
            i=int(r['supplier'][1:])-1;k=int(r['tier'])-1;z[i,k]=float(r['selected'])
            for j in range(4):q[i,j,k]=float(r[f'G{j+1}'])
        obj=read(ROOT/'results/lab3/results.json')['solutions'][name]['objective']
        record('lab3/'+name,verify.purchasing(d,q,z,obj))
    d=read(ROOT/'data/lab3.json');p=read(ROOT/'results/lab3/lp_plan.json')
    record('lab3/lp',verify.purchasing(d,p['q'],p['z'],integral=False))
    for n in [5,10,20,40]:
        d=read(ROOT/f'results/lab3/benchmark_data/n{n}.json')
        for form in ['strong','weak']:
            for mode in ['lp','milp']:
                p=read(ROOT/f'results/lab3/benchmark_solutions/n{n}_{form}_{mode}.json')
                record(f'lab3/benchmark/{n}/{form}/{mode}',verify.purchasing(d,p['q'],p['z'],integral=mode=='milp',formulation=form))
    d=read(ROOT/'data/lab2.json');p=read(ROOT/'results/lab2/greedy.json')
    record('lab2/greedy',verify.network(d,p['flow'],p['wh_inventory'],p['store_inventory']))
    d=read(ROOT/'data/lab3.json');p=read(ROOT/'results/lab3/greedy.json')
    record('lab3/greedy',verify.purchasing(d,p['q'],p['z']))
    # Deliberately corrupt each kind of plan. A verifier that always says yes must fail this audit.
    d=read(ROOT/'data/lab1.json');assert not verify.credit(d,np.full(6,1000.))['passed']
    d=read(ROOT/'data/lab2.json');p=read(ROOT/'results/lab2/greedy.json');f=np.array(p['flow']);f[0,0,0]+=.001
    assert not verify.network(d,f,p['wh_inventory'],p['store_inventory'])['passed']
    d=read(ROOT/'data/lab3.json');p=read(ROOT/'results/lab3/greedy.json');z=np.array(p['z']);i,k=np.argwhere(z>.5)[0];z[i,k]=.5
    assert not verify.purchasing(d,p['q'],z)['passed']
    summary=dict(passed=True,plans_checked=len(results),mutation_checks_passed=3,checks=results)
    (ROOT/'results'/'independent_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(results)} saved plans; 3 intentionally invalid plans rejected; tolerance 1e-7.')
    return summary

if __name__=='__main__':run()
