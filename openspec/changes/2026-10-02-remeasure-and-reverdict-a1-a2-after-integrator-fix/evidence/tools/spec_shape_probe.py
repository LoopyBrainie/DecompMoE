"""Two questions, and the second one is the decisive one.

Q1 (was my last check even meaningful?): are the archive's spec.md files FULL
specs or OpenSpec DELTAs? Comparing a delta against a full spec would make my
"Change 2 spec edits are lost" alarm a self-inflicted false positive.

Q2 (decisive): do the LIVE specs still satisfy the Change 2 anchor-coverage
contract -- 36 wayfinder / 23 skeleton / 4 governance, 100% coverage, 0
duplicates, 0 misplacements? That number was recomputed at Change 2 completion.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
ARCH = ROOT / "openspec/changes/archive/2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard/specs"
EXPECT = {"wayfinder": 36, "decompmoe-skeleton": 23, "governance": 4}

print("Q1  archive spec.md size vs live spec.md size")
for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
    a, l = ARCH / cap / "spec.md", ROOT / f"openspec/specs/{cap}/spec.md"
    ab = a.read_bytes() if a.is_file() else b""
    heads = ab.decode("utf-8", "replace").splitlines()[:3]
    kind = "DELTA" if b"## ADDED" in ab or b"## MODIFIED" in ab or b"## REMOVED" in ab else "FULL?"
    print(f"  {cap:<20} archive {len(ab):>7} B   live {l.stat().st_size:>7} B   -> {kind}")
    for h in heads:
        print(f"      | {h[:96]}")
print()

print("Q2  anchor coverage of the LIVE specs (against Change 2's recomputed baseline)")
req_hdr = re.compile(r"^###\s+Requirement:")
anch = re.compile(r'<a\s+id="req-([0-9A-Za-z\-]+)"></a>')
for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
    live = (ROOT / f"openspec/specs/{cap}/spec.md").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    reqs = req_hdr.findall(live)
    anchors = anch.findall(live)
    # first top-level item of each Requirement body
    first_item_is_anchor = 0
    for m in re.finditer(r"^###\s+Requirement:", live, re.M):
        seg = live[m.start():]
        nxt = re.search(r"^###\s+", seg[len(m.group(0)):], re.M)
        seg = seg[: len(m.group(0)) + nxt.start()] if nxt else seg
        if re.search(r'<a\s+id="req-[0-9A-Za-z\-]+"></a>', seg):
            first_item_is_anchor += 1
    dup = len(anchors) - len(set(anchors))
    req_ids = {re.sub(r"^Requirement:\s*", "", r).split()[0] for r in reqs if r.split()}
    anc_ids = set(anchors)
    uncovered = sorted(req_ids - anc_ids)
    print(f"  {cap:<20} requirements={len(reqs):>3}  anchors={len(anchors):>3}  "
          f"expected={EXPECT[cap]:>3}  duplicates={dup}  "
          f"anchor_is_first_item={first_item_is_anchor}/{len(reqs)}")
    if uncovered:
        print(f"      requirements WITHOUT a matching anchor id: {uncovered}")
