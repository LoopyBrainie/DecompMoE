## Context

`openspec/specs/wayfinder/spec.md` currently has 33 `**Source:**` fields; 6 are pure-change references (L525, L543, L558, L594, L609, L628) and 1 is a pure CLAUDE.md/test/archive reference (L678) — none of which contain the literal `wayfinder/tickets/` substring that `CLAUDE.md` §2 rule 3 and §3 mandate. The drift accumulated because `scripts/lint_no_dead_defensive.py` (the only archive-time gate) covers only dead-defensive try/except anti-patterns, not spec-field format. CLAUDE.md §3 already declares `lint gate exit=0` as the archive precondition (commit `19543eb`), so the fix is to add a second lint script under the same gate rather than redesign the archive flow.

The 6 pure-change lines have a real audit story to tell: each is downstream of an archived change (`fix-openspec-doc-bugs` Decision 2 / `fix-math-consistency-audit-2026-08` Decisions 2, 3, 6, 7) whose design genuinely replaced or refined what an earlier `wayfinder/tickets/A*.md` ticket had recorded. The honest fix is the `(historical, <original-value>; superseded by <change> Decision N)` annotation, modeled on the existing L251 precedent for the `1/128` → `1/(2·N_e)` threshold change. Forging a fake ticket link (e.g. assigning L525 → A6b-1 without reading A6b-1 to confirm it really did discuss CentroidDriver dual channels) would replicate the L251-style patch-trace the issue 1 audit flagged.

L678 is structurally different: its design origin is the `CLAUDE.md` §6 第 8 条 amendment (commits `bec147d` + `83a0503`), not any A* ticket. Forcing a ticket reference there would be dishonest; the design decision is to let the lint rule fail on L678 at archive time, which is an **intentional signal** that L678 belongs in a separate `governance` capability, not in `wayfinder`. Closing that signal is out of scope for this change (which is meta: it builds the gate, it does not itself close every existing violation).

## Goals / Non-Goals

**Goals:**
- Mechanically enforce `wayfinder/tickets/<ID>.md` substring on every `**Source:**` line in `openspec/specs/**/spec.md` at archive time.
- Provide an executable audit tool (`scripts/lint_no_source_field_drift.py`) that reports per-line violations, so a failed archive points to the exact offending file + line.
- Establish the `(historical, <original-value>; superseded by <change> Decision N)` annotation as the canonical format for tickets whose recorded value has been superseded.
- Preserve zero-exemption semantics: no per-line exemption table; the rule is content-based and survives spec edits.

**Non-Goals:**
- Refactoring L678 into a separate `openspec/specs/governance/spec.md` capability. That migration is a separate change; this change makes it possible (by enforcing the rule) but does not perform it.
- Forcing annotation text on every existing line — only the 6 confirmed pure-change lines are patched in this change. Future archived changes must comply at archive time.
- Modifying `scripts/lint_no_dead_defensive.py` or its `JUSTIFIED_EXEMPTIONS` registry (db14222). The new lint script is a separate file to avoid contaminating the line-number exemption semantics.
- Touching `wayfinder/tickets/*.md` files (would violate CLAUDE.md §6 第 6 条 "不要重写 wayfinder ticket 来调和 spec 与 ticket 不一致").

## Decisions

### Decision 1: Independent lint script, not a registration in `JUSTIFIED_EXEMPTIONS`

**Rationale**: `scripts/lint_no_dead_defensive.py` registers per-line exemptions in `JUSTIFIED_EXEMPTIONS: list[tuple[str, int, str]]` keyed by `(relpath, line_no, reason)`. Spec.md Source lines are markdown text, not code; keying by line number would drift every time spec.md is edited and silently grow the exemption table — the same chronic-rot pattern the current script only narrowly avoids because dead-defensive lines rarely move. A separate script with a pure-string substring rule has zero state to drift.

**Alternatives considered**:
- Adding `**Source:**` lines to `JUSTIFIED_EXEMPTIONS` — rejected (line-number drift rot).
- Merging into `lint_no_dead_defensive.py` as a second check function — rejected (semantic mismatch: dead-defensive is code anti-pattern, source-field is governance; co-locating would suggest equivalence and confuse future maintainers).
- Schema-level enforcement (`.openspec.yaml` template injecting required fields) — rejected (template lives in `openspec new change` CLI; the spec fields are hand-written in long-form markdown, template injection does not reach them).

### Decision 2: Pure string substring rule, not regex with anchor exceptions

**Rationale**: The rule is "every `**Source:**` line must contain the substring `wayfinder/tickets/`". A single regex with no lookarounds, no backrefs, and no per-line exemptions. The rule is content-based (substring search), so it survives line shifts, paragraph renumbering, and reflow.

