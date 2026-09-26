## Why

per `proposal.md` Why 段。本设计文档详述 4 项 fix 的 per-decision rationale + alternatives considered + risk mitigation。

## Per-Fix Decision Rationale

### Decision 1: A1.1 修复方式 = §4 frame disclosure 措辞补丁 (option D1=a)

**Choice**: `req-gov-1` 加 §4 `Residual frame disambiguation`,spec 必须 explicit 选 impl-internal 或 mpmath true reference 当 "< 1e-9" claims 的参考帧。原 §4(`f"actual={...}"` 嵌入义务)顺位 §5。

**Rationale**:
- 实测两参考帧都成立:impl-internal(`_betainc_regularized` Gauss-Legendre 8-point 60-segment quadratic approximate)at `1.1735482746999482 rad` gives `|½·I_{sin²θ}(7.5,½) − 1/16| = 1.164e-14 ✓`;mpmath `betainc(regularized=True)` true reference at same θ gives `4.146e-7`。
- 两参考都是 **mathematically defensible**:impl-internal 是 impl 自洽精度(true to its own bisection root-finding);mpmath true 是真闭式积分精度。
- `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` PASS 验证的是 impl-internal claim(test uses `_betainc_regularized`,L73 `sphere._betainc_regularized(s2, (16 - 1) / 2.0, 0.5)`)。
- spec 没明示参考帧是 wording 缺陷:reader 看 `< 1e-9` 不知是 impl vs true。
- 修法选 explicit disambiguation 而不是 implicit(比如改 `< 1e-9` → `< 2e-7` 之类):explicit 保留 spec 现有 precision claim 强度同时锁参考帧。

**Alternatives considered**:
- (a) `**只**`加 §4 frame disclosure 措辞 —— **采纳**:最小 wording 改动,spec precision 强度不变,refers-to-existing 形式
- (b) 同时修 wayfinder L233(原文 "(closed-form residual ... < 1e-9)" wording 加 "impl-internal" 限定) —— 拒绝:跨多 file 改 wording 风险扩大,scope 越界 per plan D1 推荐
- (c) 改 impl `_betainc_regularized` 实现到 mpmath 一致性精度 —— 拒绝:out of scope per plan,行为变更需独立 ticket;且 performance cost 未知(Gauss-Legendre 8-point 是 implicit performance choice)

**Wording 内容**:
```
4. **Residual frame disambiguation** — claims of "< 1e-9" or similar precision bounds on bisection Voronoi output MUST specify the reference regularized incomplete beta implementation:
   - **impl-internal reference**: `_betainc_regularized` (Gauss-Legendre 8-point, 60 subintervals) at the canonical value `1.1735482746999482 rad` yields `|½·I_{sin²θ}(7.5, ½) − 1/16| = 1.16e-14` (impl-internal `< 1e-9` ✓)
   - **true closed-form reference (mpmath `betainc(regularized=True)`) at the same θ**: `4.15e-7` (NOT `< 1e-9`; impl-systematic-error bound)
   Spec MUST clarify which frame is used for "< 1e-9" claims. Either frame is acceptable as long as the frame is explicit (avoid silent reference-frame shifting).
```

### Decision 2: A1.2/A1.3 修复方式 = 加新 Scenario (option D2=a)

**Choice**: `req-6` 在 `Scenario: N_e dependence of voronoi_angle` (L104-L106) 与 `Scenario: no hard-coded table values` (L108-L110) 之间加新 Scenario `Bisection output + narrative precision disclosure`。

**Rationale**:
- 现状 `Scenario: MVP self-consistency` 和 `Scenario: N_e dependence of voronoi_angle` 都是 `[residual < 1e-9] AND [≈ 1.1735 rad] AND [exceeds θ_{1/e}]` 形式,reader 易把 narrative `≈ 1.1735 rad` 直接代入算 residual。
- 加新 Scenario 把 precision 关系 explicit 写出:prose 4-decimal vs impl output 16-digit vs impl-internal residual vs mpmath true residual。
- 不改原 wording 是 plan D2 推荐:cycle-23 已修过 spec L122 (0.0284 → 0.02845) 之类的路径,改了 narrative ≈ 字面可能踩其他 cycle 反链。保留原 wording + 旁注 disclosure 是最安全。

**Alternatives considered**:
- (a) 加新 Scenario 旁注 disclosure —— **采纳**
- (b) 改原 Scenario wording 加 explicit parenthetical —— 拒绝:risk 把原 `≈ 1.1735 rad` 改成更长字面,影响外部 reference grep(A5-3 / A8-1 ticket 反链可能 verbatim 引用 `1.1735 rad` 字面)
- (c) 加 impl-output 与 narrative 双重 wording —— 拒绝:不增加信息密度,只是 wording 加 redundancy

