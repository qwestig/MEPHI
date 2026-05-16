import argparse

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def u_exact(x: np.ndarray | float, t: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    t_arr = np.asarray(t, dtype=float)
    value = 1.5 * np.exp(x_arr * t_arr) * np.cos(x_arr * t_arr) - x_arr**2
    return float(value) if np.ndim(x) == 0 and np.ndim(t) == 0 else value


def forcing(x: np.ndarray | float, t: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    t_arr = np.asarray(t, dtype=float)
    s = x_arr * t_arr
    value = 2.0 + 1.5 * np.exp(s) * (x_arr * np.cos(s) + (2.0 * t_arr**2 - x_arr) * np.sin(s))
    return float(value) if np.ndim(x) == 0 and np.ndim(t) == 0 else value


def phi(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = 1.5 - x_arr**2
    return float(value) if np.ndim(x) == 0 else value


def g_left(t: np.ndarray | float) -> np.ndarray | float:
    t_arr = np.asarray(t, dtype=float)
    value = 1.5 - 3.0 * t_arr
    return float(value) if np.ndim(t) == 0 else value


def g_right(t: np.ndarray | float) -> np.ndarray | float:
    t_arr = np.asarray(t, dtype=float)
    value = 1.5 * np.exp(t_arr) * np.cos(t_arr) - 1.0
    return float(value) if np.ndim(t) == 0 else value


def grid_1d(a: float, b: float, step: float) -> np.ndarray:
    n_steps = int(round((b - a) / step))
    if not np.isclose(a + n_steps * step, b):
        raise ValueError("(b - a) must be divisible by step")
    return a + np.arange(n_steps + 1, dtype=float) * step


def thomas_solve(lower: np.ndarray, diag: np.ndarray, upper: np.ndarray, rhs_vec: np.ndarray) -> np.ndarray:
    n = diag.size
    c_star = np.zeros(n, dtype=float)
    d_star = np.zeros(n, dtype=float)

    c_star[0] = upper[0] / diag[0]
    d_star[0] = rhs_vec[0] / diag[0]

    for i in range(1, n):
        denom = diag[i] - lower[i] * c_star[i - 1]
        if i < n - 1:
            c_star[i] = upper[i] / denom
        d_star[i] = (rhs_vec[i] - lower[i] * d_star[i - 1]) / denom

    result = np.zeros(n, dtype=float)
    result[-1] = d_star[-1]
    for i in range(n - 2, -1, -1):
        result[i] = d_star[i] - c_star[i] * result[i + 1]
    return result


def interior_rhs(prev: np.ndarray, x: np.ndarray, t_n: float, t_np1: float, r: float, tau: float) -> np.ndarray:
    rhs = np.zeros_like(prev)
    f_avg = 0.5 * tau * (forcing(x[1:-1], t_n) + forcing(x[1:-1], t_np1))
    rhs[1:-1] = prev[1:-1] + r * (prev[2:] - 2.0 * prev[1:-1] + prev[:-2]) + f_avg
    return rhs


def build_system_first_order(
    x: np.ndarray,
    prev: np.ndarray,
    t_n: float,
    t_np1: float,
    h: float,
    tau: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    nx = x.size
    r = tau / (2.0 * h**2)
    lower = np.zeros(nx, dtype=float)
    diag = np.zeros(nx, dtype=float)
    upper = np.zeros(nx, dtype=float)
    rhs = interior_rhs(prev, x, t_n, t_np1, r, tau)

    lower[1:-1] = -r
    diag[1:-1] = 1.0 + 2.0 * r
    upper[1:-1] = -r

    diag[0] = 1.0 + 2.0 / h
    upper[0] = -2.0 / h
    rhs[0] = g_left(t_np1)

    diag[-1] = 1.0
    rhs[-1] = g_right(t_np1)
    return lower, diag, upper, rhs


def build_system_second_order(
    x: np.ndarray,
    prev: np.ndarray,
    t_n: float,
    t_np1: float,
    h: float,
    tau: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    nx = x.size
    if nx < 4:
        raise ValueError("Second-order boundary approximation needs at least 4 spatial nodes")

    r = tau / (2.0 * h**2)
    lower = np.zeros(nx, dtype=float)
    diag = np.zeros(nx, dtype=float)
    upper = np.zeros(nx, dtype=float)
    rhs = interior_rhs(prev, x, t_n, t_np1, r, tau)

    lower[1:-1] = -r
    diag[1:-1] = 1.0 + 2.0 * r
    upper[1:-1] = -r

    a0 = 1.0 + 3.0 / h
    a1 = -4.0 / h
    a2 = 1.0 / h
    g = g_left(t_np1)

    a_int = lower[1]
    b_int = diag[1]
    c_int = upper[1]
    f_int = rhs[1]

    diag[0] = a0 - a2 * a_int / c_int
    upper[0] = a1 - a2 * b_int / c_int
    rhs[0] = g - a2 * f_int / c_int

    diag[-1] = 1.0
    rhs[-1] = g_right(t_np1)
    return lower, diag, upper, rhs


def solve_heat_first_order(x: np.ndarray, t: np.ndarray, h: float, tau: float) -> np.ndarray:
    nt, nx = t.size, x.size
    u = np.zeros((nt, nx), dtype=float)
    u[0, :] = phi(x)
    u[0, -1] = g_right(t[0])

    for n in range(nt - 1):
        lower, diag, upper, rhs = build_system_first_order(x, u[n, :], float(t[n]), float(t[n + 1]), h, tau)
        u[n + 1, :] = thomas_solve(lower, diag, upper, rhs)
    return u


def solve_heat_second_order(x: np.ndarray, t: np.ndarray, h: float, tau: float) -> np.ndarray:
    nt, nx = t.size, x.size
    u = np.zeros((nt, nx), dtype=float)
    u[0, :] = phi(x)
    u[0, -1] = g_right(t[0])

    for n in range(nt - 1):
        lower, diag, upper, rhs = build_system_second_order(x, u[n, :], float(t[n]), float(t[n + 1]), h, tau)
        u[n + 1, :] = thomas_solve(lower, diag, upper, rhs)
    return u


def print_final_time_table(x: np.ndarray, exact_last: np.ndarray, first_last: np.ndarray, second_last: np.ndarray, t_final: float) -> None:
    print(f"\nTable at final time t = {t_final:.2f}")
    print(f"{'x':>7} {'u_exact':>14} {'u_1st':>14} {'|err|':>11} {'u_2nd':>14} {'|err|':>11}")
    for i in range(x.size):
        err1 = abs(first_last[i] - exact_last[i])
        err2 = abs(second_last[i] - exact_last[i])
        print(f"{x[i]:7.2f} {exact_last[i]:14.8f} {first_last[i]:14.8f} {err1:11.3e} {second_last[i]:14.8f} {err2:11.3e}")


def print_error_report(exact: np.ndarray, first: np.ndarray, second: np.ndarray) -> None:
    max_err_first = np.max(np.abs(first - exact))
    max_err_second = np.max(np.abs(second - exact))
    max_err_first_final = np.max(np.abs(first[-1, :] - exact[-1, :]))
    max_err_second_final = np.max(np.abs(second[-1, :] - exact[-1, :]))

    print("\nMax absolute error")
    print(f"{'Approximation':<26} {'Global max':>14} {'At t=T':>14}")
    print(f"{'Boundary O(h)':<26} {max_err_first:14.6e} {max_err_first_final:14.6e}")
    print(f"{'Boundary O(h^2)':<26} {max_err_second:14.6e} {max_err_second_final:14.6e}")


def save_solution_plot(
    x: np.ndarray,
    exact_last: np.ndarray,
    first_last: np.ndarray,
    second_last: np.ndarray,
    t_final: float,
    filename: str,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(x, exact_last, color="black", linewidth=2.2, label=f"exact u(x, {t_final:.2f})")
    plt.plot(x, first_last, "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h)")
    plt.plot(x, second_last, "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h^2)")
    plt.xlabel("x")
    plt.ylabel("u(x, T)")
    plt.title(f"Lab 8, variant 7: heat equation profile at T={t_final:.2f}")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def save_error_plot(t: np.ndarray, err_first: np.ndarray, err_second: np.ndarray, filename: str) -> None:
    tiny = 1e-18
    plt.figure(figsize=(10, 6))
    plt.semilogy(t, np.maximum(err_first, tiny), "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h)")
    plt.semilogy(t, np.maximum(err_second, tiny), "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h^2)")
    plt.xlabel("t")
    plt.ylabel("max_x |u_num - u_exact|")
    plt.title("Max spatial error over time, variant 7")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab 8, variant 7: mixed BVP for inhomogeneous heat equation")
    parser.add_argument("--tau", type=float, default=0.05, help="Time step (default: 0.05)")
    parser.add_argument("--T", type=float, default=1.0, help="Final time (default: 1.0)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    h = 0.05
    tau = float(args.tau)
    t_final = float(args.T)
    if tau <= 0.0:
        raise ValueError("tau must be positive")
    if t_final <= 0.0:
        raise ValueError("T must be positive")

    x = grid_1d(0.0, 1.0, h)
    t = grid_1d(0.0, t_final, tau)

    first = solve_heat_first_order(x, t, h, tau)
    second = solve_heat_second_order(x, t, h, tau)

    tt, xx = np.meshgrid(t, x, indexing="ij")
    exact = u_exact(xx, tt)

    print("Lab 8: mixed BVP for heat equation, variant 7")
    print("u_t = u_xx + f(x,t)")
    print("u(x,0)=1.5-x^2")
    print("u(0,t)-2*u_x(0,t)=1.5-3*t, u(1,t)=1.5*exp(t)*cos(t)-1")
    print("u_exact(x,t)=1.5*exp(x*t)*cos(x*t)-x^2")
    print(f"Grid: h = {h:.2f}, tau = {tau:.2f}, T = {t_final:.2f}, Nx = {x.size}, Nt = {t.size}")

    print_final_time_table(x, exact[-1, :], first[-1, :], second[-1, :], t_final)
    print_error_report(exact, first, second)

    solution_plot_name = "solution_variant7.png"
    error_plot_name = "error_variant7.png"
    save_solution_plot(x, exact[-1, :], first[-1, :], second[-1, :], t_final, solution_plot_name)
    err_first_t = np.max(np.abs(first - exact), axis=1)
    err_second_t = np.max(np.abs(second - exact), axis=1)
    save_error_plot(t, err_first_t, err_second_t, error_plot_name)
    print(f"Saved plot: {solution_plot_name}")
    print(f"Saved plot: {error_plot_name}")


if __name__ == "__main__":
    main()
