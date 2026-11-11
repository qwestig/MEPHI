from pathlib import Path
from copy import deepcopy
import time
import numpy as np
from .common import Model, dump, csvout, require_optimal
from . import verify

def build(d, shortfall=False):
    m=Model(); shape=(3,4,4)
    f=np.empty(shape,dtype=int); iw=np.empty((3,4),dtype=int); ir=np.empty((4,4),dtype=int)
    for w,j,t in np.ndindex(shape):
        f[w,j,t]=m.var(f'f_{w+1}_{j+1}_{t+1}',d['cost'][w][j][t],upper=d['capacity'][w][j][t])
    for w,t in np.ndindex(3,4): iw[w,t]=m.var(f'iw_{w+1}_{t+1}',d['holding_wh'][w],upper=d['max_wh'][w])
    for j,t in np.ndindex(4,4): ir[j,t]=m.var(f'ir_{j+1}_{t+1}',d['holding_store'][j],upper=d['max_store'][j])
    u=np.empty((4,4),dtype=int) if shortfall else None
    if shortfall:
        # Lexicographic phase 1: minimize unmet demand, with no transport cost.
        m.c=[0.]*len(m.c)
        for j,t in np.ndindex(4,4): u[j,t]=m.var(f'unmet_{j+1}_{t+1}',1.,upper=d['demand'][j][t])
    for w,t in np.ndindex(3,4):
        row={int(f[w,j,t]):1 for j in range(4)}; row[int(iw[w,t])]=1
        if t: row[int(iw[w,t-1])]=-1
        rhs=d['supply'][w][t]+(d['initial_wh'][w] if t==0 else 0)
        m.row(row,lower=rhs,upper=rhs,name=f'warehouse_{w+1}_period_{t+1}')
    for j,t in np.ndindex(4,4):
        row={int(f[w,j,t]):1 for w in range(3)}; row[int(ir[j,t])]=-1
        if t: row[int(ir[j,t-1])]=1
        if shortfall: row[int(u[j,t])]=1
        rhs=d['demand'][j][t]-(d['initial_store'][j] if t==0 else 0)
        m.row(row,lower=rhs,upper=rhs,name=f'store_{j+1}_period_{t+1}')
    return m,(f,iw,ir,u)

def unpack(x, ix):
    x=np.array(x)
    return tuple(x[a] for a in ix[:3])

def greedy(d):
    start=time.perf_counter()
    f=np.zeros((3,4,4)); iw=np.zeros((3,4)); ir=np.zeros((4,4)); stock=np.array(d['initial_wh'],dtype=float)
    for t in range(4):
        stock+=np.array(d['supply'])[:,t]; need=np.array(d['demand'])[:,t].copy()
        for w,j in sorted(np.ndindex(3,4),key=lambda a:d['cost'][a[0]][a[1]][t]):
            q=min(stock[w],need[j],d['capacity'][w][j][t]); f[w,j,t]=q; stock[w]-=q; need[j]-=q
        iw[:,t]=stock
    check=verify.network(d,f,iw,ir)
    return dict(seconds=time.perf_counter()-start,check=check,flow=f.tolist(),wh_inventory=iw.tolist(),store_inventory=ir.tolist())

