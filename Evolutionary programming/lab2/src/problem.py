"""Capacitated waste collection with one depot and a fixed fleet."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Evaluation:
    distance: float
    overload: int
    loads: tuple[int, ...]

    @property
    def feasible(self) -> bool:
        return self.overload == 0


class Problem:
    def __init__(self, data: dict):
        self.data = data
        self.capacity = data["capacity"]
        self.vehicles = data["vehicles"]
        self.nodes = data["nodes"]
        self.n = len(self.nodes) - 1
        if (self.n < 1 or self.vehicles < 1 or self.capacity <= 0
                or [node["id"] for node in self.nodes] != list(range(self.n + 1))
                or self.nodes[0]["demand"] != 0
                or any(not 0 < node["demand"] <= self.capacity for node in self.nodes[1:])):
            raise ValueError("Invalid depot, customer IDs, fleet, capacity or demands")
        self.demands = [node["demand"] for node in self.nodes]
        self.tokens = tuple(range(1, self.n + 1)) + tuple(-i for i in range(1, self.vehicles))
        self.distances = [
            [math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for b in self.nodes]
            for a in self.nodes
        ]
        # A verified packing guarantees repair even if local relocation gets stuck.
        self.reference_routes = self._pack(list(range(1, self.n + 1)))
        if self.reference_routes is None:
            raise ValueError("This instance requires a supplied feasible packing; FFD failed")

    @classmethod
    def load(cls, path: Path) -> Problem:
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def validate(self, chromosome: Sequence[int]) -> None:
        if len(chromosome) != len(self.tokens) or set(chromosome) != set(self.tokens):
            raise ValueError("Chromosome must contain every customer and separator exactly once")

    def decode(self, chromosome: Sequence[int]) -> list[list[int]]:
        routes: list[list[int]] = [[]]
        for token in chromosome:
            if token < 0:
                routes.append([])
            else:
                routes[-1].append(token)
        return routes

    def encode(self, routes: list[list[int]]) -> list[int]:
        if len(routes) != self.vehicles:
            raise ValueError("Wrong number of routes")
        chromosome: list[int] = []
        for index, route in enumerate(routes):
            if index:
                chromosome.append(-index)
            chromosome.extend(route)
        self.validate(chromosome)
        return chromosome

    def route_distance(self, route: Sequence[int]) -> float:
        return sum(self.distances[a][b] for a, b in zip([0, *route], [*route, 0]))

    def evaluate(self, chromosome: Sequence[int]) -> Evaluation:
        self.validate(chromosome)
        routes = self.decode(chromosome)
        loads = tuple(sum(self.demands[i] for i in route) for route in routes)
        return Evaluation(sum(self.route_distance(route) for route in routes),
                          sum(max(0, load - self.capacity) for load in loads), loads)

    def _pack(self, order: list[int]) -> list[list[int]] | None:
        position = {customer: index for index, customer in enumerate(order)}
        routes: list[list[int]] = [[] for _ in range(self.vehicles)]
        loads = [0] * self.vehicles
        for customer in sorted(order, key=lambda i: (-self.demands[i], position[i])):
            target = next((j for j in range(self.vehicles)
                           if loads[j] + self.demands[customer] <= self.capacity), None)
            if target is None:
                return None
            routes[target].append(customer)
            loads[target] += self.demands[customer]
        for route in routes:
            route.sort(key=position.__getitem__)
        return routes

    def repair(self, chromosome: Sequence[int]) -> list[int]:
        """Move customers out of overloaded routes; use verified packing if stuck.

        Repair reads demands, not the objective. Each candidate is evaluated only
        once afterwards, so objective-call accounting includes all scoring work.
        """
        self.validate(chromosome)
        routes = self.decode(chromosome)
        loads = [sum(self.demands[i] for i in route) for route in routes]
        while max(loads) > self.capacity:
            source = max(range(self.vehicles), key=loads.__getitem__)
            candidates = [
                (loads[source] - self.demands[c] > self.capacity,
                 abs(loads[source] - self.demands[c] - self.capacity), -loads[target], c, target)
                for c in routes[source] for target in range(self.vehicles)
                if target != source and loads[target] + self.demands[c] <= self.capacity
            ]
            if not candidates:
                order = [c for c in chromosome if c > 0]
                packed = self._pack(order)
                if packed is None:
                    position = {c: i for i, c in enumerate(order)}
                    packed = [sorted(route, key=position.__getitem__) for route in self.reference_routes]
                return self.encode(packed)
            _, _, _, customer, target = min(candidates)
            routes[source].remove(customer)
            routes[target].append(customer)
            loads[source] -= self.demands[customer]
            loads[target] += self.demands[customer]
        return self.encode(routes)

    def greedy(self) -> list[int]:
        """Nearest neighbour within a capacity-feasible route, then repair."""
        remaining = set(range(1, self.n + 1))
        routes: list[list[int]] = []
        for _ in range(self.vehicles):
            route: list[int] = []
            load, current = 0, 0
            while candidates := [i for i in remaining if load + self.demands[i] <= self.capacity]:
                customer = min(candidates, key=lambda i: (self.distances[current][i], i))
                route.append(customer)
                remaining.remove(customer)
                load += self.demands[customer]
                current = customer
            routes.append(route)
        routes[-1].extend(sorted(remaining))
        return self.repair(self.encode(routes))
