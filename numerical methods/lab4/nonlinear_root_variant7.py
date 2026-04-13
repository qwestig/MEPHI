import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def f(x: np.ndarray | float) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=float)
    arg = (x_arr - 3.0) / 8.0
    if np.any((arg < -1.0) | (arg > 1.0)):
        raise ValueError("arccos argument is outside [-1, 1]")
    y = np.arccos(arg) - 0.5 * x_arr**2 + 3.0 * x_arr + 1.0
    return float(y) if np.ndim(x) == 0 else y


def df(x: float) -> float:
    arg = (x - 3.0) / 8.0
    term = 1.0 - arg**2
    if term <= 0.0:
        raise ValueError("Derivative is undefined at this x")
    return -1.0 / (8.0 * np.sqrt(term)) - x + 3.0


def validate_interval(a: float, b: float) -> None:
    if not (0.0 < a < b < 10.0):
        raise ValueError("Interval must satisfy 0 < a < b < 10")
    fa = f(a)
    fb = f(b)
    if fa * fb > 0.0:
        raise ValueError("f(a) and f(b) must have opposite signs for bracketing")


def bisection(a: float, b: float, eps: float, max_iter: int = 200) -> dict[str, float | int | bool]:
    left, right = a, b
    f_left = float(f(left))
    f_right = float(f(right))

    if abs(f_left) <= eps:
        return {"x": left, "fx": f_left, "iterations": 0, "converged": True}
    if abs(f_right) <= eps:
        return {"x": right, "fx": f_right, "iterations": 0, "converged": True}

    for it in range(1, max_iter + 1):
        mid = 0.5 * (left + right)
        f_mid = float(f(mid))

        if abs(f_mid) <= eps or 0.5 * (right - left) <= eps:
            return {"x": mid, "fx": f_mid, "iterations": it, "converged": True}

        if f_left * f_mid <= 0.0:
            right = mid
            f_right = f_mid
        else:
            left = mid
            f_left = f_mid

    x_last = 0.5 * (left + right)
    return {
        "x": x_last,
        "fx": float(f(x_last)),
        "iterations": max_iter,
        "converged": False,
    }


def newton(
    a: float,
    b: float,
    eps: float,
    x0: float | None = None,
    max_iter: int = 100,
    deriv_tol: float = 1e-14,
) -> dict[str, float | int | bool]:
    left, right = a, b
    f_left = float(f(left))
    f_right = float(f(right))
    x = 0.5 * (a + b) if x0 is None else float(x0)

    if not (left <= x <= right):
        x = 0.5 * (left + right)

    for it in range(1, max_iter + 1):
        fx = float(f(x))
        if abs(fx) <= eps:
            return {"x": x, "fx": fx, "iterations": it - 1, "converged": True}

        if f_left * fx <= 0.0:
            right = x
            f_right = fx
        else:
            left = x
            f_left = fx

        dfx = float(df(x))
        if abs(dfx) < deriv_tol:
            x_new = 0.5 * (left + right)
        else:
            x_new = x - fx / dfx
            if not np.isfinite(x_new) or x_new <= left or x_new >= right:
                x_new = 0.5 * (left + right)

        fx_new = float(f(x_new))
        if abs(x_new - x) <= eps or abs(fx_new) <= eps:
            return {"x": x_new, "fx": fx_new, "iterations": it, "converged": True}

        x = x_new

    return {"x": x, "fx": float(f(x)), "iterations": max_iter, "converged": False}


def print_results_table(
    eps_values: list[float],
    bis_data: list[dict[str, float | int | bool]],
    newton_data: list[dict[str, float | int | bool]],
) -> None:
    print("\nRoot finding results (variant 7)")
    print("Equation: arccos((x - 3)/8) - x^2/2 + 3x + 1 = 0")
    print(
        f"{'Method':<12} {'eps':>10} {'x':>16} {'|f(x)|':>14} {'iters':>8} {'conv':>8}"
    )
    for eps, r in zip(eps_values, bis_data):
        print(
            f"{'Bisection':<12} {eps:10.1e} {float(r['x']):16.10f} {abs(float(r['fx'])):14.3e} "
            f"{int(r['iterations']):8d} {str(bool(r['converged'])):>8}"
        )
    for eps, r in zip(eps_values, newton_data):
        print(
            f"{'Newton':<12} {eps:10.1e} {float(r['x']):16.10f} {abs(float(r['fx'])):14.3e} "
            f"{int(r['iterations']):8d} {str(bool(r['converged'])):>8}"
        )


