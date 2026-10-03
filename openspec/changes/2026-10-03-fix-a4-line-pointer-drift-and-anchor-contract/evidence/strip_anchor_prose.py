"""Remove anchor-element literals quoted inside Requirement prose.

C3 (req-gov-6): an anchor element quoted in a Requirement body still occupies the
id namespace when the document is parsed. The contract text itself was violating
its own rule, so the fix is to state the rule without emitting the element.

CRLF is preserved: the file is read with newline='' and split on '\\n' only, so
the '\\r' stays on each line and the byte layout is untouched apart from the
replaced segments.

Every substitution asserts an exact hit count, and a line-length floor is checked
so a whole-line replacement can never silently truncate prose (the substring-
replacement defect mode).
"""

import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
SPECS = ROOT / "openspec" / "specs"

# (file, exact old substring, new substring, expected hits, min_new_len_ratio)
EDITS = [
    # --- wayfinder: req-19 prose quoting req-17's anchor -------------------
    (
        "wayfinder/spec.md",
        "Req 17 (anchored `<a id=\"req-17\"></a>`) reports",
        "Req 17 (`#req-17` Stateless Per-Frame C Recomputation) reports",
        1,
        1.0,
    ),
    # --- governance req-gov-6 clause 1 table cell ---------------------------
    (
        "governance/spec.md",
        "a block-level `<a id=\"req-N-slug\"></a>` anchor, referenced as",
        "a block-level HTML anchor on that row, referenced as",
        1,
        0.5,
    ),
    # --- governance req-gov-6 clause 3 --------------------------------------
    (
        "governance/spec.md",
        "   unique, and every `### Requirement:` heading MUST be immediately preceded by its\n"
        "   `<a id=\"req-N\"></a>` anchor. An anchor literal quoted inside prose or inside a code span MUST NOT\n"
        "   appear in a Requirement body",
        "   unique, and every `### Requirement:` heading MUST be immediately preceded by an HTML anchor\n"
        "   element on its own line, whose `id` attribute is that Requirement's id. An anchor element\n"
        "   quoted inside prose or inside a code span MUST NOT\n"
        "   appear in a Requirement body",
        1,
        1.0,
    ),
    # --- governance req-gov-6 Scenario --------------------------------------
    (
        "governance/spec.md",
        "  example `` `<a id=\"req-20\"></a>` ``",
        "  example — any Requirement's own anchor element, whichever id it carries —",
        1,
        0.9,
    ),
]

# req-23's body mirrors req-22 twice, each time quoting its anchor element
# WITHOUT a closing tag — a shape the well-formed `<a id="X"></a>` pattern misses
# but which still occupies the id namespace when parsed.
EDITS.append(
    (
        "decompmoe-skeleton/spec.md",
        "`<a id=\"req-22\">`",
        "`` `#req-22` ``",
        2,
        0.0,
    ),
)

ANCHOR_TOKEN = '<a id="'


def main() -> int:
    problems = []
    by_file: dict[str, list[str]] = {}
    for rel, old, new, want, floor in EDITS:
        by_file.setdefault(rel, []).append(old)

    for rel, edits in by_file.items():
        path = SPECS / rel
        text = path.read_text(encoding="utf-8", newline="")
        original = text
        # Multi-line patterns are written with '\n'; the file uses CRLF, so the
        # newline has to be matched to whatever the file actually contains.
        eol = "\r\n" if "\r\n" in text else "\n"
        for _rel, old, new, want, floor in [e for e in EDITS if e[0] == rel]:
            old_eol = old.replace("\n", eol)
            new_eol = new.replace("\n", eol)
            n = text.count(old_eol)
            if n != want:
                problems.append(f"{rel}: expected {want} hit(s) of {old[:60]!r}, got {n}")
                continue
            if len(new) < len(old) * floor:
                problems.append(
                    f"{rel}: replacement would truncate {old[:40]!r} "
                    f"({len(old)} -> {len(new)} chars, floor {floor})"
                )
                continue
            text = text.replace(old_eol, new_eol, want)
        if text != original:
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            print(f"wrote {rel}")

    # Re-verify from disk: no anchor token on any line that is not a standalone anchor.
    for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
        p = SPECS / cap / "spec.md"
        raw = p.read_bytes()
        crlf, lf = raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")
        if lf:
            problems.append(f"{cap}/spec.md: {lf} bare LF mixed into {crlf} CRLF (line endings changed)")
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if ANCHOR_TOKEN in line and not (
                line.strip().startswith(ANCHOR_TOKEN) and line.strip().endswith("</a>")
            ):
                problems.append(f"{cap}/spec.md:{i}: anchor token in prose still present")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nall anchor-in-prose occurrences removed; CRLF preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
