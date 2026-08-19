# DecompMoE Wayfinder Map

> **本 map 的 status：CHARTING (step 3 完成，即将进 step 5 fire research subagents)**
> 命名已定：**DecompMoE**（见 Decisions so far）

## Destination

两份 deliverable：

1. **Decision 文档 (ADR-style)**：每个 design decision 的备选方案、为什么选这个、走过的 trail
2. **数学架构设计 (Spec-style)**：完整的形式化、训练流程、关键算法、复杂度分析

两件产物伴生，decision 文档是 rationale trail，spec 是造物本身。

## Notes

### Scope Lock
- **架构范式**：Decoder-Only Llama（标准 Multi-Head Self-Attention + SwiGLU FFN 替换）
- **显式排除**：Linear Attention / SSM (Mamba) / RNN 隐状态路由
- **不包含**：训练出 baseline 结果、完整 arxiv 论文写作（实验/ablation/相关工作综述）

### Complexity Budget
- **A3 提取算子**：Decode 阶段必须满足单 Token `O(d_c · d_k)` 或 `O(d_c)` 时间复杂度 + `O(d_c)` 空间状态
- **A7 推理增量**：维护 C 的状态开销必须 ≤ `O(d_c)` per token
- **任何 O(S) per token 的全量 KV 重算方案一票否决**

### Coupled Pair
- **A6a (Loss & Stability) ↔ A6b (Curriculum & Schedule)**：任一边界惩罚 / 阶段切换条件变更，必须同步校验另一边

### 工作约定
- **语言**：中文为主，数学符号用 LaTeX
- **grill 模式**：单题推进，agent 推荐答案 + 人类决定；不达成共识不烤下一个
- **type 标签**：本 map 几乎全 `grilling`；可能涉及 `research` 的 ticket：A3-1（算子选型可参考现有工作）、A8-1（baseline 选型）
- **依赖追踪**：每个 ticket body 标注 `Blocks` / `Blocked by` 边

### 领域 / skills
- 领域：MoE / Transformer 架构 / 数值优化
- 调用的 skill：grilling（默认入口）、domain-modeling（需要时引入）

## Decisions so far

<!-- 每关闭一个 ticket 加一行：gist + 链接 -->

