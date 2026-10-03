#!/usr/bin/env python3
"""Lint gate: detect OpenSpec Source fields that lack a per-capability reverse-link.

Background (per review of `openspec/changes/fix-wayfinder-spec-source-field-drift`
and `openspec/changes/migrate-l678-source`, extended by
`openspec/changes/tighten-source-field-format-lint-2026-09`):
    CLAUDE.md §2 rule 3 and §3 mandate that every `**Source:**` field in
    `openspec/specs/**/spec.md` carry a primary reverse-link to the spec's
    design lineage. The primary reverse-link is per-capability:
      - `openspec/specs/governance/spec.md` (governance-origin specs, whose
        lineage is `CLAUDE.md` amendments rather than wayfinder tickets):
        Source lines MUST contain the substring `CLAUDE.md`.
      - All other `openspec/specs/**/spec.md` (wayfinder-ticketed specs +
        decompmoe-skeleton + future peers that cite wayfinder tickets):
        Source lines MUST contain the substring `wayfinder/tickets/`.

    A `change <name> design.md (Decision N)` reference MAY appear additionally
    as a secondary link, but its presence does NOT substitute for the primary
    ticket / governance reverse-link.

This script greps OpenSpec spec files for `**Source:**` lines and rejects any
line that violates any of three independent structural checks:

  1. **Capability-aware substring presence** — the line MUST contain the
     per-capability required primary reverse-link substring.
  2. **Backtick wrapping** (NEW in `tighten-source-field-format-lint-2026-09`)
     — every occurrence of the required primary reverse-link substring MUST
     appear inside a backtick-delimited inline code span. A reverse-link
     that appears OUTSIDE a code span (e.g. `wayfinder/tickets/A6a-2.md` as
     bare text instead of `` `wayfinder/tickets/A6a-2.md` ``) is a violation
     regardless of substring presence.
  3. **Primary-first ordering** (NEW in `tighten-source-field-format-lint-2026-09`)
     — the first top-level item of the line (split by `,` or `;` at paren-
     depth 0, with code-span atomicity: a backtick toggles an atomic flag
     so a delimiter inside a code span does NOT split) MUST be a backtick-
     wrapped code span whose contents include the per-capability required
     primary reverse-link substring. A clause of the form
     ``change `<name>` design.md (Decision N)`` MAY NOT precede the primary
     reverse-link.

Anti-patterns flagged:
  1. `**Source:**` line in a wayfinder-lineage spec whose content does not contain the substring `wayfinder/tickets/`.
  2. `**Source:**` line in a governance-lineage spec whose content does not contain the substring `CLAUDE.md`.
  3. `**Source:**` line whose required reverse-link substring appears OUTSIDE a backtick code span.
  4. `**Source:**` line whose first top-level item is not the per-capability primary reverse-link.

Design constraints (per `openspec/changes/fix-wayfinder-spec-source-field-drift/design.md`,
extended by `openspec/changes/migrate-l678-source/design.md` Decision 3 and
`openspec/changes/tighten-source-field-format-lint-2026-09/design.md` Decisions 1-3):
  - Independent of `scripts/lint_no_dead_defensive.py` — disjoint file globs, no shared state, no shared imports.
  - NO exemption table (not `JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not env var, not CLI flag).
  - Content-based rule (substring + single-pass inline scan of code spans / paren depth) so the rule survives line shifts without chronic exemption-table rot.
  - Per-capability mapping is hardcoded as a small in-script table (NOT an exemption registry, NOT a CLI flag, NOT an env var) — same anti-pattern guardrails as the original rule. Adding a new governance-lineage capability is a script edit + L678-style follow-up change, not a runtime toggle.
  - The structural checks (backtick wrapping, primary-first ordering) are implemented as a hand-rolled single-pass tokenizer over a single `**Source:**` line — NO new dependency (no `mistune`, `markdown-it-py`, etc.; the project depends only on `torch` + `torchvision` and adding a Markdown parser for one lint script is not cost-effective).
  - Output goes to stdout (aligned with `lint_no_dead_defensive.py` convention).
  - Exit code 0 iff every `**Source:**` line satisfies all three structural checks; 1 otherwise.

Tokenizer limitations (documented per `tighten-source-field-format-lint-2026-09/design.md` Risks R1, R2):
  - Single-backtick code spans only; double-backtick (`` ``...`` ``) and backslash-escaped backticks are NOT supported. The live spec tree uses single-backtick exclusively.
  - Single-line Source fields only; a `**Source:**` line whose `,` or `;` split delimiters appear on subsequent lines will be reported as a violation rather than concatenated.

Run as a pre-commit gate or in CI:
    python scripts/lint_no_source_field_drift.py [PATH ...]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

SPECS_GLOB = "openspec/specs/**/spec.md"

# AC-81: the line-start anchor used to be `^\*\*Source:\*\*`, which a leading
# indent or a Markdown blockquote marker (`> `) bypasses completely -- such a
# line was invisible to every check below, so an indented `**Source:**` with a
# wrong reverse-link passed. The prefix class covers both, plus an optional
# ordered-list marker, since a Requirement body may legitimately be quoted or
# nested.
#
# Relaxing this is only safe because the body is now sliced by the *match end
# offset* rather than by a fixed length (see `lint_file`). Slicing
# `line[len("**Source:**"):]` would take 10 characters from the front of
# `> **Source:** ...` and produce the body `ource:** ...`, which then fails
# every check for the wrong reason.
#
# Measured on the tree at the time of the change: 0 lines are newly visible, so
# this closes a bypass without introducing a violation.
SOURCE_LINE_RE = re.compile(r"^[\s>]*(?:\d+\.\s*)?\*\*Source:\*\*")

# Per-capability Source reverse-link substring map (hardcoded — NOT an exemption table).
# Keys are paths (relative to repo root) of spec files whose Source lines use a non-default
# primary reverse-link. The default `DEFAULT_REQUIRED_SUBSTRING` (wayfinder ticket lineage)
# applies to every other spec path. Adding a new governance-lineage capability is a script
# edit + follow-up OpenSpec change, NOT a runtime toggle.
# Paths are derived from `_REPO_ROOT` (computed from `__file__`) at module load so the
# script remains correct if it is moved to a sub-directory under `scripts/`. The lookup
# uses suffix matching so callers passing either absolute (from `glob`) or relative (from
# CLI args with cwd at repo root) `path` values both resolve correctly.
def _repo_root() -> Path:
    """Return the repo root inferred from this script's location.

    `__file__` is at `scripts/lint_no_source_field_drift.py`; its parent's parent is the
    repo root. The same anchor is used by `collect_paths()` (which builds `SPECS_GLOB`
    matches from the same root), keeping the table key and the glob root in lock-step so
    both remain consistent if the script is relocated.
    """
    return Path(__file__).resolve().parent.parent


_REPO_ROOT = _repo_root()

# Per-capability paths derived from `_REPO_ROOT` (so the script is robust to relocation).
REQUIRED_SUBSTRING_BY_PATH_RELATIVE: dict[Path, str] = {
    _REPO_ROOT / "openspec" / "specs" / "governance" / "spec.md": "CLAUDE.md",
}

DEFAULT_REQUIRED_SUBSTRING = "wayfinder/tickets/"

# Form requirement per marker substring (AC-24 / wayfinder req-34).
#
# The marker (`DEFAULT_REQUIRED_SUBSTRING`) is a fixed-length needle, which is what
# checks ② (backtick wrapping) and ③ (primary-first ordering) are defined over. It is
# deliberately NOT changed to a regex: those two checks index into the body by
# `len(marker)`, so a pattern would silently change their semantics.
#
# The pattern below is the *form* that check ① additionally requires: the primary
# reverse-link must name a concrete file, not just the directory. Before AC-24 the
# bare directory form `wayfinder/tickets/` and the extension-less form
# `wayfinder/tickets/A4-1` were indistinguishable from the canonical
# `wayfinder/tickets/A4-1.md` at the gate, so an untraceable lineage could pass.
#
# `<ID>` matches the repository's actual ticket naming convention (23 files, e.g.
# `A0-1.md`, `A4-1.md`, `A6a-2.md`, `A6b-1.md`, `A8-3.md`).
#
# Keyed by the marker substring so there is exactly ONE source of truth for the
# per-capability requirement: a second parallel path table would be free to drift.
REQUIRED_FORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "wayfinder/tickets/": re.compile(r"wayfinder/tickets/[A-Za-z0-9]+-[0-9A-Za-z]+\.md"),
    "CLAUDE.md": re.compile(r"CLAUDE\.md"),
}

# Used when a capability marker has no entry in `REQUIRED_FORM_PATTERNS`. Defaults
# to the strict ticket form (the lineage-bearing default), never to the loose
# directory prefix: an unmapped capability must not be able to skip check ①.
DEFAULT_REQUIRED_FORM_PATTERN = REQUIRED_FORM_PATTERNS["wayfinder/tickets/"]


def _unbackticked_refs(body: str, required_substring: str) -> list[str]:
    """Return every occurrence of ``required_substring`` in ``body`` that lies OUTSIDE a backtick code span.

    Single-pass scan: the function tracks an ``in_code_span`` flag toggled by each
    backtick (when not already inside a code span). When ``in_code_span`` is False
    and ``required_substring`` appears as a contiguous substring of the
    not-yet-captured run, the substring is appended to the result list. The
    function returns substrings that are *contained within* ``required_substring``-bearing
    runs that started outside a code span; the exact match returned is the
    substring itself (so a caller can grep on the result and identify the
    offending location).

    Limitations (documented at module level): single-backtick code spans only;
    no double-backtick (``..``), no backslash-escaped backticks, no fence-
    delimited code blocks within the same line. The live spec tree uses single-
    backtick exclusively for Source-field reverse-links.

    Args:
        body: The line body (typically the substring after ``**Source:**``).
        required_substring: The per-capability primary reverse-link substring
            (e.g. ``wayfinder/tickets/`` or ``CLAUDE.md``).

    Returns:
        A list of occurrences (each equal to ``required_substring`` itself, one
        per unbackticked occurrence). Empty list means every occurrence of
        ``required_substring`` in ``body`` was backtick-wrapped (or there were
        no occurrences at all).
    """
    results: list[str] = []
    if not required_substring:
        return results
    in_code_span = False
    i = 0
    n = len(body)
    needle_len = len(required_substring)
    while i < n:
        ch = body[i]
        if ch == "`":
            in_code_span = not in_code_span
            i += 1
            continue
        if not in_code_span and body[i:i + needle_len] == required_substring:
            results.append(required_substring)
            i += needle_len
            continue
        i += 1
    return results


def _split_top_level_items(body: str) -> list[str]:
    """Split ``body`` by ``,`` or ``;`` at paren-depth 0, with code-span atomicity.

    The state machine maintains:
      - ``in_code_span`` (bool): toggled by each backtick when not already inside
        a code span. A delimiter character inside a code span does NOT act as
        a top-level separator.
      - ``paren_depth`` (int): incremented by ``(``, decremented by ``)``. A
        delimiter character inside parens does NOT act as a top-level separator.

    Delimiters: ``,`` and ``;``. (Semicolons are used in the governance Source
    field to separate ``CLAUDE.md`` lineage clauses from change-decision 反链.)
    The split is whitespace-stripped on each captured item.

    Limitations (documented at module level): single-backtick code spans only;
    no backslash-escape support; a delimiter inside ``(..)`` does not split, but
    a delimiter inside a code span does not split either.

    Args:
        body: The line body (typically the substring after ``**Source:**``).

    Returns:
        A list of items in original order; the first item is the "primary
        reverse-link container". Empty body returns ``[]``. A body with no
        delimiter returns a single-item list ``[body.strip()]``.
    """
    if not body.strip():
        return []
    items: list[str] = []
    buf: list[str] = []
    in_code_span = False
    paren_depth = 0
    for ch in body:
        if ch == "`":
            in_code_span = not in_code_span
            buf.append(ch)
            continue
        if not in_code_span and (ch == "("):
            paren_depth += 1
            buf.append(ch)
            continue
        if not in_code_span and (ch == ")"):
            paren_depth = max(paren_depth - 1, 0)
            buf.append(ch)
            continue
        if (ch == "," or ch == ";") and paren_depth == 0 and not in_code_span:
            items.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        items.append("".join(buf).strip())
    # Filter empty leading/trailing artifacts from leading delimiters, but
    # preserve any empty interior item (shouldn't happen in practice but the
    # state machine could produce it if body starts/ends with a delimiter).
    return [item for item in items if item]


def _first_code_span(item: str) -> str | None:
    """Return the first backtick-wrapped code span in ``item``, or None.

    Scans ``item`` left-to-right tracking the same ``in_code_span`` flag as
    ``_split_top_level_items``. The first captured span (between an opening
    backtick and its matching closing backtick) is returned. Returns ``None``
    if ``item`` has no code spans.

    Limitations: single-backtick spans only.
    """
    if "`" not in item:
        return None
    in_code_span = False
    start = -1
    for i, ch in enumerate(item):
        if ch == "`":
            if not in_code_span:
                in_code_span = True
                start = i + 1
            else:
                return item[start:i]
    return None


def _code_spans(body: str) -> list[str]:
    """Return every backtick-wrapped code span in ``body``, in order.

    Same tokenizer as `_first_code_span` and `_split_top_level_items`
    (single-backtick spans only, no backslash-escape support), but returns all
    spans instead of just the first. Used by check ① to test whether a required
    *form* occurs inside backticks, as opposed to check ② which tests whether
    the bare *marker* occurs outside them.

    An unterminated trailing backtick yields no span (the span is only emitted
    when its closing backtick is seen), so a malformed line cannot be credited
    with a form it never closed.
    """
    spans: list[str] = []
    in_code_span = False
    start = -1
    for i, ch in enumerate(body):
        if ch == "`":
            if not in_code_span:
                in_code_span = True
                start = i + 1
            else:
                spans.append(body[start:i])
                in_code_span = False
    return spans


def required_form_pattern_for(path: Path) -> re.Pattern[str]:
    """Return the reverse-link FORM pattern required for `path`.

    Resolves the per-capability marker via `required_substring_for(path)` and
    then looks the marker up in `REQUIRED_FORM_PATTERNS`. Deriving the pattern
    from the marker (rather than from a second path table) keeps the capability
    dispatch single-sourced: a new capability is added in exactly one place.

    Falls back to `DEFAULT_REQUIRED_FORM_PATTERN` for a marker with no explicit
    form, which keeps a hypothetical future capability from silently skipping
    check ①.
    """
    return REQUIRED_FORM_PATTERNS.get(
        required_substring_for(path), DEFAULT_REQUIRED_FORM_PATTERN
    )


def required_substring_for(path: Path) -> str:
    """Return the primary reverse-link substring required for `path`.

    Per-capability lookup against `REQUIRED_SUBSTRING_BY_PATH_RELATIVE`; falls back to
    `DEFAULT_REQUIRED_SUBSTRING` for paths not in the table (i.e., the
    wayfinder-ticket lineage default). Matches by suffix (the last N path components
    of the candidate `path` must match the last N path components of a table key) so
    the lookup is robust against whether `path` is absolute or relative, and against
    cwd differences.

    The input path is resolved to absolute via `Path.resolve()` first so relative
    CLI args (e.g. `openspec/specs/governance/spec.md`) and absolute paths from
    `collect_paths()` glob both compare against the table keys on equal terms. This
    also normalizes Windows backslash/forward-slash representations.
    """
    path = path.resolve()
    for k, v in REQUIRED_SUBSTRING_BY_PATH_RELATIVE.items():
        if len(path.parts) >= len(k.parts) and path.parts[-len(k.parts):] == k.parts:
            return v
    return DEFAULT_REQUIRED_SUBSTRING


def iter_source_lines(paths: Iterable[Path]) -> Iterator[tuple[Path, int, str]]:
    """Yield (path, line_number, line_content) for every `**Source:**` line in `paths`.

    `paths` is an iterable of file paths. Each path is read line-by-line; lines
    starting with `**Source:**` (no leading whitespace) are yielded with their
    1-based line number.
    """
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if SOURCE_LINE_RE.match(line):
                    yield path, line_no, line.rstrip("\n")


def lint_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of `(line_no, line_content, reason)` violations in `path`.

    A violation is a `**Source:**` line that fails any of three structural
    checks (per `openspec/changes/tighten-source-field-format-lint-2026-09/design.md`
    Decisions 1-3), where check 1 has two independent parts:

      1a. **Capability-aware marker presence**: the line MUST contain the
         per-capability required substring (`required_substring_for(path)`).
         Violation reason: ``"source field missing required reverse-link <required> for capability"``.
      1b. **Reverse-link form presence** (AC-24): at least one backtick-wrapped
         code span MUST match the per-capability FORM pattern
         (`required_form_pattern_for(path)`), i.e. name a concrete file
         (``wayfinder/tickets/<ID>.md``) rather than only the directory prefix.
         1a alone admitted the bare directory form and the extension-less form
         as passing, so an untraceable lineage cleared the gate. Violation
         reason: ``"source field reverse-link <required> must name a concrete
         file (expected a backtick-wrapped match for <pattern>)"``.
      2. **Backtick wrapping**: every occurrence of ``required`` MUST appear
         inside a backtick code span. Violation reason per occurrence:
         ``"unbackticked reverse-link: <required>"``.
      3. **Primary-first ordering**: the first top-level item of the line
         (split by ``,`` / ``;`` at paren-depth 0, code-span atomic) MUST be a
         backtick-wrapped code span whose contents include ``required``.
         Violation reason: ``"first item is not the primary reverse-link
         (first code span = <...>, required substring = <required>)"``.

    All four parts are independent: a line may fail 1b while passing 1a, 2 and 3
    (the bare directory form), or fail 1a while passing 1b (a well-formed
    reverse-link to the wrong capability).

    The returned tuples are sorted by `line_no`. Multiple violations per line
    are possible (each check is independent).
    """
    required = required_substring_for(path)
    form_pattern = required_form_pattern_for(path)
    missing_reason = f"source field missing required reverse-link {required!r} for capability"
    form_reason = (
        f"source field reverse-link {required!r} must name a concrete file "
        f"(expected a backtick-wrapped match for {form_pattern.pattern!r})"
    )
    violations: list[tuple[int, str, str]] = []
    for _, line_no, line in iter_source_lines([path]):
        # Strip the leading "**Source:**" marker to get the line body. The slice
        # starts at the regex match end, NOT at a fixed length: SOURCE_LINE_RE
        # now accepts an indent, a `>` quote marker, or an ordered-list marker
        # ahead of the field, and a fixed-length slice would cut the body in the
        # wrong place and report a violation for a correctly formed field.
        m = SOURCE_LINE_RE.match(line)
        if m is None:  # unreachable via iter_source_lines; guarded so a future
            # change to that generator cannot silently slice an unmatched line
            fail_here = f"internal: line {line_no} yielded without matching SOURCE_LINE_RE"
            violations.append((line_no, line, fail_here))
            continue
        body = line[m.end():].strip()
        # Check 1a: capability-aware marker presence.
        if required not in body:
            violations.append((line_no, line, missing_reason))
            continue  # Without the required substring, checks 1b, 2 and 3 are moot
                      # (they would either trivially pass on no occurrences or
                      # degenerate on an empty body).
        # Check 1b: reverse-link FORM presence. Independent of 1a/2/3 — the
        # directory prefix alone satisfies 1a and 2, so without this check the
        # bare `wayfinder/tickets/` form and the extension-less
        # `wayfinder/tickets/A4-1` form were indistinguishable from the
        # canonical `wayfinder/tickets/A4-1.md` at the gate (AC-24).
        if not any(form_pattern.search(span) for span in _code_spans(body)):
            violations.append((line_no, line, form_reason))
        # Check 2: backtick wrapping. Every occurrence of `required` must be
        # inside a backtick code span.
        for _occurrence in _unbackticked_refs(body, required):
            violations.append(
                (line_no, line, f"unbackticked reverse-link: {required!r}")
            )
        # Check 3: primary-first ordering. The first top-level item must be a
        # code span whose contents include `required`.
        items = _split_top_level_items(body)
        if not items:
            continue
        first_item = items[0]
        first_span = _first_code_span(first_item)
        if first_span is None or required not in first_span:
            violations.append(
                (
                    line_no,
                    line,
                    f"first item is not the primary reverse-link "
                    f"(first code span = {first_span!r}, required substring = {required!r})",
                )
            )
    return violations


