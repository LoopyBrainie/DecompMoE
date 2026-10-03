"""Why does the lint attribute this reference to `governance`?

Prints every `req-N` / `#req-N` / `Req N` occurrence on the line together with
the capability words and `<cap>/spec.md` paths within the resolution window, so
the precedence chain can be read off directly instead of guessed at.
"""

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("lnp", ROOT / "scripts" / "lint_no_line_pointers.py")
lnp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lnp)

path = ROOT / "openspec" / "specs" / "decompmoe-skeleton" / "spec.md"
line = path.read_text(encoding="utf-8").splitlines()[97]
print(f"line length: {len(line)}")

refs = [(m.group(1), m.start()) for m in lnp.RE_REF_PLAIN.finditer(line)]
refs += [(m.group(1), m.start()) for m in lnp.RE_REF_WORD.finditer(line)]
refs += [(m.group(1), m.start()) for m in lnp.RE_REF_HASH.finditer(line)]
refs.sort(key=lambda x: x[1])

own = lnp.capability_of_spec(path)
inv = lnp.anchor_inventory(lnp.spec_paths())

for rid, pos in refs:
    cap, outcome = lnp.resolve_capability(rid, line, pos, own, inv)
    if outcome == "resolved" and cap in inv and rid in inv[cap]:
        continue
    print(f"\nUNRESOLVED {rid!r} at {pos} -> cap={cap} outcome={outcome}")
    print(f"  path rule  : {lnp.capability_from_path(line, pos)}")
    print(f"  word rule  : {lnp.nearest_capability(line, pos)}")
    lo, hi = max(0, pos - 60), min(len(line), pos + 60)
    print(f"  window     : ...{line[lo:hi]}...")
    for m in lnp.RE_PATH_CAPABILITY.finditer(line, max(0, pos - 48), min(len(line), pos + 48)):
        print(f"  path hit   : {m.group(0)!r} -> {m.group(1)} (ends {m.end()})")
    for m in lnp.RE_CAP_MENTION.finditer(line, max(0, pos - 48), min(len(line), pos + 48)):
        print(f"  word hit   : {m.group(0)!r} at {m.start()}-{m.end()}")
sys.exit(0)
