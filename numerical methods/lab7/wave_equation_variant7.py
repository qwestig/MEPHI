import argparse

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def u_exact(x: np.ndarray | float, t: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    t_arr = np.asarray(t, dtype=float)
    value = -0.25 * np.exp(x_arr + t_arr - 1.0) + 2.0 / np.cosh(x_arr * t_arr)
    return float(value) if np.ndim(x) == 0 and np.ndim(t) == 0 else value


def forcing(x: np.ndarray | float, t: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    t_arr = np.asarray(t, dtype=float)
    s = x_arr * t_arr
    sech = 1.0 / np.cosh(s)
    tanh = np.tanh(s)
    value = -0.25 * np.exp(x_arr + t_arr - 1.0) + 2.0 * (2.0 * x_arr**2 - t_arr**2) * (2.0 * tanh**2 - 1.0) * sech
    return float(value) if np.ndim(x) == 0 and np.ndim(t) == 0 else value


def phi(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = 2.0 - 0.25 * np.exp(x_arr - 1.0)
    return float(value) if np.ndim(x) == 0 else value


def psi(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = -0.25 * np.exp(x_arr - 1.0)
    return float(value) if np.ndim(x) == 0 else value


def g_left(t: np.ndarray | float) -> np.ndarray | float:
    t_arr = np.asarray(t, dtype=float)
    value = 2.0 - 0.25 * np.exp(t_arr - 1.0)
    return float(value) if np.ndim(t) == 0 else value


def g_right(t: np.ndarray | float) -> np.ndarray | float:
    t_arr = np.asarray(t, dtype=float)
    value = (2.0 + 2.0 * t_arr * np.tanh(t_arr)) / np.cosh(t_arr)
    return float(value) if np.ndim(t) == 0 else value


def grid_1d(a: float, b: float, step: float) -> np.ndarray:
    n_steps = int(round((b - a) / step))
    if not np.isclose(a + n_steps * step, b):
        raise ValueError("(b - a) must be divisible by step")
    return a + np.arange(n_steps + 1, dtype=float) * step


def validate_stability(h: float, tau: float) -> None:
    c = 1.0 / np.sqrt(2.0)
    sigma = c * tau / h
    if sigma > 1.0 + 1e-12:
        raise ValueError(f"Unstable explicit scheme: c*tau/h = {sigma:.4f} > 1")


def apply_right_boundary_first(row: np.ndarray, h: float, t_val: float) -> None:
    gamma = float(g_right(t_val))
    row[-1] = (gamma - row[-2] / h) / (1.0 - 1.0 / h)


def apply_right_boundary_second(row: np.ndarray, h: float, t_val: float) -> None:
    if row.size < 3:
        raise ValueError("Second-order boundary approximation needs at least 3 spatial nodes")
    gamma = float(g_right(t_val))
    row[-1] = (gamma - (2.0 / h) * row[-2] + (0.5 / h) * row[-3]) / (1.0 - 1.5 / h)


def solve_wave_first_order(x: np.ndarray, t: np.ndarray, h: float, tau: float) -> np.ndarray:
    nt, nx = t.size, x.size
    u = np.zeros((nt, nx), dtype=float)
    u[0, :] = phi(x)
    u[:, 0] = g_left(t)

    u[1, 1:-1] = u[0, 1:-1] + tau * psi(x[1:-1])
    apply_right_boundary_first(u[1, :], h, float(t[1]))

    coef = tau**2 / (2.0 * h**2)
    for n in range(1, nt - 1):
        lap = u[n, 2:] - 2.0 * u[n, 1:-1] + u[n, :-2]
        src = forcing(x[1:-1], t[n])
        u[n + 1, 1:-1] = 2.0 * u[n, 1:-1] - u[n - 1, 1:-1] + coef * lap + 0.5 * tau**2 * src
        u[n + 1, 0] = g_left(t[n + 1])
        apply_right_boundary_first(u[n + 1, :], h, float(t[n + 1]))

    return u


def solve_wave_second_order(x: np.ndarray, t: np.ndarray, h: float, tau: float) -> np.ndarray:
    nt, nx = t.size, x.size
    if nx < 3:
        raise ValueError("Second-order scheme needs at least 3 spatial nodes")

    u = np.zeros((nt, nx), dtype=float)
    u[0, :] = phi(x)
    u[:, 0] = g_left(t)

    utt0 = -0.25 * np.exp(x - 1.0) - 2.0 * x**2
    u[1, 1:-1] = u[0, 1:-1] + tau * psi(x[1:-1]) + 0.5 * tau**2 * utt0[1:-1]
    apply_right_boundary_second(u[1, :], h, float(t[1]))

    coef = tau**2 / (2.0 * h**2)
    for n in range(1, nt - 1):
        lap = u[n, 2:] - 2.0 * u[n, 1:-1] + u[n, :-2]
        src = forcing(x[1:-1], t[n])
        u[n + 1, 1:-1] = 2.0 * u[n, 1:-1] - u[n - 1, 1:-1] + coef * lap + 0.5 * tau**2 * src
        u[n + 1, 0] = g_left(t[n + 1])
        apply_right_boundary_second(u[n + 1, :], h, float(t[n + 1]))

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
    print(f"{'1st order IC/BC':<26} {max_err_first:14.6e} {max_err_first_final:14.6e}")
    print(f"{'2nd order IC/BC':<26} {max_err_second:14.6e} {max_err_second_final:14.6e}")


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
    plt.plot(x, first_last, "o-", linewidth=1.2, markersize=3.5, label="IC/BC O(h,tau)")
    plt.plot(x, second_last, "o-", linewidth=1.2, markersize=3.5, label="IC/BC O(h^2,tau^2)")
    plt.xlabel("x")
    plt.ylabel("u(x, T)")
    plt.title(f"Lab 7, variant 7: wave equation profile at T={t_final:.2f}")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def save_error_plot(t: np.ndarray, err_first: np.ndarray, err_second: np.ndarray, filename: str) -> None:
    tiny = 1e-18
    plt.figure(figsize=(10, 6))
    plt.semilogy(t, np.maximum(err_first, tiny), "o-", linewidth=1.2, markersize=3.5, label="IC/BC O(h,tau)")
    plt.semilogy(t, np.maximum(err_second, tiny), "o-", linewidth=1.2, markersize=3.5, label="IC/BC O(h^2,tau^2)")
    plt.xlabel("t")
    plt.ylabel("max_x |u_num - u_exact|")
    plt.title("Max spatial error over time, variant 7")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab 7, variant 7: mixed BVP for inhomogeneous wave equation")
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
    validate_stability(h, tau)

    first = solve_wave_first_order(x, t, h, tau)
    second = solve_wave_second_order(x, t, h, tau)

    tt, xx = np.meshgrid(t, x, indexing="ij")
    exact = u_exact(xx, tt)

    print("Lab 7: mixed BVP for wave equation, variant 7")
    print("2*u_tt = u_xx + f(x,t)")
    print("u(x,0)=2-0.25*exp(x-1), u_t(x,0)=-0.25*exp(x-1)")
    print("u(0,t)=2-0.25*exp(t-1), u(1,t)-u_x(1,t)=(2+2*t*tanh(t))/cosh(t)")
    print("u_exact(x,t)=-0.25*exp(x+t-1)+2/cosh(x*t)")
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
