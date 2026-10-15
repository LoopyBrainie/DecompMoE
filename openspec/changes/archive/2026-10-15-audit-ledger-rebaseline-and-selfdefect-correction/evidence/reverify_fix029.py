#!/usr/bin/env python3
r"""Re-verify FIX-029's numeric claim at a pinned commit.

Why this script exists
----------------------
`opsx-changes.md` / FIX-029 carries an `evidence` line whose two numbers are
transposed relative to its own green/red labels. The defect class this change
repairs is "an observation copied by hand into the ledger". Therefore the
corrected values must be *regenerated*, not transcribed -- including from this
change's own proposal-stage conversation, which is the same untrusted channel.

What it measures
----------------
The construction under `tests/test_metrics.py::
test_mci_centered_covariance_upper_endpoint_unreachable`, for a range of `d_c`:

    T          = torch.eye(d_c)                          # line 154
    mu         = T.mean(dim=0)                           # line 156
    centered   = T - mu                                  # line 157
    M_centered = (centered.T @ centered) / d_c            # line 158
    eigvals    = torch.linalg.eigvalsh(M_centered)        # line 159

against the two literal thresholds the test applies:

    nonzero_count = int((eigvals > 1e-10).sum().item())   # line 161
    assert eigvals[0].item() < 1e-10                     # line 166

Run from the repository root:
    PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/reverify_fix029.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import torch

TEST = Path("tests/test_metrics.py")
TEST_FN = "test_mci_centered_covariance_upper_endpoint_unreachable"
THRESHOLD = 1e-10
D_C_VALUES = (8, 16, 32, 64)


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, check=True)
    return result.stdout.decode("utf-8", "replace")


def report_test_shape() -> None:
    """Task 2.4: establish that the d_c sweep is NOT test coverage.

    The test hard-codes `d_c = 16` and is not parameterised, so nothing in the
    test suite exercises any other d_c. The sweep below is therefore a property
    of the CONSTRUCTION, and the ledger wording must not imply the test covers
    the variants.

    The `d_c` literal is located INSIDE the target test's own body: the file
    carries several `d_c = 16` literals, and a file-wide first-match search
    reports a line belonging to a different test.
    """
    source = TEST.read_text(encoding="utf-8")
    lines = source.splitlines()

    start = next(
        (i for i, ln in enumerate(lines) if ln.startswith(f"def {TEST_FN}(")),
        None,
    )
    assert start is not None, f"{TEST_FN} not found in {TEST}"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("def ")),
        len(lines),
    )
    body = lines[start:end]

    literals = [
        (start + 1 + offset, ln.strip())
        for offset, ln in enumerate(body)
        if re.match(r"^\s*d_c = \d+$", ln)
    ]
    assert literals, f"no `d_c = <int>` literal inside {TEST_FN}"

    parametrize = [
        f"{TEST}:{start + 1 + offset}"
        for offset, ln in enumerate(body)
        if ln.strip().startswith("@pytest.mark.parametrize")
    ]

    print("== test shape ==")
    print(f"  test function      : {TEST_FN}  (lines {start + 1}-{end})")
    print(f"  d_c literal(s)     : "
          f"{', '.join(f'{TEST}:{n} ({t})' for n, t in literals)}")
    print(f"  parametrize marks  : {parametrize or 'none'}")
    print("  => the d_c sweep below is a property of the CONSTRUCTION, "
          "not of the test suite.")
    print()


def sweep() -> None:
    print(f"torch {torch.__version__}")
    print(f"threshold literal: {THRESHOLD!r}  (tests/test_metrics.py:161 and :166)")
    print()
    print(f"{'d_c':>4}  {'eigvals[0]':>16}  {'nonzero':>9}  {'rank_ok':>8}  "
          f"{'nearzero_ok':>11}  {'verdict':>8}")
    for d_c in D_C_VALUES:
        identity = torch.eye(d_c)
        mu = identity.mean(dim=0)
        centered = identity - mu.unsqueeze(0)
        m_centered = (centered.T @ centered) / d_c
        eigvals = torch.linalg.eigvalsh(m_centered)
        nonzero_count = int((eigvals > THRESHOLD).sum().item())
        smallest = eigvals[0].item()
        rank_ok = nonzero_count == d_c - 1
        nearzero_ok = smallest < THRESHOLD
        verdict = "PASS" if rank_ok and nearzero_ok else "RED"
        print(f"{d_c:>4}  {smallest:>+16.6e}  {nonzero_count:>4}/{d_c - 1:<4}  "
              f"{str(rank_ok):>8}  {str(nearzero_ok):>11}  {verdict:>8}")


def provenance() -> None:
    print()
    print("== provenance ==")
    print(f"  HEAD               : {git('rev-parse', 'HEAD').strip()}")
    history = git("log", "--oneline", "--", str(TEST)).strip().splitlines()
    print(f"  commits touching {TEST}: {len(history)}")
    for line in history[:5]:
        print(f"      {line}")


if __name__ == "__main__":
    report_test_shape()
    sweep()
    provenance()
