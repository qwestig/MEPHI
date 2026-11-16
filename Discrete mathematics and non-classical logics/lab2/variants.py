"""Формулы и отношения первого варианта задания, без исправления исходных условий."""
from logic import DOMAINS, parse, print_analysis, show_entail

VARIANTS = {
    1: {
        "formulas": [
            '(p → q) ∨ (q → p)',
            '((p → q) → p) → p',
            '(p ∧ ¬p) ∨ q',
            '(p ∧ ¬p) ∧ q',
            '((p → q) ∧ (q → r)) → (p → r)',
        ],
        "relations": [
            (['p ∨ q', 'p → r', 'q → r', 'r → s', 's → t'], 't'),
            (['p → q', 'p → r', '(q ∧ r) → s', 's → t', 't → u'], '¬p ∨ u'),
            (['p ∨ q', 'p → r', 'q → s', 'r → t', 's → t'], 't ∧ (p ∨ ¬p)'),
            (['p ∨ q', 'p → r', 'q → s', '(r ∨ s) → t', 's → u'], 't → u'),
        ],
    },
}

def show_variant(number):
    if number not in VARIANTS:
        raise ValueError("В работе используется вариант 1")
    v = VARIANTS[number]
    print(f"\nВАРИАНТ {number}")
    for i, formula in enumerate(v["formulas"], 1):
        print(f"\nF{i}: {parse(formula)}")
        for s in DOMAINS:
            print_analysis(parse(formula), s)
    for i, (premises, conclusion) in enumerate(v["relations"], 1):
        print(f"\nR{i}: {', '.join(str(parse(p)) for p in premises)} ⊨ {parse(conclusion)}")
        for s in DOMAINS:
            show_entail([parse(p) for p in premises], parse(conclusion), s)
