"""Dump every site the validated detector finds, grouped by file, for
hand adjudication. Nothing is auto-fixed: the whole point is that a
detector's count is a claim to be adjudicated, not a result.

    uv run --no-project python evidence/dump_census.py [root] [outfile]
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pointer_scan as ps  # noqa: E402


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\myProject\DecompMoE")
    out = Path(sys.argv[2] if len(sys.argv) > 2
               else HERE / "census-dump.txt")

    sites = ps.scan(root)
    actionable = [s for s in sites if not s.historical]
    historical = [s for s in sites if s.historical]

    by_file: dict[str, list] = {}
    for s in actionable:
        by_file.setdefault(s.path, []).append(s)

    lines = []
    lines.append("root: %s" % root)
    lines.append("sites=%d actionable=%d historical=%d files=%d"
                 % (len(sites), len(actionable), len(historical),
                    len({s.path for s in sites})))
    lines.append("")
    lines.append("=" * 78)
    lines.append("ACTIONABLE (%d)" % len(actionable))
    lines.append("=" * 78)
    for rel in sorted(by_file):
        lines.append("")
        lines.append("--- %s  (%d site(s)) ---" % (rel, len(by_file[rel])))
        for s in sorted(by_file[rel], key=lambda x: (x.line, x.detail)):
            lines.append("  L%-5d %-16s %s" % (s.line, s.kind, s.detail))
            lines.append("         | %s" % s.text)

    lines.append("")
    lines.append("=" * 78)
    lines.append("HISTORICAL-EXEMPT (%d)" % len(historical))
    lines.append("=" * 78)
    for s in sorted(historical, key=lambda x: (x.path, x.line)):
        lines.append("  %s:%d  marker=%r  %s"
                     % (s.path, s.line, s.marker, s.detail))

    out.write_text("\n".join(lines), encoding="utf-8")
    print("wrote %s" % out)
    print("actionable=%d historical=%d files=%d"
          % (len(actionable), len(historical), len({s.path for s in sites})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
