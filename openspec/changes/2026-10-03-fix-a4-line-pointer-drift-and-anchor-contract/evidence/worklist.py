"""Deterministic work list for the remaining actionable pointer sites.

For each actionable census site: the file, the line, the exact pointer tokens
found, the owning Requirement as resolved from the CURRENT spec (advisory only —
line numbers in the citation may predate this change, so the rewrite target is
confirmed against the Requirement's own body text), and the full line.

Sites are grouped by the pointer's own text so a repeated citation (e.g. the 10
`wayfinder L249` sites) is decided once and applied uniformly.
"""

import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pc", HERE / "pointer_census.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

RE_TOKEN = re.compile(r"(?:[A-Za-z_][\w/]*\.py:\d{1,4}(?:-\d{1,4})?)"
                      r"|(?:\b(?:wayfinder|skeleton|decompmoe-skeleton|spec)\b[^`\"]{0,20}?L\d{1,4}(?:-\d{1,4})?)"
                      r"|(?:\b(?:req-\d+|Req\.?\s*\d+)\s+L\d{1,4})"
                      r"|(?:\bL\d{1,4}(?:-\d{1,4})?\s+(?:spec|wayfinder|skeleton)\b)"
                      r"|(?:\blines?\s+\d{1,4}\b)")

ROOT = HERE.parents[3]
TITLES = {}


def title(cap: str, rid: str) -> str:
    if (cap, rid) in TITLES:
        return TITLES[(cap, rid)]
    p = ROOT / "openspec" / "specs" / cap / "spec.md"
    ls = p.read_text(encoding="utf-8").splitlines()
    out = "<not found>"
    for i, l in enumerate(ls):
        if l.strip() == f'<a id="{rid}"></a>':
            for j in range(i + 1, min(i + 4, len(ls))):
                if ls[j].startswith("### Requirement:"):
                    out = ls[j][len("### Requirement:"):].strip()
                    break
            break
    TITLES[(cap, rid)] = out
    return out


def main() -> int:
    anchors = pc.build_anchor_maps()
    sites = []
    for path in pc.iter_files():
        r = pc.rel(path)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "http" in line:
                continue
            tgt = pc.classify(line)
            if tgt is None or pc.has_historical_marker(line):
                continue
            cap, hint, nums, kind = tgt
            toks = [m.group(0).strip() for m in RE_TOKEN.finditer(pc.RE_LABEL_L.sub(" ", line))]
            owner = hint
            if owner is None and nums:
                amap = anchors.get(cap, {}) if cap in anchors else {}
                for n in nums:
                    if n in amap:
                        owner = amap[n]
                        break
            sites.append({
                "file": r, "line": lineno, "tokens": toks, "cap": cap,
                "owner": owner, "kind": kind, "text": line.rstrip(),
            })

    print(f"ACTIONABLE SITES: {len(sites)}\n")
    by_file: dict[str, list[dict]] = {}
    for s in sites:
        by_file.setdefault(s["file"], []).append(s)
    for f in sorted(by_file, key=lambda k: -len(by_file[k])):
        rows = by_file[f]
        print(f"\n{'='*78}\n{f}  ({len(rows)})\n{'='*78}")
        for s in sorted(rows, key=lambda x: x["line"]):
            own = f'{s["cap"]} {s["owner"]}' if s["owner"] else f'{s["cap"]} <unresolved>'
            print(f"  L{s['line']}  tokens={s['tokens']}")
            print(f"          -> {own}"
                  + (f' : {title(s["cap"], s["owner"])}' if s["owner"] and s["cap"] in
                     ("wayfinder", "decompmoe-skeleton", "governance") else ""))
            print(f"          {s['text'].strip()[:190]}")

    print(f"\n{'='*78}\nPOINTER TOKEN FREQUENCY\n{'='*78}")
    for tok, n in Counter(t for s in sites for t in s["tokens"]).most_common():
        print(f"  {n:3d}  {tok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
