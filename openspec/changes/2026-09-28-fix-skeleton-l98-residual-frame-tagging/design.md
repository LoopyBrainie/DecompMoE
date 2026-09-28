# Design: 2026-09-28-fix-skeleton-l98-residual-frame-tagging

## Context

上一轮归档的 change `2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding`（commit `33deb9b` apply、`e5fec3a` archive）关闭了 Voronoi 数值精度缺陷族中的 A1 / A5，并顺手修复了 code review 报出的 P1–P5。剩下的缺陷分两类：

**可立即修（空闲区）**——`decompmoe-skeleton` req-6 L98 的两处 `< 1e-9` 未标参考系，违反 `governance` req-gov-1 §4。`decompmoe-skeleton` 是三个 capability 中唯一**没有被任何 active change 声明 delta** 的，故可安全修改。

**被 delta 争抢阻塞**——`governance` L20/L21 与 `wayfinder` L233/L274-276 存在同族（乃至更严重）的缺陷，但它们的 delta 已被并行 session 占用。

本 design 记录的是**为什么只修前者**，以及在实施过程中实测到的、会影响后续 change 的仓库事实。

---

## Goals / Non-Goals

**Goals**

1. 让 req-6 body 的两处 `< 1e-9` 声明**指向确定的参考系**，满足 req-gov-1 §4 的 "Spec MUST clarify which frame is used"。
2. 只动空闲 capability，**零新增数字**（全部复用仓库既有实测值）。
3. 把被阻塞项的阻塞原因、替换措辞、复现命令**留成可执行的记录**，使后继 change 能机械接手。

**Non-Goals**

- 不改 `governance` / `wayfinder`（Delta contention，Decision 2）。
- 不改任何并行 session 的 change 目录（Decision 3）。
- 不新增测试或 lint 规则。
- 不解冻 `CLAUDE.md` §5 的 4dp prose 形式，不动 A1 已确立的双层 literal 契约。

---

## Decisions

### Decision 1 — 补 frame 标注，且同时写出两个参考系的数值与否定结论

**选择**：不只加「impl-internal frame」四个字，而是把两个参考系的残差**都**写进同一从句，并显式给出「true closed-form 侧**不**满足 `< 1e-9`」的否定结论。

**理由**：req-gov-1 §4 说的是 "Either frame is acceptable as long as the frame is explicit" —— 单写一个 frame 名即已合规。但本仓的实际情况是**两个 frame 的真值相反**（impl-internal 真、true closed-form 假）。若只写 "impl-internal frame per §4" 而不给出对照，读者无法自行判断该 frame 选择的代价有多大，也无法从 body 推知同 Requirement 的 Scenario L115 早已记录了 `4.15e-7` 这一事实。写出两侧 + 否定结论，使 L98 与 L102 / L106 / L114 / L115 构成一个自洽的整体。

**具体措辞**（L98 occurrence 1）：

```
(residual `< 1e-9`, impl-internal frame per `openspec/specs/governance/spec.md`
req-gov-1 §4 — `1.16e-14` at `(N_e=16, d_c=16)`, `1.94e-15` at `(N_e=64, d_c=16)`;
the true closed-form frame instead yields `4.15e-7` / `1.43e-9` and does **not**
meet `< 1e-9`), NOT via a hard-coded table
```

occurrence 2 只需一个短标注（该处已有 req-gov-1 §3 引用，语境已足）：

```
with the bisection residual `< 1e-9` in the impl-internal frame per
`openspec/specs/governance/spec.md` req-gov-1 §4);
```

**数字出处（零新增）**：

| 数字 | 出处 | 语义 |
|---|---|---|
| `1.16e-14` | `governance/spec.md:20` + skeleton L114 | impl-internal, N_e=16 |
| `4.15e-7` | `governance/spec.md:21` + skeleton L115 | true closed-form, N_e=16 |
| `1.94e-15` | skeleton L114 | impl-internal, N_e=64 |
| `1.43e-9` | skeleton L115 | true closed-form, N_e=64 |

本 change 逐个独立复算确认（`tasks.md` §4），未从旧报告照抄。

### Decision 2 — `governance` / `wayfinder` 的同族缺陷挂起，不叠第三份 delta

OpenSpec 的 `## MODIFIED Requirements` delta 是**按 Requirement 整块覆盖**执行的，不是按行 patch。**两份**未归档 delta 同时 `MODIFIED` 同一 Requirement 时，**后归档者会静默丢弃先归档者的全部编辑** —— 不报错、不告警、两个 lint 与 `openspec validate` 全绿。这是本仓已发生过的高代价陷阱。

实测 delta 归属（只看 `<change>/specs/` 目录，**不**按正文 mention 判断——后者会被 Out-of-scope 清单与 Source 反链污染成假阳性）：

