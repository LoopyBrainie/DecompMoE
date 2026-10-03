"""Probe 2: how are anchors positioned relative to Requirement headings?"""

import re
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
HEAD = re.compile(r"^### Requirement:")
ANCHOR = re.compile(r'<a id="([^"]+)"></a>')

for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
    ls = (ROOT / "openspec" / "specs" / cap / "spec.md").read_text(encoding="utf-8").splitlines()
    heads = [i for i, l in enumerate(ls) if HEAD.match(l)]
    gap_hist: dict[int, int] = {}
    covered_strict = covered_skipblank = 0
    missing: list[str] = []
    for i in heads:
        prev = ls[i - 1].strip() if i else ""
        gap = 0
        k = i - 1
        while k >= 0 and not ls[k].strip():
            gap += 1
            k -= 1
        near = ls[k].strip() if k >= 0 else ""
        gap_hist[gap] = gap_hist.get(gap, 0) + 1
        if ANCHOR.fullmatch(prev):
            covered_strict += 1
        if ANCHOR.fullmatch(near):
            covered_skipblank += 1
        else:
            missing.append(f"L{i+1}:{ls[i][:60]}")
    print(f"== {cap}: headings={len(heads)} strict_prev_line={covered_strict} "
          f"nearest_nonempty={covered_skipblank} gap_hist={gap_hist}")
    for m in missing:
        print("   NO ANCHOR:", m)

    # req-20 block sanity
    if cap == "wayfinder":
        for target in ("req-20", "req-17", "req-2"):
            idx = [i for i, l in enumerate(ls) if l.strip() == f'<a id="{target}"></a>']
            if not idx:
                print(f"   {target}: ANCHOR LINE NOT FOUND")
                continue
            i = idx[0]
            end = next((j for j in range(i + 1, len(ls)) if HEAD.match(ls[j])), len(ls))
            scen = [l for l in ls[i:end] if l.startswith("#### Scenario:")]
            src = [l for l in ls[i:end] if l.startswith("**Source:**")]
            print(f"   {target}: block L{i+1}-L{end} lines={end-i} scenarios={len(scen)} source={len(src)}")
sys.exit(0)
