"""Map every actionable site to the Requirement that contains it.

The delta must name Requirements, not line numbers, so the work list needs
a capability -> Requirement -> lines mapping built from the anchor lines
rather than from any recorded pointer.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The detector lives in scripts/, not here: the gate and the census MUST
# be the same implementation. A private copy in a change directory is
# exactly how the two drifted apart the first time.
sys.path.insert(0, str(HERE.parents[3] / 'scripts'))

import pointer_scan as ps  # noqa: E402

ROOT = Path(r"D:\myProject\DecompMoE")
SPECS = {
    "wayfinder": ROOT / "openspec" / "specs" / "wayfinder" / "spec.md",
    "decompmoe-skeleton": ROOT / "openspec" / "specs" / "decompmoe-skeleton" / "spec.md",
    "governance": ROOT / "openspec" / "specs" / "governance" / "spec.md",
}

RE_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
RE_REQ_HEAD = re.compile(r"^### Requirement:")


def req_spans(path: Path):
    """[(anchor_id, title, first_line, last_line)] in 1-based line numbers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    marks = []  # (lineno, anchor, title)
    cur_anchor = None
    for i, line in enumerate(lines, 1):
        m = RE_ANCHOR.search(line)
        if m:
            cur_anchor = m.group(1)
            continue
        if RE_REQ_HEAD.match(line) and cur_anchor:
            marks.append((i, cur_anchor,
                          line.replace("### Requirement:", "").strip()))
    spans = []
    for idx, (ln, anc, title) in enumerate(marks):
        end = marks[idx + 1][0] - 1 if idx + 1 < len(marks) else len(lines)
        spans.append((anc, title, ln, end))
    return spans


def owner(cap: str, lineno: int):
    for anc, title, start, end in req_spans(SPECS[cap]):
        if start <= lineno <= end:
            return anc, title
    return None, None


def main() -> int:
    sites = [s for s in ps.scan(ROOT) if not s.historical]
    by_req: dict = {}
    for s in sorted(sites, key=lambda x: (x.path, x.line)):
        cap = None
        for name in SPECS:
            if s.path.startswith("openspec/specs/%s/" % name):
                cap = name
        if cap:
            anc, title = owner(cap, s.line)
            key = (cap, anc, title)
        else:
            key = (None, s.path, None)
        by_req.setdefault(key, []).append(s)

    print("%-58s %s" % ("TARGET", "SITES"))
    print("-" * 78)
    total = 0
    for (cap, anc, title), group in sorted(
            by_req.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
        label = ("%s %s" % (cap, anc)) if cap else anc
        print("%-58s %d" % (label, len(group)))
        if title:
            print("    %s" % title[:72])
        for s in group:
            print("      %s L%-5d %-16s %s"
                  % ("", s.line, s.kind, s.detail))
        total += len(group)
    print("-" * 78)
    print("TOTAL %d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
