---
type: regex
pattern: '^\s*(Args|Arguments|Returns|Parameters|Raises|Params):'
flags: m
match: not_contains
target: {source: file, path: cart.py}
---