- [A0-1 架构命名](tickets/A0-1.md) — 定 **DecompMoE**（decomposed MoE），3 音节，design 哲学主导；备选 GeoMoE（更 distinctive 但失 "分解" 表达）保留为 spec 中可引用的别名
- [A1-1 符号与术语规范](tickets/A1-1.md) — 形式符号 `Σ_i`，各向同性退化为 `σ_i² I`；引入 `P_i = Σ_i^{-1}` 精度矩阵作内部优化参量；subscript (i, l, h, t) 锁定；术语映射表 + 代码命名（`GeometricRouter` / `TerritoryHolder` / `territory_volume` / `active_territories` / `coverage_balance_loss` / `territory_seeding` / `territory_collapse`）；**A2-2 修订**：去掉 head 索引 h，符号退化为 per-layer `C_t^l / c_i^l / Σ_i^l / P_i^l`
- [A2-1 拓扑挂载点](tickets/A2-1.md) — 锁 **(A) Post-FFN 替换**（MVP 单变量原则）；显式排除 Pre-Attn 动态 Bias（Scope Lock）；Future Work 章节保留 "Extension: Pre-Attn Geometric Bias" 但不进入当前 MVP scope；FlashAttention / PagedAttention / 专家并行框架零侵入
- [A2-2 路由特征来源 + Head 聚合](tickets/A2-2.md) — **A2-2a**: l 层本层 K, V（per-token layer-wise）；**A2-2b**: Layer-wise Head-Aggregated（每层一个 C，per-layer `c_i^l, Σ_i^l`）；Future Work 保留 "Extension: Per-Head Territory Routing" + "Extension: Cross-Layer KV Conditioning"
- [A3-1 C 提取算子选型](tickets/A3-1.md) — **v2 球面归一化贯穿**：per-head 投影 → per-head 球面归一 → cross-head mean → final 球面归一；`C_t^l ∈ S^{d_c-1}`；`O(d_c · d_k)` per token；GQA-aware（`H_kv`）；v1 的 RMS Standardize 被 per-head spherical projection 替代
- [A3-2 C 提取可微性 + c_i 生命周期](tickets/A3-2.md) — C 提取全可微（D 路径，无 STE）；c_i 4 阶段生命周期：Phase 0 spherical k-means → Phase 1-3 masked spherical EMA（α=0.90→0.95→0.99，δ_g 死专家保护）→ Phase 4 projected SGD（球面 Riemannian）；解决鸡生蛋问题
- [A4-1 距离度量](tickets/A4-1.md) — 各向同性归一化弦长平方 `d = 1 - C^T c_i` ∈ [0,2]；有界 β 参数化 `β = β_min + (β_max-β_min)·Sigmoid(γ)`，β_min=0.1, β_max=32；Logit 形式 `logit = β(C^T c - 1)` ∈ [-2β, 0]；**3 个梯度上界 ≤ β_max = 32**（数值稳定硬保证）；Future Work: 各向异性 Fisher-von Mises 切空间 Mahalanobis；w_i 不入 Logit（post-aggregation 独立混合），A4-2 边界由 A4-2 决定
- [A4-2 门控函数形式](tickets/A4-2.md) — **彻底剔除 w_i**；Top-k 稀疏掩码 + Local Softmax + 纯几何凸组合；前向 `x_out = x + Σ_{i∈I_k} p_i · Expert_i(x)`，Σ p_i ≡ 1；**Native Sparse Sub-gradient**（-∞ 掩码让非 Top-k 梯度严格为 0，无需 STE）；MVP **k=2**
- [A5-1 专家内部结构](tickets/A5-1.md) — **Standard SwiGLU FFN**（与 Llama baseline 结构同构）；`Expert_i(x) = (SiLU(xW^g) ⊙ xW^u) W^d`；每专家 3·d_model·d_ffn；总参数 `N_e · 3·d_model·d_ffn`；激活 `k · 3·d_model·d_ffn`；**控制变量保证**：Expert 内部零 C 注入，性能差异唯一归因 A0-A4 路由链条；零 custom op，复用 vLLM/Megatron/DeepSpeed SwiGLU kernel；Future Work: Geometry-Aware Conditioning + Low-Rank Expert
- [A5-2 共享专家映射](tickets/A5-2.md) — **(0) 无共享专家**（Pure Geometric Routing）；公式 `x_out = x + Σ_{i∈I_k} p_i · Expert_i(x)` 严格保持；3 条数学保证：方差无漂移（Var[Δx|x] ≤ σ_e²）+ 槽位无侵占 + Mixtral 对齐；**Caveat**：交叉协方差 ≈ 0 需"独立初始化 + 训练充分分化"双前提；Future Work: 显式 shared expert + 球面 β→0 极限
- [A5-3 超参 Scaling](tickets/A5-3.md) — **(S) Standard MoE Scaling**（Mixtral 风格）；d_c=16, N_e=64, k=2, d_ffn=Align_16(4/3·d_model)；β schedule **1.0 → 16**（Phase 1 → Phase 3）；Capacity Factor 32x；**球面几何自洽**：θ_Voronoi 25.75° > θ_1/e 20.36°（β=16），g_boundary 0.205 仍有 tail overlap；Future Work: Fine-grained + 联合 scaling
- [A5-3 v2 4070 MVP](tickets/A5-3.md) — **4070 8GB 单卡可跑**：d_model=1024, N_e=16, k=2, d_ffn=2048, L=4；Total 452M / Active 100M；**Active FLOPs 1:1 严格对齐 Dense**（d_ffn_dense=4096）；球面几何仍自洽（θ_Voronoi≈52° > 20.36°）；Future Work: Fine-grained + 更大规模
- [A6a-1 损失函数构成](tickets/A6a-1.md) — `L_total = L_CE + α·L_lb + λ(t)·L_sep`；**α=0.01** 固定 L_lb (Switch style, f_i.detach)；**λ(t) 阶段 schedule**（0 → cosine ramp → 0.001）；L_sep = `(||C^T C||_F² - N_e) / (N_e(N_e-1))` 软正交损失；**Notation**: per-token `C_t^l` vs per-expert `C` 矩阵符号冲突 mark；Future Work: z-loss 兜底
- [A6a-2 数值异常恢复](tickets/A6a-2.md) — **执行顺序**: `Backward → clip(1.0) → step → L2_norm(c)` (一阶黎曼 SGD 等价)；5 项 safeguard: ① Global Grad Clip ② NaN 三级 escalation (1 skip / 3 LR÷10 / 10 halt) ③ **Splitting Resurrection** (clone j* + 0.85 协同衰减) ④ β Saturation Guard (30.4 warn / 28.8×50% LR÷2) ⑤ Loss Spike Defense (Phase 3+, 2.5×EMA, LR×0.8)；Inline/Periodic/Conditional 三类执行
- [A6b-1 4 阶段演进](tickets/A6b-1.md) — **5 阶段 1/5/20/30/44% 时长**；**β_max(t) 分段线性** (P1=1.0 / P2 1→4 / P3 4→16 / P4 [1,32] free)；**Time-Driven 切换**；阶段细节：P0 K-Means init / P1 专家训练 L_lb logging / P2 EMA α=0.95 + Resurrection / P3 EMA α=0.99 + L_sep cosine + Loss Spike & Saturation / P4 全部 + Projected SGD + **Adam 动量 reset**；**β 更新 = 标量空间 Box-Constrained Projected SGD**（与 c_i 球面 L2 Retraction 共享"投影约束"框架，几何不同）
- [A6b-2 阶段切换触发器](tickets/A6b-2.md) — **3 层混合**：Layer 1 Time-Driven 硬切（1K/6K/26K/56K/100K）+ Layer 2 State-Driven Advisory（4 信号：归一化熵 R_H / 负载偏斜 S_load / β 饱和 R_β-sat / 重叠指数 L_sep/WB，只读不自动切）+ Layer 3 Hard Cutoff；**D_c 排除实时监控归 A8 离线**（O(N_e²) + 阈值难定）
- [A7-1 Prefill vs Decode 解耦](tickets/A7-1.md) — **(S) 同样算法 + 零分支**；统一 `(L')` 投影 + 双重球面归一；张量 `[B, S, H_kv, d_k] → [B, S, d_c]`；**C 禁入 KV Cache**；Decode 走 SRAM/Registers（16 floats = 64 bytes，零 HBM 读写）；Prefill 走 HBM（Backward 需保留梯图）
- [A7-2 增量更新律](tickets/A7-2.md) — **(R) 无状态逐帧重算**；`C_t = L2_Norm((1/H_kv)·Σ_h L2_Norm(W^K k + W^V v + b))`；**~65.5K FLOPs/token, 0 Bytes HBM 读写**；C_t 对 decoder latency 影响 < 0.5%；**三类演化解耦**: C_t stateless / c_i EMA-SGD (A3-2) / W_proj AdamW
- [A7-3 硬件 / Kernel 友好度](tickets/A7-3.md) — **4 项硬件兼容 + 零 custom kernel**；物理参数：W_proj ~64KB 100% L2 驻留，激活 4KB 100% SRAM/RF 驻留，**0 HBM 增量流量**；框架兼容：FlashDecoding ✅ / PagedAttention ✅ / vLLM/TGI/SGLang/TRT-LLM/Megatron/DeepSpeed 全部 ✅；torch.compile ⚠️ 优化路径（Inductor 可自动融合，MVP 不依赖）；MVP 实现：PyTorch Eager Mode + 4 步原生算子
- [A8-1 Baseline 体系](tickets/A8-1.md) — **6 baseline / 4070 MVP 闭环**；Primary (E) Dense SwiGLU d_ffn=4096 + (M') Mixtral 复现 N_e=8 k=2 + (Q1) Qwen1.5-MoE-A2.7B QLoRA 压缩；Direct (G) GMoE X-空间欧氏距离；Ablation (R) Random Routing + **(S') Random Centroids**（A3-2 质心学习隔离）；**Active FLOPs 1:1 严格对齐**（MoE 50.4M = Dense 50.4M per token）
- [A8-2 几何量化指标](tickets/A8-2.md) — **8 指标分 2 类**（4 实时 + 4 离线）；实时：L_sep (c_i 散布) / R_H (利用熵) / S_load (负载偏斜) / UR (使用率)；离线：SP (特化纯度) / D_c (球面 geodesic 散布) / **MCI** (有效维度占比，替代 CV 因球面下界不可达) / CG (Debug only)；L_sep 改写为 `(1/(N_e(N_e-1)))·Σ(c_i^T c_j)²` 清晰形式（与旧 L_sep 等价）
- [A8-3 可视化工具链](tickets/A8-3.md) — **6 模块 production-ready spec**；3D PCA (固定视角 25/135) + D_c 热力图 (Optimal Leaf Ordering) + 2D Voronoi (椭圆 β 拟合) + 轨迹动画 (固定 W_PCA) + TensorBoard dashboard + plantuml 文档；工具栈 matplotlib/sklearn/scipy/imageio/tensorboard/plantuml
- [WF-1 Audit OpenSpec Docs Completeness](tickets/WF-1.md) — PASS-WITH-WARNINGS：21 ticket 全部 1:1 映射到 spec Requirement，`openspec validate --strict` 通过；3 项 minor warning（proposal 未显式 R/S 数、design 引用无 anchor、tasks 2.4 描述精度），均不影响 archive；后续可进入 `/opsx:archive`
- [WF-2 Polish OpenSpec Spec](tickets/WF-2.md) — PASS：3 项 WF-1 warning 全部收敛（proposal R/S 数 / spec 锚点 + design 相对链接 / tasks 2.4 判定路径拆分）+ 21 ticket deep-check 发现的 A4-1 γ 梯度上界精度修正（15.95 ⊂ 32 子集，行为契约未扩张），`openspec validate --strict` 双 change 通过；archive 顺序 polish → introduce 已执行，主 spec `openspec/specs/wayfinder/spec.md` 落地 21 锚点 / 21 Requirements / 34 Scenarios

