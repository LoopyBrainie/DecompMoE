"""Diagnostic: locate every `<a id=...>` literal in a spec and classify it.

Three buckets per literal:
  BOUNDARY  -- own line is `<a id="x"></a>`, the standard Requirement anchor
  INLINE    -- own line is `### Requirement: ...` with a leading anchor (block form)
  PROSE     -- an anchor literal quoted inside body prose (forbidden by C3)

Also reports anchor->heading coverage and duplicate ids.
"""

import collections
import re
import sys
from pathlib import Path

SPECS = Path("openspec/specs")
CAPS = ("wayfinder", "decompmoe-skeleton", "governance")
ANCHOR_RE = re.compile(r'<a id="([^"]+)"></a>')
HEAD_RE = re.compile(r"^### Requirement:")


def classify(spec_path: Path) -> dict:
    text = spec_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    report = {"boundary": [], "inline": [], "prose": []}
    for i, line in enumerate(lines, start=1):
        for rid in ANCHOR_RE.findall(line):
            s = line.strip()
            if s == f'<a id="{rid}"></a>':
                report["boundary"].append((i, rid))
            elif HEAD_RE.match(s):
                report["inline"].append((i, rid, s[:90]))
            else:
                report["prose"].append((i, rid, s[:160]))
    return report


def main() -> int:
    rc = 0
    for cap in CAPS:
        spec = SPECS / cap / "spec.md"
        rep = classify(spec)
        text = spec.read_text(encoding="utf-8")
        lines = text.splitlines()
        headings = [(i, l) for i, l in enumerate(lines, start=1) if HEAD_RE.match(l)]
        ids = collections.Counter(ANCHOR_RE.findall(text))
        dup = {k: v for k, v in ids.items() if v > 1}
        total = sum(len(v) for v in rep.values())
        bound = {rid for _, rid in rep["boundary"]}
        head_ids = [rep["boundary"][k][1] for k in range(len(rep["boundary"]))]
        covered = len(bound)
        print(f"== {cap}: total_literals={total} boundary={len(rep['boundary'])} "
              f"inline={len(rep['inline'])} prose={len(rep['prose'])} "
              f"headings={len(headings)} dup={dup}")
        # boundary anchors that do not introduce a heading, or headings without a boundary
        boundary_lines = {i: rid for i, rid in rep["boundary"]}
        orphan_anchor = [i for i, rid in rep["boundary"] if i + 1 >= len(lines)]
        for i, rid, s in rep["inline"]:
            print(f"   INLINE L{i} id={rid} :: {s}")
        for i, rid, s in rep["prose"]:
            print(f"   PROSE  L{i} id={rid} :: {s}")
        if dup:
            for rid in dup:
                sites = [i for i, x in rep["boundary"] + rep["inline"] if x == rid]
                print(f"   DUP id={rid} sites={sites}")
        if total != len(headings) or dup:
            rc = 1
        del head_ids, covered, orphan_anchor
    return rc


if __name__ == "__main__":
    sys.exit(main())
