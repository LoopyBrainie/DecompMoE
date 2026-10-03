#!/usr/bin/env python3
"""Generate the two spec deltas for change 2026-10-03-a5-archive-gate-executability.

Why a script and not a hand-written delta:

* `req-34` is a 75-line / 7-Scenario block whose body contains very long single
  lines. Hand-transcription is a character-level corruption risk, and a corrupted
  body still greps fine for every keyword — the failure is silent.
* The substitution below is *bounded*: it replaces one unique in-line token and
  leaves every surrounding byte untouched, so it is structurally incapable of
  truncating a line the way a whole-line replacement is.

Verification is deliberately redundant with the tests (see `verify_deltas.py`):
block-level difflib, Scenario-count preservation, Source-field preservation, and
a line-length-collapse guard.

Run from anywhere inside the repository, before or after the archive moves this
change under `openspec/changes/archive/`:

    python openspec/changes/archive/2026-10-03-a5-archive-gate-executability/evidence/gen_deltas.py
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_EVIDENCE_DIR = Path(__file__).resolve().parent
_PATHS_SPEC = importlib.util.spec_from_file_location(
    "_a5_evidence_paths", _EVIDENCE_DIR / "_paths.py"
)
assert _PATHS_SPEC is not None and _PATHS_SPEC.loader is not None
_paths = importlib.util.module_from_spec(_PATHS_SPEC)
_PATHS_SPEC.loader.exec_module(_paths)

REPO = _paths.find_repo_root(_EVIDENCE_DIR)
CHANGE = _paths.find_change_dir(REPO, "2026-10-03-a5-archive-gate-executability")
_paths.refuse_if_archived("gen_deltas.py", CHANGE)
WAYFINDER_SPEC = REPO / "openspec" / "specs" / "wayfinder" / "spec.md"
OUT_WAYFINDER = CHANGE / "specs" / "wayfinder" / "spec.md"
OUT_GOVERNANCE = CHANGE / "specs" / "governance" / "spec.md"

ANCHOR_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
REQ_RE = re.compile(r"^### Requirement: (.+)$")


def fail(msg: str) -> None:
    print(f"gen_deltas: FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def extract_block(lines: list[str], requirement_title_fragment: str) -> tuple[int, int, str]:
    """Return `(start, end, title)` for the block whose heading contains the fragment.

    Block boundary rule: a line is a block start only if it is a standalone
    anchor AND the first non-empty line after it is a `### Requirement:` heading.
    Using "the next line is a heading" instead yields a one-line shell and lets a
    block-level anchor truncate its own Requirement (reproduced 3x in this repo's
    archive history).
    """
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

    for idx, (ln, anchor_id, title) in enumerate(starts):
        if requirement_title_fragment in title:
            end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(lines)
            return ln, end, title
    fail(f"no Requirement matching {requirement_title_fragment!r}")


def substitute_line(block: list[str], token: str, replacement: str) -> None:
    """Replace `token` with `replacement` in exactly one line of `block`.

    Bounded by construction: only the token changes, so the rest of the line —
    including the trailing period and any clause after the token — is preserved
    byte-for-byte. A whole-line assignment given a fragment is the classic way to
    silently destroy a line here.
    """
    hits = [i for i, line in enumerate(block) if token in line]
    if len(hits) != 1:
        fail(f"token expected in exactly 1 line, found {len(hits)}: {token[:70]!r}")
    i = hits[0]
    before = len(block[i])
    block[i] = block[i].replace(token, replacement)
    if len(block[i]) < before * 0.7:
        fail(f"line collapsed from {before} to {len(block[i])} chars at block line {i+1}")


# --- wayfinder: MODIFIED req-34 ---------------------------------------------

OLD_CLAUSE_1 = (
    "1. **Capability-aware substring presence** — the line MUST contain the "
    "per-capability required primary reverse-link substring (`CLAUDE.md` for "
    "governance, `wayfinder/tickets/` for all others)."
)
NEW_CLAUSE_1 = (
    "1. **Capability-aware presence, two independent parts** — the line MUST contain the "
    "per-capability required primary reverse-link marker (`CLAUDE.md` for governance, "
    "`wayfinder/tickets/` for all others), AND at least one backtick-wrapped code span MUST "
    "name a concrete file in the per-capability required form: `wayfinder/tickets/<ID>.md` "
    "for ticket lineage (where `<ID>` is the ticket file's stem, e.g. `A4-1`), or the "
    "literal `CLAUDE.md` for governance, which has no file to name. The bare directory form "
    "`wayfinder/tickets/` and the extension-less form `wayfinder/tickets/<ID>` MUST each be "
    "reported as violations: neither resolves to a file, and at the gate they are "
    "indistinguishable from the canonical form, so an untraceable reverse-link could pass."
)

OLD_SCENARIO_THEN = (
    "verifies the line contains the substring `wayfinder/tickets/` (or `CLAUDE.md` for the "
    "governance capability)"
)
NEW_SCENARIO_THEN = (
    "verifies (a) the line contains the per-capability marker substring `wayfinder/tickets/` "
    "(or `CLAUDE.md` for the governance capability), and (b) at least one backtick-wrapped "
    "code span matches the per-capability form (`wayfinder/tickets/<ID>.md`, or the literal "
    "`CLAUDE.md` for governance)"
)

OLD_SCENARIO_WHEN = (
    "contains the per-capability required primary reverse-link substring "
    "(`wayfinder/tickets/` for wayfinder-ticketed / decompmoe-skeleton specs, `CLAUDE.md` for "
    "governance specs) OUTSIDE a backtick-delimited code span"
)
NEW_SCENARIO_WHEN = (
    "contains the per-capability required primary reverse-link marker "
    "(`wayfinder/tickets/` for wayfinder-ticketed / decompmoe-skeleton specs, `CLAUDE.md` for "
    "governance specs) OUTSIDE a backtick-delimited code span"
)

NEW_SCENARIO = """
#### Scenario: Bare-directory and extension-less reverse-link forms are violations

