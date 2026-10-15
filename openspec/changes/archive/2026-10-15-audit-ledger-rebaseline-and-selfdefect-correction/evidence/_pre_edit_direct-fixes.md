# direct-fix 桶：已定位问题清单（32 条）

> 本文件只收录 `bucket == direct-fix` 的条目。另有五桶 —— `opsx-change`（见同级 `lists/opsx-changes.md`）与 `conflict` / `archive-only` / `context` / `user-decision` —— 记录在 `context/` 下，不在此文件。

**测量基线**：HEAD = `dde0e1d`（`git rev-list --count HEAD` = 261 commits）。本清单所有 evidence 均在该 commit 复算，行号复核以 `git show HEAD:<path>` 取 blob 为准。
**性质**：这是**已定位问题的存目**，不是处置方案表。读者用它判断「哪里有问题」，如何处置由人另行决定；因此全文不给出改法、目标值、优先级或处理顺序。
**输入**：`.audit/gradual-review-2026-10-07/_work3/c1/classified.json`（`items` 共 88 条；本桶 32 条）。

---

## 速览

| ref | 分类 | severity | location | 问题一句话 |
|---|---|---|---|---|
| **FIX-008** | **DIR-1** | CRITICAL | `scripts/lint_pointer_detector.py:345` | POSIX 相对路径拼接后直接 `read_text`，该文件必然不存在 |
| **FIX-009** | **DIR-1** | CRITICAL | `scripts/pointer_scan.py:832-841` | 同一路径拼接后紧跟 `exists()` 静默跳过，`scan()` 静默返回空列表 |
| **FIX-010** | **DIR-1** | MAJOR | `scripts/lint_pointer_detector.py:322`、`:336` | 两条 `check` 测的不是同一个量（`live_actionable` vs `live`） |
| **FIX-012** | **DIR-1** | MAJOR | `scripts/lint_no_dead_defensive.py:37-51,61,69` | 三条 PATTERNS 硬编码 arity=2，全仓唯一实例三条正则全部无匹配 |
| **FIX-013** | **DIR-1** | MAJOR | `scripts/lint_no_line_pointers.py`（作用域与六条正则） | 310 条引用中 302 条被计入「unqualified」跳过，exit 0 覆盖不足六分之一 |
| **FIX-014** | **DIR-1** | MINOR | `scripts/run_gates.py:815` | 门禁以 `sys.executable -m pytest` 调用，继承启动解释器 |
| **FIX-002** | **DIR-2** | MAJOR | `tests/test_distance.py` + `tests/test_beta.py`（`distance.logit` 全部求值点） | 符号翻转变异下 493 测试仍全绿，`logit` 测试族对符号零判别力 |
| **FIX-003** | **DIR-2** | MAJOR | `tests/test_extraction.py:496-544`、`:438`；`tests/test_extraction_phase.py:169` | 三个测试 docstring 声称守护近零/空胞语义，两变异下均保持绿色 |
| **FIX-004** | **DIR-2** | MAJOR | `src/decompmoe/extraction.py:171-176` | EMA 分支近零回退全量测试零覆盖，且该分支在 float32 下近乎不可达 |
| **FIX-017** | **DIR-2** | MAJOR | `src/decompmoe/schedule.py:131-133` + 三处测试 docstring | 四处引号型 Scenario/Requirement 标题全库解析失败 |
| **FIX-005** | **DIR-2** | MINOR | `tests/test_extraction.py:616` | 该测试靠数据依赖的浮点精确抵消触发分支，20 万次抽样仅 31.39% 落入阈值下 |
| **FIX-025** | **DIR-2** | MINOR | `src/decompmoe/metrics.py` 五个退化分支 | CG/D_chord/R_H/MCI/SP 的退化分支全部零覆盖 |
| **FIX-043** | **DIR-2** | MINOR | `tests/test_a3_contract_alignment.py:600,601` | 以裸 `==` 钉定浮点值，prior finding F-11 自 2026 年起逐字存在 |
| **FIX-018** | **DIR-3** | MAJOR | `openspec/specs/wayfinder/spec.md:602,608`；`src/decompmoe/viz.py:1,3-4` | req-25 无任何 deferral 措辞，deferral 只存在于代码 docstring |
| **ARC-002** | **DIR-3** | MINOR | `src/decompmoe/`；`tests/test_sphere.py:251` | 「球面几何自洽」依赖的两个量在 `src/` 中均无实现 |
| **FIX-016** | **DIR-3** | MINOR | `src/decompmoe/metrics.py:73-75` | 全仓唯一残留的过期数字：注释写 75，spec 与代码均已到 76 |
| **FIX-019** | **DIR-3** | MINOR | `src/decompmoe/viz.py:1`；`tests/test_beta.py:291` | 24 处裸 `Req N` 无 capability 限定，至少三处编号即已错指 |
| **FIX-026** | **DIR-3** | MINOR | `tests/test_beta.py:131-132` | 测试侧 β₀ 字面量与 spec canonical 闭式在第 17 位有效数字上不同 |
| **FIX-045** | **DIR-3** | MINOR | `openspec/specs/decompmoe-skeleton/spec.md:491` | 单行 1658 字符同时承载容差公式与旧界作废标记 |
| **FIX-015** | **DIR-4** | MAJOR | `openspec/changes/archive/2026-09-23-07-.../tasks.md` | 786 个受追踪 blob 中唯一一个无法 UTF-8 解码 |
| **FIX-021** | **DIR-4** | MAJOR | `openspec/changes/**` 430 份散文制品 | 69 处引用指向 6 个不存在的 anchor id |
| **FIX-023** | **DIR-4** | MAJOR | `wayfinder/tickets/A6b-1.md:35`、`:119` | Resolution 实际采纳的 β 方案与 Question 段不同，无 `(historical` 标注 |
| **FIX-030** | **DIR-4** | MAJOR | `wayfinder/map.md:67` | 声称 Scenario 计数 103 是 `34b445a` 的值，HEAD 为 105 |
| **FIX-031** | **DIR-4** | MAJOR | `openspec/changes/**` 与 `openspec/specs/**` | 100 处裸路径引用写作 `wayfinder/spec.md`，该路径在仓库历史中从未存在 |
| **FIX-032** | **DIR-4** | MAJOR | `openspec/changes/archive/**` 32 个 change 的 `tasks.md` | 167 个未勾选 `- [ ]` 框，归档状态下完成度字段与实际不符 |
| **FIX-035** | **DIR-4** | MINOR | `openspec/changes/` 下两个 0 文件目录 | 69 处引用指向两个被 `.gitignore` 排除的空壳目录 |
| **FIX-044** | **DIR-4** | MINOR | `wayfinder/map.md:54,55,45`；`wayfinder/tickets/A5-3.md:28,33` | 四处 `(historical, …)` 标注粒度彼此不一致 |
| **FIX-027** | **DIR-5** | MAJOR | `.audit/README.md:11-29`、`:22-28` | 索引描述 2 个子目录，实际 5 个；索引写于 14–18 天前 |
| **FIX-028** | **DIR-5** | MAJOR | `.audit/wayfinder-opsx-code-review/README.md:37`、`:7`、`:56-60` | 推进量称 30 commit / 265 文件，实测 84 / 412 |
| **FIX-036** | **DIR-5** | MAJOR | `.audit/wayfinder-opsx-code-review/context/06-known-false-positives.md:15,42` | 同一文件对「被证伪数」给出 10 与 17 两个数字，7 条差额无解释 |
| **FIX-038** | **DIR-5** | MAJOR | `.audit/reviews/` 的 12 个 harness | 6 个无落盘输出，头条 finding 正出自其中之一；2 个覆写既有证据文件 |
| **FIX-040** | **DIR-5** | MINOR | `.audit/audit-verification/README.md`、`.audit/spec-math-audit/README.md` | 三处自报行数与实测差 1；spec-math-audit 另有第三套账 |
| | | | | **本桶合计 32 条** |

排序：**按分类**，分类内再按 severity（CRITICAL → MAJOR → MINOR）、同级内按 ref。severity 是字段不是主键，见下节。

---

## 分类：本桶 32 条的分法

本清单**自成一册**：类号不与任何另一份清单共享，条目不跨文件对照。**分类**回答的是这一条属于哪一类直接修改；**不回答**怎么改、改成什么值、先做哪条 —— 改法、目标值、优先级、处理顺序仍全部不在本文件内。类内按 severity（CRITICAL → MAJOR → MINOR）、同级内按 ref 排序。

**severity 是字段，不是排序主键。** 它仍逐条记在速览表与每条的 `**severity**` 行内，但不再决定条目的归属与次序 —— 决定归属的是**分类**。

| 类 | 判据 | 成员 | 条数 |
|---|---|---|---|
| **DIR-1** | 落点是 `scripts/**` 门禁脚本自身 | FIX-008 / FIX-009 / FIX-010 / FIX-012 / FIX-013 / FIX-014 | **6** |
| **DIR-2** | 落点是 `tests/**`，且与 `src/` 的对应分支构成配对 | FIX-002 / FIX-003 / FIX-004 / FIX-017 / FIX-005 / FIX-025 / FIX-043 | **7** |
| **DIR-3** | 落点是 `src/**`，目的是与既有 spec 文字对齐 | FIX-018 / ARC-002 / FIX-016 / FIX-019 / FIX-026 / FIX-045 | **6** |
| **DIR-4** | 落点是 `openspec/**` 与 `wayfinder/**` 的归档 / 治理文档 | FIX-015 / FIX-021 / FIX-023 / FIX-030 / FIX-031 / FIX-032 / FIX-035 / FIX-044 | **8** |
| **DIR-5** | 落点是 `.audit/**` 制品自身的自陈数字 | FIX-027 / FIX-028 / FIX-036 / FIX-038 / FIX-040 | **5** |

| | | **本桶合计** | **32** |

### 不重不漏（本桶内，实测）

- **无重**：本桶 32 条 ref 两两互异；各类成员集合与速览表 `分类` 列逐类相等（6 + 7 + 6 + 8 + 5 = 32）。
- **无漏**：32 条 == `_work3/c1/classified.json` 中本桶的 32 条，集合完全相等（json-only 0 / list-only 0）。
- **口径**：每条在三处一致出现 —— 速览表 `分类` 列、所属小节的 `## 分类` 标题、条目的物理顺序；三者可逐条对照。

### 本节明确不覆盖的范围

`classified.json` 共 88 条，另 48 条在 `conflict`(22) / `archive-only`(12) / `context`(9) / `user-decision`(5) 四桶。这 48 条**不在本文件的 `## 附：` 之前，也不参与上面的归口计数**；它们的桶定义与分布记录在 `context/07-verdict-taxonomy.md` §1（实测：该文件记录的是四桶的**定义与条数**，48 条的逐条 ref 未在 `context/*.md` 中全量点名 —— 22 / 48 被点名，其余以桶级计数登记）。因此本节的「40 条不重不漏」是对**两份清单**的陈述，不是对 88 条的陈述。

---

## 分类 DIR-1 · 门禁脚本（6 条）

### FIX-008 — CRITICAL

- **location**：`scripts/lint_pointer_detector.py:345`
- **artifact**：`scripts/lint_pointer_detector.py`
- **problem**：该行把 POSIX 风格相对路径 `rel` 用 `rel.replace("/", "\\")` 拼进 `Path`，随后 `read_text`。在 POSIX 上路径分隔符 `\\` 不是分隔符，整串被当作单个文件名，该文件必然不存在。缺陷自 `34b445a` 起逐字未变。
- **analysis**：影响面大于报告所述：报告称「第 6 节及以后的检查从未运行」，实测更严重——崩溃发生在第 5 节内部，使第 5 节的部分检查在 POSIX 上要么空转通过要么成为唯一目击者（见 FIX-010 的执行序）。缺陷本身在 HEAD 存活是可验证事实；但 POSIX 上的实际退出码与 traceback 原文在本轮无法取得（Windows 环境），故本项的运行时后果保持 UNVERIFIABLE。
- **consequence**：POSIX 平台上该检测器在第 5 节中途崩溃，其后各节的检查全部不产生结论。
- **evidence**（测于 `@dde0e1d`）：静态 —— `git log 34b445a..HEAD -- scripts/lint_pointer_detector.py` 为 0 commit，`git diff HEAD --` 该文件为空；L345 逐字为 `txt = (REPO / rel.replace("/", "\\")).read_text(encoding="utf-8")`（本轮经 `git show HEAD:` 复核确认）。失败为确定性的而非概率性的：`git ls-tree -r --name-only HEAD` 共 786 条，名字含反斜杠者 0 条。缺失的 POSIX 证据（声明保留 UNVERIFIABLE）：Linux/CI 上 `run_gates.py` 的真实退出码、崩溃后 stdout 尾部、任何 POSIX 文件系统上的 traceback 原文；Windows 上无法构造该路径（NTFS 以 `\\` 作分隔符，会 `OSError [Errno 2]`），故只能以 `PurePosixPath.parts` 论证。
- **severity**：CRITICAL
- **status**：UNVERIFIABLE
- **crossrefs**：FIX-009 / FIX-010 / CTX-010
- **source_ledger**：A7, A8, B4

