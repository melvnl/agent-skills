import os
import subprocess
import unittest

from helpers import HookTestCase, decision, reason


def git(project, *args):
    subprocess.run(["git", "-C", project, "-c", "user.email=t@example.com", "-c", "user.name=t"] + list(args),
                   check=True, capture_output=True)


class ProtectDatabaseMigrationsTest(HookTestCase):
    SCRIPT = "pre-tool-use/protect-database-migrations.py"

    def setUp(self):
        super().setUp()
        git(self.project, "init", "-q")
        os.makedirs(os.path.join(self.project, "app", "migrations"))
        for name in ("0001_initial.py", "__init__.py"):
            open(os.path.join(self.project, "app", "migrations", name), "w").write("# m\n")
        git(self.project, "add", ".")
        git(self.project, "commit", "-q", "-m", "init")

    def edit(self, rel):
        return self.hook({"tool_name": "Edit", "tool_input": {"file_path": os.path.join(self.project, rel), "new_string": "x"}})

    def test_committed_migration_asks(self):
        code, out, _ = self.edit("app/migrations/0001_initial.py")
        self.assertEqual(decision(out), "ask")
        self.assertIn("new migration", reason(out))

    def test_new_migration_and_init_and_other_files_pass(self):
        open(os.path.join(self.project, "app", "migrations", "0002_add_reason.py"), "w").write("# new\n")
        for rel in ["app/migrations/0002_add_reason.py", "app/migrations/__init__.py", "app/models.py"]:
            self.assertIsNone(decision(self.edit(rel)[1]), rel)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
