import os
import subprocess
import unittest

from helpers import HookTestCase, reason, write_config


class SessionContextInitTest(HookTestCase):
    SCRIPT = "session/session-context-init.py"

    def make_factory(self):
        os.makedirs(os.path.join(self.project, ".factory"))
        os.makedirs(os.path.join(self.project, "tasks"))
        with open(os.path.join(self.project, "tasks", "STATUS.md"), "w") as fh:
            fh.write("# Status\n\n| Phase | 1 |\n" + "".join(f"line {i}\n" for i in range(100)))

    def test_factory_repo_gets_status_and_git_context(self):
        self.make_factory()
        subprocess.run(["git", "-C", self.project, "init", "-q"], check=True)
        write_config(self.project, {"financial_core": ["src/credit/**"]})
        code, out, _ = self.hook({"hook_event_name": "SessionStart", "source": "startup"})
        text = reason(out)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("| Phase | 1 |", text)
        self.assertIn("Git: branch", text)
        self.assertIn("financial_core", text)
        self.assertNotIn("line 60", text)  # bounded snapshot

    def test_compact_adds_reverification_reminder(self):
        self.make_factory()
        code, out, _ = self.hook({"hook_event_name": "SessionStart", "source": "compact"})
        self.assertIn("re-read tasks/STATUS.md", reason(out))

    def test_non_factory_repo_is_silent(self):
        code, out, _ = self.hook({"hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual((code, out), (0, None))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
