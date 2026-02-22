:- encoding(utf8).

/*
  Laboratory work #1 (Level 1): genealogy knowledge base.
  Data model:
  - parent(Parent, Child)
  - male(Person)
  - female(Person)
*/

% -------- Base facts: gender --------

male(fedor).
male(alexei).
male(boris).
male(petr).
male(ivan).
male(dmitry).
male(sergey).
male(oleg).
male(nikita).
male(kirill).
male(victor).
male(pavel).

female(galina).
female(nina).
female(olga).
female(larisa).
female(anna).
female(elena).
female(vera).
female(maria).
female(sofia).
female(alina).
female(ekaterina).

% -------- Base facts: parent-child --------

% Generation 0 -> Generation 1
parent(fedor, alexei).
parent(galina, alexei).
parent(fedor, boris).
parent(galina, boris).
parent(fedor, larisa).
parent(galina, larisa).

% Generation 1 -> Generation 2
parent(alexei, ivan).
parent(nina, ivan).
parent(alexei, elena).
parent(nina, elena).

parent(boris, sergey).
parent(olga, sergey).
parent(boris, maria).
parent(olga, maria).

parent(larisa, dmitry).
parent(petr, dmitry).
parent(larisa, anna).
parent(petr, anna).

% Generation 2 -> Generation 3
parent(ivan, nikita).
parent(anna, nikita).
parent(ivan, sofia).
parent(anna, sofia).

parent(elena, kirill).
parent(dmitry, kirill).
parent(elena, alina).
parent(dmitry, alina).

parent(sergey, victor).
parent(vera, victor).
parent(sergey, ekaterina).
parent(vera, ekaterina).

parent(maria, pavel).
parent(oleg, pavel).

% -------- Derived relations --------

mother(Mother, Child) :-
    parent(Mother, Child),
    female(Mother).

father(Father, Child) :-
    parent(Father, Child),
    male(Father).

% Full siblings share both father and mother.
sibling(X, Y) :-
    dif(X, Y),
    father(F, X),
    father(F, Y),
    mother(M, X),
    mother(M, Y).

brother(Brother, Person) :-
    sibling(Brother, Person),
    male(Brother).

sister(Sister, Person) :-
    sibling(Sister, Person),
    female(Sister).

grandparent(Grandparent, Person) :-
    parent(Grandparent, Parent),
    parent(Parent, Person).

grandfather(Grandfather, Person) :-
    grandparent(Grandfather, Person),
    male(Grandfather).

grandmother(Grandmother, Person) :-
    grandparent(Grandmother, Person),
    female(Grandmother).

uncle(Uncle, Person) :-
    parent(Parent, Person),
    brother(Uncle, Parent).

aunt(Aunt, Person) :-
    parent(Parent, Person),
    sister(Aunt, Parent).

ancestor(Ancestor, Person) :-
    parent(Ancestor, Person).
ancestor(Ancestor, Person) :-
    parent(Ancestor, Middle),
    ancestor(Middle, Person).

descendant(Descendant, Ancestor) :-
    ancestor(Ancestor, Descendant).

% First cousins: children of siblings.
first_cousin(X, Y) :-
    dif(X, Y),
    parent(PX, X),
    parent(PY, Y),
    sibling(PX, PY),
    \+ sibling(X, Y).

% Second cousins: children of first cousins.
second_cousin(X, Y) :-
    dif(X, Y),
    parent(PX, X),
    parent(PY, Y),
    first_cousin(PX, PY),
    \+ first_cousin(X, Y),
    \+ sibling(X, Y).

first_cousin_brother(Brother, Person) :-
    first_cousin(Brother, Person),
    male(Brother).

second_cousin_sister(Sister, Person) :-
    second_cousin(Sister, Person),
    female(Sister).

% -------- Required Russian aliases --------

родитель(X, Y) :- parent(X, Y).
мужчина(X) :- male(X).
женщина(X) :- female(X).
мать(X, Y) :- mother(X, Y).
отец(X, Y) :- father(X, Y).
дедушка(X, Y) :- grandfather(X, Y).
бабушка(X, Y) :- grandmother(X, Y).
брат(X, Y) :- brother(X, Y).
сестра(X, Y) :- sister(X, Y).
дядя(X, Y) :- uncle(X, Y).
тётя(X, Y) :- aunt(X, Y).
предок(X, Y) :- ancestor(X, Y).
потомок(X, Y) :- descendant(X, Y).
двоюродный_брат(X, Y) :- first_cousin_brother(X, Y).
троюродная_сестра(X, Y) :- second_cousin_sister(X, Y).
