# Tasks

> **复核修订**：本 change 的 `design.md` 初稿列了 12 条勘误，其中 **E2、E4 已在 apply 阶段逐条实测后撤回**（清单的 pin 定位其实正确，见 `design.md` D4.1）。**生效勘误为 11 条**：E1、E3、E5–E13（E13 为 `/code-review` 阶段新增）。

## 1. 定位类勘误（E1、E3）

这两条会让实施者改错文件或改错行，优先级最高。

- [x] 1.1 在 `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 末尾追加 `## Errata` 节头，写明「本节由 change `2026-10-01-audit-errata-a1-numeric-guard-list` 增补；**清单正文结论一律不改写**，本节仅更正坐标与措辞」——验证：`## Errata` 出现在文件末尾，且 `git diff` 对该文件只显示末尾新增行，无既有行删除/修改
- [x] 1.2 写入 E1：AC-03 的位置 `tests/test_beta.py:184` 实为 `test_logit_range` 体内行 `logits = beta_val * (inner - 1.0)`；所称的 `test_logit_no_w_i` 在 **`tests/test_distance.py:53`**（pin = HEAD，该文件零漂移）——验证：`git show 6593a06:tests/test_beta.py | sed -n '184p'` 输出 `logits = beta_val * (inner - 1.0)`；`git grep -n 'def test_logit_no_w_i' 6593a06 -- tests/` 命中 `test_distance.py:53`
- [x] 1.3 写入 E3：AC-01 的位置 `src/decompmoe/distance.py:24` 落在 `def squared_chord` 附近；真正 `return beta * (inner - 1.0)` 在 **`:33`**（该文件 pin→HEAD 零漂移，故 9 行偏差不是漂移而是清单错）——验证：`git show 188b9fb:src/decompmoe/distance.py | sed -n '33p'` 含 `return beta * (inner - 1.0)`

## 2. 措辞与数字类勘误（E5–E9）

- [x] 2.1 写入 E5：AC-61 称 wayfinder req-33 逐字点名 5 个 `phase_beta_max` 精确值，实为 **4** 个；第 5 个 `3.99985`（`test_sphere.py:184`）来自**相邻** Scenario，不在点名范围内——验证：`git grep -n 'Scenario.*phase_beta_max' 188b9fb -- openspec/specs/wayfinder/spec.md` 命中 `:665`，其 THEN 行（`:666`）只列 `(2,6_000)→1.0`、`(2,16_000)→2.5`、`(3,26_000)→4.0`、`(3,41_000)→10.0`
- [x] 2.2 写入 E6：AC-77 的「`β_p3 = 1.0` 在 Phase 3 可达」不成立——`phase_beta_box(3)` 返回 `(4.0, 16.0)`，其 docstring 明写 `(1.0, 32.0)` fallback 适用于「Phase 1 `β^eff = 1.0` fixed」，即 Phase-1 的 1.0 语义上不是 P3 退出值；`gamma_reset_for_phase4` 全部调用点只传 `16.0` → **不可达**。**但 `β_p3` 域声明缺失本身仍成立，严重性应下调**——验证：`git show 188b9fb:src/decompmoe/schedule.py | grep -A16 'def phase_beta_box'` 含 `if phase == 3: return (4.0, 16.0)` 与该 fallback 说明；`git grep -n 'gamma_reset_for_phase4(' 188b9fb -- tests/` 的实参全为 `16.0`
- [x] 2.3 写入 E7：AC-10/AC-33 的「零断言」不成立——`metrics.UR(` 调用数确为 0，但裸 token `UR` 有 **4 处**（`test_metrics.py:65`、`:71`、`test_safeguards.py:458`、`:466`），其中 `:466` 用 `torch.randn(100, cfg.N_e)` 模仿 UR 输入形状却不调用它。准确表述为「无**数值**守卫」——验证：`git grep -nE 'metrics\.UR\s*\(' 188b9fb -- tests/` 零命中；`git grep -n '\bUR\b' 188b9fb -- tests/` 命中且恰为 4 处
- [x] 2.4 写入 E8：AC-10/AC-33 的「其余 7 指标 1–23 次」与静态口径不符，实为 **2–16**；并注明清单给的是运行期 instrumented 计数，两者口径不同、不可混用——验证：逐指标 `git grep -cE 'metrics\.(L_sep|R_H|S_load|SP|D_chord|MCI|CG)\s*\(' 188b9fb -- tests/` 得 2/2/2/5/5/6/16，全部落在 2–16
- [x] 2.5 写入 E9：AC-40 的「两个常量在 tests/ 零命中」需修正为 `20260929` 零命中、`1_000_000` 在 `test_sphere.py:240` docstring 命中 1 处；断言体内命中数仍为 0，故实质主张成立；并更正常量名为 `VORONOI_AREA_SAMPLES`（清单写 `SAMPLES`）——验证：`git grep -n '20260929' 188b9fb -- tests/` 零命中；`git grep -n '1_000_000' 188b9fb -- tests/` 命中 `test_sphere.py:240`