# --- check ④: every Requirement carries a Source field -----------------------
#
# Checks ①a/①b/②/③ are *format* checks: they only ever look at lines that
# `iter_source_lines` already yielded. A Requirement with no `**Source:**` line
# at all therefore passed the gate silently — 20 of the 68 live Requirements
# were in that state at the time of this change.
#
# Those 20 are grandfathered rather than backfilled. Writing a lineage for them
# requires researching the design origin of each one, and a fabricated lineage
# is worse than an acknowledged gap: it would satisfy ①a while pointing at
# nothing. So the registry below is an explicit list of `(capability, anchor_id)`
# pairs, generated by measurement, and two things are enforced:
#
#   * a Requirement NOT in the registry and without a field is a violation, so
#     any newly authored one fails immediately;
#   * a registry entry whose Requirement no longer exists, or which now carries
#     a field, is itself a violation, so the registry cannot quietly outlive the
#     defect it was written to excuse.
#
# Re-generate with the measurement snippet in this change's `evidence/` after
# any backfill, and expect the count to shrink, never to grow silently.
SOURCE_EXEMPTIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("decompmoe-skeleton", "req-1"),  # Canonical Package And Version Identifier
        ("decompmoe-skeleton", "req-2"),  # Total And Active Parameter Estimator
        ("decompmoe-skeleton", "req-3"),  # Active FLOPs Parity Against Dense Baseline
        ("decompmoe-skeleton", "req-4"),  # Wire-Level Contracts
        ("decompmoe-skeleton", "req-5"),  # Inverse-Temperature Sigmoid With Gradient Bounds
        ("decompmoe-skeleton", "req-6"),  # Voronoi Self-Consistency Threshold
        ("decompmoe-skeleton", "req-7"),  # C Extraction Four-Step Pipeline
        ("decompmoe-skeleton", "req-8"),  # Isotropic Squared-Chord Distance And Logit
        ("decompmoe-skeleton", "req-9"),  # Top-K Sparse Mask With Local Softmax
        ("decompmoe-skeleton", "req-10"),  # Standard SwiGLU Expert With No Shared Branch
        ("decompmoe-skeleton", "req-11"),  # Loss Composition With Staged Lambda
        ("decompmoe-skeleton", "req-13"),  # Five-Phase Schedule State Machine
        ("decompmoe-skeleton", "req-14"),  # Six Visualization Module Protocol Stubs
        ("decompmoe-skeleton", "req-15"),  # Hard-Constraint Grep Invariants
        ("decompmoe-skeleton", "req-16"),  # Centroid Driver Semantic Invariants
        ("decompmoe-skeleton", "req-17"),  # Centroid Driver Invariant Test Scenarios
        ("decompmoe-skeleton", "req-19"),  # Spherical L2 Normalization Formula
        ("decompmoe-skeleton", "req-20"),  # Beta Parameterization Operational Domain
        ("decompmoe-skeleton", "req-22"),  # Eight Metrics And Classification
        ("wayfinder", "req-34"),  # Source Field Format Invariant for OpenSpec Specs
    }
)