---

### FIX-009 — CRITICAL

- **location**：`scripts/pointer_scan.py:832-841`（`scan()` 内 `p = root / rel.replace("/", "\\")`，其后 `if not p.exists(): continue`）
- **artifact**：`scripts/pointer_scan.py`
- **problem**：与 FIX-008 同病但表现相反：同样的路径拼接之后紧跟 `exists()` 静默跳过，于是在 POSIX 上 `scan()` 不崩溃而是静默返回空列表。
- **analysis**：这一处把 FIX-008 的「响亮崩溃」变成「静默空转」，是本轮因果链被重排的根因：崩溃之前，第 5 节的两条相反检查已在无任何文件被读取的情况下被判定。实测送进循环的 80 个 tracked files 中实际读取 0 个、被 `exists()` 静默跳过 80 个、`scan()` 返回 `[]`。报告称「唯一缺陷在 lint 文件里」被证伪：缺陷同时存在于门禁编排层。
- **consequence**：POSIX 上指针扫描静默返回空，下游据此判定的检查得到的是空集合而非真实结果。
- **evidence**（测于 `@dde0e1d`，静态复核）：本轮经 `git show HEAD:scripts/pointer_scan.py` 逐行确认：`scan()` 起于 L832，循环内 L835 为 `p = root / rel.replace("/", "\\")`、L836–837 为 `if not p.exists(): continue`、L841 为 `return dedupe(sites)`。POSIX 行为由结构论证 —— 实测送入 80 个 tracked files、读取 0 个、跳过 80 个、返回 `[]`（80 = `len(tracked_files(REPO))`）。同样保留 UNVERIFIABLE：POSIX 上 `scan()` 静默返回空后的完整 stdout 尾部未取得。
- **severity**：CRITICAL
- **status**：UNVERIFIABLE
- **crossrefs**：FIX-008 / FIX-010
- **source_ledger**：A8

> **本轮复核**：`scripts/pointer_scan.py` @HEAD 共 844 行，L832 为 `def scan(root: Path, files=None):`，与上文所引范围 `:832-841` 一致。

---

### FIX-010 — MAJOR

- **location**：`scripts/lint_pointer_detector.py:322`（`check len(live_actionable) == 0`）与 `:336`（`check len(live) > 0`）
- **artifact**：`scripts/lint_pointer_detector.py`；`.audit/DecompMoE-逐级review.md:388,390`
- **problem**：两条检查测的不是同一个量：`:336` 测 `len(live)`（含 historical），`:322` 测 `len(live_actionable)`。两约束联立等价于 `historical ≥ 1`，因此报告所称「设计上永远无法成立」不成立。报告把 `live` 误读为 `live_actionable`，该误读在 `34b445a` 的 baseline 上即已成立，不是时效问题。
- **analysis**：报告的因果断言「`run_gates.py` 永远红」被 HEAD 实测证伪（Windows 上 exit 0，493 passed）；该断言在 baseline 当时为红，是因为当时 historical 站点恰为 0，属树状态而非设计后果。缺陷因此是潜伏而非触发：门禁今天同时通过「零 actionable」与「≥1 站点」两条，只因历史站点重新出现。执行序上更严重的一点是，在 POSIX 上 `:322` 会**空转通过** —— 检测器一个文件都没读，却报「产品树干净」，而 `:336` 是唯一目击者。若按报告 §9 的方向处理 `:336`，POSIX 上的响亮失败会被替换为 `:322` 的静默假绿。第 4 节用 `scan_commit()`、第 6 节用 `tracked_files()`，两者都跨平台且不经过 `scan()`，故都无法观测该破损。
- **consequence**：门禁的通过条件依赖 `historical ≥ 1` 这一树状态；该约束在 POSIX 上退化为对空集合的判定。
- **evidence**（测于 `@dde0e1d`）：实测 section 5 @HEAD 完整输出为 `sites=5 actionable=0 historical=5 files=3`，四条 PASS；5 个站点全部为 historical。第 4 节实测 `sites=224 actionable=209 historical=15 files=24`，与 Windows 逐位相同。报告 `:388`/`:390` 的「永远无法成立」/「永远红」断言与该输出冲突。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-008 / FIX-009
- **source_ledger**：A7, A8

> **本轮复核**：`scripts/lint_pointer_detector.py:322` 逐字为 `check("product tree has zero actionable pointers",`（条件行紧接其后）、`:336` 为 `len(live) > 0,` —— 与上文一致。

---

### FIX-012 — MAJOR

- **location**：`scripts/lint_no_dead_defensive.py:37-51`（三条 PATTERNS，全部硬编码 arity = 2）、`:61`（`JUSTIFIED_EXEMPTIONS = []`）、`:69`（`SRC_DIR.glob("*.py")` 非递归且从不扫 `tests/`）；唯一未覆盖的实例在 `src/decompmoe/schedule.py:48-51`
- **artifact**：`scripts/lint_no_dead_defensive.py`；`src/decompmoe/schedule.py`
- **problem**：该 lint 今日 exit 0 且输出 `OK (no anti-patterns found)`，但全仓唯一的 `try/except` 死防御实例对它的三条正则逐条无匹配：三条 PATTERNS 全部写作 `except\s*\( <恰好两个异常名>\s*\)`，而 `schedule.py:50` 的 `except (TypeError, ValueError, OverflowError)` 有三个名字且 `ValueError` 后是逗号。
- **analysis**：该 lint 的绿由「无匹配」产生，而非由「无该反模式」产生 —— 这是本轮与 FIX-010 同构的一类失效：空转的绿灯。此外三处设计事实彼此未被任何一方声明为差异：作用域非递归（今日递归恰等于 glob 故尚为潜在）、从不扫 `tests/`、以及 `JUSTIFIED_EXEMPTIONS` 为空表 —— 后者与 `lint_no_line_pointers` 明文声明「NO exemption table」的政策相反。全仓唯一的真实死防御实例是用户工作树里 `gating.py` 那个源码注释自承为 no-op 的 `torch.where` 包装，属人工发现，该 lint 今日报 OK。
- **consequence**：该 lint 的绿灯来自「无匹配」而非「无反模式」；三处作用域/豁免表的设计差异无任何一方声明。
- **evidence**（测于 `@dde0e1d`，静态复核）：本轮经 `git show HEAD:scripts/lint_no_dead_defensive.py` 逐行确认 —— 三条 PATTERNS 分别为 `(ValueError, ZeroDivisionError)`（L40）、`(ValueError, RuntimeError)`（L44）、`(TypeError, ValueError)`（L48），均硬编码恰好两个名字；`:61` 为 `JUSTIFIED_EXEMPTIONS: list[tuple[str, int, str]] = []`；`:69` 为 `for path in sorted(SRC_DIR.glob("*.py")):`。对 `schedule.py:50` 的 `except (TypeError, ValueError, OverflowError) as exc:` 实测三条正则全部返回 False。实跑输出 `OK (no anti-patterns found)`，exit 0。今日 `src/decompmoe` 下 14 个 `.py`，递归与非递归计数相同。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-023
- **source_ledger**：B4, B5

---

### FIX-013 — MAJOR

- **location**：`scripts/lint_no_line_pointers.py`（作用域 `SCAN_ROOTS` @`:81`、`SCAN_SUFFIX` @`:82`、正则 `RE_ANCHOR` @`:122` / `RE_HEADING` @`:123` / `RE_REF_HASH` @`:126` / `RE_REF_PLAIN` @`:130` / `RE_REF_WORD` @`:132` / `RE_PATH_CAPABILITY` @`:147`）；实跑输出行「unqualified references skipped: 302」
- **artifact**：`scripts/lint_no_line_pointers.py`
- **problem**：C4「引用可解析」检查的 310 条引用中有 302 条被计入并跳过，未被判定；该 lint 的 exit 0 因而覆盖不足六分之一的引用可解析性。
- **analysis**：该 lint 与 FIX-012 相反 —— 它有意识地在无 spec 可识别时 exit 1（C2/C3/C4 不允许空转通过），但「unqualified」这条逃逸路径本身没有上限与分类，被跳过的 302 条中有多少是真破损，本轮无法判断。这正是 CTX-001 中「未声明测量约定」的一例：一个既非计数也非容差的测量口径（什么算可解析的引用）被声明在代码里却没有被声明在被引用的契约里。
- **consequence**：C4 的可解析性判定覆盖 8/310；逃逸路径无上限、无分类，被跳过者中是否含真实破损本轮不可判定。
- **evidence**（测于 `@dde0e1d`，实跑）：exit 0，输出 `35 file(s) scanned, 3 spec(s)`；`placeholders skipped: 8`；`unqualified references skipped: 302`。本轮复核 `git show HEAD:scripts/lint_no_line_pointers.py` 确认 `:81` = `SCAN_ROOTS = ("openspec/specs", "src", "tests")`、`:82` = `SCAN_SUFFIX = (".md", ".py")`、`:97` = `SELF_TEST_PATTERNS = _ps.SELF_EXCLUDE`（无豁免表，政策见 `:50–53`）、`:122/123/126/130/132/147` 六条正则与上文逐一相符。保留 UNVERIFIABLE：被跳过的 302 条 C4 引用是否掩盖真实破损。
- **severity**：MAJOR
- **status**：ledger 无独立 `status` 字段；条目正文自带一条保留的 UNVERIFIABLE（被跳过的 302 条的性质未判定）。
- **crossrefs**：CTX-001 / FIX-012
- **source_ledger**：B5

---

### FIX-014 — MINOR

- **location**：`scripts/run_gates.py:815`（`_run([sys.executable, "-m", "pytest", "-q"])`）
- **artifact**：`scripts/run_gates.py`
- **problem**：门禁以 `sys.executable -m pytest` 调用 pytest，继承启动门禁的解释器；用系统 Python 运行同一条命令失败于 `No module named pytest`（exit 1，`GATE FAIL: 1 gate(s)`）。因此门禁的绿是解释器的性质，不止是树的性质。
- **analysis**：后果是「通过」这一信号不可单独解读：同一棵树、同一 HEAD，在不同解释器下给出相反的门禁结论。这与 `run_gates.py` 自带的 `GATE RESULT INVALID`（exit 2，区分「报红」与「不知道」）在语义上相邻，但覆盖的是另一维度 —— exit 2 处理的是工作树在运行期间移动，本项处理的是解释器在运行前就不是门禁预期的那个。两者都属「结果的成立条件未被记录」，是 CTX-001 的一例变体。
- **consequence**：门禁的「通过」信号不可单独解读；同一棵树在同一 HEAD 下于不同解释器给出相反的门禁结论。
- **evidence**（测于 `@dde0e1d`，实测）：仓库 venv 下 `python scripts/run_gates.py` → exit 0，`GATE OK`，493 passed 1 skipped；系统 Python 下同一命令 → `No module named pytest`，exit 1。`git show HEAD:scripts/run_gates.py:815` 逐字复核为 `_run([sys.executable, "-m", "pytest", "-q"])`。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CTX-001 / FIX-011
- **source_ledger**：B5

> **本轮复核**：`scripts/run_gates.py:814` 为 `if not args.skip_pytest:`、`:815` 为 `_run([sys.executable, "-m", "pytest", "-q"])`、`:816` 为 `if rc == 0:` —— 与上文一致。

---


---

## 分类 DIR-2 · 测试与实现配对（7 条）

### FIX-002 — MAJOR

