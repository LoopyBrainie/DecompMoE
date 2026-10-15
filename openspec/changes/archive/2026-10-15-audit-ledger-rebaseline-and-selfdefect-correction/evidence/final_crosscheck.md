# 4.2 汇总对账

**命令**：`uv run python evidence/final_crosscheck.py` → 输出见 `final_crosscheck.txt`
**结论**：`CROSSCHECK OK — bidirectional, no orphans on either side, D-1 invariant holds`

## 分母

| 量 | 值 | 来源 |
|---|---|---|
| `bucket == opsx-change` | **8** | `_work3/c1/classified.json`（`total` 88，`opsx-change` 8） |
| `opsx-changes.md` 带 `**HEAD 复验（ded0944）**` 的条目 | **8** | 本 change 写入 |
| `direct-fixes.md` 带该字段的条目 | **0** | 3.6 承诺「仅 pin 更新」 |
| `evidence/reverify/*.md` | **17** | 8 opsx-change + 9 direct-fix |
| `bucket == direct-fix` | **32** | 同上 |

三桶分流的依据是 `classified.json` 的 `bucket` 字段，不是文件名猜测。9 份
direct-fix 记录**存在而台账无字段**，正是 3.6 的契约：判据「被引文件在
`dde0e1d..ded0944` 窗口内零 commit」可机械判定，故落 evidence；其余 23 条
口径异质，具名移交。

## 双向对账表（按 **ref** 索引，不按文件位置）

| ref | 台账取值 | evidence 取值 | 修复 commit | 一致 |
|---|---|---|---|---|
| FIX-001 | `CLOSED_BY_COMMIT` | `CLOSED_BY_COMMIT` | `df4a1d2` | OK |
| FIX-006 | `CLOSED_BY_COMMIT` | `CLOSED_BY_COMMIT` | `642d8e9` | OK |
| FIX-007 | `CLOSED_BY_COMMIT` | `CLOSED_BY_COMMIT` | `c568803` | OK |
| FIX-020 | `NARROWED` | `NARROWED` | — | OK |
| FIX-029 | `STILL_REPRODUCES` | `STILL_REPRODUCES` | — | OK |
| FIX-034 | `ENTRY_MISSTATED` | `ENTRY_MISSTATED` | — | OK |
| FIX-041 | `STILL_REPRODUCES` | `STILL_REPRODUCES` | — | OK |
| FIX-042 | `STILL_REPRODUCES` | `STILL_REPRODUCES` | — | OK |

**8/8 双向一致**：无「台账有字段而缺记录」，无「有记录而台账漏字段」，无取值分歧。

取值分布：`CLOSED_BY_COMMIT` 3 / `STILL_REPRODUCES` 3 / `NARROWED` 1 /
`ENTRY_MISSTATED` 1。

## D-1 不变量

`CLOSED_BY_COMMIT` 条数 = 3，`**修复 commit**` 字段数 = 3，且脚本逐条校验
「该列当且仅当取值为 `CLOSED_BY_COMMIT` 时存在」——3 条 `CLOSED` 各带一个，
5 条非 `CLOSED` 各不带。FIX-034 按 3.4 的要求不设该列。

## 为什么必须双向且必须按 ref

本轮真实发生过一次**单向检查放行**的失效：批量写回时，我按条目在文件中的
**位置**而非 **ref** 把 8 段裁定文本对应过去，而实际文件顺序是
`001, 020, 041, 006, 007, 034, 042, 029`，与我假设的顺序不同。结果 6 条的
取值落到错误条目上（FIX-020 拿到 FIX-006 的 `CLOSED_BY_COMMIT`，FIX-041 拿到
FIX-007 的，依此类推），3 个 `修复 commit` 字段也落错 3 处。

该失效**任何正向检查都发现不了** —— 每条记录都存在、每个字段都非空、每个取值
都是合法枚举值。本 change 的 `design.md` D-7 由此立此对账脚本。

## 本脚本自身的一次假阳性（第 8 次同型事件）

初版把「direct-fix 条目带 verdict 字段」写成 `ref in direct`。但 `direct` 是
**由全部 `### FIX-…` 标题构成的字典**，包含无字段的条目，故该表达式测的是
**条目存在**而非**字段存在**，把 32 条全部误报为 `LEAKED`。改为
`ref in direct and direct[ref]["n"] > 0` 后为 0。

与前 7 次同源：**判据的匹配器比被测对象宽，于是输出恒真，而结论按恒真的读法
写了下去**。反向例是 FIX-001 的 `grep` 正则比被测对象**窄**（漏 `ARC-002` 与两个
中文标题），结论同样按未受影响的读法写了下去。宽窄两个方向都出错的共同缺失是
同一个：拿到机器输出后没有问「这条命令实际回答的是哪个问题」。
