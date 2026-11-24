---
type: llm
focus: {source: file, path: money.py}
---

PASS if the code records why half-to-even rounding is used (matching the payment provider's rounding), in a short comment, a docstring line, or an unmistakable constant name such as PROVIDER_ROUNDING, so a later reader would not "fix" it to half-up.

FAIL if the reason for half-to-even rounding is not recorded anywhere in the file, or if the file is padded with comments that restate what each line does.
