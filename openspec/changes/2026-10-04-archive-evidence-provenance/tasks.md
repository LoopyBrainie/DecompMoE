# Tasks — 归档证据溯源修复

状态说明：W1 / W2 / W3 / W4 已实施并验证。W5 按裁决搁置。
**本 change 目前无法通过自己的 archive precondition** —— 新 lint 在真实树上报红
15 处，全部位于**其他 session 的在途 change**（7 处 `2026-10-04-a8-doc-closure`、
8 处 `2026-10-04-phase2-gamma-reset-ramp-closure`）。本 change 自身 0 处。
详见 `tasks.md` §6.2。

## 1. 事实记录（W1）

- [x] 1.1 建 `openspec/changes/2026-10-04-archive-evidence-provenance/`
      （`.openspec.yaml` `schema: spec-driven`）
      Verify: 目录存在且 `.openspec.yaml` 两行
- [x] 1.2 `proposal.md` 承载 A 组（A1–A7、A9–A12）事实，每条带 revision
      Verify: `proposal.md` 含「计数口径声明」小节 + A 组表格
- [x] 1.3 `proposal.md` 写入 **不可复算清单**（A8 `65 → 67`、B7「48 个脏条目」），
      与可复算数字**分区陈述**
      Verify: 检索「not reconstructible from git」应命中 2 行
- [x] 1.4 `proposal.md` 记录 A10 / A11（`.audit` 证人永不入库、且未记 36/23/6 拆分）
- [x] 1.5 `proposal.md` 写入 B 组（B1–B7）与**定性下调**（scoping artifact，非自违反）
- [x] 1.6 `proposal.md` 登记 C 组 `27336a4`，状态明写「本轮不 revert、不改归档」
      Verify: 检索「已知，待独立裁决」
- [x] 1.7 `proposal.md` 声明**不改任何** `openspec/changes/archive/**` 路径
      Verify: `git status --porcelain -- openspec/changes/archive/` 必须为空

## 2. 账本基线三态（W2）

- [x] 2.1 `scripts/run_gates.py`：新增 `worktree_digest(snap)`，以两个**内容** digest
      对比各自空值判定净脏 —— **不用** `status_lines`（`req-gov-8`）
      Verify: `test_worktree_digest_is_none_only_when_both_content_digests_are_empty`
- [x] 2.2 payload 增第 5 字段 `worktree_digest`，与 `written_at_head` 并列
      Verify: 实写后 `sorted(d) == ['change','expect_new','ledger','worktree_digest','written_at_head']`
- [x] 2.3 落盘保持 `newline="\n"`（Windows CRLF 会过不了本仓自己的 `git diff --check`）
- [x] 2.4 `--verify` 三态：digest 非空 ⟹ `EXIT_INVALID`；字段缺失 ⟹ `EXIT_INVALID`；
      digest 为 `null` ⟹ 正常 pass/fail
      Verify: 三个测试各自覆盖一条路径
- [x] 2.5 **`--write` 禁止因工作树脏而拒绝**（D3 的回归守护）
      Verify: `test_ledger_written_on_dirty_worktree_verifies_as_unknown` 断言
      `rc_write == EXIT_OK`
- [x] 2.6 修正既有 fixture：`_write_ledger_file` / `_write_ledger_file_named` 增
      `"worktree_digest": None`（synthetic 基线的语义本就是「净」）
      Verify: `pytest tests/test_run_gates.py` 全绿

## 3. 规范固化（W3）

- [x] 3.1 `specs/governance/spec.md` delta 增 `## ADDED Requirements` → `req-gov-12`
      **不取 `req-gov-9`**（该 id 曾被 `## REMOVED`，复用会让账本无法区分已删除与新增）
      Verify: `openspec validate <name> --type change --strict` exit 0
- [x] 3.2 `req-gov-12` 四条义务 + 五条 Scenario；`Source:` primary 反链为
      backtick 包裹的 `CLAUDE.md`（per `req-34` 的 per-capability dispatch）
- [x] 3.3 第 4 条把 D3 钉进规范：`--write` MUST NOT 因工作树非净而拒绝
      （防止后来者「顺手加固」成闸门）
