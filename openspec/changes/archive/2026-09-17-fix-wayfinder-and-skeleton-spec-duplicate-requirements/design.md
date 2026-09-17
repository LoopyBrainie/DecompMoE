## Context

`decompmoe-skeleton/spec.md` 经历过多次"在主 spec 写旧 Req → 在 skeleton 写新 ADDED Req 做语义对齐"的演进。`04fd653` 把 5 对并存版本同时带进了仓库，造成"每个主题双 Req"。`wayfinder/spec.md` 中 `resurrection_perturb_distribution` 的 body 在 L577 / L642 与各自 Scenario（L582 / L650）签名不一致，导致读者按 body 写代码会被 Scenario 测试拒收。

本次 change 是纯 spec 清理——`src/decompmoe/` 已经按 ADDED 版语义实现，删除旧 Req 与对齐 body 不会触发任何代码改动。详见 `proposal.md - Why / What Changes`。

## Goals / Non-Goals

**Goals:**
- 让 `decompmoe-skeleton/spec.md` 回到"每个主题单一权威 Req"——5 对并存合并为 5 个 ADDED
- 让 `wayfinder/spec.md` 的 `resurrection_perturb_distribution` 两处 body 与 Scenario 自洽
- 不触发 `src/decompmoe/` 任何代码改动
- 不触发 `tests/` 任何测试改动

**Non-Goals:**
- 不重命名任何 Req（保留 ADDED 现有的"— D1 / — Phase-4 / — CG / — max(…z…, ε)"后缀）
- 不重写 ADDED Req 的措辞（ADDED 已记录正确语义）
- 不修 HIGH-1（`should_resurrect` 签名 drift）——已在 `fix-safeguards-should-resurrect-signature-drift` 处理
- 不修 wayfinder L20（"4070 MVP Hyperparameter Set"，**不是** "Frozen MVP Hyperparameter Set"）——这是 wayfinder 的精炼措辞版本，不与 skeleton L20 重复

## Decisions

### Decision 1：用 REMOVED 而非 MODIFIED 处理 skeleton 5 个旧 Req

**选项**：
- (a) **REMOVED 5 个旧 Req**（本次采用）——`apply` 阶段从主 spec 删除旧 Req，保留 ADDED 作为唯一权威
- (b) MODIFIED 5 个旧 Req，body 改为"see ADDED Req at L..."——双 Req 仍在，永久留下 dead-link
- (c) DEPRECATED 标记 5 个旧 Req——同上，仍然双 Req

**Rationale**：
ADDED Reqs 已经完整承载语义（措辞/数值/Scenario 都齐全），把旧 Req 留作 ghost 会形成"spec rot"——以后任何 spec 维护者都得判断"两个 Req 哪个对"，但 ADDED 标题里"— D1 / — Phase-4 / — CG / — max(…z…, ε)"后缀已经让新旧关系一目了然。REMOVED 是 OpenSpec 提供的"显式清理"语义，比"MODIFIED 留空 body"更明确。

**替代方案代价**：(b)/(c) 都会留下"spec 双胞胎"，违反"每个主题单一权威 Req"原则。

### Decision 2：L436 / L440 / L444 三个 Scenarios 留 orphan，不迁到 L510 ADDED 下

**选项**：
- (a) **orphan Scenarios**（本次采用）——Scenarios 留在原行号，不挂在任何 Req header 下
- (b) 复制到 L510 ADDED Req 下——内容与 L516 / L522 / L528 的 ADDED Scenarios 重复

**Rationale**：
L436 / L440 / L444 三个 Scenarios 在 L510 ADDED 已有等价表达（L516 "Parameterization endpoints" / L522 "gamma reset for phase 4 boundary continuity" / L528 "beta_effective is continuous at Phase 3 → 4 boundary"），迁移会产生"同一 invariant 写两遍"。OpenSpec 允许 orphan Scenarios（不被任何 Req 引用），对 grep / lint 工具透明，对 spec 阅读者而言相当于"被删 Req 的执行轨迹"——仍可在 git history 中追溯。

**替代方案代价**：(b) 造成 Scenarios 重复，违反 DRY；后续若修改一个，apply 阶段容易漏掉另一个。

### Decision 3：`resurrection_perturb_distribution` 的 `dim` 参数设 keyword-only

