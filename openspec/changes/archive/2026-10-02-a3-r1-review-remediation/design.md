# Design

## D1 — spec 修订全部脚本生成，块级回验，不手抄

`wayfinder` 若干 Requirement 的正文是单行数千字符，手抄进 delta 必然字符级漂移。
本轮的做法：① 按 `<a id="req-N">` 锚点从主 spec 抽取**整块原文**到 scratch 文件；
② 每处替换**断言命中次数恰为 1**；③ 写出 delta；④ **块级逐行 `difflib` 回验**；
⑤ 6 项 stale-token 扫描确认旧措辞一个都不残留。

第 ④ 步不可省：本仓有过一次 substring 替换导致原行尾部悬空，而**所有目标 keyword
仍然 grep 命中、单看检查项全过**。grep 是结构损坏时的假阴性来源。

## D2 — F1 的充分条件必须落在**被除的那个量**上

`extract_C` 四步流水线的最后一步是 `spherical_l2_normalize(z̄)`，实现是
`z̄ / max(‖z̄‖₂, ε)`。决定输出范数的是 `‖z̄‖₂`，**不是任何单个 `‖z^{l,h}‖₂`**。
C2 当时把条件写在 per-head 上，是因为它读的是「哪一步会除以 ε」——但那一步除的是
跨头均值。

反例构造（`H_kv=8`，`d_c=16`，`proj_W_V[h,0,0]=1`，`proj_b=0`，前 4 头 `V=+1`、
后 4 头 `V=-1`）：

```
per-head ‖z_h‖ = [1.0]×8      旧前置条件满足
跨头均值 ‖z̄‖ = 0.0
extract_C ‖C_t‖ = 0.0          Scenario 断言 = 1（1e-5）被违反
对照：全同号 → 1.0；  3 正 5 负 → 1.0
```

req-19 的 per-head 次 ε 区间是**另一种**可违反情形，被均值条件包含，所以没有丢覆盖。

教训可推广：**给一条闭式加「前提」时，前提必须约束那个真正进入分母/被比较的量，
而不是流程中「看起来最相关」的那一步的中间量。**

## D3 — `UR` 的并集读法：把裁决搬进 spec，并换一个有区分力的 fixture

裁决本身不变（并集），理由是 spec 的 `I[f_i > 0]` 对**专家**求和、且注解是
"fraction of experts actually selected"。本轮做两件事：

1. **写进 req-20 的 Scenario**，不再只活在测试 docstring 里（这是 F3 的实质）。
2. **换掉有区分力的 fixture**。初稿用的 200 步历史（窗口内每步恰好 `{0,1}` 激活）
   在两种读法下都给 0.125——激活集在窗口内恒定时两者不可区分。新的 fixture 让
   激活集**在窗口内变化**：前半只激活专家 0、后半只激活专家 1，于是并集 `2/16`
   而逐占比均值 `1/16`，并把两个读法**并排钉在同一条测试里**。

## D4 — F4 的更正：删掉那个不成立的对立，而不是换个说法

初稿的整个框架是「台账给了两个 spec 值，分别支持两条规则」。实测两个环节都不成立：
200 步 fixture 不具区分力；0.0625 的出处是 `wayfinder/tickets/A8-2.md:93`，而该
ticket 的 UR 是 **per-expert** 的 `f̄_i^(100)`，均匀路由下健康值就是 1/16——把它
当 spec 判据是范畴错误（spec 的 UR 是「被选中过的专家占比」，健康值 1.0）。

所以正确的事实是：**真判据只有 0.125 一个，且它支持并集读法。** 结论不变，但支持
它的论证要换。已归档的 C4 `design.md` 里**保留**了初稿结论并在其后追加「D5 更正」
——后来者需要知道这个坑在哪（`CLAUDE.md` §1：不隐藏困惑）。

## D5 — F7：`abs` 会短路，所以**规则的理由要换，规则不动**

实测 pytest 9.1.1：

```
approx(3.0,          abs=0).tolerance = 0.0
approx(134217728.0,  abs=0).tolerance = 0.0        governance 原称 ≈1.34e-4
3.0 + 1e-13 == approx(3.0, abs=0)  ->  False        即 abs=0 就是零容差
DEFAULT_RELATIVE_TOLERANCE = 1e-06                  governance 原称 1e-12
```

