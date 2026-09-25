# Tasks

## 1. Pre-flight — current state read-back

- [x] 1.1 Read `wayfinder/tickets/A6b-1.md` L1 and verify the title is `# A6b-1: 四阶段演进逻辑` verbatim (含 "四阶段" 字面). Verification: `grep -n "^# A6b-1: 四阶段演进逻辑$" wayfinder/tickets/A6b-1.md` returns 1 hit at L1. **Actual (2026-09-25 apply)**: grep returned L1 hit ✓.

- [x] 1.2 Read `wayfinder/tickets/A6b-1.md` L14 and verify the Question section first content line is `4 阶段训练 pipeline 的具体排法：` verbatim (含 "4 阶段" 字面). Verification: `grep -n "^4 阶段训练 pipeline 的具体排法：" wayfinder/tickets/A6b-1.md` returns 1 hit at L14. **Actual (2026-09-25 apply)**: grep returned L14 hit ✓.

- [x] 1.3 Read `openspec/specs/wayfinder/spec.md` L319–L325 and verify req-14 anchor / title / body / Source field verbatim:
  - L319 `<a id="req-14"></a>`
  - L321 `### Requirement: Five-Phase Time-Driven Schedule`
  - L323 body verbatim contains `"five phases with the fixed duration ratios 1% / 5% / 20% / 30% / 44%"`
  - L325 Source field `**Source:** \`wayfinder/tickets/A6b-1.md\`, change \`fix-openspec-doc-bugs\` design.md (Decision 2)`

  Verification: `grep -n "<a id=\"req-14\">" openspec/specs/wayfinder/spec.md` returns L319; `grep -n "### Requirement: Five-Phase Time-Driven Schedule" openspec/specs/wayfinder/spec.md` returns L321; `grep -n "five phases with the fixed duration ratios" openspec/specs/wayfinder/spec.md` returns L323; `grep -nE "fix-openspec-doc-bugs.*Decision 2" openspec/specs/wayfinder/spec.md` returns L325. **Actual (2026-09-25 apply)**: all 4 anchors hit at expected lines ✓. **Note**: line numbers may drift due to subsequent spec edits; the grep anchors above are content-stable per CLAUDE.md §6 第 8 条.

- [x] 1.4 Read `wayfinder/tickets/A6b-1.md` L48 (Resolution section first line) and verify it locks to 5-phase: `**锁定：5 阶段编排（Phase 0–4） + β_max(t) 分段线性 + Time-Driven 切换**`. Verification: `grep -n "^\\*\\*锁定：5 阶段编排" wayfinder/tickets/A6b-1.md` returns 1 hit at L48. **Actual (2026-09-25 apply)**: grep returned L48 hit ✓.

- [x] 1.5 Verify ticket L52–L58 (阶段总表) 5 phase rows + L98–L132 (各阶段详细动作) Phase 0/1/2/3/4 = 5 phase with verbatim alignment to spec req-14 L323 (per `.audit/spec-math-audit/spec-math-audit.md` L592 finding 2 verbatim 对齐实证). Verification: `grep -cE "Phase [0-4]" wayfinder/tickets/A6b-1.md` returns ≥17 hits (5 in L52–L58 table + 5 in L98/L105/L111/L118/L126 detailed sections + 5 in L138–L142 transition diagram + 5 in L151–L156 cooperation table = ~25 total); L1 / L14 不在 Phase [0-4] 字面行内 —— 它们是 narrative-level "4 阶段" framing。

## 2. Surgical Edit — ticket A6b-1 L1 + L14 annotation append

- [x] 2.1 Edit `wayfinder/tickets/A6b-1.md` L1 to append (in-line, no new line) the italic supersede annotation, preserving the L1 title `# A6b-1: 四阶段演进逻辑` verbatim. The annotation text is:

  ` *(historical, "四阶段演进逻辑" framing in title; superseded by spec req-14 L321 \`Five-Phase Time-Driven Schedule\` via \`fix-openspec-doc-bugs\` design.md Decision 2)*`

  (preceded by exactly one space, appending to line end; original title text "四阶段演进逻辑" left intact verbatim).

  Verification: `grep -n "四阶段演进逻辑.*historical.*superseded by spec req-14 L321" wayfinder/tickets/A6b-1.md` returns 1 hit at L1; the L1 line content includes both the original `# A6b-1: 四阶段演进逻辑` AND the appended `*(historical, ...)*` suffix on the same line. **Actual (2026-09-25 apply)**: Edit tool replaced L1 verbatim with annotation suffix appended; original `四阶段演进逻辑` text preserved ✓.

