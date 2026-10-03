#!/usr/bin/env python3
"""Generate the governance delta for change 2026-10-03-fix-a5-review-findings-round-2.

Why a generator rather than a hand-written delta:

* `req-gov-8`'s body is a multi-line paragraph. Re-typing it risks silent
  corruption, and a corrupted body still greps fine for every keyword it kept.
* The edit to it is *bounded*: each edit replaces one unique in-line token and
  leaves every surrounding byte untouched, so it is structurally incapable of
  truncating a line the way a whole-line assignment given a fragment is.

Verification is deliberately redundant with the tests (see `verify_deltas.py`):
block-level difflib against the live spec, Scenario preservation, Source-field
preservation, and a line-length-collapse guard.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_EVIDENCE_DIR = Path(__file__).resolve().parent
_PATHS_SPEC = __import__("importlib.util", fromlist=["util"]).spec_from_file_location(
    "_r2_evidence_paths", _EVIDENCE_DIR / "_paths.py"
)
assert _PATHS_SPEC is not None and _PATHS_SPEC.loader is not None
_paths = __import__("importlib.util", fromlist=["util"]).module_from_spec(_PATHS_SPEC)
_PATHS_SPEC.loader.exec_module(_paths)

CHANGE_NAME = "2026-10-03-fix-a5-review-findings-round-2"
REPO = _paths.find_repo_root(_EVIDENCE_DIR)
CHANGE = _paths.find_change_dir(REPO, CHANGE_NAME)
_paths.refuse_if_archived("gen_deltas.py", CHANGE)

GOV_SPEC = REPO / "openspec" / "specs" / "governance" / "spec.md"
OUT_GOV = CHANGE / "specs" / "governance" / "spec.md"

ANCHOR_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
REQ_RE = re.compile(r"^### Requirement: (.+)$")


def fail(msg: str) -> None:
    print(f"gen_deltas: FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def extract_block(lines: list[str], anchor_id: str) -> tuple[int, int, str]:
    """Return `(start, end, title)` for the block introduced by `anchor_id`.

    Block boundary rule: a line is a block start only if it is a standalone
    anchor AND the first non-empty line after it is a `### Requirement:` heading.
    """
    start = None
    for i, line in enumerate(lines):
        m = ANCHOR_RE.match(line.strip())
        if m and m.group(1) == anchor_id:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (rm := REQ_RE.match(lines[j])):
                start = i
                title = rm.group(1)
                break
    if start is None:
        fail(f"no block start for anchor {anchor_id!r}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("<a id="):
            end = i
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return start, end, title


def substitute_line(block: list[str], token: str, repl: str) -> None:
    """Replace `token` with `repl` on exactly one line of `block`.

    Bounded by construction: only the token is touched, so surrounding prose
    cannot be lost. The assertion on the hit count is the point -- a token that
    matches zero lines means the edit silently did nothing, and one that matches
    two means it hit the wrong place.
    """
    hits = [i for i, line in enumerate(block) if token in line]
    if len(hits) != 1:
        fail(f"token {token!r} matched {len(hits)} line(s) in block, expected 1")
    i = hits[0]
    before = len(block[i])
    block[i] = block[i].replace(token, repl)
    if len(block[i]) < before * 0.7:
        fail(
            f"line {i} collapsed from {before} to {len(block[i])} chars -- "
            "looks like a truncated whole-line replacement"
        )


def build() -> str:
    live = GOV_SPEC.read_text(encoding="utf-8").splitlines()

    # --- req-gov-8: porcelain digest -> content digests ----------------------
    s, e, _title = extract_block(live, "req-gov-8")
    g8 = live[s:e]

    substitute_line(
        g8,
        "a digest of `git status --porcelain`",
        "three content-sensitive components: the committed base "
        "(`git rev-parse HEAD`), a digest of the *content* of every tracked "
        "modification staged or unstaged (`sha256(git diff HEAD)`), and a digest "
        "of every untracked file's bytes enumerated individually, so that a new "
        "file inside an untracked directory counts",
    )
    substitute_line(
        g8,
        "computed over a tree that changed mid-run describes content that no "
        "longer exists.",
        "computed over a tree that changed mid-run describes content that no "
        "longer exists. A digest of `git status --porcelain` does not satisfy "
        "this Requirement: porcelain encodes a path and a status letter, not "
        "content, so two worktrees differing only in the bytes of an "
        "already-dirty file produce byte-identical porcelain and therefore a "
        "byte-identical digest.",
    )

    # New Scenario: the collision, stated so it cannot be re-derived wrong.
    g8 += [
        "",
        "#### Scenario: Two worktrees differing only in the bytes of a dirty file",
        "",
        "- **GIVEN** one tracked file already modified, whose content then changes again "
        "without its path or its status changing",
        "- **THEN** a digest of `git status --porcelain` MUST be identical for both states",
        "- **AND** the run MUST still detect the change, from tracked content rather "
        "than from porcelain",
        "- **AND** a derived count of changed entries MUST NOT be treated as an "
        "independent signal, because it is a coarser function of the same porcelain string",
    ]

    # --- req-gov-9: removed, its Scenario title asserts the opposite ----------
    s9, e9, title9 = extract_block(live, "req-gov-9")
    if "cannot detect" not in live[s9:e9][0] and "cannot detect" not in "\n".join(
        live[s9:e9]
    ):
        fail("req-gov-9 no longer contains the expected false Scenario title")
    if not any("cannot detect" in l for l in live[s9:e9]):
        fail("req-gov-9 false premise not found where expected")

    # --- req-gov-10: the same procedure, corrected and extended ------------
    # The title differs from the removed one on purpose. `openspec validate`
    # rejects a Requirement present in both ADDED and REMOVED, and a MODIFIED
    # block cannot be used because the existing Scenario *title* is the false
    # claim. The new title names what the Requirement now additionally requires
    # -- naming every loss -- rather than being a cosmetic respelling of the
    # same sentence.
    g10 = [
        '<a id="req-gov-10"></a>',
        "",
        "### Requirement: Spec Anchor Ledger Survives Archive And Names Every Loss",
        "",
        "`openspec archive` MUST leave the spec anchor ledger unchanged. The archive",
        "procedure MUST be: write the ledger, archive, compare the ledger, restore any lost",
        "anchor surgically, re-verify. Re-running the archive MUST NOT be used to repair a",
        "lost anchor, because a second archive overwrites the first repair.",
        "",
        "A point-in-time coverage check MUST NOT be treated as sufficient on its own. It",
        "does detect a swallowed anchor, because a swallow removes one Requirement's",
        "block-start anchor while leaving the heading count alone, and a simultaneously",
        "added Requirement carries its own anchor, so the deficit cannot be cancelled. What",
        "it cannot do is name anything: it reports a per-capability deficit rather than the",
        "anchor id or the Requirement that lost it, it cannot see an anchor id that",
        "survived but was re-attached to a different Requirement, and it cannot separate a",
        "lost anchor from one the change declared and never added. The ledger comparison",
        "MUST supply those three, and MUST report a lost anchor by id and by the Requirement",
        "it introduced, in a list separate from the declared-but-never-added one.",
        "",
        "**Source:** `CLAUDE.md` §6 (Hard Constraints — the 100% anchor coverage clause), "
        "change `2026-10-03-a5-archive-gate-executability` design.md (Decision D4 — a "
        "ledger, not a point-in-time count), corrected by change "
        "`2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D2 — the D4 premise "
        "was measured and is false)",
        "",
        "#### Scenario: A swallowed anchor is a count deficit, not an invisible loss",
        "",
        "- **WHEN** the archive drops the anchor of the Requirement following the one it rewrote",
        "- **THEN** the Requirement-heading count and the block-start anchor count diverge",
        "- **AND** a point-in-time coverage check MUST report the uncovered Requirement",
        "- **AND** the deficit MUST NOT be cancellable by any simultaneous addition, because "
        "an added Requirement carries its own anchor and moves both counts together",
        "",
        "#### Scenario: Naming what a count cannot",
        "",
        "- **GIVEN** a baseline ledger and a current ledger taken across one archive",
        "- **THEN** a before/after comparison MUST name each lost anchor id and the Requirement "
        "title it introduced",
        "- **AND** it MUST report an anchor id whose id is unchanged but whose introduced title "
        "changed, which a count-based check reports as fully covered",
        "- **AND** only a before/after comparison is permitted to make that claim",
        "",
        "#### Scenario: Lost and never-added are separate classes",
        "",
        "- **GIVEN** a baseline ledger, one anchor that disappeared, and one anchor the change "
        "declared it would add but which is absent",
        "- **THEN** both MUST be reported",
        "- **AND** they MUST appear in separate labelled lists",
        "- **AND** a report giving only the net count MUST be treated as insufficient",
        "",
        "#### Scenario: A block boundary requires the Requirement heading to follow the anchor",
        "",
        "- **WHEN** a standalone anchor line is followed by a blank line and prose rather than "
        "a `### Requirement:` heading",
        "- **THEN** it MUST NOT be treated as a Requirement block start",
        "- **AND** an anchor quoted inline inside prose MUST NOT be counted as a Requirement header",
        "",
        "#### Scenario: A section sub-anchor is not a declared Requirement",
        "",
        "- **GIVEN** an `## ADDED Requirements` delta block whose Requirement also carries a "
        "block-level section anchor such as `req-20-mci`",
        "- **THEN** only the anchor that introduces the `### Requirement:` heading MUST be "
        "collected as a declared addition",
        "- **AND** the section anchor MUST NOT be reported as a declared-but-never-added anchor, "
        "because the declared set is compared against block starts, which never contain it",
        "",
        "#### Scenario: Repairing a lost anchor",
        "",
        "- **WHEN** the ledger comparison reports a lost anchor",
        "- **THEN** the anchor and its following blank line MUST be restored by direct edit",
    ]

    # --- req-gov-11: Source field existence ---------------------------------
    g11 = [
        '<a id="req-gov-11"></a>',
        "",
        "### Requirement: Spec Requirements Carry A Source Field",
        "",
        "Every Requirement in a capability spec MUST carry a top-level `**Source:**` field. A",
        "Requirement that ships without one MUST fail the gate. Requirements that predate this",
        "Requirement and have no field MUST be listed in a registry of justified exemptions,",
        "and the registry MUST be an explicit, reviewable list of anchor ids rather than a count",
        "or a prefix, so that a newly authored Requirement without a field fails immediately.",
        "",
        "A registry entry MUST record the capability and the anchor id it exempts. An entry that",
        "names an anchor id which no longer exists, or which now carries a field, MUST itself be",
        "reported, so the registry cannot silently outlive the defect it was written to excuse.",
        "",
        "**Source:** `CLAUDE.md` §3 (Source 反链 requirement) and §6 (the ban on unverifiable "
        "clauses), change `2026-10-03-fix-a5-review-findings-round-2` design.md (Decision D4 — "
        "grandfather, do not fabricate lineage)",
        "",
        "#### Scenario: A new Requirement without a Source field",
        "",
        "- **WHEN** a Requirement is added to a capability spec without a top-level `**Source:**` field",
        "- **THEN** the Source-field gate MUST report the capability and the Requirement title",
        "- **AND** it MUST exit non-zero",
        "",
        "#### Scenario: A pre-existing Requirement with no field is exempt by id",
        "",
        "- **GIVEN** a Requirement whose anchor id appears in the justified-exemption registry",
        "- **THEN** the existence check MUST NOT report it",
        "- **AND** the registry MUST be reported separately from the violation list, so a green "
        "run does not imply full coverage",
        "",
        "#### Scenario: A stale exemption is itself a finding",
        "",
        "- **GIVEN** a registry entry whose anchor id no longer exists, or whose Requirement now "
        "carries a `**Source:**` field",
        "- **THEN** the gate MUST report the stale entry",
        "- **AND** it MUST exit non-zero, so the registry must be pruned rather than accumulate",
    ]

    removed9 = [
        "### Requirement: " + title9,
        "",
        "**Reason**: The Requirement's central Scenario was titled "
        "\"Point-in-time coverage cannot detect the archive defect\" and its body asserted that "
        "after a swallow \"the anchor count and the Requirement-heading count remain equal\" and "
        "a point-in-time check \"MUST still report the tree as fully covered\". Measured, both "
        "halves are false: removing one anchor line from a spec with 9 Requirement headings "
        "leaves 8 anchors, and the coverage check reports the uncovered Requirement. A Scenario "
        "title cannot be corrected in place, because `MODIFIED` blocks must retain the existing "
        "Scenario headings verbatim or the archive refuses to drop them -- so a spec that kept "
        "the old title would contradict its own body.",
        "",
        "**Migration**: Superseded by `req-gov-10`, which carries the same archive-procedure "
        "obligations with the false premise replaced by the measured behaviour, and adds the two "
        "defects a count-based check provably cannot see (an anchor id re-attached to a "
        "different Requirement, and a section sub-anchor miscounted as a declared addition). "
        "Cross-references to `req-gov-9` in `CLAUDE.md` and in `scripts/run_gates.py` were "
        "updated to `req-gov-10` in the same change.",
    ]

    out: list[str] = ["## MODIFIED Requirements", ""]
    out += g8 + [""]
    out += ["## REMOVED Requirements", ""]
    out += removed9 + [""]
    out += ["## ADDED Requirements", ""]
    out += g10 + [""]
    out += g11
    return "\n".join(out) + "\n"


def main() -> None:
    text = build()
    # Self-check on the *text*, before it is written: a block that lost a
    # Scenario or a Source field must fail here, not after the archive.
    # Counts are line-anchored. A raw substring count also matches the
    # backticked `### Requirement:` inside Scenario prose and would over-count
    # by two -- a counter that is a coarser function of the thing it measures
    # is exactly what these gates exist to reject.
    headings = re.findall(r"^### Requirement: ", text, re.M)
    assert len(headings) == 4, f"expected 4 Requirement blocks, got {len(headings)}: {headings}"
    sources = re.findall(r"^\*\*Source:\*\*", text, re.M)
    # MODIFIED req-gov-8, ADDED req-gov-10, ADDED req-gov-11. The REMOVED
    # block must NOT carry one: a removal is not a live Requirement.
    assert len(sources) == 3, f"expected 3 Source fields, got {len(sources)}"
    modified_part = text.split("## REMOVED Requirements")[0]
    assert "req-gov-9" not in modified_part, (
        "req-gov-9 must not appear in MODIFIED; it is being REMOVED. "
        "A mention in the REMOVED block's Migration note is expected and correct."
    )
    for anchor in ("req-gov-8", "req-gov-10", "req-gov-11"):
        assert f'<a id="{anchor}"></a>' in text, f"missing anchor {anchor}"
    OUT_GOV.parent.mkdir(parents=True, exist_ok=True)
    OUT_GOV.write_text(text, encoding="utf-8")
    print(f"  wrote {OUT_GOV.relative_to(REPO)} ({len(text.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
