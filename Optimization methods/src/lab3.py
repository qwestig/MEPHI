from pathlib import Path
from copy import deepcopy
import time
import numpy as np
from .common import Model,dump,csvout,require_optimal
from . import verify
from .data import lab3_data

def build(d, formulation='strong'):
    m=Model(); n=len(d['capacity']); q=np.empty((n,4,3),dtype=int); z=np.empty((n,3),dtype=int)
    for i,k in np.ndindex(n,3): z[i,k]=m.var(f'z_{i+1}_{k+1}',d['fixed'][i],upper=1,integer=True)
    for i,j,k in np.ndindex(n,4,3): q[i,j,k]=m.var(f'q_{i+1}_{j+1}_{k+1}',d['price'][i][j]*(1-d['discount'][k]))
    for j in range(4): m.row({int(q[i,j,k]):1 for i in range(n) for k in range(3)},
                              lower=d['demand'][j],upper=d['demand'][j],name=f'demand_{j+1}')
    for i in range(n):
        m.row({int(z[i,k]):1 for k in range(3)},upper=1,name=f'one_tier_{i+1}')
        m.row({int(q[i,j,k]):1 for j,k in np.ndindex(4,3)},upper=d['capacity'][i],name=f'capacity_{i+1}')
        for k in range(3):
            low=d['thresholds'][k]; up=min([30.,60.,np.inf][k],d['capacity'][i])
            row={int(q[i,j,k]):1 for j in range(4)}
            m.row({**row,int(z[i,k]):-low},lower=0,name=f'tier_lower_{i+1}_{k+1}')
            if formulation=='strong':
                m.row({**row,int(z[i,k]):-up},upper=0,name=f'tier_upper_{i+1}_{k+1}')
                for j in range(4):
                    m.row({int(q[i,j,k]):1,int(z[i,k]):-min(d['demand'][j],up)},upper=0,name=f'product_link_{i+1}_{j+1}_{k+1}')
            else:
                # Unconditional U is retained: integer feasible sets remain equivalent.
                m.row(row,upper=up,name=f'unconditional_tier_upper_{i+1}_{k+1}')
                m.row({**row,int(z[i,k]):-d['big_m']},upper=0,name=f'loose_link_{i+1}_{k+1}')
    return m,(q,z)

def unpack(x,ix):
    x=np.asarray(x); return x[ix[0]],x[ix[1]]

def greedy(d):
    t=time.perf_counter(); n=len(d['capacity']); need=np.array(d['demand'],float)
    q=np.zeros((n,4,3)); z=np.zeros((n,3)); unused=set(range(n))
    while need.sum()>1e-7 and unused:
        choices=[]
        for i in sorted(unused):
            amount=min(d['capacity'][i],need.sum())
            if amount<=1e-9: continue
            take=np.zeros(4); left=amount
            for j in np.argsort(d['price'][i],kind='stable'):
                take[j]=min(need[j],left); left-=take[j]
            vol=take.sum()
            k=max(k for k in range(3) if d['thresholds'][k]<=vol+1e-9)
            cost=(take@np.array(d['price'][i]))*(1-d['discount'][k])+d['fixed'][i]
            choices.append((cost/vol,i,k,take))
        if not choices: break
        _,i,k,take=min(choices,key=lambda a:(a[0],a[1]))
        q[i,:,k]=take; z[i,k]=1; need-=take; unused.remove(i)
    check=verify.purchasing(d,q,z)
    return dict(q=q.tolist(),z=z.tolist(),check=check,seconds=time.perf_counter()-t)

