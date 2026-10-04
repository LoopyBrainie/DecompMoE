# Spec Delta

## MODIFIED Requirements

### Requirement: Canonical Package And Version Identifier

The package SHALL expose `decompmoe.__canonical_name__ == "DecompMoE"`, `decompmoe.__alias__ == "GeoMoE"`, and `decompmoe.__version__` as a `str` matching PEP 440 semantics. The package SHALL expose a stable `__all__` listing every public symbol introduced by this skeleton. **De-duplication rule (normative):** "every public symbol" means the **de-duplicated union** of the `__all__` entries declared by the 13 submodules — a name declared in more than one submodule counts **once**. At MVP that union is exactly **76** names; together with the 3 package dunders (`__version__`, `__canonical_name__`, `__alias__`) the package-level `__all__` therefore has **79** entries. The **only** cross-module name collision at MVP is `flops_per_token`, declared in both `config` and `metrics` (the `metrics` definition is a passthrough wrapper that mirrors `config.flops_per_token`); the package-level `__all__` MUST bind that name to the `config` definition, and the `metrics` definition MUST remain reachable as `decompmoe.metrics.flops_per_token`. **MUST NOT:** summing the 13 per-module counts without de-duplication yields **77** and is not the expected total. The alias SHALL NOT appear as a code identifier anywhere in the package (only in design prose / docstrings).

**Source:** `wayfinder/tickets/A1-1.md`, change `2026-10-04-phase2-gamma-reset-ramp-closure` design.md (Decision 6 — the union grows 75 → 76 because `gamma_reset_for_phase2` is a new public schedule-layer symbol; the de-duplication rule and the single-collision statement are unchanged because the new name has no cross-module twin)

#### Scenario: Name resolution
- **WHEN** `decompmoe.__canonical_name__` is accessed
- **THEN** it returns the literal string `"DecompMoE"`

#### Scenario: Alias preserved
- **WHEN** `decompmoe.__alias__` is accessed
- **THEN** it returns the literal string `"GeoMoE"` for documentation continuity

#### Scenario: gamma_reset_for_phase2 is on the public surface

- **WHEN** the 13 submodules' `__all__` entries are de-duplicated
- **THEN** the union contains `gamma_reset_for_phase2` exactly once, it is declared by `schedule`, and `from decompmoe import gamma_reset_for_phase2` resolves
- **AND** the union size, the un-deduplicated per-module sum, and the package-level `__all__` size are **76**, **77**, and **79** respectively (integer closed forms -> bare `==`, never `pytest.approx(..., abs=0)` per governance req-gov-1 §1)
- **AND** the counts MUST be re-pinned by any future change that adds or removes a public symbol; a symbol that is public but absent from `__all__` violates the enumeration obligation above
