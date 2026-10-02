## ADDED Requirements

<a id="req-gov-5"></a>

### Requirement: Numeric Literal Provenance in Specs

**Source:** `CLAUDE.md` §6 (Hard Constraints), `CLAUDE.md` §2 (Truth Source Hierarchy), change `2026-10-02-repair-spell-numeric-literal-provenance` design.md (Decision A2 magnitude self-consistency, Decision A3 three machine-checkable defect classes)

The system MUST NOT admit a numeric literal into any peer spec under `openspec/specs/**` unless the literal carries provenance, and MUST NOT let a literal without provenance carry a proof obligation.

Concretely: a spec numeric literal MUST state (a) the value, (b) **what determines that value** — the governing equation, convergence criterion, or estimator whose property it is — and (c) a recomputation entry point (a derivation chain, or a named script/change whose evidence reproduces it). A literal that satisfies (a) alone is a magic number and MUST NOT enter a spec.

Three defect classes are named because they are machine-checkable without re-running an oracle, and because this repository has produced one instance of each:

1. **C1 — magnitude impossibility.** The literal's decimal precision exceeds what its claimed computation path can produce. Discriminator: if the literal is a residual of magnitude `r`, the compared quantities must agree to `-log10(r)` decimal places; a single float64 operation has a rounding floor near `1e-16` (53-bit mantissa). A literal demanding agreement far below that floor is impossible on the claimed path and MUST be replaced, not restated. Repository instance: a bisection residual quoted as `5.01e-52`, which would require 50.1 decimal places of agreement — 35 orders of magnitude below the float64 floor.
2. **C2 — a bracket tolerance presented as a root property.** A value produced by a solver's internal convergence criterion MUST NOT be labelled as the value at the mathematical root unless it is evaluated at that root by the definition equation. If it is a bracket tolerance, the spec MUST say so. Repository instance: the same `5.01e-52`, which is the oracle's own bisection bracket residual, not the residual at the canonical root (measured `1.4635872379108090131680874e-17` at N_e=16 and `1.9420345120803994000206689e-18` at N_e=64, mpmath `betainc(a, b, 0, x, regularized=True)` at dps=60).
3. **C3 — an API default read as an API semantic.** A statement about what a library call *does* MUST be established by reading the library's source and by a behavioural construction, not by its documentation wording or by a remembered default. Repository instance: a claim that `pytest.approx(expected, abs=T)` applies `max(T, rel*|expected|)`; on pytest 9.1.1 the `rel` default is `None`, not `1e-6`, and the `abs` branch returns before the `max`, so the tolerance is exactly `T`.

#### Scenario: A magnitude-impossible literal is detected without re-deriving it

- **WHEN** a numeric literal in a peer spec is a residual of magnitude `r` and its text names a float64 computation path
- **THEN** the required decimal agreement `-log10(r)` MUST be at most 16 decimal places
- **AND** if `-log10(r) > 16`, the literal MUST fail the check and MUST NOT be restated into another literal; the defect class MUST be recorded as C1
- **AND** the failure message MUST embed the actual magnitude as `f"actual={...}"`

#### Scenario: A bracket tolerance is labelled as such

- **WHEN** a spec literal is produced by a solver's convergence criterion rather than evaluated at a mathematical root
- **THEN** the spec MUST label it as the convergence criterion's tolerance and MUST NOT describe it as the value at the root
- **AND** if the spec claims a root value, that value MUST be obtained by evaluating the governing definition equation at the root
- **AND** the two MUST NOT be interchanged in the same Requirement

#### Scenario: An API-semantics claim is settled by source and behaviour, not by wording

- **WHEN** a spec states what a third-party API call does with a given argument combination
- **THEN** the claim MUST be accompanied by a source reference and by a behavioural construction that discriminates between the candidate readings
- **AND** if two candidate readings give the SAME result for the claim at hand, the spec MUST state which reading it used rather than leaving it implicit
- **AND** the environment in which the claim was measured MUST be named, because library defaults are version-dependent

#### Scenario: Archive copies are not retro-edited

- **WHEN** a defective literal also appears inside `openspec/changes/archive/**`
- **THEN** the archived copy MUST be left byte-identical, because it is the historical record of what a past change did
- **AND** this Requirement's Source field MUST register the retained occurrence so a later auditor can distinguish "deliberately retained history" from "missed fix"

#### Scenario: Numeric assertions inside this Requirement obey the discipline it states

- **WHEN** a Scenario of this Requirement asserts a numeric value
- **THEN** an integer closed form MUST use bare `==` and a float closed form MUST use `pytest.approx(value, abs=...)`
- **AND** the failure message MUST embed the computed value as `f"actual={...}"`
- **AND** `pytest.approx(..., abs=0)` MUST NOT appear on an integer closed form
