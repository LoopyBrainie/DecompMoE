# Tasks

- [x] 1.1 pre-flight 全部 needle。验证：5 个 needle 在写入前全部命中（req-2 尾部 / req-15 Layer 2 / req-23 正文 / req-23 Scenario WHEN / req-23 Scenario 标题），任一缺失则不写入。**→ 5/5 命中。**
- [x] 1.2 req-23 收窄为 Phase 1–4。验证：正文加 Phase scope 注记；Scenario WHEN 改为 Phase 1–4；标题改为 `Spherical norm is strictly one in Phase 1-4`。**→ 完成。**
- [x] 1.3 req-2 增补 `territory_collapse` deferral 注记。**→ 完成，挂在 L24 单行内（1387 字符）。**
- [x] 1.4 新增 req-38 Territory Collapse Deferred Contract。验证：反链为 `` `wayfinder/tickets/A1-1.md` ``（真实血缘：A1-1:112 的标识符映射表含该行，且 A1-1 是 req-2 自身反链票）。**→ 完成。**
- [x] 1.5 req-15 增补 Layer 2 deferral note。**→ 完成。**
- [x] 1.6 块级 diff 回验（非 grep）。验证：req-2 / req-15 / req-23 三块逐行 `unified_diff`；旧 WHEN 子句「any Phase (0 K-Means」已消失。**→ 3 块 diff 如期，旧 token 扫描 0 残留。**
- [x] 1.7 anchor 契约复算。验证：standalone anchor 数 = `### Requirement:` 数 = 37、无重复、CRLF 保留。**→ 37/37/无重复 ✅（见 design.md D5：先报的 39 命中 + req-17/req-20 重复是复核脚本自己的过计数，HEAD 本来就是 38 命中含 2 处反引号内行内引用）。**
- [x] 1.8 门禁。验证：`lint_no_dead_defensive.py` exit=0 ✅；`lint_no_source_field_drift.py` exit=0 ✅；`openspec validate --specs` 3 passed / 0 failed ✅；`pytest tests/` **227 passed** ✅；每个 Requirement 均有 `wayfinder/tickets/...` 反链（脚本复算 0 缺失）✅。
