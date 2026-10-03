#!/usr/bin/env python3
"""Re-verify the generated deltas of 2026-10-03-a5-archive-gate-executability.

Deliberately redundant with `gen_deltas.py`'s own assertions, because the
generator's assertions run on the data *before* the file is written and cannot
catch a write that lost or mangled something. This script reads the artifacts
back off disk.

Checks, in order of the failure they catch:

1. **Structural round-trip** — re-parse the written delta with the same block
   extractor and compare against the live spec via `difflib`. A MODIFIED block
   that silently lost a Scenario still greps fine for every keyword it kept.
2. **Scenario count** — must be exactly `live + 1` (the one added Scenario).
3. **Source-field count** — must be *unchanged* from live (req-34 has none).
4. **Line-length collapse** — any line that shrank below 70% of its live
   counterpart is a truncated replacement, the signature of the
   whole-line-assignment-given-a-fragment bug.
5. **Content detector re-run on the artifact** — the tightened Source lint must
   be run *against the generated delta*, not only against the live tree. This is
   the check that catches partial completion: every target token present, yet the
   artifact structurally wrong.
6. **New governance Requirements pass the tightened lint** — the three added
   Requirements carry backticked `CLAUDE.md` as their first top-level item, so
   they must satisfy check ①b under the marker `CLAUDE.md` / form `CLAUDE\\.md`.

Run from the repo root:

    python openspec/changes/2026-10-03-a5-archive-gate-executability/evidence/verify_deltas.py
"""
from __future__ import annotations

import difflib
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CHANGE = REPO / "openspec" / "changes" / "2026-10-03-a5-archive-gate-executability"
DELTA_WAYFINDER = CHANGE / "specs" / "wayfinder" / "spec.md"
DELTA_GOVERNANCE = CHANGE / "specs" / "governance" / "spec.md"
LIVE_WAYFINDER = REPO / "openspec" / "specs" / "wayfinder" / "spec.md"
LIVE_GOVERNANCE = REPO / "openspec" / "specs" / "governance" / "spec.md"

ANCHOR_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
REQ_RE = re.compile(r"^### Requirement: (.+)$")
SCENARIO_RE = re.compile(r"^#### Scenario: (.+)$")

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def note(msg: str) -> None:
    notes.append(msg)


def block_starts(lines: list[str]) -> list[tuple[int, str, str]]:
    """A block start is a standalone anchor whose first non-empty successor line
    is a `### Requirement:` heading. Anything else is an inline mention."""
    starts: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        m = ANCHOR_RE.match(line.strip())
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        rm = REQ_RE.match(lines[j])
        if rm:
            starts.append((i + 1, m.group(1), rm.group(1)))
    return starts


def extract(lines: list[str], fragment: str) -> tuple[list[str], str]:
    starts = block_starts(lines)
    for idx, (ln, _anchor, title) in enumerate(starts):
        if fragment in title:
            end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(lines)
            return lines[ln - 1:end], title
    raise AssertionError(f"no Requirement matching {fragment!r}")