- **WHEN** a `**Source:**` line's only ticket reverse-link is the bare directory form `` `wayfinder/tickets/` `` or the extension-less form `` `wayfinder/tickets/A4-1` ``
- **THEN** the script MUST report a violation stating that the reverse-link does not name a concrete file
- **AND** it MUST NOT be reported as passing merely because the marker substring is present, backtick-wrapped, and first
- **AND** the canonical form `` `wayfinder/tickets/A4-1.md` `` MUST pass unchanged
- **AND** the governance form `` `CLAUDE.md` `` MUST pass unchanged, since governance lineage names a file already and the tightened form check MUST NOT be asymmetric between capabilities
"""


def build_wayfinder_delta() -> str:
    lines = WAYFINDER_SPEC.read_text(encoding="utf-8").splitlines()
    start, end, title = extract_block(lines, "Source Field Format Invariant")
    block = lines[start - 1:end]

    n_scen_before = sum(1 for l in block if l.startswith("#### Scenario:"))
    n_lines_before = len(block)
    # `req-34` has NO top-level `**Source:**` field of its own — every match for
    # "Source:" inside its block is an inline mention in its prose. So the
    # invariant to assert is that the count is *unchanged*, not that one exists.
    # (Wayfinder currently has 36 Requirement headings and 35 top-level Source
    # lines; the lint validates Source lines that exist and cannot detect one that
    # is missing entirely. That gap is out of this change's scope — recorded, not
    # silently fixed.)
    n_source_before = sum(1 for l in block if l.startswith("**Source:**"))

    substitute_line(block, OLD_CLAUSE_1, NEW_CLAUSE_1)
    substitute_line(block, OLD_SCENARIO_THEN, NEW_SCENARIO_THEN)
    substitute_line(block, OLD_SCENARIO_WHEN, NEW_SCENARIO_WHEN)

    # Append the new Scenario as the last block element, keeping the trailing
    # blank line that separates this Requirement from the next one.
    while block and not block[-1].strip():
        block.pop()
    block.extend(NEW_SCENARIO.strip("\n").splitlines())
    block.append("")

    n_scen_after = sum(1 for l in block if l.startswith("#### Scenario:"))
    n_source_after = sum(1 for l in block if l.startswith("**Source:**"))
    if n_scen_after != n_scen_before + 1:
        fail(f"Scenario count {n_scen_before} -> {n_scen_after}, expected +1")
    if n_source_after != n_source_before:
        fail(f"Source-field count changed {n_source_before} -> {n_source_after}")

    body = "\n".join(block).rstrip("\n") + "\n"
    print(
        f"  req-34: {n_lines_before} -> {len(block)} lines, "
        f"{n_scen_before} -> {n_scen_after} Scenarios, "
        f"Source fields {n_source_before} -> {n_source_after} (unchanged)"
    )
    # The extracted block ALREADY begins with `<a id="req-34"></a>` and then the
    # `### Requirement:` heading. Do NOT prepend another heading: doing so
    # duplicates the Requirement and the parser then reads the block as having
    # zero scenarios. The anchor must stay on its own line immediately above the
    # heading, which is the block-boundary rule this extractor implements.
    assert block[0].startswith("<a id="), f"block must start with its anchor: {block[0]!r}"
    assert block[1].startswith("### Requirement:"), f"block[1] must be the heading: {block[1]!r}"
    assert block[1] == f"### Requirement: {title}", "block heading must match extracted title"
    return "## MODIFIED Requirements\n\n" + body


# --- governance: ADDED req-gov-7 / 8 / 9 ------------------------------------


def build_governance_delta() -> str:
    return "## ADDED Requirements\n" + GOV_BLOCK.strip("\n") + "\n"


GOV_BLOCK = """
<a id="req-gov-7"></a>
### Requirement: Archive Gate Must Be Executable

Every gate named as an `/opsx:archive` precondition MUST be a runnable command, MUST
exit non-zero on a tree that carries the defect class it claims to detect, and MUST be
reachable from a single named entry point. `CLAUDE.md` §3 MUST NOT enumerate individual
lint scripts: a list that must be edited by hand whenever a lint is added can and does
drift out of step with the scripts actually present, and a drifted list is a gate that
silently covers nothing.

