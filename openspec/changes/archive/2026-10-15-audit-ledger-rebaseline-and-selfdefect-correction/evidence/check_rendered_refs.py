#!/usr/bin/env python3
r"""Cross-check the refs RENDERED as `### ` entry headings against classified.json.

This is the check that was botched during planning: the ad-hoc grep used then
(`^### \(FIX\|CFL\|CTX\|OPX\)`) silently excluded `ARC-002` and the two
Chinese section headings, producing a false "32 vs 31" discrepancy. The false
result was caught and corrected before `proposal.md` was finalised; this script
exists so the correct check is reproducible rather than re-derived.

Note the deliberate difference from the botched grep: it matches ANY `^### `
line, then separates entry headings from section headings by requiring the
heading text to begin with an all-caps ref token.

Run from the repository root:
    PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/check_rendered_refs.py
"""
import json
import re
from pathlib import Path

# NOTE: this script prints Chinese section headings. Invoke it as
#     PYTHONIOENCODING=utf-8 uv run python <this file>
# so the Windows console codepage does not render them as mojibake; the
# captured evidence file would otherwise be unreadable and therefore useless as
# a re-checkable record.

CLASSIFIED = Path(".audit/gradual-review-2026-10-07/_work3/c1/classified.json")
LISTS = Path(".audit/gradual-review-2026-10-07/lists")

# `### FIX-001 — CRITICAL` / `### ARC-002 — MINOR`: ref token then an em dash.
ENTRY_HEADING = re.compile(r"^###\s+((?:FIX|ARC|CTX|CFL|OPX)-\d+)\s+[—-]")
# Everything else at `### ` is a section heading, not an entry.
ANY_HEADING = re.compile(r"^###\s+(.*)$")


def classify(path: Path) -> tuple[list[str], list[str]]:
    entries: list[str] = []
    sections: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not ANY_HEADING.match(line):
            continue
        found = ENTRY_HEADING.match(line)
        if found:
            entries.append(found.group(1))
        else:
            sections.append(line[4:].strip())
    return entries, sections


def main() -> None:
    # Deliberately NOT wrapped in try/except. An evidence script must fail
    # loudly when its input is missing or malformed: a swallowed error here
    # would produce a clean-looking capture that asserts nothing, which is the
    # exact failure class this change exists to eliminate.
    payload = json.loads(CLASSIFIED.read_text(encoding="utf-8"))
    items = payload["items"] if isinstance(payload, dict) else payload

    for bucket, filename in (("opsx-change", "opsx-changes.md"),
                             ("direct-fix", "direct-fixes.md")):
        expected = {str(i.get("id") or i.get("ref")) for i in items
                    if i.get("bucket") == bucket}
        entries, sections = classify(LISTS / filename)
        rendered = set(entries)

        print(f"--- {filename} (bucket == {bucket}) ---")
        print(f"classified.json denominator : {len(expected)}")
        print(f"rendered entry headings     : {len(entries)} (unique {len(rendered)})")
        print(f"section headings (excluded) : {len(sections)} -> {sections}")
        print(f"missing from file           : {sorted(expected - rendered) or 'none'}")
        print(f"extra in file               : {sorted(rendered - expected) or 'none'}")
        print(f"VERDICT                     : "
              f"{'MATCH' if expected == rendered and len(entries) == len(expected) else 'MISMATCH'}")
        print()


if __name__ == "__main__":
    main()
