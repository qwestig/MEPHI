"""Проверки парсера и верификатора с примерами входа и результата."""

import unittest

from formulas import (
    FormulaError,
    Implication,
    find_substitution,
    parse,
    substitute,
)
from verifier import AXIOMS, ProofError, ProofSession


PROOF = [
    "(s ⊃ (r ⊃ q)) ⊃ ((s ⊃ r) ⊃ (s ⊃ q))",
    "(p ⊃ (r ⊃ q)) ⊃ ((p ⊃ r) ⊃ (p ⊃ q))",
    "(p ⊃ (r ⊃ p)) ⊃ ((p ⊃ r) ⊃ (p ⊃ p))",
    "p ⊃ (r ⊃ p)",
    "p ⊃ r ⊃ (p ⊃ p)",
    "(p ⊃ (q ⊃ p)) ⊃ (p ⊃ p)",
    "p ⊃ p",
]


class ParserTests(unittest.TestCase):
    def test_parses_nested_formula(self):
        self.assertEqual(str(parse("((p ⊃ q) ⊃ r)")), "((p ⊃ q) ⊃ r)")

    def test_implication_is_left_associative(self):
        self.assertEqual(parse("p ⊃ q ⊃ r"), parse("(p ⊃ q) ⊃ r"))
        self.assertNotEqual(parse("p ⊃ q ⊃ r"), parse("p ⊃ (q ⊃ r)"))

    def test_rejects_malformed_input_and_other_operators(self):
        for text in ["", "p ⊃", "⊃ p", "(p ⊃ q", "p ⊃ q)", "p -> q", "p → q", "p & q", "pq"]:
            with self.subTest(text=text), self.assertRaises(FormulaError):
                parse(text)

    def test_formula_tree_has_implication_parts(self):
        formula = parse("p ⊃ q")
        self.assertIsInstance(formula, Implication)
        self.assertEqual(str(formula.left), "p")
        self.assertEqual(str(formula.right), "q")


class SubstitutionTests(unittest.TestCase):
    def test_one_variable_substitution(self):
        source = AXIOMS["K"]
        target = parse("(a ⊃ b) ⊃ (q ⊃ (a ⊃ b))")
        self.assertEqual(find_substitution(source, target), ("p", parse("a ⊃ b")))
        self.assertEqual(substitute(source, "p", parse("a ⊃ b")), target)

    def test_rejects_partial_or_multiple_substitutions(self):
        self.assertIsNone(find_substitution(AXIOMS["K"], parse("a ⊃ (q ⊃ p)")))
        self.assertIsNone(find_substitution(AXIOMS["K"], parse("a ⊃ (b ⊃ a)")))

    def test_f_is_constant_not_a_substitution_variable(self):
        self.assertIsNone(find_substitution(AXIOMS["E¬"], parse("((p ⊃ a) ⊃ a) ⊃ p")))
        with self.assertRaises(ValueError):
            substitute(AXIOMS["E¬"], "f", parse("a"))


class VerifierTests(unittest.TestCase):
    def test_axiom_and_beta_are_accepted(self):
        session = ProofSession()
        self.assertEqual(session.add("p ⊃ (q ⊃ p)")[1].rule, "axiom")
        self.assertEqual(session.add("p ⊃ (r ⊃ p)")[1].rule, "β")

    def test_rejects_well_formed_but_undeduced_formula(self):
        with self.assertRaises(ProofError):
            ProofSession().add("p")

    def test_rejected_input_does_not_enter_step_list(self):
        session = ProofSession()
        for text in ["p ⊃", "p"]:
            try:
                session.add(text)
            except (FormulaError, ProofError):
                pass
        self.assertEqual(session.steps, [])

    def test_full_proof_and_show_input_output(self):
        session = ProofSession()
        expected_rules = ["β", "β", "β", "β", "MP", "β", "MP"]
        for text, expected_rule in zip(PROOF, expected_rules):
            formula, reason = session.add(text)
            print(f"ВХОД: {text}")
            print(f"ВЫХОД: {reason.describe(formula)}")
            print(f"ОЖИДАЛОСЬ: шаг принят по правилу {expected_rule}\n")
            self.assertEqual(reason.rule, expected_rule)
        self.assertEqual(str(session.steps[-1][0]), "(p ⊃ p)")
        self.assertEqual(len(session.steps), 7)


if __name__ == "__main__":
    unittest.main()
