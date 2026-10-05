# Spec Delta

## MODIFIED Requirements

### Requirement: Canonical Package And Version Identifier

The package SHALL expose `decompmoe.__canonical_name__ == "DecompMoE"`, `decompmoe.__alias__ == "GeoMoE"`, and `decompmoe.__version__` as a `str` matching PEP 440 semantics. The package SHALL expose a stable `__all__` listing every public symbol introduced by this skeleton. **De-duplication rule (normative):** "every public symbol" means the **de-duplicated union** of the `__all__` entries declared by the 13 submodules — a name declared in more than one submodule counts **once**. At MVP that union is exactly **76** names; together with the 3 package dunders (`__version__`, `__canonical_name__`, `__alias__`) the package-level `__all__` therefore has **79** entries. The **only** cross-module name collision at MVP is `flops_per_token`, declared in both `config` and `metrics` (the `metrics` definition is a passthrough wrapper that mirrors `config.flops_per_token`); the package-level `__all__` MUST bind that name to the `config` definition, and the `metrics` definition MUST remain reachable as `decompmoe.metrics.flops_per_token`. **MUST NOT:** summing the 13 per-module counts without de-duplication yields **77** and is not the expected total. The alias SHALL NOT appear as a code identifier anywhere in the package (only in design prose / docstrings).

<!-- No `**Source:**` line, deliberately. `("decompmoe-skeleton", "req-1")` is
     entry 1 of `SOURCE_EXEMPTIONS` in scripts/lint_no_source_field_drift.py:
     req-1 is grandfathered as lacking a lineage field, and the lint enforces
     that a registry entry which NOW carries one is itself a violation. Adding
     the line here would apply the delta into a spec tree where req-1 carries a
     field while still being registered as exempt -- i.e. it would turn the very
     next `/opsx:archive` red. req-1 keeps its exemption and stays consistent
     with its 19 exempt decompmoe-skeleton peers. Design lineage for this
     change is recorded in the change's own design.md Decision 6. -->

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
- **AND** those three counts are the values the de-duplication rule **yields**, not independent constants: they are normative, so a count that stops matching the rule is itself a violation of this Requirement rather than stale documentation. A symbol that is public but absent from `__all__` violates the enumeration obligation above, and the counts are what make that omission detectable
