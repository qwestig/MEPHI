import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def f(x: np.ndarray) -> np.ndarray:
    return np.exp(x / 3.0) / (1.0 + x**2)


def uniform_nodes(a: float, b: float, n_nodes: int) -> np.ndarray:
    return np.linspace(a, b, n_nodes)


def chebyshev_nodes(a: float, b: float, n_nodes: int) -> np.ndarray:
    k = np.arange(n_nodes)
    x_std = np.cos((2 * k + 1) * np.pi / (2 * n_nodes))
    return (a + b) / 2.0 + (b - a) * x_std / 2.0


def barycentric_weights(nodes: np.ndarray) -> np.ndarray:
    n = len(nodes)
    w = np.ones(n)
    for j in range(n):
        diff = nodes[j] - np.delete(nodes, j)
        w[j] = 1.0 / np.prod(diff)
    return w


def barycentric_interpolate(
    x_eval: np.ndarray,
    nodes: np.ndarray,
    values: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    result = np.empty_like(x_eval, dtype=float)
    eps = 1e-14

    for i, x in enumerate(x_eval):
        d = x - nodes
        close = np.where(np.abs(d) < eps)[0]
        if close.size > 0:
            result[i] = values[close[0]]
            continue

        terms = weights / d
        result[i] = np.sum(terms * values) / np.sum(terms)

    return result


def midpoint_points(nodes: np.ndarray) -> np.ndarray:
    sorted_nodes = np.sort(nodes)
    return 0.5 * (sorted_nodes[:-1] + sorted_nodes[1:])


def print_report(name: str, x_star: np.ndarray, fx: np.ndarray, px: np.ndarray) -> None:
    err = np.abs(fx - px)
    print(f"\n{name}")
    print("-" * len(name))
    print(f"{'x*':>10} {'f(x*)':>16} {'P(x*)':>16} {'|f-P|':>16}")
    for x, fv, pv, e in zip(x_star, fx, px, err):
        print(f"{x:10.6f} {fv:16.10e} {pv:16.10e} {e:16.10e}")
    print(f"max error:  {np.max(err):.10e}")
    print(f"mean error: {np.mean(err):.10e}")


def save_plots(
    a: float,
    b: float,
    n_nodes: int,
    nodes_uniform: np.ndarray,
    values_uniform: np.ndarray,
    weights_uniform: np.ndarray,
    nodes_cheb: np.ndarray,
    values_cheb: np.ndarray,
    weights_cheb: np.ndarray,
) -> None:
    x_dense = np.linspace(a, b, 1200)
    f_dense = f(x_dense)

    p_dense_uniform = barycentric_interpolate(
        x_dense, nodes_uniform, values_uniform, weights_uniform
    )
    p_dense_cheb = barycentric_interpolate(x_dense, nodes_cheb, values_cheb, weights_cheb)

    err_uniform = np.abs(f_dense - p_dense_uniform)
    err_cheb = np.abs(f_dense - p_dense_cheb)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(x_dense, f_dense, label="f(x)", linewidth=2.0, color="black")
    axes[0].plot(
        x_dense,
        p_dense_uniform,
        label="Lagrange, uniform nodes",
        linestyle="--",
        linewidth=1.6,
        color="#1f77b4",
    )
    axes[0].plot(
        x_dense,
        p_dense_cheb,
        label="Lagrange, Chebyshev nodes",
        linestyle="-.",
        linewidth=1.6,
        color="#d62728",
    )
    axes[0].scatter(nodes_uniform, values_uniform, s=24, color="#1f77b4", alpha=0.8)
    axes[0].scatter(nodes_cheb, values_cheb, s=24, color="#d62728", alpha=0.8)
    axes[0].set_ylabel("y")
    axes[0].set_title(f"Interpolation on [{a}, {b}], n={n_nodes}")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(
        x_dense,
        err_uniform,
        label="|f-P|, uniform nodes",
        linewidth=1.6,
        color="#1f77b4",
    )
    axes[1].plot(
        x_dense,
        err_cheb,
        label="|f-P|, Chebyshev nodes",
        linewidth=1.6,
        color="#d62728",
    )
    axes[1].set_yscale("log")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("absolute error")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig("interpolation_n10.png", dpi=200)
    plt.close(fig)


def main() -> None:
    a, b = 0.0, 10.0
    n_nodes = 10

    nodes_uniform = uniform_nodes(a, b, n_nodes)
    values_uniform = f(nodes_uniform)
    weights_uniform = barycentric_weights(nodes_uniform)
    x_star_uniform = midpoint_points(nodes_uniform)
    f_star_uniform = f(x_star_uniform)
    p_star_uniform = barycentric_interpolate(
        x_star_uniform, nodes_uniform, values_uniform, weights_uniform
    )

    nodes_cheb = chebyshev_nodes(a, b, n_nodes)
    values_cheb = f(nodes_cheb)
    weights_cheb = barycentric_weights(nodes_cheb)
    x_star_cheb = midpoint_points(nodes_cheb)
    f_star_cheb = f(x_star_cheb)
    p_star_cheb = barycentric_interpolate(
        x_star_cheb, nodes_cheb, values_cheb, weights_cheb
    )

    print(f"f(x) = exp(x/3) / (1 + x^2),  interval [{a}, {b}], n = {n_nodes} nodes")
    print_report("Uniform nodes", x_star_uniform, f_star_uniform, p_star_uniform)
    print_report("Chebyshev nodes", x_star_cheb, f_star_cheb, p_star_cheb)
    save_plots(
        a,
        b,
        n_nodes,
        nodes_uniform,
        values_uniform,
        weights_uniform,
        nodes_cheb,
        values_cheb,
        weights_cheb,
    )
    print("Saved plot: interpolation_n10.png")


if __name__ == "__main__":
    main()