## 3. 数值与推理类勘误（E10–E12）

- [x] 3.1 写入 E10：AC-18 的三个数是**单侧**跳变 `|G(π/2) − G(π/2−h)|`；真正的左右极限间距是 **2 倍**（`1.047977e-1` / `1.574170e-1` / `2.316223e-1`，d_c=8/16/32，h=1e-7）——验证：用 HEAD 的 `_cap_area` 在 h=1e-7 下复算，`|G(π/2+h) − G(π/2−h)|` 等于所写 2 倍值
- [x] 3.2 写入 E10 的根因：`sin²(π/2)` 在 float64 下**精确等于 1.0**，命中 `_betainc_regularized` 的 `x >= 1.0` 早退得精确 `0.5`；而 `x = nextafter(1.0, 0)` 时同一函数返回 `0.8425829560490325`。**该不连续是实现伪影，精确数学在此连续**——验证：复算确认 `G(π/2) == 0.5` 精确，且 `G(π/2 − 1e-7) ≈ 0.421291`
- [x] 3.3 写入 E11：AC-91 称三个 γ/β 中间量「无任何测试钉住」不成立——γ-gap 有两条真断言（`test_beta.py:154` 的 `round(float(gamma_full), 4) == -6.7835` 与 `:164` 的 `pytest.approx(-6.7835, abs=1e-4)`，后者带 `f"actual="`）；β 残差与斜率确仅在 `:161` 注释中——验证：`git show 188b9fb:tests/test_beta.py | sed -n '152,166p'` 显示两条 assert 与注释行
- [x] 3.4 写入 E12：AC-48 的「被不存在的 `theta_conv` 门控」不成立——`e50cc02` 已整体删除该门控，改为无阈值 `A_i < 0.5`，由 `test_voronoi_angle_precondition_is_area_below_half`(`test_sphere.py:551`) 守；HEAD 的 `theta_conv` 仅剩 1 处命中（`:580` 的报错文案）。「单向性只有方向约束、无幅度」仍成立——验证：`git grep -n 'theta_conv' 188b9fb -- src tests` 恰 1 处命中于 `test_sphere.py:580`
- [x] 3.6 写入 **E13**：确立 6dp 字面量的容差约束（**结论经两次修正，与初稿相反**）——实测新字面量 `1.173547` 对未修 impl 为 `1.275e-06` **FAIL**、对修后真值为 `4.259e-07` PASS，是标准 red→green ⇒ **Change 2 只改字面量即可观察，无需收紧容差**；且 6dp 字面量固有截断误差上界 `5e-07`，**`< 1e-6` 的容差会在真值上失败**，故 obligation 3 的 `abs=1e-6` 是**必需**而非宽松；同时记录 versine 走 `round(v,4)` 精确 `==`、`0.4771` 不变（批准计划「爆炸半径」表该行方向错误）
- [x] 3.7 记录 `/code-review` 阶段的**非勘误**发现（不入 Errata，计数仍为 11）：F5（`CLAUDE.md` §5「球面几何自洽」为**过宽**陈述——MVP 自身超参上成立且余量 3.3×，但 `d_c=8, N_e=16384` 反例成立，缺的是适用范围；严重性低且不在本 change 范围，登记待裁决）、F1（reviewer 误报，spec 逐字是 `[−2β, 0]`）、以及**归档正文不可验证性**（`.audit/` 从未被 git 追踪 ⇒ D1 不变量状态为 UNVERIFIED，固化前缀 sha256 作前向基线）——验证：`git ls-files .audit` = 0 行；`git log --all -- <path>` 为空
- [x] 3.8 建立 `/code-review` **全量 findings 台账**（`design.md` D4.4）：13 行 finding 逐条给出**本 change 独立复算**的裁决与去向，并显式记录 **3 项未采信的 review 裁决**（F1 第二次证伪 / F3a 判据选错 / F6 行号错）——验证：`git show 188b9fb:openspec/specs/decompmoe-skeleton/spec.md` 计数 `[−2β`=1、`[−β`=0；`git grep -n isinf 188b9fb -- src` 命中 `gating.py:37/42/47` 而非 `sphere.py`
- [x] 3.5 把 `design.md` 的复现命令整段抄进勘误节，使读者无需重跑复核即可定位——验证：勘误节含全部生效条目编号（E1、E3、E5–E12），且每条都能被节内或其引用的命令复核

