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
from the archive that motivated this work and asserts the lint reports it.

**Where the discrimination actually lives, stated plainly.** Under the original
block-wide baseline scope, a *silent* assertion could not discriminate: a fixture
that passes under per-line scope also passes under block scope, because block scope
is strictly more permissive. Only a *reported* assertion can. So after D2 narrowed
the scope, the direction of the second half of that test flipped: the same evidence
with its revision moved to a later line must now be **reported**, and that assertion
is the discriminating one. The green case now only states the positive rule (a count
line carrying its own baseline is silent). Anyone reading only the green half is
reading the weaker half; the design rationale is in `design.md` D2 and the probe
table there is the one to check.
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
    """The motivating evidence must be reported, and silent only when baselined.

    Both directions matter. Red alone would be a lint that cannot pass; green alone
    would be a lint that cannot fire.
    """
    assert L.check_text(REAL_INSTANCE), (
        f"the verbatim incident sentence is a baseline-less count and MUST be "
        f"reported; if this fails the lint cannot detect the case that motivated "
        f"it, actual={L.check_text(REAL_INSTANCE)}"
    )

    # D2 narrowed the baseline scope from the block to the count's own line, so the
    # discriminating half of this test FLIPPED rather than staying green. The
    # original three-line fixture cannot stay silent under the new rule, and
    # keeping it silent would have meant keeping the defect. What is asserted here
    # is the direction that actually separates the two rules: the same figures,
    # with the revision on a later line, are now reported.
    baselined = (
        "It was caught by the **net count**: the ledger moved 65 → 67 where 65 + 3\n"
        "additions = 68, recorded at `ea802c8`; the intermediate state is not\n"
        "reconstructible from git."
    )
    assert L.check_text(baselined) != [], (
        f"a revision on a later line must no longer bless this paragraph's counts, "
        f"actual={L.check_text(baselined)}"
    )
    # The positive rule, stated in one line: a count carrying its own baseline is
    # silent. This half cannot discriminate old from new (block scope also passes),
    # which is why it is not the half doing the work above.
    green = (
        "It was caught by the **net count**: the ledger moved 65 → 67 where 65 + 3 "
        "additions = 68, recorded at `ea802c8`; the intermediate state is not "
        "reconstructible from git."
    )
    assert L.check_text(green) == [], (
        f"a revision named on the count's own line must silence the report, "
        f"actual={L.check_text(green)}"
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
        # D4 narrowed this marker from the bare substring `histor` to the word
        # `historical`, matched on an ASCII word boundary. The old form also
        # silenced `history` and `historian`; `test_exemptions_match_on_word_
        # boundaries_but_keep_cjk_substrings` now pins that those stay unsilenced.
        ("原值 36/decompmoe-skeleton 23 个，historical", "historical"),
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
        "historical",
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


def test_scope_follows_gate_change(monkeypatch, tmp_path) -> None:
    """`GATE_CHANGE` narrows the scan to one change, per req-gov-7's scoping rule.

    Without this, the gate's verdict is a function of every sibling change's
    in-flight edits — which is how a gate gets switched off, and how a green can
    be produced by somebody else's commit instead of by this change.

    The tree is SYNTHETIC. An earlier version of this test named a real,
    then-unarchived change and asserted the repo-wide scan saw strictly more.
    Both halves were a function of live repository state: archiving that change
    silently emptied the scoped scan, and archiving every sibling emptied the
    difference, so a routine archive turned this test red for a reason that had
    nothing to do with the lint. A scoping rule must be pinned by the fixture,
    not by whatever changes happen to be open this week.
    """
    changes = tmp_path / "changes"
    docs = tmp_path / "docs"
    (changes / "alpha-change").mkdir(parents=True)
    (changes / "beta-change").mkdir(parents=True)
    (changes / "archive" / "gone-change").mkdir(parents=True)
    docs.mkdir(parents=True)
    (changes / "alpha-change" / "proposal.md").write_text("alpha\n", encoding="utf-8")
    (changes / "beta-change" / "design.md").write_text("beta\n", encoding="utf-8")
    (changes / "archive" / "gone-change" / "proposal.md").write_text("old\n", encoding="utf-8")
    (docs / "kept.md").write_text("doc\n", encoding="utf-8")

    monkeypatch.setattr(L, "_CHANGES_DIR", changes)
    monkeypatch.setattr(L, "_ARCHIVE_DIR", changes / "archive")
    monkeypatch.setattr(L, "_DOCS_DIR", docs)

    monkeypatch.setenv("GATE_CHANGE", "alpha-change")
    rels = [p.relative_to(tmp_path).as_posix() for p in L.evidence_files()]
    assert rels, "a scoped scan over a real change must find files"
    for rel in rels:
        assert "alpha-change" in rel or rel.startswith("docs/"), (
            f"scoped mode admits only the named change and docs/: {rel}"
        )
    # The archive is excluded in BOTH modes (req-gov-5), so an archived change
    # must not sneak in through the repo-wide branch either.
    assert not any("gone-change" in r for r in rels), f"archive must stay excluded: {rels}"

    monkeypatch.delenv("GATE_CHANGE", raising=False)
    wide = [p.relative_to(tmp_path).as_posix() for p in L.evidence_files()]
    assert len(wide) > len(rels), (
        f"repo-wide mode must scan more than scoped mode: {len(wide)} vs {len(rels)}"
    )
    assert "changes/beta-change/design.md" in wide, (
        f"repo-wide mode must admit the sibling change: {wide}"
    )
    assert not any("gone-change" in r for r in wide), f"archive must stay excluded: {wide}"


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

# ---------------------------------------------------------------------------
# Change C (2026-10-07-lint-count-baseline-scope-and-gate-set-integrity)
# Each pattern change is asserted in BOTH directions: the defect is caught, and
# the neighbouring non-defect is not flagged. A one-sided test passes just as
# happily against a pattern that matches everything.
# ---------------------------------------------------------------------------


def test_ratio_pattern_ignores_prose_phase_enumeration() -> None:
    """D1: `Phase 2/3` enumerates two phases; it is not a ratio.

    This was the only false positive the pattern family produced, and it had
    already forced three prose workarounds (`34b445a` swapped the slash for an
    en-dash). The narrowing must be surgical: compact real ratios survive.
    """
    assert L._count_kinds("Phase 2/3") == [], (
        f"prose enumeration is not a ratio, actual={L._count_kinds('Phase 2/3')!r}"
    )
    assert L._count_kinds("Phase 2/3 ramp closure") == [], (
        f"prose enumeration mid-sentence, actual={L._count_kinds('Phase 2/3 ramp closure')!r}"
    )
    # A rejected alternative required whitespace around the slash and lost these.
    # `3/16 = 0.1875` is live prose in openspec/specs/wayfinder/spec.md.
    assert L._count_kinds("3/16 = 0.1875") == ["ratio"], (
        f"a compact real ratio must still fire, actual={L._count_kinds('3/16 = 0.1875')!r}"
    )
    assert L._count_kinds("2/3") == ["ratio"], (
        f"actual={L._count_kinds('2/3')!r}"
    )
    assert L._count_kinds("48 / loose 48") == ["paired counts"], (
        f"actual={L._count_kinds('48 / loose 48')!r}"
    )


def test_hex_only_english_words_confer_no_baseline() -> None:
    """D3: `defaced` and friends are prose, not commit hashes.

    Under the old `\\b[0-9a-f]{7,40}\\b` any paragraph containing one of these was
    treated as baselined and its real counts went unreported.
    """
    hash_re = next(
        r for r, (_, kind) in zip(L._BASELINE_RES, L.BASELINE_PATTERNS) if kind == "commit hash"
    )
    for word in ("defaced", "effaced", "feedbac"):
        assert hash_re.match(word) is None, (
            f"{word!r} is an English word, not a commit hash, actual match={bool(hash_re.match(word))}"
        )
    for h in ("82b84d6", "051f247", "f8e5b26d5a34fd7d2d276e80808cf2eaff143ac7", "abcdef1"):
        assert hash_re.match(h) is not None, (
            f"{h!r} must still read as a commit hash, actual match={bool(hash_re.match(h))}"
        )

    # End to end: the word must not silence a real count in its own paragraph.
    para = f"The history was defaced. We counted 3 条 defects."
    assert L.find_unbaselined_counts(para.splitlines()), (
        "a hex-only English word must not bless the paragraph's real counts"
    )
    para_ok = "The history was defaced. We counted 3 条 defects, see `82b84d6`."
    assert L.find_unbaselined_counts(para_ok.splitlines()) == [], (
        f"a real hash must still baseline it, actual={L.find_unbaselined_counts(para_ok.splitlines())!r}"
    )


def test_exemptions_match_on_word_boundaries_but_keep_cjk_substrings() -> None:
    """D4: the marker is the word `historical`, and CJK exemptions must survive.

    `\b` is an ASCII word boundary and CJK characters are word characters, so a
    uniform `\\b...\\b` over every marker would make `无法复算` unmatchable and kill
    every Chinese exemption. That regression is worse than the one being fixed,
    which is why the two classes take different code paths.
    """
    for word in ("histor", "history", "historian"):
        assert L.has_exemption(word) is False, (
            f"{word!r} merely starts with the marker letters, actual={L.has_exemption(word)!r}"
        )
    for phrase in ("historical", "pre-this-change", "superseded", "not reconstructible"):
        assert L.has_exemption(phrase) is True, (
            f"{phrase!r} must remain exempt, actual={L.has_exemption(phrase)!r}"
        )
    for cjk in ("无法复算", "不可复算", "待独立裁决", "不处置"):
        assert L.has_exemption(cjk) is True, (
            f"CJK exemption {cjk!r} must survive, actual={L.has_exemption(cjk)!r}"
        )
    # And end to end: a "history" sentence must not exempt a bare count.
    assert L.find_unbaselined_counts(["We reviewed history. We found 3 条 defects."]) != [], (
        "an unrelated 'history' must not exempt the paragraph"
    )


def test_one_baseline_no_longer_blesses_a_whole_paragraph() -> None:
    """D2: a baseline on the last line used to baseline every count above it.

    Coverage shrank as paragraphs grew longer, which is the inverse of what the
    lint exists to do. The count's own line must carry its own baseline.
    """
    spread = [
        "We saw 3 条 defects, 4 处 warnings, 5 次 retries, 6 个 outliers, 7 份 reports.",
        "Reproduce with `git rev-parse HEAD`.",
    ]
    assert L.find_unbaselined_counts(spread), (
        "a baseline on a neighbouring line must not bless these counts, "
        f"actual={L.find_unbaselined_counts(spread)!r}"
    )
    together = ["We saw 3 条 defects, reproducible via `git rev-parse HEAD`."]
    assert L.find_unbaselined_counts(together) == [], (
        f"a baseline on the count's own line must still work, "
        f"actual={L.find_unbaselined_counts(together)!r}"
    )
    bare = ["We saw 3 条 defects."]
    assert len(L.find_unbaselined_counts(bare)) == 1, (
        f"a bare count must still be reported, actual={L.find_unbaselined_counts(bare)!r}"
    )
    # Regression: the scope must be the count's OWN line, not the block start.
    # `_block_bounds` extends a block upward across every non-blank line, so in a
    # list the block start is the PREVIOUS item. An implementation that reads the
    # block start here tests a neighbour's baseline -- the same defect one level
    # in, and it was shipped once before this line was written.
    listed = [
        "- [ ] 4.1 found 3 条 defects, reproduce with `grep -c`",
        "- [ ] 4.2 found 4 条 warnings",
    ]
    assert len(L.find_unbaselined_counts(listed)) == 1, (
        f"a later list item must be judged on its own line, not its predecessor's "
        f"baseline, actual={L.find_unbaselined_counts(listed)!r}"
    )
    listed_ok = [
        "- [ ] 4.1 found 3 条 defects, reproduce with `grep -c`",
        "- [ ] 4.2 found 4 条 warnings, reproduce with `grep -c`",
    ]
    assert L.find_unbaselined_counts(listed_ok) == [], (
        f"each item's own baseline must silence it, "
        f"actual={L.find_unbaselined_counts(listed_ok)!r}"
    )


def test_table_row_still_accepts_a_baseline_named_in_its_header() -> None:
    """D2's table exception: the header is the legitimate place for a baseline.

    Carried over from `_block_bounds`'s prior rationale rather than from
    measurement -- both variants scored 943 on the archived corpus -- so it is
    pinned by a test rather than left to drift.
    """
    table = [
        "| phase | count, baselined by `git rev-parse HEAD` |",
        "| --- | --- |",
        "| 2 | 3 条 |",
        "| 3 | 4 条 |",
    ]
    assert L.find_unbaselined_counts(table) == [], (
        f"a table's header baseline must cover its rows, "
        f"actual={L.find_unbaselined_counts(table)!r}"
    )
    unbaselined = [
        "| phase | count |",
        "| --- | --- |",
        "| 2 | 3 条 |",
    ]
    assert len(L.find_unbaselined_counts(unbaselined)) == 1, (
        f"an unbaselined table must still be reported, "
        f"actual={L.find_unbaselined_counts(unbaselined)!r}"
    )


def test_baseline_scope_is_per_line() -> None:
    """Granularity is the line, not the individual count within it.

    Two counts on one line share that line's baseline, because a baseline is a
    line-level token; attributing it to individual counts inside the line would be
    arbitrary. The defect D2 removes is the *paragraph*, not the line. Pinned here
    so the granularity is stated rather than left to be inferred from a docstring —
    and so a future "make it per-count" edit has to come here and say why.
    """
    shared = ["We counted 3 条 defects and 4 处 warnings, both at `82b84d6`."]
    assert L.find_unbaselined_counts(shared) == [], (
        f"counts on one line share that line's baseline, "
        f"actual={L.find_unbaselined_counts(shared)!r}"
    )
    unbaselined = ["We counted 3 条 defects and 4 处 warnings with no baseline."]
    assert len(L.find_unbaselined_counts(unbaselined)) == 1, (
        f"one block, one finding even with two counts on the line, "
        f"actual={L.find_unbaselined_counts(unbaselined)!r}"
    )


def test_exemption_scope_stays_block_while_baselines_go_per_line() -> None:
    """The two scopes are deliberately asymmetric, and the asymmetry is the point.

    A baseline is a provenance token about a figure, so it must sit with the
    figure. An exemption is a sentence about recomputability and is routinely
    written next to the figure it qualifies. Measured over the archived corpus,
    174 of the exempted count-lines carry their marker on a *different* line, so
    narrowing exemptions too would red them for no defect. Both directions are
    pinned: moving a baseline down breaks it, moving an exemption down does not.
    """
    # Baseline moved to the next line: must be reported.
    baseline_moved = [
        "We counted 3 条 defects here.",
        "Reproduce with `git rev-parse HEAD`.",
    ]
    assert L.find_unbaselined_counts(baseline_moved), (
        f"a baseline on the next line must NOT silence this, "
        f"actual={L.find_unbaselined_counts(baseline_moved)!r}"
    )
    # Exemption moved to the next line: still exempt, by design.
    exemption_moved = [
        "We counted 3 条 defects here.",
        "The figure is not reconstructible from git.",
    ]
    assert L.find_unbaselined_counts(exemption_moved) == [], (
        f"an exemption in the adjacent sentence must still apply, "
        f"actual={L.find_unbaselined_counts(exemption_moved)!r}"
    )
    # And the same shape for a CJK marker, since the two marker classes already
    # take different matching paths.
    cjk_moved = ["We counted 3 条 defects here.", "该数字不可复算。"]
    assert L.find_unbaselined_counts(cjk_moved) == [], (
        f"a CJK exemption in the adjacent sentence must still apply, "
        f"actual={L.find_unbaselined_counts(cjk_moved)!r}"
    )


def test_report_quotes_the_line_that_actually_failed() -> None:
    """The reported line and the quoted text must be the same line.

    Pre-D2 they were the same by construction — a reported block had no baseline
    anywhere — so the report could name the block's first count line for free.
    They are not the same now, and quoting a line that visibly carries the
    baseline makes the lint look like it is contradicting itself in the one line
    the reader actually looks at.
    """
    lines = ["a 12% b 34% at `82b84d6`", "later 56% here"]
    findings = L.find_unbaselined_counts(lines)
    assert len(findings) == 1, f"actual={findings!r}"
    lineno, kind, quoted = findings[0]
    assert lineno == 2, (
        f"the failing line is 2, not the block's first count line; actual={findings!r}"
    )
    assert quoted == lines[1], (
        f"the quoted text must be the failing line's own text, actual={findings!r}"
    )
    assert "82b84d6" not in quoted, (
        f"quoting a line that carries the baseline reads as self-contradiction, "
        f"actual={findings!r}"
    )
    assert kind == "percentage", f"actual={findings!r}"
