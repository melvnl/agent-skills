import os
import unittest

from helpers import HookTestCase, decision, reason, write_config


class ValidateLogSchemaTest(HookTestCase):
    SCRIPT = "post-tool-use/validate-log-schema.py"

    def write(self, content):
        path = os.path.join(self.project, "svc.py")
        open(path, "w").write(content)
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})

    def test_inactive_without_configuration(self):
        self.assertIsNone(self.write('logger.info(f"user {uid} logged in")\n')[1])

    def test_violations_reported(self):
        write_config(self.project, {"logging": {"event_name_pattern": "^[a-z][a-z0-9_]*$"}})
        for line, expected in [('logger.info(f"user {uid} logged in")', "f-string"),
                               ('logger.info("Decision made for %s" % ref)', "formatting"),
                               ('logger.info("Decision Made")', "doesn't match"),
                               ("logger.info(message)", "not a constant")]:
            code, out, _ = self.write(line + "\n")
            self.assertEqual(decision(out), "block", line)
            self.assertIn(expected, reason(out), line)

    def test_conforming_calls_pass(self):
        write_config(self.project, {"logging": {"event_name_pattern": "^[a-z][a-z0-9_]*$"}})
        for line in ['logger.info("decision_completed", extra={"status": s})', "log.warning('bureau_timeout')",
                     'logger.exception(\n    "scoring_failed",\n    extra={"request_id": rid},\n)']:
            self.assertIsNone(self.write(line + "\n")[1], line)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
