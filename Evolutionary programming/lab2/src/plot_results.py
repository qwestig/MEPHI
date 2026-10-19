"""Create report figures from the saved experiment, without rerunning the GA."""

import argparse
from collections import defaultdict
import csv
import json
import os
from pathlib import Path
import statistics
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lab2-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

from problem import Problem

ROOT = Path(__file__).resolve().parents[1]
LABELS = {"random_feasible": "Случайный + ремонт", "penalty_swap": "Штраф + обмен",
          "penalty_inversion": "Штраф + инверсия", "repair_swap": "Ремонт + обмен",
          "repair_inversion": "Ремонт + инверсия"}
COLORS = ["#8795a5", "#2c71b8", "#b276b2", "#db8c24", "#21866c"]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    output = args.results
    snapshot = json.loads((output / "experiment_snapshot.json").read_text(encoding="utf-8"))
    problem = Problem(snapshot["instance"])
    summaries = read_csv(output / "summary.csv")
    runs = read_csv(output / "runs.csv")
    methods = [row["method"] for row in summaries]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none"})

    def save(fig, name):
        fig.savefig(output / f"{name}.svg", bbox_inches="tight")
        fig.savefig(output / f"{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    grouped = defaultdict(list)
    for row in read_csv(output / "trajectories.csv"):
        grouped[row["method"], int(row["evaluations"])].append(float(row["best_feasible_distance"]))
    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    for method, color in zip(methods, COLORS):
        xs = sorted(count for name, count in grouped if name == method)
        ys = [grouped[method, count] for count in xs]
        ax.plot(xs, [statistics.fmean(values) for values in ys], color=color, label=LABELS[method], lw=2)
        ax.fill_between(xs, [min(values) for values in ys], [max(values) for values in ys], color=color, alpha=0.09)
    ax.set(title="Сходимость: среднее и диапазон 20 запусков",
           xlabel="Оценки целевой функции (включая начальную популяцию)",
           ylabel="Длина лучшего допустимого маршрута, км")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=9, loc="upper right")
    save(fig, "convergence")

    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    values = [[float(row["distance"]) for row in runs if row["method"] == method] for method in methods]
    boxes = ax.boxplot(values, tick_labels=[LABELS[m].replace(" + ", "\n+ ") for m in methods], patch_artist=True)
    for box, color in zip(boxes["boxes"], COLORS):
        box.set_facecolor(color)
        box.set_alpha(0.4)
    for index, series in enumerate(values, 1):
        ax.scatter([index + ((i % 5) - 2) * 0.035 for i in range(len(series))], series,
                   s=15, color=COLORS[index - 1], alpha=0.75, zorder=3)
    greedy = problem.evaluate(problem.greedy()).distance
    ax.axhline(greedy, color="#57606a", linestyle="--", label=f"Жадная эвристика: {greedy:.2f} км")
    ax.set(title="Итоговое качество при бюджете 10 000 оценок", ylabel="Суммарная длина, км")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(fontsize=9)
    save(fig, "quality")

    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    x = list(range(len(methods)))
    ax.bar([i - 0.18 for i in x], [100 * float(r["mean_feasible_fraction"]) for r in summaries],
           width=0.36, label="Среди всех оценённых кандидатов", color="#2c71b8")
    ax.bar([i + 0.18 for i in x], [100 * float(r["mean_final_feasible_fraction"]) for r in summaries],
           width=0.36, label="В последней популяции", color="#21866c")
    ax.set_xticks(x, [LABELS[m].replace(" + ", "\n+ ") for m in methods])
    ax.set(ylim=(0, 119), ylabel="Допустимые решения, %", title="Допустимость после обработки ограничений")
    ax.legend(fontsize=9, loc="upper center")
    ax.grid(axis="y", alpha=0.2)
    save(fig, "feasibility")

    solutions = json.loads((output / "best_solutions.json").read_text(encoding="utf-8"))
    method = min(solutions, key=lambda name: solutions[name]["distance"])
    best = solutions[method]
    fig, ax = plt.subplots(figsize=(9, 8), layout="constrained")
    for index, (route, load) in enumerate(zip(best["routes"], best["loads"])):
        coords = [problem.nodes[i] for i in [0, *route, 0]]
        ax.plot([p["x"] for p in coords], [p["y"] for p in coords], "o-", color=COLORS[index + 1],
                lw=1.8, ms=5, label=f"Машина {index + 1}: {load}/{problem.capacity} контейнеров")
        for a, b in zip(coords, coords[1:]):
            ax.annotate("", xy=(a["x"] + 0.58 * (b["x"] - a["x"]), a["y"] + 0.58 * (b["y"] - a["y"])),
                        xytext=(a["x"] + 0.42 * (b["x"] - a["x"]), a["y"] + 0.42 * (b["y"] - a["y"])),
                        arrowprops={"arrowstyle": "->", "color": COLORS[index + 1]})
    offsets = {1: (4, 4), 3: (-15, 4), 13: (-18, -13), 14: (5, -8), 19: (-18, -12)}
    for point in problem.nodes[1:]:
        ax.annotate(str(point["id"]), (point["x"], point["y"]), xytext=offsets.get(point["id"], (5, 6)),
                    textcoords="offset points", fontsize=9, bbox={"facecolor": "white", "alpha": 0.65, "edgecolor": "none", "pad": 1})
    depot = problem.nodes[0]
    ax.scatter([depot["x"]], [depot["y"]], marker="s", s=100, c="black", zorder=5)
    ax.annotate("Депо", (depot["x"], depot["y"]), xytext=(6, -16), textcoords="offset points")
    ax.set(title=f"Лучшее найденное решение: {best['distance']:.2f} км\n{LABELS[method]}, seed = {best['seed']}",
           xlabel="x, км", ylabel="y, км", xlim=(0, 103), ylim=(0, 105), aspect="equal")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=9)
    ax.grid(alpha=0.2)
    save(fig, "best_routes")

    fig, ax = plt.subplots(figsize=(9, 8), layout="constrained")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    boxes = [(0.25, 0.91, 0.5, 0.055, "Данные, параметры и seed"),
             (0.15, 0.79, 0.7, 0.07, "Начальная популяция: жадное решение\n+ случайные перестановки"),
             (0.15, 0.63, 0.7, 0.09, "Ремонт → длина / штраф → длина + λ · перегрузка\nОбновить архив лучшего допустимого решения"),
             (0.22, 0.29, 0.56, 0.08, "Элитизм, турнир, OX,\nобмен или инверсия"),
             (0.15, 0.09, 0.7, 0.08, "Лучшее допустимое решение,\nCSV, графики и отчёт")]
    for x0, y0, width, height, label in boxes:
        ax.add_patch(FancyBboxPatch((x0, y0), width, height, boxstyle="round,pad=0.006",
                                   facecolor="#eaf2f8", edgecolor="#2c71b8"))
        ax.text(x0 + width / 2, y0 + height / 2, label, ha="center", va="center", fontsize=10)
    ax.add_patch(Polygon([(0.5, 0.565), (0.71, 0.5), (0.5, 0.435), (0.29, 0.5)],
                         facecolor="#fff3d6", edgecolor="#b77916"))
    ax.text(0.5, 0.5, "Бюджет\nисчерпан?", ha="center", va="center", fontsize=10)

    def arrow(points):
        ax.plot([p[0] for p in points], [p[1] for p in points], color="#334155", lw=1.2)
        ax.annotate("", xy=points[-1], xytext=points[-2],
                    arrowprops={"arrowstyle": "->", "color": "#334155", "shrinkB": 0})

    for y1, y2 in [(0.904, 0.866), (0.784, 0.726), (0.624, 0.565), (0.435, 0.376)]:
        arrow([(0.5, y1), (0.5, y2)])
    arrow([(0.214, 0.33), (0.07, 0.33), (0.07, 0.675), (0.144, 0.675)])
    arrow([(0.71, 0.5), (0.94, 0.5), (0.94, 0.13), (0.856, 0.13)])
    ax.text(0.53, 0.405, "Нет", fontsize=10)
    ax.text(0.80, 0.515, "Да", fontsize=10)
    ax.set_title("Блок-схема генетического алгоритма", pad=15)
    save(fig, "algorithm")
    print(f"Figures saved to {output}")


if __name__ == "__main__":
    main()
