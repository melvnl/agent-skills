import os
import unittest

from helpers import HookTestCase, decision, reason


class DetectHardcodedCredentialsTest(HookTestCase):
    SCRIPT = "post-tool-use/detect-hardcoded-credentials.py"

    def write(self, rel, content):
        path = os.path.join(self.project, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(content)
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})

    def test_credential_assignment_flagged_with_absolute_line(self):
        code, out, _ = self.write("app/settings.py", "DEBUG = False\nDB_PASSWORD = 'S3cureLongValue'\n")
        self.assertEqual((code, decision(out)), (0, "block"))
        self.assertIn("app/settings.py:2 `DB_PASSWORD`", reason(out))
        self.assertNotIn("S3cureLongValue", reason(out))

    def test_edit_reports_line_in_file(self):
        path = os.path.join(self.project, "svc/client.py")
        os.makedirs(os.path.dirname(path))
        new = "api_key = \"live-9f8e7d6c5b4a\""
        with open(path, "w") as fh:
            fh.write("import os\n\n\n" + new + "\n")
        code, out, _ = self.hook({"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": "x", "new_string": new}})
        self.assertIn("svc/client.py:4", reason(out))

    def test_names_starting_with_the_keyword(self):
        for content in ["password = 'Tr0ub4dor&3x'", "token: str = 'abcdef123456'", "secret_value = 'zx9qp2lm7v'", '{"password": "Tr0ub4dor&3x"}', "cfg = {'api_key': 'k-123456789'}"]:
            code, out, _ = self.write("app/conf.py", content + "\n")
            self.assertEqual(decision(out), "block", content)

    def test_allowed_cases(self):
        for rel, content in [("app/settings.py", "DB_PASSWORD = os.environ['DB_PASSWORD']"),
                             ("app/forms.py", "PASSWORD_FIELD = 'password_field'"),
                             ("app/auth.py", "token_type = 'bearer'"),
                             ("app/settings.py", "SECRET_KEY = 'changeme-in-production'"),
                             ("tests/test_auth.py", "password = 'test-password-123'"),
                             ("docs/setup.md", "password = 'example-secret-value'"),
                             (".env.example", "API_KEY=your-api-key-here")]:
            code, out, _ = self.write(rel, content + "\n")
            self.assertIsNone(decision(out), (rel, content))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
