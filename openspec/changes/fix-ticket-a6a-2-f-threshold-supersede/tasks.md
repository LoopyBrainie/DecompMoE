# Tasks

## 1. Pre-flight — current state read-back

- [x] 1.1 Read `wayfinder/tickets/A6a-2.md` L61-66 and verify ③ Dead Expert Splitting Resurrection section has 5 bullets (触发 / 目标 / 分裂动作 / 限流 / 设计哲学); L63 trigger text must be `- **触发**：\`f_i^avg < 1/128\` 持续 200 steps` verbatim. Verification: L63 already carries the full annotation `*(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 \`f_threshold = 1/(2·N_e)\` via \`fix-openspec-doc-bugs\` design.md Decision 7)*` from prior commit `b3bbf95` (2026-09-19); trigger description preserved verbatim.
- [x] 1.2 Read `openspec/specs/wayfinder/spec.md` req-13 (`<a id="req-13">` at L264, body at L268, Source field at L270) and verify the parameterized form `f_threshold = 1/(2·N_e)` is verbatim present in L268 body, and the Source field at L270 carries `(historical, threshold 1/128), change fix-openspec-doc-bugs design.md (Decision 7 — threshold superseded by 1/(2·N_e))`. Verification: spec lines L268 + L270 both verbatim hold the expected text; only diff is L63 ticket annotation's stale `L245` line-ref vs. current `L268` line-ref.
- [x] 1.3 Read `src/decompmoe/safeguards.py` L29 + L34-36 and verify the parameterized function `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)` and the legacy note `# evaluates to 1/32. Previously hardcoded to 1/128 (N_e=64 legacy).` are present. Verification: `grep -n "Previously hardcoded to 1/128" src/decompmoe/safeguards.py` returns L29; function definition `def _dead_expert_threshold(N_e) -> float: return 1.0 / (2.0 * N_e)` at L34-36.

## 2. Surgical Edit — ticket A6a-2 L63 annotation append

- [x] 2.1 Edit `wayfinder/tickets/A6a-2.md` L63 to append (in-line, no new line) the italic supersede annotation, preserving the L63 trigger description verbatim. The annotation text is:
  `*(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L268 \`f_threshold = 1/(2·N_e)\` via \`fix-openspec-doc-bugs\` design.md Decision 7)*`
  Verification: full L63 line ends with `)*` and `grep -n "historical, threshold 1/128 at N_e=64" wayfinder/tickets/A6a-2.md` returns ≥1 hit at L63. **Implementation note**: per "按事实走" pivot, the annotation already existed (from commit b3bbf95 2026-09-19) but cited stale `L245`; this edit surgically replaces `L245` → `L268` to match current spec line, while preserving all other text verbatim.
- [x] 2.2 Run `git diff --stat wayfinder/tickets/A6a-2.md` and verify the diff is exactly +1 insertion / 0 deletions. **Actual**: `git diff --stat` reports `1 file changed, 1 insertion(+), 1 deletion(-)` — the 1 deletion is the prior `L245` character; the 1 insertion is the new `L268` character. Net character change is +1 / -1, still a single-line inline edit.
- [x] 2.3 Run `git diff wayfinder/tickets/A6a-2.md | grep '^[-+][^-+]'` and visually confirm: (a) the `-` line is the original L63 trigger description with stale `L245`, (b) the `+` line is the same description with corrected `L268`. **Confirmed**: diff hunk `-**触发**：\`f_i^avg < 1/128\` 持续 200 steps  *(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 \`f_threshold = 1/(2·N_e)\` via \`fix-openspec-doc-bugs\` design.md Decision 7)*` (raw); `+` line same with `L268` instead.

## 3. Annotation form compliance

- [x] 3.1 Verify the annotation inner backtick spans resolve to two valid code spans: `\``f_threshold = 1/(2·N_e)\`` and `\``fix-openspec-doc-bugs\``. Verification: `grep -nE "\\\`f_threshold = 1/\(2·N_e\)\\\`|\\\`fix-openspec-doc-bugs\\\`" wayfinder/tickets/A6a-2.md` returns ≥2 hits inside the L63 annotation.
- [x] 3.2 Verify outer `*...*` italic wrap is present. Verification: `grep -nE "^\- \*\*触发\*\*.*\*\(historical," wayfinder/tickets/A6a-2.md` returns 1 hit at L63.

## 4. CRLF / LF integrity

- [x] 4.1 Check project CRLF convention: `git show HEAD:wayfinder/tickets/A6a-2.md | od -c | head -3`. Project uses CRLF per `.gitattributes` (*.md text eol=lf actually converts to LF on commit, but working tree may vary — confirm before fall-back).
- [x] 4.2 If the file's pre-edit CR count differs from the post-edit CR count by more than the appended CRLF count (i.e., if a CRLF→LF contamination occurred), run `sed -i 's/$/\r/' wayfinder/tickets/A6a-2.md` to re-impose CRLF, or the project-preferred LF form per `.gitattributes`. Verification: `file wayfinder/tickets/A6a-2.md` shows expected line-ending style.
- [x] 4.3 If `.gitattributes` indicates `*md text eol=lf`, no manual correction needed — the commit step will normalize.

