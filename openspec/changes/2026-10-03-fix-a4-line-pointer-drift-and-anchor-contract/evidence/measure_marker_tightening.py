"""Measure the scope delta between the loose and the substantive marker set.

The census exempts a whole LINE on any marker substring. `ex-` and `->` fire on
ordinary vocabulary ("example", math arrows, `-> Tensor` return annotations), so
they exempt lines that also carry a live pointer. This script reports, for each
loosely-exempt line, whether it is still exempt under a substantive-only marker
set, and for the ones that flip, prints the live pointer that would be missed.

Substantive set = the markers the new req-gov-6 clause 6 names as an explicit
historical marker, minus the two that are not discriminative on their own.
"""

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pc", HERE / "pointer_census.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

LOOSE_ONLY = {"ex-", "→"}
SUBSTANTIVE = tuple(m for m in pc.HISTORICAL_MARKERS if m not in LOOSE_ONLY)
COMMIT_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


def has_substantive(text: str) -> bool:
    low = text.lower()
    if any(m.lower() in low for m in SUBSTANTIVE):
        return True
    return bool(COMMIT_RE.search(text))


def main() -> int:
    loose_exempt, flips = [], []
    for path in pc.iter_files():
        r = pc.rel(path)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "http" in line:
                continue
            tgt = pc.classify(line)
            if tgt is None or not pc.has_historical_marker(line):
                continue
            loose_exempt.append((r, lineno, line))
            if not has_substantive(line):
                cap, hint, nums, kind = tgt
                flips.append((r, lineno, kind, nums, line.strip()[:200]))

    print(f"loose-exempt lines          : {len(loose_exempt)}")
    print(f"substantive-exempt lines    : {len(loose_exempt) - len(flips)}")
    print(f"FLIP to actionable          : {len(flips)}")
    print()
    for r, lineno, kind, nums, text in flips:
        print(f"  {r}:{lineno}  kind={kind} lines={nums}")
        print(f"      {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
