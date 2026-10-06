# Proposal

## Why

`.audit/wayfinder-opsx-code-review` 的 A-8 清单把 **6** 条问题归入 **user-decision** 桶——问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」是未定语义，故只登记不推进。本 change 落定其中 **4** 条**纯文档面**的裁决（UD-01 / UD-02 / UD-04 / UD-06 / UD-03 共 **5** 项，见 design.md），全部零 spec delta。（复算：`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 中 `### UD-` 条目按主桶筛选；该路径**未版本化**——`git ls-files .audit` → 0——故此基线依赖工作树存在，消失时须改标 `not reconstructible`，见 design.md 顶部的「计数约定」。）

其中两条最紧：

- **UD-04**：`CLAUDE.md` §2 把 `wayfinder/map.md` + 23 tickets 定为第 4 档「参考性、非约束性」，§8 的 2026-08-21 裁决同向；但 §8 的三步修复协议 (a) 又要求 ticket 端必须维护 `(historical, …)` 标注。实测 `openspec/specs/governance/spec.md` 的 `req-gov-4` **clause (1) 已经把这个矛盾收掉了**——它把 advisory 的语义显式收窄为 ticket-edit policy：「tickets MAY be superseded by OpenSpec changes without amending the ticket itself; this is the ONLY meaning of "advisory"」。所以矛盾不在 spec，在 `CLAUDE.md` 的措辞没引用这个 scope 划分。⇒ 只需一次措辞手术。
- **UD-01 / UD-02**：`CLAUDE.md` §4 的三分支架构声明 `dev → main` 与 `dev → release` 通道，但实测 `git merge-base main dev` 退出 1 且无输出（main 的 root 是只含 `.gitignore` + `LICENSE` 的 Initial commit `051f247`，与 dev 无任何共同祖先），`release` 分支在本地/远端均无（决定性两腿：`git for-each-ref refs/heads/release`、`git ls-remote --heads origin release`；reflog / `packed-refs` / `git tag` 三腿仅作辅助，理由见 design.md 的证据力分级），tag 本地与远端均为 0。**规范声称的通道在当前拓扑下跑不通**。（`origin` 的默认展示分支曾指向 `main` ⇒ 从 GitHub 首页进入看到的是一棵与开发线无关的空树；该问题**已于 2026-10-05 修复**，见 design.md 末尾的更正节与本 change 的 `tasks.md` 6.1。）

## What Changes

- **`CLAUDE.md` §4**：在 `release` 行之后加一段「未启用」事实陈述（main 的真实形态、与 dev 无合并关系、release/tag 未建立），**保留三分支架构为 aspirational 规范**，不预设将来是否建 release。**不改写为 dev 单分支**——§4 是专门立的规范，改写会同时牵动 L51 的 `dev` 条目。
- **`CLAUDE.md` §8**：在 2026-08-21 裁决段追加一句，显式引用 `governance` req-gov-4 clause (1) 的 scope 划分——「非约束」= 不得推翻 spec / ticket 文本可不经 amendment 偏离；监控与标注义务不受影响。
- **A-8 报告**：新增 `deferred-evidence` 桶，逐条记录 3 条被 `SECURITY WARNING [Irreversible Local Destruction]` 封条的 hand-back（原结论 / 失效原因 / 前置条件 / 重跑范围）。
- **审计台账登记**：登记 `REVIEW-LEDGER.md` **与** `LOOPS.md` 的位置与状态，**不回流**。

**不做什么（明确的非目标）**：不建 `release` 分支、不打 tag、不做 `dev → main` 合并（含 `--allow-unrelated-histories`）、不回流任何台账文件、不重跑被封条的 agent。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 本 change 的 `.openspec.yaml` 声明 `skip_specs: true`。`governance` req-gov-4 clause (1) **已经**承载了本 change 要对齐的语义；本 change 只让 `CLAUDE.md` 文本与之对齐，**零 Requirement 内容变更**。按仓规不为通过 validate 而造空 delta。）

## Impact

- **文档面**：仅 `CLAUDE.md` 的 §4 与 §8 两处（改动点已逐行核实：L53 `release` 行后、L92 裁决段末）。
- **引用格式**：prose passage 的引用必须是「Requirement 号 + 标题 + ≥8 字符 verbatim 引文」，**禁止行号**（`scripts/lint_no_line_pointers.py` 检查 C1，依 `governance` req-gov-6）。历史行号引用仅在带 marker（`histor` / `pre-this-change` / `was` / prior commit id）时豁免，且豁免按 marker 判定、不按登记表。
- **引用选择**：`CLAUDE.md` §8 只能引 `req-gov-4` **clause (1)**（advisory scope 收窄）。**不得**引 clause 4(a) 作为标注义务依据——兄弟 change `2026-10-04-fix-wayfinder-advisory-drift-a7` 的 design.md D4 已裁定该义务的治理依据是 `wayfinder` req-34。
- **规范面 / 实现面**：`openspec/specs/**` 与 `src/**` 零改动。
- **报告面**：`.audit/` 下的 A-8 报告（该目录被 `.gitignore` 忽略、非版本化）。若该目录在执行时不存在，登记内容落到本 change 的 `design.md` 而非新建报告文件。
- ~~**一处 git 操作**（apply 阶段后置）：`git remote set-head origin dev`，改的是远端默认展示分支指针，不动任何 ref 拓扑。~~ **本条原文有误，已作废**：`git remote set-head` 只写**本地** `refs/remotes/origin/HEAD` 这个 remote-tracking 缓存 ref，**不改远端**；实测执行后 `git ls-remote --symref origin HEAD` 仍返回 `refs/heads/main`，且本地缓存因此与远端事实相反，必须回滚。**真正的修法是** `gh repo edit <owner>/<repo> --default-branch dev`（改远端仓库设置），已于 2026-10-05 执行并经三路复验。完整证据表与「同一命令在两种情形下处置相反」的判据，见 `design.md` 末尾的更正节；`tasks.md` 6.1 记录了执行与复验。
