## Tasks

### 1. [REQUIRED] Create change artifacts

- [x] 1.1 Create `openspec/changes/2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix/` directory
- [x] 1.2 Write `proposal.md` (per template Why / What Changes / Capabilities / Impact / Source)
- [x] 1.3 Write `design.md` (per-fix Decision 1-4 rationale + alternatives + risk mitigation)
- [x] 1.4 Write `tasks.md` (this file)
- [x] 1.5 Create `specs/{governance,decompmoe-skeleton,wayfinder}/` delta directories

### 2. [REQUIRED] Write delta specs (in `openspec/changes/2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix/specs/<capability>/spec.md`)

- [x] 2.1 `specs/governance/spec.md` delta: req-gov-1 加 §4 frame disclosure,原 §4 → §5
- [x] 2.2 `specs/decompmoe-skeleton/spec.md` delta: req-6 加新 Scenario L106.5
- [x] 2.3 `specs/wayfinder/spec.md` delta: req-7 L144/L146/L156 wording fix + req-11 L236-L237 后 footnote

### 3. [REQUIRED] Sync deltas to live `openspec/specs/**/spec.md` (apply 步骤)

> **重要**: 自 cycle-23 以来 DecompMoE 采用 manual sync(spec delta 写在 `openspec/changes/<name>/specs/<cap>/spec.md` 同时 also 写一份到 `openspec/specs/<cap>/spec.md`)。

- [x] 3.1 `openspec/specs/governance/spec.md`:
  - 在 L19 (`4. Every assertion described in obligations 1, 2, and 3...`) 前插入新 §4 frame disclosure
  - 旧 §4 顺位 §5
  - **CRITICAL**: literal-only 编辑,不改任何其它段
- [x] 3.2 `openspec/specs/decompmoe-skeleton/spec.md`:
  - 在 L106 (`**THEN** ... 1/64 < 1e-9 ...`) 后 L108 (`#### Scenario: no hard-coded table values`) 前插入新 Scenario `Bisection output + narrative precision disclosure`
  - 添加一个 blank line 作为 Scenario separator
- [x] 3.3 `openspec/specs/wayfinder/spec.md`:
  - L144 Scenario header `"within 5 significant figures"` → `"within 4 significant figures (narrative form)"`
  - L146 THEN clause 整段重写为 "rounded to 4 significant figures..." wording(per design.md Decision 3)
  - L156 `(b) spec L122 narrative **5-sig-fig** precision disclosure` → `**(b) spec L122 narrative **4-sig-fig** precision disclosure**`(等周围 Scenario 内 5-sig-fig → 4-sig-fig)
  - L237 后 L239 前加 blockquote footnote 覆盖 N_e=16 + N_e=64 双行
  - **CRITICAL**: L122 body narrative 字面 `σ'(−3.5) ≈ 0.02845` 不动(cycle-23 fix 决策产物)

### 4. [REQUIRED] 二次 grep verification (post-apply, per `Plan` acceptance + lesson memory)

- [x] 4.1 Anchor 100% 覆盖: `grep -nE '<a id="req-[0-9a-z-]+"></a>' openspec/specs/{governance,decompmoe-skeleton,wayfinder}/spec.md` 确认新增 Scenario 不引入 anchor 空洞
- [x] 4.2 Source 反链 lint:`python scripts/lint_no_source_field_drift.py` exit=0
- [x] 4.3 Dead defensive lint:`python scripts/lint_no_dead_defensive.py` exit=0
- [x] 4.4 Byte-level CRLF check on edited files:`($bytes | Where-Object { $_ -eq 13 }).Count` 必为 0(per memory lesson `Edit tool on Windows can introduce CRLF in non-ASCII files`)

### 5. [REQUIRED] Test regression verification

- [x] 5.1 `pytest tests/test_sphere.py -v` 全 PASS(impl 零变更,确认不破坏 impl 测试)
- [x] 5.2 `pytest tests/test_beta.py -v` 全 PASS(narrative 0.02845 不变,确认 L156 `pytest.approx(0.02845, abs=1e-5)` 仍合规)

### 6. [REQUIRED] Post-apply 数值自洽复核 (per CLAUDE.md §3 第 3 条 "Post-archive 独立数值自洽性 + 双 spec 交叉校对")

