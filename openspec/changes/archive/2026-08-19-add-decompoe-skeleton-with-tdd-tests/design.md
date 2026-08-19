## Context

The 21 Requirements × 34 Scenarios of `openspec/specs/wayfinder/spec.md` are formalized but have no Python counterpart. `pyproject.toml` declares `name="decompmoe"` and pins `torch==2.12.1` / `torchvision==0.27.1` (`pytorch-cu130`); `.venv/` is provisioned. The codebase has no `.py` files, no `.git/`, no CI. The skeleton MUST be (a) type-safe, (b) pure-function where math is involved, (c) wire-level Protocol-stub where execution semantics are owned by future changes, and (d) verifiable end-to-end via `pytest`. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Make the spec's 21 R × 34 S testable in isolation by emitting one pytest module per sub-task (ST-01 … ST-12)
- Emit frozen dataclasses for hyperparameter sets (`MVPConfig`) and `Protocol` stubs for wire-level boundaries (`GeometricRouter`, `TerritoryHolder`, `BlockAdapter`)
- Keep every mathematical primitive a pure function (no hidden state, no autograd graph outside `gradcheck` tests)
- Encode hard constraints as source-level grep invariants (no `w_i` in logit, no `cpp_extension` import, no `kv_cache_c` field, etc.)
- Pass `mypy src/decompmoe --strict` with zero errors

**Non-Goals:**
- Implement executable forward/backward pass for the full router (`GeometricRouter.forward`) — this is deferred to a follow-up code-level change
- Introduce a CUDA / Triton kernel — explicitly forbidden by CLAUDE.md §6
- Add shared expert — explicitly forbidden by A5-2
- Modify `openspec/specs/wayfinder/spec.md` — spec is the immutable truth source; this change materializes it, does not redefine it
- Run training, baselines, or paper-writing tasks — all out of scope per CLAUDE.md §7
- Implement the visualization toolchain beyond Protocol stubs — real visualizations are deferred to a §6/§7 waiver change

## Decisions

### D1 — Single Source Of Truth For Constants

**Decision**: All numeric constants (`β_min`, `β_max`, `α`, `λ_max`, `30.4`, `28.8`, `1/128`, `200`, `1000`, `5/20/30/44%`) live as `Final[float]` in the appropriate module, exported via `__all__`. `MVPConfig` does NOT mirror them — `MVPConfig` only stores geometry (`d_model`, `N_e`, `k`, `d_ffn`, `L`, `H_kv`, `d_k`, `d_c`).

**Rationale**: Hard-constraint grep tests in `spec` require constants to be searchable strings; if they were tucked inside `MVPConfig`, the grep tests would have to navigate the dataclass. Co-locating with the module that uses them gives a single canonical home and a grep-friendly fingerprint.

**Alternatives considered**:
- *Mirror everything in `MVPConfig`* → rejected because the `0.95` factor is an algorithmic constant (β-safety), not a geometric one.
- *Centralize in a single `constants.py`* → rejected because there is no shared usage; constants are referenced by exactly one module.

### D2 — Wire-Level Stubs As `typing.Protocol`

**Decision**: `GeometricRouter`, `TerritoryHolder`, `BlockAdapter` are `typing.Protocol` classes with method signatures only (no bodies, no default implementations).

**Rationale**: A `Protocol` is a structural-typing artifact that the static type checker can verify, but at runtime it produces zero code. This lets us express "this Protocol MUST declare X" (test `test_router_contract_signatures`) without committing to a specific implementation.

**Alternatives considered**:
- *Use `abc.ABC`* → rejected because abstract classes can carry implementation and would tempt someone to add a `forward` body that doesn't yet exist.
- *Use plain functions with type hints* → rejected because the contract is per-method, not per-function.

### D3 — Loss/LB Uses Detached Fractions

**Decision**: `L_lb` is computed using `f_per_expert.detach()` before being added to `L_total`. The `.detach()` call is grep-tested by `test_lb_uses_detached_fractions`.

**Rationale**: A4-2 / A6a-1 both pin the Switch-style fixed-weight `L_lb` with detached fractions; the detach is a load-balancing regularizer that should NOT influence router gradients. Grep testing pins the invariant.

**Alternatives considered**:
- *Add `.detach()` inside the function but hide behind a helper* → rejected because the grep invariant would need to traverse the helper chain.

