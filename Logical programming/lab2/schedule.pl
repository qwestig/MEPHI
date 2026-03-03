:- encoding(utf8).
:- use_module(library(lists)).

/*
  Laboratory work #2 (Level 1): synthetic schedule knowledge base.
  Core fact:
  - lesson(Group, Subject, Teacher, Day, Time, Room)
*/

% -------- Domain facts --------

group(g1).
group(g2).
group(g3).
group(g4).
group(g5).

subject(matan).
subject(algebra).
subject(informatics).
subject(physics).
subject(english).
subject(history).
subject(philosophy).
subject(economics).
subject(programming).
subject(logic).

teacher(ivanov).
teacher(petrova).
teacher(smirnov).
teacher(sidorov).
teacher(kuznetsova).

room(a101).
room(a102).
room(a103).
room(a104).
room(a105).
room(a106).
room(a107).
room(a108).
room(a109).
room(a110).

day(mon).
day(tue).
day(wed).
day(thu).
day(fri).

time_slot('08:00', 1).
time_slot('10:00', 2).
time_slot('12:00', 3).
time_slot('14:00', 4).
time_slot('16:00', 5).
time_slot('18:00', 6).

% -------- Weekly schedule --------

% Monday
lesson(g1, matan, ivanov, mon, '08:00', a101).
lesson(g1, programming, smirnov, mon, '12:00', a102).
lesson(g2, english, petrova, mon, '10:00', a103).
lesson(g2, physics, sidorov, mon, '12:00', a104).
lesson(g3, algebra, ivanov, mon, '10:00', a105).
lesson(g3, history, kuznetsova, mon, '14:00', a106).
lesson(g4, informatics, smirnov, mon, '08:00', a107).
lesson(g4, philosophy, petrova, mon, '10:00', a108).
lesson(g5, economics, sidorov, mon, '12:00', a109).
lesson(g5, logic, ivanov, mon, '14:00', a110).

% Tuesday
lesson(g1, physics, sidorov, tue, '10:00', a104).
lesson(g1, english, petrova, tue, '14:00', a103).
lesson(g2, matan, ivanov, tue, '08:00', a101).
lesson(g2, programming, smirnov, tue, '12:00', a102).
lesson(g3, philosophy, petrova, tue, '08:00', a108).
lesson(g3, informatics, kuznetsova, tue, '12:00', a107).
lesson(g4, history, petrova, tue, '12:00', a106).
lesson(g4, algebra, ivanov, tue, '14:00', a105).
lesson(g5, english, petrova, tue, '08:00', a103).
lesson(g5, programming, smirnov, tue, '10:00', a102).

% Wednesday
lesson(g1, logic, ivanov, wed, '10:00', a101).
lesson(g1, informatics, kuznetsova, wed, '12:00', a107).
lesson(g2, economics, sidorov, wed, '10:00', a109).
lesson(g2, history, petrova, wed, '14:00', a106).
lesson(g3, programming, smirnov, wed, '08:00', a102).
lesson(g3, physics, sidorov, wed, '12:00', a104).
lesson(g4, english, petrova, wed, '10:00', a103).
lesson(g4, matan, ivanov, wed, '12:00', a105).
lesson(g5, philosophy, kuznetsova, wed, '10:00', a108).
lesson(g5, algebra, ivanov, wed, '14:00', a110).

% Thursday
lesson(g1, history, petrova, thu, '08:00', a106).
lesson(g1, economics, sidorov, thu, '10:00', a109).
lesson(g2, logic, ivanov, thu, '12:00', a101).
lesson(g2, english, petrova, thu, '14:00', a103).
lesson(g3, matan, ivanov, thu, '10:00', a105).
lesson(g3, philosophy, petrova, thu, '12:00', a108).
lesson(g4, programming, smirnov, thu, '08:00', a102).
lesson(g4, physics, sidorov, thu, '14:00', a104).
lesson(g5, informatics, kuznetsova, thu, '12:00', a107).
lesson(g5, history, petrova, thu, '14:00', a106).

% Friday
lesson(g1, programming, smirnov, fri, '08:00', a102).
lesson(g1, philosophy, petrova, fri, '10:00', a108).
lesson(g2, informatics, kuznetsova, fri, '08:00', a107).
lesson(g2, physics, sidorov, fri, '10:00', a104).
lesson(g3, english, petrova, fri, '12:00', a103).
lesson(g3, economics, sidorov, fri, '14:00', a109).
lesson(g4, logic, ivanov, fri, '10:00', a101).
lesson(g4, history, kuznetsova, fri, '12:00', a106).
lesson(g5, matan, ivanov, fri, '08:00', a105).
lesson(g5, programming, smirnov, fri, '12:00', a110).

% -------- Level 1 predicates --------

free_room(Day, Time, Room) :-
    room(Room),
    day(Day),
    time_slot(Time, _),
    \+ lesson(_, _, _, Day, Time, Room).

group_load(Group, Count) :-
    group(Group),
    findall(1, lesson(Group, _, _, _, _, _), Lessons),
    length(Lessons, Count).

schedule_windows(Group, WindowsCount) :-
    group(Group),
    findall(W, (day(Day), windows_in_day(Group, Day, W)), DayWindows),
    sum_list(DayWindows, WindowsCount).

windows_in_day(Group, Day, Windows) :-
    day(Day),
    findall(Slot, (lesson(Group, _, _, Day, Time, _), time_slot(Time, Slot)), Slots),
    sort(Slots, Sorted),
    windows_between_lessons(Sorted, Windows).

windows_between_lessons([], 0).
windows_between_lessons([_], 0).
windows_between_lessons(Slots, Windows) :-
    Slots = [First | _],
    last(Slots, Last),
    findall(
        GapSlot,
        (between(First, Last, GapSlot), \+ member(GapSlot, Slots)),
        Gaps
    ),
    length(Gaps, Windows).

% -------- Extra helper predicates for queries --------

group_subject_time(Group, Subject, Day, Time) :-
    lesson(Group, Subject, _, Day, Time, _).

groups_of_teacher(Teacher, Groups) :-
    teacher(Teacher),
    findall(Group, lesson(Group, _, Teacher, _, _, _), RawGroups),
    sort(RawGroups, Groups).

teacher_free_day(Teacher, Day) :-
    teacher(Teacher),
    day(Day),
    \+ lesson(_, _, Teacher, Day, _, _).

teacher_free_days(Teacher, Days) :-
    teacher(Teacher),
    findall(Day, teacher_free_day(Teacher, Day), RawDays),
    sort(RawDays, Days).

% -------- Required Russian aliases --------

группа(X) :- group(X).
предмет(X) :- subject(X).
преподаватель(X) :- teacher(X).
аудитория(X) :- room(X).
день(X) :- day(X).
занятие(G, S, T, D, Time, R) :- lesson(G, S, T, D, Time, R).

свободна_аудитория(Day, Time, Room) :- free_room(Day, Time, Room).
нагрузка_группы(Group, Count) :- group_load(Group, Count).
окна_в_расписании(Group, WindowsCount) :- schedule_windows(Group, WindowsCount).

когда_у_группы_предмет(Group, Subject, Day, Time) :-
    group_subject_time(Group, Subject, Day, Time).

группы_преподавателя(Teacher, Groups) :-
    groups_of_teacher(Teacher, Groups).

свободный_день_преподавателя(Teacher, Day) :-
    teacher_free_day(Teacher, Day).

свободные_дни_преподавателя(Teacher, Days) :-
    teacher_free_days(Teacher, Days).