**选项**：
- (a) **`f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None`**（本次采用）——`dim` keyword-only
- (b) `f_per_expert, target_idx, eps_std=0.05, dim: int | None = None`——`dim` positional-or-keyword

**Rationale**：
Scenario 显式写"`dim=None` raises `TypeError`"——这是个**契约边界**信号：忘记传 `dim` 必须在调用点立即失败，而不是依赖运行时 `is None` 兜底。Python 的 `*,` keyword-only 语法正好表达这个意图——它把"传 dim"从"可选参数"提升为"必填契约参数"，让 lint / IDE 能静态捕获"`dim` 未传"的错误。

**替代方案代价**：(b) 的运行时 `if dim is None: raise TypeError(...)` 检查与 (a) 在功能上等价，但 (a) 把契约前移到签名层，更易被静态检查工具识别，符合项目"math principle must guard, not just functionality"原则（见 `~/.claude/projects/D--myProject-DecompMoE/memory/math-principle-must-guard-not-just-functionality.md`）。

### Decision 4：不修 `resurrect_expert` wrapper 的 `cfg` 参数

**选项**：
- (a) **不动 `resurrect_expert(i, j_star, β_per_expert, cfg)`**（本次采用）——wrapper 仍接受 `cfg`
- (b) 改为 `resurrect_expert(i, j_star, β_per_expert, dim: int)`——移除 `cfg`，让 `dim` 显式

**Rationale**：
`resurrect_expert` 是 single-event wrapper（"same Python call stack" 契约），它需要 `cfg: MVPConfig` 来 source `cfg.d_c`（per-expert dimensionality）。这与 `resurrection_perturb_distribution` 的"纯函数 + 显式 dim"是不同抽象层——wrapper 故意保留 `cfg` 以避免 caller 重复传 `dim`。两个 API 共存是设计意图，不是冗余。

**替代方案代价**：(b) 会让 wrapper 调用方重复传 `dim`（caller 已经持有 `cfg`），违背"wrapper 的存在意义"。

## Risks / Trade-offs

- **[Risk] L436 / L440 / L444 的 orphan Scenarios 在未来 OpenSpec 版本可能被自动警告** → Mitigation：本次 change 不触碰这三个 Scenarios 的内容；若未来 OpenSpec 升级后报错，可在 L510 ADDED 下用同一文本替换 orphan 行（已记录在 `Migration` section）
- **[Risk] wayfinder L577 / L642 body 改为新签名后，与 `fix-safeguards-should-resurrect-signature-drift` change 的 `should_resurrect` 签名收敛不一致** → Mitigation：HIGH-1 的 `should_resurrect` 签名（apply 时已对齐 `f_per_expert` 参数）在本次 change **不重复修改**；两者是不同函数，`should_resurrect` 属于 safeguards 范畴
- **[Risk] apply 阶段若 `opsx sync` 不识别 orphan Scenarios，可能误删 L436-446 整段** → Mitigation：`openspec sync` 的 spec delta 处理是声明式的（仅按 `## REMOVED Requirements` / `## MODIFIED Requirements` section 操作），orphan Scenarios 不在 delta section 内不会被自动触碰；apply 前会跑一次 `openspec validate` 预检
- **[Trade-off] 删 5 个旧 Req 后，git blame `04fd653` 之前的 commit 仍能找回这些 Req 的原始版本**——这是 OpenSpec 的 git-first 优势，无需额外 mitigation

## Migration Plan

1. `apply` 阶段在 dev 分支上按 delta 顺序执行：
   - 先 `decompmoe-skeleton`（REMOVED 5 个 Req）：从 `openspec/specs/decompmoe-skeleton/spec.md` 删除 L20 / L94 / L145 / L307 / L432 的 Req 块（保留 L436 / L440 / L444 orphan Scenarios 不动）
   - 再 `wayfinder`（MODIFIED 2 个 Req）：把 L577 与 L642 的 body 改为新签名
2. apply 前跑 `openspec validate --change fix-wayfinder-and-skeleton-spec-duplicate-requirements` 确认 delta 通过校验
3. apply 后跑 `python scripts/lint_no_dead_defensive.py`（exit=0 是 archive 前置条件，见 `19543eb` 修复的 `12f673d` 漏洞）
4. **回滚策略**：若 apply 后 lint 失败，`git revert` 整批 commit 即可——5 处 Req 删除 + 2 处 body 修改都是 declarative，可逆