| capability | 声明者 |
|---|---|
| `decompmoe-skeleton` | **空闲** —— 无 active change 声明（详见 Decision 5） |
| `governance` | `2026-09-28-fix-a2-a3-a4-residual-precision-claims` |
| `wayfinder` | `2026-09-28-fix-a2-a3-a4-…` **和** `2026-09-28-fix-a7-flops-attribution-and-stale-ref` |

因此 `governance` L20/L21（`60 subintervals` 描述了从未存在的求积；`< 1 ppm` 字面读法为假——函数自身相对误差 `6.63 ppm`）与 `wayfinder` L233 / L274-276（未标注且在真闭式下为假）**本轮一律不动**。

**解锁条件**：`a2-a3-a4` 与 `a7` 均已归档，且 `tasks.md` §5 的 post-archive 审计对 `1e-4 rad` 零匹配。

**后继 change 的合并规则**：`governance` + `wayfinder` **必须同一个 change 出两份 delta**。拆成两个 change 会让它们在 archive 时互相产生第三份争抢。

### Decision 3 — A5 回退风险只报告，不代改

`a2-a3-a4` 当前 **0/27 任务完成**，且未对工作树施加任何 spec 改动。其 `wayfinder` req-11 delta 是从 **`33deb9b` 之前的快照**构造的。实测 diff 其 delta 与当前 live spec：

```
live-only 行（peer 归档时会 REVERT）:  5
peer-only 行（peer 自己的 A4 增补）:  6
peer delta 含 'prose-to-prose'    : False
peer delta 含 '59×'               : False
peer delta 含 '< 1e-4 rad'        : True    <-- 幽灵授权仍在
```

**后果**：该 change 归档时，其 full-block delta 会把 `wayfinder` req-11 覆写回 `33deb9b` 之前的版本，**恢复已被归档 change 删除的 `< 1e-4 rad`「test tolerance permitted by §2」幽灵授权**。

**选择**：**报告 + 留可重跑审计任务**，不修改他人 session 的 change 目录。

**理由**：(a) 改他人 change 的 delta 会破坏其 27 项任务的完整性假设，且该 session 正在活跃工作；(b) A5 修复已提交（`33deb9b`）且已归档，`archive/2026-09-28-fix-a1-a5-…/` 是现成的重施来源，**可恢复**；(c) 真正的修复动作是「让该 session 在归档前重同步 delta」，属用户/该 session 的动作，不是本 change 能代劳的。

**缓解**：`tasks.md` §5 落一条 re-runnable 的 grep 审计，把静默回退变成**可检测的失败**。

### Decision 4 — delta 必须程序化构造，禁止手抄

req-6 的 delta 是 full-block 替换，block 内含 164 个反引号、4 个 Scenario、约 25 行长散文。手抄重述的历史失败模式已在本仓实证：上一个 change 手抄 3 个 Requirement，产生 **3 处静默缺陷 + 1 处重复**（时间戳 `22:02:52`→`22:52:52` 换位、`σ'` 误抄成 `γ'`、同一句混用 U+2212 与 ASCII 两种减号字形、`design.md design.md` 重复）——**全部不会让 Markdown 渲染失败，也无法靠肉眼在长 Requirement 里发现**，而 `pytest` / 两个 lint / `openspec validate` **全都抓不到**（它们只查反链格式、防御性代码、测试行为，不校验 spec 文本逐字保真）。

**因此本 change 的 delta 由脚本从 live spec 抽取 + 定点替换生成**，并施加三层验证：

1. **替换命中断言**：每个 target 必须在**全文件范围**唯一（`count == 1`），且在 block 内唯一。
2. **往返验证**：按 header 整体**逆序**全部反向替换，必须与原文**逐字节相等**。
3. **结构 / Markdown 合法性**：反引号配平、Scenario 数不变、无 `<a id=>` 锚点混入、frame 标注增量为 `+2`。

**并额外用 provenance 断言锁死 live 与 delta 的一致性**：live spec 的 block 由 delta block **反向替换后必须等于改前的 live block**——这在结构上保证「live 编辑不可能与 delta 漂移」。

### Decision 5 — delta 归属必须在**动手前一刻**复查

`decompmoe-skeleton` 在 plan 撰写时为空闲，**实施时已出现新声明**：`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure/specs/decompmoe-skeleton/` 目录存在。

实测该目录**为空壳**（无 `spec.md` 文件），且其自身 `tasks.md` §1 首行明写「本 change **不动 spec / src / tests**，仅 audit-closure 留痕」，§2 Out of scope 第 1 条「**不修改任何 spec body**」。故不构成真实争抢，`decompmoe-skeleton` 仍可安全修改。

**记录此事实的意义**：空目录 ≠ delta 声明，也不是「一定不会有 delta」。判定必须读**内容意图**（该 change 的 proposal / tasks 是否计划改 spec），不能只看目录是否存在，也不能只看目录名。

### Decision 6 — 不新增测试

本 change 是**纯散文标注修正**，无新行为可钉。四个数字的可验性已在 `tasks.md` §4 由独立复算脚本守护（每次 apply 必跑），但那是**一次性验证**，不是常驻回归测试。