- [x] 3.4 Requirement 末段要求 anchor 计数**带计数规则**，并要求不可复算数字
      显式标注 *not reconstructible*

## 4. 证据层 lint（W4）— 已实施

- [x] 4.1 裁决 `.audit/**` 扫描目标 → **A1**（改为受版本控制的证据层）
      实测依据：`.gitignore:37` 排除 `.audit`，`git ls-files .audit` = **0 tracked**
      （本地 82 文件）
      Verify: `L.evidence_files()` 不返回任何 `.audit/` / `openspec/specs/` /
      `openspec/changes/archive/` 路径（有测试断言）
- [x] 4.2 `scripts/lint_no_baseline_counts.py`（`req-gov-7` Scenario:352-354
      自动入门禁，`discover_lints()` glob 发现）
      Verify: `uv run python scripts/lint_no_baseline_counts.py` 在真实树上 **RED**
- [x] 4.3 基准 token 集合**显式枚举**（7 类：commit hash / `HEAD` / change 名 /
      Requirement 锚点 / 可复算命令 / 计数口径 / 显式基线词），并在 docstring 给出
      判定标准与理由
      Verify: docstring「WHAT COUNTS AS A BASELINE」小节
- [x] 4.4 豁免走 marker 不走登记表（8 个 marker；**无** registry）
      Verify: `test_exemption_marker_silences_the_report` 5 个参数
- [x] 4.5 **判别性测试**（`design.md` D5，合并前置条件）
      `tests/test_lint_no_baseline_counts.py` = **28 passed**
      - 判别对：同一条真实句子，加基准前 RED、加基准后 GREEN
        （`test_red_on_real_instance_and_green_once_baselined`，
        素材为 `incident.md:25-26` 的**逐字**原句）
      - 含**复刻本 lint 写作过程中真实盲区**的用例：表格行整行跳过、
        fence 状态误判、每计数重复上报、`第 8 条` 误判、
        相邻块的基准错误地压制本块
### 4.x 实施中发现并修正的缺陷（lint 自身）

1. `\b` 置于 CJK 字符之后**永不匹配**（`条` 与后一个字均为 word char）⇒ CJK counter 形同虚设
2. 行内出现 `` ``` `` 即翻转 fence 状态（误判）
3. 表格行被整行跳过 ⇒ 计数表成为盲区（改为：表格块 = 整段 `|` 连续行，含表头）
4. `第 8 条`（子条款引用）被误判为计数 ⇒ 改为**先剥离**再匹配（lookbehind 无法跨空格）
5. `48 / loose 48`（`strict N / loose N` 写法）不被 `\d+/\d+` 匹配 ⇒ 增 `paired counts`

> 缺陷 1–5 由 4.5 的判别性测试抓出。**若只写「lint 通过」而不写判别测试，
> 这些会一起出厂** —— 其中缺陷 1 会让本 lint 对全部中文证据完全失效而仍然 exit 1
> （因英文 ratio 仍触发），即「报红但漏报中文」。

### 4.y 独立复核后补上的修正

复核指出：缺陷 2（原记为「fence 状态误判」）的**测试并不判别** —— 喂入格式良好的
fence 时，错误实现与正确实现返回同一结果。已补 `test_fence_toggle_ignores_inline_backticks`，
其输入把行内 ``` 与真 fence 分开；复核已实测反置实现会被抓住。

复核另指出：缺陷 1–5 的枚举不完整 —— 另有 spec 内部自相矛盾、测试空转、
扫描域未实现 `design.md` D4 判据等。逐条修正见 `design.md` D10 / D11 与本文件 §4.7。

- [x] 4.7 复核 findings 全部处置
      - `req-gov-12`：消除「MUST record a digest」与「digest MUST be `null`」的自相矛盾；
        `null` 明确定义为**已记录的值**而非缺省；补第 4 种 entry 形态（空串/异类型）
      - `req-gov-12` legacy Scenario：把「MUST NOT report a violation」限定为
        **anchor 级**判定；新增 Scenario 规定「根本不是账本」是调用方错误、不得呈现为判定
      - lint 扫描域：由「受版本控制的证据层」改为**按 `GATE_CHANGE` scope 到被归档的 change**
        + `docs/**`（`design.md` D4）
      - `run_gates.py` 模块 docstring：exit 2 的第二个成因（账本无声明基准）写入
      - legacy 补救信息：区分「归档内不可重写」与「在途可重写」
      - lint docstring：补 `处/份/篇/字符`、`wc -l`、heading/fence/表格块三条非计数位规则
      - 补测试：4 种 entry 形态、payload 键集、`_EMPTY_SHA256` 恒等式、
        `status_lines` 不可参与净脏判定、`GATE_CHANGE` 传播与 scope 行为、
        8 个 marker 全覆盖