def run(d,out):
    out=Path(out); results={}; checks={}; scenarios=[]
    m,ix=build(d); r=m.solve(out/'logs'/'base.log'); require_optimal(r)
    basef,_,_=unpack(r['x'],ix)
    busiest=tuple(int(x) for x in np.unravel_index(np.argmax(basef.sum(axis=2)),(3,4)))
    cases={k:deepcopy(d) for k in ['base','overload','failure','growth','stress']}
    w,j=busiest
    cases['overload']['capacity'][w][j]=(np.array(d['capacity'][w][j])*.5).tolist()
    for k in ['failure','stress']: cases[k]['capacity'][w][j]=[0.]*4
    for k in ['growth','stress']: cases[k]['demand']=(np.array(d['demand'])*1.2).tolist()
    all_constraints=[]; bottlenecks=[]; diagnostics={}
    for name,data in cases.items():
        m,idx=build(data)
        result=r if name=='base' else m.solve(out/'logs'/f'{name}.log')
        results[name]=result; dump(out/'scenarios'/f'{name}.json',data)
        row=dict(scenario=name,status=result['status'],cost=result['objective'],
                 demand=float(np.sum(data['demand'])),available=float(np.sum(data['supply'])+sum(data['initial_wh'])+sum(data['initial_store'])))
        if result['x'] is not None:
            f,iw,ir=unpack(result['x'],idx)
            check=verify.network(data,f,iw,ir,result['objective']); assert check['passed']; checks[name]=check
            csvout(out/f'solution_{name}.csv',[dict(warehouse=f'W{w+1}',store=f'R{j+1}',period=t+1,
                flow=f[w,j,t],capacity=data['capacity'][w][j][t],unit_cost=data['cost'][w][j][t]) for w,j,t in np.ndindex(3,4,4)])
            csvout(out/f'inventory_{name}.csv',[dict(node=f'{prefix}{i+1}',period=t+1,inventory=a[i,t])
                   for prefix,a in [('W',iw),('R',ir)] for i,t in np.ndindex(a.shape)])
            if name=='base':
                prevw=np.column_stack([d['initial_wh'],iw[:,:-1]])
                prevr=np.column_stack([d['initial_store'],ir[:,:-1]])
                for prefix,a in [('W',prevw+np.array(d['supply'])-f.sum(axis=1)-iw),
                                 ('R',prevr+f.sum(axis=0)-np.array(d['demand'])-ir)]:
                    for i,t in np.ndindex(a.shape):
                        all_constraints.append(dict(node=f'{prefix}{i+1}',period=t+1,balance_residual=a[i,t]))
                for w,j,t in np.ndindex(3,4,4):
                    if abs(f[w,j,t]-d['capacity'][w][j][t])<=1e-7:
                        col=idx[0][w,j,t]; marginal=result['col_dual'][col]
                        dd=deepcopy(d); dd['capacity'][w][j][t]+=.001
                        mm,_=build(dd); rr=mm.solve(out/'logs'/f'capacity_{w}_{j}_{t}.log'); require_optimal(rr)
                        down=deepcopy(d); down['capacity'][w][j][t]-=.001
                        dm,_=build(down); dr=dm.solve(out/'logs'/f'capacity_down_{w}_{j}_{t}.log'); require_optimal(dr)
                        bottlenecks.append(dict(route=f'W{w+1}->R{j+1}',period=t+1,flow=f[w,j,t],
                            shadow_cost=marginal,predicted_change=marginal*.001,
                            actual_change=rr['objective']-result['objective'],
                            change_when_reduced=dr['objective']-result['objective'],
                            perturbed_upper_dual=rr['col_dual'][col]))
        else:
            # Explicit conservation cut: total demand cannot exceed all available goods.
            cut_deficit=max(0.,row['demand']-row['available'])
            fm,fix=build(data,shortfall=True); fr=fm.solve(out/'logs'/f'elastic_{name}.log'); require_optimal(fr)
            flow,wi,ri=unpack(fr['x'],fix); unmet=np.array(fr['x'])[fix[3]]
            repaired=deepcopy(data); repaired['demand']=(np.array(data['demand'])-unmet).tolist()
            check=verify.network(repaired,flow,wi,ri); assert check['passed']
            assert abs(unmet.sum()-fr['objective'])<=1e-7
            dump(out/f'elastic_plan_{name}.json',dict(flow=flow,wh_inventory=wi,store_inventory=ri,unmet=unmet))
            diagnostics[name]=dict(total_supply_cut_shortfall=cut_deficit,minimum_unmet=float(unmet.sum()),
                                   unmet=unmet.tolist(),repaired_check=check,
                                   interpretation='Минимальное снижение спроса при фиксированных поставках, запасах и ёмкостях; не IIS.')
            csvout(out/f'unmet_{name}.csv',[dict(store=f'R{j+1}',period=t+1,unmet=unmet[j,t]) for j,t in np.ndindex(4,4)])
        scenarios.append(row)
    g=greedy(d)
    if g['check']['passed']:
        g['gap_percent']=100*(g['check']['objective_recomputed']-r['objective'])/r['objective']
    else: g['gap_percent']=None
    dump(out/'greedy.json',g)
    csvout(out/'greedy_solution.csv',[dict(warehouse=f'W{w+1}',store=f'R{j+1}',period=t+1,flow=g['flow'][w][j][t]) for w,j,t in np.ndindex(3,4,4)])
    csvout(out/'balances.csv',all_constraints); csvout(out/'bottlenecks.csv',bottlenecks)
    csvout(out/'scenarios.csv',scenarios); dump(out/'checks.json',checks); dump(out/'diagnostics.json',diagnostics)
    dump(out/'results.json',dict(solutions=results,busiest=busiest,scenarios=scenarios,bottlenecks=bottlenecks))
    return dict(data=d,results=results,scenarios=scenarios,checks=checks,greedy=g,busiest=busiest,
                bottlenecks=bottlenecks,diagnostics=diagnostics,base_arrays=unpack(r['x'],ix))
