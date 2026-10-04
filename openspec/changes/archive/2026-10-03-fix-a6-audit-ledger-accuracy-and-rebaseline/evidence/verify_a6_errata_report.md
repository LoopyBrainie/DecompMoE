# verify_a6_errata report

Frozen head: `95718cfa0b7e417935d2fbdd873eb7fec06ebb9b`
Pin: `6593a06`

**65 checks, 64 passed, 1 failed**

| check | result | detail |
|---|---|---|
| `B-AC06-anchor` | PASS | 'def _betainc_regularized(x: float, a: float, b: float) -> float:' |
| `B-AC06-pinstate` | PASS | '    """Regularized incomplete beta function I_x(a, b) via Gauss–Legendre 8-point.' |
| `B-AC06-fixed` | PASS |  |
| `B-AC06-commit` | PASS |  |
| `B-AC26-norevert` | PASS | pin=6ddbdefb fix=6ddbdefb parent=6ddbdefb |
| `B-AC26-prefix-absent` | PASS | 8f50659 blob=7a88c637 |
| `B-AC26-actual` | PASS | count=10 |
| `B-AC26-anchor` | PASS | L167='    known L_sep_raw).' L178='        f"actual={lam_start}; λ(26_000) should be 0 at the phase-3 ramp start"' |
| `B-AC26-verdict` | PASS | 'FIXED_BY_COMMIT' |
| `B-AC26-timing` | PASS | merge-base --is-ancestor pin e50cc02 rc=0 |
| `B-AC27-numbers` | PASS | decompmoe-skeleton=14/1; governance=9/1; wayfinder=3/2 |
| `B-AC27-crosscheck` | PASS | wayfinder net=1; decompmoe-skeleton net=13; governance net=8 |
| `B-AC27-baseline` | PASS | intervals=[[12, 12], [34, 34], [98, 98], [113, 116], [132, 132], [135, 141], [150, 150], [158, 158], [162, 162], [261, 261], [273, 273], [276, 277], [332, 335], |
| `B-AC27-single-cause` | PASS | 33f7cc9 fix(voronoi_angle): replace defective measurement layer with mean per-cell equivalent-cap radius |
| `B-AC29-line` | PASS | hits=[1336] |
| `B-AC29-outofrepo` | PASS |  |
| `B-AC29-deadkey` | PASS | key count=197 |
| `B-AC29-livekey` | PASS |  |
| `B-AC30-anchor` | PASS | 'class CentroidDriver:' |
| `B-AC30-wrongfile` | PASS | mentions=1 |
| `B-AC30-fixed` | PASS |  |
| `B-AC30-key` | PASS |  |
| `B-AC30-commit` | PASS |  |
| `B-AC50-anchor` | PASS | L383='The system MUST recompute `C_t^l` every Decode step from `(K' |
| `B-AC50-anchor-ctx` | PASS |  |
| `C-AC50-arith` | PASS | macs=33168 flops=66336 new=0.197697 old=0.196838 436=0.436047 |
| `G-AC50-keys` | PASS |  |
| `B-AC51-anchor` | PASS | '    assert router_per_layer == 32_896, f"actual={router_per_layer}"' |
| `B-AC51-base` | PASS | '' |
| `B-AC51-grep` | PASS | hits=['6593a06:tests/test_schedule.py:127:    `WB = 0.0476` and a `> 2.0` severe-clustering threshold; neither appears'] |
| `G-AC51-key` | PASS |  |
| `G-AC-06-keys` | PASS | dead=[] |
| `G-AC-26-keys` | PASS | dead=[] |
| `G-AC-27-keys` | PASS | dead=[] |
| `G-AC-29-keys` | PASS | dead=[] |
| `G-AC-30-keys` | PASS | dead=[] |
| `G-AC-50-keys` | PASS | dead=[] |
| `G-AC-51-keys` | PASS | dead=[] |
| `F-counts` | PASS | A=108 B=15 |
| `F-errata` | **FAIL** | sections=5 |
| `F-fixing` | PASS | count=3 |
| `F-AC-06-verdict_class` | PASS | expected '**裁决**：FIXED_BY_COMMIT' |
| `F-AC-06-baseline_status` | PASS | expected '**基线**：`touched-since-pin`' |
| `F-AC-06-location_line` | PASS | expected ':67' |
| `F-AC-06-fixing` | PASS |  |
| `F-AC-26-verdict_class` | PASS | expected '**裁决**：FIXED_BY_COMMIT' |
| `F-AC-26-baseline_status` | PASS | expected '**基线**：`unchanged-since-pin`' |
| `F-AC-26-location_line` | PASS | expected ':178' |
| `F-AC-26-fixing` | PASS |  |
| `F-AC-27-verdict_class` | PASS | expected '**裁决**：MOVED' |
| `F-AC-27-baseline_status` | PASS | expected '**基线**：`unchanged-since-pin`' |
| `F-AC-27-location_line` | PASS | expected ':122' |
| `F-AC-29-verdict_class` | PASS | expected '**裁决**：PARTIALLY_REAL' |
| `F-AC-29-baseline_status` | PASS | expected '**基线**：`unverifiable (no pin line)`' |
| `F-AC-29-location_line` | PASS | expected ':1336' |
| `F-AC-30-verdict_class` | PASS | expected '**裁决**：FIXED_BY_COMMIT' |
| `F-AC-30-baseline_status` | PASS | expected '**基线**：`unchanged-since-pin`' |
| `F-AC-30-location_line` | PASS | expected ':90' |
| `F-AC-30-fixing` | PASS |  |
| `F-AC-50-verdict_class` | PASS | expected '**裁决**：PARTIALLY_REAL' |
| `F-AC-50-baseline_status` | PASS | expected '**基线**：`unchanged-since-pin`' |
| `F-AC-50-location_line` | PASS | expected ':383' |
| `F-AC-51-verdict_class` | PASS | expected '**裁决**：PARTIALLY_REAL' |
| `F-AC-51-baseline_status` | PASS | expected '**基线**：`unchanged-since-pin`' |
| `F-AC-51-location_line` | PASS | expected ':69' |
