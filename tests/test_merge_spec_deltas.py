"""Tests for scripts/merge_spec_deltas.py: parameterization + anchor assignment。

Recovers from `openspec archive --yes` EPERM on Windows hosts. The script
splices MODIFIED blocks into the master and appends ADDED blocks with
auto-assigned `<a id="req-N"></a>` anchors (numbered from the next unused
slot after the master's highest existing anchor). These tests guard against
the v1 bug that deleted 15 master requirements when the boundary regex
matched `---` separators instead of the requirement / anchor headers.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "merge_spec_deltas.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "merge_spec_deltas", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mod():
    return _load_module()


def _write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


# ---------- primitive: anchor scanning ----------


def test_highest_existing_anchor_picks_max(mod):
    text = (
        'foo\n<a id="req-7"></a>\nbar\n'
        '<a id="req-12"></a>\nbaz\n'
        '<a id="req-3"></a>\n'
    )
    assert mod.highest_existing_anchor(text) == 12


def test_highest_existing_anchor_zero_when_absent(mod):
    assert mod.highest_existing_anchor("no anchors here") == 0


# ---------- primitive: block anchoring ----------


def test_ensure_block_anchor_prepends_when_missing(mod):
    block = "### Requirement: Foo\nbody\n"
    out = mod.ensure_block_anchor(block, "req-9")
    assert out.startswith('<a id="req-9"></a>')
    assert "### Requirement: Foo" in out


def test_ensure_block_anchor_preserves_existing(mod):
    block = '<a id="req-2"></a>\n\n### Requirement: Foo\nbody\n'
    assert mod.ensure_block_anchor(block, "req-9") == block


# ---------- end-to-end merge ----------


def test_merge_replaces_modified_and_appends_added_with_consecutive_anchors(
    tmp_path, mod
):
    master = tmp_path / "spec.md"
    delta = tmp_path / "delta.md"

    _write(
        master,
        "preamble\n\n<a id=\"req-1\"></a>\n\n### Requirement: One\nbody\n",
    )
    _write(
        delta,
        "## MODIFIED Requirements\n\n"
        "### Requirement: One\nNEW body for One\n\n"
        "## ADDED Requirements\n\n"
        "### Requirement: Two\nbody two\n\n"
        "### Requirement: Three\nbody three\n",
    )

    applied, missing, assigned = mod.merge_into_master(
        master, delta, "test-cap"
    )

    assert applied == ["One"]
    assert missing == []
    assert assigned == 2

    text = master.read_text(encoding="utf-8")
    assert '<a id="req-2"></a>' in text
    assert '<a id="req-3"></a>' in text
    assert "NEW body for One" in text
    assert "### Requirement: Two" in text
    assert "### Requirement: Three" in text
    # Old "body" of One is gone (replaced by NEW body for One)
    assert "### Requirement: One\nNEW body for One" in text


def test_merge_continues_anchor_sequence_from_existing_max(tmp_path, mod):
    master = tmp_path / "spec.md"
    delta = tmp_path / "delta.md"

    _write(
        master,
        "<a id=\"req-25\"></a>\n\n### Requirement: TwentyFive\nbody 25\n",
    )
    _write(
        delta,
        "## ADDED Requirements\n\n"
        "### Requirement: NewOne\nbody\n",
    )

    _applied, _missing, assigned = mod.merge_into_master(
        master, delta, "test-cap"
    )

    assert assigned == 1
    text = master.read_text(encoding="utf-8")
    # Assigned anchor is req-26, not req-1
    assert '<a id="req-26"></a>' in text
    assert '<a id="req-1"></a>' not in text.split(
        '<a id="req-25"></a>'
    )[-1]


def test_merge_refuses_missing_modified_title(tmp_path, mod):
    master = tmp_path / "spec.md"
    delta = tmp_path / "delta.md"

    _write(master, "preamble\n<a id=\"req-1\"></a>\n")
    _write(
        delta,
        "## MODIFIED Requirements\n\n"
        "### Requirement: NotInMaster\nbody\n",
    )

    applied, missing, assigned = mod.merge_into_master(
        master, delta, "test-cap"
    )

    assert applied == []
    assert missing == ["NotInMaster"]
    assert assigned == 0
    # And the master is left untouched when no MODIFIED applied (ADDED also
    # skipped because the delta has no ADDED section — see test below for
    # the partial-success case).
    assert "NotInMaster" not in master.read_text(encoding="utf-8")


def test_merge_partial_success_when_some_modified_missing(tmp_path, mod):
    """ADDED blocks still get appended when one MODIFIED title is absent;
    the missing title is reported but doesn't abort."""
    master = tmp_path / "spec.md"
    delta = tmp_path / "delta.md"

    _write(
        master,
        "<a id=\"req-1\"></a>\n\n### Requirement: Known\nbody\n",
    )
    _write(
        delta,
        "## MODIFIED Requirements\n\n"
        "### Requirement: Known\nNEW body\n\n"
        "### Requirement: Ghost\nbody\n\n"
        "## ADDED Requirements\n\n"
        "### Requirement: Extra\nbody\n",
    )

    applied, missing, assigned = mod.merge_into_master(
        master, delta, "test-cap"
    )

    assert applied == ["Known"]
    assert missing == ["Ghost"]
    assert assigned == 1
    text = master.read_text(encoding="utf-8")
    assert "NEW body" in text
    assert '<a id="req-2"></a>' in text
    assert "### Requirement: Extra" in text