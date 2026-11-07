#!/usr/bin/env python3
"""trace_check.py: check requirement traceability in a Software Factory repository. Read-only.

Reads the factory's Markdown tables:
  product/PRD.md        rows whose first cell is FR-n / NFR-n / BR-n / Q-n   (definitions)
  product/FEATURES.md   rows whose first cell is F-nn; other cells reference requirement ids
  specs/<F-ID>-*/SPEC.md  AC-n rows (Verifies column) and <F-ID>-FR-n rows (Traces to column)
  tasks/<F-ID>-*.md     T-n rows (Covers column)
and searches test files for acceptance-criteria citations: "<F-ID> AC-n", "<F-ID>-AC-n", "<F-ID>/AC-n".
Ranges like "FR-21..FR-27" or "FR-21–FR-27" expand to every id in between.

FAIL  a reference to an id that is not defined; a defined FR/NFR/BR owned by no feature;
      an acceptance criterion that verifies nothing; a spec requirement with no acceptance criterion.
WARN  an acceptance criterion no test cites; a task covering nothing.
Deprecated PRD ids (a row containing "Deprecated") are exempt from ownership.

Usage: trace_check.py [--root DIR] [--tests GLOB ...] [--json]
       default test globs: tests/**/*.py test/**/*.py **/test_*.py **/*_test.py **/*.test.* **/*.spec.*
Exit:  0 = no FAIL, 1 = FAIL found, 2 = not a factory layout (no product/PRD.md).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ID = r"(?:FR|NFR|BR|Q)-\d+"
ID_RE = re.compile(rf"\b({ID})\b")
RANGE_RE = re.compile(r"\b(FR|NFR|BR|Q)-(\d+)\s*(?:\.\.|–|—)\s*(?:\1-)?(\d+)\b")
FEATURE_DIR_RE = re.compile(r"^(F-\d+)")
DEFAULT_TEST_GLOBS = ["tests/**/*.py", "test/**/*.py", "**/test_*.py", "**/*_test.py", "**/*.test.*", "**/*.spec.*"]
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".factory"}


def table_rows(text):
    """Yield (header_cells, row_cells) for every Markdown table row (separator rows skipped)."""
    header = None
    for line in text.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            header = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = cells
            continue
        yield header, cells


def ids_in(text):
    found = set(ID_RE.findall(text))
    for kind, lo, hi in RANGE_RE.findall(text):
        lo, hi = int(lo), int(hi)
        if lo <= hi and hi - lo <= 500:
            found.update(f"{kind}-{n}" for n in range(lo, hi + 1))
    return found


def col(header, name):
    for i, h in enumerate(header):
        if h.lower().startswith(name):
            return i
    return None


def scan(root, test_globs):
    res = {"defined": set(), "deprecated": set(), "owned": {}, "refs": [], "acs": [], "spec_frs": [],
           "tasks": [], "test_citations": set(), "fail": [], "warn": []}
    prd = root / "product" / "PRD.md"
    for _, cells in table_rows(prd.read_text(encoding="utf-8")):
        if cells and re.fullmatch(ID, cells[0]):
            res["defined"].add(cells[0])
            if any("deprecated" in c.lower() for c in cells[1:]):
                res["deprecated"].add(cells[0])

    features = root / "product" / "FEATURES.md"
    if features.exists():
        for _, cells in table_rows(features.read_text(encoding="utf-8")):
            if cells and re.fullmatch(r"F-\d+", cells[0]):
                for rid in ids_in(" ".join(cells[1:])):
                    res["owned"].setdefault(rid, set()).add(cells[0])
                    res["refs"].append(("product/FEATURES.md", cells[0], rid))

    for spec in sorted((root / "specs").glob("*/SPEC.md")):
        m = FEATURE_DIR_RE.match(spec.parent.name)
        if not m:
            continue
        fid, where = m.group(1), str(spec.relative_to(root))
        for header, cells in table_rows(spec.read_text(encoding="utf-8")):
            first = cells[0] if cells else ""
            if re.fullmatch(r"AC-\d+", first):
                vi = col(header, "verifies")
                verifies = ids_in(cells[vi]) if vi is not None and vi < len(cells) else set()
                verifies |= set(re.findall(rf"{re.escape(fid)}-FR-\d+", " ".join(cells)))
                res["acs"].append((fid, first, verifies, where))
                for rid in verifies:
                    if ID_RE.fullmatch(rid):
                        res["refs"].append((where, first, rid))
            elif re.fullmatch(rf"{re.escape(fid)}-(?:FR|NFR)-\d+", first):
                ti = col(header, "traces")
                traces = ids_in(cells[ti]) if ti is not None and ti < len(cells) else set()
                res["spec_frs"].append((fid, first, where))
                for rid in traces:
                    res["refs"].append((where, first, rid))

    for task_file in sorted((root / "tasks").glob("F-*.md")):
        where = str(task_file.relative_to(root))
        for header, cells in table_rows(task_file.read_text(encoding="utf-8")):
            if cells and re.fullmatch(r"T-\d+", cells[0]):
                ci = col(header, "covers")
                covers = cells[ci] if ci is not None and ci < len(cells) else ""
                res["tasks"].append((where, cells[0], covers))
                for rid in ids_in(covers):
                    res["refs"].append((where, cells[0], rid))

    cite = re.compile(r"\b(F-\d+)[\s_/:-]*AC-(\d+)\b")
    seen = set()
    for pattern in test_globs:
        for path in root.glob(pattern):
            if path in seen or not path.is_file() or SKIP_DIRS & set(path.relative_to(root).parts):
                continue
            seen.add(path)
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for f, n in cite.findall(text):
                res["test_citations"].add((f, f"AC-{n}"))
    return res


def evaluate(res):
    fail, warn = res["fail"], res["warn"]
    for where, owner, rid in res["refs"]:
        if rid not in res["defined"]:
            fail.append(f"{where}: {owner} references undefined {rid}")
    for rid in sorted(res["defined"] - res["deprecated"]):
        if not rid.startswith("Q-") and rid not in res["owned"]:
            fail.append(f"product/PRD.md: {rid} is owned by no feature in product/FEATURES.md")
    for fid, ac, verifies, where in res["acs"]:
        if not verifies:
            fail.append(f"{where}: {ac} verifies no requirement")
        if (fid, ac) not in res["test_citations"]:
            warn.append(f"{where}: {ac} is cited by no test (expected '{fid} {ac}' in a test)")
    covered = {(fid, v) for fid, _, verifies, _ in res["acs"] for v in verifies}
    for fid, fr, where in res["spec_frs"]:
        if (fid, fr) not in covered:
            fail.append(f"{where}: {fr} has no acceptance criterion (add it to an AC's Verifies column)")
    for where, task, covers in res["tasks"]:
        if not covers.strip() or covers.strip() in {"-", "—"}:
            warn.append(f"{where}: {task} covers no requirement or acceptance criterion")
    return fail, warn


def main(argv=None):
    ap = argparse.ArgumentParser(description="Software Factory traceability check")
    ap.add_argument("--root", default=".")
    ap.add_argument("--tests", nargs="*", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if not (root / "product" / "PRD.md").exists():
        print(f"not a Software Factory layout: {root}/product/PRD.md not found", file=sys.stderr)
        return 2
    res = scan(root, args.tests if args.tests is not None else DEFAULT_TEST_GLOBS)
    fail, warn = evaluate(res)
    summary = {"defined": len(res["defined"]), "features_owning": len({f for s in res["owned"].values() for f in s}),
               "acceptance_criteria": len(res["acs"]), "tasks": len(res["tasks"]), "fail": len(fail), "warn": len(warn)}
    if args.json:
        print(json.dumps({"summary": summary, "fail": fail, "warn": warn}, indent=2))
    else:
        for line in fail:
            print(f"FAIL  {line}")
        for line in warn:
            print(f"WARN  {line}")
        print("summary: " + ", ".join(f"{k}={v}" for k, v in summary.items()))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
