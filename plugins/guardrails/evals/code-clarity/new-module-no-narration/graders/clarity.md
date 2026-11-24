---
type: llm
focus: {source: file, path: cart.py}
---

PASS if intent is carried by function names, parameter names, types and named constants (for example the discount thresholds and rates), and the file has at most a few short comments, each explaining why rather than what. A module docstring of one line is acceptable.

FAIL if most functions have docstrings that restate their name or parameters, if comments narrate what the next line does (e.g. "calculate the subtotal", "return the total"), if the thresholds and rates are bare magic numbers, or if there is defensive code for states the task does not describe (e.g. checks for negative quantities with custom exceptions, or try/except around plain arithmetic).
