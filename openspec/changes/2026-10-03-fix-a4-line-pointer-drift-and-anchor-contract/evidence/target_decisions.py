"""Token -> Requirement decision table for the remaining actionable sites.

Groups every actionable site by its pointer token, resolves each token to the
Requirement that currently owns the cited coordinate, and — because the cited
line numbers predate this change — cross-checks the owner by looking for a
characteristic phrase from the citing line inside that Requirement's body.
A mismatch between "resolved owner" and "phrase owner" is reported, because it
is the signal that the citation's line number is stale.
"""

import importlib.util
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location("pc", HERE / "pointer_census.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)
spec.loader.exec_module(pc)

RE_TOKEN = re.compile(r"(?:[A-Za-z_][\w/]*\.py:\d{1,4}(?:-\d{1,4})?)"
                      r"|(?:\b(?:wayfinder|skeleton|decompmoe-skeleton|spec)\b[^`\"]{0,20}?L\d{1,4}(?:-\d{1,4})?)"
                      r"|(?:\b(?:req-\d+|Req\.?\s*\d+)\s+L\d{1,4})"
                      r"|(?:\bL\d{1,4}(?:-\d{1,4})?\s+(?:spec|wayfinder|skeleton)\b)"
                      r"|(?:\blines?\s+\d{1,4}\b)")

SPEC_TEXT = {c: (ROOT / "openspec" / "specs" / c / "spec.md").read_text(encoding="utf-8")
             for c in ("wayfinder", "decompmoe-skeleton", "governance")}


def req_block(cap: str, rid: str) -> str:
    ls = SPEC_TEXT[cap].splitlines()
    start = next((i for i, l in enumerate(ls) if l.strip() == f'<a id="{rid}"></a>'), None)
    if start is None:
        return ""
    end = next((j for j in range(start + 1, len(ls)) if ls[j].startswith("### Requirement:")), len(ls))
    return "\n".join(ls[start:end])


def title(cap: str, rid: str) -> str:
    for l in req_block(cap, rid).splitlines():
        if l.startswith("### Requirement:"):
            return l[len("### Requirement:"):].strip()
    return "<not found>"


def main() -> int:
    anchors = pc.build_anchor_maps()
    groups: dict[str, list[dict]] = defaultdict(list)
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
            if not toks:
                toks = ["<no token>"]
            owner = hint
            if owner is None and nums:
                for n in nums:
                    amap = anchors.get(cap, {})
                    if n in amap:
                        owner = amap[n]
                        break
            for t in toks:
                groups[t].append({"file": r, "line": lineno, "cap": cap, "owner": owner,
                                  "text": line.strip()})

    for tok in sorted(groups, key=lambda k: -len(groups[k])):
        rows = groups[tok]
        caps = {r["cap"] for r in rows}
        owners = {r["owner"] for r in rows}
        cap = sorted(caps)[0]
        own = sorted(o for o in owners if o)[0] if any(owners) else None
        # sanity: does the citing line's most distinctive literal appear in the owner?
        probe = None
        for cand in re.findall(r"[A-Za-z_][A-Za-z0-9_]{6,}", rows[0]["text"]):
            if cand in ("specifically", "decompmoe", "safeguards", "metrics", "extraction"):
                continue
            if cap in SPEC_TEXT and cand in req_block(cap, own) if own else False:
                probe = cand
                break
        print(f"\n### {tok!r}   n={len(rows)}   cap={cap}  resolved={own}")
        if own and cap in SPEC_TEXT:
            print(f"    title : {title(cap, own)}")
            print(f"    probe : {probe or '<none of the line identifiers appear in that Requirement>'}")
        if len(owners) > 1:
            print(f"    !! multiple resolved owners: {sorted(o for o in owners if o)}")
        for r in rows[:4]:
            print(f"      {r['file']}:{r['line']}  {r['text'][:120]}")
        if len(rows) > 4:
            print(f"      ... +{len(rows)-4} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
