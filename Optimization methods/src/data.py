"""Synthetic educational data; deterministic PCG64 streams, no external banking data."""
from pathlib import Path
import json
import numpy as np
from .common import SEED, dump

def lab1_data():
    r = np.random.default_rng(SEED)
    demand = r.integers(20, 43, 6).astype(float)
    profit = np.round(r.uniform(.075, .16, 6), 4)
    risk = np.round(r.uniform(.25, .95, 6), 2)
    hours = r.integers(6, 16, 6).astype(float)
    a = np.array([np.ones(6), risk, hours])
    b = np.round(a @ demand * np.array([.62,.49,.56]),2)
    return dict(branches=[f'B{i+1}' for i in range(6)], demand=demand.tolist(),
                profit=profit.tolist(), risk=risk.tolist(), hours=hours.tolist(),
                resources=b.tolist(), resource_names=['funding','risk_limit','staff_hours'])

def lab2_data():
    r = np.random.default_rng(SEED+1000)
    demand = r.integers(24, 41, (4,4)).astype(float)  # store, period
    supply = np.zeros((3,4))
    for t in range(4):
        supply[:,t] = np.ceil(demand[:,t].sum()*1.055*np.array([.30,.34,.36]))
    return dict(warehouses=['W1','W2','W3'], stores=['R1','R2','R3','R4'], periods=[1,2,3,4],
                demand=demand.tolist(), supply=supply.tolist(),
                initial_wh=r.integers(5,11,3).tolist(), initial_store=[0.]*4,
                capacity=r.integers(24,43,(3,4,4)).tolist(),
                cost=np.round(r.uniform(2,9,(3,4,4)),2).tolist(),
                holding_wh=np.round(r.uniform(.4,.9,3),2).tolist(),
                holding_store=np.round(r.uniform(1.2,2,4),2).tolist(),
                max_wh=[80.]*3, max_store=[30.]*4)

def lab3_data(n=5):
    # The benchmark has a separate stream for each n; no hand-picked instances.
    r = np.random.default_rng(SEED+2000+n)
    demand = np.round(r.integers(34,51,4)*n/5,2)
    cap = r.integers(75,106,n).astype(float)
    return dict(suppliers=[f'S{i+1}' for i in range(n)], goods=['G1','G2','G3','G4'],
                demand=demand.tolist(), capacity=cap.tolist(),
                price=np.round(r.uniform(3,8,(n,4)),2).tolist(),
                fixed=r.integers(25,61,n).tolist(), discount=[0.,.07,.15],
                thresholds=[0.,30.,60.], big_m=1000000.)

def generate(root):
    data = Path(root)/'data'
    for name, obj in [('lab1',lab1_data()),('lab2',lab2_data()),('lab3',lab3_data())]:
        dump(data/(name+'.json'), obj)
    dump(data/'variant.json', dict(name='Кртян Левон', group='Б24-517', N=7,Q=1,Y=26,
                                  V=1+((17*7+7+26)%20),seed=SEED,
                                  streams=dict(lab1=SEED,lab2=SEED+1000,lab3_base=SEED+2005)))

def load(root, name):
    return json.loads((Path(root)/'data'/(name+'.json')).read_text(encoding='utf-8'))
