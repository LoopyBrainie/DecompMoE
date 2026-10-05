"""Tests for `scripts/lint_no_baseline_counts`.

Load pattern mirrors `tests/test_lint_no_source_field_drift.py`: the script lives
in `scripts/`, which is NOT on the pyproject `pythonpath`, so it is loaded with
`importlib` rather than by putting `scripts/` on `sys.path` — lint infrastructure
is not first-party code.

**The discriminative test is the point of this file.** `lint_no_line_pointers.py`
exists because "the same defect family was fixed by hand five times, each pass
leaving siblings behind, because no check could say whether the fix was complete".
A lint that has never gone red has never demonstrated it can. So
`test_red_on_real_instance_and_green_once_baselined` takes the *verbatim* sentence
from the archive that motivated this work, asserts the lint reports it, and then
asserts the same sentence is clean once a baseline is named.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lint_no_baseline_counts.py"
_spec = importlib.util.spec_from_file_location("_lint_no_baseline_counts_under_test", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None, "Could not load lint spec"
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
del _spec


# --- the discriminative test -------------------------------------------------

# Verbatim from archive/2026-10-03-a5-archive-gate-executability/evidence/incident.md,
# "How it was detected". This is the sentence the whole change is about: the ledger
# moved 65 -> 67 and the net count is the ONLY thing that caught the swallowed anchor.
# No commit anywhere holds a governance=8-anchor state, so this figure cannot be
# re-derived — and the sentence names no baseline to tell the reader that.
REAL_INSTANCE = (
    "It was caught by the **net count**: the ledger moved 65 → 67 where 65 + 3\n"
    "additions = 68. One anchor short."
)


def test_red_on_real_instance_and_green_once_baselined() -> None:
    """The motivating sentence must be reported, and silent once it has a baseline.

    Both directions matter. Red alone would be a lint that cannot pass; green alone
    would be a lint that cannot fire. The pair is what makes the gate trustworthy.
    """
    assert L.check_text(REAL_INSTANCE), (
        "the verbatim incident sentence is a baseline-less count and MUST be reported; "
        "if this fails the lint cannot detect the case that motivated it"
    )

    baselined = (
        "It was caught by the **net count**: the ledger moved 65 → 67 where 65 + 3\n"
        "additions = 68. One anchor short. Recorded at `ea802c8`; the intermediate\n"
        "state is not reconstructible from git."
    )
    assert L.check_text(baselined) == [], (
        f"a revision plus a not-reconstructible marker must silence the report, "
        f"actual={L.check_text(baselined)}"
    )


# --- what counts as a count --------------------------------------------------


@pytest.mark.parametrize(
    "line, why",
    [
        ("the ledger moved 65 → 67", "transition"),
        ("strict 48 / loose 48", "paired counts"),
        ("governance accounted for 12% of anchors", "percentage"),
        ("A-8 清单有 6 条问题归入该桶", "CJK counter"),
        ("`_paths.py` 新增 110 行", "CJK counter"),
    ],
)
def test_detects_each_count_form(line: str, why: str) -> None:
    assert L.check_text(line), f"{why} form must be detected in: {line!r}"


@pytest.mark.parametrize(
    "line",
    [
        "`CLAUDE.md` §6 第 8 条",  # clause reference, not a measurement
        "## D8 — 数值闭式的二分",  # a heading is a label, not a claim
        "total ≈ 452M",
        "the ledger is at `ea802c8`",  # hash but no count: nothing to baseline
    ],
)
def test_does_not_flag_non_counts(line: str) -> None:
    assert L.check_text(line) == [], f"not a count, must not be reported: {line!r}"


# --- what counts as a baseline -----------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        "the ledger moved 65 → 67 at `ea802c8`",  # commit hash
        "实测 23 条，HEAD 工作树",  # HEAD
        "见 2026-10-04-phase2-gamma-reset-ramp-closure",  # change name
        "strict 48 / loose 48 per req-gov-1",  # Requirement anchor
        "65 anchors (`git ls-files` 复核)",  # reproducible command
        "总计 68（`block_starts` 口径）",  # the counting rule itself
        "48/48 在 revision 27336a4 成立",  # explicit baseline word
    ],
)
def test_baseline_in_same_block_silences_the_report(line: str) -> None:
    assert L.check_text(line) == [], f"a baseline is present, must be silent: {line!r}"


def test_baseline_in_an_adjacent_block_does_not_silence() -> None:
    """A baseline in the neighbouring paragraph is not this block's baseline.

    Over-silencing is the failure mode that lets a whole document drift again: if
    any baseline anywhere in the file suppressed every count, the lint would be
    decorative.
    """
    text = (
        "At `ea802c8` the count was 65 anchors.\n"
        "\n"
        "The dirty entries at delivery time were 48 个脏条目.\n"
    )
    findings = L.check_text(text)
    assert len(findings) == 1, f"exactly the unbaselined block must be reported, actual={findings}"
    assert "48" in findings[0][2], f"expected the second block, actual={findings}"

# --- exemption markers (in-document, no registry) ---------------------------


@pytest.mark.parametrize(
    "line, marker",
    [
        ("65 → 67 不可复算", "无法复算"),
        ("65 → 67 (not reconstructible from git)", "not reconstructible"),
        ("48 dirty entries — pre-this-change", "pre-this-change"),
        ("原值 65 条, superseded by spec req-gov-12", "superseded"),
        ("27336a4 已知，待独立裁决", "待独立裁决"),
        ("65 → 67 条，本轮不处置", "不处置"),
        # `histor` is a bare substring, so it also silences "historical". That is
        # deliberate — a historical figure is past-tense by definition — but it is
        # also the marker most capable of over-silencing, so it is pinned here
        # rather than left to be discovered as a false negative.
        ("原值 36/decompmoe-skeleton 23 个，historical", "histor"),
    ],
)
def test_every_declared_marker_silences_the_report(line: str, marker: str) -> None:
    """One case per declared marker, so the set cannot grow without coverage.

    `tasks.md` claimed "8 markers" while testing 5. The count of a declared set and
    the count of its covered members are both checkable, so both are.
    """
    assert marker in L.EXEMPTION_MARKERS, f"{marker!r} is not a declared marker"
    assert L.check_text(line) == [], f"marker {marker!r} must exempt: {line!r}"


def test_marker_set_is_fully_covered_by_the_cases_above() -> None:
    """Every declared marker appears in a silencing test.

    Guards the drift this file exists to prevent: a new marker added to the script
    without a case would otherwise be untested, and a marker removed from the script
    would leave a case passing for the wrong reason.
    """
    covered = {
        "pre-this-change",
        "histor",
        "superseded",
        "not reconstructible",
        "无法复算",
        "不可复算",
        "待独立裁决",
        "不处置",
    }
    assert set(L.EXEMPTION_MARKERS) == covered, (
        f"declared markers and covered markers diverged: "
        f"declared={sorted(set(L.EXEMPTION_MARKERS))} covered={sorted(covered)}"
    )


# --- blind spots this lint had while being written --------------------------


def test_count_table_without_a_baseline_is_reported() -> None:
    """A table row is not exempt just because it is a table.

    This was a real blind spot: table rows were skipped wholesale, and a count
    table is the most natural place for this family to hide. The table's HEADER
    is where a baseline would be named, so the whole run including the header is
    the block.
    """
    text = (
        "| revision | wayfinder | governance |\n"
        "|---|---|---|\n"
        "| `940b27c` | 36 | 6 |\n"
    )
    assert L.check_text(text) == [], "header names revisions, so this table IS baselined"

    unbaselined = (
        "| phase | wayfinder | governance |\n"
        "|---|---|---|\n"
        "| one | 36 | 6 |\n"
        "| two | 38 | 9 |\n"
    )
    assert L.check_text(unbaselined), "a table with no revision anywhere must be reported"


def test_fenced_block_is_quoted_material_and_not_reported() -> None:
    """Counts inside a fence belong to the quoted text, not to this document."""
    text = (
        "```text\n"
        "65 → 67 48 / 48 12% 6 条\n"
        "```\n"
    )
    assert L.check_text(text) == [], f"fenced counts are quoted, actual={L.check_text(text)}"


def test_fence_toggle_ignores_inline_backticks() -> None:
    """A ``` appearing mid-sentence must not open a fence.

    This is the discriminating half. The test above feeds a well-formed fence, and
    an implementation that toggles on `` ``` `` *anywhere in a line* passes it too —
    which is exactly the first-draft bug this file was written to pin. Without an
    input that separates the two, the fix is unfalsifiable and the docstring's claim
    that it is "pinned" is false.
    """
    text = "the ledger moved 65 → 67 ``` inline\n"
    findings = L.check_text(text)
    assert findings, (
        "an inline ``` is not a fence delimiter; the count on that line is real prose "
        f"and must still be reported, actual={findings}"
    )
    assert "transition" in findings[0][1], findings


def test_one_report_per_block_not_per_count() -> None:
    """A paragraph of five unbaselined counts is one defect, not five.

    Reporting per count inflates the headline number, which is the number the
    triage pass reads first — and an inflated number is how a family gets
    dismissed as noise.
    """
    text = "ratios 48/48 and 49/49 and 12% and 5 项 and 65 → 67\n"
    assert len(L.check_text(text)) == 1, (
        f"expected 1 block-level report, actual={L.check_text(text)}"
    )


# --- scope -------------------------------------------------------------------


def test_inline_code_span_counts_are_quoted_material() -> None:
    """A count inside backticks shows the *shape* a rule matches, not a claim.

    Same argument as the fence rule, applied to the inline case: this file's own
    defect list contains `48 / loose 48` written to show what the pattern looks
    like, and that is not a measurement of anything in this repository.
    """
    quoted = "5. `48 / loose 48` 不被 `\\d+/\\d+` 匹配 ⇒ 增 `paired counts`\n"
    assert L.check_text(quoted) == [], (
        f"a count quoted in backticks is an example, actual={L.check_text(quoted)}"
    )
    # …but the same count outside backticks is a real claim and must be reported.
    real = "5. 48 / loose 48 is the actual violation ratio on this tree\n"
    assert L.check_text(real), "outside backticks the count is a claim, must be reported"


def test_code_span_stripping_does_not_hide_the_baseline() -> None:
    """The strip is local to count detection; baselines still match inside spans.

    The commonest baseline of all is a hash written in a code span. If stripping
    spans also removed baselines, every `at <sha>` would start reporting — the
    mirror image of the bug above, and far worse.
    """
    assert L.check_text("at `ea802c8` the count is 65 → 67\n") == [], (
        "a hash inside a code span is still a baseline"
    )


def test_named_test_counts_as_a_baseline() -> None:
    """A test that pins a figure is a re-derivation pointer, like a command.

    A table of closed forms whose Assert column names the test enforcing it is
    baselined: the reader can re-assert the claim. Without this, every such table
    reports — and the tables most likely to be baselined are the well-sourced ones.
    """
    pinned = (
        "| closed form | asserted by |\n"
        "|---|---|\n"
        "| payload 键集恰为 5 项 | `test_written_payload_carries_exactly_the_five` |\n"
    )
    assert L.check_text(pinned) == [], (
        f"a named test is a baseline, actual={L.check_text(pinned)}"
    )
    unpinned = (
        "| closed form | asserted by |\n"
        "|---|---|\n"
        "| payload 键集恰为 5 项 | (none) |\n"
    )
    assert L.check_text(unpinned), "without the pointer, the count is unbaselined"


def test_evidence_files_excludes_archive_and_specs() -> None:
    """The gate must not demand an edit the archive rules forbid."""
    paths = L.evidence_files()
    rels = [str(p.relative_to(_REPO_ROOT)).replace("\\", "/") for p in paths]
    assert rels, "must find the evidence layer"
    for rel in rels:
        assert "openspec/changes/archive/" not in rel, (
            f"archive is read-only (req-gov-5) and must not be scanned: {rel}"
        )
        assert not rel.startswith("openspec/specs/"), (
            f"spec counts are governed by req-gov-5's provenance clause: {rel}"
        )
        assert not rel.startswith(".audit/"), (
            f".audit is gitignored and unversioned: {rel}"
        )
        assert rel.endswith((".md",)), rel


def test_spec_counts_are_inert_to_the_lint_rules_but_never_routed_here() -> None:
    """Two separate claims, asserted separately.

    The first: a count under a spec heading is ordinary prose to these rules, and
    the rules do not know or care which file a line came from. Asserting that
    `check_text` ignores the filename would be vacuous — it takes no filename — so
    the meaningful half is the second: nothing routes a spec *file* here.
    """
    findings = L.check_text("## Requirement: X\n\nThe count is 65 → 67 here.\n")
    assert len(findings) == 1, (
        "the rule is content-based and would fire on this prose; what matters is "
        f"that no spec FILE is ever routed here, actual={findings}"
    )
    rels = [str(p.relative_to(_REPO_ROOT)).replace("\\", "/") for p in L.evidence_files()]
    assert not any(r.startswith("openspec/specs/") for r in rels), (
        f"spec files are governed by req-gov-5's provenance clause, not here: {rels}"
    )


def test_scope_follows_gate_change(monkeypatch) -> None:
    """`GATE_CHANGE` narrows the scan to one change, per req-gov-7's scoping rule.

    Without this, the gate's verdict is a function of every sibling change's
    in-flight edits — which is how a gate gets switched off, and how a green can
    be produced by somebody else's commit instead of by this change.
    """
    monkeypatch.setenv("GATE_CHANGE", "2026-10-04-archive-evidence-provenance")
    rels = [str(p.relative_to(_REPO_ROOT)).replace("\\", "/") for p in L.evidence_files()]
    assert rels, "a scoped scan over a real change must find files"
    for rel in rels:
        assert "2026-10-04-archive-evidence-provenance" in rel or rel.startswith("docs/"), (
            f"scoped mode admits only the named change and docs/: {rel}"
        )

    monkeypatch.delenv("GATE_CHANGE", raising=False)
    wide = [str(p.relative_to(_REPO_ROOT)).replace("\\", "/") for p in L.evidence_files()]
    assert len(wide) > len(rels), (
        f"repo-wide mode must scan more than scoped mode: {len(wide)} vs {len(rels)}"
    )


def test_scoped_to_a_nonexistent_change_scans_nothing_and_says_so(
    monkeypatch, capsys
) -> None:
    """A gate pointed at a change that is not there must not report a green.

    Silently scanning zero files and printing OK is a pass that means "I looked at
    the wrong place" — `req-gov-7`'s `all([])` failure mode, reached by a
    different route.
    """
    monkeypatch.setenv("GATE_CHANGE", "no-such-change-2099-01-01-nope")
    rels = [str(p.relative_to(_REPO_ROOT)).replace("\\", "/") for p in L.evidence_files()]
    assert not any("no-such-change" in r for r in rels), (
        f"a missing change must contribute no files: {rels}"
    )
    out = capsys.readouterr().out
    assert "does not exist" in out, out
    assert "not a pass" in out, (
        f"the message must say the result is not a pass, got: {out}"
    )
