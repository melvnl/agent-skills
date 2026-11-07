import os
import subprocess
import sys
import unittest

from helpers import HookTestCase, decision, reason, write_config

OPT_IN = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "1", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
OPT_OUT = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
FAIL = f"{sys.executable} -c \"import sys; print('2 failed'); sys.exit(1)\""
PASS = f"{sys.executable} -c \"import sys; sys.exit(0)\""


def git(project, *args):
    subprocess.run(["git", "-C", project] + list(args), check=True, capture_output=True)


class VerifyBeforeStopTest(HookTestCase):
    SCRIPT = "stop/verify-before-stop.py"

    def setUp(self):
        super().setUp()
        git(self.project, "init", "-q")
        git(self.project, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")

    def dirty(self):
        open(os.path.join(self.project, "a.py"), "w").write("x = 1\n")

    def test_failure_blocks_stop_once(self):
        write_config(self.project, {"commands": {"verify": FAIL}})
        self.dirty()
        code, out, _ = self.hook({"hook_event_name": "Stop", "stop_hook_active": False}, env=OPT_IN)
        self.assertEqual(decision(out), "block")
        self.assertIn("2 failed", reason(out))
        code, out, _ = self.hook({"hook_event_name": "Stop", "stop_hook_active": True}, env=OPT_IN)
        self.assertIsNone(out)

    def test_pass_and_clean_tree_are_silent(self):
        write_config(self.project, {"commands": {"verify": FAIL}})
        git(self.project, "add", ".")
        git(self.project, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "cfg")
        self.assertIsNone(self.hook({"stop_hook_active": False}, env=OPT_IN)[1])  # clean tree: nothing to verify
        write_config(self.project, {"commands": {"verify": PASS}})
        self.assertIsNone(self.hook({"stop_hook_active": False}, env=OPT_IN)[1])

    def test_requires_opt_in(self):
        write_config(self.project, {"commands": {"verify": FAIL}})
        self.dirty()
        self.assertIsNone(self.hook({"stop_hook_active": False}, env=OPT_OUT)[1])

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
