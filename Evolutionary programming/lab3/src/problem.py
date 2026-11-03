"""Synthetic hardware catalogue and an exhaustive, finite reference problem."""
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def generate(seed=132603):
    rng = random.Random(seed)
    cpus = []
    for i, (score, power, price) in enumerate([(80, 85, 160), (75, 35, 240), (110, 95, 260),
            (108, 45, 350), (145, 120, 400), (138, 65, 490), (180, 150, 610), (170, 80, 700)]):
        cpus.append(dict(name=f'CPU-{i+1}', score=score, power=power, price=price+rng.randint(-8, 8),
                         memory='DDR4' if i < 4 else 'DDR5', board_price=100 if i < 4 else 160))
    gpus = [dict(name=f'GPU-{i+1}', score=s, power=w, price=p+rng.randint(-8, 8))
            for i, (s, w, p) in enumerate([(35, 25, 90), (65, 55, 150), (95, 95, 240),
                (90, 60, 310), (135, 140, 420), (150, 110, 560), (195, 230, 780), (235, 285, 1120)])]
    ram = [dict(name=f'{size} GB', size=size, price=round(size*2.2), power=3+size/16)
           for size in [8, 16, 24, 32, 48, 64]]
    storage = [dict(name=name, score=s, price=p, power=w) for name, s, p, w in
               [('HDD-1TB', 10, 40, 9), ('SATA-500GB', 30, 55, 4), ('SATA-1TB', 38, 85, 5),
                ('NVMe-1TB', 60, 110, 6), ('NVMe-2TB', 68, 185, 7)]]
    return dict(seed=seed, source='Synthetic educational catalogue; not commercial offers',
                cpu=cpus, gpu=gpus, ram=ram, storage=storage, fixed_price=130, fixed_power=35)


class Problem:
    def __init__(self, data):
        self.data = data
        self.categories = ['cpu', 'gpu', 'ram', 'storage']
        self.sizes = tuple(len(data[k]) for k in self.categories)
        self.genomes = list(itertools.product(*(range(n) for n in self.sizes)))
        self.objectives = {g: self.evaluate(g) for g in self.genomes}
        self.ideal = tuple(min(v[k] for v in self.objectives.values()) for k in range(3))
        self.nadir = tuple(max(v[k] for v in self.objectives.values()) for k in range(3))

    def evaluate(self, genome):
        if len(genome) != 4 or any(not 0 <= g < n for g, n in zip(genome, self.sizes)):
            raise ValueError('Invalid component index')
        cpu, gpu, ram, disk = [self.data[k][i] for k, i in zip(self.categories, genome)]
        price = self.data['fixed_price'] + cpu['board_price'] + sum(c['price'] for c in [cpu, gpu, ram, disk])
        # Matching RAM generation is selected by the decoder; DDR5 has a surcharge.
        if cpu['memory'] == 'DDR5':
            price += round(ram['size'] * 0.5)
        power = self.data['fixed_power'] + sum(c['power'] for c in [cpu, gpu, ram, disk])
        perf = 0.5*cpu['score'] + 0.5*min(gpu['score'], 1.3*cpu['score']) + 0.5*min(ram['size'], 32) + 0.12*disk['score']
        return float(price), power, -perf

    def normalize(self, objective):
        return tuple((v-lo)/(hi-lo) for v, lo, hi in zip(objective, self.ideal, self.nadir))

    def describe(self, genome):
        chosen = {k: self.data[k][i]['name'] for k, i in zip(self.categories, genome)}
        chosen['memory_generation'] = self.data['cpu'][genome[0]]['memory']
        return chosen


if __name__ == '__main__':
    path = ROOT / 'data/catalogue.json'
    path.write_text(json.dumps(generate(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(path)