- **location**：`tests/test_distance.py:50`、`:62-74`、`:104`（`distance.logit` 的全部求值点）；`tests/test_beta.py:175-196`（内联式 `test_logit_range`）；`tests/test_beta.py:198,223,305`（额外三条内联）
- **artifact**：`tests/test_distance.py`；`tests/test_beta.py`；`src/decompmoe/distance.py:33`
- **problem**：把 `src/decompmoe/distance.py:33` 的 `beta * (inner - 1.0)` 翻转为 `beta * (1.0 - inner)` 后，493 个测试仍 493 passed / 1 skipped，与基线逐条相同。全仓 `distance.logit` 仅 2 处求值，均落在 `inner = 1` 这一两种写法给出同一结果的退化点上；`test_distance.py:78` 的梯度断言只比较范数，而范数在两种实现下都是 `|β|`。
- **analysis**：这是本轮唯一机理完全闭合的判别力缺陷：阳性对照变异（另处改动）被 `test_distance.py::test_logit_zero_at_aligned` 抓住，证明 harness 有能力检出该文件的改动，故「存活」是真实盲区而非测试整体失效。结构上有 7 条测试对该符号翻转免疫（4 条直接以 `distance` 为主语或触及 logit 语义，另 3 条在 `test_beta.py` 内联同样公式）。报告只指出 `test_logit_range` 一条失明，实测是整个 logit 测试族均无判别力 —— 即符号是 `src/decompmoe/distance.py` 的可观测契约，却无任何测试对它取值。
- **consequence**：`distance.logit` 的符号取向在 `src/` 中是自由变量，而没有任何测试对其取值；全仓两处求值点恰好落在两种实现不可区分的退化点上。
- **evidence**（测于 `@dde0e1d`）：三次运行 —— A4-mutate 的 `control_run.txt` = 493 passed 1 skipped；`mutant_run.txt`（符号翻转）= 493 passed 1 skipped；`sentinel_run.txt`（另一处变异）= 1 failed 492 passed。B4-code §4 以 `M1 = beta*(1.0−inner)` 复跑得 3 failed / 490 passed，与基线逐条相同（捕获数 0）；M2 sentinel = 1 red。影子归因用两个避开退化点的探针：行为探针 `logit(e₁, −e₁, β=4.0)` 得 −8.0 vs +8.0，梯度探针 `dlogit/dC` 在 `C = c = e₁` 处得 `+[4,0]` vs `−[4,0]`。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-001
- **source_ledger**：A4, B4

> **本轮复核**：`src/decompmoe/distance.py:33` 逐字为 `return beta * (inner - 1.0)` —— 与上文一致。`tests/test_beta.py:175` 为 `def test_logit_range() -> None:`、`:191` 为内联式 `logits = beta_val * (inner - 1.0)`，`:198` 为 `def test_grad_C_bound()`、`:223` 为 `def test_grad_gamma_bound()`，三处与上文一致；但上文所列第三条内联 `tests/test_beta.py:305` 在 HEAD 是空行（L301–304 是 `test_max_grad_per_gamma_phase4_closed_form` 的断言块，`:307` 起为 `def test_max_grad_per_gamma_phase4()`），该行号未落在内联公式上。

---

### FIX-003 — MAJOR

- **location**：`tests/test_extraction.py:496-544`（`def` 恰在 496 行；夹具 L523 `X = torch.zeros(T, d_c)`）；`tests/test_extraction.py:438`（`test_empty_cell_preserves_centroid`）；`tests/test_extraction_phase.py:169`（`test_empty_cell_falls_back_to_the_previous_centroid`）；对照 `src/decompmoe/extraction.py:171`（`use_old = norm < 1e-9`）与 `:189` 的 `atol=1e-6`
- **artifact**：`tests/test_extraction.py`；`tests/test_extraction_phase.py`；`src/decompmoe/extraction.py`
- **problem**：三个测试的 docstring 都声称守护近零 / 空胞语义，但两个空胞守卫测试在删除守卫、用 spec 明令禁止的 `clamp_min(1e-6)` 作分母这两个变异下均保持绿色；近零分支测试的零张量夹具使被守护分支永不进入。
- **analysis**：空胞守卫两测试的失明有解析证明：守卫生效时 `candidate = α·c + (1−α)·c = c`，守卫移除时 `candidate = α·c`，两者经 `normalize` 都得 `c/‖c‖`，对任意 `α∈(0,1)` 与任意 `c` 范数恒等；12 种配置下守卫 ON/OFF 的最大分歧为 1.192e-07，低于 `:189` 的 `atol=1e-6`。`tests/test_extraction.py:461` 虽写 `atol=1e-12`，但只检查第 0 行（非空专家），根本没有采样被守护的行。报告把机理表述为「变绿只因尺度不变性」—— 尺度不变性确为机制，但 `torch.equal(normalize(0.9·c₀), c₀)` 实测为 False（差 1.192e-07），故是尺度不变性与默认 `rtol=1e-05` 两个缺陷栈叠才使测试为绿。严重性因此高于报告的「容差掩盖」刻画：观测量在当前夹具下不可观测，而非仅被容差放宽。
- **consequence**：三个测试的 docstring 做出未被兑现的守护承诺，读者据此认为该分支有覆盖；实测观测量在当前夹具下根本不被采样。
- **evidence**（测于 `@dde0e1d`）：猴补丁抓 `torch.nn.functional.normalize` 在 `extraction.py:173` 的唯一调用点，按 `extraction.py:171` 的判据重推，抓到张量与重推值 `torch.equal` → True（探针无侵入，493 测试在探针下全绿）。实测 `n_i=[4,4,0,0]`、`‖mean_n‖=0`、`‖candidate‖=[0.900000095367, 0.899999976158, 1.0, 0.999999940395]`、`use_old` 全 False，与报告逐位吻合；漂移实测 1.1920928955078125e-07。变异 M1（删 `torch.where(n_i>0, mean_n, centroids)`）与 M3（`clamp_min(1e-6)`）下两个测试均绿。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-001 / FIX-005
- **source_ledger**：A3, A4

> **本轮复核**：`tests/test_extraction.py:496` 逐字为 `def test_near_zero_candidate_fallback() -> None:`、`:523` 为 `X = torch.zeros(T, d_c)`、`:438` 为 `def test_empty_cell_preserves_centroid()`、`:461` 为 `assert torch.allclose(out[0], centroids[0], atol=1e-12),` —— 与上文一致。`tests/test_extraction_phase.py:169` 为 `def test_empty_cell_falls_back_to_the_previous_centroid() -> None:` —— 一致。`src/decompmoe/extraction.py:171` 为 `use_old = norm < 1e-9` —— 一致；但上文所称「`:189` 的 `atol=1e-6`」在 `src/decompmoe/extraction.py` 中不存在：`atol=1e-6` 在该文件全文 0 次命中（该文件共 251 行），L189 逐字为 `return torch.where(`。HEAD 上 `atol=1e-6` 的实际出现位置在测试侧，`tests/test_extraction_phase.py:189` 逐字为 `assert torch.allclose(out[e], centroids[e], atol=1e-6),`。上文按存目原样保留该 location。

---

### FIX-004 — MAJOR

- **location**：`src/decompmoe/extraction.py:171-176`（EMA 分支的 `use_old` 判据）；测试侧唯一两个真触发测试 `tests/test_extraction.py:547` 与 `tests/test_extraction.py:616`，触发的都是 `extraction.py:188` 的 Phase-4 另一分支
- **artifact**：`src/decompmoe/extraction.py`；`tests/test_extraction.py`；`tests/test_extraction_phase.py`
- **problem**：EMA 分支的近零回退在全量测试中零覆盖；对唯一自由参数做 200 万点扫描后其可达最小范数仍高于 `1e-9` 阈值约 37 倍，即该分支在 float32 实现下近乎不可达。
- **analysis**：报告未捕获这一条。证据分两层：插桩全量 493 个测试，记录每次 `CentroidDriver.step` 调用，EMA_090/095/099 三相共 1012 次调用触发 0 次，candidate 范数最小仅 0.707491，比阈值高 7.07e8 倍；可达性分析显示根因是 masked-mean 缩放 `s` 的残差量级（`1 − 0.90` 在 binary64 下为 0.09999999999999998，0.9 不可表示，`0.9c + 0.1(−9c)` 残留 O(1e-8)），而 Phase-4 分支用「同值减两次」可精确抵消，故两分支在数值可达性上不等价。后果是该分支的语义在当前实现与当前测试下均无任何执行覆盖 —— 既无测试触及，也几乎无法被测试触及。
- **consequence**：EMA 分支的近零回退语义在当前实现与当前测试下均无执行覆盖；该分支的可触发性依赖输入分布的浮点巧合。
- **evidence**（测于 `@dde0e1d`）：pytest 插件插桩全量 493 测试，`EMA_090` = 1007 次调用 / 0 次 near-zero 触发，`EMA_095` = 2 / 0，`EMA_099` = 3 / 0，`PROJECTED_SGD` = 6 / 2（10 个测试、1012 次 EMA 调用、触发 0）。对缩放 `s` 的 200 万点扫描，最优 `‖candidate‖` = 3.725290e-08，仍高于 1e-9 约 37 倍。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-003 / FIX-005
- **source_ledger**：A3

> **本轮复核**：`src/decompmoe/extraction.py:171` 逐字为 `use_old = norm < 1e-9`、`:172–174` 为该分支的 `torch.where` 返回、`:188` 为 Phase-4 分支的 `use_old = norm < 1e-9` —— 与上文一致。`tests/test_extraction.py:547` 为 `def test_near_zero_candidate_fallback_phase4() -> None:` —— 一致。
>
> **D3 更正（2026-10-11）**：上一版本复核在上句之后接着写「但上文所引 `tests/test_extraction_phase.py:616` 在 HEAD 不存在：`tests/test_extraction_phase.py` @HEAD 共 251 行，该行号越界」。该诊断**方向反了**：缺陷不是行号越界，而是**文件写错了**。`tests/test_extraction.py` @HEAD 第 616 行逐字为 `def test_phase_4_sgd_near_zero_candidate_fallback() -> None:` —— 即上文要引的测试确实存在，只是不在 `test_extraction_phase.py` 而在 `test_extraction.py`。`test_extraction_phase.py` 中不存在任何 near-zero / fallback 测试（grep `near_zero|fallback` 零命中）。上文全部 6 处引用的原值为 `tests/test_extraction_phase.py:616`，现均记为 `tests/test_extraction.py:616`。

---

### FIX-017 — MAJOR

