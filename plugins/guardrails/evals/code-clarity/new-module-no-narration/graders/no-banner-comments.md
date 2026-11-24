---
type: regex
pattern: '^\s*#\s*[-=#*~]{3,}'
flags: m
match: not_contains
target: {source: file, path: cart.py}
---
