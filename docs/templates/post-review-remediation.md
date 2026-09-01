# Post-Review Remediation Commit Template

> Source of truth: commit `151697a` of `fix-math-consistency-audit-2026-08-apply`
> (archived as `2026-09-01-fix-math-consistency-audit-2026-08-apply`).
> Use this template when responding to a review findings list that contains
> both bug fixes and structural guard additions.

---

## Template Structure

```text
fix(post-review-N): <one-line summary>

Per <commit-hash> Re-Review findings (Bug #<id1>/#<id2>/...):

Bug #<id1> (<category> <description>):
  - Removed <anti-pattern> (<why it's broken in 1 sentence>)
  - Added EXPLICIT '<real guard>' (<why this is the right guard>)
  - <Old failure mode>: <before> -> <after>
  - <Old silent failure>: <silent result> -> now <explicit raise/error>

Bug #<id2> (...):
  - ...

...

 verified:
  - <command to verify> -> <actual output>

 try/excepts (<rationale for keeping>):
  - pi-lens '<dead-defensive>' lint flagged these as dead code
  - VERIFIED: <concrete test showing real exception> -> these are REAL
    <category>, not dead
  - Added '# noqa: dead-defensive' tags with justification comment

Bug #<idN> (<category> <description>):
  - Rewrote <what> to honestly describe <actual behavior>
  - <Old claim>: <docstring promise>
  - <New reality>: <what test actually does>
  - Acknowledged that <profiling/etc> is <limitation>; not worth chasing

Bug #<idN+1> (<category> <description>):
  - Reviewer was wrong: <misreading of X>
  - <Correct interpretation>: <what the rule actually says>
  - <ruff/lint check> passes; no change needed

New: scripts/<name>.py
  - <One-line purpose>
  - <Patterns detected>
  - <Noqa whitelist mechanism>
  - Run as <pre-commit hook / CI gate> to prevent <recurrence>

Stats:
  - Lint gate: <before> -> <after>
  - Tests: <pass count> passed (<regression status>)
  - <Silent failure path>: <closed/explicit>
```

---

## Why This Structure Works

### 1. Group by Bug ID, not by file

Each review finding gets its own block. Even if multiple bugs live in the
same file, separating them makes the diff-by-diff accountability obvious
and lets the reviewer cross-reference line-by-line.

### 2. Each Bug block follows: "Removed X / Added Y" + observable evidence

```text
Bug #11 (R_H dead catch):
  - Removed try/except around 'entropy / torch.log(tensor(n))'
    (PyTorch tensor div never raises; returns NaN/Inf silently)
  - Added EXPLICIT 'if n < 2: raise ValueError' input guard BEFORE
    the division (spec Req 20: R_H only valid for n >= 2)
```

This pattern answers four questions per finding:

- **What was wrong?** Removed code + reason
- **What's the right fix?** Added code + spec justification
- **What was the failure mode?** Before → after (observable)
- **Why this is the right guard?** Spec citation

### 3. Distinguish "real defensive code" from "dead defensive code"

```text
schedule.py try/excepts (lines 160, 171):
  - pi-lens 'dead-defensive' lint flagged these as dead code
  - VERIFIED: float(None) / float('abc') / float(object()) DO raise
    TypeError/ValueError -> these are REAL input validation, not dead
  - Added '# noqa: dead-defensive' tags with justification comment
```

When a linter disagrees with the human review, **show your work**. Run the
verification command and paste the output. This is the audit trail that
makes the commit message defensible at the next review.

### 4. Honest docstring rewrite, not silent divergence

```text
Bug #14 (test_complexity_budget docstring):
  - docstring previously claimed 'MAC count must match spec within 1%'
  - Implementation never measured MACs (just shape + spherical invariant)
  - Rewrote docstring to honestly describe what test does: closed-form
    value 33_040 + d_c/d_k scaling + actual extract_C invocation with
    shape + unit-sphere invariant checks
  - Acknowledged that MAC profiling is backend-dependent (CUDA kernel
    fusion can change observed MACs 2x); not worth chasing
```

If a docstring claims more than the implementation delivers, **fix the
docstring, not the test**. Lying in docstrings to make a weaker test
"pass" the spec is worse than acknowledging the gap.

### 5. Explicit dismissal of false-positive review findings

```text
Bug #15 (PEP 8 E303 in 9988f41):
  - Reviewer was wrong: E303 = 'too many blank lines' (not 'need 2')
  - 1 blank line between import and module-level code is E305 (correct)
  - ruff check passes; no change needed
```

When you disagree with a review finding, say so explicitly and cite the
authoritative source. Silently ignoring a finding without explanation
creates a re-review loop.

### 6. Stats line at the end (mandatory)

```text
Stats:
  - Lint gate: 3 violations -> 0 violations
  - Tests: 136 passed (no regression)
  - R_H silent NaN path: now explicit ValueError
```

The reviewer should be able to read the stats line and know:

- Did the gate they care about get better or worse?
- Did any tests regress?
- Did the silent-failure class get closed?

---

## Anti-Patterns to Avoid

### ❌ Single-bullet "fixed stuff" commit

```text
fix: review findings

- fixed some bugs
- updated tests
- cleaned up
```

This is a code smell: it groups multiple findings into one bullet,
provides no evidence, and leaves no audit trail.

### ❌ Verbose narrative commit

```text
fix: comprehensive post-review pass

The recent code review highlighted several issues with the
implementation of [feature]. After careful analysis and
consultation with the team, we determined that the best
course of action was to...
```

Front-load the actionable content. Narrative belongs in the PR
description, not the commit message.

### ❌ Suppressing review feedback with `# noqa` without justification

```text
return entropy / torch.log(torch.tensor(float(n)))  # noqa
```

Always explain *why* the suppression is justified, in the same line or
in the commit message. A bare `# noqa` without context is technical debt
that compounds.

---

## Verification Before Commit

Before writing the commit message, run:

```bash
# 1. Full test suite
uv run pytest tests/ -q

# 2. Lint gate (must be 0 violations)
uv run python scripts/lint_no_dead_defensive.py

# 3. Independent numerical re-audit (for spec-mandated values)
uv run python -c "..."
```

If any of these fail, the commit message shouldn't claim they pass.

---

## When NOT to Use This Template

- **Single-line trivial fix**: just use `fix: <one-line description>`
- **Refactor with no behavior change**: use `refactor: <description>`
- **New feature**: use `feat: <description>`
- **Review finding is a single bug**: a normal `fix: ...` commit is
  sufficient; the structured template is for **multi-finding remediation
  rounds**.

---

## Source of Truth

This template was extracted from commit `151697a` in response to
`opsx:fix-math-consistency-audit-2026-08-apply` review. If a future
post-review remediation commit produces a better structure, update this
file and link to the new exemplar.
