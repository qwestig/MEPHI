import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def f(x: np.ndarray) -> np.ndarray:
    return np.log(1.0 + np.sin(x) ** 2)


def f_prime_exact(x: np.ndarray) -> np.ndarray:
    return np.sin(2.0 * x) / (1.0 + np.sin(x) ** 2)

def f_second_exact(x: np.ndarray) -> np.ndarray:
    num = 2.0 * np.cos(2.0 * x) * (1.0 + np.sin(x) ** 2) - np.sin(2.0 * x) ** 2
    den = (1.0 + np.sin(x) ** 2) ** 2
    return num / den


def grid(a: float, b: float, n_intervals: int) -> tuple[np.ndarray, float]:
    x = np.linspace(a, b, n_intervals + 1)
    h = (b - a) / n_intervals
    return x, h


def first_derivative_forward(y: np.ndarray, h: float) -> np.ndarray:
    d = np.full_like(y, np.nan, dtype=float)
    d[:-1] = (y[1:] - y[:-1]) / h
    return d


def first_derivative_central(y: np.ndarray, h: float) -> np.ndarray:
    d = np.full_like(y, np.nan, dtype=float)
    d[1:-1] = (y[2:] - y[:-2]) / (2.0 * h)
    return d


def second_derivative_central_o2(y: np.ndarray, h: float) -> np.ndarray:
    d2 = np.full_like(y, np.nan, dtype=float)
    d2[1:-1] = (y[2:] - 2.0 * y[1:-1] + y[:-2]) / (h**2)
    return d2


def second_derivative_central_o4(y: np.ndarray, h: float) -> np.ndarray:
    d2 = np.full_like(y, np.nan, dtype=float)
    d2[2:-2] = (-y[4:] + 16.0 * y[3:-1] - 30.0 * y[2:-2] + 16.0 * y[1:-3] - y[:-4]) / (
        12.0 * h**2
    )
    return d2