**Alternatives considered**:
- Regex allowing `wayfinder/tickets/CLAUDE.md` as an exemption for governance-origin requirements — rejected (introduces a half-exemption; future abuse vector).
- Regex requiring `**Source:**` at line start + ticket path with strict shape — rejected (over-constrains; future extensions like multi-line Source blocks would need exemption).
- Allowing `(autonomous, post-2026-08-21)` annotation as a ticket-substitute — rejected (same exemption-by-stealth problem; the L678-intentional-failure mechanism is the clean signal).

### Decision 3: Per-line violation report, not aggregate count

**Rationale**: The lint output must include `file:line: <violating content>` for every failure, so an archive failure points to the exact location. An aggregate-only "N violations" output would force maintainers to grep themselves, defeating the purpose of an automated gate.

### Decision 4: L678 left as-is, not patched in this change

**Rationale**: L678 (Test Guard Precision for Closed-Form Numerical Claims) is the canary. Its design origin is `CLAUDE.md` §6 第 8 条 as amended by `bec147d` + `83a0503`. No A* ticket is its legitimate design predecessor. Patching it with a `(historical, ...)` annotation would be dishonest; the design intent of this change is that the lint rule **fail** on L678, signalling that it must migrate to a `governance` capability in a separate change. That signal is the gate working as intended.

**Alternatives considered**:
- Patching L678 with `wayfinder/tickets/A4-1.md` and a long annotation — rejected (false attribution; A4-1 is about β parameterization, not test precision).
- Special-casing L678 in the lint script — rejected (introduces the very exemption mechanism we are trying to avoid).
- Refactoring L678 into `openspec/specs/governance/spec.md` in this change — rejected (scope creep; out of issue 1's footprint; requires its own design and tasks).

### Decision 5: `(historical, <original-value>; superseded by <change> Decision N)` annotation syntax pinned

**Rationale**: L251 is the only existing precedent in the codebase (`(historical, threshold \`1/128\`)`) and it carries both the original value and a `superseded by` clause. Pinning the syntax to that precedent means future annotators have one template to follow, not three. The annotation MUST include the original value (not just a `historical` marker) so a reader can reconstruct the design history without leaving the spec.

## Risks / Trade-offs

- **L678 archive-time failure on this very change** — The wayfinder main spec carries L678 as-is. Any future `/opsx:archive` against `wayfinder` will trigger the lint failure on L678 until L678 migrates to `governance`. This is the intended signal, not a bug. → **Mitigation**: Document L678 in `tasks.md` §2.7 as the explicit "open migration debt" item for a follow-up change.

- **Archive-time gate could mask unintended spec edits** — A spec field could be silently removed or changed in a way that passes the substring check but breaks the annotation's honesty (e.g. updating `(historical, threshold \`1/64\`)` to `(historical, threshold \`1/128\`)` without re-auditing). → **Mitigation**: The lint checks substring presence, not annotation truthfulness. Annotation honesty remains a code-review responsibility, as it is today.

- **Exemption mechanism absence might be too rigid** — If a future legitimate use case requires a Source field without a ticket (e.g. a research-paper-only requirement), the rule will fail and the maintainer will have to either change the rule or add a ticket. → **Mitigation**: That friction is intentional. Adding a ticket is cheap; silently expanding the exemption mechanism is the failure mode this change is designed to prevent.

- **Two lint scripts instead of one** — Slightly higher overhead at archive time, and a maintainer touching gates has to update two files instead of one. → **Mitigation**: The scripts have disjoint domains (code anti-pattern vs spec-field format); combining them would conflate concerns. The `CLAUDE.md` §3 archive-precondition line will list both scripts by name.

- **No retroactive closure of all 7 current violations in this change** — This change patches 6 of 7 and signals L678 as intentional debt. A reviewer expecting "all violations closed" will see 1 remain. → **Mitigation**: `tasks.md` §2.7 explicitly names the L678 follow-up as out-of-scope for this change but in-scope for the gate.

## Migration Plan

1. Land this change (`fix-wayfinder-spec-source-field-drift`) with the lint script + 6 patched Source lines + CLAUDE.md wording micro-adjust. Archive step will trigger lint failure on L678; **the archive of this change's spec delta does not touch L678** (it modifies only the 6 lines listed in `tasks.md` §2.1–§2.6 and adds the new `Source Field Format Invariant` requirement).
2. Open a follow-up change (e.g. `migrate-l678-to-governance-capability`) to move L678 into `openspec/specs/governance/spec.md` and delete it from `openspec/specs/wayfinder/spec.md`. That change will pass the lint gate (governance capability's Source field can comply because it has its own design lineage).
3. Once step 2 lands, any future change to `wayfinder/spec.md` archives cleanly under the new lint rule.

**Rollback**: Removing the lint script and reverting the 6 Source-line patches is a single revert commit; the gate returns to its pre-change state (no source-field enforcement). No data migration; no API impact.

## Open Questions

None. The audit of the 6 patched lines is captured in `tasks.md` §2.1–§2.6 with explicit per-line ticket choices and annotation content. L678's intentional debt is captured in `tasks.md` §2.7.
