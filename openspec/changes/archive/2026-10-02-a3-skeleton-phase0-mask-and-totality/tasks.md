# Tasks

- [x] 1.1 pre-flight 全部 needle。验证：4 个 needle（req-1 `__all__` 句 / req-7 输出一致性 THEN / req-18 签名句 / req-18 Phase 0 条目）在写入前全部命中。**→ 4/4 命中。**
- [x] 1.2 req-18 `mask` 升为 REQUIRED 位置参数条款。**→ 完成，写明「MUST 拒绝而非替代」及其机制（全批均值广播 → territory collapse）。**
- [x] 1.3 req-18 Phase 0 义务升格为规范性 MUST。验证：交叉引用已收窄的 `wayfinder` req-23（Phase 1–4）。**→ 完成（见 design.md D1：两侧必须成对，否则 Phase 0 变成契约真空）。**
- [x] 1.4 req-1 增补去重规则。验证：并集 **75**、包级含 3 dunder = **78**、求和 **76** 明确标为 MUST-NOT；`flops_per_token` 绑定 `config` 且 `metrics` 版保持可达。**→ 完成（design.md D3：三个数一起写，避免下游重踩求和 vs 并集）。**
- [x] 1.5 req-7 输出一致性断言加前置条件（X-main38）。验证：与 req-19 使用同一阈值 `ε = 1e-6`；**未**放宽 1e-5 容差（design.md D4：缺的是适用条件不是精度）。**→ 完成。**
- [x] 1.6 块级 diff 回验。验证：req-1 / req-7 / req-18 三块逐行 `unified_diff`；旧 req-7 无条件断言**已不再是整行**。**→ 3 块 diff 如期；旧行作为子串保留是新行的前缀（预期），作为整行已消失。**
- [x] 1.7 anchor 契约 + 行尾复算。**→ standalone anchor 23 = `### Requirement:` 23、无重复、CRLF 645/645、bare LF 0 ✅**（首轮报的 39 命中 + req-17/req-20 重复是复核脚本过计数，见 design.md D5）。
- [x] 1.8 门禁。验证：`lint_no_dead_defensive.py` exit=0 ✅；`lint_no_source_field_drift.py` exit=0 ✅；`openspec validate --specs` 3 passed / 0 failed ✅；`pytest tests/` **227 passed** ✅。
  > **复核脚本抓到的第二个自造缺陷**：脚本检查「每个 Requirement 是否有反链」并报 18 条缺失。实际 lint 规则是「**每条存在的 `**Source:**` 行**须含反引号反链」——本 spec 仅 4 条 Source 行且 4 条合规。脚本凭空发明了一条不存在的规则（design.md D5）。**未据此改动 spec。**

---

**非目标（明确不在本 change 范围）**：req-1 的 75/78 整数闭式测试（bare `==`，禁 `pytest.approx(abs=0)`）与 req-18 `mask` 必填的代码侧签名落地，属于后续配套代码 change。本 change 为 **spec-only**，其 `tasks.md` 不保留未完成任务——留一个永不相交的待办会让 `openspec validate --archived` 报 incomplete，等于把 scope 泄漏伪装成进度。

