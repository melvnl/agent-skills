import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trace_check  # noqa: E402

PRD = """
| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-1 | Submit an application | Must | 1 |
| FR-2 | Evaluate eligibility | Must | 1 |
| FR-3 | Old export | Deprecated | 1 |
| BR-1 | Score >= 600 is eligible | Must | 1 |
| Q-1 | Which bureau? | | |
"""
FEATURES = """
| ID | Feature | Requirements | Phase | Status |
|---|---|---|---|---|
| F-01 | Intake | FR-1 | 1 | ⬜ |
| F-02 | Eligibility | FR-2, BR-1 | 1 | ⬜ |
"""
SPEC = """
| ID | Requirement | Traces to |
|---|---|---|
| F-02-FR-1 | Evaluate score against threshold | FR-2, BR-1 |

| ID | Given | When | Then | Verifies | Method |
|---|---|---|---|---|---|
| AC-1 | score 600 | evaluated | approved | F-02-FR-1, BR-1 | Unit |
"""
TASKS = """
| ID | Task | Depends on | Covers (FR/AC) | Done when | Status |
|---|---|---|---|---|---|
| T-1 | Rule evaluation | — | FR-2, AC-1 | tests pass | ⬜ |
"""
TEST = "def test_threshold():  # F-02 AC-1\n    pass\n"


def build(root, prd=PRD, features=FEATURES, spec=SPEC, tasks=TASKS, test=TEST):
    files = {
        "product/PRD.md": prd,
        "product/FEATURES.md": features,
        "specs/F-02-eligibility/SPEC.md": spec,
        "tasks/F-02-eligibility.md": tasks,
        "tests/test_eligibility.py": test,
    }
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")


class TraceCheckTest(unittest.TestCase):
    def run_check(self, **overrides):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            build(root, **overrides)
            res = trace_check.scan(root, trace_check.DEFAULT_TEST_GLOBS)
            return trace_check.evaluate(res)

    def test_clean_repo_passes(self):
        fail, warn = self.run_check()
        self.assertEqual(fail, [])
        self.assertEqual(warn, [])

    def test_undefined_reference_fails(self):
        fail, _ = self.run_check(features=FEATURES.replace("FR-2, BR-1", "FR-2, BR-1, FR-9"))
        self.assertTrue(any("undefined FR-9" in f for f in fail), fail)

    def test_unowned_requirement_fails_but_deprecated_and_questions_are_exempt(self):
        fail, _ = self.run_check(features=FEATURES.replace("| F-01 | Intake | FR-1 | 1 | ⬜ |\n", ""))
        self.assertTrue(any("FR-1 is owned by no feature" in f for f in fail), fail)
        self.assertFalse(any("FR-3" in f or "Q-1" in f for f in fail), fail)

    def test_acceptance_criterion_without_verifies_fails(self):
        fail, _ = self.run_check(spec=SPEC.replace("| F-02-FR-1, BR-1 | Unit |", "|  | Unit |"))
        self.assertTrue(any("AC-1 verifies no requirement" in f for f in fail), fail)

    def test_spec_requirement_without_acceptance_criterion_fails(self):
        spec = SPEC.replace("| F-02-FR-1 | Evaluate", "| F-02-FR-1 | Evaluate").replace(
            "| F-02-FR-1, BR-1 | Unit |", "| BR-1 | Unit |")
        fail, _ = self.run_check(spec=spec)
        self.assertTrue(any("F-02-FR-1 has no acceptance criterion" in f for f in fail), fail)

    def test_uncited_acceptance_criterion_warns(self):
        fail, warn = self.run_check(test="def test_threshold():\n    pass\n")
        self.assertEqual(fail, [])
        self.assertTrue(any("AC-1 is cited by no test" in w for w in warn), warn)

    def test_ranges_expand(self):
        prd = PRD + "| FR-4 | a | Must | 1 |\n| FR-5 | b | Must | 1 |\n| FR-6 | c | Must | 1 |\n"
        features = FEATURES + "| F-03 | Range | FR-4..FR-6 | 1 | ⬜ |\n"
        fail, _ = self.run_check(prd=prd, features=features)
        self.assertEqual(fail, [])

    def test_not_a_factory_layout_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(trace_check.main(["--root", d]), 2)


if __name__ == "__main__":
    unittest.main()
