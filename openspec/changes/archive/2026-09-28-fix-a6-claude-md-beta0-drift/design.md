# Design

## Context

See `proposal.md` — Why（缺陷、根因、severity 降级论证）。

本 design 只需补充实现前必须定下的技术选择。单行文档替换本身无架构含义；下列 3 个 Decision 之所以需要成文，是因为它们都可能被后续 reviewer 质疑，且答错会引入新缺陷。

## Goals / Non-Goals

**Goals:**

- 把 severity 降级（MAJOR → MEDIUM）的判定依据固化，避免下一轮 audit 再次按原清单定级。
- 钉死替换目标字面量的形式（4-sig-fig）及其与 spec 既有风格的对应关系。
- 显式记录「不加 guard test / 不加 lint」的理由与已知盲区。

**Non-Goals:**

- 不设计任何 `CLAUDE.md` ↔ spec 一致性的自动化校验机制（记为 future scope，见 Decision 3）。
- 不设计 `CLAUDE.md` §5 其余字面量的普查方案（属 Out of scope）。
- 不涉及任何代码实现。

## Decisions

### Decision 1 — severity 定为 MEDIUM 而非 MAJOR

**选择**：MEDIUM。

**依据**：`CLAUDE.md` §8 定义的「污染」有严格定义 —— 三条**已观测的传染通道**：(i) `src/` 默认值直接抄 ticket 数值，(ii) tests `assert == stale_value` 锁定，(iii) reader-ticket-not-spec 复制 stale 数值。前两条已在 `adf41ef`（2026-09-19，通道 i+ii）、`d239f57`（2026-09-21，cycle-12）、`f077be8`（2026-09-21，cycle-13）闭合；`src/decompmoe/config.py:55` 与 `tests/test_beta.py:38` 现均为 1.035。

**通道 (iii) 仍开放，且本缺陷正是它的一个实例** —— `CLAUDE.md:61` 是读者可见的叙述摘要、承载 `wayfinder/tickets/A4-1.md` 的 stale `β_0 ≈ 1.0`。`governance/spec.md:144`（`req-gov-4` §3）明文规定「传染链已断」的判定「does NOT exempt the project from this monitoring obligation — recurrence remains possible whenever a new contributor reads a ticket without consulting the corresponding spec」。故本缺陷的准确定性是：**通道 (iii) 未闭合的一个真实残留**，而非「三条通道全部闭合后的例外」。该定性不改变 severity 判定（无 `src/`/`tests/` 外溢、无 guard test 会变红），但决定了它须按 `req-gov-4` §3 继续纳入周期性 audit 复核。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 维持 MAJOR（清单原级） | MAJOR 隐含「正在扩散或已扩散到 `src/`/`tests/`」，本缺陷不满足。虚高定级会稀释后续 audit 的信号密度 —— 这正是 `b23f0e5` 承诺处理的 reviewer 精度问题（该 commit 自身也把一条 finding 降级并记录理由） |
| 降为 LOW | 不成立。3.39% 的数值漂移 + `CLAUDE.md` §5/§8 的自相矛盾是真实的、可被 reader 触发的缺陷，不是排版瑕疵 |
| 定为 HIGH | 不成立。HIGH 在本仓的先例（`b23f0e5` H1–H3）保留给「规范当前处于事实错误 / 空转 / phantom」级别。本缺陷不影响任何规范性 Requirement |

### Decision 2 — 替换目标取 `1.035`（4-sig-fig），不取 `1.0350601609682665718`

**选择**：`β_0 ≈ 1.035`。

