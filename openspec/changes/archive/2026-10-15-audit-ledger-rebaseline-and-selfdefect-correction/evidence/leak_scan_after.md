# leak_scan 复扫裁定（写回后）

**对象**：`openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction` 的任务 4.1
**命令**：`uv run python evidence/leak_scan.py > evidence/leak_scan_after.txt`
**基线**：`evidence/leak_scan_baseline.md`（D3 轮，写回前）

`leak_scan.py` 的 `body_of()` 在遇 `## 附：` 时截断，故本 change 新增的
「附：本轮 HEAD 复验登记」小节（`opsx-changes.md:314` 起）与 `direct-fixes.md`
的本轮 pin 更新均在扫描范围之外。这是设计意图，不是漏扫 —— 该设计已由既有
leak-scan 附录记录。

---

## 1. 计数变化

| 清单 | PASS 1 原始命中 | PASS 2 (a) 逐字引用 | (b) 本文件自身的处置建议 |
|---|---|---|---|
| `direct-fixes.md` | 6 → **6**（未变） | 63 → **63**（未变） | **0** |
| `opsx-changes.md` | 6 → **16** | 7 → **8** | **0** |

**direct-fixes.md 的 6 处与 63 处全部未变**，与 3.6「仅 pin 更新、不逐条追裁定」
的承诺一致：新增文本只涉及 pin 声明、覆盖范围说明与可靠性注记，三段均为
**陈述本桶的测量口径**，不含任何条目级处置主张。

**opsx-changes.md 新增 10 处**，全部落在 8 条的 `**HEAD 复验（ded0944）**` 与
`**修复 commit**` 字段内，逐条如下。

---

## 2. 新增 10 处逐条归类

D3 轮确立的判据（见 `direct-fixes.md:677` 与 `opsx-changes.md:249`）：
> **(a) 类判据**：引文归属于被引制品，本文件只负责转述它，不对它作改动主张。
> **(b) 类判据**：把被引物说成应当改成什么、应当优先处理或应当取什么值。

| 行 | 模式 | 文本要点 | 类别 | 判据 |
|---|---|---|---|---|
| L82 | `修复` | `` `CLOSED_BY_COMMIT` — 修复 commit `df4a1d2` `` | (a) | 字段名 + 已发生事实；actor 为具名 commit，可 `git show df4a1d2` 复核 |
| L83 | `修复` | `- **修复 commit**：`df4a1d2`（…窗口内判据…） | (a) | 同上；`D-1` 规定的必带字段名 |
| L138 | `修复` | `` `CLOSED_BY_COMMIT` — 修复 commit `642d8e9` `` | (a) | 同 L82 |
| L139 | `修复` | `- **修复 commit**：`642d8e9` | (a) | 同 L83 |
| L155 | `改为` | 上确界措辞改为「**supremum over the closed range of `β`, not a value attained by any finite `γ`**」 | (a) | 过去式转述 `c568803` 所为；引文**逐字**命中 `openspec/specs/wayfinder/spec.md`（含粗体标记，已机械核验） |
| L155 | `改为` | `ded0944` 的 F1 把 `test_grad_C_bound` 的内联复述改为调用实现 | (a) | 过去式转述具名 commit 的动作；无目标值 |
| L155 | `修复` | `` `CLOSED_BY_COMMIT` — 修复 commit `c568803` `` | (a) | 同 L82 |
| L156 | `修复` | `- **修复 commit**：`c568803` | (a) | 同 L83 |
| L174 | `修复` | 无可指名的修复 commit：`dde0e1d..ded0944` 窗口内 `wayfinder/spec.md` 仅被 `c568803` 触及 | (a) | **否定式**事实陈述：声明「无」，不是主张「当修」 |
| L174 | `修复` | （`design.md` D-1 规定 `ENTRY_MISSTATED` 不带修复 commit 列） | (a) | 转述本 change 自身 `design.md` 的元数据规则，不是对被引制品的主张 |

**(b) 类命中数 = 0。**

### 最接近边界的一处：L155 第二条

`改为` 是本 change 唯一一处出现在**祈使语境之外**的改动动词读法，最容易被读作处置建议。
判它为 (a) 的两条理由：

1. **时态与 actor 齐备**。句式为「`c568803` 做了什么」，不是「应该做什么」。同句的后半
   还给出了可机械复核的证据（`git show c568803 -- wayfinder/spec.md`）。
2. **引文归属被引制品**。所引文字是 `openspec/specs/wayfinder/spec.md` 在 HEAD 的现文，
   逐字命中（含 `**` 粗体标记）。若把它视为本文件的改动主张，则本文件就在**指定被引制品的措辞**；
   事实是它只在转述该制品当前的措辞。这一条是 PASS 2 把 (a) 从 7 抬到 8 的原因。

若日后有第三方仍认为该处应归 (b)，处置办法不是改判，而是把该引文改为间接引述
（去掉引号并加「其现文为」）。本轮未作此改动，因为逐字引用对复核更有利。

---

## 3. PASS 2 (a) 由 7 涨到 8 的机械依据

新增的 1 处 (a) 即上表 L155 的 req-30 上确界引文。核验命令：

```
$ grep -o 'is a \*\*supremum over the closed range of `β`[^）]*' openspec/specs/wayfinder/spec.md
```

**写回过程中此处出过一次错并已更正**：初稿的引文写作「a supremum over the closed
range of `β`, not a value attained by any finite `γ`」，**丢掉了原文的 `**` 粗体标记**，
因而对 spec 而言不是逐字引用，PASS 2 的机械判据会失效。更正为逐字形式（含 `**`）后，
`q in led == True` 且 `q in spec == True` 双向成立。

这是本轮写回的**第 7** 次「机器判据与人工判读脱节」事件（前 6 次的机制登记见
`design.md` D-6）：凭记忆转述引文时丢掉了格式标记，肉眼读起来完全一样，
但机械核对会否证。