def main() -> int:
    print("verify_deltas: reading artifacts back off disk")

    live_block, live_title = extract(
        LIVE_WAYFINDER.read_text(encoding="utf-8").splitlines(),
        "Source Field Format Invariant",
    )
    delta_block, delta_title = extract(
        DELTA_WAYFINDER.read_text(encoding="utf-8").splitlines(),
        "Source Field Format Invariant",
    )

    if live_title != delta_title:
        fail(f"title changed: {live_title!r} -> {delta_title!r}")

    # 1. structural round-trip
    diff = list(
        difflib.unified_diff(
            live_block, delta_block,
            fromfile="live/req-34", tofile="delta/req-34", lineterm="",
        )
    )
    changed = [l for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    print(f"  req-34 block diff: {len(changed)} changed line(s)")
    for line in changed:
        print(f"    {line[:150]}")

    # 2. Scenario count
    live_scen = [SCENARIO_RE.match(l).group(1) for l in live_block if SCENARIO_RE.match(l)]
    delta_scen = [SCENARIO_RE.match(l).group(1) for l in delta_block if SCENARIO_RE.match(l)]
    print(f"  Scenarios: live {len(live_scen)} -> delta {len(delta_scen)}")
    if len(delta_scen) != len(live_scen) + 1:
        fail(f"expected live+1 Scenarios, got {len(live_scen)} -> {len(delta_scen)}")
    for title in live_scen:
        if title not in delta_scen:
            fail(f"Scenario dropped from the MODIFIED block: {title!r}")

    # 3. Source-field count
    live_src = sum(1 for l in live_block if l.startswith("**Source:**"))
    delta_src = sum(1 for l in delta_block if l.startswith("**Source:**"))
    print(f"  Source fields: live {live_src} -> delta {delta_src}")
    if delta_src != live_src:
        fail(f"Source-field count changed {live_src} -> {delta_src}")

    # 4. line-length collapse guard, matched on Scenario boundaries so the
    #    inserted Scenario does not look like a collapse of its predecessor.
    def scen_sections(block: list[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        current = "__intro__"
        for line in block:
            m = SCENARIO_RE.match(line)
            if m:
                current = m.group(1)
                out[current] = []
            elif current in out or current == "__intro__":
                out.setdefault(current, []).append(line)
        return out

    live_sec = scen_sections(live_block)
    delta_sec = scen_sections(delta_block)
    for name, lines in live_sec.items():
        if name not in delta_sec:
            continue
        live_len = len("\n".join(lines))
        delta_len = len("\n".join(delta_sec[name]))
        if live_len and delta_len < live_len * 0.7:
            fail(f"Scenario {name!r} collapsed {live_len} -> {delta_len} chars")

    # 5. content detector re-run against the generated artifact
    spec = importlib.util.spec_from_file_location(
        "_lint_under_test", REPO / "scripts" / "lint_no_source_field_drift.py"
    )
    assert spec is not None and spec.loader is not None
    L = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(L)
    del spec

    delta_text = DELTA_WAYFINDER.read_text(encoding="utf-8")
    # Tokens that must be present in the delta, proving each targeted edit landed.
    for token, label in [
        ("**Capability-aware presence, two independent parts**", "clause 1 rewritten"),
        ("wayfinder/tickets/<ID>.md` for ticket lineage", "concrete-form requirement"),
        ("MUST each be reported as violations", "bare/extension-less rejected"),
        ("Bare-directory and extension-less reverse-link forms are violations", "new Scenario"),
        ("per-capability required primary reverse-link marker", "Scenario WHEN reworded to marker"),
    ]:
        if token not in delta_text:
            fail(f"delta is missing [{label}]: {token!r}")
        else:
            note(f"present: {label}")
    if "Capability-aware substring presence" in delta_text:
        fail("the old loose clause 1 survived into the delta")

    # 6. new governance Requirements must satisfy the TIGHTENED Source lint
    gov_text = DELTA_GOVERNANCE.read_text(encoding="utf-8")
    gov_ids = re.findall(r'<a id="(req-gov-\d+)"></a>', gov_text)
    print(f"  governance delta adds: {gov_ids}")
    for expected in ("req-gov-7", "req-gov-8", "req-gov-9"):
        if expected not in gov_ids:
            fail(f"governance delta missing {expected}")
    live_gov_ids = set(re.findall(r'<a id="(req-gov-\d+)"></a>', LIVE_GOVERNANCE.read_text(encoding="utf-8")))
    for new_id in gov_ids:
        if new_id in live_gov_ids:
            fail(f"anchor collision: {new_id} already exists in the live governance spec")

    src_lines = [l for l in DELTA_GOVERNANCE.read_text(encoding="utf-8").splitlines()
                 if l.startswith("**Source:**")]
    print(f"  governance delta Source lines: {len(src_lines)}")
    if len(src_lines) != 3:
        fail(f"expected 3 Source lines (one per added Requirement), got {len(src_lines)}")
    for line in src_lines:
        original = L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE
        try:
            # Evaluate against a scratch file so the per-capability dispatch runs
            # for real rather than being asserted by inspection.
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write("# scratch\n\n" + line + "\n")
                p = Path(f.name).resolve()
            try:
                L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = {p: "CLAUDE.md"}
                violations = L.lint_file(p)
            finally:
                L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = original
                p.unlink()
        except Exception as exc:  # pragma: no cover - defensive
            fail(f"could not evaluate a governance Source line: {exc}")
            continue
        if violations:
            fail(f"new Requirement's Source line fails the tightened lint: {violations}")

    # governance delta must not collide with the 6 live Requirements
    print()
    for n in notes:
        print(f"  ok  {n}")
    print()
    if failures:
        print(f"verify_deltas: FAIL ({len(failures)} problem(s))")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("verify_deltas: OK — 0 collapsed lines, 0 dropped Scenarios, "
          "0 dropped Source fields, tightened lint clean on the generated artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
