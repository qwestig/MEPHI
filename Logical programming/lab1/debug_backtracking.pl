:- encoding(utf8).
:- [family].

run_backtracking_debug :-
    writeln('=== Проверка backtracking и полноты ответов ==='),

    writeln('\n0) Примеры базовых/производных отношений (мать/отец/дедушка):'),
    (   мать(M0, ivan),
        format('  мать(X, ivan): X = ~w~n', [M0]),
        fail
    ;   true
    ),
    (   отец(F0, ivan),
        format('  отец(X, ivan): X = ~w~n', [F0]),
        fail
    ;   true
    ),
    (   дедушка(G0, nikita),
        format('  дедушка(X, nikita): X = ~w~n', [G0]),
        fail
    ;   true
    ),

    writeln('\n1) Все потомки fedor (рекурсия предок/2):'),
    (   предок(fedor, X1),
        format('  X = ~w~n', [X1]),
        fail
    ;   true
    ),

    writeln('\n2) Все предки alina (обратный поиск):'),
    (   предок(X2, alina),
        format('  X = ~w~n', [X2]),
        fail
    ;   true
    ),

    writeln('\n3) Все дяди nikita:'),
    (   дядя(X3, nikita),
        format('  X = ~w~n', [X3]),
        fail
    ;   true
    ),

    writeln('\n4) Все двоюродные братья ivan:'),
    (   двоюродный_брат(X4, ivan),
        format('  X = ~w~n', [X4]),
        fail
    ;   true
    ),

    writeln('\n5) Все троюродные сестры ekaterina:'),
    (   троюродная_сестра(X5, ekaterina),
        format('  X = ~w~n', [X5]),
        fail
    ;   true
    ),

    writeln('\n6) Проверка уникальных ответов (без дублей):'),
    setof(X6, предок(fedor, X6), Descendants),
    format('  setof(X, предок(fedor, X), Xs) -> ~w~n', [Descendants]),
    setof(X7, предок(X7, alina), Ancestors),
    format('  setof(X, предок(X, alina), Xs) -> ~w~n', [Ancestors]),

    writeln('\n=== Рекомендация для пошаговой трассировки ==='),
    writeln('Запусти в SWI-Prolog:'),
    writeln('?- trace, предок(fedor, X).'),
    writeln('Используй ; для перехода к следующему решению и наблюдения backtracking.'),
    writeln('Для выхода: notrace.').
