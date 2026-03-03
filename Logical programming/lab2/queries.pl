:- encoding(utf8).
:- begin_tests(schedule_level1).

:- [schedule].

% 1) Когда у группы g1 предмет logic?
test(group_subject_time_logic_g1, all((Day, Time) == [(wed, '10:00')])) :-
    когда_у_группы_предмет(g1, logic, Day, Time).

% 2) Когда у группы g3 предмет economics?
test(group_subject_time_economics_g3, all((Day, Time) == [(fri, '14:00')])) :-
    когда_у_группы_предмет(g3, economics, Day, Time).

% 3) Какие аудитории свободны в среду в 10:00?
test(free_rooms_wed_10, true(Rooms == [a102,a104,a105,a106,a107,a110])) :-
    setof(R, свободна_аудитория(wed, '10:00', R), Rooms).

% 4) У каких групп занятия ведёт ivanov?
test(groups_of_ivanov, true(Groups == [g1,g2,g3,g4,g5])) :-
    группы_преподавателя(ivanov, Groups).

% 5) Нагрузка группы g1 (количество пар в неделю).
test(group_load_g1, true(Count == 10)) :-
    нагрузка_группы(g1, Count).

% 6) Нагрузка группы g4.
test(group_load_g4, true(Count == 10)) :-
    нагрузка_группы(g4, Count).

% 7) Окна в расписании группы g1.
test(windows_g1, true(Windows == 2)) :-
    окна_в_расписании(g1, Windows).

% 8) Окна в расписании группы g3.
test(windows_g3, true(Windows == 3)) :-
    окна_в_расписании(g3, Windows).

% 9) Какие дни свободны у преподавателя smirnov?
test(free_days_smirnov, true(Days == [])) :-
    свободные_дни_преподавателя(smirnov, Days).

% 10) Проверка занятости аудитории: a101 занята в понедельник в 08:00.
test(room_busy_mon_08, [fail]) :-
    свободна_аудитория(mon, '08:00', a101).

% 11) Проверка: в пятницу в 18:00 любая аудитория свободна (нет занятий).
test(all_rooms_free_fri_18, true(Rooms == [a101,a102,a103,a104,a105,a106,a107,a108,a109,a110])) :-
    setof(R, свободна_аудитория(fri, '18:00', R), Rooms).

% 12) У группы g5 есть programming во вторник.
test(g5_programming_tue, [nondet]) :-
    когда_у_группы_предмет(g5, programming, tue, '10:00').

:- end_tests(schedule_level1).

print_case_result(Index, Name, Expected, Actual) :-
    (   Expected == Actual
    ->  Status = 'PASS'
    ;   Status = 'FAIL'
    ),
    format('[~w] ~w~n', [Index, Name]),
    format('    expected: ~q~n', [Expected]),
    format('    actual:   ~q~n', [Actual]),
    format('    status:   ~w~n~n', [Status]).

run_demo_queries :-
    findall((Day, Time), plunit_schedule_level1:когда_у_группы_предмет(g1, logic, Day, Time), G1Logic),
    print_case_result(1, 'g1 - logic', [(wed, '10:00')], G1Logic),

    findall((Day, Time), plunit_schedule_level1:когда_у_группы_предмет(g3, economics, Day, Time), G3Eco),
    print_case_result(2, 'g3 - economics', [(fri, '14:00')], G3Eco),

    setof(R, plunit_schedule_level1:свободна_аудитория(wed, '10:00', R), FreeWed10),
    print_case_result(3, 'free rooms wed 10:00', [a102,a104,a105,a106,a107,a110], FreeWed10),

    plunit_schedule_level1:группы_преподавателя(ivanov, IvanovGroups),
    print_case_result(4, 'groups of ivanov', [g1,g2,g3,g4,g5], IvanovGroups),

    plunit_schedule_level1:нагрузка_группы(g1, LoadG1),
    print_case_result(5, 'load g1', 10, LoadG1),

    plunit_schedule_level1:нагрузка_группы(g4, LoadG4),
    print_case_result(6, 'load g4', 10, LoadG4),

    plunit_schedule_level1:окна_в_расписании(g1, WindowsG1),
    print_case_result(7, 'windows g1', 2, WindowsG1),

    plunit_schedule_level1:окна_в_расписании(g3, WindowsG3),
    print_case_result(8, 'windows g3', 3, WindowsG3),

    plunit_schedule_level1:свободные_дни_преподавателя(smirnov, SmirnovFreeDays),
    print_case_result(9, 'free days smirnov', [], SmirnovFreeDays),

    (   plunit_schedule_level1:свободна_аудитория(mon, '08:00', a101)
    ->  MonBusyCheck = free
    ;   MonBusyCheck = busy
    ),
    print_case_result(10, 'room a101 mon 08:00', busy, MonBusyCheck),

    setof(R, plunit_schedule_level1:свободна_аудитория(fri, '18:00', R), FreeFri18),
    print_case_result(11, 'free rooms fri 18:00', [a101,a102,a103,a104,a105,a106,a107,a108,a109,a110], FreeFri18),

    (   plunit_schedule_level1:когда_у_группы_предмет(g5, programming, tue, '10:00')
    ->  G5ProgTue = yes
    ;   G5ProgTue = no
    ),
    print_case_result(12, 'g5 programming tue 10:00', yes, G5ProgTue).

run_level1_checks :-
    format('=== Unit tests (plunit) ===~n', []),
    run_tests([schedule_level1]),
    format('~n=== Demo output (query results) ===~n', []),
    run_demo_queries.

% Run full checks with visible test work:
% swipl -q -l queries.pl -g run_level1_checks -t halt