真正的诱惑是「加一个测试断言 `1.16e-14 < 1e-9` 且 `4.15e-7 > 1e-9`」——但 `tests/test_sphere.py` 已被 `a2-a3-a4` 占用（其 A4 要在该文件新增角度域偏差上界测试），再动产生竞争编辑；且这类断言的探测价值有限（它守护的是 mpmath 与实现的差，不是本 change 的行为）。

**留作 future scope**：为「`< 1e-9` 类声明必须带 frame 标注」建立机械 lint（扫 `openspec/specs/**` 中出现 `< 1e-N` 邻近是否含 frame 关键词）。`scripts/` 当前空闲，技术上可实施；但这是治理条款级扩展，超出本次措辞修正 scope。归档 change 的 Decision 4 同样留下过同类未守护的禁令（「MUST NOT be paired」至今无机械 guard），两次都不扩 scope 是有意的。

**[并发 session 在 gate 运行期间改写工作树]** —— 本 change 实施期间实测：`uv run pytest` 得到 `206 passed` 而非 `33deb9b` 记录的 `204`，`git diff e5fec3a` 显示 `CLAUDE.md` / `governance` / `wayfinder` / `tests/test_beta.py` / `tests/test_sphere.py` 均已被改动，而 `git log` 显示 HEAD 仍是 `e5fec3a`。即：**并行 session 正在同一工作树上落盘**，只是尚未提交。

缓解：(a) 本 change 的 commit **只包含自己的两个路径**（`openspec/specs/decompmoe-skeleton/spec.md` + 本 change 目录），不吞并 peer 的未提交工作；(b) 复跑 `_apply_live.py` 确认本 change 的 L98 编辑未被 peer 覆盖（`git diff --numstat` 仍为 `1 1`，且 block == delta block）；(c) `tasks.md` §5.1 / §5.7 / §5.8 的措辞已改为「**本 change 零贡献**」而非绝对数字断言，避免把并发漂移写成自己的成果或缺陷。

**教训**：gate 的绝对基线数字（`204 passed`、`governance identical`）**只在独占工作树上成立**。多 session 并行时，应断言「本 change 的 diff 不含 X」而非「X 未被改动」。

---

## Risks / Trade-offs

**[只修一半，spec 内部仍不自洽]** —— req-6 补了 frame 标注，`wayfinder` req-11 与 `governance` 的同款缺陷仍在。接受：内部一致性不值得用「污染 peer delta」去换。Phase 2（Decision 2 解锁后）闭合缺口。

**[`a2-a3-a4` 未重同步即归档 → A5 被静默回退]** —— 本 plan 最高影响风险。缓解：`tasks.md` §5 审计任务把它变成可检测失败；`archive/2026-09-28-fix-a1-a5-…/` 是现成重施来源；用户负责通知该 session。

**[L98 行长进一步恶化]** —— 该行已极长，本次再插入一个长括号从句。接受：spec 现行体例就是「每个 Requirement 一行散文」，拆行属结构性改动。缓解：插入收敛为**单个括号**，且全部数字复用仓库既有值。

**[实施期工具陷阱（已实测，勿重复踩）]**：
- `mpmath.betainc(a, b, x)` 3 参形式**不是**正则化下不完全 beta；`betainc(a, b, x, regularized=True)` 在本点返回的是**上尾**（N_e=16 处给 `0.875`，而 `I_x` 应为 `0.125`）。真值必须用 `betainc(a, b, 0, x) / beta(a, b)`——这与 `_betainc_regularized` 的构造一致（`sphere.py` L81-117：积分 / `exp(log_beta)`）。**第一次验证脚本用错调用形式，得到的残差是 `2.25e-01` 量级而非 `4.15e-07`**，是「先核对函数定义再套验证」而非「先套验证再看数字」的典型反例。
- 用 Python 文本模式整体重写 spec 时，`open(..., 'w')` 会把 `\n` 翻译成 `\r\n`（Windows）。本文件在 HEAD 本身即为全 CRLF，故**未**引入换行符污染；但**行数**从 623 降到 622 暴露了另一个问题：以剥离尾部空行的 block 覆盖 `lines[start:end]` 会**吃掉块尾的空行分隔**。修复方式不是 `git checkout`（被权限门禁拒绝），而是按 delta 逆推证明块边界后用定点替换补回，并以 `git diff --numstat` 应为 `1 1` 收口。

---

## Migration Plan

单步、无回滚分支：

1. 脚本从 live `decompmoe-skeleton/spec.md` 抽取 req-6 block，施加 2 处断言替换，生成 `specs/decompmoe-skeleton/spec.md` delta（三层验证）。
2. 由 delta block 反向证明等价性后写入 live spec L98。
3. 跑全部 gate（§ tasks.md）。
4. 单 commit on `dev`。
5. archive。

回退：`git revert` 单个 commit 即可，delta 制品保留在 archive 目录中可追溯。
