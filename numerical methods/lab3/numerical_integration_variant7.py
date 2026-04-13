import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def f(x: np.ndarray) -> np.ndarray:
    return x * np.exp(x)


def exact_integral(a: float, b: float) -> float:
    antiderivative = lambda x: (x - 1.0) * np.exp(x)
    return float(antiderivative(b) - antiderivative(a))


def grid(a: float, b: float, n_intervals: int) -> tuple[np.ndarray, float]:
    x = np.linspace(a, b, n_intervals + 1)
    h = (b - a) / n_intervals
    return x, h


def integrate_rectangles_left(a: float, b: float, n_intervals: int) -> float:
    x, h = grid(a, b, n_intervals)
    return float(h * np.sum(f(x[:-1])))


def integrate_rectangles_right(a: float, b: float, n_intervals: int) -> float:
    x, h = grid(a, b, n_intervals)
    return float(h * np.sum(f(x[1:])))


def integrate_rectangles_midpoint(a: float, b: float, n_intervals: int) -> float:
    h = (b - a) / n_intervals
    x_mid = a + (np.arange(n_intervals) + 0.5) * h
    return float(h * np.sum(f(x_mid)))


def integrate_trapezoid(a: float, b: float, n_intervals: int) -> float:
    x, h = grid(a, b, n_intervals)
    y = f(x)
    return float(h * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1]))


def integrate_simpson(a: float, b: float, n_intervals: int) -> float:
    if n_intervals % 2 != 0:
        raise ValueError("Simpson's rule requires an even number of intervals")

    x, h = grid(a, b, n_intervals)
    y = f(x)
    return float(
        h / 3.0 * (y[0] + y[-1] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-2:2]))
    )


def abs_rel_error(approx: float, exact: float) -> tuple[float, float]:
    abs_err = abs(approx - exact)
    rel_err = abs_err / abs(exact) if exact != 0.0 else np.nan
    return abs_err, rel_err


def print_single_grid_report(a: float, b: float, n_intervals: int, exact: float) -> None:
    h = (b - a) / n_intervals
    i_rect_l = integrate_rectangles_left(a, b, n_intervals)
    i_rect_r = integrate_rectangles_right(a, b, n_intervals)
    i_rect = integrate_rectangles_midpoint(a, b, n_intervals)
    i_trap = integrate_trapezoid(a, b, n_intervals)
    i_simp = integrate_simpson(a, b, n_intervals)

    abs_rl, rel_rl = abs_rel_error(i_rect_l, exact)
    abs_rr, rel_rr = abs_rel_error(i_rect_r, exact)
    abs_r, rel_r = abs_rel_error(i_rect, exact)
    abs_t, rel_t = abs_rel_error(i_trap, exact)
    abs_s, rel_s = abs_rel_error(i_simp, exact)

    print("\nMain grid results")
    print("-----------------")
    print(f"n_intervals = {n_intervals}, h = {h:.6f}")
    print(f"{'Method':<26} {'Integral':>16} {'Abs error':>16} {'Rel error':>16}")
    print(
        f"{'Rectangles (left)':<26} {i_rect_l:16.10e} {abs_rl:16.10e} {rel_rl:16.10e}"
    )
    print(
        f"{'Rectangles (right)':<26} {i_rect_r:16.10e} {abs_rr:16.10e} {rel_rr:16.10e}"
    )
    print(
        f"{'Rectangles (midpoint)':<26} {i_rect:16.10e} {abs_r:16.10e} {rel_r:16.10e}"
    )
    print(f"{'Trapezoid':<26} {i_trap:16.10e} {abs_t:16.10e} {rel_t:16.10e}")
    print(f"{'Simpson':<26} {i_simp:16.10e} {abs_s:16.10e} {rel_s:16.10e}")


def convergence_data(a: float, b: float, n_values: list[int], exact: float) -> dict[str, np.ndarray]:
    hs = []
    err_rect_left = []
    err_rect_right = []
    err_rect = []
    err_trap = []
    err_simp = []

    for n in n_values:
        h = (b - a) / n
        hs.append(h)

        i_rect_left = integrate_rectangles_left(a, b, n)
        i_rect_right = integrate_rectangles_right(a, b, n)
        i_rect = integrate_rectangles_midpoint(a, b, n)
        i_trap = integrate_trapezoid(a, b, n)
        i_simp = integrate_simpson(a, b, n)

        err_rect_left.append(abs(i_rect_left - exact))
        err_rect_right.append(abs(i_rect_right - exact))
        err_rect.append(abs(i_rect - exact))
        err_trap.append(abs(i_trap - exact))
        err_simp.append(abs(i_simp - exact))

    return {
        "h": np.array(hs, dtype=float),
        "rect_left": np.array(err_rect_left, dtype=float),
        "rect_right": np.array(err_rect_right, dtype=float),
        "rect": np.array(err_rect, dtype=float),
        "trap": np.array(err_trap, dtype=float),
        "simp": np.array(err_simp, dtype=float),
    }


def print_convergence_table(n_values: list[int], conv: dict[str, np.ndarray]) -> None:
    print("\nConvergence table (max abs error = abs(I_h - I_exact))")
    print(
        "n_intervals       h      err_rect_left    err_rect_right     err_rect_mid"
        "      err_trapezoid      err_simpson"
    )
    for n, h, e_l, e_r, e_m, e_t, e_s in zip(
        n_values,
        conv["h"],
        conv["rect_left"],
        conv["rect_right"],
        conv["rect"],
        conv["trap"],
        conv["simp"],
    ):
        print(
            f"{n:11d} {h:8.5f} {e_l:16.6e} {e_r:17.6e} {e_m:16.6e}"
            f" {e_t:18.6e} {e_s:16.6e}"
        )


