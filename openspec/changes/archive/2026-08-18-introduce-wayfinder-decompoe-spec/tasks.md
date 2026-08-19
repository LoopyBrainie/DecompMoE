## 1. Spec Structural Review

- [ ] 1.1 Verify every `### Requirement:` in `specs/wayfinder/spec.md` has at least one `#### Scenario:` (exactly four hashtags, no three-hash or bullet substitution)
- [ ] 1.2 Verify all normative verbs use SHALL / MUST; no should / may; "MUST NOT" used where the design rejects an alternative (Linear Attention, SSM, RNN, Pre-Attention Dynamic Bias, shared expert, custom kernel)
- [ ] 1.3 Verify every Requirement carries a `**Source:**` field referencing the originating ticket file path under `wayfinder/tickets/`
- [ ] 1.4 Verify `## ## Purpose`'s exclusion clause 50 characters and contains no "TBD Update Purpose after archive" placeholder

## 2. Cross-Section Consistency Audit

- [ ] 2.1 Numeric fidelity check — confirm against ticket bodies: `β ∈ [0.1, 32]`, `β_min = 0.1`, `β_max = 32`; C-extraction ≈ 65.5 K FLOPs/token at `H_kv=8, d_k=128, d_c=16`; `W_proj ≈ 64 KB` in BF16 100% L2-resident; activations ≈ 4 KB 100% SRAM/RF-resident; 0 bytes HBM delta; Phase ratios `1/5/20/30/44%`; Phase boundaries `1 K / 6 K / 26 K / 56 K / 100 K`; Resurrection trigger `< 1/128` for 200 steps with 1000-step rate limit; β Saturation Guard thresholds `30.4` and `28.8`; Loss Spike `2.5 × EMA`; perturbation `N(0, 0.05² I)`; decay factor `0.85`
- [ ] 2.2 Notation consistency check — every formula uses the locked symbols `Σ_i`, `P_i = Σ_i^{-1}`, `(i, l, h, t)`; per-layer head-aggregated form `C_t^l / c_i^l / Σ_i^l / P_i^l` is the only head-elided form present
- [ ] 2.3 Code-name mapping check — confirm `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse` mapping is intact in the Formal Symbols Requirement
- [ ] 2.4 Scope-Lock consistency check, spec side — grep `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` for `Linear Attention` / `SSM` / `RNN` / `Pre-Attention Dynamic Bias` / `checkpoint conversion`; each MUST appear only inside `## Purpose`'s exclusion clause, not inside any `### Requirement:` body or `#### Scenario:` body.
- [ ] 2.5 Scope-Lock consistency check, ticket side — for each of the five terms, run `grep -nE 'Future Work' wayfinder/tickets/*.md` and confirm any ticket mentions appear only inside the ticket's `## Future Work` section, not inside the ticket's Resolution body.
- [ ] 2.6 Naming consistency check — every Requirement that names the project uses "DecompMoE"; "GeoMoE" appears only inside `Naming And Alias Convention` Requirement and inside Future Work references
- [ ] 2.7 Hardware-compatibility matrix check — confirm `FlashDecoding / PagedAttention / vLLM / TGI / SGLang / TensorRT-LLM / Megatron-LM / DeepSpeed-MoE` and `torch.compile` (optional) are the exact set; no missing or extra entries

## 3. Ticket-to-Requirement Reference Matrix

- [ ] 3.1 Build the inverse map: each `wayfinder/tickets/A*-*.md` is cited by at least one Requirement's `**Source:**` field; record any ticket without a citation as a follow-up
- [ ] 3.2 Confirm all 21 tickets are covered (`A0-1, A1-1, A2-1, A2-2, A3-1, A3-2, A4-1, A4-2, A5-1, A5-2, A5-3 (v2 section), A6a-1, A6a-2, A6b-1, A6b-2, A7-1, A7-2, A7-3, A8-1, A8-2, A8-3`)
- [ ] 3.3 If a ticket is uncovered, append a short `#### Scenario:` to the nearest Requirement (or open a follow-up issue) — do NOT silently drop the ticket

## 4. Archive Readiness

- [ ] 4.1 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` from `D:\myProject\DecompMoE`; confirm zero errors and zero "TBD Purpose" placeholders
- [ ] 4.2 Run `openspec status introduce-wayfinder-decompoe-spec`; confirm `isPlanningComplete: true` and every artifact reports `status: "done"`
- [ ] 4.3 Run `openspec instructions archive --change introduce-wayfinder-decompoe-spec --json` (read-only) to verify the archive command will succeed; confirm the archive target is `openspec/specs/wayfinder/spec.md`
- [ ] 4.4 Run `openspec archive introduce-wayfinder-decompoe-spec --yes` only after the user explicitly approves; record the archive SHA and timestamp in the change directory as `ARCHIVE_LOG.md`

## 5. Documentation Trail Update

- [ ] 5.1 Append a one-line header note to `wayfinder/map.md`: `> Spec source of truth (post-archive): openspec/specs/wayfinder/spec.md — this map retains the decision trail.`
- [ ] 5.2 Verify `wayfinder/tickets/*.md` remain unchanged (formalize is translation, not rewrite); any ticket body drift indicates a spec must be revised, not the ticket
- [ ] 5.3 If a project-root `README.md` exists, append a short OpenSpec section listing the wayfinder capability and the procedure to propose changes; otherwise skip with a note in `ARCHIVE_LOG.md`