**依据**：`openspec/specs/wayfinder/spec.md:146` 显式记录了本仓的 narrative precision 风格选择（4-sig-fig，与 `σ'(−3.5) ≈ 0.02845` 的 4-sig 对齐），并说明为何不用 5-sig（`0.028453`）。`wayfinder:130` / `:578` / `:589` 与 `decompmoe-skeleton:483` 一律用 `β_0 ≈ 1.035`。`CLAUDE.md` §5 是 narrative 摘要块，采用同精度才一致。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| `1.0350601609682665718`（50-digit 精确值） | 精度远超 §5 冻结块其余各行（`452M` / `4096` / `67.24°`），反而制造新的不一致 |
| `1.0351`（4-dp round） | `1.0350601…` 的 4-dp round 是 `1.0351`，而 spec 全用 1.035。对齐 spec 而非自行 round |
| 只删 `（β_0 ≈ 1.0）` 括注 | 失去 §5 作为 MVP 参数速查表的作用。§5 已自述为 frozen 权威摘要，删项比改值更伤可用性 |

### Decision 3 — 不加 guard test，也不加 lint 脚本

**选择**：两者都不加。

**为何加不了 guard test**：`CLAUDE.md` §5 不承载闭式，无可对账对象。`CLAUDE.md` §6 第 8 条要求「spec 中每个含具体数值的算式必须有 `pytest.approx` 或 `==` 直接对账」—— 该规则的适用域是 **spec Requirement**，不是文档摘要。为一句叙述文字造一个 pytest 断言，等于把文档当契约源，违反 `CLAUDE.md` §2 truth hierarchy（`openspec/specs/**/spec.md` 是第 1 级，`CLAUDE.md` 是第 3 级来源记录）。

**为何加不了 lint**：`scripts/lint_no_source_field_drift.py` 实测只读 `openspec/specs/**/spec.md`（其必含子串表以 `_REPO_ROOT / "openspec" / "specs" / ...` 构造），**不读取 `CLAUDE.md` 内容**；`scripts/lint_no_dead_defensive.py` 检查 `src/` 防御性代码。二者对 `CLAUDE.md` §5 的数值漂移**零覆盖**。

**已知盲区（记为 future scope，不在本 change）**：`CLAUDE.md` §5 与 spec 的数值一致性目前**无任何自动化 gate**。未来若要覆盖，需要新增「解析 `CLAUDE.md` §5 冻结块 → 与 spec canonical 值逐项对账」的 lint 脚本，属治理条款级扩展（`governance` capability 的 Requirement 变更），必须另开 cycle 并配 TDD。本 change 不代劳。

**考虑过的替代方案**：

| 替代 | 为何不选 |
|---|---|
| 加 pytest 断言 `MVPConfig().beta_initial == 1.035` | 该断言**已存在**（`tests/test_beta.py::test_beta_param_init_default`，`pytest.approx(..., abs=1e-3)` 形态）。再加一条只是在断言 `src/` 已有事实，与 `CLAUDE.md` 文本仍无耦合 |
| 加一条测试 grep `CLAUDE.md` 含 `1.035` | 把 markdown 文本内容做成测试契约，与 Decision 3 的「CLAUDE.md 非契约源」直接矛盾；且该模式会诱使后续把全部 §5 字面量测试化，方向错误 |
| 本 change 顺带加 lint | 属治理条款变更（须改 `governance` Requirement + 写 TDD），远超「一行漂移修复」的范围，违反 `CLAUDE.md` §3 surgical |

## Risks / Trade-offs

- **[并行 session 推进 HEAD 导致行号漂移]** → 实测已发生：`b23f0e5` → `53ca016`（13:00:43）。apply 阶段必须 `git show HEAD:CLAUDE.md` 重新定位，不得沿用 proposal 行号。
- **[`CLAUDE.md` 漂移无 gate，同类缺陷会再次逃逸]** → 已知盲区，见 Decision 3。缓解只能是周期性 audit 复核，本 change 无法在工具层解决。
- **[把 1.0 改成 1.035 会让 `CLAUDE.md` 与 spec 的耦合加深]** → 评估为可接受且必要：§5 已自述为 frozen 权威摘要，不耦合才是缺陷本身。
- **[无 `specs/` delta 可能在后续 review 被质疑「零 delta change」]** → `.openspec.yaml` 已设 `skip_specs: true` 并在 proposal 的 Capabilities 段给出理由；`openspec validate --strict` 可证其合规。
