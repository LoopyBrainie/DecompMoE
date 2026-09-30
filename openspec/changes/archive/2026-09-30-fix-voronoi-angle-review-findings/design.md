# Design — `2026-09-30-fix-voronoi-angle-review-findings`

## Decision 1 — BLOCKER 1：把 Jensen 前提从「per-d_c 角度边界」换成 `A_i < 0.5`

`voronoi_angle` 的单侧界是 `θ̂ ≤ canonical`。原实现靠「每个胞腔半径落在 `G` 的第一段凸分支内」，
为此在 docstring 与三份 spec 里写下了 `θ_conv(d_c) = 81.3148° / 82.6036° / 83.7313°`。

**这些数字是伪影。** 对 `G(θ) = ½·I_{sin²θ}((d_c−1)/2, ½)` 求导：

    d/dθ I_{sin²θ}(a, ½) = sin^(2a−1)(θ) / B(a, ½) · 2 sin θ cos θ
    ⇒ G'(θ)  = sin^(d_c−2)(θ) / B((d_c−1)/2, ½)
    ⇒ G''(θ) = (d_c−2)·sin^(d_c−3)(θ)·cos(θ) / B((d_c−1)/2, ½)

`d_c ≥ 3` 且 `0 < θ < π/2` 时 `sin`、`cos` 皆正 ⇒ `G'' > 0` 恒成立，**`(0, π/2)` 内无零点**。
（`d_c = 2` 是退化情形：`G'' ≡ 0`，`G` 线性而非严格凸；`canonical_voronoi_angle` 本就拒绝 `d_c < 2`。）

验证方式：解析式与 mpmath 50 位精度下 `½·I_{sin²θ}(a,½)` 的中心差分在 12 位有效数字上一致。

**为什么 `θ_conv` 会「出现」**：`sphere._betainc_regularized` 用**单个** 8 点 Gauss–Legendre 面板、
无细分。`G` 在 `θ → π/2` 附近变化剧烈（`G(π/2) = 0.5` 是饱和点），二阶差分把求积误差放大
`~h⁻²`，于是在 `d_c = 8/16/32` 分别于 `≈81.3°/82.6°/83.7°` 翻号。**这三个值不是数学对象，
是 `h = 1e-5` 与面板阶数的联合产物。**

**修复方向是简化而非削弱。** 前提从「半径 < `θ_conv(d_c)`」降为「面积 < 0.5」：

- `G` 严格凸 ⇒ `G⁻¹` 在 `(0, 0.5)` 凹 ⇒ Jensen 成立；
- 等价条件：`G⁻¹(A_i) < π/2 ⟺ A_i < G(π/2) = 0.5`；
- MVP：`1/N_e = 0.0625`，实测最大胞腔 `≈ 0.077`，余量 `6.5×`。

唯一真正失去定理地位的是 `A_i > 0.5`（`N_e = 2` 且两站点不对称时可达），那里反射分支接管。
这一条**原本就是** OBSERVED BEHAVIOUR，docstring 继续如实标注。

### Decision 2 — BLOCKER 2：删除同义反复测试，用解析闭式取代

原 `test_voronoi_angle_convexity_boundary`：

1. `_convexity_boundary(d_c)` 反复调用 `_cap_area_second_derivative`（= `sphere._cap_area` 的中心差分）二分翻号点；
2. 再把该测量值 `pytest.approx(81.3148, abs=1e-3)` 钉住；
3. 再断言翻号点上方 `G'' < 0`。

问题有三层：**(i)** 用被质疑的求积去测被质疑的性质，**同义反复**；**(ii)** 钉住的是伪影；
**(iii)** `G''(above) < 0` 对真实 `G` 是**假命题** —— 任何人修正 `_betainc_regularized` 的求积都会让这个测试变红。

替换为 `test_voronoi_angle_precondition_is_area_below_half`，三段断言：

| 段 | 断言 | 失败模式 |
|---|---|---|
| (1) | `G''(θ) > 0`，`θ ∈ {0.5, 30, 60, 81.3148, 82.6036, 83.7313, 88, 89.5}°`，`d_c ∈ {8,16,32}` | 前提表述被改坏 / 闭式写错 |
| (2) | 三个**已退役** `θ_conv` 值上方 `+1°` 与 `+5°` 处 `G'' > 0` | BLOCKER 1 的假命题回流 |
| (3) | 等面积见证 `A = G(canonical) = 1/N_e < 0.5`，且 `0.5/A = N_e/2` | 前提在真实调用点上不成立 |

用 `math.gamma` 表达 `1/B((d_c−1)/2, ½) = Γ((d_c+1)/2) / (Γ((d_c−1)/2)·Γ(½))`，
**零新增依赖**（不引入 mpmath）。段 (2) 是显式的回归守护：它把「`81.3148°` 不是凸性边界」
写成可执行断言，而不是靠 docstring 措辞维持。