_ANCHOR_LINE_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
_REQUIREMENT_HEADING_RE = re.compile(r"^### Requirement: (.+)$")


def requirement_blocks(lines: list[str]) -> list[tuple[int, str, str, bool]]:
    """Return `(line_no, anchor_id, title, has_source_field)` per Requirement.

    Uses the same block-start rule as `scripts/run_gates.py`: an anchor line
    introduces a Requirement only when the first non-empty line after it is a
    `### Requirement:` heading. A bare anchor followed by prose is an inline
    mention, and a section sub-anchor followed by `#### Scenario:` is a section
    header — counting either as a Requirement would produce phantom violations.
    """
    starts: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        m = _ANCHOR_LINE_RE.match(line.strip())
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and (rm := _REQUIREMENT_HEADING_RE.match(lines[j])):
            starts.append((i, m.group(1), rm.group(1)))

    out: list[tuple[int, str, str, bool]] = []
    for idx, (start, anchor_id, title) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        has_source = any(SOURCE_LINE_RE.match(l) for l in lines[start:end])
        out.append((start + 1, anchor_id, title, has_source))
    return out


def check_source_presence(path: Path, capability: str | None = None) -> list[str]:
    """Report Requirements in THIS FILE with no `**Source:**` field.

    Also reports a registry entry whose Requirement has since gained a field --
    that condition is per-file and can be decided from this file alone.

    "An entry names a Requirement that no longer exists" is deliberately NOT
    checked here: that is a whole-capability question, and a per-file check
    cannot answer it without reporting every other entry as stale the moment
    anyone runs against a single file. See `check_registry_stale`.

    `capability` defaults to the spec's parent directory name, which is the
    capability name for every path under `openspec/specs/<capability>/`.
    """
    cap = capability if capability is not None else path.parent.name
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = requirement_blocks(lines)
    if not blocks:
        return [f"{cap}: no Requirement blocks parsed from {path} -- check the file"]

    problems: list[str] = []
    for line_no, anchor_id, title, has_source in blocks:
        if has_source:
            if (cap, anchor_id) in SOURCE_EXEMPTIONS:
                problems.append(
                    f"stale SOURCE_EXEMPTIONS entry: {cap}/{anchor_id} now carries a "
                    f"**Source:** field -- prune the registry"
                )
            continue
        if (cap, anchor_id) in SOURCE_EXEMPTIONS:
            continue
        problems.append(
            f"{cap} L{line_no}: Requirement {title!r} has no top-level **Source:** "
            f"field (anchor {anchor_id})"
        )
    return problems


