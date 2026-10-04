# 统一门禁与检测器的豁免路径，并修正一处引文漂移

## Why

第四轮独立复核判定 **FAIL**。它的头条不是清单，是一条**架构事实**：

```python
# scripts/lint_no_line_pointers.py:299（修复前）
if has_historical_marker(line):
    continue
```

`has_historical_marker` 是**整行**谓词。而同一文件里的 `classify_pointer` 调用 `ps.scan_line` 收集行号后，**从不读 `s.historical`**——它把检测器算出来的逐定位符裁决扔掉了。

也就是说：**第三、四轮全部的豁免工程，从来没有到达真正执行门禁的那个 lint。** 在清扫前的树 `8de4124^` 上实测：

```
lint_no_line_pointers C1 violations : 0
detector strong-actionable sites    : 18   (9 lines × 2)
of those, lines C1 EXEMPTS wholesale: 9 / 9
```

那 9 行正是那 9 个清扫目标。检测器报它们 LIVE，门禁同时报这些行干净——同一次运行里，两套结论。

这是本系列**最初的根因在隔壁目录重演**：两份实现各自演化、漂移，然后在同一次运行里互相矛盾。第三轮 `design.md` 写着「门禁与普查必须共用一份实现」，而门禁恰恰在共用检测器的**检测**部分之后，又自己接回了**豁免**部分。

另有两处是我自己造成的、且性质相同：

- **`design.md` D6 的 errata 是第三个数字。** 它声称「更正」上一轮未重算的数字，却自己写了两个没测过的值。D6 的小节标题正是「数字必须重算」。
- **`governance:145` 被我指到了不含该主张的 Requirement。** 我按**行号归属**（L184-185 落在 req-8）而不是按**内容**判定，而该句谈的是 θ_Voronoi 52°→67.24°；`req-8`（L181-196）不含 `Voronoi`、不含 `67.24`，`req-11`（L247-302）三者全含。**同一提交**在 `A1-1.md:98` 与 `A5-3.md:63` 把同一个 52°→67.24° 的取代关系正确归给了 `req-11`。

## Scope

- `scripts/lint_no_line_pointers.py` — `classify_pointer` 返回逐站点 historicality；C1 改为「全部站点皆历史才豁免」。
- `scripts/pointer_scan.py` — `superseded:` 变体、lead 尊重 code span 掩码、`原` 同形异义、死标记项、标记不得跨越另一定位符。
- `scripts/lint_pointer_detector.py` — 范围钉死（15 进 / 4 出）、`MIN_CHECKS` 提到有效值。
- `openspec/specs/governance/spec.md` — 1 处引文改指 `req-11`（1 份 delta）。
- `tests/` — 7 项新守护测试，含「门禁与检测器对规范形态必须一致」。

## What Changes

1. **门禁与检测器共用同一条豁免路径。** `classify_pointer` 返回 `(nums, weak, all_historical)`；C1 仅在 `all_historical` 为真时跳过。**一个定位符一个裁决：一行只有在它所有站点都是历史记录时才豁免。**
2. **`superseded:`（冒号形）计入 lead。** 距已覆盖语法一个字符。
3. **lead 尊重 code span 掩码。** 此前它是唯一不查掩码的规则；把短语**写下来讨论这个约定**不等于它本身是一次实例。
4. **`原` 不再是裸单字。** `原理`（原理）、`原子`（原子）、`还原`（还原）都含 `原`，各豁免一处活指针；单字符标记无法分辨义项。改为必须带它所compound 的过去态词（`原值`/`原实现`/`原定义`/`原先`…）。**这是词法近似，承认之**；替代方案是保留一个会在普通技术词汇上开火的单字匹配。第三轮在同一处**加入** `旧` 时只让同形异义问题更严重。
5. **标记不得跨越另一定位符。** 一个标记注解**一个**对象；必须跨过同行另一个定位符才能到达的标记，不是这个对象的标记。
6. **普查范围钉死。** 在 `in_scope` 里加一条 `wayfinder/tickets/` 排除，会把普查从 80 个文件降到 56、基线从 24 降到 18，**而整条门禁管线（4 个 lint + pytest）全绿**——尽管第三轮刚清扫的正是那 6 个票据文件。总数抓不住减法，具名文件能。
7. **`MIN_CHECKS` 45 → 80。** 45 时删掉 `if found:` 内的 6 项检查仍留 58、仍绿；80 时同样删除留 77，被抓。真正承重的是无括号的 `len(found) > 0`。
8. **`governance:145` 改指 `req-11`。**

## Errata on round 4

以下全部由本轮**亲自重测**，并写明测量工具。归档件不可变。

| 量 | round 4 的 D6 所写 | 本轮实测 | 备注 |
|---|---|---|---|
| `628d5c5` sites | `102` | **`102`** | 唯一对上的 |
| `628d5c5` actionable | `85` | **`94`** | D6 写的是未测值 |
| `628d5c5` strong | `80` | **`89`** | D6 写的是未测值 |
| `628d5c5` files | `17` | **`17`** | 对 |
| `1526b98` strong（被称为「已核实」） | `189` | **`198`** | 189 是**第三轮**检测器的值 |
| 范围算术 | `682` tracked / `594` archive | **`724` / `636`** | 另有 8 个被 `SELF_EXCLUDE`/working-note 排除，D6 把差值全归给 archive |

`682 − 594 = 88 ≠ 80` 这个矛盾在 D6 里没有被察觉：**结论（80）是对的，支撑它的算术是错的。**

D6 中另一条子结论经复核**成立**：「旧检测器报 100」中的 `100` 确为上一轮 harness 的 `BASELINE_MIN_STRONG` 阈值下界，不是测量值。本轮不再引用任何未由我亲自测量的旧检测器数字。

## 已知残留（不在本轮范围）

- **短距离跨子句**：`(historical, …); now spec.md L453`、`was X) - but see spec.md L453`、`formerly X; current value: spec.md L453` 仍豁免。共同点是「标记与当前目标之间无结构线索」；任何泛化规则都会与本仓依赖的规范注解冲突。复核确认活树 0 例。
- **普查召回**：`path … prose … L###` 结构性不可见（43 个 `L<2+digits>` token 中 13 个被覆盖），14 个未覆盖 token 全在 `governance/spec.md`，其中 9 个指向 gitignored 的 `.audit/`。
- **`before` 作介词**（"the value before clipping"）与 `original`（"the original entry point"）仍被当作标记；与 `before the change` 词法不可分。
- **`.audit/` 被 gitignore**，指向它的定位符无法由 `git` 校验。
- **`run_gates.py`** 归档后 `validate` 报 ERROR、GBK 控制台崩 `UnicodeEncodeError`——属并行 session，不碰。