def run(d,out,repeats=3):
    out=Path(out); results={}; checks={}; scenarios=[]
    m,ix=build(d); r=m.solve(out/'logs'/'base.log'); require_optimal(r)
    q,z=unpack(r['x'],ix); chosen=[d['suppliers'][i] for i in range(len(z)) if z[i].sum()>.5]
    largest=int(np.argmax(q.sum(axis=(1,2))))
    cases={name:deepcopy(d) for name in ['base','deficit','stress']}
    cases['deficit']['capacity'][largest]*=.8
    cases['stress']['capacity'][largest]=0.
    cases['stress']['demand']=(np.array(d['demand'])*1.2).tolist()
    for name,data in cases.items():
        model,idx=build(data); result=r if name=='base' else model.solve(out/'logs'/f'{name}.log')
        require_optimal(result); results[name]=result
        aq,az=unpack(result['x'],idx)
        check=verify.purchasing(data,aq,az,result['objective']); assert check['passed']; checks[name]=check
        rows=[dict(supplier=data['suppliers'][i],tier=k+1,selected=az[i,k],volume=aq[i,:,k].sum(),
                   **{data['goods'][j]:aq[i,j,k] for j in range(4)}) for i,k in np.ndindex(len(az),3)]
        csvout(out/f'solution_{name}.csv',rows); dump(out/'scenarios'/f'{name}.json',data)
        scenarios.append(dict(scenario=name,status=result['status'],cost=result['objective'],
                               suppliers='; '.join(data['suppliers'][i] for i in range(len(az)) if az[i].sum()>.5),
                               tiers='; '.join(f'{data["suppliers"][i]}:T{k+1}' for i,k in np.ndindex(az.shape) if az[i,k]>.5),
                               mip_gap=result['mip_gap'],seconds=result['seconds']))
    lp=m.solve(out/'logs'/'base_lp.log',relax=True); require_optimal(lp)
    lq,lz=unpack(lp['x'],ix)
    lc=verify.purchasing(d,lq,lz,lp['objective'],integral=False); assert lc['passed']
    csvout(out/'solution_lp.csv',[dict(supplier=d['suppliers'][i],tier=k+1,z=lz[i,k],volume=lq[i,:,k].sum()) for i,k in np.ndindex(lz.shape)])
    dump(out/'lp_plan.json',dict(q=lq,z=lz,check=lc))
    fractional=[dict(supplier=d['suppliers'][i],tier=k+1,z=lz[i,k],volume=lq[i,:,k].sum()) for i,k in np.ndindex(lz.shape) if abs(lz[i,k]-round(lz[i,k]))>1e-7]
    g=greedy(d); assert g['check']['passed']
    g['gap_percent']=100*(g['check']['objective_recomputed']-r['objective'])/r['objective']
    dump(out/'greedy.json',g)
    csvout(out/'greedy_solution.csv',[dict(supplier=d['suppliers'][i],tier=k+1,z=g['z'][i][k],
                  **{d['goods'][j]:g['q'][i][j][k] for j in range(4)}) for i,k in np.ndindex(len(z),3)])
    # Star 6: paired instances, explicit LP bounds, independently checked incumbents.
    raw=[]; summary=[]
    for n in [5,10,20,40]:
        dd=deepcopy(d) if n==5 else lab3_data(n)
        dump(out/'benchmark_data'/f'n{n}.json',dd)
        for formulation in ['strong','weak']:
            model,idx=build(dd,formulation)
            lr=model.solve(out/'logs'/f'bench_{n}_{formulation}_lp.log',relax=True)
            require_optimal(lr)
            lqq,lzz=unpack(lr['x'],idx)
            lcheck=verify.purchasing(dd,lqq,lzz,lr['objective'],integral=False,formulation=formulation)
            assert lcheck['passed']
            dump(out/'benchmark_solutions'/f'n{n}_{formulation}_lp.json',dict(q=lqq,z=lzz,check=lcheck))
            mr=[]
            for rep in range(repeats):
                rr=model.solve(out/'logs'/f'bench_{n}_{formulation}_rep{rep}.log',time_limit=30.)
                if rr['x'] is None: raise RuntimeError('Benchmark has no incumbent')
                qq,zz=unpack(rr['x'],idx)
                cc=verify.purchasing(dd,qq,zz,rr['objective']); assert cc['passed']
                if rep==0: dump(out/'benchmark_solutions'/f'n{n}_{formulation}_milp.json',dict(q=qq,z=zz))
                dump(out/'benchmark_checks'/f'n{n}_{formulation}_{rep}.json',cc)
                raw.append(dict(n=n,formulation=formulation,repeat=rep,status=rr['status'],seconds=rr['seconds'],
                                cost=rr['objective'],lp_bound=lr['objective'],nodes=rr['nodes'],mip_gap=rr['mip_gap'],dual_bound=rr['dual_bound']))
                mr.append(rr)
            best=min(x['objective'] for x in mr)
            summary.append(dict(n=n,formulation=formulation,variables=len(model.c),constraints=len(model.rows),
                   binaries=sum(model.integer),lp_bound=lr['objective'],milp_cost=best,
                   lp_gap_percent=100*(best-lr['objective'])/best,
                   median_seconds=float(np.median([x['seconds'] for x in mr])),
                   median_nodes=float(np.median([x['nodes'] for x in mr])),
                   final_mip_gap=max(x['mip_gap'] for x in mr),
                   all_optimal=all(x['status']=='Optimal' for x in mr)))
    for n in [5,10,20,40]:
        ss=[x for x in summary if x['n']==n]
        assert ss[0]['lp_bound']+1e-6>=ss[1]['lp_bound']
        if all(s['all_optimal'] for s in ss): assert abs(ss[0]['milp_cost']-ss[1]['milp_cost'])<=1e-6
    csvout(out/'benchmark_raw.csv',raw); csvout(out/'benchmark.csv',summary)
    csvout(out/'scenarios.csv',scenarios); dump(out/'checks.json',dict(milp=checks,lp=lc))
    dump(out/'results.json',dict(solutions=results,lp=lp,fractional=fractional,benchmark=summary,disabled_supplier=d['suppliers'][largest]))
    return dict(data=d,results=results,scenarios=scenarios,checks=checks,lp=lp,fractional=fractional,
                greedy=g,benchmark=summary,base_arrays=(q,z),lp_arrays=(lq,lz),disabled_supplier=d['suppliers'][largest])
