"""Синтаксические деревья и парсер формул варианта 1."""

from dataclasses import dataclass
from typing import Union
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
        # Полные скобки сохраняют структуру при повторном чтении.
        return f"({self.left} → {self.right})"


Formula = Union[Atom, Implication]
FALSE = Atom("f")


class FormulaError(ValueError):
    """Входная строка не является правильно построенной формулой."""


def parse(text: str) -> Formula:
    """Разобрать строку. Импликация ассоциативна влево (слайд 16)."""
    # Нормализация позволяет копировать математические буквы из PDF: 𝑝 → p.
    text = unicodedata.normalize("NFKC", text).replace("->", "→").replace("⊃", "→")
    tokens = []
    for position, char in enumerate(text, start=1):
        if char.isspace():
            continue
        if char in "()→" or char.isascii() and char.isalpha():
            tokens.append(char)
        else:
            raise FormulaError(f"Недопустимый символ {char!r} на позиции {position}.")

    index = 0

    def primary() -> Formula:
        nonlocal index
        if index == len(tokens):
            raise FormulaError("Ожидалась переменная, f или выражение в скобках.")
        token = tokens[index]
        index += 1
        if token == "(":
            result = expression()
            if index == len(tokens) or tokens[index] != ")":
                raise FormulaError("Ожидалась закрывающая скобка ')'.")
            index += 1
            return result
        if token.isascii() and token.isalpha():
            return Atom(token)
        raise FormulaError(f"Ожидалась переменная, f или '(', получено {token!r}.")

    def expression() -> Formula:
        nonlocal index
        result = primary()
        while index < len(tokens) and tokens[index] == "→":
            index += 1
            result = Implication(result, primary())
        return result

    if not tokens:
        raise FormulaError("Формула пустая.")
    try:
        result = expression()
    except RecursionError as error:
        raise FormulaError("Слишком большая глубина вложенности скобок.") from error
    if index != len(tokens):
        raise FormulaError(
            f"Неожиданный символ {tokens[index]!r}: проверьте операции и скобки. "
            "Переменная состоит из одного символа."
        )
    return result


def variables(formula: Formula) -> set[str]:
    if isinstance(formula, Atom):
        # f — константа; подстановка вместо неё запрещена.
        return set() if formula == FALSE else {formula.name}
    return variables(formula.left) | variables(formula.right)


def substitute(formula: Formula, variable: str, replacement: Formula) -> Formula:
    """Заменить все вхождения одной переменной. Вставленное дерево не менять."""
    if variable == "f":
        raise ValueError("Нельзя подставлять формулу вместо константы f.")
    if isinstance(formula, Atom):
        return replacement if formula.name == variable else formula
    return Implication(
        substitute(formula.left, variable, replacement),
        substitute(formula.right, variable, replacement),
    )


def find_substitution(source: Formula, target: Formula):
    """Найти одну подстановку source → target, сравнивая структуры деревьев."""
    for variable in sorted(variables(source)):
        replacement = None

        def match(before: Formula, after: Formula) -> bool:
            nonlocal replacement
            if isinstance(before, Atom) and before.name == variable:
                if replacement is None:
                    replacement = after
                return replacement == after
            if isinstance(before, Atom):
                return before == after
            return (
                isinstance(after, Implication)
                and match(before.left, after.left)
                and match(before.right, after.right)
            )

        if match(source, target) and replacement is not None:
            return variable, replacement
    return None

