"""Консольный интерфейс лабораторной работы № 1, вариант 1."""

from formulas import FormulaError
from verifier import AXIOMS, ProofError, ProofSession


HELP = """Введите формулу, используя символ ⊃ и латинские буквы.
f — постоянная ложь. Переменная состоит из одной буквы.
Без скобок p ⊃ q ⊃ r означает (p ⊃ q) ⊃ r.
Команды: :list — принятые шаги; :axioms — аксиомы;
:reset — новый сеанс; :help — помощь; :quit — выход."""


def main() -> None:
    session = ProofSession()
    print("Лабораторная работа № 1. Верификатор доказательств. Вариант 1.")
    print(HELP)
    while True:
        try:
            text = input(f"Шаг {len(session.steps) + 1}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nСеанс завершён.")
            return

        if text == ":quit":
            return
        if text == ":help":
            print(HELP)
        elif text == ":axioms":
            for name, formula in AXIOMS.items():
                print(f"{name}: {formula}")
        elif text == ":list":
            if not session.steps:
                print("Принятых шагов пока нет.")
            for number, (formula, reason) in enumerate(session.steps, start=1):
                print(f"{number}. {formula} [{reason.rule}]")
        elif text == ":reset":
            session = ProofSession()
            print("Начат новый сеанс.")
        elif text.startswith(":"):
            print("Неизвестная команда. Введите :help.")
        else:
            try:
                formula, reason = session.add(text)
            except FormulaError as error:
                print(f"Ошибка записи: {error}")
            except ProofError as error:
                print(error)
            except RecursionError:
                print("Формула слишком глубока для проверки. Используйте меньшую вложенность.")
            else:
                print(reason.describe(formula))


if __name__ == "__main__":
    main()
