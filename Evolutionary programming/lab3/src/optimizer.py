"""NSGA-II, weighted-sum GA and random baseline, implemented from scratch."""
from bisect import bisect_right
import random


def dominates(a, b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] <= b[2] and a != b


def fronts(values):
    dominated = [[] for _ in values]
    counts = [0]*len(values)
    for i, a in enumerate(values):
        for j in range(i+1, len(values)):
            b = values[j]
            if dominates(a, b):
                dominated[i].append(j)
                counts[j] += 1
            elif dominates(b, a):
                dominated[j].append(i)
                counts[i] += 1
    layer = [i for i, count in enumerate(counts) if count == 0]
    layers = []
    while layer:
        layers.append(layer)
        following = []
        for i in layer:
            for j in dominated[i]:
                counts[j] -= 1
                if counts[j] == 0:
                    following.append(j)
        layer = following
    return layers


def crowding(layer, values):
    distance = {i: 0.0 for i in layer}
    if len(layer) <= 2:
        return {i: float('inf') for i in layer}
    for k in range(3):
        order = sorted(layer, key=lambda i: values[i][k])
        span = values[order[-1]][k] - values[order[0]][k]
        if not span:
            continue
        distance[order[0]] = distance[order[-1]] = float('inf')
        for pos in range(1, len(order)-1):
            distance[order[pos]] += (values[order[pos+1]][k] - values[order[pos-1]][k])/span
    return distance


def nondominated(items):
    """3D first front, using a 2D skyline after sorting the first objective.

    Return one representative per objective vector; duplicate hardware is allowed
    in the population but must not inflate front-size or recall metrics.
    """
    unique = {}
    for genome, value in items:
        unique.setdefault(value, genome)
    ys, zs, result = [], [], []
    for value in sorted(unique):
        y, z = value[1:]
        position = bisect_right(ys, y)
        if position and zs[position-1] <= z:
            continue
        # Remove entries in the auxiliary skyline, never historical 3D results.
        end = position
        while end < len(ys) and zs[end] >= z:
            end += 1
        ys[position:end] = [y]
        zs[position:end] = [z]
        result.append((unique[value], value))
    return result


def hypervolume(points, reference):
    """Exact union of 3D minimisation boxes by slabs along the first axis."""
    points = sorted(set(points))
    total = 0.0
    active = []
    for i, point in enumerate(points):
        active.append(point)
        right = points[i+1][0] if i+1 < len(points) else reference[0]
        if right <= point[0]:
            continue
        floor, area = reference[2], 0.0
        for _, y, z in sorted(active, key=lambda p: (p[1], p[2])):
            if z < floor:
                area += max(0, reference[1]-y)*(floor-z)
                floor = z
        total += (right-point[0])*area
    return total


class Recorder:
    def __init__(self, problem, budget, reference):
        self.problem, self.budget, self.reference = problem, budget, reference
        self.count, self.seen, self.history = 0, {}, []

    def evaluate(self, genome):
        value = self.problem.evaluate(genome)
        self.seen[genome] = value
        self.count += 1
        if self.count % 400 == 0 or self.count == self.budget:
            front = nondominated(self.seen.items())
            hv = hypervolume([self.problem.normalize(v) for _, v in front], self.reference)
            self.history.append((self.count, hv, len(front)))
        return value


def random_genome(problem, rng):
    return tuple(rng.randrange(n) for n in problem.sizes)


def child(a, b, problem, cfg, rng):
    genes = list(a)
    if rng.random() < cfg['crossover_probability']:
        genes = [x if rng.random() < 0.5 else y for x, y in zip(a, b)]
    for k, n in enumerate(problem.sizes):
        if rng.random() < cfg['mutation_probability']:
            genes[k] = rng.randrange(n)
    return tuple(genes)


def nsga2(problem, cfg, seed, record):
    rng, size = random.Random(seed), cfg['population_size']
    population = [random_genome(problem, rng) for _ in range(size)]
    values = [record.evaluate(g) for g in population]
    while record.count < record.budget:
        layers = fronts(values)
        ranks = {i: rank for rank, layer in enumerate(layers) for i in layer}
        distances = {i: d for layer in layers for i, d in crowding(layer, values).items()}
        def tournament():
            a, b = rng.sample(range(len(population)), 2)
            return population[min([a, b], key=lambda i: (ranks[i], -distances[i]))]
        offspring = [child(tournament(), tournament(), problem, cfg, rng)
                     for _ in range(min(size, record.budget-record.count))]
        offspring_values = [record.evaluate(g) for g in offspring]
        combined, scores = population+offspring, values+offspring_values
        chosen = []
        for layer in fronts(scores):
            if len(chosen)+len(layer) <= size:
                chosen.extend(layer)
            else:
                dist = crowding(layer, scores)
                chosen.extend(sorted(layer, key=lambda i: -dist[i])[:size-len(chosen)])
                break
        population, values = [combined[i] for i in chosen], [scores[i] for i in chosen]


def weighted_ga(problem, cfg, seed, record):
    rng = random.Random(seed)
    weights = cfg['weights']
    if record.budget % len(weights):
        raise ValueError('Weighted runs need equal integer sub-budgets')
    sub_budget, size = record.budget//len(weights), cfg['weighted_population']
    for weight in weights:
        end = record.count+sub_budget
        population = [random_genome(problem, rng) for _ in range(size)]
        values = [record.evaluate(g) for g in population]
        def scalar(value):
            return sum(w*f for w, f in zip(weight, problem.normalize(value)))/sum(weight)
        while record.count < end:
            elite = sorted(range(len(population)), key=lambda i: scalar(values[i]))[:2]
            new_pop, new_values = [population[i] for i in elite], [values[i] for i in elite]
            def tournament():
                return population[min(rng.sample(range(len(population)), 3), key=lambda i: scalar(values[i]))]
            for _ in range(min(size-2, end-record.count)):
                genome = child(tournament(), tournament(), problem, cfg, rng)
                new_pop.append(genome)
                new_values.append(record.evaluate(genome))
            population, values = new_pop, new_values


def random_search(problem, cfg, seed, record):
    rng = random.Random(seed)
    for _ in range(record.budget):
        record.evaluate(random_genome(problem, rng))