### D4 — TDD Workflow: Red → Green → Refactor Per ST

**Decision**: For each ST, we (1) write the failing pytest cases named in the plan, (2) implement the minimum code to make them pass, (3) refactor for type hints / dataclass / docstring — never introducing new behavior. Every ST must be all-green before advancing.

**Rationale**: The plan explicitly requires this. Spec is the behavior contract; tests are the executable enforcement layer; code is the third layer that must conform to both.

**Alternatives considered**:
- *Write all tests first, then all code* → rejected because we lose the "smallest failing test" feedback that drives minimality.

### D5 — `centroid` Pipeline Versus `c_i` Notation

**Decision**: Code uses `c_centroids` (shape `[N_e, d_c]`) for the per-expert centroids and `C` (shape `[B, N, d_c]`) for per-token signatures. Docstrings distinguish `C_t^l` (per-token, per-layer) vs `c_i^l` (per-expert, per-layer).

**Rationale**: A1-1 pins the notation. Code identifiers match spec symbols one-to-one (`C_t^l → C`, `c_i^l → c_centroids[i]`).

**Alternatives considered**:
- *Use `c_i` in code* → rejected because Python naming convention prefers `c_centroids` (avoids `c_i` shadowing and clearly indicates a matrix).

### D6 — `centroid` Lifecycle: `Phase` Enum + Plain Class

**Decision**: `CentroidDriver` is a plain Python class with a `phase: Phase` attribute and a `step(centroids, X, mask) -> Tensor` method. `Phase` is an `IntEnum` with explicit integer values matching the spec (`SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4`).

**Rationale**: A3-2 specifies the integer-coded phases; an `IntEnum` makes the integer mapping machine-verifiable.

**Alternatives considered**:
- *String enum* → rejected because the spec's integer mapping must be honored for downstream schedule integration.

### D7 — Tests Use `hypothesis` Only Where Property Tests Add Value

**Decision**: Property tests (1000-sample random input) are used only in `distance.py` (`test_distance_range`, `test_logit_grad_safe`) and `sphere.py` (`test_unit_sphere_invar`); everywhere else, fixed seeds and explicit tensors suffice.

**Rationale**: Distance/logit have continuous ranges that benefit from sampling; categorical / step-machine / metric checks are fully covered by deterministic assertions.

**Alternatives considered**:
- *Use `hypothesis` everywhere* → rejected because it slows the test suite and yields no additional coverage for the deterministic checks.

## Risks / Trade-offs

- **[Risk]** `MVPConfig` doesn't store `β_min` / `β_max` / `α` / `λ_max` — a future change might forget to import them. → **Mitigation**: Constants live next to their usage site (see D1), and `test_beta_param_init_default` asserts `MVPConfig().beta_initial == 1.0`.
- **[Risk]** `Protocol` stubs may be incomplete — they declare only the signatures explicitly required, not the full router interface. → **Mitigation**: The plan is formalize-only; the spec does not yet require a full `GeometricRouter` interface, only the methods in Req 3, 4, 16, 17, 18.
- **[Risk]** Future code-level change (executable forward/backward) might bypass these Protocols. → **Mitigation**: `mypy --strict` + the grep invariant tests will catch any import of `torch.utils.cpp_extension` or `triton`.
- **[Risk]** `centroid` Lifecycle Driver Phase 0 "non-differentiable" assertion is subtle — Phase 0 must not register gradient on `centroids`, but the rest of the pipeline (Steps 1–3) must be fully differentiable. → **Mitigation**: Two separate tests: `test_phase_seeding_no_grad` (Phase 0) and `test_full_differentiability` (Phases 1–4 + extraction).
- **[Risk]** Hard-constraint grep invariants can drift silently if anyone adds `shared` to `ExpertPool`. → **Mitigation**: `test_expert_pool_no_shared_branch` is part of the suite; CI / `pytest -v` will fail loudly.

## Migration Plan

Not applicable — this change adds new files only; no existing behavior is modified. To use the skeleton, a developer imports from `decompmoe.config`, `decompmoe.contracts`, etc. To implement a downstream code-level change (e.g. full forward), they propose a new OpenSpec change that re-uses these Protocols and dataclasses.

## Open Questions

None at this time. All decision points above were resolved with documented rationale; the spec is the single source of truth, and the plan maps spec → ST → test file with one-to-one correspondence.