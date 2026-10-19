"""Hand-written OX genetic algorithm and a repaired random-search baseline."""

from __future__ import annotations

from dataclasses import dataclass
import random
from time import perf_counter

from problem import Evaluation, Problem


def order_crossover(a: list[int], b: list[int], rng: random.Random) -> list[int]:
    """OX treats uniquely labelled separators as permutation elements."""
    left, right = sorted(rng.sample(range(len(a) + 1), 2))
    child = [None] * len(a)
    child[left:right] = a[left:right]
    used = set(a[left:right])
    fill = [item for item in b[right:] + b[:right] if item not in used]
    positions = list(range(right, len(a))) + list(range(left))
    for position, item in zip(positions, fill):
        child[position] = item
    return child


def mutate(chromosome: list[int], kind: str, rng: random.Random) -> list[int]:
    child = chromosome[:]
    i, j = sorted(rng.sample(range(len(child)), 2))
    if kind == "swap":
        child[i], child[j] = child[j], child[i]
    elif kind == "inversion":
        child[i:j + 1] = reversed(child[i:j + 1])
    else:
        raise ValueError(f"Unknown mutation: {kind}")
    return child


@dataclass(frozen=True)
class Parameters:
    population_size: int = 80
    evaluation_budget: int = 10000
    tournament_size: int = 3
    elitism: int = 2
    crossover_probability: float = 0.9
    mutation_probability: float = 0.3
    penalty_coefficient: float = 10000.0
    constraints: str = "repair"
    mutation: str = "inversion"

    def __post_init__(self):
        if not 0 <= self.elitism < self.population_size:
            raise ValueError("Elitism must be smaller than population")
        if not 1 <= self.tournament_size <= self.population_size:
            raise ValueError("Invalid tournament size")
        if self.evaluation_budget < self.population_size:
            raise ValueError("Budget must cover initial population")
        if not (0 <= self.crossover_probability <= 1 and 0 <= self.mutation_probability <= 1):
            raise ValueError("Invalid operator probability")
        if self.penalty_coefficient <= 0 or self.constraints not in {"repair", "penalty"}:
            raise ValueError("Invalid constraint parameters")
        if self.mutation not in {"swap", "inversion"}:
            raise ValueError("Invalid mutation")


@dataclass
class Result:
    chromosome: list[int]
    distance: float
    evaluations: int
    generations: int
    feasible_evaluations: int
    final_feasible_fraction: float
    seconds: float
    history: list[tuple[int, float]]


def genetic_algorithm(problem: Problem, params: Parameters, seed: int) -> Result:
    start = perf_counter()
    rng = random.Random(seed)
    best: list[int] = []
    best_distance = float("inf")
    evaluations = feasible_evaluations = 0

    def score(chromosome: list[int]) -> tuple[list[int], Evaluation, float]:
        nonlocal best, best_distance, evaluations, feasible_evaluations
        if params.constraints == "repair":
            chromosome = problem.repair(chromosome)
        evaluation = problem.evaluate(chromosome)
        evaluations += 1
        feasible_evaluations += evaluation.feasible
        if evaluation.feasible and evaluation.distance < best_distance:
            best, best_distance = chromosome[:], evaluation.distance
        return chromosome, evaluation, evaluation.distance + params.penalty_coefficient * evaluation.overload

    # Every method receives the same feasible constructive seed and pays one call.
    population = [score(problem.greedy())]
    for _ in range(params.population_size - 1):
        population.append(score(rng.sample(list(problem.tokens), len(problem.tokens))))
    history = [(evaluations, best_distance)]
    generations = 0

    def tournament():
        return min(rng.sample(population, params.tournament_size), key=lambda item: item[2])[0]

    while evaluations < params.evaluation_budget:
        next_population = sorted(population, key=lambda item: item[2])[:params.elitism]
        count = min(params.population_size - params.elitism, params.evaluation_budget - evaluations)
        for _ in range(count):
            a, b = tournament(), tournament()
            child = order_crossover(a, b, rng) if rng.random() < params.crossover_probability else a[:]
            if rng.random() < params.mutation_probability:
                child = mutate(child, params.mutation, rng)
            next_population.append(score(child))
        population = next_population
        generations += 1
        history.append((evaluations, best_distance))
    return Result(best, best_distance, evaluations, generations, feasible_evaluations,
                  sum(item[1].feasible for item in population) / len(population),
                  perf_counter() - start, history)


def random_search(problem: Problem, params: Parameters, seed: int) -> Result:
    start = perf_counter()
    rng = random.Random(seed)
    best = problem.greedy()
    best_distance = problem.evaluate(best).distance
    history = []
    checkpoints = set(range(params.population_size, params.evaluation_budget + 1,
                            params.population_size - params.elitism)) | {params.evaluation_budget}
    for evaluations in range(2, params.evaluation_budget + 1):
        chromosome = problem.repair(rng.sample(list(problem.tokens), len(problem.tokens)))
        value = problem.evaluate(chromosome).distance
        if value < best_distance:
            best, best_distance = chromosome, value
        if evaluations in checkpoints:
            history.append((evaluations, best_distance))
    if params.evaluation_budget == 1:
        history = [(1, best_distance)]
    return Result(best, best_distance, params.evaluation_budget, 0, params.evaluation_budget,
                  1.0, perf_counter() - start, history)
