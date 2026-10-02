# Design

## D1 — `__all__` 先离线普查再接线，不边写边试

`__init__.py` 原本**零 import**，所以「把 75 个名字填进 `__all__`」这件事在接线
之前从未被执行过。直接改 `__init__.py` 再跑测试，会把「循环 import」和「真缺陷」
混在一起报错，难以归因。

因此分三步离线做完再落地：① AST 普查（不 import，零循环风险）得到并集 75 /
求和 76 / 冲突集合；② 逐个 `importlib.import_module` 实测 13 个子模块可导入；
③ 实测并集中每个名字在其声明模块上确实可解析。结果：13/13 可导入、75/75 可解析、
唯一冲突 `flops_per_token`。接线本身因此是机械的。

## D2 — `flops_per_token` 用显式再绑定，而不是靠 import 顺序

生成 import 块时按模块名字母序排列，于是 `metrics`（字母序在 `config` 之后）会
**覆盖** `config` 的定义——第一次生成后实测 `decompmoe.flops_per_token.__module__`
是 `decompmoe.metrics`，与 req-1 的绑定规则相反。

修法是在 import 块**之后**显式再绑定一次，而不是去调整字母序。理由：依赖字母序
的绑定是隐式的，下次有人重排 import 或重新生成这个文件时就会静默翻转；显式再绑定
把规则写在代码里，且带注释说明为什么在这里。C2 的 req-1 条款要求的正是
「`config` 为 canonical」，所以这行是条款的实现，不是风格选择。

## D3 — 两条既有测试因修复而失败，处理方式不同

`__all__` 接线让两条测试转红，两条都不是「测试写错了」，而是**契约冲突**，处理
方式因此不同：

- `test_extract_C_signature` 钉的是**旧拼写** `W_K/W_V/b`。req-7 才是真相源，
  重命名是修复，所以测试跟随 spec 更新。顺带加了一条反向断言：旧拼写**必须**
  消失，使「照 spec 写却被静默绑定」不可能发生。
- `test_no_other_module_defines_should_resurrect` 检查「任何模块**有**
  `should_resurrect` 属性就违规」。但 req-1 要求包级 `__all__` 导出全部公开符号，
  而 `should_resurrect` 是公开符号——**两个契约直接冲突**。

  该测试真正要防的是**二次定义**（历史上造成过 ownership 歧义，见其 docstring
  引用的 Finding #10）。包级再导出是**同一个函数对象**，不产生歧义。因此改为比较
  **对象身份**：与 `safeguards.should_resurrect` 是同一对象 → 记为再导出放行；
  是不同对象 → 才是违规。并补一条正向断言，要求包级名字仍可达（否则 req-1 的公共面
  反而缺了一块）。测试的**意图被保留，判据被纠正**。

## D4 — AC-44 用 `phase_boundaries(total_steps)` 而不是自己缩放

`_PHASE_BOUNDS` 原本是硬编码元组 `(1_000, 6_000, 26_000, 56_000, 100_000)`。核对
发现它**恰好等于** `phase_boundaries(100_000)`（比例 1/5/20/30/44% 的累积切点）。
所以正确的改法不是在这边再实现一套缩放，而是复用 `schedule.phase_boundaries`——
单一真相源，且 `phase_id` / `phase_beta_max` 本来就在用它。

顺带删掉 `_PHASE_BOUNDS`：本次改动让它变成孤儿常量，而它既不在 `__all__` 里、
也没有测试引用。保留一个由 `phase_boundaries()` 一行派生的重复常量，正是本次
重判要消灭的那类「两份真相」。

## D5 — 两条新测试写错了，是测试的错不是代码的错

第一版 `test_clip_global_grad_norm_*` 断言返回值 ≈ 1.0，实测得 3.22。查 docstring
才知道该函数返回的是**裁剪前**范数（"Returns the pre-clip norm"）——代码正确，
测试的期望写错。已改为对照 `torch.linalg.norm(p.grad)`，并另加一条断言确认裁剪
本身确实发生了（裁剪后范数 = 1.0），这样「返回值语义」和「裁剪生效」两件事都被钉住。

第一版 `test_beta_effective_forwards_total_steps` 取 `step=3_000`，两个预算下的
Phase-2 进度都被 clamp 到 0，于是两边 cap 都是 1.0、断言恒假。换成 `step=16_000`
后：100K 的 Phase-2 窗口 [6k,26k) 给出进度 0.5，50K 的 [3k,13k) 已过窗尾 clamp 到
1.0 —— 两者**必须**不同，正是需要的差异点。

**两次都是「测试期望没经过独立复算」**，与 A-3 台账记录的那类问题同源：数值断言
必须自己算一遍，不能照着直觉写。