def save_error_plot(conv: dict[str, np.ndarray], filename: str) -> None:
    plt.figure(figsize=(9, 6))
    plt.loglog(conv["h"], conv["rect_left"], "o-", label="Rectangles (left), O(h)")
    plt.loglog(conv["h"], conv["rect_right"], "o-", label="Rectangles (right), O(h)")
    plt.loglog(conv["h"], conv["rect"], "o-", label="Rectangles (midpoint), O(h^2)")
    plt.loglog(conv["h"], conv["trap"], "o-", label="Trapezoid, O(h^2)")
    plt.loglog(conv["h"], conv["simp"], "o-", label="Simpson, O(h^4)")

    plt.gca().invert_xaxis()
    plt.xlabel("h")
    plt.ylabel("absolute error")
    plt.title("Error vs grid step (numerical integration, variant 7)")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def _plot_rectangles(ax: Axes, a: float, b: float, n_intervals: int, mode: str, title: str) -> None:
    x, h = grid(a, b, n_intervals)
    x_dense = np.linspace(a, b, 1200)
    y_dense = f(x_dense)

    if mode == "left":
        heights = f(x[:-1])
    elif mode == "right":
        heights = f(x[1:])
    elif mode == "midpoint":
        heights = f(x[:-1] + 0.5 * h)
    else:
        raise ValueError(f"Unknown rectangle mode: {mode}")

    ax.plot(x_dense, y_dense, color="black", linewidth=2.0, label="f(x)")
    ax.bar(
        x[:-1],
        heights,
        width=h,
        align="edge",
        color="#4c72b0",
        edgecolor="#1f4e79",
        alpha=0.28,
        linewidth=1.0,
        label="Rectangles",
    )
    ax.axhline(0.0, color="gray", linewidth=1.0)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()


def _plot_trapezoid(ax: Axes, a: float, b: float, n_intervals: int) -> None:
    x, _ = grid(a, b, n_intervals)
    y = f(x)
    x_dense = np.linspace(a, b, 1200)
    y_dense = f(x_dense)

    ax.plot(x_dense, y_dense, color="black", linewidth=2.0, label="f(x)")
    for i in range(n_intervals):
        xs = [x[i], x[i], x[i + 1], x[i + 1]]
        ys = [0.0, y[i], y[i + 1], 0.0]
        ax.fill(xs, ys, color="#55a868", alpha=0.22)
        ax.plot([x[i], x[i + 1]], [y[i], y[i + 1]], color="#2f6b43", linewidth=1.2)

    ax.axhline(0.0, color="gray", linewidth=1.0)
    ax.set_title("Trapezoid")
    ax.grid(alpha=0.3)
    ax.legend()


def _plot_simpson(ax: Axes, a: float, b: float, n_intervals: int) -> None:
    if n_intervals % 2 != 0:
        raise ValueError("Simpson visualization requires even n_intervals")

    x, _ = grid(a, b, n_intervals)
    y = f(x)
    x_dense = np.linspace(a, b, 1200)
    y_dense = f(x_dense)

    ax.plot(x_dense, y_dense, color="black", linewidth=2.0, label="f(x)")

    for i in range(0, n_intervals, 2):
        xs = x[i : i + 3]
        ys = y[i : i + 3]
        coeffs = np.polyfit(xs, ys, deg=2)
        xq = np.linspace(xs[0], xs[2], 180)
        yq = coeffs[0] * xq**2 + coeffs[1] * xq + coeffs[2]
        ax.fill_between(xq, 0.0, yq, color="#c44e52", alpha=0.2)
        ax.plot(xq, yq, color="#8f2f33", linewidth=1.3)

    ax.axhline(0.0, color="gray", linewidth=1.0)
    ax.set_title("Simpson")
    ax.grid(alpha=0.3)
    ax.legend()


def save_methods_visualization(a: float, b: float, n_intervals: int, filename: str) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True, sharey=True)

    x_dense = np.linspace(a, b, 1200)
    axes[0, 0].plot(x_dense, f(x_dense), color="black", linewidth=2.0, label="f(x)")
    axes[0, 0].axhline(0.0, color="gray", linewidth=1.0)
    axes[0, 0].set_title("Function f(x)")
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend()

    _plot_rectangles(axes[0, 1], a, b, n_intervals, mode="left", title="Rectangles (left)")
    _plot_rectangles(axes[0, 2], a, b, n_intervals, mode="right", title="Rectangles (right)")
    _plot_rectangles(axes[1, 0], a, b, n_intervals, mode="midpoint", title="Rectangles (midpoint)")
    _plot_trapezoid(axes[1, 1], a, b, n_intervals)
    _plot_simpson(axes[1, 2], a, b, n_intervals)

    for ax in axes[1, :]:
        ax.set_xlabel("x")
    for ax in axes[:, 0]:
        ax.set_ylabel("y")

    fig.suptitle(f"Numerical integration schemes on [{a}, {b}], n={n_intervals}", fontsize=12)
    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)


def main() -> None:
    a, b = -2.0, 1.0
    n_intervals_main = 40
    n_values = [10, 20, 40, 80, 160, 320]
    n_intervals_visual = 8

    exact = exact_integral(a, b)

    print(f"Exact integral I = {exact:.10e}")

    print_single_grid_report(a, b, n_intervals_main, exact)

    conv = convergence_data(a, b, n_values, exact)
    print_convergence_table(n_values, conv)

    plot_name = "error_vs_h_variant7.png"
    save_error_plot(conv, plot_name)
    print(f"Saved plot: {plot_name}")

    methods_plot_name = "integration_methods_variant7.png"
    save_methods_visualization(a, b, n_intervals_visual, methods_plot_name)
    print(f"Saved plot: {methods_plot_name}")


if __name__ == "__main__":
    main()
