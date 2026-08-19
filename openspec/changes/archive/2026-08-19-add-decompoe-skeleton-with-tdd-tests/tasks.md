## 1. ST-01 — Package Skeleton + Frozen MVP Config + Wire-Level Contracts

- [x] 1.1 Write `tests/test_config.py` with failing pytest cases: `test_mvp_locked_constants`, `test_mvp_is_frozen`, `test_total_param_estimate`, `test_active_flops_parity`, `test_canonical_name`
- [x] 1.2 Write `tests/test_contracts.py` with failing pytest cases: `test_router_contract_signatures`, `test_no_kv_cache_field`
- [x] 1.3 Implement `src/decompmoe/__init__.py` (version, `__all__`, `__canonical_name__`, `__alias__`)
- [x] 1.4 Implement `src/decompmoe/config.py` (`MVPConfig` frozen dataclass + `compute_total_and_active` + `flops_per_token`)
- [x] 1.5 Implement `src/decompmoe/contracts.py` (Protocol stubs for `GeometricRouter`, `TerritoryHolder`, `BlockAdapter`)
- [x] 1.6 Run `pytest tests/test_config.py tests/test_contracts.py -v` → all green before advancing

## 2. ST-02 — β Sigmoid + Bounded γ + Gradient Upper-Bound Checks

- [ ] 2.1 Write `tests/test_beta.py` with failing pytest cases: `test_beta_endpoints`, `test_beta_monotone`, `test_logit_range`, `test_grad_C_bound`, `test_grad_gamma_bound`, `test_beta_param_init_default`
- [ ] 2.2 Implement `src/decompmoe/beta.py` (`inverse_temperature`, `MAX_GRAD_PER_C`, `MAX_GRAD_PER_GAMMA`)
- [ ] 2.3 Run `pytest tests/test_beta.py -v` → all green before advancing

## 3. ST-03 — Spherical Normalization Primitive

- [ ] 3.1 Write `tests/test_sphere.py` with failing pytest cases: `test_unit_sphere_invar`, `test_near_zero_numerically_safe`, `test_double_normalize_idempotent`, `test_voronoi_angle_self_consistency`
- [ ] 3.2 Implement `src/decompmoe/sphere.py` (`spherical_l2_normalize`, `voronoi_angle`)
- [ ] 3.3 Run `pytest tests/test_sphere.py -v` → all green before advancing

## 4. ST-04 — C Extraction Four-Step Pipeline + Differentiability

- [ ] 4.1 Write `tests/test_extraction.py` with failing pytest cases: `test_pipeline_shape`, `test_aggregate_across_heads_awareness`, `test_complexity_budget`, `test_full_differentiability`, `test_no_surrogate_in_codebase`
- [ ] 4.2 Implement `src/decompmoe/extraction.py` (`extract_C` 4-step pure function)
- [ ] 4.3 Run `pytest tests/test_extraction.py -v` → all green before advancing

## 5. ST-05 — Centroid Four-Phase Lifecycle Driver

- [ ] 5.1 Write `tests/test_extraction_phase.py` with failing pytest cases: `test_phase_seeding_no_grad`, `test_phase_090_ema`, `test_phase_095_to_099_ema_coefficients`, `test_phase_4_projected_sgd`, `test_phase_transition_swaps_rule`, `test_dead_expert_protection`
- [ ] 5.2 Add `CentroidDriver` class + `Phase` enum to `src/decompmoe/extraction.py`
- [ ] 5.3 Run `pytest tests/test_extraction_phase.py -v` → all green before advancing

## 6. ST-06 — Isotropic Squared-Chord Distance + Logit Composition

- [ ] 6.1 Write `tests/test_distance.py` with failing pytest cases: `test_distance_range`, `test_distance_zero_at_align`, `test_distance_two_at_antipode`, `test_logit_zero_at_aligned`, `test_logit_no_w_i`, `test_logit_grad_safe`
- [ ] 6.2 Implement `src/decompmoe/distance.py` (`squared_chord`, `logit`)
- [ ] 6.3 Run `pytest tests/test_distance.py -v` → all green before advancing

## 7. ST-07 — Top-K Sparse Mask + Local Softmax Gating

- [ ] 7.1 Write `tests/test_gating.py` with failing pytest cases: `test_k_equals_two`, `test_neg_inf_sentinel_used`, `test_partition_of_unity`, `test_zero_grad_for_non_top_k`, `test_forward_formula_strictness`, `test_convex_combination_dtype_safe`
- [ ] 7.2 Implement `src/decompmoe/gating.py` (`topk_mask_with_neg_inf`, `local_softmax`)
- [ ] 7.3 Run `pytest tests/test_gating.py -v` → all green before advancing

