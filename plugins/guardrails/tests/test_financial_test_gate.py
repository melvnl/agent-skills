import os
import subprocess
import unittest

from helpers import HookTestCase, decision, reason, write_config


def git(project, *args):
    subprocess.run(["git", "-C", project, "-c", "user.email=t@example.com", "-c", "user.name=t"] + list(args),
                   check=True, capture_output=True)


class FinancialTestGateTest(HookTestCase):
    SCRIPT = "pre-tool-use/financial-test-gate.py"

    def setUp(self):
        super().setUp()
        git(self.project, "init", "-q")
        for rel in ["src/credit/rules.py", "src/notify.py", "tests/test_rules.py"]:
            os.makedirs(os.path.dirname(os.path.join(self.project, rel)), exist_ok=True)
            open(os.path.join(self.project, rel), "w").write("x = 1\n")
        git(self.project, "add", ".")
        git(self.project, "commit", "-q", "-m", "init")
        write_config(self.project, {"financial_core": ["src/credit/**"]})

    def change(self, rel, stage=True):
        open(os.path.join(self.project, rel), "a").write("y = 2\n")
        if stage:
            git(self.project, "add", rel)

    def commit(self, command="git commit -m 'change'"):
        return self.hook({"tool_name": "Bash", "tool_input": {"command": command}})

    def test_core_change_without_tests_denied(self):
        self.change("src/credit/rules.py")
        code, out, _ = self.commit()
        self.assertEqual(decision(out), "deny")
        self.assertIn("src/credit/rules.py", reason(out))

    def test_core_change_with_tests_allowed(self):
        self.change("src/credit/rules.py")
        self.change("tests/test_rules.py")
        self.assertIsNone(decision(self.commit()[1]))

    def test_commit_all_includes_unstaged_tracked_changes(self):
        self.change("src/credit/rules.py", stage=False)
        self.assertIsNone(decision(self.commit("git commit -m x")[1]))
        self.assertEqual(decision(self.commit("git commit -am x")[1]), "deny")

    def test_non_core_and_non_commit_commands_pass(self):
        self.change("src/notify.py")
        self.assertIsNone(decision(self.commit()[1]))
        self.change("src/credit/rules.py")
        self.assertIsNone(decision(self.commit("git status && git diff --cached")[1]))

    def test_inactive_without_financial_core(self):
        write_config(self.project, {})
        self.change("src/credit/rules.py")
        self.assertIsNone(decision(self.commit()[1]))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
