import unittest

from helpers import HookTestCase, decision, reason

AWS = "AKIA" + "QWERTYUIOPASDFGH"
GH = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
JWT = "eyJhbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


class DetectSecretExposureTest(HookTestCase):
    SCRIPT = "pre-tool-use/detect-secret-exposure.py"

    def test_write_with_aws_key_denied_without_echoing_value(self):
        code, out, _ = self.hook({"tool_name": "Write", "tool_input": {"file_path": "/p/settings.py", "content": f"x = 1\nKEY = '{AWS}'\n"}})
        self.assertEqual(decision(out), "deny")
        self.assertIn("AWS access key id (line 2)", reason(out))
        self.assertNotIn(AWS, reason(out))

    def test_edit_and_bash_detected(self):
        code, out, _ = self.hook({"tool_name": "Edit", "tool_input": {"file_path": "/p/a.py", "old_string": "x", "new_string": f"token = '{GH}'"}})
        self.assertEqual(decision(out), "deny")
        code, out, _ = self.hook({"tool_name": "Bash", "tool_input": {"command": f"curl -H 'Authorization: Bearer {JWT}' https://api"}})
        self.assertEqual(decision(out), "deny")
        code, out, _ = self.hook({"tool_name": "Write", "tool_input": {"file_path": "/p/k", "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIE\n"}})
        self.assertEqual(decision(out), "deny")

    def test_placeholders_and_normal_code_allowed(self):
        for content in ["AWS_KEY = os.environ['AWS_ACCESS_KEY_ID']", "key = 'AKIAIOSFODNN7EXAMPLE'",
                        "DATABASE_URL = 'mysql://${DB_USER}:${DB_PASS}@db/app'", "token = request.headers.get('Authorization')"]:
            code, out, _ = self.hook({"tool_name": "Write", "tool_input": {"file_path": "/p/a.py", "content": content}})
            self.assertIsNone(decision(out), content)

    def test_old_string_is_not_scanned(self):
        code, out, _ = self.hook({"tool_name": "Edit", "tool_input": {"file_path": "/p/a.py", "old_string": f"k='{AWS}'", "new_string": "k=os.environ['K']"}})
        self.assertIsNone(decision(out))

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
