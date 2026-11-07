import unittest

from helpers import HookTestCase, decision, reason, write_config


class ProtectFinancialCoreTest(HookTestCase):
    SCRIPT = "pre-tool-use/protect-financial-core.py"

    def edit(self, rel):
        return self.hook({"tool_name": "Edit", "tool_input": {"file_path": f"{self.project}/{rel}", "new_string": "x"}})

    def test_asks_for_configured_paths(self):
        write_config(self.project, {"financial_core": ["src/credit/**", "src/money.py"]})
        for rel in ["src/credit/rules.py", "src/credit/bands/v2.py", "src/money.py"]:
            code, out, _ = self.edit(rel)
            self.assertEqual(decision(out), "ask", rel)
            self.assertIn(rel, reason(out))

    def test_other_paths_and_unconfigured_projects_pass(self):
        self.assertIsNone(self.edit("src/credit/rules.py")[1])
        write_config(self.project, {"financial_core": ["src/credit/**"]})
        self.assertIsNone(self.edit("src/notifications/sms.py")[1])

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