**Source:** `CLAUDE.md` §3 (Workflow Conventions — the `/opsx:archive` precondition clause),
change `2026-10-03-a5-archive-gate-executability` design.md (Decision D1 — glob discovery
replaces enumeration)

#### Scenario: The gate list is not a separate list

- **WHEN** a new lint is added under `scripts/`
- **THEN** it MUST become part of the archive precondition without any edit to `CLAUDE.md`
- **AND** the precondition MUST name one entry-point command, not a per-script list

#### Scenario: A gate that cannot fail is not a gate

- **WHEN** the entry point discovers zero lints
- **THEN** it MUST exit non-zero
- **AND** it MUST NOT report a pass on the grounds that no discovered lint reported a violation

#### Scenario: The change being archived is validated as a change

- **WHEN** the archive precondition runs for a change with no spec delta and no `skip_specs`
- **THEN** the entry point MUST exit non-zero
- **AND** the reported cause MUST name the missing delta or the missing `skip_specs` marker
- **AND** the check MUST be scoped to the change being archived, so that unrelated stale changes in the same directory do not determine the result

<a id="req-gov-8"></a>
### Requirement: Gate Result Must Be Reproducible

A gate run MUST record `git rev-parse HEAD` and a digest of `git status --porcelain`
before executing, and MUST re-verify both after the last gate completes. If either
differs, the run MUST be reported as INVALID — a state distinct from both pass and
failure. An archive MUST be gated against a quiesced worktree, because a green result
computed over a tree that changed mid-run describes content that no longer exists.

**Source:** `CLAUDE.md` §3 (Workflow Conventions), change
`2026-10-03-a5-archive-gate-executability` design.md (Decision D2 — exit code 2 reserved
for an unstable worktree)

#### Scenario: The worktree changes while the gates run

- **WHEN** the post-run `git rev-parse HEAD` or worktree digest differs from the pre-run value
- **THEN** the entry point MUST report `GATE RESULT INVALID`
- **AND** it MUST exit with a code distinct from both the pass code and the violation code
- **AND** it MUST NOT print a pass summary for that run

#### Scenario: A dirty state with an unchanged file count is still a change

- **GIVEN** two different dirty worktrees that contain the same number of changed entries
- **THEN** the run MUST still detect the change
- **AND** the comparison MUST NOT rely on a changed-entry count alone

#### Scenario: A stable run is reported normally

- **WHEN** every gate completes and the pre-run and post-run snapshots are identical
- **THEN** the result MUST be reported as pass or violation according to the gates alone

<a id="req-gov-9"></a>
### Requirement: Spec Anchor Ledger Across Archive

`openspec archive` MUST leave the spec anchor ledger unchanged. The archive procedure
MUST be: write the ledger, archive, compare the ledger, restore any lost anchor
surgically, re-verify. Re-running the archive MUST NOT be used to repair a lost anchor,
because a second archive overwrites the first repair. A lost anchor MUST be reported by
id and by the Requirement it introduced, and MUST be listed separately from a declared-but-
never-added anchor, since the two are indistinguishable from raw counts alone.

**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause),
change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a ledger, not a
point-in-time count)

#### Scenario: Point-in-time coverage cannot detect the archive defect

- **WHEN** the archive drops the anchor of the Requirement following the one it rewrote
- **THEN** the anchor count and the Requirement-heading count remain equal
- **AND** a point-in-time coverage check MUST still report the tree as fully covered
- **AND** only a before/after ledger comparison MUST name the lost anchor

#### Scenario: Lost and never-added are separate classes

- **GIVEN** a baseline ledger, one anchor that disappeared, and one anchor the change declared it would add but which is absent
- **THEN** both MUST be reported
- **AND** they MUST appear in separate labelled lists
- **AND** a report giving only the net count MUST be treated as insufficient

#### Scenario: A block boundary requires the Requirement heading to follow the anchor

- **WHEN** a standalone anchor line is followed by a blank line and prose rather than a `### Requirement:` heading
- **THEN** it MUST NOT be treated as a Requirement block start
- **AND** an anchor quoted inline inside prose MUST NOT be counted as a Requirement header

#### Scenario: Repairing a lost anchor

- **WHEN** the ledger comparison reports a lost anchor
- **THEN** the anchor and its following blank line MUST be restored by direct edit
- **AND** the archive MUST NOT be re-run as the repair mechanism
"""


def main() -> int:
    print("gen_deltas: building wayfinder MODIFIED req-34")
    wf = build_wayfinder_delta()
    print("gen_deltas: building governance ADDED req-gov-7/8/9")
    gv = build_governance_delta()

    OUT_WAYFINDER.parent.mkdir(parents=True, exist_ok=True)
    OUT_GOVERNANCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_WAYFINDER.write_text(wf, encoding="utf-8")
    OUT_GOVERNANCE.write_text(gv, encoding="utf-8")

    print(f"  wrote {OUT_WAYFINDER.relative_to(REPO)} ({len(wf)} bytes)")
    print(f"  wrote {OUT_GOVERNANCE.relative_to(REPO)} ({len(gv)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
