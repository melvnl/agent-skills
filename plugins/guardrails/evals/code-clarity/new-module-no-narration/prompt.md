---
description: New code carries intent in names and types, not comments or docstrings
tags: [code-clarity]
runs: 1
max_turns: 6
allowed_tools: [Write]
---

Create `cart.py` with:

- the subtotal of a list of line items, each a price in cents and a quantity;
- a tiered discount: 10% off a subtotal of at least 10000 cents, 20% off at least 50000 cents;
- the final total after the discount and a tax rate passed in by the caller, rounded to whole cents.

Put everything in that one file and write the file.