### Decision 3 — HIGH 3 + HIGH 4：σ 推导重做，两个数字一起错

`governance` obligation 7 的 worked instance 写着：

> per-cell SD `√(A(1−A)/M)`，`dG/dθ = 0.488421`，→ per-cell angle SD `0.0284°` →
> mean SE `0.0284°/√16 = 0.0071°` → `5σ = 0.0355°`

**这假设了 `N_e` 个胞腔面积相互独立。但它们不独立，而且不是「近似独立」——是确定性恒等式。**
实现是**单一** `M` 点集、每点 `argmax` 唯一归属：

    areas = bincount(owner, minlength=N_e) / M     ⇒   Σ_i n_i = M  恒成立

故 `Σ_i A_i ≡ 1` 精确成立，`Σ_i ε_i ≡ 0` 精确成立（`ε_i := A_i − 1/N_e`）。Taylor 展开：

    θ̂ − G⁻¹(1/N_e) = (1/N_e)·[ g'·Σε_i + ½·g''·Σε_i² + O(ε³) ]
                     └─ 一阶项恒为 0 ─┘

一阶项**恒消**，涨落是二阶。`Var(ε_i²) ≈ 2·Var(ε_i)² = 2(A(1−A)/M)²`，故

    Var(Σ ε_i²) ≈ 2·N_e·(A(1−A)/M)²      ⇒   涨落按 1/M 标度，不是 1/√M

代入 MVP（`d_c=16, N_e=16, M=1e6`），`G'(θ₀) = 0.488436`、`g'' = [G⁻¹]'' = −G''/G'³ = −24.6207`：

    σ = |g''|·A(1−A)·√2 / (2·√N_e·M) = 1.461e-5 °
    5σ = 7.31e-5 °

**两条独立证据互证**：

1. 闭式：`σ = 1.461e-5°`；
2. 实测：8 个 probe seed 在固定 `M` 下的 SD = `1.353e-5°`（spread `4.20e-5°`），吻合到 ~8%。

**HIGH 3 是同一段的算术错误**：`abs=1e-3` 对作者自己的 `5σ = 0.0355°` 是 `0.028×`，不是 `28×`
（漏小数点）。obligation 7 因此自相矛盾：对**修正后**的 `5σ = 7.31e-5°`，`1e-3` 是 `13.7×`。
本 change 写 `13.7×`，并在 obligation 7 正文写死「把 `N_e` 个面积当独立会得到 `5σ = 0.0355°`，
大 `486×`，MUST NOT be reintroduced」——**把错误写进规范当负面锚点**，比静默改掉更防回归。

连带更正：单侧性 Scenario 原写 `756σ / 319σ / 70σ`（对旧 `5σ` 自洽），在新 `5σ` 下是
`3.7e5× / 1.6e5× / 3.4e4×`。

### Decision 4 — MEDIUM 5：零面积胞腔**授权**而非抛错

`_dup_centroids(d_c, 8)`（8 份 `e_1` 拷贝）下实测 `areas = [250678, 249432, 249392, 250498, 0, 0, 0, 0]`
（`d_c=4, N_e=8`）—— 4 个胞腔面积为 0，每个贡献 `G⁻¹(0) = 0`，把 `θ̂` 系统性压低。

`G⁻¹(0) = 0` **在数学上是对的**（零面积胞腔的等效球冠半径就是 0）。而且
`test_voronoi_angle_one_sided_gap` 的三个见证（`8` 份 / `4` 份重复质心 + 12 站点反极对簇）
**故意**制造零面积胞腔。抛错会直接推翻 `decompmoe-skeleton` req-6 的既有 Scenario
「Realized measurement layer is one-sided…」，那是 spec 契约而非实现细节。

故：**授权并写进 spec**，同时在 docstring 标注它标志退化镶嵌（不是采样失败）。
这是「spec 缺口」的补齐，不是行为变更。

### Decision 5 — MEDIUM 6 + 7：dtype 回归修复与单位范数契约

**MEDIUM 7（回归）**：旧实现 `centroids @ centroids.T` 两侧同 dtype，`float64` 可用。
重写为 `probes @ centroids.T` 后，`probes` 来自默认 `float32` 的 `torch.randn`，于是
`RuntimeError: expected m1 and m2 to have the same dtype, but got: float != double`。

修法：`.to(centroids.dtype)`。**不改 float32 路径的任何数值**（`randn` 仍按默认 dtype 生成后
归一化，再转换），故无回归；实测 `float32` 与 `float64` 在同一夹具上给出**逐位相同**的
`1.5707963267948966`。

**MEDIUM 6（静默错误）**：owner 是 `argmax_i (p̂ · c_i)`。这只在每个 `‖c_i‖₂ = 1` 时等同于
「按夹角取最近站点」；否则内积被 `‖c_i‖₂` 缩放，一个**远但长**的站点会压过**近但短**的站点，
实现的镶嵌与调用者意图静默不同。

修法：`allclose(‖c_i‖₂, 1, atol=1e-6, rtol=0)` 否则抛 `ValueError`，消息点名**行号**与修复建议。
选择抛错而非静默归一化：静默归一化会掩盖调用者的 bug，且本模块既有错误路径
（`dim()` / `N_e < 2` / `d_c < 2` / `num_experts < 2`）都是抛错风格。
`1e-6` 对 float32 累积（约 `1e-7`）有 10× 余量。实测 23 个既有测试无一 fixture 被误伤。

### Decision 6 — LOW 8 / 9 / 10 与界收紧

**LOW 8**：`e(θ) = arccos(1 − 2sin(θ/2)) − θ`，`e′ = 0 ⟺ 3s² − 4s + 1 = 0 ⟺ s = 1/3`。
精确值 `θ* = 2·arcsin(1/3) = 38.9424412689814°`，`e(θ*) = 31.5863380965279°`。
docstring 写 `38.9420°` / `31.5868°`，第 4 位小数错。改为 10 位小数直接钉精确值。

**LOW 9**：`test_voronoi_angle_reflected_cap_branch_n_e_2` 用两站点 20° 对称夹具，断言
`approx(90.0, abs=1e-2)`。但退化形式 `G⁻¹(mean A_i)` 在该夹具上**也**返回 `90.0°`，
所以这个断言**无法区分走了哪个分支**。改为 spy `sphere._cap_radius`：记录每次 `(area, radius)`，
断言存在 `area > 0.5` 且其 `radius > π/2`。这才是「反射分支确实经由 `voronoi_angle` 执行过」的直接证据。
（原测试已有的 `areas.max() > 0.5` 检查保留，它验证的是夹具而非调用路径。）

**LOW 10**：archived `design.md` §1.6 记 `runtime 0.155 s`（实测 `0.098–0.132 s`），
`tasks.md` D.7 同。**不改 archived 字节**——它们是历史变更日志，不是真相源。改为在本
`design.md` 记录 supersession。**LOW 8 的 `31.5868°` / `38.9420°` 同样出现在 archived `design.md`，
处置一致。** 若审计偏好字节级更正历史，需另开 change 并显式声明该惯例。

**界收紧**：`test_voronoi_measurement_layer` 的 `1.0°` 对真实 gap `0.0399°` 有 25× 余量
（reviewer 指出过松）。收到 `0.2°`（5× 余量）。这仍远大于 `5σ = 7.31e-5°`，因此继续是
commensurability 界而非统计界——测试 docstring 已说明该 fixture 的 gap 是**真实**偏差
（其点集有效秩 3，胞腔本就不等面积），统计界会误杀真信号。

## Supersession 记录（审计用）

以下内容出现在 `openspec/changes/archive/2026-09-29-fix-voronoi-angle-measurement-layer-semantics/`
中，**已被本 change 取代**，保留原样仅作历史：

| 位置 | 陈旧内容 | 取代为 |
|---|---|---|
| `design.md` §1.6 表 | per-cell SD `0.0284°`、mean SE `0.0071°`、`5σ 0.0355°` | `σ = 1.461e-5°`、`5σ = 7.31e-5°`（`ΣA_i ≡ 1` 下一阶相消） |
| `design.md` §1.6 | runtime `0.155 s` | 实测 `0.098–0.132 s` |
| `design.md` §1.5 | 峰值 `+31.5868°` @ `38.9420°` | `+31.5863380965°` @ `38.9424412690°` |
| `design.md` / `tasks.md` D.7 | seed 稳定性 `8.6e-5°`（4 seeds） | `4.20e-5°` spread、`1.353e-5°` SD（8 seeds） |
| `design.md` / spec / 测试 | `θ_conv(d_c)` 凸性边界 | `G` 在 `(0, π/2)` 严格凸，前提 `∀i: A_i < 0.5` |

**唯一真相源是 `openspec/specs/**/spec.md`（`CLAUDE.md` §2 第 1 级）**，本表仅为审计导航。

## 复现脚本

本 change 的全部数字由两个脚本产出（系统 temp 目录，不入库）：

- `check_theta_conv.py` — `G''` 解析 vs 50 位 FD vs 仓库求积的三方对照（BLOCKER 1）；
- `fix_numbers.py` — `σ` 闭式 + 跨 seed 实测 + `1/M` 标度 + 峰值精确值 + 运行时 + 零面积胞腔 + dtype 回归。

两者均以 `mp.mp.dps = 50` 运行，`G` 一律用 `mp.betainc(..., regularized=True)` 而非仓库求积。
