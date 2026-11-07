"""Split a shell command line into simple commands and tokens, without executing anything.

Not a full shell parser. It handles the cases guardrails need deterministically: ;, &&, ||, |, &,
newlines, $(...) and backtick substitutions, `bash -c '...'` / `sh -c` recursion, leading VAR=value
assignments, and wrappers such as sudo, env, nohup, time, command, xargs. Quoted text never splits.
"""
import shlex

WRAPPERS = {"sudo", "env", "nohup", "time", "command", "nice", "ionice", "xargs", "exec", "timeout", "doas"}
SHELLS = {"bash", "sh", "zsh", "dash"}


def _segments(command):
    """Split on unquoted control operators; extract $(...) and `...` bodies as extra segments."""
    segs, buf, i, quote = [], [], 0, None
    subs = []
    while i < len(command):
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(c); i += 1; c = command[i]
            buf.append(c); i += 1
            continue
        if c in "'\"":
            quote = c; buf.append(c); i += 1; continue
        if c == "\\" and i + 1 < len(command):
            buf.append(command[i:i + 2]); i += 2; continue
        if command.startswith("$(", i):
            depth, j = 1, i + 2
            while j < len(command) and depth:
                depth += {"(": 1, ")": -1}.get(command[j], 0); j += 1
            subs.append(command[i + 2:j - 1]); buf.append(" __SUBST__ "); i = j; continue
        if c == "`":
            j = command.find("`", i + 1)
            j = len(command) if j == -1 else j
            subs.append(command[i + 1:j]); buf.append(" __SUBST__ "); i = j + 1; continue
        if command.startswith("&&", i) or command.startswith("||", i):
            segs.append("".join(buf)); buf = []; i += 2; continue
        if c in ";|&\n":
            segs.append("".join(buf)); buf = []; i += 1; continue
        buf.append(c); i += 1
    segs.append("".join(buf))
    for s in subs:
        segs.extend(_segments(s))
    return [s.strip() for s in segs if s.strip()]


def _tokens(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def simple_commands(command, _depth=0):
    """Return a list of token lists, one per simple command, with wrappers and env assignments removed."""
    result = []
    for seg in _segments(command or ""):
        toks = _tokens(seg)
        while toks and ("=" in toks[0] and not toks[0].startswith("=") and toks[0].split("=", 1)[0].isidentifier()):
            toks = toks[1:]
        while toks and toks[0] in WRAPPERS:
            toks = toks[1:]
            while toks and toks[0].startswith("-"):
                toks = toks[1:]
            while toks and "=" in toks[0] and toks[0].split("=", 1)[0].isidentifier():
                toks = toks[1:]
        if not toks:
            continue
        base = toks[0].rsplit("/", 1)[-1]
        if base in SHELLS and "-c" in toks[1:] and _depth < 3:
            idx = toks.index("-c")
            if idx + 1 < len(toks):
                result.extend(simple_commands(toks[idx + 1], _depth + 1))
                continue
        toks[0] = base
        result.append(toks)
    return result
