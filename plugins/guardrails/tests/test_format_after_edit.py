import os
import sys
import unittest

from helpers import HookTestCase, decision, reason, write_config

OPT_IN = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "1", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
OPT_OUT = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
# A tiny "formatter": uppercases the file. Uses the interpreter running the tests.
UPPER = f"{sys.executable} -c \"import sys;p=sys.argv[1];s=open(p).read();open(p,'w').write(s.upper())\" {{files}}"


class FormatAfterEditTest(HookTestCase):
    SCRIPT = "post-tool-use/format-after-edit.py"

    def setUp(self):
        super().setUp()
        self.path = os.path.join(self.project, "a.py")
        with open(self.path, "w") as fh:
            fh.write("x = 1\n")

    def edit(self, env):
        return self.hook({"tool_name": "Edit", "tool_input": {"file_path": self.path, "new_string": "x = 1"}}, env=env)

    def test_reformatted_file_adds_reread_context(self):
        write_config(self.project, {"commands": {"format": UPPER}})
        code, out, _ = self.edit(OPT_IN)
        self.assertEqual(code, 0)
        self.assertIn("Re-read", reason(out))
        self.assertEqual(open(self.path).read(), "X = 1\n")

    def test_not_run_without_opt_in(self):
        write_config(self.project, {"commands": {"format": UPPER}})
        code, out, _ = self.edit(OPT_OUT)
        self.assertIsNone(out)
        self.assertEqual(open(self.path).read(), "x = 1\n")

    def test_not_run_without_config_or_outside_globs(self):
        code, out, _ = self.edit(OPT_IN)
        self.assertIsNone(out)
        write_config(self.project, {"commands": {"format": {"run": UPPER, "files": ["**/*.js"]}}})
        code, out, _ = self.edit(OPT_IN)
        self.assertIsNone(out)

    def test_failing_formatter_is_fed_back(self):
        write_config(self.project, {"commands": {"format": f"{sys.executable} -c \"import sys; print('boom'); sys.exit(3)\""}})
        code, out, _ = self.edit(OPT_IN)
        self.assertEqual(decision(out), "block")
        self.assertIn("exit 3", reason(out))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