`ApproxScalar.tolerance` 在 `rel is None and abs is not None` 时**直接返回
`absolute_tolerance`**，根本不调用 `max`。所以 obligation 1 与 obligation 3 里那
两段推导都是假的。

**规则保留，理由替换**为版本无关的陈述：精确整数主张是关于**精确性**的主张，而
`pytest.approx` 按定义就是一个「容许容差」的比较；`pyproject.toml` **没有 pin
pytest 版本**，靠 `ApproxScalar` 的实现细节拿到零容差会让这条纪律静默地变成版本
依赖。裸 `==` 在任何量级、任何版本上按构造就是零容差。

这条也顺带清掉了我自己在 `tests/test_a3_contract_alignment.py` 模块 docstring 里
写的**另一种同样错的版本**（「`rel=1e-6` 默认值与 `abs` 并存」）。两处文本在同一个
commit 里互相矛盾，留着会让维护者怀疑整条纪律。

## D6 — 新发现但本轮不修：`n_i.clamp_min(1.0)` 在 `0 < n_i < 1` 时静默改变结果

写 dense-mask 测试时实测到：驱动的 `safe_n = n_i.clamp_min(1.0)` 并非「仅用于避免
0/0 NaN」——当 `0 < n_i < 1` 时它会把分母抬到 1，**静默改变 `m_i` 的值**。代码注释
声称它「solely to guard the division against 0/0 NaN」，这句在 `n_i < 1` 时是错的。

本轮**只记录不修**：它不在 13 条 finding 里，修它要决定「`n_i < 1` 时的规范行为」
（是真 per-expert 均值？还是别的东西？），那是一次需要 derivation 的语义选择
（`CLAUDE.md` §6 禁止用 policy + code-first 关掉数学语义问题）。新测试的 fixture
因此显式取 `n_i > 1` 并断言该前置，使 clamp 成为 no-op。

## D7 — F9：给 `randn` 加 `device=` 不等于修好了探针

原修复是 `torch.randn(..., generator=generator, device=centroids.device)`，而
`generator = torch.Generator().manual_seed(...)` 仍在**默认设备**。torch 在采样时会
校验 generator 的设备类型，用 CPU generator 驱动 CUDA 采样会抛
`Expected a 'cuda' device type for generator but found 'cpu'`。所以那次修复在
CUDA host 上并没有闭合 AC-79。

守卫同步改造：原来的断言是 `assert "device=centroids.device" in inspect.getsource(...)`
——**钉的是拼写**。字符串出现在注释里也过，行为等价的重写（如先 `dev =
centroids.device`）反而挂。改为 AST 属性断言（`Generator` / `randn` / `rand` 的每个
调用必须带 `device=` 关键字），并把 `.manual_seed(...)` 排除在外——它是已绑定设备的
Generator 上的方法，要求它带 `device=` 会拒掉正确代码（我第一版就踩了这个，是
跑测试发现的）。

CUDA 行为半边用 `skipif` 并写明理由：本机无 GPU，`torch.randn` 的默认设备本就等于
`centroids.device`，该缺陷**不可达**，所以本机上只有结构守卫在真正验证这一项。
写明比让它静默通过诚实。

## D8 — F10：characterization 常数不是闭式，承重的断言必须是闭式

`1.421196 / -0.023137` 是 999 步 float32 递推的输出，无 Requirement、无 Scenario
背书，会随 torch/BLAS 变化漂移。所以承重断言换成两个**每步检查**的量：

- req-18 Invariant 2 的 `‖c_i^(t+1)‖₂ ≡ 1.0`——真正的 spec 闭式，原测试完全没查；
- 非退化性：任意两步之间没有两个质心重合（性质，不是数字）。

characterization 值保留在末尾，docstring 明确标注它是 change-detector 而非闭式；
被删分支的 5999 步数字标注为「已不可复现的散文」。

## D9 — 归档后必须同时查 anchor 计数**和** diff

本仓的 `openspec archive` 有反复出现的破坏形态。本轮归档前的 delta 里 wayfinder 的
**最后一个 block 是 req-32**，而 req-32 在主 spec 中并非最后一个——按前两轮实测的
规律，delta 末块之后紧邻的 anchor 会被整行删除。因此归档后跑两道判据：
① spec 形状门禁（anchor 覆盖 + 重复）；② `git diff -U0` 逐行确认**没有一行是我没
打算改的**。第 ② 道抓的是「给未改动块插空行」这类计数门禁看不见的损坏。
