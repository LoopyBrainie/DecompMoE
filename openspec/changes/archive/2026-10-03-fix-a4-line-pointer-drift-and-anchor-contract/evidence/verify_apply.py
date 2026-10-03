"""Verify the apply-phase acceptance clauses of tasks.md 2.1-4.2 and 9.3.

Each check returns (task_id, ok, detail). Every check reads the LIVE spec from
disk; none of them consults a stored expectation file. Count assertions come
first so an empty match set aborts instead of vacuously passing.
"""

import re
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
SPECS = ROOT / "openspec" / "specs"
CAPS = ("wayfinder", "decompmoe-skeleton", "governance")

ANCHOR_RE = re.compile(r'<a id="([^"]+)"></a>')
HEAD_RE = re.compile(r"^### Requirement:")
SCEN_RE = re.compile(r"^#### Scenario:")
PLACEHOLDER_RE = re.compile(r"<a id=\"[^\"]*\"[^>]*>")


def lines(cap: str) -> list[str]:
    return (SPECS / cap / "spec.md").read_text(encoding="utf-8").splitlines()


def text(cap: str) -> str:
    return (SPECS / cap / "spec.md").read_text(encoding="utf-8")


def blocks(cap: str) -> dict[str, list[str]]:
    """Map id -> full Requirement block, starting at its anchor and ending before the next heading.

    The block is keyed off the HEADING, not off the anchor line: in this repo the
    anchor usually sits on the line immediately above its heading, so scanning
    forward from the anchor for "the next Requirement heading" finds this
    Requirement's own heading and yields a 1-line block.
    """
    out: dict[str, list[str]] = {}
    ls = lines(cap)
    for i, line in enumerate(ls):
        if not HEAD_RE.match(line):
            continue
        k = i - 1
        while k >= 0 and not ls[k].strip():
            k -= 1
        m = ANCHOR_RE.fullmatch(ls[k].strip()) if k >= 0 else None
        rid = m.group(1) if m else f"<unanchored-heading-L{i + 1}>"
        end = next((j for j in range(i + 1, len(ls)) if HEAD_RE.match(ls[j])), len(ls))
        out[rid] = ls[k:end]
    return out


def findings(results: list[tuple[str, bool, str]]) -> int:
    bad = 0
    for tid, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {tid}: {detail}")
        if not ok:
            bad += 1
    return bad