## 5. 搁置 / 登记

- [ ] 5.1 `27336a4` 归档内改动 —— **本轮不处置**，已在 `proposal.md` C 组登记
- [x] 5.2 A10（`.audit` 作第二证人却永不入库）—— 已在 `proposal.md` A 组登记
- [x] 5.3 A11（`.audit` 未记 36/23/6 拆分）—— 同上

## 6. 门禁

> **本节不复述违规数字。** 复述即制造新的计数 —— 上一版写下「15 处、本 change 0 处」
> 之后，本文件又新增了符合定义的计数，使该数字当场失效（见 `design.md` D11）。
> 实时数字由命令本身产出：
>
> ```bash
> # scope 到本 change（门禁模式）
> GATE_CHANGE=2026-10-04-archive-evidence-provenance \
>   uv run python scripts/lint_no_baseline_counts.py
> # 全仓（独立运行模式）
> uv run python scripts/lint_no_baseline_counts.py
> ```

- [ ] 6.1 detached worktree 上 `run_gates.py --change <name>` exit 0
      **未执行**：用户裁决**暂不提交**，detached worktree 必须指向已提交的 commit。
- [x] 6.2 门禁 scope 已修正
      首版 lint 扫**所有**未归档 change，其红完全由两个他人 session 的在途 change 决定 ——
      这正是 `req-gov-7` Scenario:367 明文要禁的形状（「so that unrelated stale changes
      in the same directory do not determine the result」），也与 `cmd_gates` 对
      `openspec validate` 已有的 scope 做法不一致。现改为按 `GATE_CHANGE` scope 到被归档的
      change（`run_gates.py` 经环境变量传递，**不**用位置参数：另两个 lint 会把位置参数
      当成待扫描路径）。他人 change 的违规在 repo-wide 模式下仍会报出，但在本 change 的
      门禁中不再参与判定。
- [x] 6.3 `pytest` 回归 —— 由命令产出，不在本文件复述总数（见上方 D11 说明）：
      `uv run python -m pytest -q`
- [x] 6.4 `openspec validate <name> --type change --strict` exit 0
- [x] 6.5 `openspec validate --specs --strict` exit 0
- [x] 6.6 五个 lint 在本 change 的门禁 scope 下全部 exit 0：
      ```bash
      GATE_CHANGE=2026-10-04-archive-evidence-provenance \
        uv run python scripts/run_gates.py --change <name> --skip-pytest
      ```
      逐个直跑亦可（未提交时 detached worktree 不可用，见 6.1）
- [x] 6.7 归档未被触碰
      `git status --porcelain -- openspec/changes/archive/` 中的唯一条目
      `2026-10-01-audit-errata-a1-numeric-guard-list/` 的 CreationTime 为 2026-10-01，
      早于本 session，非本 change 产物
- [x] 6.8 跨 lint 交互（复核附带发现，未在本 change 处置）
      新测试中一处 `req-gov-12` token 被 `lint_no_line_pointers` 的 **C4** 报为
      「does not resolve in capability 'governance'」—— 因为该 Requirement 要到本 change
      归档时才进入 live spec。**C4 不查询 historical marker**（`check_c4` 只认
      `is_self_test` 逃逸），故 `pre-this-change` 标记无效。
      本 change 的处置：把该引用改写为散文（测试语义不依赖该 id）。
      **遗留**：`lint_no_line_pointers` 的 C4 无法豁免**前向引用**，因此任何在被扫描
      文件里引用自己即将新增的 Requirement 的 change，在归档前都过不了 C4。
      这是该 lint 的结构缺口，不在本 change 范围，留待独立 change。