def check_registry_stale(specs_dir: Path) -> list[str]:
    """Report registry entries whose Requirement no longer exists in the tree.

    Whole-tree check, because "no longer exists" is only decidable against the
    complete spec for a capability. Also reports an entry for a capability that
    has no spec file at all, which would otherwise exempt nothing while looking
    legitimate in the source.
    """
    problems: list[str] = []
    by_capability: dict[str, set[str]] = {}
    for spec in sorted(specs_dir.glob("*/spec.md")):
        cap = spec.parent.name
        blocks = requirement_blocks(spec.read_text(encoding="utf-8").splitlines())
        by_capability[cap] = {anchor_id for _, anchor_id, _, _ in blocks}

    for cap, anchor_id in sorted(SOURCE_EXEMPTIONS):
        if cap not in by_capability:
            problems.append(
                f"stale SOURCE_EXEMPTIONS entry: {cap}/{anchor_id} -- no spec file "
                f"for capability {cap!r} under {specs_dir}"
            )
        elif anchor_id not in by_capability[cap]:
            problems.append(
                f"stale SOURCE_EXEMPTIONS entry: {cap}/{anchor_id} no longer exists"
            )
    return problems


def collect_paths(args: list[str]) -> list[Path]:
    """Resolve CLI positional args to a list of spec files.

    If `args` is empty, walk `SPECS_GLOB` from the repo root (parent of `scripts/`).
    If `args` is non-empty, treat each as a file path. Directories are NOT
    recursively walked — pass explicit files.
    """
    if args:
        return [Path(a) for a in args]
    repo_root = Path(__file__).resolve().parent.parent
    return sorted(repo_root.glob(SPECS_GLOB))


