"""Generate and save the synthetic variant-13 instance, with an explicit seed."""

import argparse
import json
from pathlib import Path
import random

from problem import Problem

ROOT = Path(__file__).resolve().parents[1]


def generate(seed: int = 132026) -> dict:
    rng = random.Random(seed)
    nodes = [{"id": 0, "name": "Депо", "x": 50, "y": 50, "demand": 0}]
    for i in range(1, 21):
        nodes.append({"id": i, "name": f"Площадка {i:02d}", "x": rng.randint(5, 95),
                      "y": rng.randint(5, 95), "demand": rng.randint(3, 9)})
    data = {"variant": 13, "seed": seed, "vehicles": 4, "capacity": 35,
            "distance_unit": "км (условная модель района)", "demand_unit": "контейнер",
            "nodes": nodes}
    Problem(data)  # Verify a feasible packing before publishing the instance.
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=132026)
    parser.add_argument("--output", type=Path, default=ROOT / "data/waste_collection.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(args.seed), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)
