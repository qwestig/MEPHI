"""Create a convergence plot from experiment output using only Python's standard library."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import statistics
import math


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("results/trajectories.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/convergence.svg"))
    args = parser.parse_args()

    values: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    with args.input.open(encoding="utf-8") as source:
        for row in csv.DictReader(source):
            values[row["method"]][int(row["step"])].append(float(row["best_value"]))

    # A generation is meaningful only for GA configurations. Random search has one
    # value per function evaluation, so it is compared numerically in summary.csv.
    values.pop("random_search", None)
    curves = {}
    for method, steps in values.items():
        ordered = sorted(steps.items())
        curves[method] = [(step, min(items), statistics.fmean(items), max(items)) for step, items in ordered]

    width, height = 1000, 620
    left, top, right, bottom = 85, 65, 30, 80
    plot_width, plot_height = width - left - right, height - top - bottom
    max_step = max(point[0] for curve in curves.values() for point in curve)
    log_values = [math.log10(max(point[index], 1e-12)) for curve in curves.values() for point in curve for index in (1, 2, 3)]
    log_min, log_max = math.floor(min(log_values)), math.ceil(max(log_values))

    def position(step: int, value: float) -> tuple[float, float]:
        x = left + plot_width * step / max(max_step, 1)
        y = top + plot_height * (log_max - math.log10(max(value, 1e-12))) / max(log_max - log_min, 1)
        return x, y

    colors = ["#1565c0", "#d84315", "#2e7d32", "#6a1b9a"]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#202124}.axis{stroke:#404040}.grid{stroke:#d9d9d9;stroke-dasharray:4 4}</style>',
           '<text x="500" y="32" text-anchor="middle" font-size="21" font-weight="bold">Сходимость генетического алгоритма на функции Саломона</text>']
    for tick in range(log_min, log_max + 1):
        y = position(0, 10 ** tick)[1]
        svg.append(f'<line class="grid" x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}"/>')
        svg.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" font-size="13">10^{tick}</text>')
    svg += [f'<line class="axis" x1="{left}" x2="{left}" y1="{top}" y2="{height-bottom}"/>',
            f'<line class="axis" x1="{left}" x2="{width-right}" y1="{height-bottom}" y2="{height-bottom}"/>']
    for step in range(0, max_step + 1, max(1, max_step // 8)):
        x, _ = position(step, 1)
        svg.append(f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle" font-size="13">{step}</text>')
    svg.append(f'<text x="{left + plot_width/2:.1f}" y="{height-25}" text-anchor="middle" font-size="15">Поколение</text>')
    svg.append(f'<text transform="translate(23 {top + plot_height/2:.1f}) rotate(-90)" text-anchor="middle" font-size="15">Лучшее значение f(x), логарифмическая шкала</text>')
    for (method, curve), color in zip(curves.items(), colors):
        lower = [position(step, low) for step, low, _, _ in curve]
        upper = [position(step, high) for step, _, _, high in curve]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in lower + list(reversed(upper)))
        mean = " ".join(f"{x:.1f},{y:.1f}" for x, _, y, _ in [(position(step, value)[0], low, position(step, value)[1], high) for step, low, value, high in curve])
        svg.append(f'<polygon points="{points}" fill="{color}" opacity="0.16"/>')
        svg.append(f'<polyline points="{mean}" fill="none" stroke="{color}" stroke-width="3"/>')
        legend_y = 58 + list(curves).index(method) * 22
        svg.append(f'<line x1="{width-265}" x2="{width-240}" y1="{legend_y}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="{width-232}" y="{legend_y+5}" font-size="13">{method}: среднее; полоса — min/max</text>')
    svg.append('</svg>')
    args.output.write_text("\n".join(svg), encoding="utf-8")


if __name__ == "__main__":
    main()
