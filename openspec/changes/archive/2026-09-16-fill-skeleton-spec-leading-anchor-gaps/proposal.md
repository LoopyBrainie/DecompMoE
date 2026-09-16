## Why

`openspec/specs/decompmoe-skeleton/spec.md` ships **22 Requirements** but only the last **5** carry the leading anchor IDs (`<a id="req-N"></a>`) that cross-references and OpenSpec tooling rely on. The first 17 Requirements (L8–L331) are anchorless and therefore unlinkable, breaking parity with `openspec/specs/wayfinder/spec.md`, where every Requirement (33/33) has a leading anchor.

The previously listed fix `fix-skeleton-spec-anchor-placement-2026-09-15` described this work as "trailing → leading" — fact-checked in the prior turn and found inaccurate: the existing 5 anchors are already leading, and the line range (L363–L466) is off-by-L14 from the real anchor positions (L349, L385, L405, L430, L455). The true gap is missing anchors, not misplaced ones. This change is the corrected version of that fix.

## What Changes

- Insert one leading anchor `<a id="req-N"></a>` (followed by a blank line) immediately before each of the 17 anchorless `### Requirement:` headings in `openspec/specs/decompmoe-skeleton/spec.md`, covering Requirement headings at L8, L20, L36, L56, L64, L84, L100, L120, L136, L152, L176, L204, L264, L284, L300, L315, L331.
- The 5 existing anchors at L349, L385, L405, L430, L455 remain **unchanged** (already leading, already correct).
- No requirement text, scenario text, or `**Source:**` annotation is altered.

## Capabilities

### New Capabilities
<!-- None — anchor insertion is structural, not behavioral. -->

### Modified Capabilities
<!-- None — anchor insertion does not modify any requirement. The capability decompmoe-skeleton already exists with its 22 Requirements; we only add navigational anchors. skip_specs: true is set in .openspec.yaml. -->

## Impact

- `openspec/specs/decompmoe-skeleton/spec.md` — 17 new anchor lines (one blank line + `<a id="req-N"></a>` line per Requirement); file grows by ~17 lines.
- No code, API, dependency, or test changes.
- No behavioral change; anchors are navigational metadata only.
- Lint impact: passes `scripts/lint_no_dead_defensive.py` and `scripts/lint_no_source_field_drift.py` (no new symbols, no `Source:` field edits).