## 8. ST-08 — SwiGLU Expert + No-Shared-Expert Invariant

- [ ] 8.1 Write `tests/test_experts.py` with failing pytest cases: `test_swiglu_formula`, `test_expert_param_count`, `test_no_c_injection`, `test_expert_pool_no_shared_branch`, `test_no_custom_kernel`, `test_isomorphic_to_llama_ffn`
- [ ] 8.2 Implement `src/decompmoe/experts.py` (`SwiGLUExpert`, `ExpertPool`)
- [ ] 8.3 Run `pytest tests/test_experts.py -v` → all green before advancing

## 9. ST-09 — Loss Composition `L_CE + α·L_lb + λ(t)·L_sep`

- [ ] 9.1 Write `tests/test_loss.py` with failing pytest cases: `test_load_balance_alpha_fixed`, `test_lb_uses_detached_fractions`, `test_lambda_zero_phase_1_2`, `test_lambda_cosine_ramp_phase_3`, `test_lambda_fixed_phase_4`, `test_sep_formula`, `test_token_vs_expert_C_notation`
- [ ] 9.2 Implement `src/decompmoe/loss.py` (`L_total`, `LossParts`, `compute_L_sep`)
- [ ] 9.3 Run `pytest tests/test_loss.py -v` → all green before advancing

## 10. ST-10 — Numerical Safeguards (5 Predicates + Helpers)

- [ ] 10.1 Write `tests/test_safeguards.py` with failing pytest cases: `test_clip_grad_norm_threshold`, `test_nan_ladder`, `test_resurrection_trigger_window`, `test_resurrection_perturb_distribution`, `test_beta_saturation_warning_at_30_4`, `test_beta_saturation_global_lr_halve_at_28_8`, `test_loss_spike_defense_phase3plus`, `test_step_ordering`
- [ ] 10.2 Implement `src/decompmoe/safeguards.py` (5 helpers + `STEP_ORDER` constant)
- [ ] 10.3 Run `pytest tests/test_safeguards.py -v` → all green before advancing

## 11. ST-11 — Five-Phase Scheduler + Three-Layer Hybrid Trigger

- [ ] 11.1 Write `tests/test_schedule.py` with failing pytest cases: `test_phase_ratios_pure_function`, `test_phase_id_at_boundary`, `test_phase1_freeze_router`, `test_phase2_freeze_experts`, `test_phase3_b_ramp`, `test_phase4_b_dynamic_box`, `test_adam_momentum_reset_on_phase4_entry`, `test_advisory_signals_read_only`
- [ ] 11.2 Implement `src/decompmoe/schedule.py` (`phase_id`, `phase_step_frozen_names`, `should_reset_adam`, `advisory_signals`)
- [ ] 11.3 Run `pytest tests/test_schedule.py -v` → all green before advancing

## 12. ST-12 — Eight Metrics + Six Viz Module Protocol Stubs

- [ ] 12.1 Write `tests/test_metrics.py` with failing pytest cases: `test_sep_formula_matches_loss`, `test_R_H_partition_of_unity_input`, `test_S_load_zero_at_uniform`, `test_four_realtime_four_offline_classification`, `test_active_flops_parity_per_arch`
- [ ] 12.2 Write `tests/test_viz_protocols.py` with failing pytest cases: `test_viz_modules_complete`, `test_viz_stack_pinned`, `test_PCA_camera_angles_fixed`
- [ ] 12.3 Implement `src/decompmoe/metrics.py` (8 metric functions + `flops_per_token` + `REALTIME` / `OFFLINE` frozensets)
- [ ] 12.4 Implement `src/decompmoe/viz.py` (6 Protocol stubs + `IMPLEMENTATION_STACK` frozenset)
- [ ] 12.5 Run `pytest tests/test_metrics.py tests/test_viz_protocols.py -v` → all green before advancing

## 13. Final Verification Gates

- [ ] 13.1 `pytest tests/ -v` → all 14 test files green
- [ ] 13.2 `openspec validate --strict` → zero errors
- [ ] 13.3 Hard-constraint grep: no `StraightThroughEstimator` / `w_i.*logit` / `shared.*expert` matches in `src/decompmoe/`
- [ ] 13.4 Hard-constraint grep: no `cpp_extension` / `triton` / custom-CUDA imports in `src/decompmoe/`
- [ ] 13.5 Run `openspec archive add-decompoe-skeleton-with-tdd-tests --yes` to close the change