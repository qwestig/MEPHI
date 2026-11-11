from pathlib import Path
from copy import deepcopy
import numpy as np
from .common import Model, dump, csvout, require_optimal
from . import verify

def build(d):
    m=Model(); n=len(d['branches'])
    for i in range(n): m.var(d['branches'][i],-d['profit'][i])
    a=np.array([np.ones(n),d['risk'],d['hours']])
    for k in range(3): m.row(enumerate(a[k]),upper=d['resources'][k],name=d['resource_names'][k])
    for i in range(n): m.row({i:1},upper=d['demand'][i],name='demand_'+d['branches'][i])
    return m

def run(d, out):
    out=Path(out); results={}; scenarios=[]; checks={}
    cases={'base':deepcopy(d),'deficit':deepcopy(d),'stress':deepcopy(d)}
    cases['deficit']['resources'][0]*=.8
    cases['stress']['resources'][0]*=.8; cases['stress']['resources'][2]*=.6
    for name,data in cases.items():
        m=build(data); r=m.solve(out/'logs'/f'{name}.log'); require_optimal(r)
        check=verify.credit(data,r['x'],-r['objective']); assert check['passed']
        checks[name]=check; results[name]=r
        scenarios.append(dict(scenario=name,status=r['status'],profit=-r['objective'],
                              funding=data['resources'][0],risk=data['resources'][1],hours=data['resources'][2],
                              plan='; '.join(f'{b}={x:.5f}' for b,x in zip(d['branches'],r['x']))))
        dump(out/'scenarios'/f'{name}.json',data)
        csvout(out/f'solution_{name}.csv', [dict(branch=b,loan_million=x,annual_income_million=x*p)
               for b,x,p in zip(d['branches'],r['x'],d['profit'])])
    base=results['base']; x=np.array(base['x']); price=-np.array(base['row_dual'])
    a=np.array([np.ones(6),d['risk'],d['hours']]); b=np.r_[d['resources'],d['demand']]
    aa=np.vstack([a,np.eye(6)])
    rows=[dict(constraint=name,usage=float(v),limit=float(lim),slack=float(lim-v),shadow_price=float(p))
          for name,v,lim,p in zip(build(d).rnames,aa@x,b,price)]
    csvout(out/'constraints.csv', rows)
    csvout(out/'reduced_costs.csv',[dict(branch=d['branches'][j],loan=x[j],
                opportunity_cost=float(aa[:,j]@price-d['profit'][j])) for j in range(6)])
    predictions=[]
    for name in ['deficit','stress']:
        delta=np.array(cases[name]['resources'])-d['resources']
        pred=float(price[:3]@delta); actual=-results[name]['objective']+base['objective']
        predictions.append(dict(scenario=name,predicted_change=pred,actual_change=actual,error=actual-pred))
    for k in range(3):
        dd=deepcopy(d); delta=.001; dd['resources'][k]+=delta
        r=build(dd).solve(out/'logs'/f'perturb_{k}.log'); require_optimal(r)
        change=-r['objective']+base['objective']
        predictions.append(dict(scenario='small_increase_'+d['resource_names'][k],predicted_change=price[k]*delta,
                                actual_change=change,error=change-price[k]*delta))
    csvout(out/'shadow_prediction.csv',predictions)
    # Star 10: build and solve the full dual, including all six demand multipliers.
    dual=Model()
    for i,name in enumerate(build(d).rnames): dual.var('dual_'+name,b[i])
    for j in range(6): dual.row(enumerate(aa[:,j]),lower=d['profit'][j],name='branch_'+str(j+1))
    dr=dual.solve(out/'logs'/'full_dual.log'); require_optimal(dr)
    u=np.array(dr['x']); gap=dr['objective']+base['objective']
    cert=dict(primal_profit=-base['objective'],dual_cost=float(b@u),gap=float(gap),
              dual_nonnegative_violation=float(np.maximum(-u,0).max(initial=0)),
              dual_constraint_violation=float(np.maximum(np.array(d['profit'])-aa.T@u,0).max(initial=0)),
              primal_complementarity=float(np.abs(u*(b-aa@x)).max(initial=0)),
              dual_complementarity=float(np.abs(x*(aa.T@u-d['profit'])).max(initial=0)))
    cert['passed']=all(abs(cert[k])<=1e-7 for k in ['gap','dual_nonnegative_violation','dual_constraint_violation','primal_complementarity','dual_complementarity'])
    assert cert['passed']
    dump(out/'dual_certificate.json',cert)
    csvout(out/'dual_solution.csv',[dict(multiplier=n,value=v) for n,v in zip(build(d).rnames,u)])
    dump(out/'checks.json',checks); csvout(out/'scenarios.csv',scenarios)
    dump(out/'results.json',dict(solutions=results,dual=dr,certificate=cert,constraints=rows,predictions=predictions))
    return dict(data=d,results=results,scenarios=scenarios,checks=checks,constraints=rows,
                predictions=predictions,dual=dr,certificate=cert)
