# Proposal

## Why

`tests/` 下 48 处 `torch.allclose` 调用点全部省略 `rtol` 参数，`rtol` 的隐式默认 `1e-5` 参与判定却从未被任何人选择过。根因不在这 48 个测试，而在治理条文本身：`governance` req-gov-1 的 7 条 obligation 把「阈值须由该 dtype 的 eps 与量的尺度推导」写成了**逐案枚举白名单**（obligation 3 的二分 `abs=1e-6`、obligation 7 的 Monte-Carlo `5σ`），而非一般义务——`torch.allclose` 的 `rtol` 永远落在枚举之外。实测（HEAD `dde0e1d` 干净导出、torch 2.12.1+cu130 / pytest 9.1.1）显示：48 处中当前真正被默认 `rtol` 放过真实漂移的有 **2 处**（`tests/test_extraction.py:461`、`:540`，均为 `atol=1e-12`），但危害并不止于翻转——8 处 `assert not torch.allclose(...)`（负极性）里默认 `rtol` 方向与「失明」**相反**（放宽阈值使否定断言更难成立），3 处完全不给容差的断言其通过条件完全由两个无人选择的默认值决定。本 change 把规则从枚举一般化，并逐条处置这些落在规则空白区的站点。

## What Changes

- **一般化 req-gov-1 的阈值规则**（governance delta）：新增三条可判定的一般义务，覆盖数值比较的三个未被现有 obligation 触及的面——(a) 使用带默认相对项的比较器（`torch.allclose` / `torch.testing.assert_close` 的 `rtol`）时，相对项 MUST 显式给出且 MUST 可由被保护量的量级与 spec 声明的精度导出；(b) 既不给 `atol` 也不给 `rtol` 的比较 MUST NOT 出现；(c) 负极性（否定）断言的容差方向与正向相反，MUST 显式声明。三条义务均不点名任何现有站点。
- **处置 2 处当前失明站点**：`:461`（空胞保留）通过实现侧一行空胞直通（`torch.where` passthrough，与 skeleton req-16 已逐字要求的 `torch.where(use_old, prev, normalize(...))` guard 同构）使漂移严格为 0，比较器升级为 `torch.equal`；`:540`（near-zero fallback）把测试构造升到 float64 使 fallback 以约 7 个数量级余量真正触发，fallback 行用 `torch.equal`、健康行走 float64-ulp 推导的 `torch.allclose(atol=..., rtol=0.0)`。〔基线：`evidence/flip-post.md`〕
- **处置负极性与无容差站点**：8 处 `assert not torch.allclose` 与 3 处无容差站点按新增义务逐处显式化（负极性方向反转在注释与 design 中说明）。〔基线：`evidence/flip-baseline.md` @ `dde0e1d`〕
- **可选机械门禁**：新增一条 lint，经 `run_gates.py` glob 发现，机械卡住「新写的 `allclose` 未显式给出相对项」。
- **范围边界**：FIX-041（`req-gov-9` 编号悬空，20 处散文引用）与 FIX-042（Source 字段豁免 20/70）**不在本 change**，各自独立立项。本 change 仅覆盖 FIX-001 + FIX-020（同属 req-gov-1 的一体两面）。

## Capabilities

### New Capabilities

（无。本 change 不引入新 capability。）

### Modified Capabilities

- `governance`: Requirement「Test Guard Precision for Closed-Form Numerical Claims」（req-gov-1）所承载的阈值规则由逐案枚举一般化——新增三条覆盖「默认相对项显式且可导出」「无容差禁止」「负极性容差显式」的一般义务。delta 以三个独立 ADDED Requirement 承载（每个 Requirement 一个行为），req-gov-1 既有 7 条 obligation 文本保持不变，作为新增一般义务的特化实例。

## Impact

- **spec**：`openspec/specs/governance/spec.md` req-gov-1 追加三条一般义务（archive 时并入主 spec）。
- **tests**：`tests/test_extraction.py`（`:461`/`:540`/`:636` 三处 `atol=1e-12` 站点）、8 处负极性 `assert not torch.allclose`、3 处无容差站点。
- **src**：`src/decompmoe/extraction.py`（`CentroidDriver.step` 空胞分支一行直通；与 skeleton req-16 的 guard 模式同构，属 conformance 修复，不改变 spec 已钉死的 invariant）。
- **门禁**：可选新增一条 `scripts/lint_*.py`，经 `run_gates.py` 自动发现。archive 前工作树须落定（当前工作树 8 项脏，脏树跑门禁会以 `GATE RESULT INVALID` exit 2）。〔基线：工作树项数由 `git status --porcelain` 实测〕
- **不在范围**：FIX-041、FIX-042；本 change 不修 `fix001-verification-report.md` §A.6 的内部不一致（属 `.audit` 制品，不进 spec 路径）。