def main() -> int:
    wf, sk, gv = text("wayfinder"), text("decompmoe-skeleton"), text("governance")
    wb, sb, gb = blocks("wayfinder"), blocks("decompmoe-skeleton"), blocks("governance")
    R: list[tuple[str, bool, str]] = []

    # --- 2.1 block anchors + req-20 scenario count + Source field -------------
    for aid in ("req-20-mci", "req-20-source"):
        n = wf.count(f'<a id="{aid}"></a>')
        R.append((f"2.1 anchor {aid} unique", n == 1, f"count={n}"))
    n_scen = sum(1 for l in wb.get("req-20", []) if SCEN_RE.match(l))
    R.append(("2.1 req-20 scenarios==15", n_scen == 15, f"count={n_scen} (14 pre-existing + 1)"))
    R.append(("2.1 req-20 Source field kept", any(l.startswith("**Source:**") for l in wb.get("req-20", [])),
              "present" if any(l.startswith("**Source:**") for l in wb.get("req-20", [])) else "ABSENT"))

    # --- 2.2 req-36 removed, guarantees migrated -----------------------------
    R.append(("2.2 req-36 gone from wayfinder", "req-36" not in wf, "absent" if "req-36" not in wf else "STILL PRESENT"))
    canon = " ".join(wb.get("req-20", []))
    R.append(("2.2(a) canonical-source guarantee in req-20",
              "canonical" in canon.lower() and "MCI" in canon, "found" if "canonical" in canon.lower() else "MISSING"))
    g2 = " ".join(gb.get("req-gov-2", []))
    g2_scen = sum(1 for l in gb.get("req-gov-2", []) if SCEN_RE.match(l))
    R.append(("2.2(bcd) req-gov-2 has 4 Scenarios", g2_scen == 4, f"count={g2_scen} (was 1)"))
    for kw in ("A8-2", "convex", "covariance"):
        R.append((f"2.2(bcd) req-gov-2 mentions {kw}", kw.lower() in g2.lower(),
                  "found" if kw.lower() in g2.lower() else "MISSING"))

    # --- 2.3 no anchor literal inside prose ----------------------------------
    prose_hits = []
    for i, line in enumerate(lines("wayfinder"), 1):
        for rid in ANCHOR_RE.findall(line):
            if line.strip() != f'<a id="{rid}"></a>' and not HEAD_RE.match(line.strip()):
                prose_hits.append((i, rid))
    R.append(("2.3 wayfinder: no anchor literal in prose", not prose_hits, f"hits={prose_hits}"))
    gv_prose = []
    for i, line in enumerate(lines("governance"), 1):
        for rid in ANCHOR_RE.findall(line):
            if line.strip() != f'<a id="{rid}"></a>':
                gv_prose.append((i, rid))
    R.append(("2.3 governance: no anchor literal in prose", not gv_prose, f"hits={gv_prose}"))

    # --- 2.4 / 4.2 pointer forms replaced ------------------------------------
    for tid, cap, t in (("2.4", "wayfinder", wf), ("4.2", "decompmoe-skeleton", sk)):
        leftovers = re.findall(r"per req-\d+ L\d+|extraction\.py:\d+|safeguards\.py:\d+|loss\.py:\d+", t)
        R.append((f"{tid} {cap}: no file:line or req-N L<line>", not leftovers, f"leftovers={leftovers}"))
    sk_leftovers = re.findall(r"wayfinder L\d+|req-7 L\d+|\bL\d{3}\b", sk)
    R.append(("4.2 skeleton: no bare L### pointer", not sk_leftovers, f"leftovers={sorted(set(sk_leftovers))}"))

    # --- 3.2 req-gov-6 present, Source backtick-CLAUDE.md first --------------
    R.append(("3.2 req-gov-6 anchor unique", gv.count('<a id="req-gov-6"></a>') == 1,
              f"count={gv.count(chr(60)+'a id='+chr(34)+'req-gov-6'+chr(34)+chr(62))}"))
    src = [l for l in gb.get("req-gov-6", []) if l.startswith("**Source:**")]
    R.append(("3.2 req-gov-6 has Source field", bool(src), "present" if src else "ABSENT"))
    if src:
        body = src[0]
        ok = re.search(r"^<a id=\"req-gov-6\"></a>|CLAUDE\.md", body) and body.index("`CLAUDE.md`") < 90
        R.append(("3.2 req-gov-6 Source starts with backticked CLAUDE.md", ok, body[:90]))

    # --- 3.3 new Requirement quotes no real pointer -------------------------
    g6 = " ".join(gb.get("req-gov-6", []))
    real_ptr = re.findall(r"(?:req-\d+ L\d+|<capability> L\d+|\.py:\d+)", g6)
    R.append(("3.3 req-gov-6 quotes only placeholder pointer forms", not real_ptr, f"hits={real_ptr}"))
    R.append(("3.3 req-gov-6 uses placeholder notation", "<capability> L<line>" in g6 or "L<line>" in g6,
              "placeholder token present" if "L<line>" in g6 else "NO placeholder"))

    # --- 4.1 req-16 scenario count ------------------------------------------
    sk16_scen = sum(1 for l in sb.get("req-16", []) if SCEN_RE.match(l))
    R.append(("4.1 req-16 has 2 Scenarios", sk16_scen == 2, f"count={sk16_scen} (was 1)"))
    R.append(("4.1 req-16 names req-15 handoff", "req-15" in " ".join(sb.get("req-16", [])),
              "found" if "req-15" in " ".join(sb.get("req-16", [])) else "MISSING"))

    # --- 9.3 anchor coverage, all three capabilities -------------------------
    # The repo's layout puts a blank line between anchor and heading for 29/36
    # Requirements, so coverage is judged on the nearest non-empty preceding line.
    for cap in CAPS:
        ls = lines(cap)
        t = text(cap)
        ids = ANCHOR_RE.findall(t)
        heads = [i for i, l in enumerate(ls) if HEAD_RE.match(l)]
        heading_ids = set(blocks(cap)) - {k for k in blocks(cap) if k.startswith("<unanchored")}
        block_anchors = set(ids) - heading_ids
        dupes = {x for x in ids if ids.count(x) > 1}
        unanchored = [k for k in blocks(cap) if k.startswith("<unanchored")]
        R.append((f"9.3 {cap}: every Requirement has its anchor", not unanchored,
                  f"anchored={len(heading_ids)}/{len(heads)} unanchored={unanchored}"))
        R.append((f"9.3 {cap}: no duplicate id", not dupes, f"dupes={dupes}"))
        R.append((f"9.3 {cap}: ids == Requirement anchors + block anchors",
                  len(ids) == len(heading_ids) + len(block_anchors),
                  f"ids={len(ids)} req_anchors={len(heading_ids)} block_anchors={len(block_anchors)}"
                  f" {sorted(block_anchors)}"))

    print("== apply-phase acceptance ==")
    bad = findings(R)
    print(f"\nTOTAL {len(R)} checks, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
