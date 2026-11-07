"""Test helpers: run a hook script as Claude Code would (JSON on stdin) and parse its outcome."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def run_hook(rel_script, payload, project_dir=None, env=None, raw=None):
    project_dir = project_dir or tempfile.mkdtemp()
    full_env = dict(os.environ)
    full_env["CLAUDE_PROJECT_DIR"] = project_dir
    full_env.pop("PYTHONPATH", None)
    if env:
        full_env.update(env)
    data = raw if raw is not None else json.dumps(dict({"cwd": project_dir, "session_id": "test"}, **payload))
    proc = subprocess.run([sys.executable, os.path.join(ROOT, rel_script)], input=data, capture_output=True,
                          text=True, env=full_env, cwd=project_dir, timeout=60)
    out = None
    if proc.stdout.strip():
        out = json.loads(proc.stdout)
    return proc.returncode, out, proc.stderr


def decision(out):
    """'deny' / 'ask' for PreToolUse, 'block' for PostToolUse/Stop, None when allowed silently."""
    if not out:
        return None
    if "hookSpecificOutput" in out and "permissionDecision" in out["hookSpecificOutput"]:
        return out["hookSpecificOutput"]["permissionDecision"]
    return out.get("decision")


def reason(out):
    if not out:
        return ""
    return out.get("reason") or out.get("hookSpecificOutput", {}).get("permissionDecisionReason", "") \
        or out.get("hookSpecificOutput", {}).get("additionalContext", "")


def write_config(project_dir, cfg):
    os.makedirs(os.path.join(project_dir, ".claude"), exist_ok=True)
    with open(os.path.join(project_dir, ".claude", "guardrails.json"), "w") as fh:
        json.dump(cfg, fh)


class HookTestCase(unittest.TestCase):
    SCRIPT = None

    def setUp(self):
        self.project = tempfile.mkdtemp()

    def hook(self, payload, **kw):
        return run_hook(self.SCRIPT, payload, project_dir=kw.pop("project_dir", self.project), **kw)

    def assertMalformedInputFailsOpen(self):
        code, out, err = run_hook(self.SCRIPT, {}, project_dir=self.project, raw="not json")
        self.assertEqual(code, 1)
        self.assertIsNone(out)
        self.assertNotIn("Traceback", err)
