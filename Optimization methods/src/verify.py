"""Independent domain checks. NumPy only; no solver imports or model matrices."""
import numpy as np
TOL = 1e-7

def finish(parts, objective, expected=None):
    # Each residual is positive exactly when its physical constraint is violated.
    maxes = {k:float(np.max(np.maximum(np.asarray(v,dtype=float),0.), initial=0.)) for k,v in parts.items()}
    err = abs(objective-expected) if expected is not None else 0.
    return dict(passed=bool(all(v<=TOL for v in maxes.values()) and err<=TOL),
                tolerance=TOL, violations=maxes, objective_recomputed=float(objective),
                objective_error=float(err))

def credit(d, x, expected=None):
    x=np.asarray(x); resources=np.asarray(d['resources'])
    usage=np.array([x.sum(), np.asarray(d['risk'])@x, np.asarray(d['hours'])@x])
    return finish(dict(nonnegative=-x, demand=x-np.asarray(d['demand']),
                       resources=usage-resources), np.asarray(d['profit'])@x, expected)

def network(d, f, iw, ir, expected=None):
    f,iw,ir=map(np.asarray,(f,iw,ir))
    prevw=np.column_stack([d['initial_wh'],iw[:,:-1]])
    prevr=np.column_stack([d['initial_store'],ir[:,:-1]])
    bw=prevw+np.asarray(d['supply'])-f.sum(axis=1)-iw
    br=prevr+f.sum(axis=0)-np.asarray(d['demand'])-ir
    value=(f*np.asarray(d['cost'])).sum()+(iw*np.asarray(d['holding_wh'])[:,None]).sum()+(ir*np.asarray(d['holding_store'])[:,None]).sum()
    return finish(dict(flow_nonnegative=-f,wh_nonnegative=-iw,store_nonnegative=-ir,
                       route_capacity=f-np.asarray(d['capacity']),
                       warehouse_storage=iw-np.asarray(d['max_wh'])[:,None],
                       store_storage=ir-np.asarray(d['max_store'])[:,None],
                       warehouse_balance=np.abs(bw),store_balance=np.abs(br)),value,expected)

def purchasing(d, q, z, expected=None, integral=True, formulation='strong'):
    q,z=map(np.asarray,(q,z)); n=len(d['capacity'])
    demand=np.asarray(d['demand']); cap=np.asarray(d['capacity'])
    low=np.broadcast_to(d['thresholds'],(n,3))
    up=np.minimum(np.broadcast_to([30.,60.,np.inf],(n,3)),cap[:,None])
    volumes=q.sum(axis=1) # supplier,tier
    val=(q*np.asarray(d['price'])[:,:,None]*(1-np.asarray(d['discount']))).sum()+(z*np.asarray(d['fixed'])[:,None]).sum()
    parts=dict(q_nonnegative=-q,z_nonnegative=-z,z_upper=z-1,
               demand=np.abs(q.sum(axis=(0,2))-demand),one_tier=z.sum(axis=1)-1,
               capacity=q.sum(axis=(1,2))-cap,
               tier_lower=low*z-volumes)
    if formulation=='strong':
        parts['tier_upper']=volumes-up*z
        parts['product_links']=q-np.minimum(demand[None,:,None],up[:,None,:])*z[:,None,:]
    else:
        parts['unconditional_tier_upper']=volumes-up
        parts['loose_big_M']=volumes-d['big_m']*z
    if integral: parts['integrality']=np.abs(z-np.rint(z))
    return finish(parts,val,expected)