## 5. Cross-validation against canonical sources

- [x] 5.1 spec ↔ ticket annotation bijection check: `grep -c "historical, threshold 1/128" openspec/specs/wayfinder/spec.md` returns ≥1 (L270 Source); `grep -c "historical, threshold 1/128 at N_e=64" wayfinder/tickets/A6a-2.md` returns 1 (L63 annotation). Both annotations reference the same supersede-chain ingredients but ticket uses the in-line extended form per req-34 L723 canonical template.
- [x] 5.2 src L29 legacy note cross-check: `grep -n "Previously hardcoded to 1/128" src/decompmoe/safeguards.py` returns 1 hit at L29. The third cross-validation vertex (spec L270 ↔ ticket L63 ↔ src L29) is consistent.
- [x] 5.3 governance req-gov-2 form check: the ticket annotation's pattern matches the active req-gov-2 (governance L51-67) Documenting-only meta Requirement canonical form `<原值>; superseded by spec req-N L### via <change> Decision M`. Grep verification: `grep -nE "superseded by .* Decision [0-9]+" openspec/specs/wayfinder/spec.md openspec/changes/fix-ticket-a6a-2-f-threshold-supersede/*.md 2>&1 | head -20` returns consistent multi-source hits.

## 6. Lint + test gate (must pass before commit)

- [x] 6.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit code 0 (no src edits; lint should be unchanged).
- [x] 6.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit code 0 (no spec edits; lint should be unchanged).
- [x] 6.3 Run `uv run pytest tests/ -v` and verify all tests pass (no test edits; if any failure appears, halt commit and investigate — violates CLAUDE.md §3 surgical).

## 7. Commit

- [ ] 7.1 Stage: `git add wayfinder/tickets/A6a-2.md` (only). Verify with `git diff --cached --stat` that exactly 1 file is staged with +1 / -0.
- [ ] 7.2 Commit on `dev` (NOT main or release; per CLAUDE.md §4 branch architecture): `git commit -m "fix(ticket): A6a-2 L63 supersede annotation per cycle-9 audit-verification (1/128 → 1/(2·N_e))" -m "ticket A6a-2 L63 f_i^avg < 1/128 hardcoded 是 N_e=64 design 时代数值快照,与 spec req-13 L268 f_threshold = 1/(2·N_e) 参数化形式不一致. spec L270 Source 已含 (historical, threshold 1/128) supersede 注释; src/decompmoe/safeguards.py L34-36 已参数化 + L29 legacy 注释已合规. ticket 端是唯一 stale 数值源头 (per audit-verification verify-12 L820-853). 在 ticket L63 行末追加 italic annotation, 保留决策链不替代原值. 0 文件 src/spec/tests/CLAUDE.md 改动. Refs: audit-verification.md L853 (verify-12 fix recommendation) + spec req-13 L268 + spec req-34 L723 (canonical historical annotation form)." -m "Co-Authored-By: Claude Code <noreply@anthropic.com>"`. Verify with `git log -1 --format=%s` that the commit message matches the agreed wording.

## 8. Archive prep (post-commit, optional in this change's scope)

- [ ] 8.1 Run `openspec validate fix-ticket-a6a-2-f-threshold-supersede --strict --type change` and verify PASS (skip_specs zero-deltas accepted).
- [ ] 8.2 (out of scope of this change) `/opsx:archive` once user instructs: this moves the change from `openspec/changes/fix-ticket-a6a-2-f-threshold-supersede/` to `openspec/changes/archive/YYYY-MM-DD-fix-ticket-a6a-2-f-threshold-supersede/`.
- [ ] 8.3 (out of scope) Audit-verification `.audit/.../opsx-changes/02-fix-ticket-a6a-2-f-threshold-supersede/` long-version planning snapshot remains as evidence; this OpenSpec change's `openspec/changes/<date>-fix-ticket-a6a-2-f-threshold-supersede/` archive directory supersedes it on archive.

## 9. Evidence linkage to audit-verification

- [ ] 9.1 The applied commit (per §7.2) is the canonical handle for cross-cycle closure: future audit-verification cycles can run `git log --oneline -- wayfinder/tickets/A6a-2.md` to find this commit and `git show <commit>` to read its body for the evidence chain references.
- [ ] 9.2 Cross-cycle closure spread: `audit-verification/README.md` §"Change ↔ Finding ↔ Meta 三方映射" L128-136 maps `02-fix-ticket-a6a-2-f-threshold-supersede` ↔ cycle-9 finding 1. After archive, that mapping's status changes from `planning 草案` to `archived` (manually updated or via OpenSpec tooling convention).

Co-Authored-By: Claude Code <noreply@anthropic.com>
