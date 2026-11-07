import os
import unittest

from helpers import HookTestCase, decision, reason


class DetectSensitiveLoggingTest(HookTestCase):
    SCRIPT = "post-tool-use/detect-sensitive-logging.py"

    def write(self, content, name="svc.py"):
        path = os.path.join(self.project, name)
        with open(path, "w") as fh:
            fh.write(content)
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})

    def test_flagged(self):
        cases = {
            'logger.info("login", extra={"email": user.email})': "`email`",
            'logger.debug(f"headers={request.headers}")': "request.headers",
            'log.warning("auth failed", extra={"authorization": auth_header})': "`authorization`",
            "logging.error('payload %s', request.data)": "request.data",
            'logger.info("applicant", extra={"national_id": app.nik})': "`national_id`",
            'self.logger.info("token issued", extra=dict(access_token=tok))': "`access_token`",
            'logger.info("profile", extra=vars(profile))': "vars(profile)",
        }
        for line, expected in cases.items():
            code, out, _ = self.write("import logging\n" + line + "\n")
            self.assertEqual(decision(out), "block", line)
            self.assertIn(expected, reason(out), line)
            self.assertIn("svc.py:2", reason(out), line)

    def test_multiline_call_is_scanned(self):
        code, out, _ = self.write('logger.info(\n    "login",\n    extra={\n        "phone": user.phone,\n    },\n)\n')
        self.assertIn("`phone`", reason(out))
        self.assertIn("svc.py:1", reason(out))

    def test_not_flagged(self):
        for line in ['logger.info("authorization_failed", extra={"request_id": rid, "reason_code": code})',
                     'logger.info("password reset requested", extra={"has_email": True, "customer_ref": ref})',
                     'logger.info("decision_completed", extra={"status": status, "duration_ms": ms})',
                     'logger.warning("token_expired", extra={"token_type": "refresh", "email_verified": False})',
                     'logger.error("Invalid email format")',
                     'email = user.email  # not a log call',
                     'logger.info("otp_sent", extra={"otp_length": 6})']:
            code, out, _ = self.write(line + "\n")
            self.assertIsNone(decision(out), line)

    def test_non_python_files_ignored(self):
        code, out, _ = self.write('logger.info("x", {email})\n', name="notes.md")
        self.assertIsNone(out)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
