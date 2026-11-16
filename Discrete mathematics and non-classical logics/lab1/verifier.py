"""Проверка очередного шага доказательства по аксиомам, MP и β."""

from dataclasses import dataclass

from formulas import Formula, Implication, find_substitution, parse


AXIOMS = {
    "K": parse("p ⊃ (q ⊃ p)"),
    "S": parse("(s ⊃ (p ⊃ q)) ⊃ ((s ⊃ p) ⊃ (s ⊃ q))"),
    "E¬": parse("((p ⊃ f) ⊃ f) ⊃ p"),
}


@dataclass(frozen=True)
class Reference:
    """Формула и источник, на который можно сослаться в объяснении."""

    formula: Formula
    label: str


@dataclass(frozen=True)
class Justification:
    """Основание, по которому программа приняла формулу."""

    rule: str
    sources: tuple[Reference, ...]
    variable: str = ""
    replacement: Formula | None = None

    def describe(self, formula: Formula) -> str:
        if self.rule == "axiom":
            return f"Формула {formula} является аксиомой {self.sources[0].label}."
        if self.rule == "repeat":
            return f"Формула {formula} уже принята ({self.sources[0].label})."
        if self.rule == "MP":
            implication, premise = self.sources
            return (
                f"Формула {formula} выводима по modus ponens из "
                f"{implication.formula} ({implication.label}) и "
                f"{premise.formula} ({premise.label})."
            )
        source = self.sources[0]
        return (
            f"Формула {formula} выводима из {source.formula} ({source.label}) "
            f"по правилу β с подстановкой формулы {self.replacement} "
            f"вместо переменной {self.variable}."
        )


class ProofError(ValueError):
    """Формула корректна, но её нельзя вывести за один разрешённый шаг."""


class ProofSession:
    """Содержит принятые формулы текущего сеанса доказательства."""

    def __init__(self) -> None:
        self.steps: list[tuple[Formula, Justification]] = []

    def known(self) -> dict[Formula, Reference]:
        """Собрать аксиомы и уже принятые формулы с их источниками."""
        result = {
            formula: Reference(formula, f"аксиома {name}")
            for name, formula in AXIOMS.items()
        }
        for number, (formula, _) in enumerate(self.steps, start=1):
            result.setdefault(formula, Reference(formula, f"шаг {number}"))
        return result

    def check(self, formula: Formula) -> Justification:
        """Найти основание для шага; список сеанса здесь не изменяется."""
        for name, axiom in AXIOMS.items():
            if formula == axiom:
                return Justification("axiom", (Reference(axiom, name),))

        known = self.known()
        if formula in known:
            return Justification("repeat", (known[formula],))

        for source, reference in known.items():
            if isinstance(source, Implication) and source.right == formula:
                if source.left in known:
                    return Justification("MP", (reference, known[source.left]))

        for source, reference in known.items():
            substitution = find_substitution(source, formula)
            if substitution is not None:
                variable, replacement = substitution
                return Justification("β", (reference,), variable, replacement)

        raise ProofError(
            f"Формула {formula} является правильно построенной, но не выводится "
            "за один шаг из аксиом и ранее принятых формул по MP или β."
        )

    def add(self, text: str) -> tuple[Formula, Justification]:
        """Разобрать, проверить и при успехе сохранить новый шаг."""
        formula = parse(text)
        justification = self.check(formula)
        self.steps.append((formula, justification))
        return formula, justification
