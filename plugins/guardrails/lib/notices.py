"""Once-per-session notices shared by hooks that run in parallel (format-after-edit, lint-after-edit).

`claim(data, key)` is True for the first hook in this session and project to claim `key`; later claims of the
same key are False, so a skipped check is mentioned once instead of on every edit. Markers are empty files
under the system temp directory, created atomically.
"""
import hashlib
import os
import re
import tempfile

from lib import hookio


def _dir(data):
    session = str(data.get("session_id") or "no-session")
    scope = hashlib.sha256((session + "\0" + os.path.realpath(hookio.project_dir(data))).encode()).hexdigest()[:20]
    return os.path.join(tempfile.gettempdir(), "engineering-guardrails-notices", scope)


def claim(data, key):
    directory = _dir(data)
    try:
        os.makedirs(directory, exist_ok=True)
        name = re.sub(r"[^A-Za-z0-9._-]", "_", key)[:80] + "-" + hashlib.sha256(key.encode()).hexdigest()[:12]
        fd = os.open(os.path.join(directory, name), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    except OSError:
        return True  # can't record it: mentioning twice beats never mentioning
    os.close(fd)
    return True