**Wording 内容**(整新 Scenario):
```
#### Scenario: Bisection output + narrative precision disclosure

- **WHEN** reviewing the MVP self-consistency Scenario above (`≈ 1.1735 rad`) and the N_e-dependence Scenario below (`≈ 1.0205 rad`)
- **THEN** the reader understands:
  - `≈ 1.1735 rad` / `≈ 1.0205 rad` are narrative prose at ~4-decimal precision; NOT exact bisection values
  - The impl bisection OUTPUT is `1.1735482746999482 rad` (N_e=16) / `1.0205068335735599 rad` (N_e=64) at 16-digit precision
  - The impl-internal residual vs `_betainc_regularized` at the impl output is `< 1e-14` (per `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`)
  - The true closed-form residual vs mpmath `betainc(regularized=True)` at the impl output is `4.15e-7` (N_e=16) / `1.43e-9` (N_e=64); the N_e=64 impl output sits just above the `< 1e-9` reference floor at `1.43e-9` (close to the bisection noise floor; NOT below it, despite the small magnitude), while the N_e=16 impl output has larger residual (~`4e-7`) but still well within the `< 1e-6` spec tolerance per req-gov-1 §3
  - The discrepancy `8.49e-7 rad` (N_e=16) / `8.79e-9 rad` (N_e=64) between true bisection solve and impl output reflects Gauss-Legendre 8-point 60-segment systematic error in `_betainc_regularized`, bounded to < 1 ppm
```

### Decision 3: A1.5 修复方式 = L146 wording 重写 (option 内 no-option,唯一 fix)

**Choice**: `req-7 L146` 重写 THEN clause + L156 同步修 wording。

**Rationale**:
- A1.5 是 wording 矛盾客观存在:`truncated at 5 significant figures` 字面意思是 5-sig truncation(产 `0.028453`),但 narrative `0.02845` 是 4 sig figs。spec L146 自己 quote `\|0.028453−0.02845\| = 3e-6` acknowledge 这个 gap。
- 这种 "self-acknowledge 矛盾" 在 formal spec 里是 wording bug 的确凿证据(spec 知道不一致却留下来)。
- 修法选 option "rounded to 4 significant figures" + 反链 cycle-23 Decision 4:既 keep narrative 字面(cycle-23 fix 决策产物,不能回退),又 explicit 标 "4 sig figs rounded,NOT 5 sig figs",与 L156 测试 guard 一致。

**Alternatives considered**:
- 唯一 fix 是改 wording,无 alternative(因为 wording 矛盾客观存在)。**采用 opinionated wording**:`rounded to 4 significant figures (round-half-up or truncate-then-format, both yield 0.02845); the 5-sig-fig truncation would yield 0.028453, NOT displayed; the discrepancy is intentional — narrative precision is 4 sig figs to align with β_0 ≈ 1.035 (4 sig fig) closed-form style elsewhere in this Requirement (per Decision 4 of change `01-fix-ticket-stale-numerical-4file-batch` proposal)`。

**Why not just delete "truncated at 5 sig figs" 替换为 "rounded to 4 sig figs"**:这等价于本 decision,但需要明确 "两种 rounding 都产 0.02845" + 反链 cycle-23 Decision 4 + 解释 discrepancy intentional。

