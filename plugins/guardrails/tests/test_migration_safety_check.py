import os
import unittest

from helpers import HookTestCase, decision, reason

DJANGO_HEADER = "from django.db import migrations, models\n\n\nclass Migration(migrations.Migration):\n    operations = [\n"


class MigrationSafetyCheckTest(HookTestCase):
    SCRIPT = "post-tool-use/migration-safety-check.py"

    def write(self, rel, content):
        path = os.path.join(self.project, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(content)
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})

    def test_destructive_django_ops_flagged(self):
        ops = ("        migrations.RemoveField(model_name='application', name='legacy_score'),\n"
               "        migrations.RenameField('application', 'score', 'bureau_score'),\n"
               "        migrations.AddField('application', 'reason', models.CharField(max_length=64)),\n"
               "        migrations.RunPython(backfill_reason),\n    ]\n")
        code, out, _ = self.write("app/migrations/0007_x.py", DJANGO_HEADER + ops)
        text = reason(out)
        self.assertEqual(decision(out), "block")
        for expected in ["RemoveField", "RenameField", "AddField NOT NULL", "RunPython without a reverse", "0007_x.py:6"]:
            self.assertIn(expected, text)

    def test_destructive_sql_flagged(self):
        sql = ("ALTER TABLE decision DROP COLUMN legacy;\nTRUNCATE audit_tmp;\n"
               "ALTER TABLE application ADD COLUMN reason VARCHAR(64) NOT NULL;\n")
        code, out, _ = self.write("db/migrations/V7__x.sql", sql)
        for expected in ["DROP", "TRUNCATE", "NOT NULL column without DEFAULT"]:
            self.assertIn(expected, reason(out))

    def test_safe_migrations_pass(self):
        ops = ("        migrations.AddField('application', 'reason', models.CharField(max_length=64, null=True)),\n"
               "        migrations.RunPython(backfill_reason, migrations.RunPython.noop),\n    ]\n")
        self.assertIsNone(decision(self.write("app/migrations/0008_y.py", DJANGO_HEADER + ops)[1]))
        sql = "ALTER TABLE application ADD COLUMN reason VARCHAR(64) NULL;\nALTER TABLE a ADD COLUMN n INT NOT NULL DEFAULT 0;\n"
        self.assertIsNone(decision(self.write("db/migrations/V8__y.sql", sql)[1]))

    def test_non_migration_files_ignored(self):
        self.assertIsNone(self.write("app/models.py", "# RemoveField( mention\n")[1])

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
