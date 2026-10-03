# Design — 关闭豁免碰撞族与检测器完整性缺陷

## D1. 根因：豁免的单位错了，不是检测的单位错了

上一轮把全部工程量投在**检测**上，并以此宣告收口。复核推翻的正是这个宣告。独立核实确认检测器**能找到**那些站点——它们在报告里，然后被丢弃。

`scan_line` 的最后两行是问题的全部：

```python
for s in sites:
    s.marker = _exempt(line)      # <- 整行一个标记
    s.historical = bool(s.marker)
```

一行可以有十几个 locator。`governance/spec.md:133` 的 `**Source:**` 字段长达 2000 字符，其中一个子句写着 `原话建议 L1358-1359`——`原` 标注的是**那一个** locator——而规则豁免了同行全部 12 个，其中包含 `LOOPS.md` 的三个当前定位符和 `.audit/...` 的当前证据指针。

**决定**：豁免按 locator 判定。`Site` 新增 `pos: tuple`，记录 locator 在行内的半开字符区间；标记必须落在该区间前后 `EXEMPT_WINDOW` 字符内。

窗口值 40 是从三个必须保持豁免的真实站点反推的，不是拍脑袋：

| 站点 | 标记 | 到 locator 距离 | 判定 |
|---|---|---|---|
| `skeleton:635` `(historical: ticket A8-2 L70` | `historical` | 21 | 豁免（正当） |
| `skeleton:261` `…:71-80` at commit `d3689a1` | `commit` pin | 13 | 豁免（正当） |
| `governance:32` `req-33 L662-L704 pre-this-change` | `pre-this-change` | 18 | 豁免（正当） |
| `CLAUDE.md:94` `…:34-36` | `原` | ~200 | **actionable** |
| `skeleton:259` `…:211` | `before`（另一子句） | ~400 | **actionable** |

## D2. `code_span_mask` 重写

旧实现：`text.count("`", 0, pos) % 2 == 1`。两处失效：

- **双反引号。** ` `` ` 贡献 2 个、闭合再 2 个，合计偶数 → 内容被判在 span 之外。`wayfinder/spec.md:898` 的 `historical` 正在这样一个 span 内。
- **只标记定界符。** 即使单反引号，`count` 只用于**查询**，从不用于**标记**；新写的第一版掩码重犯此错，只把定界符置 1，中间仍为 0。

新实现扫描反引号**连续段**：N 个开启，恰好 N 个闭合，`[open, close)` 整体置 1。

这条路径上我自己的实现被守护测试抓了两次（`test_code_span_mask_marks_the_content_not_just_the_delimiters`、`test_code_span_mask_handles_a_double_backtick_span`），第二次是在**上线之后**——第一次修复只解决了定界符，未解决双反引号。

## D3. 标记集：判据是「是否断言过去态」

一个标记必须通过这个测试：**它可能出现在普通的现在时技术散文中吗？**

- `\bhistor\w*` 接受名词 `history` → `history stacked by metrics.UR per src/decompmoe/metrics.py:83` 自行豁免。改为 `\bhistor(?:ical|ically)\b`。
- 集合同时**过小**：本仓规范注解 `(historical, <值>; superseded by spec req-N L### via <change> Decision M)` 被 `;` 切开、随后什么也匹配不上，九个正当历史注解被报成活指针。补入 `supersed(e|ed|ing)`、`former(ly)`、`original(ly)`、`pre-(this-change|migration|edit|sweep|rebaseline)`。

**`;` 不再是 `EXEMPT_BREAK`。** 距离本身承担分隔职责；分号在本仓注解语法里不是子句边界。`EXEMPT_BREAK` 收缩为 `"。\n"`。

## D4. 窗口按尾部余量读取

窗口约束标记**起点**的位置。先截断文本再匹配，会把正好落在窗口边缘的 `**pre-edit**` 切成 `**pre`，任何模式都匹配不上——`governance:135` 因此无缘无故保持 actionable。

改为：窗口按 `end + EXEMPT_WINDOW` 截断后**再补 `MARKER_TAIL = 24` 字符**用于识别，并用 `_admissible()` 断言标记的绝对起点确实落在 `[start - W, end + W]` 内。约束不变，识别变完整。

## D5. `RE_PIN_COMMIT` 不查掩码

`at commit \`d3689a1\`` 里的反引号是排版，不是引文：它陈述的是「该定位符在那个 revision 上读」。`skeleton:261` 依赖它。设为独立规则，直接搜窗口，**不查 `mask`**。十六进制字母要求仍挡住 `0.0350601609682665718` 这类浮点尾巴。

## D6. 清单是前缀，不是文件名

`SELF_EXCLUDE` 原为 `("scripts/lint_no_line_pointers.py", "scripts/pointer_scan.py", "tests/test_lint_", "tests/test_pointer_scan.py")`。新增 `scripts/lint_pointer_detector.py` 若不加入，它会把自己的 `POSITIVES` 夹具报成 24 处活指针——与上一轮「门禁与普查各持一份清单、漂移后互相污染」是同一个失效，只是搬到了隔壁目录。改为 `scripts/lint_` 前缀，新增 lint 自动覆盖。

守护测试同步改为 `ps.in_scope([rel]) == []`（前缀语义），并断言 `"scripts/lint_" in ps.SELF_EXCLUDE`。

## D7. Errata — 对已归档记录的更正

归档件不可变。以下为独立复核指出的、本轮实测复现的更正。

