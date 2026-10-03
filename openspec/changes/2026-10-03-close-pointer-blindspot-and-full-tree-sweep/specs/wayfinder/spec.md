## MODIFIED Requirements

### Requirement: Hybrid Three-Layer Phase Triggers


The system MUST combine three trigger layers: (Layer 1) Time-Driven hard cut at the 1 K / 6 K / 26 K / 56 K / 100 K boundaries; (Layer 2) State-Driven Advisory signals — normalized entropy `R_H`, load skew `S_load`, β saturation ratio `R_β-sat`, and overlap index `L_sep / WB` (where `WB = 0.0476` is the natural baseline of the soft orthogonality loss, defined in `wayfinder/tickets/A6b-2.md` (Layer-2 advisory-signal definition) as the per-expert orthogonality baseline that the advisory ratio normalizes against; a ratio `> 2.0` indicates severe centroid clustering / territory overlap). **Deferral note (Layer 2):** the two concrete Layer 2 thresholds `WB = 0.0476` and the `> 2.0` severe-clustering ratio are **advisory-only and unimplemented in the MVP skeleton** — `advisory_signals()` is a pure passthrough that returns its four keyword arguments unchanged, and neither threshold appears as an executable literal in `src/decompmoe/` or `tests/`. The deferral is registered as a hand-off in the change that introduced Layer 2 and recorded in `tests/test_schedule.py::test_advisory_signals_read_only`; it is stated here so the spec body is no longer the only place lacking the annotation) — read-only and advisory only (never auto-trigger a transition); (Layer 3) Hard Cutoff at 100 K steps. Real-time monitoring of `D_c` (per-expert geodesic spread) MUST be excluded;` `D_c` remains an offline metric due to its `O(N_e²)` cost and unstable threshold.

**Source:** `wayfinder/tickets/A6b-2.md`

#### Scenario: Advisory signals not to auto-trigger
- **WHEN** an advisory signal crosses any threshold before its corresponding time-driven boundary
- **THEN** the system logs the advisory but does NOT advance the phase

<a id="req-16"></a>
