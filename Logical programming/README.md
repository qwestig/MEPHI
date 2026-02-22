# MEPHI — учебные проекты

## Предметы
- [Logical programming](Logical%20programming/)
# Logical programming

Лабораторные работы по дисциплине «Логическое программирование» (SWI‑Prolog).

## Структура
- `lab1/` — Генеалогическое дерево: база знаний + предикаты родства + рекурсивный вывод + тесты.

---

# Lab 1 — запуск и демонстрация

## 1) Что должно быть в папке `lab1`
- `family.pl` — база знаний и предикаты
- `tests.pl` — автоматические тесты (plunit)
- `debug_backtracking.pl` — демонстрация backtracking

## 2) Требования
Нужен установленный SWI‑Prolog (команда `swipl` доступна в терминале).

Проверка:
```bash
swipl --version
```

## 3) Быстрый запуск проверок
Запусти из папки `lab1`:
```bash
cd "lab1"
swipl -q -l tests.pl -t run_tests
swipl -q -l debug_backtracking.pl -g run_backtracking_debug -t halt
```

Что это делает:
- первая команда запускает unit‑тесты (`tests.pl`);
- вторая выводит диагностические запросы и демонстрирует backtracking.

## 4) Интерактивный режим (REPL)
Есть два удобных варианта.

### Вариант A (проще): старт REPL сразу с загруженной БЗ
Из папки `lab1`:
```bash
cd "lab1"
swipl -q -l family.pl
```
Дальше вводи запросы прямо в `?- ... .`

### Вариант B (классика): сначала `swipl`, потом загрузка файла
```bash
cd "lab1"
swipl
```
Внутри Prolog:
```prolog
?- consult('family.pl').
% или короче
?- ['family.pl'].
```

## 5) Набор REPL‑запросов для демонстрации (и скриншотов)
```prolog
?- мать(nina, ivan).
?- дедушка(fedor, ivan).
?- предок(fedor, alina).
?- потомок(victor, fedor).
?- двоюродный_брат(sergey, ivan).
?- троюродная_сестра(alina, ekaterina).
?- setof(A, предок(A, pavel), As).
```

Для демонстрации backtracking:
```prolog
?- предок(fedor, X).
```