def main(argv: list[str] | None = None) -> int:
    """Walk spec files, print per-line violations to stdout, return exit code.

    Exit code is `1` if any violation exists, `0` otherwise. Output format
    per violation is `{path}:{line_no}: {reason}: {content}`, matching the
    `lint_no_dead_defensive.py` per-line convention.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    paths = collect_paths(args)

    all_violations: list[tuple[Path, int, str, str]] = []
    for path in paths:
        for line_no, content, reason in lint_file(path):
            all_violations.append((path, line_no, content, reason))

    # Check ④ is per-file rather than per-line, so it is reported through the
    # same list with no line number. Keeping one output path means the caller
    # has a single thing to read, and the exit code stays the same.
    presence_problems: list[tuple[Path, str]] = []
    for path in paths:
        for msg in check_source_presence(path):
            presence_problems.append((path, msg))
    # The "entry names a Requirement that no longer exists" half is a
    # whole-tree question, so it is answered once against the specs directory
    # rather than per file.
    specs_dir = Path(__file__).resolve().parent.parent / "openspec" / "specs"
    if specs_dir.is_dir():
        for msg in check_registry_stale(specs_dir):
            presence_problems.append((specs_dir, msg))

    if not all_violations and not presence_problems:
        exempt_note = ""
        if SOURCE_EXEMPTIONS:
            exempt_note = f", {len(SOURCE_EXEMPTIONS)} grandfathered absence(s)"
        print(
            f"lint_no_source_field_drift: OK ({len(paths)} file(s) scanned, "
            f"no violations{exempt_note})"
        )
        return 0

    total = len(all_violations) + len(presence_problems)
    print(f"lint_no_source_field_drift: {total} violation(s) found")
    print()
    for path, line_no, content, reason in all_violations:
        print(f"  {path}:{line_no}: {reason}")
        print(f"    {content}")
    for path, msg in presence_problems:
        print(f"  {path}: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
