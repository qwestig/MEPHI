:- encoding(utf8).
:- begin_tests(family_level1).

:- [family].

% 1) Base facts
test(base_parent_true) :-
    родитель(fedor, alexei).

test(base_parent_false, [fail]) :-
    родитель(alexei, fedor).

test(base_gender_true) :-
    мужчина(ivan),
    женщина(sofia).

% 2) Derived basic relations
test(mother_true) :-
    мать(nina, ivan).

test(father_true) :-
    отец(alexei, elena).

test(grandfather_true, [nondet]) :-
    дедушка(fedor, ivan).

test(grandmother_true, [nondet]) :-
    бабушка(galina, maria).

test(brother_true, [nondet]) :-
    брат(ivan, elena).

test(sister_true, [nondet]) :-
    сестра(elena, ivan).

% 3) Uncle / aunt
test(uncle_true, [nondet]) :-
    дядя(dmitry, nikita).

test(aunt_true, [nondet]) :-
    тётя(anna, kirill).

% 4) Recursive relations
test(ancestor_direct_true, [nondet]) :-
    предок(ivan, nikita).

test(ancestor_recursive_true, [nondet]) :-
    предок(fedor, alina).

test(descendant_recursive_true, [nondet]) :-
    потомок(victor, fedor).

test(ancestor_false, [fail]) :-
    предок(nikita, fedor).

% 5) Complex relations
test(first_cousin_brother_true, [nondet]) :-
    двоюродный_брат(sergey, ivan).

test(second_cousin_sister_true, [nondet]) :-
    троюродная_сестра(alina, ekaterina).

% 6) Non-trivial query with expected set
test(all_uncles_of_nikita, true(Uncles == [dmitry])) :-
    setof(U, дядя(U, nikita), Uncles).

test(all_ancestors_of_pavel, true(Ancestors == [boris,fedor,galina,maria,oleg,olga])) :-
    setof(A, предок(A, pavel), Ancestors).

:- end_tests(family_level1).

% Run: swipl -q -l tests.pl -t run_tests
