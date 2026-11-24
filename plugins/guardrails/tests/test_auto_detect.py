"""Auto-detected format/lint: fake tool executables log how they were run (argv, cwd)."""
import json
import os
import stat
import subprocess
import sys
import unittest

from helpers import HookTestCase, decision, reason, write_config

OPT_IN = {"GUARDRAILS_RUN_PROJECT_COMMANDS": "1", "CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS": ""}
FAKE = """#!%s
import json, os, sys
with open(os.environ["FAKE_LOG"], "a") as fh:
    fh.write(json.dumps({"tool": os.path.basename(sys.argv[0]), "argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
args, target = sys.argv[1:], sys.argv[-1]
if {"format", "--write", "-w"} & set(args):
    text = open(target).read()
    open(target, "w").write(text.replace("x=1", "x = 1"))
elif os.environ.get("FAKE_FAIL"):
    print("%%s:1:1: F401 problem" %% target)
    sys.exit(1)
""" % sys.executable


class AutoDetectTest(HookTestCase):
    LINT = "post-tool-use/lint-after-edit.py"
    FORMAT = "post-tool-use/format-after-edit.py"

    def setUp(self):
        super().setUp()
        self.log = os.path.join(self.project, "..", os.path.basename(self.project) + ".log")
        self.env = dict(OPT_IN, FAKE_LOG=self.log)

    # helpers -------------------------------------------------------------------------------------
    def write(self, rel, text=""):
        path = os.path.join(self.project, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
        return path

    def tool(self, rel):
        path = self.write(rel, FAKE)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def edit(self, script, rel, content="x=1\n", **env):
        path = self.write(rel, content)
        self.SCRIPT = script
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}},
                         env=dict(self.env, **env))

    def runs(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as fh:
            return [json.loads(line) for line in fh]

    def notice(self, out):
        self.assertIsNotNone(out)
        self.assertIn("systemMessage", out)  # shown to the user
        self.assertEqual(out["systemMessage"], out["hookSpecificOutput"]["additionalContext"])  # and to Claude
        return out["systemMessage"]

    # Python ---------------------------------------------------------------------------------------
    def test_ruff_lint_runs_on_the_edited_file_and_feeds_back(self):
        self.write("pyproject.toml", "[project]\nname = 'x'\n\n[tool.ruff]\nline-length = 100\n")
        self.tool(".venv/bin/ruff")
        code, out, _ = self.edit(self.LINT, "app/main.py", FAKE_FAIL="1")
        self.assertEqual(decision(out), "block")
        self.assertIn("ruff check", reason(out))
        self.assertIn("F401", reason(out))
        run = self.runs()[0]
        self.assertEqual((run["tool"], run["argv"]), ("ruff", ["check", "app/main.py"]))
        self.assertEqual(os.path.realpath(run["cwd"]), os.path.realpath(self.project))

    def test_ruff_format_rewrites_and_asks_to_reread(self):
        self.write("ruff.toml", "line-length = 100\n")
        self.tool(".venv/bin/ruff")
        code, out, _ = self.edit(self.FORMAT, "app/main.py")
        self.assertIn("Re-read", reason(out))
        self.assertEqual(open(os.path.join(self.project, "app/main.py")).read(), "x = 1\n")

    def test_monorepo_uses_the_nearest_project_and_workspace_venv(self):
        self.write("services/api/pyproject.toml", "[tool.ruff.lint]\nselect = ['F']\n")
        self.tool(".venv/bin/ruff")  # uv workspace: one virtualenv at the root
        self.edit(self.LINT, "services/api/app/users.py")
        run = self.runs()[0]
        self.assertEqual(run["argv"], ["check", "app/users.py"])
        self.assertEqual(os.path.realpath(run["cwd"]), os.path.realpath(os.path.join(self.project, "services/api")))

    def test_configured_but_not_installed_is_mentioned_once(self):
        self.write("pyproject.toml", "[tool.ruff]\n")
        code, out, _ = self.edit(self.LINT, "a.py")
        self.assertIn("not installed", self.notice(out))
        self.assertIsNone(self.edit(self.LINT, "b.py")[1])
        self.assertEqual(self.runs(), [])

    def test_no_ruff_config_is_mentioned(self):
        self.write("pyproject.toml", "[project]\nname = 'x'\n")
        self.tool(".venv/bin/ruff")
        code, out, _ = self.edit(self.LINT, "a.py")
        self.assertIn("no Python linter is configured", self.notice(out))
        self.assertEqual(self.runs(), [])

    def test_tracked_executable_is_never_run(self):
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.tool(".venv/bin/ruff")
        subprocess.run(["git", "-C", self.project, "init", "-q"], check=True)
        subprocess.run(["git", "-C", self.project, "add", "-f", ".venv/bin/ruff"], check=True)
        code, out, _ = self.edit(self.LINT, "a.py")
        self.assertIn("tracked by git", self.notice(out))
        self.assertEqual(self.runs(), [])

    # other file types ------------------------------------------------------------------------------
    def test_unrecognized_type_is_mentioned_once_for_both_hooks(self):
        code, out, _ = self.edit(self.LINT, "docs/guide.md", "# Guide\n")
        self.assertIn("for .md files", self.notice(out))
        self.assertIsNone(self.edit(self.FORMAT, "docs/other.md", "# Other\n")[1])

    def test_eslint_and_prettier(self):
        self.write("package.json", '{"name": "web", "prettier": {"semi": false}}')
        self.write("eslint.config.js", "export default []\n")
        self.tool("node_modules/.bin/eslint")
        self.tool("node_modules/.bin/prettier")
        code, out, _ = self.edit(self.LINT, "src/page.tsx", FAKE_FAIL="1")
        self.assertIn("eslint", reason(out))
        self.edit(self.FORMAT, "src/page.tsx")
        self.assertEqual([(r["tool"], r["argv"]) for r in self.runs()],
                         [("eslint", ["src/page.tsx"]), ("prettier", ["--write", "src/page.tsx"])])

    def test_two_configured_linters_run_neither_and_say_so(self):
        self.write("package.json", "{}")
        self.write("biome.json", "{}")
        self.write(".eslintrc.json", "{}")
        self.tool("node_modules/.bin/eslint")
        self.tool("node_modules/.bin/biome")
        code, out, _ = self.edit(self.LINT, "src/a.ts")
        self.assertIn("both biome and eslint", self.notice(out))
        self.assertEqual(self.runs(), [])

    def test_go_formats_with_gofmt_and_mentions_missing_linter(self):
        self.write("go.mod", "module example.com/x\n")
        bindir = os.path.dirname(self.tool("../%s-bin/gofmt" % os.path.basename(self.project)))
        path_env = bindir + os.pathsep + os.environ.get("PATH", "")
        self.edit(self.FORMAT, "cmd/main.go", PATH=path_env)
        self.assertEqual([(r["tool"], r["argv"]) for r in self.runs()], [("gofmt", ["-w", "cmd/main.go"])])
        code, out, _ = self.edit(self.LINT, "cmd/main.go", PATH=path_env)
        self.assertIn("no Go linter is auto-detected", self.notice(out))

    # precedence and switches -----------------------------------------------------------------------
    def test_configured_command_wins_over_detection(self):
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.tool(".venv/bin/ruff")
        write_config(self.project, {"commands": {"lint": f"{sys.executable} -c \"print('custom'); exit(1)\" {{files}}"}})
        code, out, _ = self.edit(self.LINT, "a.py")
        self.assertIn("custom", reason(out))
        self.assertEqual(self.runs(), [])

    def test_auto_detect_off_and_opt_out_are_silent(self):
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.tool(".venv/bin/ruff")
        self.assertIsNone(self.edit(self.LINT, "a.py", GUARDRAILS_RUN_PROJECT_COMMANDS="")[1])
        write_config(self.project, {"auto_detect": False})
        self.assertIsNone(self.edit(self.LINT, "a.py")[1])
        self.assertEqual(self.runs(), [])


if __name__ == "__main__":
    unittest.main()
