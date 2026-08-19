## Why

DecompMoE 的 OpenSpec 主 spec (`openspec/specs/wayfinder/spec.md`) 已经固化了 21 Requirements × 34 Scenarios，但代码层目前只有 `pyproject.toml` —— 无任何 `.py` 文件、无 `.git/`、无 CI。形式化契约已存在，缺可 TDD 验证的最小骨架。本 change 把 spec 中可测的全部 21 R × 34 S 变现为纯函数数学层 + 类型化骨架（Protocol + frozen dataclass + 无执行体），让 spec 与 code 之间产生可执行反链；不写可运行 forward/backward，遵守 CLAUDE.md §6 的 formalize-only 约束。

## What Changes

- **新增** `src/decompmoe/` Python 包（12 个模块 + 公共入口），全部为类型化骨架 + 纯函数数学层，无可运行 forward/backward
- **新增** `tests/` 下 12 个 pytest 文件，1 对 1 镜像 12 个 ST（Sub-Task），用 `pytest` 验证 spec 中的可测项
- **不引入** 训练执行、baseline 跑数、ArXiv 论文、推理引擎实现代码、Linear Attention / SSM / RNN 替代方案、custom CUDA / Triton kernel、共享专家、`w_i` 进入 logit、`C_t` 写入 KV Cache
- **不修改** `openspec/specs/wayfinder/spec.md` —— 本 change 是骨架/spec 完全对齐验证，行为契约不动

## Capabilities

### New Capabilities
- `decompmoe-skeleton`: 12 个 ST 子任务的可 TDD 验证骨架 + 纯函数数学层（覆盖 Req 1–21 的可测项）

### Modified Capabilities
- (none — 本 change 不修改任何既有 capability 的 Requirements；`wayfinder` 主 spec 保持冻结)

## Impact

- **新增文件**: `src/decompmoe/{__init__,config,contracts,beta,sphere,extraction,distance,gating,experts,loss,safeguards,schedule,metrics,viz}.py`（14 个文件，含 `__init__.py`）
- **新增文件**: `tests/test_{config,contracts,beta,sphere,extraction,extraction_phase,distance,gating,experts,loss,safeguards,schedule,metrics,viz_protocols}.py`（14 个文件）
- **依赖**: 仅使用既有 `torch==2.12.1` + `torchvision==0.27.1`；新增 dev 依赖 `pytest`（验证用，但因 spec 不要求执行，可暂不加入 `pyproject.toml`）
- **外部 API**: 无（本 change 是 internal skeleton，不暴露 public API）
- **架构**: 类型化骨架 + 纯函数数学层 —— 不可执行 forward/backward；所有可执行逻辑必须另起 change 走 `/opsx:propose`