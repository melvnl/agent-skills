import io
import json
import sys
import unittest
from contextlib import redirect_stdout

from helpers import ROOT  # noqa: F401  (adds plugin root to sys.path)
from lib import config, hookio, patterns, shellparse


class ShellParseTest(unittest.TestCase):
    def cmds(self, line):
        return [" ".join(t) for t in shellparse.simple_commands(line)]

    def test_splits_on_control_operators_but_not_inside_quotes(self):
        self.assertEqual(self.cmds("echo 'a && b'; ls -la && git status | head"),
                         ["echo a && b", "ls -la", "git status", "head"])

    def test_strips_wrappers_and_env_assignments(self):
        self.assertEqual(self.cmds("FOO=1 sudo -E env BAR=2 rm -rf /tmp/x"), ["rm -rf /tmp/x"])

    def test_recurses_into_shell_dash_c_and_substitutions(self):
        self.assertEqual(self.cmds("bash -c 'git push --force origin main'"), ["git push --force origin main"])
        self.assertIn("rm -rf build", self.cmds("echo $(rm -rf build)"))
        self.assertIn("whoami", self.cmds("echo `whoami`"))

    def test_absolute_binary_paths_normalize(self):
        self.assertEqual(self.cmds("/bin/rm -rf x"), ["rm -rf x"])


class GlobTest(unittest.TestCase):
    def test_double_star_matches_any_depth(self):
        self.assertTrue(config.matches("/p/src/credit/rules/a.py", ["src/credit/**"], "/p"))
        self.assertTrue(config.matches("/p/app/migrations/0001_x.py", ["**/migrations/*.py"], "/p"))
        self.assertTrue(config.matches("/p/migrations/0001_x.py", ["**/migrations/*.py"], "/p"))
        self.assertFalse(config.matches("/p/app/migrations/sub/x.py", ["**/migrations/*.py"], "/p"))

    def test_basename_patterns(self):
        self.assertTrue(config.matches("/p/deep/.env", [".env"], "/p"))
        self.assertFalse(config.matches("/p/.env.example", [".env"], "/p"))

    def test_outside_project_is_none(self):
        self.assertIsNone(config.relative("/elsewhere/x", "/p"))


class PatternsTest(unittest.TestCase):
    def test_secret_detected_by_name_and_line_without_value(self):
        text = "a = 1\nkey = 'AKIA" + "ABCDEFGHIJKLMNOP'\n"
        self.assertEqual(list(patterns.find_secrets(text)), [("AWS access key id", 2)])

    def test_placeholders_are_ignored(self):
        self.assertEqual(list(patterns.find_secrets("url = 'postgres://user:changeme@db/x'")), [])
        self.assertEqual(list(patterns.find_secrets("url = 'mysql://${USER}:${PASS}@db/x'")), [])


class HookIOTest(unittest.TestCase):
    def test_deny_emits_documented_shape(self):
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            hookio.deny("no")
        self.assertEqual(cm.exception.code, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")

    def test_edited_text_covers_write_edit_multiedit(self):
        data = {"tool_input": {"content": "A", "new_string": "B", "edits": [{"new_string": "C"}, {"old_string": "x"}]}}
        self.assertEqual(hookio.edited_text(data), "A\nB\nC")


if __name__ == "__main__":
    unittest.main()
