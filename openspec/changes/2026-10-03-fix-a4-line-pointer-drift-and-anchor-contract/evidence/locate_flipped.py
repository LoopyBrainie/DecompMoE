"""Ground truth for the 4 sites that flipped to actionable after marker tightening."""

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location("pc", HERE / "pointer_census.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

TARGETS = [
    ("openspec/specs/decompmoe-skeleton/spec.md", 273),
    ("openspec/specs/decompmoe-skeleton/spec.md", 635),
    ("tests/test_config.py", 121),
    ("tests/test_sphere.py", 185),
]

anchors = pc.build_anchor_maps()


def owner_of(cap: str, lineno: int) -> str:
    amap = anchors.get(cap, {})
    return amap.get(lineno, "<unresolved>")


def title_of(cap: str, rid: str) -> str:
    p = ROOT / "openspec" / "specs" / cap / "spec.md"
    ls = p.read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(ls):
        if l.strip() == f'<a id="{rid}"></a>':
            for j in range(i + 1, min(i + 4, len(ls))):
                if ls[j].startswith("### Requirement:"):
                    return ls[j][len("### Requirement:"):].strip()
    return "<not found>"


for rel, lineno in TARGETS:
    line = (ROOT / rel).read_text(encoding="utf-8").splitlines()[lineno - 1]
    cap, hint, nums, kind = pc.classify(line)
    print(f"=== {rel}:{lineno}  kind={kind} cap={cap} hint={hint} lines={nums}")
    m = re.findall(r"[^\s]*(?:L\d{2,4}|\.py:\d+)", line)
    print(f"    pointer tokens: {m}")
    for cap2 in ("wayfinder", "decompmoe-skeleton"):
        for n in nums:
            o = owner_of(cap2, n)
            if o and not o.startswith("<"):
                print(f"    {cap2} L{n} -> {o} : {title_of(cap2, o)}")
    print(f"    full line: {line.strip()[:400]}")
    print()
sys.exit(0)
