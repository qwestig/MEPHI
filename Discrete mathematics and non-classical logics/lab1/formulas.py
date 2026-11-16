"""Формулы варианта 1: синтаксические деревья и их обработка."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Atom:
    """Одна переменная или константа f."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Implication:
    """Импликация с левой и правой частями."""

    left: "Formula"
    right: "Formula"

    def __str__(self) -> str:
        return f"({self.left} ⊃ {self.right})"


Formula = Atom | Implication
FALSE = Atom("f")


class FormulaError(ValueError):
    """Входная строка не является правильно построенной формулой."""


def parse(text: str) -> Formula:
    """Проверить строку и построить дерево формулы. Импликация связывается слева."""
    tokens: list[str] = []
    for position, char in enumerate(text, start=1):
        if char.isspace():
            continue
        if char in "()⊃" or (char.isascii() and char.isalpha()):
            tokens.append(char)
        else:
            raise FormulaError(f"Недопустимый символ {char!r} на позиции {position}.")

    index = 0

    def primary() -> Formula:
        nonlocal index
        if index >= len(tokens):
            raise FormulaError("Ожидалась переменная или формула в скобках.")

        token = tokens[index]
        index += 1
        if token == "(":
            result = expression()
            if index >= len(tokens) or tokens[index] != ")":
                raise FormulaError("Ожидалась закрывающая скобка ')'.")
            index += 1
            return result
        if token.isascii() and token.isalpha():
            return Atom(token)
        raise FormulaError(f"Ожидалась переменная или '(', получено {token!r}.")

    def expression() -> Formula:
        nonlocal index
        result = primary()
        while index < len(tokens) and tokens[index] == "⊃":
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
            f"Неожиданный символ {tokens[index]!r}: проверьте скобки и операции. "
            "Переменная состоит из одной латинской буквы."
        )
    return result


def variables(formula: Formula) -> set[str]:
    """Вернуть переменные формулы; f является константой, а не переменной."""
    if isinstance(formula, Atom):
        return set() if formula == FALSE else {formula.name}
    return variables(formula.left) | variables(formula.right)


def substitute(formula: Formula, variable: str, replacement: Formula) -> Formula:
    """Заменить все вхождения одной переменной, не меняя вставленную формулу."""
    if variable == "f":
        raise ValueError("Нельзя подставлять формулу вместо константы f.")
    if isinstance(formula, Atom):
        return replacement if formula.name == variable else formula
    return Implication(
        substitute(formula.left, variable, replacement),
        substitute(formula.right, variable, replacement),
    )


def find_substitution(source: Formula, target: Formula) -> tuple[str, Formula] | None:
    """Найти одну переменную, замена которой превращает source в target."""
    for variable in sorted(variables(source)):
        replacement: Formula | None = None

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