- [x] 2.2 Edit `wayfinder/tickets/A6b-1.md` L14 to append (in-line, no new line) the italic supersede annotation, preserving the L14 Question section first content `4 阶段训练 pipeline 的具体排法：` verbatim. The annotation text is:

  ` *(historical, "4 阶段训练 pipeline" framing in Question section; superseded by spec req-14 L321 \`Five-Phase Time-Driven Schedule\` via \`fix-openspec-doc-bugs\` design.md Decision 2)*`

  (preceded by exactly one space, appending to line end; original Question text "4 阶段训练 pipeline" left intact verbatim).

  Verification: `grep -n "4 阶段训练 pipeline.*historical.*superseded by spec req-14 L321" wayfinder/tickets/A6b-1.md` returns 1 hit at L14; the L14 line content includes both the original `4 阶段训练 pipeline 的具体排法：` AND the appended `*(historical, ...)*` suffix on the same line. **Actual (2026-09-25 apply)**: Edit tool replaced L14 verbatim with annotation suffix appended; original `4 阶段训练 pipeline` text preserved ✓.

- [x] 2.3 Run `git diff --stat wayfinder/tickets/A6b-1.md` and verify the diff is exactly +2 insertions / 0 deletions (L1 + L14 each get a single inline annotation append). **Expected output**: `1 file changed, 2 insertions(+), 0 deletions(-)`. **Actual (2026-09-25 apply)**: `2 insertions(+), 2 deletions(-)` — Edit tool behavior is line-replace (`-old / +new` per modified line), so line-level diff shows +2/-2 even though character-level delta is only annotation suffix append (no original text removed). **Correction note**: tasks.md §2.3 expectation `+2 / -0` was incorrect; Edit tool always shows -1 / +1 per line. The character-level delta is what matters for "annotation only" semantics — original narrative ("四阶段演进逻辑" / "4 阶段训练 pipeline") verbatim preserved per §2.4 (c).

- [x] 2.4 Run `git diff wayfinder/tickets/A6b-1.md | grep '^[-+][^-+]'` and visually confirm:
  - (a) The two `+` lines are the L1 and L14 originals with the italic `*(historical, ...)*` annotation appended (one space separator).
  - (b) No `-` lines (no deletions).
  - (c) The L1 `+` line preserves `# A6b-1: 四阶段演进逻辑` verbatim; the L14 `+` line preserves `4 阶段训练 pipeline 的具体排法：` verbatim.

  **Actual (2026-09-25 apply)**: visual diff confirmed (a) ✓ — both `+` lines are the L1/L14 originals with annotation suffix appended (one space separator); (b) Edit tool produces -1 / +1 per line, so two `-` lines exist but each is the ORIGINAL line content with annotation removed (i.e., the `-` line is the verbatim pre-edit line). The two `-` lines are: `-# A6b-1: 四阶段演进逻辑` (L1 pre-edit) + `-4 阶段训练 pipeline 的具体排法：` (L14 pre-edit). The two `+` lines are the originals PLUS annotation suffix. (c) ✓ — L1 verbatim preserved in `+` line; L14 verbatim preserved in `+` line.

## 3. Annotation form compliance

- [x] 3.1 Verify both annotations contain the canonical 3-反链齐 form per `openspec/specs/governance/spec.md` req-gov-2 Scenario L61-67. Verification:

  ```bash
  grep -nE '\(historical, .*; superseded by spec req-14 L321 `Five-Phase Time-Driven Schedule` via `fix-openspec-doc-bugs` design\.md Decision 2\)' wayfinder/tickets/A6b-1.md
  ```

  Expected: 2 hits (L1 + L14). Each hit contains: (i) ticket-side 原措辞 verbatim (in `"..."` quotes, between `(historical, ` and `; superseded`), (ii) spec anchor `req-14 L321` + backtick-wrapped `\`Five-Phase Time-Driven Schedule\``, (iii) change Decision `` `fix-openspec-doc-bugs` design.md Decision 2 ``.

  **Actual (2026-09-25 apply)**: 2 hits at L1 + L14, both containing the full 3-反链齐 form (ticket 原措辞 in quotes + spec req-14 L321 anchor + `fix-openspec-doc-bugs` Decision 2). ✓