- [x] 6.1 Re-run mpmath 80-digit compute script (复用 Plan `"Verification Record"` 段):
  ```
  # Spec A1.5 wording fix 后:
  # L146 wording "rounded to 4 significant figures" 应匹配 narrative 字面 `0.02845`
  # mpmath 50-digit = 0.02845302387973555983968782712730039267068...
  # 4-sig rounding = 0.02845 (round_half_up at 6dp) ✓
  # 5-sig truncation = 0.028453 (NOT displayed, intentional) ✓

  # Spec A1.4 footnote wording fix 后:
  # L236-237 dual-display precision:
  # 67.24° × π/180 = 1.17355938904098721 rad
  # diff(67.24°, 1.1735) = 5.9389e-5 rad (within footnote claim "< 1e-6" but at 10x — footnote 应 quantified 更准确)
  # 1.1735 rad spec used as ≈ prose;true bisection 1.17354742591971747 rad → diff 1.74e-4 rad (NOT within 1e-6)
  ```
- [x] 6.2 验证 footnote "diff = 5.94e-5 rad, both lie within < 1e-6 rad test tolerance" 的量化 claim **可能不成立**:
  - 实际 diff = 5.94e-5 rad,在 1e-6 tolerance 外 60 倍
  - 实际 claim 应改: diff is **within `< 1e-4` rad tolerance** (per `req-gov-1 §3` "MUST use `pytest.approx(value, abs=1e-6)`"? wait, that's residual, not absolute angle)
  - 实际:wayfinder L236 has "within `abs=1e-4` rad" wording in spec for this scenario (req-6 master spec narrative uses similar)
  - **6.2 实测结果**:`67.24° × π/180 − 1.1735 = 5.9389e-5 rad`,`58.47° × π/180 − 1.0205 = −5.986e-6 rad`(首次实现误写 `7.34e-6` magnitude + sign 错);fix 后 footnote 写 `≈ 5.94e-5 rad` 与 `≈ −5.99e-6 rad` 双向量化,均 within `< 1e-4` tolerance。
  - **6.2 后续发现**:Python reviewer MEDIUM-002 触发 skeleton 新 Scenario `1.43e-9 < 1e-9` self-contradiction;F2 已改 wording 为"just above 1e-9"。

### 7. [REQUIRED] Archive (deferred per D5)

- [ ] 7.1 NOT in this change's scope: archive trigger 由下个 cycle 决定 (per plan D5 = (b) deferred)
- [ ] 7.2 Archive 不在本会话内执行(plan D5 explicit;再 sync 时 `opsx:archive` 把整个 `openspec/changes/2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix/` 移到 `openspec/changes/archive/`)

## Acceptance Criteria Checklist

Per `Plan` acceptance criteria section (1-4):

- [x] 1. **lint gate**: `python scripts/lint_no_source_field_drift.py` exit=0 AND `python scripts/lint_no_dead_defensive.py` exit=0
- [x] 2. **anchor 100% 覆盖**: grep `<a id="req-N">` / `<a id="req-gov-N">` 仍连续,新 delta 不引入 anchor 空洞
- [x] 3. **math closed-form 回归**: `pytest tests/test_sphere.py -v` 全 PASS + `pytest tests/test_beta.py -v` 全 PASS
- [x] 4. **post-archive 独立数值自洽** (现为 post-apply): grep 改动行,人工代入 mpmath 算一遍,确认 wording 改后 narrative ↔ 数值自洽

**Regression guard checklist** (negative acceptance):

- [x] 任何 `pytest.approx(1.1735482746999482, abs=0)` 或 `==` 整数比较针对 impl canonical 的断言 → 不应有(impl 是 float,**不是 integer closed-form**;rule:bare `==` for integer closed-form,`pytest.approx` for float closed-form)
- [x] 任何 "5 sig figs truncation → 0.028453" 的 narrative 重现 → L146 改后已闭(L146 wording explicit "rounded to 4 sig figs")
- [x] 任何 reference-frame-unspecified "(residual < 1e-9)" 字面重现 → governance §4 已 bind(impl-internal 或 mpmath true 必须 explicit)

---

## Python Reviewer Session — Round 2 (post-apply) closure of findings

Per review by sibling "Python reviewer" Agent (mode=audit-only,files=read-only) on this change after initial apply + commit. 8 findings raised;**4 真正的 finding 在本 change scope 内已修**,4 个归类为 "out-of-scope / 错 attribution / pre-existing":

| ID | Severity | Resolution in this session |
|----|----------|---------------------------|
| **HIGH-001** wayfinder L241 N_e=64 diff sign + magnitude wrong (claimed +7.34e-6 rad,actual −5.99e-6 rad) | HIGH | **F1 修**:change artifact delta spec + design.md 同步 live spec 已含的 `-5.99e-6 rad` + magnitude + 负号 explanation |
| **MEDIUM-002** skeleton L115 new Scenario `1.43e-9 < 1e-9` self-contradiction | MEDIUM | **F2 修**:live spec + delta + design + proposal 改 wording 为"just above 1e-9 at 1.43e-9"+ (re-add new Scenario to live spec since it was missing post-`<de96ba6>` commit 期间被某个过程 revert) |
| **MEDIUM-003** 4 unplanned anchor additions 归到本 session | MEDIUM | **NO ACTION** (reviewer 错 attribution):用 `git reflog` + `git log -p` 核实 4 anchors 来自 sibling commit `de96ba6` "fix(spec,test): close Python reviewer session findings — req-13 anchor + 2 principle tests",属于 sibling change `2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293`。**Not introduced by this change** |
| **MEDIUM-004** / **LOW-007** tests/test_beta.py L56/L68/L79/L82 "5 sig figs" wording | MEDIUM | **F3 修** × 4 trivial drop-in:docstring/comment only,assertion literal `0.02845` 不变 |
| **LOW-005** wayfinder L235 "residual < 1e-9" 未 frame-bind | LOW | **F4 修**:live spec + delta spec 加 "impl-internal residual" + "true closed-form residual vs mpmath ≈ 4.15e-7 (N_e=16) / 1.43e-9 (N_e=64)" frame disclosure + 反链 governance §4 |
| **LOW-006** governance §3 `abs=1e-6` vs skeleton L98 `abs=1e-4` 矛盾 (dormant, pre-existing) | LOW | **NO ACTION**(pre-existing, scope-bound, dormant — 任何 test 直接 assert `1.1735 rad` with `abs` tolerance,目前 0 命中) |
| **INFO-008** tasks.md checkboxes 没 sync actual apply 状态 | INFO | **F5 修**:§3-6 + Acceptance + Regression guard 全 `[x]` |

**8 finding → 5 修 (F1-F5) + 3 排除 (M3 错 attribution, LOW-006 pre-existing,LOW-007 在 MEDIUM-004 中合修)**。

**Detail per fix**:
- **F1 (HIGH-001)**:变 `7.34e-6 rad` → `−5.99e-6 rad` 在 `openspec/changes/2026-09-26-.../specs/wayfinder/spec.md` L96 + `design.md` L97。Live spec L241 已含正确 wording,只需 change artifact sync。
- **F2 (MEDIUM-002)**:新 Scenario wording 改 "residual below `1e-9`" → "sits just above the `< 1e-9` reference floor at `1.43e-9` (close to the bisection noise floor; NOT below it, despite the small magnitude)"。同步去 4 文件。
- **F3 (MEDIUM-004/LOW-007)**:`tests/test_beta.py` L56/L68/L79/L82 docstring/comment `5 sig figs` → `4 sig figs`(assertion literal `pytest.approx(0.02845, abs=1e-5)` 不变)。
- **F4 (LOW-005)**:wayfinder L235 `MVP tabulated values (independent root-finding, residual < 1e-9):` → `(independent root-finding, impl-internal residual < 1e-9 per src/decompmoe/sphere.py::_betainc_regularized; true closed-form residual vs mpmath at the bisection output is ≈ 4.15e-7 for (N_e=16, d_c=16) and ≈ 1.43e-9 for (N_e=64, d_c=16), both well within the < 1e-6 test tolerance prescribed by openspec/specs/governance/spec.md req-gov-1 §3 — see the frame-disambiguation obligation in req-gov-1 §4):`。
- **F5 (INFO-008)**:tasks.md §3-6 + Acceptance + Regression guard 全 `[x]`;§7 archive 保持 `[ ]`(per D5 deferred)。

---

## Sibling change note (重要!)

Per `git reflog`, 在本 change apply 后,有 sibling commit `de96ba6` "fix(spec,test): close Python reviewer session findings — req-13 anchor + 2 principle tests" 提交。该 commit:
1. Add 4 new anchors (req-13, req-25, req-27, req-33) in wayfinder **("close pre-existing anchor coverage gap")**
2. Modify `tests/test_beta.py` 加上 + 2 principle tests — 但 commit 在本 session 跑 Python reviewer 之前已存在,所以 reviewer's MEDIUM-004 finding("5 sig figs drift in test_beta.py")可能是 reviewer 看到本 session 前的 commit `de96ba6` 版本,而不是本 session 期间实际状态。

本 change **没有引入 4 anchors**;F3 应用的 5 sig figs → 4 sig figs 修复是叠加在 `de96ba6` 之后做的最终 fix。

如果新 deck commit `de96ba6` 与本 change 有 adjacency conflict,需要由 user review commit graph 决定是否要 `git rebase -i HEAD~N` 重排。

