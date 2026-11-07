"""Lightweight, deterministic scanning of Python source for call expressions. Not a parser: it finds a call
start with a regex and extends it until parentheses balance (ignoring parentheses inside string literals)."""
import re

STRING = re.compile(r"""(?s)(?:[rbuRBU]{0,2}[fF]?[rbRB]?)("{3}.*?"{3}|'{3}.*?'{3}|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')""")
FSTRING = re.compile(r"""(?s)\b[fF][rR]?("{3}.*?"{3}|'{3}.*?'{3}|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')""")
DICT_KEY = re.compile(r"""(['"])([A-Za-z_][\w-]*)\1\s*:""")
IDENT = re.compile(r"[A-Za-z_]\w*")


def calls(lines, start):
    """lines: [(lineno, text)] in order; start: compiled regex matching up to and including '('.
    Yields (lineno, call_text)."""
    text = "\n".join(t for _, t in lines)
    numbers = [n for n, _ in lines]
    for m in start.finditer(text):
        depth, i, quote = 1, m.end(), None
        while i < len(text) and depth:
            c = text[i]
            if quote:
                if c == "\\":
                    i += 1
                elif c == quote:
                    quote = None
            elif c in "'\"":
                quote = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        line_index = text.count("\n", 0, m.start())
        yield (numbers[line_index] if line_index < len(numbers) else None), text[m.start():i]


def fstring_expressions(code):
    out = []
    for m in FSTRING.finditer(code):
        out.extend(re.findall(r"\{([^{}]+)\}", m.group(1)))
    return out


def strip_strings(code):
    return STRING.sub('""', code)


def identifiers(code):
    """Identifiers outside string literals, plus names inside f-string expressions and quoted dict keys."""
    names = IDENT.findall(strip_strings(code))
    for expr in fstring_expressions(code):
        names.extend(IDENT.findall(expr))
    names.extend(k for _, k in DICT_KEY.findall(code))
    return names
