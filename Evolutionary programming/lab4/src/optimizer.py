"""Coverage archives, rarity-based GA and multi-target distance-guided GA."""
from collections import Counter
import random


class Recorder:
    def __init__(self, subject, budget, track_distances=False):
        self.subject, self.budget = subject, budget
        self.count, self.archive, self.pool, self.hits, self.history = 0, {}, {}, Counter(), []
        self.first_full = None
        self.track_distances, self.closest = track_distances, {}

    def evaluate(self, genome):
        execution = self.subject.execute(genome)
        self.count += 1
        new = execution.covered - self.archive.keys()
        if new:
            self.pool[execution.genome] = execution.covered
        for branch in new:
            self.archive[branch] = execution.genome
        self.hits.update(execution.covered)
        if self.track_distances:
            function = self.subject.functions[execution.genome[0]]
            for goal in self.subject.goals:
                if self.subject.metadata[goal[:-2]]['function'] == function:
                    value = self.subject.fitness(execution, goal)
                    if goal not in self.closest or value < self.closest[goal][0]:
                        self.closest[goal] = (value, execution)
        if len(self.archive) == len(self.subject.goals) and self.first_full is None:
            self.first_full = self.count
        if self.count % 60 == 0 or self.count == self.budget:
            self.history.append((self.count, len(self.archive)))
        return execution

    def minimized_suite(self):
        remaining = set(self.archive)
        suite = []
        while remaining:
            genome = min(self.pool, key=lambda g: (-len(self.pool[g]&remaining), g))
            covered = self.pool[genome]&remaining
            if not covered:
                raise RuntimeError('Archive cannot be covered by its witness pool')
            suite.append(dict(genome=genome, covers=sorted(self.pool[genome])))
            remaining -= covered
        # Delete redundant members, keeping coverage exactly equal to the archive.
        for index in range(len(suite)-1, -1, -1):
            others = set().union(*(set(row['covers']) for j, row in enumerate(suite) if j != index))
            if set(self.archive) <= others:
                suite.pop(index)
        return suite


def random_genome(cfg, count, rng):
    return (rng.randrange(count), *(rng.randint(cfg['lower_bound'], cfg['upper_bound']) for _ in range(3)))


def vary(a, b, cfg, function_count, constants, rng, target_function=None):
    genome = list(a)
    if rng.random() < cfg['crossover_probability']:
        genome = [x if rng.random() < 0.5 else y for x, y in zip(a, b)]
    if rng.random() < cfg['mutation_probability']:
        genome[0] = rng.randrange(function_count)
    for k in range(1, 4):
        if rng.random() < cfg['mutation_probability']:
            choice = rng.random()
            if choice < 0.20:
                genome[k] = rng.randint(cfg['lower_bound'], cfg['upper_bound'])
            elif choice < 0.45:
                genome[k] = rng.choice(constants)
            else:
                genome[k] += rng.choice([-1, 1]) if rng.random() < 0.5 else round(rng.gauss(0, 10))
            genome[k] = min(cfg['upper_bound'], max(cfg['lower_bound'], genome[k]))
    if target_function is not None:
        genome[0] = target_function
    return tuple(genome)


def random_search(subject, cfg, seed, record, constants):
    rng = random.Random(seed)
    for _ in range(record.budget):
        record.evaluate(random_genome(cfg, len(subject.functions), rng))


def genetic_search(subject, cfg, seed, record, constants, directed=False):
    rng, size = random.Random(seed), cfg['population_size']
    population = [record.evaluate(random_genome(cfg, len(subject.functions), rng)) for _ in range(size)]
    attempts = Counter()
    target, target_until = None, 0
    while record.count < record.budget:
        if directed and (target is None or target in record.archive or record.count >= target_until):
            available = [goal for goal in subject.goals if goal not in record.archive] or subject.goals
            target = min(available, key=lambda goal: (attempts[goal], len(subject.paths[goal]), goal))
            target_until = record.count+cfg['restart_interval']
            # Reuse previously measured candidates; no hidden subject executions.
            candidates = population[:]
            if target in record.closest:
                candidates.append(record.closest[target][1])
            population = sorted(candidates, key=lambda e: subject.fitness(e, target))[:size//2]
            for _ in range(min(size-len(population), record.budget-record.count)):
                population.append(record.evaluate(random_genome(cfg, len(subject.functions), rng)))
        if directed:
            score = lambda e: subject.fitness(e, target)
            function_index = subject.functions.index(subject.metadata[target[:-2]]['function'])
        else:
            score = lambda e: -sum(1/(1+record.hits[b]) for b in sorted(e.covered))
            function_index = None
        elite = sorted(population, key=score)[:2]
        following = elite[:]
        count = min(size-2, record.budget-record.count)
        for _ in range(count):
            def tournament():
                return min(rng.sample(population, min(3, len(population))), key=score).genome
            genome = vary(tournament(), tournament(), cfg, len(subject.functions), constants, rng, function_index)
            following.append(record.evaluate(genome))
        if directed:
            attempts[target] += count
        population = following