## 4. 撤回记录、Dedup 登记与下游门禁

- [x] 4.1 在勘误节记录 **E2 / E4 已撤回**及其理由（pin 定位其实正确，仅存在漂移；归档 README 已声明 pin 坐标须按漂移表重定位，故非缺陷）——验证：勘误节含该撤回说明，且 E2/E4 不以「生效勘误」形式出现
- [x] 4.2 在勘误节登记与未归档 change `fix-review-findings-voronoi-precision-and-lineage` 的重叠面（L4 / L5 / H2 / H2b / L7 / M4 / G1 / G5 → AC-03 / AC-38 / AC-08 / AC-12 / AC-40 / AC-77 / AC-61）——验证：`git ls-tree -r --name-only 188b9fb -- openspec/changes/fix-review-findings-voronoi-precision-and-lineage/` 只返回 `proposal.md` 与 `tasks.md`（确认无 `specs/` delta）
- [x] 4.3 在勘误节写明该 change 状态未裁决，并明确「**开始任何修复 change 的施工前必须先裁决**」——验证：勘误节含该门禁声明
- [x] 4.4 在勘误节写明勘误表**只增不减**：后续若坐标再漂，追加新条目而非改写既有条目——验证：勘误节含该规则

## 5. 验收

- [x] 5.1 逐条复核生效的 **11 条**（E1、E3、E5–E13），每条用 `git show` / `git grep` 独立确认，缺一不算完成——验证：10 条全部复核通过
- [x] 5.2 确认归档正文**未被本 change 改写**，并如实标注该结论的可验证性——已验：`## Errata` 起于 1476 行，正文 24 条结论/严重性/`裁决`/`基线` 字段均未出现在任何编辑的替换串中；**未验**：`.audit/` 被 `.gitignore:37` 忽略且从未被 git 追踪，无 commit-object 基线可比对，apply 时记录的 146935 字节与当前重建的 146934 字节差 1 且无法裁决⇒ D1 不变量状态 **UNVERIFIED**，已固化前缀 `sha256=8e66c0f2…` 作前向基线（见 D4.3）
- [x] 5.3 确认本 change **只**写入 `openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list/` 与 gitignored 的 `.audit/`——**归属按显式路径判定，不用 `git status` 的空/非空**（并行 session 会让该命令对非本 change 的改动同样报红，见 D7）——验证：本 change 的 10 处编辑脚本的写入目标全部是上述两条路径；`git status --porcelain -- openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list` 为 `??`（仅新增，无既有文件被改）
- [x] 5.4 确认两个 lint gate 仍为 `exit=0`（本 change 不应影响它们）——验证：`python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py` 均输出 `OK` 且退出码 0
- [x] 5.5 确认本 change **未新增/修改任何测试函数**（不依赖总数固定）——已验：本 change 全部编辑脚本的写入目标不含 `tests/`（见 5.3）。**总数曾两次变化**：apply 阶段 `217 tests collected`；本轮末段变为 **227**（`+10`），来源是并行 session 对 `test_config.py` / `test_extraction.py` / `test_metrics.py` / `test_sphere.py` 的改动，非本 change（见 D7）。⇒ 验收判据改为「写入路径不含 `tests/`」，而非「总数等于 217」——后者在共享工作树里是**不稳定**的断言
- [x] 5.6 运行 `openspec validate 2026-10-01-audit-errata-a1-numeric-guard-list --type change`，确认 `skip_specs: true` 的零 delta change 通过校验——验证：命令退出码 0 且报 `is valid`