## Map Status: CHART COMPLETE

> **全部 20 tickets 关闭**——Spec 全文可由 decisions + ticket body 编译
> 下一步 effort（spec 文档外）：编译 spec 主文档（plantuml + decision trail + math spec）；执行 A8 baseline 矩阵（需新 effort）

## Dependency DAG

```
[Scope Lock: Decoder-Only Llama] ──────────────────────────────────────────┐
                                                                         │
A0 命名 ─┐                                                               │
          ├→ A1 符号 ──┐                                                 │
          │            ├→ A2 拓扑 ──┐                                   │
          │            │            ├→ A3 提取 ──→ A4 门控 ──→ A5 专家  │
          │            │            │                                    │
          │            │            ├→ A7 推理增量 (← A3, A5)            │
          │            │            │                                    │
          │            └→ A6a 损失 ─┐                                   │
          │               A6b 调度 ─┘ (coupled)                         │
          │                                                               │
          └────────────────────────────────────────────────→ A8 评估 ←──┘
                                                                  (← A2, A3, A5, A6)
```

## Not yet specified

10 个 arena 的全部 ticket 已在 `./tickets/`，等 grill 推进。

可能在 grill 中浮现的 fog：
- A6a / A6b 之间的具体耦合形式（loss 各项系数怎么随阶段变化）
- A8 的几何可观测性指标的"好"范围（什么样的 separability index 算"健康"）—— 需要实验才能定，但 spec 阶段先定性

## Out of scope

- **Linear Attention / SSM (Mamba) / RNN**：本 map 只在标准 Multi-Head Self-Attention 框架内（Scope Lock）
- **训练跑出 baseline 结果**：destination 是 spec + decision 文档，不包含实验执行
- **完整 arxiv 论文写作**：实验、ablation、相关工作综述不属本 map
- **具体超参数数值**：spec 阶段定选择策略，不定 k=2 还是 k=3 这种具体值
- **推理引擎实现代码**：spec 算法，code 留给后续 effort
- **数据集选型 / 数据准备**：仅在 A8 评估时列出该用什么任务，但不做数据 pipeline
- **Checkpoint 兼容性 / 模型转换工具**：从零设计，不涉及从 dense 或其他 MoE 转换
