import os
import sys
import unittest

from helpers import HookTestCase, decision, reason, write_config

OPT_IN = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "1", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
OPT_OUT = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
FAILING = f"{sys.executable} -c \"import sys; print('a.py:1: problem'); sys.exit(1)\" {{files}}"
PASSING = f"{sys.executable} -c \"import sys; sys.exit(0)\" {{files}}"
SLOW = {"run": f"{sys.executable} -c \"import time; time.sleep(5)\"", "timeout": 1}


class Test(HookTestCase):
    SCRIPT = "post-tool-use/typecheck-after-edit.py"

    def setUp(self):
        super().setUp()
        self.path = os.path.join(self.project, "a.py")
        open(self.path, "w").write("x = 1\n")

    def edit(self, env=OPT_IN):
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": self.path, "content": "x = 1\n"}}, env=env)

    def test_problems_fed_back_with_output(self):
        write_config(self.project, {"commands": {"typecheck": FAILING}})
        code, out, _ = self.edit()
        self.assertEqual(decision(out), "block")
        self.assertIn("a.py:1: problem", reason(out))

    def test_clean_run_is_silent(self):
        write_config(self.project, {"commands": {"typecheck": PASSING}})
        self.assertIsNone(self.edit()[1])

    def test_timeout_is_reported_not_passed(self):
        write_config(self.project, {"commands": {"typecheck": SLOW}})
        code, out, _ = self.edit()
        self.assertIn("timed out", reason(out))

    def test_requires_opt_in_and_config(self):
        write_config(self.project, {"commands": {"typecheck": FAILING}})
        self.assertIsNone(self.edit(env=OPT_OUT)[1])
        write_config(self.project, {})
        self.assertIsNone(self.edit()[1])

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
