---
description: The clarity rule must not suppress a comment the code genuinely needs
tags: [code-clarity, negative]
runs: 1
max_turns: 6
allowed_tools: [Write]
---

Create `money.py` with one function that converts a `Decimal` amount in rupiah-style major units to integer minor units (cents). Our payment provider rounds half-to-even, and our ledger has to match the provider's numbers exactly, so use the same rounding. Write the file.
