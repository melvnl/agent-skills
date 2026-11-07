import unittest

from helpers import HookTestCase, decision, reason, write_config


class ProtectSensitiveFilesTest(HookTestCase):
    SCRIPT = "pre-tool-use/protect-sensitive-files.py"

    def test_read_env_is_denied(self):
        code, out, _ = self.hook({"tool_name": "Read", "tool_input": {"file_path": f"{self.project}/.env"}})
        self.assertEqual((code, decision(out)), (0, "deny"))
        self.assertIn(".env", reason(out))

    def test_env_example_is_allowed(self):
        code, out, _ = self.hook({"tool_name": "Read", "tool_input": {"file_path": f"{self.project}/.env.example"}})
        self.assertEqual((code, decision(out)), (0, None))

    def test_bash_cat_and_copy_are_denied(self):
        for cmd in ["cat .env", "cp config/.env.production /tmp/x", "grep KEY .env && echo ok", "bash -c 'less id_rsa'"]:
            code, out, _ = self.hook({"tool_name": "Bash", "tool_input": {"command": cmd}})
            self.assertEqual(decision(out), "deny", cmd)

    def test_bash_unrelated_command_is_allowed(self):
        code, out, _ = self.hook({"tool_name": "Bash", "tool_input": {"command": "grep -rn ENV_NAME src/ | head"}})
        self.assertEqual(decision(out), None)

    def test_public_key_and_source_files_allowed(self):
        for p in ["id_ed25519.pub", "src/keys.py", "docs/env.md"]:
            code, out, _ = self.hook({"tool_name": "Read", "tool_input": {"file_path": f"{self.project}/{p}"}})
            self.assertEqual(decision(out), None, p)

    def test_configured_extra_paths_and_disable(self):
        write_config(self.project, {"protected_paths": ["config/secrets/**"]})
        code, out, _ = self.hook({"tool_name": "Edit", "tool_input": {"file_path": f"{self.project}/config/secrets/a.yml"}})
        self.assertEqual(decision(out), "deny")
        write_config(self.project, {"disabled": ["protect-sensitive-files"]})
        code, out, _ = self.hook({"tool_name": "Read", "tool_input": {"file_path": f"{self.project}/.env"}})
        self.assertEqual(decision(out), None)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