def save_function_plot(
    a: float,
    b: float,
    root_ref: float,
    bis_data: list[dict[str, float | int | bool]],
    newton_data: list[dict[str, float | int | bool]],
    filename: str,
) -> None:
    x_dense = np.linspace(a, b, 1200)
    y_dense = f(x_dense)

    plt.figure(figsize=(9, 6))
    plt.plot(x_dense, y_dense, color="black", linewidth=2.0, label="f(x)")
    plt.axhline(0.0, color="gray", linewidth=1.0)
    plt.axvline(root_ref, color="#c44e52", linestyle="--", linewidth=1.4, label="reference root")

    x_bis = np.array([float(r["x"]) for r in bis_data])
    x_newton = np.array([float(r["x"]) for r in newton_data])
    plt.scatter(x_bis, f(x_bis), s=45, color="#4c72b0", marker="o", label="bisection roots")
    plt.scatter(x_newton, f(x_newton), s=50, color="#55a868", marker="x", label="newton roots")

    plt.xlabel("x")
    plt.ylabel("f(x)")
    plt.title("Variant 7: equation and located root on (0, 10)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def save_convergence_plot(
    eps_values: list[float],
    root_ref: float,
    bis_data: list[dict[str, float | int | bool]],
    newton_data: list[dict[str, float | int | bool]],
    filename: str,
) -> None:
    eps_arr = np.array(eps_values, dtype=float)
    bis_iters = np.array([int(r["iterations"]) for r in bis_data], dtype=float)
    newton_iters = np.array([int(r["iterations"]) for r in newton_data], dtype=float)
    bis_root_err = np.array([abs(float(r["x"]) - root_ref) for r in bis_data], dtype=float)
    newton_root_err = np.array([abs(float(r["x"]) - root_ref) for r in newton_data], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(eps_arr, bis_iters, "o-", linewidth=1.5, label="Bisection")
    axes[0].plot(eps_arr, newton_iters, "o-", linewidth=1.5, label="Newton")
    axes[0].set_xscale("log")
    axes[0].invert_xaxis()
    axes[0].set_xlabel("eps")
    axes[0].set_ylabel("iterations")
    axes[0].set_title("Iterations vs eps")
    axes[0].grid(alpha=0.3, which="both")
    axes[0].legend()

    axes[1].loglog(eps_arr, bis_root_err, "o-", linewidth=1.5, label="Bisection")
    axes[1].loglog(eps_arr, newton_root_err, "o-", linewidth=1.5, label="Newton")
    axes[1].invert_xaxis()
    axes[1].set_xlabel("eps")
    axes[1].set_ylabel("|x_eps - x_ref|")
    axes[1].set_title("Root error vs eps")
    axes[1].grid(alpha=0.3, which="both")
    axes[1].legend()

    fig.suptitle("Variant 7: method convergence")
    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)


def main() -> None:
    a, b = 0.1, 9.9
    eps_values = [1e-3, 1e-6, 1e-9]

    validate_interval(a, b)

    reference = bisection(a, b, eps=1e-14, max_iter=400)
    root_ref = float(reference["x"])

    bis_data = [bisection(a, b, eps) for eps in eps_values]
    newton_data = [newton(a, b, eps, x0=5.0) for eps in eps_values]

    print_results_table(eps_values, bis_data, newton_data)
    print(f"\nReference root (bisection, eps=1e-14): x_ref = {root_ref:.12f}")

    function_plot_name = "function_and_root_variant7.png"
    save_function_plot(a, b, root_ref, bis_data, newton_data, function_plot_name)
    print(f"Saved plot: {function_plot_name}")

    convergence_plot_name = "convergence_variant7.png"
    save_convergence_plot(eps_values, root_ref, bis_data, newton_data, convergence_plot_name)
    print(f"Saved plot: {convergence_plot_name}")


if __name__ == "__main__":
    main()
