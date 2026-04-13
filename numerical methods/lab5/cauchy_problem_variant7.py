import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def u_exact(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = np.sqrt(np.cos(x_arr)) + np.exp(-x_arr)
    return float(value) if np.ndim(x) == 0 else value

def du_exact(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = -np.sin(x_arr) / (2.0 * np.sqrt(np.cos(x_arr))) - np.exp(-x_arr)
    return float(value) if np.ndim(x) == 0 else value

def rhs(x: float, y: np.ndarray) -> np.ndarray:
    u, v = float(y[0]), float(y[1])
    a = 0.5 * np.tan(x)
    source = -0.5 * np.sqrt(np.cos(x)) * (3.0 + np.tan(x))
    return np.array([v, a * v + (1.0 + a) * u + source], dtype=float)


def grid(a: float, b: float, h: float) -> np.ndarray:
    n_steps = int(round((b - a) / h))
    if not np.isclose(a + n_steps * h, b):
        raise ValueError("(b - a) must be divisible by h")
    return a + np.arange(n_steps + 1, dtype=float) * h


def euler_method(x: np.ndarray, y0: np.ndarray) -> np.ndarray:
    y = np.zeros((x.size, y0.size), dtype=float)
    y[0] = y0
    h = x[1] - x[0]
    for n in range(x.size - 1):
        y[n + 1] = y[n] + h * rhs(float(x[n]), y[n])
    return y


def rk4_step(xn: float, yn: np.ndarray, h: float) -> np.ndarray:
    k1 = rhs(xn, yn)
    k2 = rhs(xn + 0.5 * h, yn + 0.5 * h * k1)
    k3 = rhs(xn + 0.5 * h, yn + 0.5 * h * k2)
    k4 = rhs(xn + h, yn + h * k3)
    return yn + h * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def rk4_method(x: np.ndarray, y0: np.ndarray) -> np.ndarray:
    y = np.zeros((x.size, y0.size), dtype=float)
    y[0] = y0
    h = x[1] - x[0]
    for n in range(x.size - 1):
        y[n + 1] = rk4_step(float(x[n]), y[n], h)
    return y


def adams3_method(x: np.ndarray, y0: np.ndarray) -> np.ndarray:
    if x.size < 3:
        raise ValueError("Adams 3 requires at least three nodes")

    y = np.zeros((x.size, y0.size), dtype=float)
    y[0] = y0
    h = x[1] - x[0]

    y[1] = rk4_step(float(x[0]), y[0], h)
    y[2] = rk4_step(float(x[1]), y[1], h)

    for n in range(2, x.size - 1):
        f_n = rhs(float(x[n]), y[n])
        f_n1 = rhs(float(x[n - 1]), y[n - 1])
        f_n2 = rhs(float(x[n - 2]), y[n - 2])
        y[n + 1] = y[n] + h * (23.0 * f_n - 16.0 * f_n1 + 5.0 * f_n2) / 12.0

    return y


def print_solution_tables(
    x: np.ndarray,
    y_exact: np.ndarray,
    euler: np.ndarray,
    rk4: np.ndarray,
    adams: np.ndarray,
) -> None:
    print("\nTable for u(x)")
    print(
        f"{'x':>7} {'u_exact':>14} {'u_euler':>14} {'|err|':>11} "
        f"{'u_rk4':>14} {'|err|':>11} {'u_adams3':>14} {'|err|':>11}"
    )
    for i in range(x.size):
        print(
            f"{x[i]:7.2f} {y_exact[i, 0]:14.8f} {euler[i, 0]:14.8f} {abs(euler[i, 0]-y_exact[i, 0]):11.3e} "
            f"{rk4[i, 0]:14.8f} {abs(rk4[i, 0]-y_exact[i, 0]):11.3e} {adams[i, 0]:14.8f} {abs(adams[i, 0]-y_exact[i, 0]):11.3e}"
        )

    print("\nTable for u'(x)")
    print(
        f"{'x':>7} {'u_exact\'':>14} {'u_euler\'':>14} {'|err|':>11} "
        f"{'u_rk4\'':>14} {'|err|':>11} {'u_adams3\'':>14} {'|err|':>11}"
    )
    for i in range(x.size):
        print(
            f"{x[i]:7.2f} {y_exact[i, 1]:14.8f} {euler[i, 1]:14.8f} {abs(euler[i, 1]-y_exact[i, 1]):11.3e} "
            f"{rk4[i, 1]:14.8f} {abs(rk4[i, 1]-y_exact[i, 1]):11.3e} {adams[i, 1]:14.8f} {abs(adams[i, 1]-y_exact[i, 1]):11.3e}"
        )


def print_max_error_report(y_exact: np.ndarray, euler: np.ndarray, rk4: np.ndarray, adams: np.ndarray) -> None:
    euler_u = np.max(np.abs(euler[:, 0] - y_exact[:, 0]))
    rk4_u = np.max(np.abs(rk4[:, 0] - y_exact[:, 0]))
    adams_u = np.max(np.abs(adams[:, 0] - y_exact[:, 0]))

    euler_v = np.max(np.abs(euler[:, 1] - y_exact[:, 1]))
    rk4_v = np.max(np.abs(rk4[:, 1] - y_exact[:, 1]))
    adams_v = np.max(np.abs(adams[:, 1] - y_exact[:, 1]))

    print("\nMax absolute error on h=0.05")
    print(f"{'Method':<10} {'max|u-u_exact|':>18} {'max|u\'-u_exact\'|':>20}")
    print(f"{'Euler':<10} {euler_u:18.8e} {euler_v:20.8e}")
    print(f"{'RK4':<10} {rk4_u:18.8e} {rk4_v:20.8e}")
    print(f"{'Adams3':<10} {adams_u:18.8e} {adams_v:20.8e}")


def runge_estimate_for_rk4(x_fine: np.ndarray, rk4_fine: np.ndarray, x_coarse: np.ndarray, rk4_coarse: np.ndarray) -> None:
    p = 4
    denom = 2**p - 1

    idx = np.arange(0, x_fine.size, 2)
    if idx.size != x_coarse.size:
        raise ValueError("Grid mismatch for Runge estimate")

    u_exact_vals = u_exact(x_coarse)
    print("\nRunge estimate for RK4 (u component, coarse nodes)")
    print(f"{'x':>7} {'u_h=0.1':>14} {'u_h=0.05':>14} {'R_Runge':>14} {'true |err|':>14}")
    for i, j in enumerate(idx):
        rr = abs(rk4_fine[j, 0] - rk4_coarse[i, 0]) / denom
        true_err = abs(rk4_fine[j, 0] - u_exact_vals[i])
        print(
            f"{x_coarse[i]:7.2f} {rk4_coarse[i, 0]:14.8f} {rk4_fine[j, 0]:14.8f} {rr:14.6e} {true_err:14.6e}"
        )


def save_solution_plot(
    x: np.ndarray,
    y_exact: np.ndarray,
    euler: np.ndarray,
    rk4: np.ndarray,
    adams: np.ndarray,
    filename: str,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(x, y_exact[:, 0], color="black", linewidth=2.2, label="exact u(x)")
    plt.plot(x, euler[:, 0], "o-", linewidth=1.2, markersize=3.5, label="Euler")
    plt.plot(x, rk4[:, 0], "o-", linewidth=1.2, markersize=3.5, label="RK4")
    plt.plot(x, adams[:, 0], "o-", linewidth=1.2, markersize=3.5, label="Adams 3")
    plt.xlabel("x")
    plt.ylabel("u(x)")
    plt.title("Lab 5, variant 7: Cauchy problem solution on [0, 1], h=0.05")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def save_error_plot(
    x: np.ndarray,
    y_exact: np.ndarray,
    euler: np.ndarray,
    rk4: np.ndarray,
    adams: np.ndarray,
    filename: str,
) -> None:
    e_euler = np.abs(euler[:, 0] - y_exact[:, 0])
    e_rk4 = np.abs(rk4[:, 0] - y_exact[:, 0])
    e_adams = np.abs(adams[:, 0] - y_exact[:, 0])

    tiny = 1e-18
    plt.figure(figsize=(10, 6))
    plt.semilogy(x, np.maximum(e_euler, tiny), "o-", linewidth=1.2, markersize=3.5, label="Euler")
    plt.semilogy(x, np.maximum(e_rk4, tiny), "o-", linewidth=1.2, markersize=3.5, label="RK4")
    plt.semilogy(x, np.maximum(e_adams, tiny), "o-", linewidth=1.2, markersize=3.5, label="Adams 3")
    plt.xlabel("x")
    plt.ylabel("|u_num - u_exact|")
    plt.title("Absolute error for u(x), variant 7")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def main() -> None:
    a, b = 0.0, 1.0
    h_fine = 0.05
    h_coarse = 0.1
    y0 = np.array([2.0, -1.0], dtype=float)

    x_fine = grid(a, b, h_fine)
    y_exact_fine = np.column_stack((u_exact(x_fine), du_exact(x_fine)))

    y_euler = euler_method(x_fine, y0)
    y_rk4_fine = rk4_method(x_fine, y0)
    y_adams = adams3_method(x_fine, y0)

    print("Lab 5: Cauchy problem for ODE, variant 7")
    print("u'' - (tan(x)/2)u' - (1 + tan(x)/2)u = -(sqrt(cos(x))/2) * (3 + tan(x))")
    print("u(0)=2, u'(0)=-1, u0(x)=sqrt(cos(x)) + exp(-x)")
    print(f"Detailed grid: h = {h_fine:.2f}, nodes = {x_fine.size}")

    print_solution_tables(x_fine, y_exact_fine, y_euler, y_rk4_fine, y_adams)
    print_max_error_report(y_exact_fine, y_euler, y_rk4_fine, y_adams)

    x_coarse = grid(a, b, h_coarse)
    y_rk4_coarse = rk4_method(x_coarse, y0)
    runge_estimate_for_rk4(x_fine, y_rk4_fine, x_coarse, y_rk4_coarse)

    solution_plot_name = "solution_variant7.png"
    error_plot_name = "error_variant7.png"
    save_solution_plot(x_fine, y_exact_fine, y_euler, y_rk4_fine, y_adams, solution_plot_name)
    save_error_plot(x_fine, y_exact_fine, y_euler, y_rk4_fine, y_adams, error_plot_name)
    print(f"Saved plot: {solution_plot_name}")
    print(f"Saved plot: {error_plot_name}")


if __name__ == "__main__":
    main()
