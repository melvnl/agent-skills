import unittest

from helpers import HookTestCase, decision


class BlockDestructiveCommandsTest(HookTestCase):
    SCRIPT = "pre-tool-use/block-destructive-commands.py"

    def verdict(self, command):
        code, out, _ = self.hook({"tool_name": "Bash", "tool_input": {"command": command}})
        self.assertEqual(code, 0, command)
        return decision(out)

    def test_denied(self):
        for cmd in ["rm -rf /", "sudo rm -rf ~", "rm -fr ../other-project", "rm -rf /etc/x",
                    "git push --force origin main", "git push -f", "git push origin +main", "git push origin :feature",
                    "git push --force-with-lease", "git filter-branch --all",
                    "mysql -e 'DROP DATABASE app'", "psql -c \"TRUNCATE TABLE decisions\"",
                    "mysql app -e \"DELETE FROM decision;\"", "python manage.py flush --noinput",
                    "terraform destroy", "terraform apply -auto-approve", "aws s3 rm s3://bucket --recursive",
                    "aws s3 rb s3://bucket", "aws rds delete-db-instance --db-instance-identifier x",
                    "bash -c 'rm -rf $HOME'", "echo ok && git push --force", "mkfs.ext4 /dev/sda1", "shutdown -h now"]:
            self.assertEqual(self.verdict(cmd), "deny", cmd)

    def test_asks(self):
        for cmd in ["git push origin feat/x", "git reset --hard HEAD~1", "git clean -fd", "git checkout -- src/a.py",
                    "git checkout .", "git restore src/a.py", "git branch -D old", "git stash clear", "git rebase main",
                    "git commit --amend -m x", "kubectl delete pod x", "terraform apply", "python manage.py migrate app zero"]:
            self.assertEqual(self.verdict(cmd), "ask", cmd)

    def test_allowed(self):
        for cmd in ["rm -rf build dist", "rm -rf ./node_modules", "rm file.txt", "echo 'rm -rf /'",
                    "git status", "git commit -m 'drop table support'", "git checkout -b feat/x", "git restore --staged a.py",
                    "git push --help", "git push --dry-run --force", "grep -rn 'DROP TABLE' migrations/", "mysql -e 'SELECT 1'",
                    "mysql -e \"DELETE FROM decision WHERE id = 3\"", "python manage.py migrate", "aws s3 ls s3://bucket",
                    "terraform plan", "kubectl get pods"]:
            self.assertIsNone(self.verdict(cmd), cmd)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
