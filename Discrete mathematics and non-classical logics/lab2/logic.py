"""ЛР2: многозначные логики. Python 3.10+, только стандартная библиотека."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from itertools import product
import formulas
import sys

# Внутренние целые 0, 1, 2 обозначают 0, 1/2, 1; округлений нет.
DOMAINS = {"CL": (0, 2), "K3": (0, 1, 2), "L3": (0, 1, 2)}
MAX_ROWS = 100_000


def value(x: int) -> str:
    return ("0", "1/2", "1")[x]


def read_value(s: str) -> int:
    try:
        return {"0": 0, "1/2": 1, "0.5": 1, "0,5": 1, "1": 2}[s.strip()]
    except KeyError:
        raise ValueError(f"Недопустимое значение {s!r}: используйте 0, 1/2 или 1") from None


@dataclass(frozen=True)
class Node:
    op: str
    left: Node | None = None
    right: Node | None = None
    name: str = ""

    def variables(self) -> set[str]:
        if self.op == "const":
            return set()
        if self.op == "var":
            return {self.name}
        return (self.left.variables() if self.left else set()) | (self.right.variables() if self.right else set())

    def evaluate(self, env: dict[str, int], system: str) -> int:
        if self.op == "const":
            return 0
        if self.op == "var":
            return env[self.name]
        a = self.left.evaluate(env, system)
        if self.op == "¬":
            return 2 - a
        b = self.right.evaluate(env, system)
        if self.op == "∧":
            return min(a, b)
        if self.op == "∨":
            return max(a, b)
        return min(2, 2 - a + b) if system == "L3" else max(2 - a, b)

    def __str__(self):
        if self.op in ("var", "const"):
            return self.name
        if self.op == "¬":
            return f"¬{self.left}"
        return f"({self.left} {self.op} {self.right})"


def parse(source: str) -> Node:
    """Адаптер дерева расширенного парсера ЛР1 к вычислителю ЛР2."""
    def convert(node):
        if isinstance(node, formulas.Atom):
            return Node("const", name="f") if node == formulas.FALSE else Node("var", name=node.name)
        if isinstance(node, formulas.Negation):
            return Node("¬", convert(node.operand))
        operation = {formulas.Implication: "→", formulas.Conjunction: "∧", formulas.Disjunction: "∨"}[type(node)]
        return Node(operation, convert(node.left), convert(node.right))
    try:
        return convert(formulas.parse(source))
    except RecursionError:
        raise ValueError("Формула слишком сложна или глубоко вложена") from None


def interpretations(names, system):
    if system not in DOMAINS:
        raise ValueError(f"Неизвестная логика {system}")
    count = len(DOMAINS[system]) ** len(names)
    if count > MAX_ROWS:
        raise ValueError(f"Требуется {count} строк, предел {MAX_ROWS}")
    for row in product(DOMAINS[system], repeat=len(names)):
        yield dict(zip(names, row))


def evaluate(node, env, system):
    if system not in DOMAINS:
        raise ValueError(f"Неизвестная логика {system}")
    missing = node.variables() - env.keys()
    if missing:
        raise ValueError("Не заданы переменные: " + ", ".join(sorted(missing)))
    for name in node.variables():
        if type(env[name]) is not int or env[name] not in DOMAINS[system]:
            raise ValueError(f"Недопустимое значение переменной {name} в {system}")
    try:
        return node.evaluate(env, system)
    except RecursionError:
        raise ValueError("Формула слишком сложна") from None


def table(node, system):
    names = sorted(node.variables())
    return names, [(env, evaluate(node, env, system)) for env in interpretations(names, system)]


def analyze(node, system):
    names, rows = table(node, system)
    counter = next((env for env, v in rows if v != 2), None)
    witness = next((env for env, v in rows if v == 2), None)
    return dict(variables=names, interpretations=len(rows), valid=counter is None,
                satisfiable=witness is not None, identically_false=all(v == 0 for _, v in rows),
                counterexample=counter, witness=witness,
                counts={value(v): sum(x == v for _, x in rows) for v in DOMAINS[system]})


def entail(premises, conclusion, system):
    names = sorted(set().union(conclusion.variables(), *(p.variables() for p in premises)))
    models = 0
    counter = None
    total = 0
    for env in interpretations(names, system):
        total += 1
        vals = [evaluate(p, env, system) for p in premises]
        if all(v == 2 for v in vals):
            models += 1
            result = evaluate(conclusion, env, system)
            if result != 2 and counter is None:
                counter = dict(assignment=env, premises=vals, conclusion=result)
    return dict(entails=counter is None, premises_satisfiable=models > 0,
                premise_models=models, interpretations=total, counterexample=counter)


def assignment(env):
    return ", ".join(f"{k}={value(v)}" for k, v in env.items())


def print_table(headers, rows):
    rows = [[str(x) for x in row] for row in rows]
    widths = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print(" | ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(x.ljust(w) for x, w in zip(row, widths)))


def print_analysis(node, system):
    a = analyze(node, system)
    print(f"\n{system}: {node}")
    for key, label in [("valid", "Общезначима"), ("satisfiable", "Выполнима"), ("identically_false", "Тождественно ложна")]:
        print(f"{label}: {'да' if a[key] else 'нет'}")
    if a["counterexample"] is not None:
        print("Контрпример общезначимости:", assignment(a["counterexample"]))
    if a["witness"] is not None:
        print("Пример выполнимости:", assignment(a["witness"]))


def compare(node):
    names = sorted(node.variables())
    rows = []
    for env in interpretations(names, "K3"):
        vals = [value(evaluate(node, env, s)) if all(v in DOMAINS[s] for v in env.values()) else "-" for s in DOMAINS]
        rows.append([*(value(env[n]) for n in names), *vals])
    print_table([*names, *DOMAINS], rows)
    print("'-': интерпретация не входит в область классической логики.")
    pairs = [("CL", "K3"), ("CL", "L3"), ("K3", "L3")]
    for s, t in pairs:
        domain = "CL" if "CL" in (s, t) else "K3"
        same_values = all(evaluate(node, e, s) == evaluate(node, e, t) for e in interpretations(names, domain))
        a, b = analyze(node, s), analyze(node, t)
        same_properties = all(a[k] == b[k] for k in ("valid", "satisfiable", "identically_false"))
        print(f"{s}/{t}: значения на общей области совпадают: {'да' if same_values else 'нет'}; свойства совпадают: {'да' if same_properties else 'нет'}")
    for s in DOMAINS:
        print_analysis(node, s)


def show_entail(premises, conclusion, system):
    r = entail(premises, conclusion, system)
    print(f"{system}: следование {'выполняется' if r['entails'] else 'НЕ выполняется'}; моделей посылок: {r['premise_models']}/{r['interpretations']}")
    if not r["premises_satisfiable"]:
        print("Посылки совместно невыполнимы; следование выполняется вакуозно.")
    if r["counterexample"]:
        c = r["counterexample"]
        print("Контрпример:", assignment(c["assignment"]))
        print("Посылки:", ", ".join(map(value, c["premises"])), "; заключение:", value(c["conclusion"]))


def interactive():
    print("Обозначения: ¬ — не; ∧ — и; ∨ — или; → — если…то. Пример: (p ∧ ¬p) ∨ q")
    while True:
        print("\nЛР2: 1 - значение; 2 - таблица; 3 - сравнение; 4 - следование; 5 - примеры варианта 1; 0 - выход")
        choice = input("> ").strip()
        if choice == "0":
            return
        try:
            if choice == "5":
                from variants import show_variant
                show_variant(1)
                continue
            if choice not in ("1", "2", "3", "4"):
                print("Выберите пункт от 0 до 5")
                continue
            if choice == "4":
                text = input("Посылки через запятую или всё отношение с ⊨: ")

                if "⊨" in text:
                    premises_text, conclusion_text = text.split("⊨", 1)
                else:
                    premises_text = text
                    conclusion_text = input("Заключение: ")

                premises = [
                    parse(p.strip())
                    for p in premises_text.split(",")
                    if p.strip()
                ]
                conclusion = parse(conclusion_text.strip())

                for s in DOMAINS:
                    show_entail(premises, conclusion, s)
                continue
            node = parse(input("Формула: "))
            if choice == "3":
                compare(node)
                continue
            s = input("Логика (CL/K3/L3): ").strip().upper()
            if choice == "1":
                env = {n: read_value(input(n + " = ")) for n in sorted(node.variables())}
                print("Значение:", value(evaluate(node, env, s)))
            else:
                names, rows = table(node, s)
                print_table([*names, "F"], [[*(value(e[n]) for n in names), value(v)] for e, v in rows])
                print_analysis(node, s)
        except (ValueError, KeyError) as exc:
            print("Ошибка:", exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    for name in ("eval", "analyze", "compare"):
        p = sub.add_parser(name)
        p.add_argument("formula")
        if name != "compare":
            p.add_argument("--system", choices=DOMAINS, default="CL")
        if name == "eval":
            p.add_argument("assignments", nargs="*")
        if name == "analyze":
            p.add_argument("--csv", help="Сохранить таблицу в CSV")
    p = sub.add_parser("entail")
    p.add_argument("--premise", action="append", default=[])
    p.add_argument("--conclusion", required=True)
    p.add_argument("--system", choices=DOMAINS, default="CL")
    p = sub.add_parser("examples")
    p.add_argument("--variant", type=int, choices=[1], default=1)
    args = parser.parse_args()
    try:
        if args.command is None:
            interactive()
        elif args.command == "examples":
            from variants import show_variant
            for v in ([args.variant] if args.variant else [1]):
                show_variant(v)
        elif args.command == "entail":
            show_entail([parse(p) for p in args.premise], parse(args.conclusion), args.system)
        else:
            node = parse(args.formula)
            if args.command == "eval":
                env = {}
                for item in args.assignments:
                    if item.count("=") != 1:
                        raise ValueError("Оценки вводятся как p=1/2 q=1")
                    k, v = item.split("=")
                    if k in env or k not in node.variables():
                        raise ValueError(f"Лишняя или повторная переменная {k!r}")
                    env[k] = read_value(v)
                print(value(evaluate(node, env, args.system)))
            elif args.command == "compare":
                compare(node)
            else:
                names, rows = table(node, args.system)
                data = [[*(value(e[n]) for n in names), value(v)] for e, v in rows]
                print_table([*names, "F"], data)
                print_analysis(node, args.system)
                if args.csv:
                    with open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([*names, "F"])
                        writer.writerows(data)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Ошибка: {exc}\n")
    except (KeyboardInterrupt, EOFError):
        print("\nРабота завершена.")


if __name__ == "__main__":
    main()
