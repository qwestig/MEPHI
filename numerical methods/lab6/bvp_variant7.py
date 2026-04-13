import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def u_exact(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = np.sqrt(np.cos(x_arr)) + np.exp(-x_arr)
    return float(value) if np.ndim(x) == 0 else value


def p_coef(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = -0.5 * np.tan(x_arr)
    return float(value) if np.ndim(x) == 0 else value


def q_coef(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = -(1.0 + 0.5 * np.tan(x_arr))
    return float(value) if np.ndim(x) == 0 else value


def rhs(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    value = -0.5 * np.sqrt(np.cos(x_arr)) * (3.0 + np.tan(x_arr))
    return float(value) if np.ndim(x) == 0 else value


def grid(a: float, b: float, h: float) -> np.ndarray:
    n_steps = int(round((b - a) / h))
    if not np.isclose(a + n_steps * h, b):
        raise ValueError("(b - a) must be divisible by h")
    return a + np.arange(n_steps + 1, dtype=float) * h


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

    y = np.zeros(n, dtype=float)
    y[-1] = d_star[-1]
    for i in range(n - 2, -1, -1):
        y[i] = d_star[i] - c_star[i] * y[i + 1]
    return y


def interior_coefficients(x: np.ndarray, h: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = x.size
    lower = np.zeros(n, dtype=float)
    diag = np.zeros(n, dtype=float)
    upper = np.zeros(n, dtype=float)
    rhs_vec = np.zeros(n, dtype=float)

    for i in range(1, n - 1):
        p_i = float(p_coef(x[i]))
        q_i = float(q_coef(x[i]))
        f_i = float(rhs(x[i]))

        lower[i] = 1.0 / h**2 - p_i / (2.0 * h)
        diag[i] = -2.0 / h**2 + q_i
        upper[i] = 1.0 / h**2 + p_i / (2.0 * h)
        rhs_vec[i] = f_i

    return lower, diag, upper, rhs_vec


def build_system_first_order(x: np.ndarray, h: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lower, diag, upper, rhs_vec = interior_coefficients(x, h)
    n = x.size

    diag[0] = 4.0 - 1.0 / h
    upper[0] = 1.0 / h
    rhs_vec[0] = 7.0

    lower[n - 1] = -1.0 / h
    diag[n - 1] = 1.0 / h
    rhs_vec[n - 1] = -0.9403

    return lower, diag, upper, rhs_vec


def build_system_second_order(x: np.ndarray, h: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lower, diag, upper, rhs_vec = interior_coefficients(x, h)
    n = x.size
    if n < 4:
        raise ValueError("Second-order boundary approximation needs at least 4 nodes")

    left_a0 = 4.0 - 3.0 / (2.0 * h)
    left_a1 = 2.0 / h
    left_a2 = -1.0 / (2.0 * h)
    left_g = 7.0

    a1 = lower[1]
    b1 = diag[1]
    c1 = upper[1]
    f1 = rhs_vec[1]

    diag[0] = left_a0 - left_a2 * a1 / c1
    upper[0] = left_a1 - left_a2 * b1 / c1
    rhs_vec[0] = left_g - left_a2 * f1 / c1

    right_a2 = 1.0 / (2.0 * h)
    right_a1 = -2.0 / h
    right_a0 = 3.0 / (2.0 * h)
    right_g = -0.9403

    a_nm1 = lower[n - 2]
    b_nm1 = diag[n - 2]
    c_nm1 = upper[n - 2]
    f_nm1 = rhs_vec[n - 2]

    lower[n - 1] = right_a1 - right_a2 * b_nm1 / a_nm1
    diag[n - 1] = right_a0 - right_a2 * c_nm1 / a_nm1
    rhs_vec[n - 1] = right_g - right_a2 * f_nm1 / a_nm1

    return lower, diag, upper, rhs_vec


def print_table(x: np.ndarray, exact: np.ndarray, first: np.ndarray, second: np.ndarray) -> None:
    print("\nTable: boundary value problem, variant 7")
    print(f"{'x':>7} {'u_exact':>14} {'u_1st':>14} {'|err|':>11} {'u_2nd':>14} {'|err|':>11}")
    for i in range(x.size):
        err1 = abs(first[i] - exact[i])
        err2 = abs(second[i] - exact[i])
        print(f"{x[i]:7.2f} {exact[i]:14.8f} {first[i]:14.8f} {err1:11.3e} {second[i]:14.8f} {err2:11.3e}")


def print_max_error_report(exact: np.ndarray, first: np.ndarray, second: np.ndarray) -> None:
    err1 = np.max(np.abs(first - exact))
    err2 = np.max(np.abs(second - exact))
    print("\nMax absolute error on h=0.05")
    print(f"{'Boundary approximation':<26} {'max|u-u_exact|':>18}")
    print(f"{'1st order':<26} {err1:18.8e}")
    print(f"{'2nd order':<26} {err2:18.8e}")


def save_solution_plot(x: np.ndarray, exact: np.ndarray, first: np.ndarray, second: np.ndarray, filename: str) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(x, exact, color="black", linewidth=2.2, label="exact u(x)")
    plt.plot(x, first, "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h)")
    plt.plot(x, second, "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h^2)")
    plt.xlabel("x")
    plt.ylabel("u(x)")
    plt.title("Lab 6, variant 7: BVP solution on [0, 1], h=0.05")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def save_error_plot(x: np.ndarray, exact: np.ndarray, first: np.ndarray, second: np.ndarray, filename: str) -> None:
    e_first = np.abs(first - exact)
    e_second = np.abs(second - exact)

    tiny = 1e-18
    plt.figure(figsize=(10, 6))
    plt.semilogy(x, np.maximum(e_first, tiny), "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h)")
    plt.semilogy(x, np.maximum(e_second, tiny), "o-", linewidth=1.2, markersize=3.5, label="Boundary O(h^2)")
    plt.xlabel("x")
    plt.ylabel("|u_num - u_exact|")
    plt.title("Absolute error for variant 7")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def main() -> None:
    a, b = 0.0, 1.0
    h = 0.05
    x = grid(a, b, h)
    exact = u_exact(x)

    lower_1, diag_1, upper_1, rhs_1 = build_system_first_order(x, h)
    u_first = thomas_solve(lower_1, diag_1, upper_1, rhs_1)

    lower_2, diag_2, upper_2, rhs_2 = build_system_second_order(x, h)
    u_second = thomas_solve(lower_2, diag_2, upper_2, rhs_2)

    print("Lab 6: boundary value problem for ODE, variant 7")
    print("u'' - (tan(x)/2)u' - (1 + tan(x)/2)u = -(sqrt(cos(x))/2) * (3 + tan(x))")
    print("4u(0) + u'(0) = 7, u'(1) = -0.9403, u0(x)=sqrt(cos(x)) + exp(-x)")
    print(f"Grid: h = {h:.2f}, nodes = {x.size}")

    print_table(x, exact, u_first, u_second)
    print_max_error_report(exact, u_first, u_second)

    solution_plot_name = "solution_variant7.png"
    error_plot_name = "error_variant7.png"
    save_solution_plot(x, exact, u_first, u_second, solution_plot_name)
    save_error_plot(x, exact, u_first, u_second, error_plot_name)
    print(f"Saved plot: {solution_plot_name}")
    print(f"Saved plot: {error_plot_name}")


if __name__ == "__main__":
    main()