### LOW-5：普查数字

| 记录位置 | 归档件所记 | 复核实测（旧检测器） | 本轮实测（修正后检测器） |
|---|---|---|---|
| 上一轮 `design.md` D1 | `82 / 55 / 27 / 17` | `104 / 75 / 29 / 17` | `104 / 88 (strong 83) / 16 / 17` @ `628d5c5` |
| 上一轮 `proposal.md` | 「55 across 10 files」 | 「75 across 10 files」 | actionable 数随检测器变 |
| 上一轮 errata row 3 | `267 / 232 / 35 / 28` | `227 / 191 (strong 180) / 36 / 24` | @ `1526b98`: `224 / 200 (strong 189) / 24 / 24` |

**「sites」与「files」两列在两次独立测量中一致；分歧全部落在 actionable/historical 的切分上，而那正是本轮修的东西。** 归档记录里的 actionable 数是按**旧检测器**的整行豁免测的；它作为「旧检测器输出」是正确的，作为「新检测器已收口」的证据则不成立。

本轮关键量：修正后检测器在清扫前基线 `1526b98` 上报 **189 strong actionable**，旧检测器报 100。

### LOW-6：「三份 spec 逐字节相同」为假

上一轮 claim 4 称归档前后三份 spec 逐字节相同。实测：归档提交 `42d161b` 改了 `governance/spec.md` 1 行。anchor 覆盖、heading 计数、重复 id 三项断言本身正确。

### MEDIUM-3：归档并未真正归档

`git ls-tree -r 42d161b -- openspec/changes/<name>/` 返回 14 项（活跃目录仍在），归档目录 15 项。删除只存在于工作树的未暂存 ` D` 条目。新克隆该 commit 仍视此 change 为 active。

**更正 1**：本轮 `41e1663` 暂存那 14 项删除 + 补 `.openspec.yaml`，HEAD 中活跃目录 0 项、归档目录 15 项。

**更正 2**：我自己的归档保真检查器第一版报 6 处「字节不一致」，其中 3 处是**假阳性**——`.gitattributes` 声明 `*.md text eol=lf`，工作树的 CRLF 在提交时归一化，blob 实际相同。检查器改为比较 `git rev-parse HEAD:<path>` 与 `git hash-object <path>`。真实差异只有 `proposal.md`（`## What` → `## What Changes`）与 `tasks.md`（勾选翻转），均为归档工具自身改写。

### MEDIUM-4：harness 三重不可复现

`evidence/validate_detector.py`：`HERE.parents[3]/'scripts'` 归档后解析为 `openspec/scripts`；无门禁调用；硬编码两个绝对路径，基线 worktree 缺席时**静默 SKIP**——即唯一在规模化证明非真空的段落。

**更正**：迁至 `scripts/lint_pointer_detector.py`。`REPO = Path(__file__).resolve().parent.parent`（位置无关）；基线经 `ps.scan_commit(REPO, "1526b98")` 从对象库直读，**不创建 worktree、不碰 index、不留残留**（旧做法需要外部预先存在一个 worktree 才有意义）；`run_gates.py` 按 `scripts/lint_*.py` glob 自动发现，**无需改动该文件**（它属并行 session）。基线不可读 → `FAIL`，不再 `SKIP`。

### LOW-7：普查范围与语法不自洽

`tracked_files()` glob `*.md` `*.py`，`EXT` 枚举 11 种扩展。改为从 `EXT` 派生 `EXT_EXTENSIONS`。派生用 `removeprefix("(?:")`/`removesuffix(")")`：`EXT[3:-2]` 会把 `ini` 切成 `in`——这个错误由 `test_tracked_file_census_covers_every_extension_the_grammar_names` 抓到。

## D8. delta 由 diff 生成，且必须回环

三份 delta 全部由 `41e1663` 的 pre 文本与工作树 post 文本**逐 Requirement 比对**生成，不手抄。块边界判据：`<a id="...">` 之后第一个非空行是 `### Requirement:`（把任何 anchor 当边界会截断其后 Requirement 并以零 Scenario 发出）。

**回环断言**：把 delta 施加于 pre 必须逐行复现 post。此断言在本次运行中抓到两处真实缺陷——(a) 漏掉首个 anchor 之前的文件头；(b) `rstrip()` 归一化吃掉文件末尾空行，伪装成 2 行 delta 失败（实际 pre/post 均 656 行、同尾部）。比较改为**行列表**而非拼接字符串。

结果：wayfinder 2 + skeleton 1 + governance 2 = **5 个 MODIFIED Requirement**，三份 delta 回环全 OK。

## D9. 替换用有界 token，并对散文做结构断言

15 条替换，每条 token 在其文件内**恰好命中一次**（否则 FAIL，不静默重写）。`safeguards.py:222` 虽已被标记豁免，仍属同一漂移族，一并修——替换表不必与 actionable 列表一一对应。

**这一轮我自己的替换破坏了括号平衡**：token 停在段名、吃掉了其后 parenthetical 的 `(`，留下三个孤立的 `)`。门禁全绿——指针没了、普查为 0、测试通过——只有散文被毁。加了逐行括号平衡断言（忽略 code span 内内容）后修复。断言范围**只限本轮改动的行**：整文件扫描会命中既有的跨行括号散文（第 277 行）并误报为损坏。

`git diff --numstat` 为 1/1、1/1、3/3、2/2——严格等增等删，无行被毁。
