# 2026-10-04-fix-wayfinder-advisory-drift-a7

Close the still-real part of the A-7 wayfinder advisory-layer drift (AC-93/94/95/96/98/99): ticket-side `(historical, …)` annotations normalised to the req-gov-4 clause 4(a) form, `wayfinder/map.md` resynced to spec canonical values, A5-3's orphan `N_e=64` block deleted, plus a direct-quadrature regression guard that pins the Voronoi cap-area closed form. Doc-level only: 0 spec delta, 0 `src/` change.