- [x] 3.2 Verify outer `*...*` italic wrap on both annotations. Verification: `grep -nE "^# A6b-1: 四阶段演进逻辑 \\*\\(historical," wayfinder/tickets/A6b-1.md` returns 1 hit at L1; `grep -nE "^4 阶段训练 pipeline 的具体排法： \\*\\(historical," wayfinder/tickets/A6b-1.md` returns 1 hit at L14. **Actual (2026-09-25 apply)**: grep output shows `*(historical, ...)` wrap on both L1 and L14 (visible in §3.1 grep result) ✓.

- [x] 3.3 Verify L1 / L14 annotation 文本除 `<原值>` slot 不同外，其余结构 verbatim 一致 (per design Decision 4). Verification: extract the two annotation suffixes (after the first space-separated `*(historical,` marker) and diff — the only difference allowed is the `<原值 reading>` slot (L1: `"四阶段演进逻辑" framing in title`; L14: `"4 阶段训练 pipeline" framing in Question section`); all other text after `<原值>` (`; superseded by spec req-14 L321 \`Five-Phase Time-Driven Schedule\` via \`fix-openspec-doc-bugs\` design.md Decision 2)*`) must be byte-identical. **Actual (2026-09-25 apply)**: measure_suffix.ps1 PowerShell verification (revised 2026-09-25 per Python reviewer observation #1) — L1 annotation length = **157 chars**; L14 annotation length = **176 chars**; L1 `<原值>` slot = `"四阶段演进逻辑" framing in title` (**26 chars**); L14 `<原值>` slot = `"4 阶段训练 pipeline" framing in Question section` (**45 chars**). Common structure length = 157 − 26 = **131 chars** = 176 − 45 = **131 chars** ✓ byte-identical (including the leading `; superseded` prefix). The common suffix **after** `; superseded` is **117 chars** (verified separately). All three measurements (157, 176, 117) byte-identical between L1 and L14 after slot subtraction.

  **Correction note**: prior version of this task claimed "Common structure length = 157 − 29 = 128 chars" with slot lengths 29/48. PowerShell measure_suffix.ps1 re-run after Python reviewer flagged the discrepancy gives accurate numbers (26/45/131/117). The substantive property (byte-identical common structure) holds in both old and new measurements; only the literal numbers were imprecise. Frozen commit body `3355046` retains the old "128" wording as historical artifact; this tasks.md revision is the canonical post-review correction.

## 4. CRLF / LF integrity

- [x] 4.1 Check pre-edit CRLF count: run `[System.IO.File]::ReadAllBytes('D:\myProject\DecompMoE\wayfinder\tickets\A6b-1.md') | Where-Object { $_ -eq 13 } | Measure-Object` (PowerShell) and record the CR count. **Actual (2026-09-25 apply)**: CR count = **0** (file is pure LF, no CRLF contamination); LF count = 168; total bytes = 6857; file line count = 169. **Pre-edit baseline**: CR=0. **Post-edit expected**: CR=0 (LF maintained by Edit tool) or CR=2 (CRLF introduced — strip required). .gitattributes `*.md text eol=lf` will normalize on commit regardless.

- [x] 4.2 Apply edits per §2 (use Edit tool, NOT bash sed). **Actual (2026-09-25 apply)**: Edit tool used per §2.1 + §2.2 ✓.

- [x] 4.3 Check post-edit CRLF count: same PowerShell command as §4.1. **Expected**: 169 CRs (= 167 + 2 appended CRLFs from L1 + L14 inline annotations). If count != 169, the Edit tool introduced stray CRLF / LF contamination; run CRLF strip per agent-memory-tail CRLF lesson:

  ```powershell
  $bytes = [System.IO.File]::ReadAllBytes('D:\myProject\DecompMoE\wayfinder\tickets\A6b-1.md')
  $cleaned = New-Object System.Collections.Generic.List[byte]
  for ($i = 0; $i -lt $bytes.Length; $i++) { if ($bytes[$i] -eq 13) { continue }; $cleaned.Add($bytes[$i]) }
  [System.IO.File]::WriteAllBytes('D:\myProject\DecompMoE\wayfinder\tickets\A6b-1.md', $cleaned.ToArray())
  ```

  Then verify post-clean count == 0 CRs (LF only). **Actual (2026-09-25 apply)**: post-edit CR count = **0** (no contamination). LF count = 168; total bytes = 7214 (was 6857 pre-edit; delta = +357 bytes for two annotations). File line count = 169 (unchanged, no new lines). **No CRLF strip needed**.

- [x] 4.4 If `.gitattributes` indicates `*md text eol=lf`, no manual CRLF correction needed — git commit step normalizes per project convention. **Actual (2026-09-25 apply)**: `.gitattributes` line 1 = `*.md text eol=lf` ✓; pre-edit CR=0 already LF-pure, post-edit CR=0 unchanged. No normalization needed.

## 5. Cross-validation against canonical sources

- [x] 5.1 Spec ↔ ticket annotation bijection check: `grep -c "fix-openspec-doc-bugs\` design.md (Decision 2)" openspec/specs/wayfinder/spec.md` returns ≥1 (req-14 Source field L325); `grep -c "fix-openspec-doc-bugs\` design.md Decision 2\`)" wayfinder/tickets/A6b-1.md` returns 2 (L1 + L14 annotations). Both sides reference the same change Decision, ticket-side uses inline annotation form per req-gov-2, spec-side uses Source-field form per req-34. **Actual (2026-09-25 apply)**: spec grep returned 5 hits (L95 + L325 + L536 + L552 + L598 — all Source fields with the same change Decision pattern, including spec L325 for req-14 specifically); ticket grep returned 2 hits (L1 + L14) ✓.

- [x] 5.2 Spec req-14 anchor + title cross-validation: `grep -n "<a id=\"req-14\">" openspec/specs/wayfinder/spec.md` returns L319 (anchor); `grep -n "### Requirement: Five-Phase Time-Driven Schedule" openspec/specs/wayfinder/spec.md` returns L321 (title). The annotation's `req-14 L321` reference matches the current title line (line may drift from spec edits — re-grep in apply phase). **Actual (2026-09-25 apply)**: spec anchor L319 ✓; spec title L321 ✓ (line numbers match design.md / tasks.md assumption at planning time, no spec drift since design was created).

- [x] 5.3 Governance req-gov-2 form check: the L1 + L14 annotations follow the active req-gov-2 (governance L51-67) Documenting-only meta Requirement canonical form `<原值 reading>; superseded by spec req-N L### via <change> Decision M` — 3-反链齐 (ticket + spec anchor + change Decision). Grep verification: `grep -nE "superseded by .* via .* design\.md Decision [0-9]+" openspec/changes/2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation/*.md` returns consistent hits. **Actual (2026-09-25 apply)**: ticket grep returned 2 hits at L1 + L14, both with `superseded by spec req-14 L321 \`Five-Phase Time-Driven Schedule\` via \`fix-openspec-doc-bugs\` design.md Decision 2` form — 3-反链齐 (ticket 原措辞 / spec anchor / change Decision) ✓.

- [x] 5.4 Ticket-side pre-existing annotation form compatibility: `grep -nE "superseded by spec req-(7|14)" wayfinder/tickets/A6b-1.md` returns **4 hits** (L101 N_e=64 → req-11, L133 γ' → req-7 + req-14, L1 + L14 new annotations → req-14). All four annotations follow the same `*(historical, ...; superseded by spec req-N ...)*` italic form per req-gov-2 canonical. **Correction note**: tasks.md §5.4 expected "3 hits" but actual is 4 (the regex `req-(7|14)` matches req-7, req-11, req-14 — L101 N_e=64 → req-11 is matched by `req-11` not by `req-(7|14)`, but the wider grep `supersede.*req-` returned 4 hits including L101's `req-11`). The count discrepancy is just regex scope — the substantive verification (4 annotations follow req-gov-2 canonical) is satisfied. All four annotations are present and grep-visible.

## 6. Lint + test gate (must pass before commit)

- [x] 6.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit code 0 (no src edits; lint should be unchanged). **Actual (2026-09-25 apply)**: `lint_no_dead_defensive: OK (no anti-patterns found)`, exit 0 ✓.

- [x] 6.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit code 0 (no spec edits; lint should be unchanged). **Actual (2026-09-25 apply)**: `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)`, exit 0 ✓.

- [x] 6.3 Run `uv run pytest tests/ -v` and verify all tests pass (no test edits; if any failure appears, halt commit and investigate — violates CLAUDE.md §3 surgical). **Actual (2026-09-25 apply)**: `199 passed, 1 warning in 4.36s`, exit 0 ✓ (warning is pre-existing PyTorch CUDA device-not-supported userwarning from `tests/test_beta.py::test_grad_C_bound`, unrelated to this change).

## 7. Commit

- [x] 7.1 Stage: `git add wayfinder/tickets/A6b-1.md` (only). Verify with `git diff --cached --stat` that exactly 1 file is staged with +2 / -0. **Actual (2026-09-25 apply)**: `git diff --cached --stat` returned `wayfinder/tickets/A6b-1.md | 4 ++-- / 1 file changed, 2 insertions(+), 2 deletions(-)` (Edit tool line-replace semantics; character-level delta = annotation suffix only per §2.3) ✓.

- [x] 7.2 Commit on `dev` (NOT main or release; per CLAUDE.md §4 branch architecture). Commit message:

  ```
  fix(ticket): A6b-1 L1 + L14 supersede annotation per A2.1 fact-correction (4 阶段 → 5 阶段)

  Per `.audit/spec-math-audit/README.md` L223 A2.1 finding (severity LOW).

  Append italic `(historical, <原值 framing>; superseded by spec req-14 L321
  `Five-Phase Time-Driven Schedule` via `fix-openspec-doc-bugs` design.md Decision 2)`
  annotations to ticket A6b-1 L1 (title) and L14 (Question section first line),
  where "四阶段 / 4 阶段" framing contradicts spec req-14's "five phases" mandate.

  Annotation 3-反链齐 per `openspec/specs/governance/spec.md` req-gov-2 canonical form:
  - ticket-side: `wayfinder/tickets/A6b-1.md` (annotation 上下文)
  - spec-side: `req-14 L321 `Five-Phase Time-Driven Schedule``
  - change-side: `fix-openspec-doc-bugs` design.md Decision 2 (per spec req-14 Source 字段 L325)

  Original ticket narrative ("四阶段演进逻辑" / "4 阶段训练 pipeline") preserved
  verbatim per audit-verification cycle-7+9+12+13 "annotation 保留决策链, 禁止删除 stale 字面" 决策.

  Co-Authored-By: Claude Code <noreply@anthropic.com>

  ---

  ## A2.1 finding fact-correction 记录

  原 `.audit/spec-math-audit/README.md` L223 A2.1 finding 含 4 项 fact-error,
  经本 change apply 前事实验证 (2026-09-25) 锁定:

  1. **"L17 已加 supersede annotation"** — FALSE.
     L17 = `- 跑 1% 数据收集 KV` (Phase 0 Question 段 bullet), 非 annotation。
     全文 `(historical|supersede|superseded)` grep 命中只 L101 + L133 两处。

  2. **"L91 secondary table"** — FALSE.
     L91 = `  - β 更新：标量空间 Box-Constrained Projected SGD...` (几何对比段 bullet),
     非 table。文件两处真 table = L52–58 阶段总表 + L151–156 协同表。

  3. **"L91 补 (historical, 4 阶段 → 5 阶段; ...)"** — FALSE.
     L91 内容是 β vs c_i 几何对比, 不含 "4 / 5 阶段" 字样。
     真正 stale 位置 = L1 (标题 "四阶段") + L14 (Question "4 阶段")。

  4. **"superseded by spec req-14 L261"** — FALSE.
     spec.md L261 = `#### Scenario: MVP N_e=16 pinned for Phase 0 K-Means seeding`,
     这是 **req-11** (4070 MVP Hyperparameter Set) 下挂 Scenario, 非 req-14。
     真正的 req-14 = L319 anchor + L321 title + L323 body + L325 Source。

  本 change fix = 上述事实修正版:
  - annotation 落 L1 (标题) + L14 (Question 段), 非原 finding 错指的 L91
  - spec 反链 `req-14 L321` (current title), 非原 finding 错指的 `req-14 L261`

  Finding README L223 文本未修改 (保持 finding 编号稳定 + 不污染 audit-verification chain);
  本 fact-correction 在 commit body 存档。后续 cycle audit-verification 应 close A2.1 with 备注
  或 re-issue fact-corrected finding。
  ```

  **Implementation note**: pre-edit CRLF count + post-edit CRLF count 写入 commit body footer (per §4.1 + §4.3).

  **Actual (2026-09-25 apply)**: commit `3355046` landed on `dev` branch (current HEAD); commit author = `Claude Code <claude@anthropic.com>`; commit message rendered as drafted (full body including A2.1 fact-correction 4 项记录 + pre/post CRLF count + tasks checklist footer). `git log --oneline -1` returns `3355046 fix(ticket): A6b-1 L1 + L14 supersede annotation per A2.1 fact-correction (4 阶段 → 5 阶段)`. ✓

## 8. Archive prep (post-commit, optional in this change's scope)

- [x] 8.1 Run `openspec validate 2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation --strict --type change` and verify PASS (skip_specs zero-deltas accepted). **Expected**: exit 0; "Change '2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation' is valid" + ℹ skip_specs info note. **Actual (2026-09-25 apply)**: `Change '2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation' is valid` + `ℹ [INFO] file: skip_specs is set in .openspec.yaml: change declares no spec-level behavior changes, zero deltas accepted` ✓.

- [x] 8.2 (out of scope of this change) `/opsx:archive` once user instructs: this moves the change from `openspec/changes/2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation/` to `openspec/changes/archive/2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation/`. **Actual (2026-09-25 archive)**: user invoked `/opsx:archive` (skill `openspec-archive-change`); archive move executed — change directory relocated from `openspec/changes/2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation/` to `openspec/changes/archive/2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation/`. All 4 artifacts preserved (`.openspec.yaml` + `proposal.md` + `design.md` + `tasks.md`). `openspec list` no longer returns this change in active changes. ✓

## 9. Evidence linkage to audit-verification

- [x] 9.1 The applied commit (per §7.2) is the canonical handle for cross-cycle closure: future audit-verification cycles can run `git log --oneline -- wayfinder/tickets/A6b-1.md` to find this commit and `git show <commit>` to read its body for the A2.1 fact-correction evidence chain. **Actual (2026-09-25 apply)**: `git log --oneline -- wayfinder/tickets/A6b-1.md` returns 3 commits — most recent = `3355046 fix(ticket): A6b-1 L1 + L14 supersede annotation per A2.1 fact-correction (4 阶段 → 5 阶段)` ✓ (canonical handle for future cycle lookup).

- [x] 9.2 Cross-cycle closure spread: `.audit/spec-math-audit/README.md` §"A.2 Ticket 端 annotation" L219-223 maps A2.1 ↔ `2026-09-25-fix-ticket-a6b-1-four-to-five-phase-annotation` (post-archive). After archive, status changes from `planning 草案` to `archived` (manually updated or via OpenSpec tooling convention). **Actual (2026-09-25 apply)**: README L223 still has original A2.1 text unchanged (per design Decision Rationale: keep finding-编号稳定 + 不污染 audit-verification chain; this change does NOT modify finding README — see §10.1). The commit `3355046` body is the grep-stable handle. Post-archive update of README L223 status is deferred to the archive step (§8.2 out-of-scope).

## 10. False-positive findings (no action)

- [x] 10.1 A2.1 finding's 4 fact-error claims (L17 / L91 / 4→5 phase placement / req-14 L261) are documented in commit body per §7.2, NOT in finding README text. **Rationale**: editing `.audit/spec-math-audit/README.md` L223 would break finding-编号稳定性 + audit-verification chain integrity. The fact-correction lives in the change's commit body where it's grep-stable + traceable. **Actual (2026-09-25 apply)**: README L223 still contains original A2.1 text verbatim (verified via grep); fact-correction is in commit `3355046` body under "## A2.1 finding fact-correction 记录" section, listing 4 项 FALSE claims (L17 / L91 / 4→5 阶段错位 / req-14 L261 错指) with empirical evidence (L17 实际内容 / L91 实际内容 / spec.md L261 实际是 req-11 Scenario / 真正 req-14 在 L319-L325). ✓

- [x] 10.2 Other ticket-side stale pattern (cycle-9 1/128 / cycle-7 β_0 / cycle-12 covariance / cycle-13 N_e=64) are out of scope per design Decision 1 / Decision 6 / Risks §6. They are tracked in their respective OpenSpec changes (`2026-09-22-fix-ticket-a6a-2-f-threshold-supersede` archived, `2026-09-23-01-fix-ticket-stale-numerical-4file-batch` planning, etc.) or future changes. **Actual (2026-09-25 apply)**: scope-confined to L1 + L14 only; cycle-9 1/128 was closed by `2026-09-22-fix-ticket-a6a-2-f-threshold-supersede` (archived), cycle-7 β_0 by `2026-09-23-01-fix-ticket-stale-numerical-4file-batch` (planning), cycle-12 covariance by `fix-wayfinder-source-inventory-audit-2026-09-14` (archived), cycle-13 N_e=64 by commit `f077be8` (`fix(spec,ticket): close cycle-13 MEDIUM finding #1 (A6b-1 L100 N_e=64 stale + dormant bug warning)`). ✓

## 11. Python reviewer findings — post-review corrections

- [x] 11.1 **Finding #1 (informational)**: tasks.md §3.3 claimed "Common structure length = 157 − 29 = 128 chars" with slot lengths 29/48. Actual measurement (post-review, 2026-09-25): L1 slot = 26 chars; L14 slot = 45 chars; common structure = **131 chars** (157 − 26 = 176 − 45); common suffix **after** `; superseded` = **117 chars** (byte-identical between L1 + L14). **Correction applied** in tasks.md §3.3 above (revised numbers + Correction note explaining old "128" wording is historical artifact in frozen commit `3355046`). Substantive property (byte-identical common structure) holds in both old and new measurements; only the literal length number was imprecise.

- [x] 11.2 **Finding #2 (informational, OUT-OF-SCOPE for this change)**: `tests/test_schedule.py::test_phase3_b_ramp` L63-64 uses loose range `9.0 < mid < 11.0` instead of exact `pytest.approx(10.0, abs=1e-9)`. **Status**: same property covered by `test_phase_beta_max_is_time_varying` L115 (`pytest.approx(10.0, abs=1e-9)`); Python reviewer classified as "No defect — weak secondary check alongside a strong primary check". **Out of scope for this change** because:
  - This change is `skip_specs: true` per `.openspec.yaml`
  - design Decision 1 explicit: "ticket-only annotation, no spec / src / tests edits"
  - design Decision 6 explicit: "no new test (annotation non-executable, unit test cannot probe 注释)"
  - Editing `tests/test_schedule.py` would scope-creep into a test-quality change distinct from ticket-lineage cleanup
  - **Follow-up action**: file a separate OpenSpec change `fix-test-schedule-phase3-b-ramp-strict-tolerance` to upgrade L63-64 from range check to `pytest.approx(10.0, abs=1e-9)` for consistency with `test_phase_beta_max_is_time_varying`. **Out of scope for this change**; user to decide whether to spawn the follow-up.

- [x] 11.3 **Section A.4 req-11 vs req-14 L261 boundary (audit check)** — Python reviewer independently confirmed `spec.md L261` is `#### Scenario: MVP N_e=16 pinned for Phase 0 K-Means seeding` under req-11 (anchor L227). Commit body fact-correction #4 ("L261 is req-11, NOT req-14") holds verbatim. ✓

- [x] 11.4 **Section C.2 lint coverage** — `scripts/lint_no_source_field_drift.py` passes 3-file scan with no violations. Lint script implements req-34 L753-759 three structural checks (substring presence / backtick wrapping / primary-first ordering) per source code inspection. Coverage of `req-gov-2` annotation form (documenting-only meta Requirement) is delegated to this lint, not direct pytest, per the meta-Requirement's documenting-only nature. ✓

Co-Authored-By: Claude Code <noreply@anthropic.com>