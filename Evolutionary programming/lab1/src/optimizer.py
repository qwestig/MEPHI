"""Self-contained genetic algorithm for continuous minimisation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Callable

Vector = list[float]
Objective = Callable[[Vector], float]


@dataclass(frozen=True)
class GAParameters:
    population_size: int
    evaluation_budget: int
    crossover_probability: float
    mutation_probability: float
    mutation_sigma: float
    tournament_size: int = 3
    elitism: int = 1


@dataclass
class RunResult:
    best_vector: Vector
    best_value: float
    evaluations: int
    generations: int
    history: list[float]


def salomon(vector: Vector) -> float:
    """Salomon function. The global minimum is 0 at the zero vector."""
    radius = math.sqrt(sum(value * value for value in vector))
    return 1.0 - math.cos(2.0 * math.pi * radius) + 0.1 * radius


class GeneticAlgorithm:
    def __init__(
        self,
        objective: Objective,
        dimension: int,
        lower_bound: float,
        upper_bound: float,
        parameters: GAParameters,
        seed: int,
    ) -> None:
        if parameters.population_size < 2:
            raise ValueError("Population must contain at least two individuals.")
        if parameters.evaluation_budget < parameters.population_size:
            raise ValueError("Evaluation budget must cover the initial population.")
        self.objective = objective
        self.dimension = dimension
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.parameters = parameters
        self.random = random.Random(seed)

    def run(self) -> RunResult:
        population = [self._random_vector() for _ in range(self.parameters.population_size)]
        values = [self.objective(individual) for individual in population]
        evaluations = len(population)
        generations = 0
        best_index = min(range(len(population)), key=values.__getitem__)
        best_vector = population[best_index][:]
        best_value = values[best_index]
        history = [best_value]

        while evaluations < self.parameters.evaluation_budget:
            elite_indices = sorted(range(len(population)), key=values.__getitem__)[:self.parameters.elitism]
            next_population = [population[index][:] for index in elite_indices]
            elite_values = [values[index] for index in elite_indices]
            remaining = min(
                self.parameters.population_size - len(next_population),
                self.parameters.evaluation_budget - evaluations,
            )
            target_size = len(next_population) + remaining
            while len(next_population) < target_size:
                parent_a = self._tournament(population, values)
                parent_b = self._tournament(population, values)
                child = self._crossover(parent_a, parent_b)
                next_population.append(self._mutate(child))

            next_values = [self.objective(individual) for individual in next_population[len(elite_values):]]
            evaluations += len(next_values)
            population = next_population
            values = elite_values + next_values
            generations += 1

            generation_best_index = min(range(len(population)), key=values.__getitem__)
            if values[generation_best_index] < best_value:
                best_value = values[generation_best_index]
                best_vector = population[generation_best_index][:]
            history.append(best_value)

        return RunResult(best_vector, best_value, evaluations, generations, history)

    def _random_vector(self) -> Vector:
        return [self.random.uniform(self.lower_bound, self.upper_bound) for _ in range(self.dimension)]

    def _elite(self, population: list[Vector], values: list[float]) -> list[Vector]:
        indices = sorted(range(len(population)), key=values.__getitem__)[:self.parameters.elitism]
        return [population[index][:] for index in indices]

    def _tournament(self, population: list[Vector], values: list[float]) -> Vector:
        contenders = self.random.sample(range(len(population)), self.parameters.tournament_size)
        winner = min(contenders, key=values.__getitem__)
        return population[winner]

    def _crossover(self, parent_a: Vector, parent_b: Vector) -> Vector:
        if self.random.random() >= self.parameters.crossover_probability:
            return parent_a[:]
        alpha = self.random.random()
        return [alpha * a + (1.0 - alpha) * b for a, b in zip(parent_a, parent_b)]

    def _mutate(self, vector: Vector) -> Vector:
        child = vector[:]
        for index, value in enumerate(child):
            if self.random.random() < self.parameters.mutation_probability:
                value += self.random.gauss(0.0, self.parameters.mutation_sigma)
                child[index] = min(self.upper_bound, max(self.lower_bound, value))
        return child


def random_search(
    objective: Objective, dimension: int, lower_bound: float, upper_bound: float, evaluation_budget: int, seed: int
) -> RunResult:
    generator = random.Random(seed)
    best_vector: Vector | None = None
    best_value = math.inf
    history: list[float] = []
    for _ in range(evaluation_budget):
        candidate = [generator.uniform(lower_bound, upper_bound) for _ in range(dimension)]
        value = objective(candidate)
        if value < best_value:
            best_value, best_vector = value, candidate
        history.append(best_value)
    return RunResult(best_vector or [], best_value, evaluation_budget, 0, history)
