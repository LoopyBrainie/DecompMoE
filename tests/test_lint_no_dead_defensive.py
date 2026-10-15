"""Guard for `scripts/lint_no_dead_defensive.py`.

The lint reported OK for its whole life while the one real instance of the
anti-pattern sat in `src/decompmoe/schedule.py`: its three patterns each
matched a tuple of EXACTLY two exception names, and the instance named
three. A green produced by no-match is indistinguishable from a green
produced by no-defect, so these tests pin the pattern against every form it
is supposed to catch -- and, just as importantly, against the forms it must
leave alone.

This file necessarily contains literal anti-pattern strings, so
`lint_no_dead_defensive.py` skips it through the shared `SELF_EXCLUDE`
prefix list. That is the convention `governance/spec.md` requires of a lint
scanning `tests/**`.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_spec = importlib.util.spec_from_file_location(
    "lint_no_dead_defensive", _SCRIPTS / "lint_no_dead_defensive.py")
assert _spec and _spec.loader
lnd = importlib.util.module_from_spec(_spec)
# module_from_spec does not register in sys.modules; the module under test
# imports pointer_scan at import time, so register before executing.
sys.modules["lint_no_dead_defensive"] = lnd
_spec.loader.exec_module(lnd)


def _matches(text: str) -> bool:
    return any(re.search(pat, text) for pat, _ in lnd.PATTERNS)


def test_pattern_is_arity_agnostic() -> None:
    """The defect: a three-name tuple matched none of the three patterns.

    Every one of these is the same anti-pattern, and every one must match.
    """
    assert _matches("        except (TypeError, ValueError, OverflowError) as exc:")
    assert _matches("    except (ValueError, ZeroDivisionError):")
    assert _matches("    except (ValueError, RuntimeError):")
    assert _matches("    except (TypeError, ValueError):")


def test_pattern_matches_at_arity_one_and_four() -> None:
    """Arity is unconstrained, so the ends of the range must hold too."""
    assert _matches("    except (ValueError):")
    assert _matches(
        "    except (TypeError, ValueError, OverflowError, RuntimeError):"
    )


def test_pattern_ignores_newlines_and_indentation_variation() -> None:
    assert _matches("except(TypeError,ValueError):")
    assert _matches("            except  (  TypeError ,  ValueError  )  as e:")


def test_pattern_leaves_legitimate_handlers_alone() -> None:
    """A bare name is not this anti-pattern; a foreign member is not either.

    `except (KeyError, ValueError)` is ordinary input validation -- KeyError
    is not in the never-raised set, so the tuple must not match as a whole.
    """
    assert not _matches("    except SyntaxError:")
    assert not _matches("    except ValueError:")
    assert not _matches("    except (KeyError, ValueError):")
    assert not _matches("    except (IndexError, StopIteration):")
    assert not _matches("    except OSError as exc:")


def test_scope_reaches_tests_and_stays_repo_relative() -> None:
    """The widened scope must actually widen, and paths must stay repo-relative.

    The previous `path.relative_to(path.parents[2])` was hard-wired to the
    depth of `src/decompmoe/*.py`; a `tests/` path came back as
    `DecompMoE/tests/...` and every exemption key silently stopped matching.
    """
    rels = [p.relative_to(lnd.REPO_ROOT).as_posix() for p in lnd._iter_sources()]
    assert any(r.startswith("src/decompmoe/") for r in rels)
    assert any(r.startswith("tests/") for r in rels)
    assert all(not r.startswith("DecompMoE/") for r in rels)


def test_scope_skips_its_own_fixtures_and_caches() -> None:
    """A lint never reports its own fixtures."""
    rels = [p.relative_to(lnd.REPO_ROOT).as_posix() for p in lnd._iter_sources()]
    assert not any(r.startswith("tests/test_lint_") for r in rels)
    assert not any(r.startswith("scripts/lint_") for r in rels)
    assert not any("__pycache__" in r or ".ruff_cache" in r for r in rels)


def test_no_justified_exemptions_table_remains() -> None:
    """No exemption table: its (path, line) keys rot on any shift above them."""
    assert not hasattr(lnd, "JUSTIFIED_EXEMPTIONS")
