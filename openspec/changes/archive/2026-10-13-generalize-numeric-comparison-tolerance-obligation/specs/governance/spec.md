# Spec Delta

## ADDED Requirements

<a id="req-gov-13"></a>

### Requirement: Default Relative Term In A Numerical Comparison Must Be Declared And Derived

A numerical comparison performed by a comparator whose relative-tolerance parameter defaults to a nonzero value MUST supply that parameter explicitly, and the supplied value MUST be derivable from the magnitude of the protected quantity and the precision the spec declares for it. A comparison MUST NOT rely on an unstated default relative term. A comparator whose relative term defaults to absent (an absolute-only form) is not constrained by this Requirement.

#### Scenario: Relative term left at an unstated default
- **WHEN** a test compares two values with a comparator whose relative-tolerance parameter defaults to a nonzero value (e.g. `torch.allclose` with `rtol` defaulting to `1e-5`) and does not supply `rtol` explicitly
- **THEN** the relative term MUST be treated as undeclared, and the assertion MUST NOT be counted as satisfying a derived-tolerance obligation

#### Scenario: Relative term supplied and derived
- **WHEN** a test supplies the relative-tolerance parameter explicitly with a value derived from the protected quantity's magnitude and the spec-declared precision, or omits the relative term by using an absolute-only comparator
- **THEN** the assertion satisfies this Requirement

**Source:** `CLAUDE.md` §6 (Hard Constraints — 数值直接对账 / 阈值须可导出), §6 第 8 条 (对账方式依数值类型二分), change `generalize-numeric-comparison-tolerance-obligation` design.md (Decision D2 — originating audit findings FIX-001, 隐式 `rtol` 默认参与判定; FIX-020, req-gov-1 枚举代替一般义务)

<a id="req-gov-14"></a>

### Requirement: Numerical Comparison Must Declare At Least One Tolerance

A numerical comparison MUST NOT be asserted without supplying at least one of an absolute tolerance or a relative tolerance. A comparison whose pass condition is therefore decided entirely by comparator defaults MUST NOT appear, because no party selected either bound.

#### Scenario: Neither tolerance supplied
- **WHEN** a test asserts a numerical comparison supplying neither an absolute nor a relative tolerance (e.g. `torch.allclose(a, b)` with no `atol`/`rtol`)
- **THEN** the assertion violates this Requirement, because its pass condition is decided solely by comparator defaults

#### Scenario: At least one tolerance supplied
- **WHEN** a test asserts a numerical comparison supplying at least one explicit tolerance (absolute or relative)
- **THEN** the assertion satisfies this Requirement

**Source:** `CLAUDE.md` §6 (Hard Constraints — 数值直接对账 / 禁止文字断言), change `generalize-numeric-comparison-tolerance-obligation` design.md (Decision D2 — originating audit finding FIX-001, 3 处比较完全不给容差)

<a id="req-gov-15"></a>

### Requirement: Negative-Polarity Numerical Comparison Must Declare Its Tolerance

A comparison asserted in the negative (an assertion that two quantities differ beyond a tolerance) MUST supply its tolerance explicitly. For a negative-polarity assertion the relative term widens the band of values considered equal, making the assertion harder to satisfy; an unstated default relative term therefore acts in the direction opposite to a positive-polarity assertion. An undeclared tolerance on such an assertion MUST be treated as not given.


#### Scenario: Negative-polarity assertion with unstated default
- **WHEN** a test asserts `not <comparator>(a, b)` without supplying `rtol`, on a comparator whose relative term defaults to a nonzero value
- **THEN** the default relative term widens the equality band and makes the negative assertion stricter; the tolerance MUST be treated as undeclared and MUST be supplied explicitly to state the assertion's true bound

#### Scenario: Negative-polarity assertion with declared tolerance
- **WHEN** a test asserts a negative-polarity comparison supplying its tolerance explicitly
- **THEN** the assertion satisfies this Requirement

**Source:** `CLAUDE.md` §6 (Hard Constraints — 测试须测原理, 阈值须可导出), change `generalize-numeric-comparison-tolerance-obligation` design.md (Decision D3 — originating audit finding FIX-001, 8 处 `assert not torch.allclose` 中默认 `rtol` 方向与失明相反)

<a id="req-gov-16"></a>

### Requirement: Tensor Closed Form Is Guarded By An Explicit Relative Term

A spec-declared float closed form whose value is a **tensor** MUST be guarded by `torch.allclose(a, b, atol=X, rtol=0.0)` with `X` explicit and derived, or by an exact-equality assertion when the claim is an identity. `pytest.approx` MUST NOT guard it. A **scalar** float closed form continues under req-gov-1 obligation 2 to use `pytest.approx`; this extends that form to tensors.

**Source:** `CLAUDE.md` §6, change `generalize-numeric-comparison-tolerance-obligation` design.md (D6)

#### Scenario: Tensor closed form guarded by an explicit absolute tolerance
- **WHEN** a test verifies a spec-declared float closed form whose value is a tensor, using `torch.allclose(a, b, atol=X, rtol=0.0)` with `X` stated and derived
- **THEN** the assertion satisfies this Requirement

#### Scenario: Tensor closed form guarded by pytest.approx
- **WHEN** a test guards a tensor-valued closed-form claim with `pytest.approx`
- **THEN** the assertion violates this Requirement, because pytest dispatches a `torch.Tensor` through its internal `ApproxNumpy` path, yields a bare `bool` that drops the `f"actual={...}"` message, and checks neither dtype nor shape
