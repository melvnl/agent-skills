import json
import os
import stat
import tempfile
import unittest

from helpers import HookTestCase, write_config

AWS = "AKIA" + "QWERTYUIOPASDFGH"


class SensitiveOperationAuditTest(HookTestCase):
    SCRIPT = "post-tool-use/sensitive-operation-audit.py"

    def setUp(self):
        super().setUp()
        self.data_dir = tempfile.mkdtemp()
        self.env = {"CLAUDE_PLUGIN_DATA": self.data_dir}

    def records(self):
        path = os.path.join(self.data_dir, "audit.jsonl")
        if not os.path.exists(path):
            return []
        return [json.loads(l) for l in open(path)]

    def bash(self, command):
        return self.hook({"tool_name": "Bash", "tool_input": {"command": command}}, env=self.env)

    def test_sensitive_commands_recorded_with_redaction_and_private_mode(self):
        code, out, _ = self.bash(f"AWS_ACCESS_KEY_ID={AWS} DB_PASSWORD=hunter22 git push origin main")
        self.assertEqual((code, out), (0, None))
        rec = self.records()[0]
        self.assertEqual(rec["category"], "git:push")
        self.assertNotIn(AWS, rec["command"])
        self.assertNotIn("hunter22", rec["command"])
        mode = stat.S_IMODE(os.stat(os.path.join(self.data_dir, "audit.jsonl")).st_mode)
        self.assertEqual(mode, 0o600)
        for cmd, cat in [("python manage.py migrate", "django:migrate"), ("terraform apply", "terraform:apply"),
                         ("kubectl rollout restart deploy/x", "kubectl:rollout"), ("git commit -m x", "git:commit")]:
            self.bash(cmd)
            self.assertEqual(self.records()[-1]["category"], cat, cmd)

    def test_edits_to_protected_paths_recorded(self):
        write_config(self.project, {"financial_core": ["src/credit/**"]})
        self.hook({"tool_name": "Edit", "tool_input": {"file_path": f"{self.project}/src/credit/rules.py"}}, env=self.env)
        self.hook({"tool_name": "Write", "tool_input": {"file_path": f"{self.project}/app/migrations/0002_x.py"}}, env=self.env)
        self.assertEqual([r["category"] for r in self.records()], ["edit:financial_core", "edit:migration"])
        self.assertEqual(self.records()[0]["path"], "src/credit/rules.py")

    def test_ordinary_actions_not_recorded_and_no_data_dir_is_silent(self):
        self.bash("git status && pytest -q")
        self.hook({"tool_name": "Edit", "tool_input": {"file_path": f"{self.project}/src/app.py"}}, env=self.env)
        self.assertEqual(self.records(), [])
        code, out, _ = self.hook({"tool_name": "Bash", "tool_input": {"command": "git push"}}, env={"CLAUDE_PLUGIN_DATA": ""})
        self.assertEqual((code, out), (0, None))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