def error_stats(approx: np.ndarray, exact: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(approx)
    err = np.abs(approx[mask] - exact[mask])
    return float(np.max(err)), float(np.mean(err))


def print_node_table(
    x: np.ndarray,
    exact: np.ndarray,
    approx: np.ndarray,
    title: str,
    rows_limit: int = 15,
) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(f"{'x':>11} {'exact':>16} {'approx':>16} {'|err|':>16}")

    shown = 0
    for xi, ex, ap in zip(x, exact, approx):
        if not np.isfinite(ap):
            continue
        print(f"{xi:11.6f} {ex:16.10e} {ap:16.10e} {abs(ex-ap):16.10e}")
        shown += 1
        if shown >= rows_limit:
            break

    max_err, mean_err = error_stats(approx, exact)
    print(f"max error:  {max_err:.10e}")
    print(f"mean error: {mean_err:.10e}")


def save_derivative_plots(
    x: np.ndarray,
    exact_1: np.ndarray,
    exact_2: np.ndarray,
    d1_forward: np.ndarray,
    d1_central: np.ndarray,
    d2_o2: np.ndarray,
    d2_o4: np.ndarray,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)

    axes[0, 0].plot(x, exact_1, color="black", linewidth=2.0, label="exact f'(x)")
    axes[0, 0].plot(x, d1_forward, "--", linewidth=1.4, label="forward O(h)")
    axes[0, 0].plot(x, d1_central, "-.", linewidth=1.4, label="central O(h^2)")
    axes[0, 0].set_title("First derivative")
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend()

    e_fwd = np.abs(d1_forward - exact_1)
    e_ctr = np.abs(d1_central - exact_1)
    axes[1, 0].plot(x, e_fwd, linewidth=1.5, label="|err| forward")
    axes[1, 0].plot(x, e_ctr, linewidth=1.5, label="|err| central")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_xlabel("x")
    axes[1, 0].set_title("Error for f'(x)")
    axes[1, 0].grid(alpha=0.3)
    axes[1, 0].legend()

    axes[0, 1].plot(x, exact_2, color="black", linewidth=2.0, label="exact f''(x)")
    axes[0, 1].plot(x, d2_o2, "--", linewidth=1.4, label="central O(h^2)")
    axes[0, 1].plot(x, d2_o4, "-.", linewidth=1.4, label="central O(h^4)")
    axes[0, 1].set_title("Second derivative")
    axes[0, 1].grid(alpha=0.3)
    axes[0, 1].legend()

    e_o2 = np.abs(d2_o2 - exact_2)
    e_o4 = np.abs(d2_o4 - exact_2)
    axes[1, 1].plot(x, e_o2, linewidth=1.5, label="|err| O(h^2)")
    axes[1, 1].plot(x, e_o4, linewidth=1.5, label="|err| O(h^4)")
    axes[1, 1].set_yscale("log")
    axes[1, 1].set_xlabel("x")
    axes[1, 1].set_title("Error for f''(x)")
    axes[1, 1].grid(alpha=0.3)
    axes[1, 1].legend()

    fig.tight_layout()
    fig.savefig("derivatives_variant7_main_grid.png", dpi=200)
    plt.close(fig)


def save_convergence_plot(a: float, b: float, n_values: list[int]) -> None:
    hs = []
    errs_fwd = []
    errs_ctr1 = []
    errs_o2 = []
    errs_o4 = []

    for n in n_values:
        x, h = grid(a, b, n)
        y = f(x)

        d1_fwd = first_derivative_forward(y, h)
        d1_ctr = first_derivative_central(y, h)
        d2_o2 = second_derivative_central_o2(y, h)
        d2_o4 = second_derivative_central_o4(y, h)

        ex1 = f_prime_exact(x)
        ex2 = f_second_exact(x)

        hs.append(h)
        errs_fwd.append(error_stats(d1_fwd, ex1)[0])
        errs_ctr1.append(error_stats(d1_ctr, ex1)[0])
        errs_o2.append(error_stats(d2_o2, ex2)[0])
        errs_o4.append(error_stats(d2_o4, ex2)[0])

    hs_arr = np.array(hs)

    plt.figure(figsize=(9, 6))
    plt.loglog(hs_arr, np.array(errs_fwd), "o-", label="f' forward O(h)")
    plt.loglog(hs_arr, np.array(errs_ctr1), "o-", label="f' central O(h^2)")
    plt.loglog(hs_arr, np.array(errs_o2), "o-", label="f'' central O(h^2)")
    plt.loglog(hs_arr, np.array(errs_o4), "o-", label="f'' central O(h^4)")

    plt.gca().invert_xaxis()
    plt.xlabel("h")
    plt.ylabel("max absolute error")
    plt.title("Error vs grid step (variant 7)")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig("error_vs_h_variant7.png", dpi=200)
    plt.close()

    print("\nConvergence table (max error):")
    print("n_intervals       h        err_fwd_f1      err_ctr_f1      err_o2_f2      err_o4_f2")
    for n, h, e1, e2, e3, e4 in zip(n_values, hs, errs_fwd, errs_ctr1, errs_o2, errs_o4):
        print(f"{n:11d} {h:8.5f} {e1:14.6e} {e2:14.6e} {e3:14.6e} {e4:14.6e}")


def main() -> None:
    a, b = -1.5, 1.5
    n_intervals_main = 60
    n_values = [20, 40, 80, 160, 320]

    x, h = grid(a, b, n_intervals_main)
    y = f(x)

    d1_fwd = first_derivative_forward(y, h)
    d1_ctr = first_derivative_central(y, h)
    d2_o2 = second_derivative_central_o2(y, h)
    d2_o4 = second_derivative_central_o4(y, h)

    ex1 = f_prime_exact(x)
    ex2 = f_second_exact(x)

    print("Lab 2: Numerical differentiation, variant 7")
    print("f(x) = ln(1 + sin^2(x)),  x in [-1.5, 1.5]")
    print(f"Main grid: n_intervals = {n_intervals_main}, h = {h:.6f}")

    print_node_table(x, ex1, d1_fwd, "First derivative: forward differences")
    print_node_table(x, ex1, d1_ctr, "First derivative: central differences")
    print_node_table(x, ex2, d2_o2, "Second derivative: central O(h^2)")
    print_node_table(x, ex2, d2_o4, "Second derivative: central O(h^4)")

    save_derivative_plots(x, ex1, ex2, d1_fwd, d1_ctr, d2_o2, d2_o4)
    save_convergence_plot(a, b, n_values)

    print("Saved plot: derivatives_variant7_main_grid.png")
    print("Saved plot: error_vs_h_variant7.png")


if __name__ == "__main__":
    main()
