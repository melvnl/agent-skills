import unittest

from helpers import HookTestCase, decision, write_config


class ProtectProductionConfigTest(HookTestCase):
    SCRIPT = "pre-tool-use/protect-production-config.py"

    def edit(self, rel):
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": f"{self.project}/{rel}", "content": "x"}})

    def test_default_production_paths_ask(self):
        for rel in ["app/settings/production.py", "config/settings/prod.py", "deploy/prod/app.yaml",
                    "k8s/production/deployment.yaml", "terraform/envs/prod/main.tf", "charts/app/values.production.yaml"]:
            self.assertEqual(decision(self.edit(rel)[1]), "ask", rel)

    def test_configured_paths_and_non_prod_files(self):
        write_config(self.project, {"production_config": ["ops/live/**"]})
        self.assertEqual(decision(self.edit("ops/live/flags.json")[1]), "ask")
        for rel in ["app/settings/dev.py", "app/settings/test.py", "deploy/staging/app.yaml", "src/products.py"]:
            self.assertIsNone(decision(self.edit(rel)[1]), rel)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
