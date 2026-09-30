# Spec Delta — `decompmoe-skeleton`

## MODIFIED Requirements

<a id="req-21"></a>

### Requirement: Frozen MVP Hyperparameter Set — D1 Geometric-Only Fields

The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: `d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, `d_c == 16`, `H_kv == 8`, `d_k == 128`, `β_initial ≈ 1.035` (per wayfinder spec req-7 L130 closed-form `β_0 = 0.1 + 31.9·σ(γ_init)` with `γ_init ≈ −3.5`; 50-digit mpmath `β_0 = 1.0350601609682665718`). Attempting to mutate any field SHALL raise `dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance with all default values.

**MVPConfig carries only GEOMETRIC constants** (model shape: `d_model`, `N_e`, `k`, `d_ffn`, `L`, `d_ffn_dense`, `d_c`, `H_kv`, `d_k`, `vocab_size`) **plus the specific initial value `β_initial ≈ 1.035`** (narrative 4-sig-fig; spec req-7 L130 closed-form anchor). The algorithmic range constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (NOT in MVPConfig), per `design.md` Decision 1: "Algorithmic constants live with their usage site". MVPConfig does not carry `β_min` or `β_max` fields, and the canonical sources for those constants are `decompmoe.beta.BETA_MIN` and `decompmoe.beta.BETA_MAX`.

**Source:** `wayfinder/tickets/A4-1.md`, change `fix-math-consistency-audit-2026-08` design.md (Decision 1)

#### Scenario: Field defaults locked

- **WHEN** `MVPConfig()` is constructed
- **THEN** `cfg.d_model == 1024 and cfg.N_e == 16 and cfg.k == 2 and cfg.d_ffn == 2048 and cfg.L == 4`

#### Scenario: Mutation rejected

- **WHEN** any field is assigned after construction
- **THEN** `dataclasses.FrozenInstanceError` is raised

#### Scenario: MVPConfig field set is exactly the geometric constants plus β_initial

- **WHEN** the set of dataclass field names on `MVPConfig` is enumerated via `[f.name for f in dataclasses.fields(MVPConfig)]`
- **THEN** the set equals exactly `{'d_model', 'N_e', 'k', 'd_ffn', 'L', 'd_ffn_dense', 'd_c', 'H_kv', 'd_k', 'beta_initial', 'vocab_size'}` (11 fields; **`β_min` and `β_max` are NOT MVPConfig fields**; they live as `Final[float]` in `decompmoe/beta.py`)

#### Scenario: MVPConfig.beta_initial default matches spec closed-form derivation

- **WHEN** `MVPConfig().beta_initial` is compared against `0.1 + 31.9·σ(γ_init=−3.5)` evaluated via `torch.sigmoid`
- **THEN** `abs(MVPConfig().beta_initial − closed_form_value) ≤ 1e-3` (covers narrative 4-sig-fig truncation to 1.035 from 50-digit 1.0350601609682665718)
- **AND** the test does NOT degenerate to a self-referential check (i.e., `MVPConfig().beta_initial ≈ literal_value`); the closed form MUST be derived from `β_min + (β_max−β_min)·σ(γ_init)` per spec req-7 L123 Sigmoid 闭式

---
