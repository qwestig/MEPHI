"""Расширение анализатора ЛР1: Atom, Implication, primary/expression.

Исходный модуль сохранён в lab1_reference/formulas.py (восстановлен из
вывода файла в чате «Разобрать лекции по курсу»).
Добавлены ¬, ∧, ∨, имена из нескольких символов и пределы ввода.
Сохранены NFKC, обозначение ⊃, константа f и левая ассоциативность →.
"""
from dataclasses import dataclass
from typing import Union
import re
import unicodedata


@dataclass(frozen=True)
class Atom:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Implication:
    left: "Formula"
    right: "Formula"

    def __str__(self) -> str:
        return f"({self.left} → {self.right})"


@dataclass(frozen=True)
class Negation:
    operand: "Formula"

    def __str__(self) -> str:
        return f"¬{self.operand}"


@dataclass(frozen=True)
class Conjunction:
    left: "Formula"
    right: "Formula"

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"


@dataclass(frozen=True)
class Disjunction:
    left: "Formula"
    right: "Formula"

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"


Formula = Union[Atom, Implication, Negation, Conjunction, Disjunction]
FALSE = Atom("f")


class FormulaError(ValueError):
    """Входная строка не является правильно построенной формулой."""


def parse(text: str) -> Formula:
    """Рекурсивный спуск ЛР1, расширенный приоритетами ¬ > ∧ > ∨ > →."""
    if len(text) > 4000:
        raise FormulaError("Формула длиннее 4000 символов")
    text = unicodedata.normalize("NFKC", text).replace("->", "→").replace("⊃", "→")
    aliases = {"~": "¬", "!": "¬", "&": "∧", "|": "∨"}
    pattern = re.compile(r"\s+|[¬~!∧&∨|→()]|[A-Za-z_][A-Za-z_0-9]*")
    tokens = []
    position = 0
    while position < len(text):
        m = pattern.match(text, position)
        if not m:
            raise FormulaError(f"Недопустимый символ {text[position]!r} на позиции {position+1}")
        token = m.group()
        if not token.isspace():
            tokens.append((aliases.get(token, token), position+1))
        position = m.end()
    if not tokens:
        raise FormulaError("Формула пустая")
    if len(tokens) > 400:
        raise FormulaError("Формула содержит больше 400 лексем")
    tokens.append((None, len(text)+1))
    index = 0
    depth = 0

    def take(token):
        nonlocal index
        if tokens[index][0] == token:
            index += 1
            return True
        return False

    def fail(expected):
        token, pos = tokens[index]
        raise FormulaError(f"Позиция {pos}: ожидалось {expected}, получено {token!r}")

    def primary() -> Formula:
        nonlocal index
        if take("("):
            result = expression()
            if not take(")"):
                fail("закрывающая скобка ')'")
            return result
        token = tokens[index][0]
        if token is not None and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", token):
            index += 1
            return Atom(token)
        fail("переменная, f или выражение в скобках")

    def unary() -> Formula:
        nonlocal depth
        if take("¬"):
            depth += 1
            if depth > 100:
                raise FormulaError("Слишком много вложенных отрицаний")
            result = Negation(unary())
            depth -= 1
            return result
        return primary()

    def conjunction() -> Formula:
        result = unary()
        while take("∧"):
            result = Conjunction(result, unary())
        return result

    def disjunction() -> Formula:
        result = conjunction()
        while take("∨"):
            result = Disjunction(result, conjunction())
        return result

    def expression() -> Formula:
        nonlocal depth
        depth += 1
        if depth > 100:
            raise FormulaError("Слишком большая глубина вложенности скобок")
        result = disjunction()
        # Цикл, как в ЛР1: p→q→r = (p→q)→r.
        while take("→"):
            result = Implication(result, disjunction())
        depth -= 1
        return result

    try:
        result = expression()
    except RecursionError as error:
        raise FormulaError("Слишком большая глубина вложенности формулы") from error
    if tokens[index][0] is not None:
        fail("окончание формулы")
    return result


def variables(formula: Formula) -> set[str]:
    if isinstance(formula, Atom):
        return set() if formula == FALSE else {formula.name}
    if isinstance(formula, Negation):
        return variables(formula.operand)
    return variables(formula.left) | variables(formula.right)