- **location**：`src/decompmoe/schedule.py:131-133`（引用 Scenario「Phase-2 entry γ reset places β^param in the cap-saturated region」）；`tests/test_loss.py:21-22`（「L_lb closed form on uniform routing」）、`tests/test_loss.py:296-297`（「L_sep closed form degenerate boundary」）；`tests/test_sphere.py:1003-1004` 与 `:1011`（「Output norm bounded by [1 − 2ε, 1]」，附截断式 Requirement 名「Spherical L2 Normalization」）；实际标题在 `openspec/specs/wayfinder/spec.md:671` 与 `openspec/specs/decompmoe-skeleton/spec.md:488`
- **artifact**：`src/decompmoe/schedule.py`；`tests/test_loss.py`；`tests/test_sphere.py`；`openspec/specs/wayfinder/spec.md`；`openspec/specs/decompmoe-skeleton/spec.md`
- **problem**：四处引号型 Scenario / Requirement 标题在全库解析失败。其中 `tests/test_sphere.py:1003` 引的 `[1 − 2ε, 1]` 区间已被 `openspec/specs/decompmoe-skeleton/spec.md:491` 明写 obsolete，等于把一条已作废的界当作现行规范依据引用。
- **analysis**：报告只举了 `schedule.py` 一条，实为四条（口径 A 恰好 4 处）。更值得注意的是成因差异：`schedule.py:132` 的悬空是归档 `c928fc0` 新增引用时改题造成（baseline 不悬空），其余三条在 baseline 即悬空，故 F-03(iii) 是一类（4 条）而非孤例。归档未处理这条指针 —— 它把 Scenario 改了标题而没有更新指向它的代码。`tests/test_sphere.py` 一处的严重性高于其余三条，因为它引用的规范内容被同一份 spec 显式标作作废。
- **consequence**：四处引号型标题引用无法解析到现行 spec；其中一处所引内容被 spec 自身标作作废，读者据此引用的界不成立。
- **evidence**（测于 `@dde0e1d`）：`git show HEAD:src/decompmoe/schedule.py:132-133` 逐字为「Rationale (Spec Req 24 "Phase-2 entry γ reset places β^param in the / cap-saturated region" Scenario, per change」；实际标题 `openspec/specs/wayfinder/spec.md:671` 为「#### Scenario: Phase-2 entry γ reset saturates the operational clamp (float32 frame)」。`cap-saturated` 全库 0 命中（作为被引用串；B2 另测得 1 次命中即该引用自身）。11 处引用中 10 处精确命中，四条为失配项。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-018 / FIX-019
- **source_ledger**：A8, B4

> **本轮复核**：`openspec/specs/wayfinder/spec.md:671`、`openspec/specs/decompmoe-skeleton/spec.md:488`（逐字为「#### Scenario: Output norm equals 1.0 for `‖z‖₂ ≥ ε` (and 0 for `z = 0`)」）、`tests/test_loss.py:21-22` 与 `:296-297`、`tests/test_sphere.py:1003-1004` 与 `:1011` 全部与上文一致。

---

### FIX-005 — MINOR

- **location**：`tests/test_extraction.py:616`（`test_phase_4_sgd_near_zero_candidate_fallback`）
- **artifact**：`tests/test_extraction_phase.py`
- **problem**：该测试触发其声称守护的分支，靠的是 `grad[0] = centroids[0]/1e-2` 使 `candidate[0] = centroids[0] − 1e-2·(centroids[0]/1e-2)` 这一数据依赖的精确抵消；20 万次随机单位向心抽样中仅 31.39% 落在 `‖candidate‖ < 1e-9` 以下，换 `torch.manual_seed` 后有约 69% 概率不再触发。
- **analysis**：对照 `tests/test_extraction.py:547` 用 `centroids[2] = 0.0` 构造性精确抵消，本测试的抵消是浮点巧合而非结构性保证，故其守护力随输入分布变化而静默消失，且消失时不会有任何失败信号 —— 分支未被进入与分支行为正确在断言层面不可区分。
- **consequence**：该测试的守护力随输入分布变化而静默消失；消失时无失败信号，且「分支未被进入」与「分支行为正确」在断言层面不可区分。
- **evidence**（测于 `@dde0e1d`）：seed 0 下插桩 `norms = [0.0, 1.0, 0.999999940395, 1.0]`，分支确实触发；20 万次随机单位向心抽样中 31.39% 落入阈值以下；换 seed 约 69% 概率不触发。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-003 / FIX-004
- **source_ledger**：A3

> **本轮复核**：`tests/test_extraction.py:547` 逐字为 `def test_near_zero_candidate_fallback_phase4() -> None:` —— 与上文一致。
>
> **D3 更正（2026-10-11）**：上一版本复核在此之后接着写「上文所引 `tests/test_extraction_phase.py:616` 在 HEAD 不存在：该文件 @HEAD 共 **251** 行，该行号越界（超出文件长度 365 行）」。此处有两处错误，均已更正：
> 1. **诊断方向错**。不是行号越界，而是**文件名错**。`tests/test_extraction.py` @HEAD 第 616 行逐字为 `def test_phase_4_sgd_near_zero_candidate_fallback() -> None:` —— 上文要引的测试就在这里。`tests/test_extraction_phase.py` @HEAD 全文 **251 行**（splitlines），其内 `near_zero` / `fallback` 零命中。
> 2. **「超出文件长度 365 行」是虚构数字**。`tests/test_extraction_phase.py` @HEAD 实为 251 wc-l / 252 splitlines —— 616 既不超出 251 也不超出 252，365 这个数在任何口径下都不对应任何文件。该数字已删除，不予保留。
>
> 上文全部 6 处引用的原值为 `tests/test_extraction_phase.py:616`，现均记为 `tests/test_extraction.py:616`。

---

### FIX-025 — MINOR

- **location**：`src/decompmoe/metrics.py` 的退化分支 —— CG 的 `numel()==0`、D_chord 的 `N_e<2`、R_H 的 `n<2`、MCI 的 `T_n≤0`、SP 的全死
- **artifact**：`src/decompmoe/metrics.py`
- **problem**：上述五个退化分支全部零覆盖。与 FIX-003 的区别在于：此处没有任何测试 docstring 声称守护这些分支，故属覆盖缺口，而非「说谎测试」。
- **analysis**：把这一条与 FIX-003 分开记录，是因为两者的性质不同：说谎测试的 docstring 主动做出一个未兑现的承诺，读者会被误导；纯覆盖缺口不产生虚假承诺，只是这些分支的行为在当前实现下无任何执行证据。相邻的 `UR([])` 触达点则有覆盖 —— `tests/test_a3_contract_alignment.py::test_ur_single_step_matches_the_spec_closed_form` 实测触达，故不属本项。
- **consequence**：五个退化分支在当前实现下无任何执行证据；与 FIX-003 的「说谎测试」不同，此处不产生虚假承诺。
- **evidence**（测于 `@dde0e1d`）：A3 对全量测试插桩记录 `metrics` 调用；CG `numel()==0`、D_chord `N_e<2`、R_H `n<2`、MCI `T_n≤0`、SP 全死均 0 次触发；`tests/test_a3_contract_alignment.py::test_ur_single_step_matches_the_spec_closed_form` 触达 `UR([])`。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-006
- **source_ledger**：A3

---

### FIX-043 — MINOR

- **location**：`tests/test_a3_contract_alignment.py:600,601`
- **artifact**：`tests/test_a3_contract_alignment.py`
- **problem**：该处断言 `UR(zeros) == 0.0` 是以裸 `==` 钉定的浮点值，prior finding F-11 自 2026 年起仍逐字存在于同一行，未闭合。
- **analysis**：同类问题的规范侧对照：`CLAUDE.md` §6 第 8 条与 req-gov-1 要求浮点闭式用 `pytest.approx(value, abs=...)`、整数闭式用裸 `==`。本项落在两侧之间 —— 0.0 是浮点字面量但其语义是被定义为精确的退化值，故该断言是否违规取决于 req-gov-1 的二分是否覆盖「定义为精确但以浮点书写」这一形态。该二分未声明这一情形，是 CTX-001 在断言风格上的一例。prior finding 跨议题无闭合记录这一点本身与 CFL-010 是同一模式。
- **consequence**：req-gov-1 的整数/浮点二分未声明「定义为精确但以浮点书写」这一形态，本项落在该二分未覆盖的区间内。
- **evidence**（测于 `@dde0e1d`）：B5a §3 记录 F-11 `UR(zeros)==0.0` 仍在，同行 `tests/test_a3_contract_alignment.py:600,601`。req-gov-1 的二分规则见 `openspec/specs/governance/spec.md` L7–L65。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-020 / CFL-010 / CTX-001
- **source_ledger**：B5a

> **本轮复核**：`tests/test_a3_contract_alignment.py:600` 逐字为 `assert float(metrics.UR(torch.zeros(16))) == 0.0`、`:601` 逐字为 `assert float(metrics.UR(torch.zeros(4, 16))) == 0.0` —— 两行均为裸 `==` 钉定，与上文一致。`:598` 为 `metrics.UR([torch.zeros(2, 3, 16)])`，`:599` 为注释行。

---


---

## 分类 DIR-3 · 实现与 spec 文字对齐（6 条）

### FIX-018 — MAJOR

- **location**：`openspec/specs/wayfinder/spec.md:602`（req-25「MUST provide a production-ready visualization toolchain with six modules」）与 `:608`（「each of the six modules is available without bespoke scripting」）；`src/decompmoe/viz.py:1`（docstring 写「Req 21.」）、`:3-4`（「Real implementations are deferred to a §6/§7 waiver change (per CLAUDE.md §7 Out-of-Scope)」）、`:23,30,37,44,51,56`（6 个 render/write 全为 `...`）；`tests/test_viz_protocols.py:3,23`（同样写 Req 21）；`openspec/specs/decompmoe-skeleton/spec.md:366`（req-14 只登记「six Protocol stubs」）；`openspec/changes/archive/2026-08-19-add-decompoe-skeleton-with-tdd-tests/design.md:20`
- **artifact**：`src/decompmoe/viz.py`；`openspec/specs/wayfinder/spec.md` req-25；`openspec/changes/archive/2026-08-19-.../design.md`
- **problem**：req-25 是 8 项落地率登记中唯一未登记的缺口：其 Requirement 与唯一 Scenario 中无任何 deferral / waiver / stub-only 措辞，deferral 只存在于代码 docstring。且该 docstring 指向的 §6/§7 waiver change 从未存在 —— 全仓 `waiver` 仅 2 处命中，均源自 2026-08-19 那次 change 里同样把该工作推迟给同一个不存在 change 的 Non-Goals 陈述。
- **analysis**：即 2026 年 8 月的一处不存在引用被复制传播进了代码，跨越两个月仍作为唯一 deferral 记录存在。`viz.py:1` 的「Req 21」亦错 —— 可视化条款实为 req-25，wayfinder req-21 是「禁 shared expert」；该 5 行文件内因此有两条悬空引用，`tests/test_viz_protocols.py:3,23` 重复同一错误编号。这一缺陷类别（指向不存在制品的语义引用）正是 `lint_pointer_detector.py` / `lint_no_line_pointers.py` 意在捕获的类别，而二者的作用域限于行号锚点与引号型标题，不管语义引用 —— 故它能通过全部门禁。req-25 与 skeleton req-14 处于 peer capability 关系，后者登记了 stub 存在但从未修订前者，故两 capability 之间对同一对象的登记状态不一致。
- **consequence**：req-25 在其 Requirement 与唯一 Scenario 中无任何 deferral 措辞，唯一 deferral 记录位于代码 docstring 且指向从未存在的 change；两 capability 对同一对象的登记状态不一致。
- **evidence**（测于 `@dde0e1d`）：`git show HEAD:src/decompmoe/viz.py` 第 1 行逐字为 `"""6-module visualization toolchain Protocol stubs (Req 21).`，第 3–4 行为「This module provides ONLY Protocol-level stubs. Real implementations are / deferred to a §6/§7 waiver change (per CLAUDE.md §7 Out-of-Scope).」；`openspec/specs/wayfinder/spec.md:602,608` 逐字如上且无 deferral 措辞。`grep` `openspec/changes/` 的 `waiver|viz\.py|visuali[sz]ation`，唯一 `waiver` 命中为 `archive/2026-08-19-add-decompoe-skeleton-with-tdd-tests/design.md:20`。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-017 / FIX-019 / FIX-012 / FIX-013
- **source_ledger**：A6, B3, B4, B5a

> **本轮复核**：`wayfinder/spec.md:600` 为 `### Requirement: Six-Module Visualization Toolchain`、`:602` 为该 Requirement 正文、`:606` 为 `#### Scenario: Toolchain completeness`、`:608` 为其 THEN 行 —— 与上文一致；`decompmoe-skeleton/spec.md:366` 逐字为 `### Requirement: Six Visualization Module Protocol Stubs` —— 一致；`viz.py:1,3,4,23,56` 与 `tests/test_viz_protocols.py:3,23` 均与上文逐字一致。

---

### ARC-002 — MINOR

- **location**：`src/decompmoe/` 中不存在 versine；`src/decompmoe/` 中不存在 θ_{1/e}（`grep acos src/` 为空）；θ_{1/e} 的唯一可执行处为 `tests/test_sphere.py:251`；定义在 `openspec/specs/wayfinder/spec.md:263` 与 `:251/:280-281`、`openspec/specs/decompmoe-skeleton/spec.md:115`
- **artifact**：`src/decompmoe/**`；`openspec/specs/wayfinder/spec.md`；`openspec/specs/decompmoe-skeleton/spec.md`
- **problem**：报告称为「球面几何自洽」所依赖的两个量在 `src/` 中均无实现：versine 由 θ 算 `1−cos` 替代（差 3.26e-14），θ_{1/e} 只作为测试字面量存在。
- **analysis**：这不是缺陷而是位置事实，归档需要知道的是：MVP 配置的几何自洽判据（θ_Voronoi(16,16) = 67.24° > θ_{1/e}(β=16) = 20.36°）在 `src/` 中没有任何一处以可执行形式求值，它完全由 `tests/test_sphere.py:251` 的一个断言承载。因此该不变量在 `src/` 层面的守护力等于零 —— `src/` 中唯一与 chord 距离相关的量是 `squared_chord`，而 versine 与 θ_{1/e} 都只是它的旁支表述。数值侧全部确认：θ_{1/e}(β=16) = 0.355421201690223492738454683273 rad = 20.3641348063178067525910491309 deg，闭合校验 `cos θ` = 0.9375 = 15/16 精确；余量 θ_V − θ_{1/e} = 0.8181262242294939 rad = 46.8751797573236°，比值 3.30185。
- **consequence**：该几何自洽判据在 `src/` 层的守护力为零，其唯一可执行载体是 `tests/` 中的一个断言；`src/` 中唯一相关量是 `squared_chord`。
- **evidence**（测于 `@c67957b` 与 `@dde0e1d`）：`grep acos src/` 为空；versine 全仓仅在测试中以 `1−cos` 形式出现，差 3.26e-14；θ_{1/e} 的唯一可执行处为 `tests/test_sphere.py:251`。支撑值 β=32 → 14.3615115629165626°、β=64 → 10.1417933656798648°、β=2 → 60.0° 精确。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-020
- **source_ledger**：A1

> **本轮复核**：`tests/test_sphere.py:251` 逐字为 `theta_1_over_e = math.acos(15.0 / 16.0)  # arccos(1 − 1/β) at β=16`；`openspec/specs/wayfinder/spec.md:263` 为 `canonical_voronoi_angle` 的 Requirement 正文；`openspec/specs/decompmoe-skeleton/spec.md:115` 为 `### Requirement: Voronoi Self-Consistency Threshold` 的 `SHALL provide canonical_voronoi_angle(...)` 行 —— 三处与上文一致。

---

### FIX-016 — MINOR

- **location**：`src/decompmoe/metrics.py:73-75`（注释「req-1 pins the public surface at the 75-name union, so … push it to 76」）；对照 `src/decompmoe/__init__.py:13-14` 与 `tests/test_a3_contract_alignment.py:38-62`
- **artifact**：`src/decompmoe/metrics.py`
- **problem**：`metrics.py:73` 的 75 是全仓唯一残留的过期数字：`34b445a` 时 `__init__.py` 的 76 才是代码真值，陈旧的是 `metrics.py` 的 75；HEAD 上 spec 追平代码后，方向反转，`metrics.py:73` 成为唯一未随 spec 更新的记录点。
- **analysis**：该行是「同一对象、三种记录质量」的最佳标本：三处描述同一个 76/77/79 契约 —— `src/decompmoe/__init__.py:13-14` 是规则加数字且正确，`tests/test_a3_contract_alignment.py:38-62` 是规则加 AST 实算加 pin，`src/decompmoe/metrics.py:73-75` 是规则加数字但已漂移。报告称 `src/` 内部自相矛盾属实，但方向被描述反了。次要瑕疵：报告引 `__init__.py:13`，该文字实际在第 14 行。严重性低因为它是一处说明性注释且一眼可核，但它同时是 CTX-001（未声明测量约定）在数值上的标本 —— 注释记录了一个快照而不记录快照的 pin。
- **consequence**：同一 76/77/79 契约在三处以三种记录质量并存，其中一处已漂移；该注释记录快照而不记录快照的 pin。
- **evidence**（测于 `@dde0e1d`）：`git show HEAD:src/decompmoe/metrics.py` 第 73 行逐字为「# Private, NOT exported: req-1 pins the public surface at the 75-name union, so」，L74 续「# exposing the window as a public symbol would push it to 76 and desynchronise」；`__all__` 三计数经 `importlib` 实读 13 个子模块为原始求和 77、去重并集 76（唯一重名 `flops_per_token`）、包级 79；`openspec/specs/decompmoe-skeleton/spec.md:36` 声明 `union/sum/package = 76/77/79`，与代码逐位相等。`metrics.py:73-75` 写于 `a97e3a7`，`d351500` 加入 `gamma_reset_for_phase2` 后漂移。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CTX-001 / ARC-009
- **source_ledger**：A7, A8, B4

> **本轮复核**：`src/decompmoe/metrics.py:73-75` 与 `src/decompmoe/__init__.py:13-14` 均与上文一致 —— L13 逐字为「entries: 76 names, plus the 3 dunders below for 79 in total (req-1).」，即上文正文所称「报告引 `__init__.py:13`，该文字实际在第 14 行」这一瑕疵在本轮实测中未复现：该文字确在第 **13** 行（模块 docstring 的首句在 L12，句尾续于 L13，L14 为 docstring 的收尾 `"""`）。上文按存目原样保留该表述。

---

### FIX-019 — MINOR

- **location**：`src/decompmoe/viz.py:1`；`tests/test_viz_protocols.py:3,23`（Req 21）；`tests/test_beta.py:291`（「Req 22 Operational Domain」，编号与标题矛盾，实为 skeleton req-20 / wayfinder req-24）；`src/decompmoe/` 下 13 个文件共 24 处裸 `Req N`
- **artifact**：`src/decompmoe/**`；`tests/test_beta.py`；`tests/test_viz_protocols.py`
- **problem**：24 处裸 `Req N` 无 capability 限定，而 req-1…req-23 在 wayfinder 与 decompmoe-skeleton 两个 capability 中均存在且语义不同，故裸写无法确定指向；其中至少三处（Req 21 ×3、Req 22 ×1）在编号上就已指向错误的 Requirement。
- **analysis**：这与 FIX-017 是同一缺陷的两种形态：引号型标题引用失败是可检测的，裸编号引用失败是静默的 —— 没有任何检查能判定一个裸 `Req N` 指向了哪个 capability 的哪个 Requirement，因为该信息在文本中不存在。严重性分层：24 处裸写的整体风险是 INFO/MINOR（大部分恰好指向存在的编号），而 `Req 21` 与 `Req 22` 这几处是确凿的错指（viz 的两个文件、`test_beta.py:291`）。
- **consequence**：裸 `Req N` 的 capability 限定信息在文本中不存在，故其指向不可判定，且没有任何检查能判定之。
- **evidence**（测于 `@dde0e1d`）：`git show HEAD:src/decompmoe/viz.py:1` 与 `tests/test_viz_protocols.py:3,23` 均为「Req 21」；`tests/test_beta.py:291` 为「Req 22 Operational Domain」；`src/decompmoe/` 13 个文件共 24 处裸 `Req N`（B4-code §2 口径 B）。req-1…req-23 在 `wayfinder/spec.md` 与 `decompmoe-skeleton/spec.md` 中均存在且语义不同。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-017 / FIX-018
- **source_ledger**：B4

> **本轮复核**：`src/decompmoe/viz.py:1`、`tests/test_viz_protocols.py:3`（「ST-12 / Req 21.」）与 `:23`（「IMPLEMENTATION_STACK must be the 6-element frozenset per Req 21.」）、`tests/test_beta.py:291`（「Phase-4 logit-gradient bound closed-form check (per Req 22 Operational Domain」）全部与上文逐字一致。

---

### FIX-026 — MINOR

- **location**：`tests/test_beta.py:131-132`（字面量 `1.0350582488933886469`）对照 `openspec/specs/wayfinder/spec.md` req-7（`1.035060160968266571803`）
- **artifact**：`tests/test_beta.py`；`openspec/specs/wayfinder/spec.md` req-7
- **problem**：测试侧的 β₀ 字面量与 spec 的 canonical 闭式在第 17 位有效数字上不同，二者的差异来源未被任何制品追溯。
- **analysis**：差异量级（~2e-17 相对）远低于任何被钉的容差，故当前不产生测试失败；但它是 CTX-001（未声明测量约定）在数值上的又一实例 —— 两个数字各自都有其框架，却没有任何制品记录哪一个是哪个框架下的哪个量。保留 UNVERIFIABLE：这一差异是截断、四舍五入还是来自不同的 γ_init 输入，本轮未溯源。
- **consequence**：两个 β₀ 数字各自有其框架，但无任何制品记录哪一个属于哪个框架；差异来源未溯源。
- **evidence**（测于 `@dde0e1d`）：B1 §7 UNVERIFIABLE 第 6 项逐字记录 `tests/test_beta.py:131-132` 的 `1.0350582488933886469` 与 spec 的 `1.035060160968266571803`；`src/decompmoe/config.py:55` 的 `MVPConfig.beta_initial = 1.035060`。
- **severity**：MINOR
- **status**：UNVERIFIABLE
- **crossrefs**：CTX-001 / FIX-030
- **source_ledger**：B1

> **本轮复核**：`tests/test_beta.py:131` 逐字含「instead yields \`β_0 = 1.0350582488933886469\` rather than the spec's」、`:132` 逐字为「\`β_0 = 1.035060160968266571803\`。」—— 与上文一致。`src/decompmoe/config.py:55` 逐字为 `beta_initial: float = 1.035`（字面量 1.035，注释 L53 记「β_0 = 1.0350601609682665718」）—— 与上文所称 1.035060 相符。

---

### FIX-045 — MINOR

- **location**：`openspec/specs/decompmoe-skeleton/spec.md:491`（req-19 的 Scenario 1 的一条 `- **THEN**` 子句，单行 1658 字符；req-19 锚点 @L482、标题 @L484）
- **artifact**：`openspec/specs/decompmoe-skeleton/spec.md` req-19
- **problem**：该行同时承载两职：头部是完整的容差公式与其「DISPLAY FORM, not a normative equality」的限定说明，尾部是旧区间界 `[1 − 2ε, 1]` 的作废标记。全部 1658 字符压缩在一条 THEN 子句内。
- **analysis**：这是 FIX-017 中最严重那条悬空引用的成因侧：`tests/test_sphere.py:1003` 引用的 Scenario 名「Output norm bounded by [1 − 2ε, 1]」正是这一行尾部作废标记所否定的对象，而现行标题为「Output norm equals 1.0 for ‖z‖₂ ≥ ε (and 0 for z = 0)」。作废标记与被作废的标题同处一行，使「旧界仍可达」在文本层面比「旧界已作废」更容易被检索命中。行长度本身还触发 58 个 `REQUIREMENT_TOO_LONG` 警告中的一部分 —— 即 FIX-011 中 `--strict` 省略所豁免的那一类。
- **consequence**：作废标记与被作废的标题同处一行，使「旧界仍可达」比「旧界已作废」更易被检索命中；该行长度亦落入 `REQUIREMENT_TOO_LONG` 警告集。
- **evidence**（测于 `@dde0e1d`）：`openspec/specs/decompmoe-skeleton/spec.md:491` 头部逐字为「the Scenario heading's "equals 1.0" is a DISPLAY FORM, not a normative equality — the normative claim is the bound below … |pow(2).sum(−1) − 1.0| ≤ γ_{d_c} := (d_c − 1)·u / (1 − (d_c − 1)·u) ≤ d_c·eps where eps = 2.220446049250313e-16 is the float64 unit roundoff」，尾部逐字为「The prior [1 − 2ε, 1] interval bound from the OLD + ε formula is obsolete」；`tests/test_sphere.py:1002-1004` 引用的是后者对应的标题。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-017 / FIX-011
- **source_ledger**：B3

> **本轮复核**：`openspec/specs/decompmoe-skeleton/spec.md:482` 为 `<a id="req-19"></a>`、`:484` 为 `### Requirement: Spherical L2 Normalization — max(…z…, ε) Formula`、`:488` 为 Scenario 标题、`:491` 为该 THEN 子句 —— 全部与上文一致。`tests/test_sphere.py:1003-1004` 与 `:1011-1012` 逐字为「# max(‖z‖, ε) formula monotonicity (skeleton spec Req "Spherical L2 / # Normalization" Scenario "Output norm bounded by [1 − 2ε, 1]").」与「Spec: skeleton "Spherical L2 Normalization" Scenario "Output norm / bounded by [1 − 2ε, 1]".」—— 一致（该标题字符串跨 `:1011–1012` 两行，上文所记 `:1011` 为其起始行）。

---


---

## 分类 DIR-4 · 归档与治理文档（8 条）

### FIX-015 — MAJOR

- **location**：`openspec/changes/archive/2026-09-23-07-fix-spec-territory-seeding-phase-0/tasks.md`（唯一一处非 UTF-8 的受追踪 blob，offset 32 处非法续字节）
- **artifact**：`openspec/changes/archive/2026-09-23-07-fix-spec-territory-seeding-phase-0/tasks.md`
- **problem**：786 个受追踪 blob 中恰有这一个无法 UTF-8 解码：`\xe6\xae` 三字节序列的第三个字节被替换为 `0x3F`（`?`），上下文为 `b'## \xc2\xa7A. wayfinder spec \xe6\xae?(2 MODIFIED + 1 ADDED, ...'`。任何以 utf-8 严格解码遍历制品的统计都会在该文件上抛错。
- **analysis**：该文件是「静默跳过解码失败」这一实现缺陷的唯一受害者，也是审计报告头条数字 24,928 的成因（CFL-001）。它有 15,320 字节、145 个 `\n`、零 `\r`/`\r\n`、无末尾换行、`splitlines` 得 146 行。任何以「能读出来」为前提的计数在此静默丢弃 146 行，而丢弃不产生任何错误信号。本轮用 PowerShell 的 `Measure-Object` 读取同一 blob 亦见字符数 13,825 ≠ 字节数 15,320，即不同工具对该文件给出不同的行/字符数而都不报错 —— 这是该缺陷跨工具传播的直接演示。
- **consequence**：以严格 UTF-8 解码遍历制品的统计会在该文件上抛错；以「能读出来」为前提的计数则静默丢弃其全部行且不产生错误信号；同一文件在不同工具下得出不同的行/字符数。
- **evidence**（测于 `@dde0e1d`）：本轮实测 `git cat-file blob HEAD:openspec/changes/archive/2026-09-23-07-fix-spec-territory-seeding-phase-0/tasks.md` 返回 15,320 字节；`raw.decode('utf-8')` 抛 `UnicodeDecodeError`，position 32–33 非法续字节，上下文逐字为 `b'# Tasks\n\n## \xc2\xa7A. wayfinder spec \xe6\xae?(2 MODIFIED + 1 ADDED, ...'` —— 与上文逐位吻合。B2 普查 786 个受追踪 blob 中恰有 1 个无法 UTF-8 解码；本轮经 PowerShell 复读同一 blob 得 13,825 字符（B2 测得 15,320 字节），差值与损坏区段一致。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CFL-001 / CTX-001
- **source_ledger**：B2, ADJUDICATION

---

### FIX-021 — MAJOR

- **location**：`openspec/changes/**` 的 430 份散文制品（已排除 263 份 `evidence/`）
- **artifact**：`openspec/changes/**`
- **problem**：69 处引用指向 6 个不存在的 anchor id：`req-36` ×39、`req-gov-9` ×20、`req-101`、`req-37`、`req-100`、`req-gov-33`。
- **analysis**：分布高度集中：`req-36` 与 `req-gov-9` 两项占 59 处，占全部悬空 anchor 引用的 85%。`req-gov-9` 对应 governance spec 中确实存在的编号空档（见 FIX-041），故这 20 处是引用了一个从未定义的编号；`req-101` / `req-100` / `req-37` 则超出 wayfinder 的 36 个 Requirement 上界，疑为把 changelist 或 delta 的临时编号写入了散文。这与 FIX-017（引号型标题失配）是不同类别：anchor 引用形式上可解析为 id，但 id 在 live spec 中无定义，故任何按 id 解析的检查都会把「无此 Requirement」与「引用了错误的 Requirement」混为一谈。
- **consequence**：69 处散文引向本树无定义的 anchor id，85% 集中在 `req-36` 与 `req-gov-9` 两项；按 id 解析的检查无法区分「无此 Requirement」与「引用了错误的 Requirement」。
- **evidence**（测于 `@dde0e1d`）：430 份散文制品普查，排除 263 份 `evidence/` 后统计；`openspec/specs/` 三份 spec 的 anchor 覆盖实测 wayfinder 36/36、decompmoe-skeleton 23/23、governance 11/11，无重复 id、无孤儿 anchor，即 69 处引用全部指向本树不存在的 id。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-017 / FIX-041 / CTX-006
- **source_ledger**：B2

---

### FIX-023 — MAJOR

- **location**：`wayfinder/tickets/A6b-1.md:35`（「竞争动力学辅助 β 更新」，位于 Question 段）；同文件 `:119` 的 Resolution 记「β_i (Projected SGD, β 自由学习)」；`:62-71` 的 β_max(t) 硬 ramp 与 `:78-88` 的 box clamp 为其替代物；`wayfinder/tickets/A6b-2.md:19-22` 的 Question 四候选与 `:47-52` 的 Resolution 四信号表
- **artifact**：`wayfinder/tickets/A6b-1.md`；`wayfinder/tickets/A6b-2.md`
- **problem**：该 ticket 在 Resolution 中实际采纳的 β 方案与 Question 段提出的「竞争动力学辅助 β 更新」不同，且全仓该短语在可执行语境下只此 1 行、无 `(historical` 标注、无 supersede 记录。另外 A6b-2 的 Question 列出 4 个候选信号，其中 ④「σ 变化率低于 ε」在 Resolution 的四信号表中零对应且无排除记录。
- **analysis**：报告称方案 1「无决策记录」，实测需分层：Layer 2 四阈值的未实现是有登记的（`openspec/specs/wayfinder/spec.md:377` 的 Deferral note + `tests/test_schedule.py::test_advisory_signals_read_only`，`src/decompmoe/schedule.py:249-263` 的 `advisory_signals` 为纯 passthrough 亦被测试钉住）；真正无记录的只有 `A6b-1.md:35` 那一行。这是 req-gov-2 要求的 `(historical, …)` 标注义务的一个实例缺失，且与 FIX-039 中工作树对该 ticket 的未提交改动方向相反 —— 工作树删除了两处 `(historical, …)` 标注，即当前工作态正在扩大而非缩小这一缺口。
- **consequence**：A6b-1 的 Question 段方案在 Resolution 被取代但无 `(historical` 标注；A6b-2 的 ④ 候选信号无对应的排除记录。
- **evidence**（测于 `@dde0e1d`）：全仓「竞争」仅 4 命中，另 3 处为 archived changes 中「竞争 delta/编辑」同名异义，可执行语境下仅 `A6b-1.md:35` 一行；该行位于 Question 段。`openspec/specs/wayfinder/spec.md:377` 明文 read-only / never auto-trigger 并自带 Deferral note。`src/decompmoe/schedule.py:249-263` 为 passthrough；常量 0.0476 在 `src/`+`tests/` 中仅以 docstring 散文出现一次于 `tests/test_schedule.py:135`，该 docstring 自述「neither appears anywhere in src/ or tests/」。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-039 / FIX-030
- **source_ledger**：B1, A6

> **本轮复核**：`wayfinder/tickets/A6b-1.md:35` 逐字为「- 竞争动力学辅助 β 更新」、`:119` 为「- 训练：c_i (EMA 0.99) + β_i (Projected SGD, β 自由学习)」、`:62-71` 为「### β_max(t) 分段线性公式」及其代码块、`:78-88` 为「### β 更新机制：Box-Constrained Projected SGD（Phase 3+）」及其代码块 —— 全部与上文一致。`openspec/specs/wayfinder/spec.md:375` 为 `### Requirement: Hybrid Three-Layer Phase Triggers`、`:377` 为该 Requirement 正文（含 Layer 2 的 read-only 措辞）、`:379` 为 `**Source:**` 字段 —— 一致。

---

### FIX-030 — MAJOR

- **location**：`wayfinder/map.md:67`（声称 Scenarios = 103）对照 `openspec/specs/wayfinder/spec.md` @ `dde0e1d`（实测 105）
- **artifact**：`wayfinder/map.md`
- **problem**：`map.md:67` 声称的 Scenario 计数 103 是 `34b445a` 的值，HEAD 为 105。这是 CLAUDE.md §8 所述三条传播通道中唯一仍然开放的一条 —— 专为消除 ticket stale 而加的注记，其自身计数已陈旧。
- **analysis**：同一行的其余计数仍准确：Requirements 36、tickets 23 均相符；锚点 38（含 `req-20-mci` / `req-20-source` 两个子锚点）vs 声称 36，差额恰为那两个 `map.md` 未计入的子锚点。通道 (i) MVPConfig β₀ 与通道 (ii) tests `==` stale 均已断（`src/decompmoe/config.py:55` = 1.035；`tests/test_sphere.py:135` = 67.24°；`src/decompmoe/safeguards.py:35-37` 用 `1/(2·N_e)` 且 `tests/test_safeguards.py:196,238,838` 同时覆盖 1/32 与 legacy 1/128）。因此本项是 req-gov-4 三通道监控义务下唯一未闭合的实例，也说明该监控本身的有效性依赖于计数注记被持续维护。
- **consequence**：三传染通道中唯一仍开放的一条；用于消除 stale 的计数注记自身成为 stale 实例，该监控的有效性因而依赖计数注记的持续维护。
- **evidence**（测于 `@dde0e1d`）：`openspec/specs/wayfinder/spec.md` 的 Scenario 计数 @HEAD = 105（@`34b445a` = 103）；Requirement 36、anchor 38（36 Requirement 锚 + `req-20-mci` @L481、`req-20-source` @L485）。通道 (i)：`config.py:55` `beta_initial = 1.035060` vs ticket 的 β₀ ≈ 1.0。通道 (ii)：`test_sphere.py:135` = 67.24° vs ticket 的 52° / 25.75°；`safeguards.py:35-37` 为 `1/(2·N_e)` vs ticket 的 1/128。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-026 / FIX-023 / FIX-044
- **source_ledger**：B1, B3

> **本轮复核**：`wayfinder/map.md` @HEAD 共 109 行；L67 逐字含「落地 21 锚点 / 21 Requirements / 34 Scenarios *(historical, WF-2 工单当时的落地快照；当前实况 23 ticket / 36 锚点 / 36 Requirements / 103 Scenarios，anchor 覆盖 100% 合规)*」—— 与上文所称「`:67` 声称 Scenarios = 103」一致。`openspec/specs/wayfinder/spec.md:481` 为 `<a id="req-20-mci"></a>`、`:485` 为 `<a id="req-20-source"></a>` —— 一致。`src/decompmoe/config.py:55` 为 `beta_initial: float = 1.035` —— 一致。

---

### FIX-031 — MAJOR

- **location**：`openspec/changes/**` 与 `openspec/specs/**` 中的裸 `<capability>/spec.md` 引用共 100 处
- **artifact**：`openspec/changes/**`；`openspec/specs/**`
- **problem**：100 处裸路径引用写为 `wayfinder/spec.md`，而该路径在仓库历史中从未存在 —— `git log --diff-filter=ADR` 对该路径为空。真实路径为 `openspec/specs/wayfinder/spec.md`。
- **analysis**：这一类的严重性在于它与 FIX-021 的 69 处 anchor 悬空在形态上相同（引用了一个不存在的标识符），但检出难度更低：anchor 悬空至少还有一个可枚举的 id 空间，而裸路径引用的错误不在任何 id 空间内，因此任何按 id 枚举的检查都看不到它们。范围普查同时显示：近失 Scenario 标题 60、仅存在于 delta 的 Scenario 标题 21、死 ticket 6（含 `A6b-3.md` 与 `CLAUDE.md`）、死路径 2（`src/config.py`）。即腐烂集中在指针而非内容 —— 归档 change 的 delta 应用本身是健康的。
- **consequence**：100 处引用写向一个从未存在的路径；该错误不在任何可枚举的 id 空间内，按 id 枚举的检查无法观测到它。
- **evidence**（测于 `@dde0e1d`）：430 份散文制品普查（排除 263 份 `evidence/`）得裸 `<cap>/spec.md` 引用 100 处；`git log --diff-filter=ADR -- wayfinder/spec.md` 为空，即该路径从未存在；另得死路径 2 处为 `src/config.py`，死 ticket 6 处。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-021 / CTX-006
- **source_ledger**：B2

---

### FIX-032 — MAJOR

- **location**：`openspec/changes/archive/**` 中 32 个 change 的 `tasks.md`，合计 167 个未勾选的 `- [ ]` 复选框
- **artifact**：`openspec/changes/archive/**`
- **problem**：32 个已归档 change 的 `tasks.md` 中留有 167 个未勾选的 `- [ ]` 框，归档状态下 tasks 与实际完成度不符。
- **analysis**：这构成归档通道的一致性问题：归档的语义是「该 change 已完成」，而完成度字段保留了未完成项。由于归档制品不参与 `openspec validate`，178 个未勾选框在门禁层面完全不可见 —— 这是 CTX-002（五个 lint 中无一检查归档完成度）的一个实例。三次近期归档经独立核实均无未勾选框，故该形态并非当前通道的产物，而是历史累积。
- **consequence**：归档制品的完成度字段与「已归档即已完成」的语义不符；该形态在门禁层面不可见（归档制品不参与 `openspec validate`）。
- **evidence**（测于 `@dde0e1d`）：`openspec/changes/archive/**` 全量扫描 `tasks.md` 得 32 个 change / 167 个 `- [ ]` 框。其中 `2026-10-04-phase2-gamma-reset-ramp-closure`、`2026-10-04-a8-doc-closure`、`2026-10-07-lint-count-baseline-scope-and-gate-set-integrity` 三次近期归档经独立核实无未勾选框。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CTX-002 / CTX-006
- **source_ledger**：B2

---

### FIX-035 — MINOR

- **location**：`openspec/changes/2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` 与 `openspec/changes/fix-review-findings-voronoi-precision-and-lineage` 两个 0 文件目录；被 69 处引用
- **artifact**：`openspec/changes/**`
- **problem**：69 处引用指向两个同名前缀的空壳目录：`fix-review-findings-voronoi-precision-and-lineage` ×56 散在 33 个文件中，`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure` ×13 散在 12 个文件中。两个目录在 `34b445a` 与 HEAD 均为 0 个受追踪文件，且被 `.gitignore` 排除，故 `git status` 无 `??` 条目。
- **analysis**：这一条同时是缺陷与一次对核查方的更正：核查方在会话早期曾断言「报告 §6 称 2 个未归档 change、实为 4」，该断言不成立 —— `git ls-files` 实测 `34b445a` 上受追踪的 active change 恰为 2 个，报告的「2」正确；核查方用文件系统 walk 把两个不被追踪的目录也计入才得出 4。作为缺陷，本项的检出难度与 FIX-031 同源：文件系统 walk 与 `git ls-files` 给出不同的目录集合，而引用者读的是文件系统。这直接印证 CTX-001 的第 8 例（受追踪 vs 文件系统的计数口径未声明）。
- **consequence**：69 处引用指向两个在本树无受追踪文件的目录；文件系统 walk 与 `git ls-files` 给出不同的目录集合，而引用者读的是前者。
- **evidence**（测于 `@dde0e1d`）：`git ls-files` 实测这两个前缀在 `34b445a` 与 HEAD 均为 0 个受追踪文件；`34b445a` 上 `2026-10-04-a8-doc-closure` 有 4 个受追踪文件、`2026-10-04-phase2-gamma-reset-ramp-closure` 有 6 个。`git check-ignore` 确认被 `.gitignore` 排除，故 `git status --porcelain` 无 `??` 条目。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CFL-012 / CTX-001
- **source_ledger**：B2, A7

---

### FIX-044 — MINOR

- **location**：`wayfinder/map.md:54`（只标注 θ_Voronoi 25.75°，同行的 `N_e=64` / Capacity Factor 32x / β schedule 1.0→16 无标注）、`:55`（只标注 θ_Voronoi≈52°）、`:45`（A2-2 修订有正文措辞但无 `(historical` 标记）；`wayfinder/tickets/A5-3.md:28`（「锁定：(S) Standard MoE Scaling」）对照 `:33`（已是 4070 MVP）
- **artifact**：`wayfinder/map.md`；`wayfinder/tickets/A5-3.md`
- **problem**：四处 `(historical, …)` 标注的粒度彼此不一致：有的只覆盖一行中的一个量而放过同一行的其余量，有的只覆盖「事件」而不覆盖被取代的旧值。
- **analysis**：三处 supersede 的可追溯性依次递减：A2-2 去 head 索引有正文措辞（`A1-1.md:44`「A2-2 修订后」）但无 `(historical` 标记；A5-3 的 4070 MVP 覆盖最弱，仅由 `map.md:55` 的 bullet 位置覆盖 `:54`，而 `A5-3.md:28` 自身仍写「锁定：(S)」；A4-1 的 γ 梯度界旧值最弱 —— `map.md:67` 只记述「修正」这一事件，旧值全仓无存，无法从仓内判断被取代的是什么。这与 req-gov-2 要求的 `(historical, <原值>; superseded by …)` 格式的意图相悖：格式要求记原值，而最弱的一处恰恰没有原值。
- **consequence**：四处 `(historical, …)` 标注的可追溯性依次递减，最弱的一处只记「修正」事件而无原值，读者无法从仓内判断被取代的是什么。
- **evidence**（测于 `@dde0e1d`）：`wayfinder/map.md` 共 109 行，四处 `(historical,…)` 位于 L54 / L55 / L66（整条 WF-1 entry）/ L67（整条 WF-2 entry）；`map.md:45` 记 A2-2 去 head 索引 h，`wayfinder/tickets/A1-1.md:44` 有对应正文；`wayfinder/tickets/A5-3.md:28` 与 `:33` 内容如上；A4-1 旧 γ 值经全仓检索无存。解析规则声明：`## Decision` 小节仅 1/23 存在（A6b-1），决议实际落在 `## Resolution`，故一律以 Resolution 指称。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-030 / FIX-023 / FIX-039
- **source_ledger**：B1

> **本轮复核**：`wayfinder/map.md:54` 逐字含「**球面几何自洽**：θ_Voronoi 25.75° *(historical, θ_Voronoi 25.75°; superseded by spec req-11 …」且同行含 `N_e=64` / 「Capacity Factor 32x」/ 「β schedule **1.0 → 16**」；`:55` 逐字含「球面几何仍自洽（θ_Voronoi≈52° *(historical, θ_Voronoi≈52°; superseded by spec req-11 …」；`:45` 为 A1-1 条目行且以「**A2-2 修订**」收尾（A2-2 自身条目在 `:47`）—— 三处与上文一致。上文所引 `wayfinder/tickets/A5-3.md:28` 实测为 `## Resolution` 标题行（该文件逐字「**锁定：(S) Standard MoE Scaling（Mixtral 风格）+ 以下 MVP 默认值**」在 **L30**，「### 1. Dimension Scaling（4070 MVP 终态）」在 **L32**）；上文按存目原样保留 `:28` 与 `:33`。另：上文所引 `wayfinder/tickets/A1-1.md:44`「A2-2 修订后」实测 **L44 为空行**，该文字逐字在 **L45**（`**符号物理维度（A2-2 修订后）：**`），坐标差 1 行；上文按存目原样保留 `:44`。

---


---

## 分类 DIR-5 · .audit 制品自陈（5 条）

### FIX-027 — MAJOR

- **location**：`.audit/README.md:11-29`（顶层索引）与 `:22-28`（audit-verification 子目录清单）；对照 `audit-verification/README.md:15-25`
- **artifact**：`.audit/README.md`
- **problem**：索引描述 2 个子目录，实际 5 个；索引写于 2026-09-19 05:27，比最新子目录早 14 天，比逐级 review 早 18 天。索引所描述的 `audit-verification` 目录下 7 个 `verify_*.py` 与 4 份 log 已于 09-24 删除，该目录今日只有 2 个文件。
- **analysis**：后果是导航性的而非内容性的：从该索引进入的读者永远不知道三个最大制品（`spec-math-audit`、`reviews`、`wayfinder-opsx-code-review`，共 80 文件 / 39,776 行）的存在，且会按索引去找一份已被删除的可执行证据。这与 FIX-028、CFL-008 同源于「`.audit/` 无版本控制因而所有时间性陈述都无法被后续轮次校验」（见 FIX-037）。
- **consequence**：从该索引进入的读者看不到三个最大制品的存在，且会被导向一份已删除的可执行证据。
- **evidence**：文件系统实测（`.audit/` 不在版本控制内，故以 mtime 与 `Get-ChildItem` 为据）：既有 4 子目录 81 文件 / 39,776 行（`.Count`，含空行），顶层文件 2 个 / 620 L，mtime 范围 2026-09-04 → 2026-10-07 19:30；`.audit/README.md` 的 `LastWriteTime` = 2026-09-19 05:27。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-037 / FIX-028 / CFL-008
- **source_ledger**：B5a

---

### FIX-028 — MAJOR

- **location**：`.audit/wayfinder-opsx-code-review/README.md:37`（推进量与文件足迹）、`:7`（范围声明）、`:56-60`（五项免责声明）；`.audit/wayfinder-opsx-code-review/context/07-baseline-drift.md:13,42`（漂移表终止于 2026-10-01 快照）
- **artifact**：`.audit/wayfinder-opsx-code-review/README.md`；`.audit/wayfinder-opsx-code-review/context/07-baseline-drift.md`
- **problem**：README 的推进量称 pin 后已 30 个 commit、累计改动 265 个文件（`src/` 9、`tests/` 13、specs 3、changes 235）；实测 pin=`6593a06` 后为 84 个 commit、412 个文件（`src/decompmoe` 10、`tests/` 18、specs 3、changes 362、`scripts/` 6、`wayfinder/` 8、5 个单例）。漂移表恰有 D01–D10 十行覆盖 `6593a06 → 188b9fb`，README 的 30-commit 数字在 `context/` 中没有任何一行对应。
- **analysis**：该议题内的每一个 `file:line` 都处于 pin 态而无一重新推导，故其全部 265 条位置引用的现时有效性都不可从工件内部判定 —— 这使该议题的证据强度整体依赖一个未被记录的 pin 约定。同一 `README.md:7` 的范围声明另被 CFL-011 推翻。四处并存基线（`6593a06` / `fa2f0dc` / `34b445a` / 仓外 `f8e5b26`）无优先级声明，见 CFL-017。
- **consequence**：该议题全部 265 条位置引用的现时有效性不可从工件内部判定；README 的推进量与实测差 54 个 commit、147 个文件。
- **evidence**：`git` 实测 —— `git rev-list --count 6593a06..HEAD` = 84（`6593a06` 本身为 2026-09-30 01:48:44 的 commit「docs(change): record post-archive completion state + third archive anchor-loss incident」）；`6593a06..34b445a` = 75；`34b445a..HEAD` = 9；`git diff --name-only 6593a06..HEAD` = 412 个文件。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CFL-017 / CFL-011 / FIX-027
- **source_ledger**：B5a

---

### FIX-036 — MAJOR

- **location**：`.audit/wayfinder-opsx-code-review/context/06-known-false-positives.md:15`（记 10 条被结构性反证推翻）与 `:42`（§1 标题写 17 条）；`.audit/wayfinder-opsx-code-review/` 的 `classified.json`
- **artifact**：`.audit/wayfinder-opsx-code-review/context/06-known-false-positives.md`
- **problem**：同一文件对「被证伪的 finding 数」给出 10 与 17 两个数字，7 条差额无解释。另 `classified.json` 有 193 items、main bucket `archive-only` = 76，而该文件只记录 40，即 41 条 `archive-only` 未被记录。
- **analysis**：两处都是登记册与制品本身的失同步，且失同步方向相同：制品比登记册多。被漏记的 41 条 `archive-only` 中，若干条本身是 STILL_REAL 的实体缺陷 —— 即登记册的缺漏会掩盖缺陷而非仅造成文档不准。这与 CFL-009（基线四数互不相容且 finding 与驳回并存）是同一现象在两份文件上的两次出现：登记册的计数没有单一来源，也没有对账步骤。
- **consequence**：登记册的计数没有单一来源与对账步骤，失同步方向为「制品多于登记册」；漏记项中含 STILL_REAL 的实体缺陷，缺漏因而会掩盖缺陷。
- **evidence**：文件系统实测：`context/06-known-false-positives.md:15` 逐字称 108 条原始 finding 里 10 条被结构性反证推翻、19 条被标注为「弃权不是证伪」；`:42` 的 §1 标题写 17 条。`classified.json` 193 items，main bucket `archive-only` = 76，文件记录 40。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CFL-009 / FIX-037
- **source_ledger**：B5a

---

### FIX-038 — MAJOR

- **location**：`.audit/reviews/` 的 12 个 harness —— `_count_entries.py:44-47`（写 `_states_*.txt`）、`_mutation_audit{,2,3}.py`（写 `.json`）；无落盘输出的 6 个为 `_verify_rtol.py`、`_dbg.py`、`_verify_findings.py`、`_validate_survivors{,2}.py`、`_check_lint_regression.py`
- **artifact**：`.audit/reviews/**`
- **problem**：12 个 harness 中 6 个无落盘输出，而头条 finding（F-9 rtol）正出自其中之一；另有 2 个把输出写回 `.audit/reviews/` 自身，覆盖先前的证据文件。
- **analysis**：关键后果是「重跑 ≠ 读取」：`_count_entries.py` 会覆写 `_states_*.txt`，因此这些文件里记录下的计数反映的是 22:52 的文件版本，而非 23:51 的交付版本 —— 这正是 CFL-009 中四个互不相容的基线数字的机械根因。一个审计轮次的结论若只存在于 stdout，则该结论既不可复现也不可被下一轮引用，而下一轮恰恰只能引用落盘件。头号缺陷出自无落盘的 harness 这一巧合，使该缺陷在 10-03 轮与 10-07 轮之间没有任何机器可读的传递路径。
- **consequence**：重跑会覆写既有证据文件，使落盘件中的计数反映的是被覆盖前的版本；只存在于 stdout 的结论既不可复现也不可被下一轮引用。
- **evidence**：文件系统实测：`.audit/reviews/` 共 24 文件，其中 12 个 `.py` harness、4 个 `.json`、2 个 `.txt`、1 份 322 行报告，全部 mtime 2026-10-03 22:41–22:55；`_count_entries.py:44-47` 写 `_states_*.txt`，`_mutation_audit{,2,3}.py` 写 `.json`；`_verify_rtol.py` 91 行，三段式探针（V1 `:18-32` 隐式 rtol vs `rtol=0` 的行为探针、V2 `:37-63` α-swap 变异 vs `test_extraction_phase.py`、V3 `:67-91` 静态普查），无落盘输出。
- **severity**：MAJOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：FIX-022 / CFL-009 / CFL-010
- **source_ledger**：B5a, B5

---

### FIX-040 — MINOR

- **location**：`audit-verification/README.md`（声明 2353）、`spec-math-audit/README.md`（声明 1018 / 592 / 2870 / 4399）、`spec-math-audit/README.md` 内部尺寸表
- **artifact**：`.audit/audit-verification/README.md`；`.audit/spec-math-audit/README.md`
- **problem**：三处 README 自报的文件行数与实测差 1（声明 2353/1018/592，实测 2354/1019/593）；`spec-math-audit` 的尺寸表另有第三套账（声明 1018/592/2870/4399，实测 1019/593/2873/4761）。
- **analysis**：off-by-one 的方向一致（声明值比实测少 1），符合缺末尾换行时的计数约定差异 —— 这正是 CTX-001 第 7 例的实物版本（`cat-all | wc -l` 与 per-file `splitlines` 的差）。单独看是 MINOR，但第三套账的存在意味着同一目录的尺寸在同树内有三份互不相容的记录，读者无法判断哪一份是权威。
- **consequence**：同一目录的尺寸在同树内有三份互不相容的记录，读者无法从工件内部判断哪一份权威。
- **evidence**：文件系统实测（行数按 `(Get-Content <path>).Count`，含空行）：`audit-verification/audit-verification.md` 实测 2354 行 vs 声明 2353；`spec-math-audit` 主报告实测 1019 vs 声明 1018、early report 实测 593 vs 声明 592；`spec-math-audit` 目录合计实测 4761 行 vs 内部表声明 4399。
- **severity**：MINOR
- **status**：ledger 无 `status` 字段。
- **crossrefs**：CTX-001 / FIX-027
- **source_ledger**：B5a, B5

---


---

## 附：本文件的取数与自检

- **取数**：`_work3/c1/classified.json` → `items`（88 条）按 `bucket == 'direct-fix'` 过滤，得 **32** 条；**按分类（`DIR-1`–`DIR-5`）录入**，类内再按 severity（CRITICAL → MAJOR → MINOR）、同级内按 ref。
- **severity 分布**（severity 已是**字段**而非排序主键，故按分类排列后不再连续）：CRITICAL **2**（FIX-008 / FIX-009，同属 `DIR-1`）、MAJOR **18**（FIX-002 / 003 / 004 / 010 / 012 / 013 / 015 / 017 / 018 / 021 / 023 / 027 / 028 / 030 / 031 / 032 / 036 / 038）、MINOR **12**（ARC-002 / FIX-005 / 014 / 016 / 019 / 025 / 026 / 035 / 040 / 043 / 044 / 045）。合计 2+18+12 = **32**，与条目数一致。
- **分类分布**：`DIR-1` 门禁脚本 **6** / `DIR-2` 测试与实现配对 **7** / `DIR-3` 实现与 spec 文字对齐 **6** / `DIR-4` 归档与治理文档 **8** / `DIR-5` `.audit` 制品自陈 **5** = **32**。
- **status 分布**：3 条带 `status` 字段 —— FIX-008、FIX-009、FIX-026 均为 UNVERIFIABLE；另 FIX-013 的正文自带一条保留的 UNVERIFIABLE（被跳过的 302 条 C4 引用性质未判定）；其余 28 条无 `status` 字段。
- **行号复核**：本轮对 32 条的 `file:line` 引用逐条以 `git show HEAD:<path>` 取 blob 核对（`.audit/**` 条目按文件系统实测，因该目录不在版本控制内）。**发现 5 处 ledger 行号与 HEAD 实际内容不符，均按「保留 ledger 原文 + 另起复核注记」处理，未改写上文 location**：

  | 条目 | ledger 所记 | HEAD 实测 |
  |---|---|---|
  | FIX-002 | `tests/test_beta.py:305`（第三条内联公式） | 该行为空行；实落在 `:301-304`（`test_max_grad_per_gamma_phase4_closed_form` 的断言块） |
  | FIX-003 | `src/decompmoe/extraction.py:189 的 atol=1e-6` | 该文件全文 `atol=1e-6` 命中 **0** 次，L189 为 `return torch.where(`；`atol=1e-6` 的实际位置在 `tests/test_extraction_phase.py:189` |
  | FIX-004 / FIX-005 | `tests/test_extraction.py:616` | **D3 更正**：上一版本复核记作「`tests/test_extraction_phase.py:616` 在该文件 251 行内越界」，属诊断方向错误 —— 该行不在 `test_extraction_phase.py`，而是在 `test_extraction.py` @HEAD 第 616 行（逐字为 `def test_phase_4_sgd_near_zero_candidate_fallback() -> None:`）。上一版本另称「超出文件长度 365 行」，该数字不对应任何文件，已删除。 |
  | FIX-016 | 正文称「报告引 `__init__.py:13`，该文字实际在第 14 行」 | `src/decompmoe/__init__.py:13` 逐字即该文字，L14 为 docstring 收尾 `"""`；该瑕疵本轮未复现 |
  | FIX-044 | `wayfinder/tickets/A5-3.md:28`（「锁定：(S) Standard MoE Scaling」）与 `:33`（已是 4070 MVP） | `:28` 为 `## Resolution` 标题行；「锁定：(S) …」实际在 **L30**，「### 1. Dimension Scaling（4070 MVP 终态）」在 **L32** |

  其余条目所引 `file:line` 与 HEAD 快照一致（含 FIX-015 的非 UTF-8 blob —— 本轮实测 `git cat-file blob` 返回 15,320 字节、`decode('utf-8')` 在 position 32–33 抛非法续字节，上下文逐字吻合）。
- **禁用措辞自检**（实测，非事后追述）：对**本文件全部正文**（头部注释 + 速览表 + 分类节 + 32 条条目，即本附录之前全部 **54,343** 字符 / **629** 行）扫描下列 13 类模式 —— `should be` / `should change` / `fix by` / `replace with` / `add rtol` / `use NaN` / `建议` / `改为` / `修改为` / `修复` / `应当` / `推荐` / `patch`。结果：**正文命中 0 处**。分类计数：(a) 引用既有制品原文 **63** 处（其中「引用制品自身的**规范性祈使措辞**」这一子集为 **5** 处，见下方 D3 更正；原记 0 处）；(b) 本文件自身的处置建议（把某物说成应当改成什么、或指名某个函数作为改动对象）**0** 处。
>
> **本字符数写在附录内，而扫描边界排除附录**，故更新它不使该数自我失效。历史值：**54,537**（「归口分组」版，两小时后被「分类」重构取代）、50,779（两个版本加入前）。规则 A 边界本身未变。
>
> **⚠ 「归口分组」已被「分类」取代（2026-10-13 晚）**：本文件曾短暂采用一份与另一份清单**共享**的 `A`–`G` 归口组，现改为**本清单自成一册**的 `DIR-1`–`DIR-5`，条目按类重排。取代理由：共享命名空间迫使读者打开另一份文件才能看全一类，与「两份清单不得混淆」相悖。
>
> **PASS 1 全模式复核（终态）**：`_work3/d5/leak_scan.py` 的 PASS 1 扫 **13 PRIMARY + 11 BYPASS**，本文件正文原始命中 **6** 处，逐条落点与性质如下 —— L6 的 `目标值` / `优先`（头部 L6 免责声明「不给出改法、目标值、优先级或处理顺序」）、**L55 的 `改成` / `目标值` / `优先`**（分类节首句的**排除声明**「**不回答**：怎么改、改成什么值、先做哪条 …… 改法、目标值、优先级、处理顺序仍全部不在本文件内」）、L572 的 `优先`（CFL-017 交叉引用「无优先级声明」）。**按模式族分列：PRIMARY 13 类命中 0，BYPASS 11 类命中 6**，故本附录首行那句「13 类模式命中 0 处」指的是 PRIMARY 族，**未被推翻**。六处全部位于**排除声明**或对既有制品的转述内，(b) 仍为 **0**。
>
> **PASS 1 的计数不可单独作为泄漏指标。** 命中数由 4 涨到 6，全部来自新写的**排除声明** —— 该声明因逐字列举被排除的类别而自命中 `改成` / `目标值` / `优先`。在此模式表下，「声明不做这些事」与「做这些事」不可区分，只能逐处人工裁定；裁定结果为排除声明，故 (b) 不变。引用 PASS 1 数字时必须与裁定结论一同引用。
>
> **选词说明**：分类节用「分类 / 类 / 落点」，不用「建议」。理由不是「建议」一词本身有罪，而是**「分类」精确描述了该节做的事**（指派归属），而「建议」容易被读成提出处置 —— 措辞与实际行为一致，比事后辩解更可靠。

> **D3 更正（2026-10-11）· (a) 类由 0 更正为 5**：上一版本把 (a) 记作 0 处，**该计数为扫描口径造成的假阴性**，不是关于正文的真实断言。原因具体可查：上列 13 个模式是为检出**处置建议**（中英各半的祈使动词）设计的，而 (a) 类的载体是**既有制品原文中以英语书写的规范措辞** —— `MUST` / `ONLY` / `deferred to` 这类词一个都不在那 13 个模式里，因此该扫描**按构造就看不见 (a) 类**，无论正文里有多少处引用。「正文命中 0 处」本身仍然成立（它说的是那 13 个模式），只是它不能推出 (a) = 0。
>
> D3 换用判据「引文是否与既有制品逐字相同」重扫正文，得 (a) 类 **63** 处 —— 这是**机械判据**（凡引文在某个受追踪制品中逐字出现即计入），涵盖代码片段、命令、标识符等一切引用。其中**规范性祈使措辞**这一子集为 **5** 处，覆盖 3 份制品，逐条如下（均已对 `git show dde0e1d:<path>` 逐字核对）：
>
> | # | 本文件中的引文 | 出处 | 逐字核对 |
> |---|---|---|---|
> | 1 | 「MUST provide a production-ready visualization toolchain with six modules」 | `openspec/specs/wayfinder/spec.md:602` | 一致（req-25 正文行首 `The system MUST provide a production-ready visualization toolchain with six modules:`） |
> | 2 | 「each of the six modules is available without bespoke scripting」 | `openspec/specs/wayfinder/spec.md:608` | 一致（`:608` 为该 Scenario 的 `- **THEN** each of the six modules is available without bespoke scripting beyond their public APIs`） |
> | 3 | 「Real implementations are deferred to a §6/§7 waiver change (per CLAUDE.md §7 Out-of-Scope)」 | `src/decompmoe/viz.py:3-4` | 一致 |
> | 4 | 「This module provides ONLY Protocol-level stubs. Real implementations are / deferred to a §6/§7 waiver change (per CLAUDE.md §7 Out-of-Scope).」 | `src/decompmoe/viz.py:3-4` | 一致（与 #3 同源，此处按含 `ONLY` 的整块引） |
> | 5 | `MUST NOT be reported as 0` | `openspec/specs/wayfinder/spec.md:479` | 一致（SP_i 行末「SP MUST NOT be reported as `0`」） |
>
> 这 5 处是 (a) 类而非 (b) 类，判据是：**引文归属于被引制品，本文件只负责转述它，不对它作任何改动主张**。第 1、2、5 条引的是 spec 的规范性 `MUST` 措辞，第 3、4 条引的是 `viz.py` 自身的 deferral 声明 —— 全部是「某处如此写」的事实转述。反向可验：若把这些引文删掉，本文件对应条目失去的正是「被引物原文是什么」这一可核对性，而非任何处置建议。
>
> (b) 类维持 **0**：本轮 D3 逐条读完上述 5 处及其上下文，未见任何一处把被引物说成应当改成什么，也未指名任何函数作为待编辑对象。

  > 本轮初稿曾在此处记「(a) 类共 11 处」并逐条列举 FIX-032 / FIX-038 / FIX-045 等条目为引用命中 —— 该陈述是**在实际扫描之前凭印象写下的**，扫描后被自身实测推翻：正文中 `修复`、`应当`、`建议`、`patch` 四词实为 0 命中，故上表已整体删除。全文模式命中全部落在本附录自身（自本附录标题所在行起，共 **25** 处），成因是本节按要求逐条列出模式名本身，不构成对本文件的处置建议。
  >
  > 另附一次邻接措辞扫描（同样限正文）以覆盖同义绕过：`应当改为` / `建议改` / `应改` / `需改` / `改成` / `更正为` / `统一为` / `目标值` / `优先` / `先改` / `推荐使用` —— 命中 **3** 处，均为非泄漏：(i) L6「不给出改法、目标值、优先级或处理顺序」是本文件的**性质声明**，逐字列举被排除的类别；(ii) L6 同句中的「优先级」；(iii) FIX-028 正文「四处并存基线（`6593a06` / `fa2f0dc` / `34b445a` / 仓外 `f8e5b26`）无优先级声明」—— 此处「优先级声明」指**基线之间孰为准**的声明缺失，是 ledger 对工件状态的描述，不含任何处置次序。

> **D5 复扫（2026-10-12）· (a) 与 (b) 均未变，正文字符数已过时**：D5 轮在 FIX-044 条的「本轮复核」注记中补入 `wayfinder/tickets/A1-1.md` 的坐标核对后，以 D3 的 `leak_scan.py` 原样副本（`_work3/d5/leak_scan.py`）重跑同一判据。正文实测 **575 行 / 51,874 字符**。13 主模式 + 11 绕过模式合计命中 **3** 处：L6 两处（`目标值` / `优先`，即上方归类的 (i)(ii)）与 L285 一处（`优先`，即 FIX-028 的「无优先级声明」，即上方归类的 (iii)）—— **三处与 D3 的归类逐条对应，无一新增**。
>
> 分类计数：**(a) = 63** 处（与 D3 所记相同；D5 补入的引文为中文短句，不满足机械判据的「≥4 个空格分隔词」门槛，故不进入 (a) 统计）；**(b) = 0** 处 —— D5 未在本文件引入任何处置建议、替换值或优先级，新增内容全部是坐标核对与逐字引文。
>
> 唯一过时处：上文「本附录之前全部 **50,779** 字符」现记 **51,874** 字符，增量即 D5 补入的那一句核对。此处登记而不回改上句。
>
> 另：D5 轮对本文件 425 条引用中归属本文件的 121 条逐条判定，得 **97 VERIFIED / 3 CONTENT-MISMATCH / 9 NOT-IN-HEAD / 12 NOT-VERIFIABLE**；3 条 CONTENT-MISMATCH 中 2 条（A-106、A-112）在本附录上表已有留痕且经复核成立，1 条（A-113）由 D5 补入本轮注记。全轮 425 条的合计口径见 `README.md` 速览表末行与 `_work3/d5/residual-audit.md`。