**Wording 内容**:
- L144 (Scenario header): `σ'(−3.5) narrative precision matches 50-digit mpmath within **5** significant figures` → `... within **4** significant figures (narrative form)`
- L146 (THEN clause):整段重写为:
```
- **THEN** the narrative value `σ'(−3.5) ≈ 0.02845` matches the 50-digit mpmath value `0.02845302387973555984` rounded to 4 significant figures (round-half-up or truncate-then-format both yield `0.02845`); the 5-sig-fig truncation would yield `0.028453`, NOT displayed; the discrepancy is intentional — narrative precision is 4 sig figs to align with `β_0 ≈ 1.035` (4 sig fig) closed-form style elsewhere in this Requirement (per Decision 4 of change `01-fix-ticket-stale-numerical-4file-batch` proposal)
```
- L156 (Scenario L153-157 AND clause): `that nails the L122 narrative **5-sig-fig** precision disclosure` → `that nails the L122 narrative **4-sig-fig** precision disclosure`

### Decision 4: A1.4 修复方式 = blockquote footnote (option D3=a)

**Choice**: `req-11` L237 后 L239 前加 blockquote footnote,覆盖 N_e=16 行 and N_e=64 行。

**Rationale**:
- A1.4 是 prose 双显示精度不一致:`67.24°` ≈ 4-decimal-degree / `1.1735 rad` ≈ 4-decimal-rad ≠ 5-decimal-rad,差 5.94e-5 rad 是 dual-prose 独立 rounding。
- 修法选 footnote 不破坏原 wording(plan D3 推荐):原 `67.24° (≈ 1.1735 rad)` 形式保留,footnote 解释 dual display precision 的 rounding 独立性。

**Alternatives considered**:
- (a) blockquote footnote —— **采纳**
- (b) 改原 L236-237 wording 用 true 8-digit form —— 拒绝:cycle-23 fix 之后 narrative 形式已经被 L156 测试 guard (`pytest.approx(0.02845, abs=1e-5)`) 等多 surface 反链 verify,改了 risk 引发 cycle 连锁反应。
- (c) 删 dual-display 只留 1 种 —— 拒绝:同样 risk 引发 surface 反链 break。

**Wording 内容**(单个 blockquote 覆盖 two rows):
```
> **Display precision note**:
> - `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`: `67.24°` (4-decimal-degree = 4-sig-fig for angle) and `≈ 1.1735 rad` (4-decimal-rad = 5-sig-fig for rad) are dual prose forms referring to the same impl bisection output `1.1735482746999482 rad = 67.2393145636...°`. The two displays differ by `67.24° × π/180 − 1.1735 = 5.94e-5 rad` due to independent prose rounding; both lie within the `< 1e-6 rad` test tolerance prescribed by req-gov-1 §3.
> - `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`: similar dual-prose pattern; impl output `1.0205068335735599 rad = 58.47073...°`; display diff `58.47° × π/180 − 1.0205 = −5.99e-6 rad` (negative sign: `58.47° × π/180 = 1.0204940... < 1.0205 rad`), magnitude `|diff| ≈ 5.99e-6 rad` within the `< 1e-4 rad` tolerance.
```

## Risk Mitigation Per-Fix

### A1.1 Mitigation

- **wording regression**: 加 §4 不删原 §3 wording,原生 precision 强度(impl-internal `< 1e-9` claim)保留
- **lint regression**: 不改 Source 字段 / 不新增 anchor,lint `exit=0` 不变
- **CRLF**: governance/spec.md 含 `<`/`≤` 等 non-ASCII;Edit 后跑 byte-level CRLF check

### A1.2/A1.3 Mitigation

- **wording regression**: 加新 Scenario 不改原 Scenario L100-L106 与 L108-L110,wording byte-level 一致(except blank lines for new Scenario)
- **reference 保持**: 原 `≈ 1.1735 rad` / `≈ 1.0205 rad` verbatim 留在原 Scenario,新增 disclosure 只补充额外信息
- **CRLF**: decompmoe-skeleton/spec.md 含 non-ASCII;byte-level CRLF check

### A1.5 Mitigation

- **wording regression**: L146 重写是新 wording,但 narrative 字面 `0.02845` 完全不变;L156 wording 微调 `5-sig-fig` → `4-sig-fig`,不引入新信息只精确 precision claim
- **narrative 字面不动**: `0.02845` 不变 → tests `pytest.approx(0.02845, abs=1e-5)` 不变 → cycle-23 Decision 4 决策产物不被回退
- **反链 Decision 4**: 新 wording explicit 反链 `Decision 4 of change 01-fix-ticket-stale-numerical-4file-batch`,便于未来审计
- **CRLF**: wayfinder/spec.md 含 non-ASCII;byte-level CRLF check

### A1.4 Mitigation

- **wording 零回归**: footnote 加在 L237 后 L239 前,**不动** L236 / L237 原 wording 任何字符
- **footnote 形式**: blockquote `>` 是 standard markdown,不破坏现有段落结构
- **CRLF**: wayfinder/spec.md 含 non-ASCII;byte-level CRLF check

## Out-of-Scope Decisions (D5 / D6)

### D5: archive trigger = 留作 deferred 下个 cycle archive (option D5=b)

**Rationale**:
- precision-disclosure 类 wording fix 不是 cadence-赶 的安全/正确性问题,没必要立刻 archive
- 留作下个 cycle archive 允许 cycle 内继续 audit 期间,新 finding 同时进同 change(避免多 change split 同一组 wording fix)
- plan D5 推荐 (b),与 plan 推荐保持一致

### D6: wayfinder ticket annotations = 不动 (option D6=a)

**Rationale**:
- per CLAUDE.md §8 (wayfinder tickets advisory non-binding, 不影响 src/ 实现)
- cycle-23 `01-fix-ticket-stale-numerical-4file-batch` 已经把 A4-1 L58 + A5-3 L62 + A1-1 L97 加了 supersede annotation,本 change 范围内 **没有新 ticket stale 数值源头**,故无需再加 new 注释
- 不动 ticket 也是 plan D6 推荐
