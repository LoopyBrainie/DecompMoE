"""Probe: does a MODIFIED block that renames an existing Scenario get
refused? Read the exact Requirement title and Scenario headings from the
live spec rather than transcribing them, so encoding cannot corrupt the
probe.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(r"D:\myProject\DecompMoE")
SPEC = ROOT / "openspec" / "specs" / "governance" / "spec.md"
OUT = (ROOT / "openspec" / "changes"
       / "2026-10-03-close-pointer-blindspot-and-full-tree-sweep"
       / "specs" / "governance" / "spec.md")

RE_REQ = re.compile(r"^### Requirement: (.*)$")
RE_SCEN = re.compile(r"^#### Scenario: (.*)$")


def block_for(anchor_id: str):
    """Return (requirement_title, [scenario_titles]) for one Requirement."""
    lines = SPEC.read_text(encoding="utf-8").splitlines()
    start = None
    for i, line in enumerate(lines):
        if '<a id="%s"></a>' % anchor_id in line:
            start = i + 1
            break
    if start is None:
        raise SystemExit("anchor %s not found" % anchor_id)
    title = None
    scen = []
    for line in lines[start:]:
        m = RE_REQ.match(line)
        if m:
            if title is not None:
                break        # the next Requirement begins: this block ends
            title = m.group(1)
            continue
        if title is not None and RE_SCEN.match(line):
            scen.append(RE_SCEN.match(line).group(1))
    return title, scen


def build(anchor_id: str, rename: bool) -> str:
    title, scen = block_for(anchor_id)
    out = ["## MODIFIED Requirements", "",
           "### Requirement: %s" % title, "",
           "Probe body for the scenario-rename constraint.", ""]
    for i, s in enumerate(scen):
        name = s
        if rename and i == 0:
            name = s.replace("L70", "<rewritten>").replace("L74", "<rewritten>")
        out += ["#### Scenario: %s" % name, "",
                "- **WHEN** probed", "- **THEN** it passes", ""]
    return "\n".join(out)


if __name__ == "__main__":
    rename = "--rename" in sys.argv
    anchor = "req-gov-2"
    for a in sys.argv[1:]:
        if a.startswith("--anchor="):
            anchor = a.split("=", 1)[1]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = build(anchor, rename)
    OUT.write_text(text, encoding="utf-8")
    t, s = block_for(anchor)
    print("requirement: %s" % t)
    print("scenarios  : %d" % len(s))
    for x in s:
        print("   - %s" % x)
    # Read the artifact back: a generator that silently emits the wrong
    # Requirement is worse than no generator, and only re-reading catches it.
    back = OUT.read_text(encoding="utf-8")
    assert "### Requirement: %s" % t in back, "title not written verbatim"
    for x in s:
        expect = x.replace("L70", "<rewritten>").replace("L74", "<rewritten>") \
            if rename else x
        assert "#### Scenario: %s" % expect in back, "scenario lost: %s" % expect
    print("read-back OK: %d scenario(s) round-tripped" % len(s))
    print("wrote %s (rename=%s)" % (OUT, rename))
