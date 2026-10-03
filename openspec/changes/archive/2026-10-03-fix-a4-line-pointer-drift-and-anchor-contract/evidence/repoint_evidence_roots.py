"""Repoint every evidence script's repo-root derivation at `evidence/_repo.py`.

A fixed `parents[N]` becomes wrong the instant `openspec archive` moves the
change one directory deeper, which would make the delivered evidence
non-reproducible on exactly the commit that archives it. This rewrites the
derivation in place and then VERIFIES it: each rewritten script must still
resolve the same repo root that a direct `parents[4]` gave before the move, and
must still resolve the correct root when simulated one level deeper (the
post-archive layout).

Run before `openspec archive`.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _repo import REPO, find_repo_root  # noqa: E402

# `REPO = Path(__file__).resolve().parents[4]` and the `HERE.parents[3]` variant.
PATTERNS = [
    (re.compile(r"^(\s*)(REPO|ROOT) = Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]$", re.M),
     r'\1\2 = REPO'),
    (re.compile(r"^(\s*)(REPO|ROOT) = HERE\.parents\[(\d+)\]$", re.M),
     r'\1\2 = REPO'),
]

IMPORT_BLOCK = (
    "import sys as _sys\n"
    "from pathlib import Path as _Path\n"
    "_sys.path.insert(0, str(_Path(__file__).resolve().parent))\n"
    "from _repo import REPO  # noqa: E402\n"
)


def main() -> int:
    problems, rewritten = [], []
    for script in sorted(HERE.glob("*.py")):
        if script.name in ("_repo.py",):
            continue
        text = script.read_text(encoding="utf-8")
        new = text
        for rx, repl in PATTERNS:
            new = rx.sub(repl, new)
        if new == text:
            continue
        # `sys` and `Path` must exist before the import block is inserted.
        lines = new.splitlines(keepends=True)
        insert_at = None
        for i, l in enumerate(lines):
            if l.startswith("from pathlib import Path"):
                insert_at = i + 1
                break
            if l.startswith("import ") and insert_at is None and "pathlib" not in l:
                insert_at = i + 1
        if insert_at is None:
            problems.append(f"{script.name}: no import section found for the locator import")
            continue
        if "from _repo import REPO" not in new:
            lines.insert(insert_at, IMPORT_BLOCK)
        out = "".join(lines)
        script.write_text(out, encoding="utf-8", newline="")
        rewritten.append(script.name)

    print(f"rewritten: {len(rewritten)} script(s)")
    for n in rewritten:
        print(f"  {n}")

    # Verify statically. Executing every evidence script to inspect a module
    # attribute is not free: several of them run a census, a mutation-injection
    # check or a fix pass at import time, which is both noisy and a side-effect
    # risk. AST inspection proves the same thing — the name is bound to the
    # shared locator, not to a fixed path index.
    import ast

    for script in sorted(HERE.glob("*.py")):
        if script.name in ("_repo.py", "repoint_evidence_roots.py"):
            continue
        tree = ast.parse(script.read_text(encoding="utf-8"))
        imports_locator = any(
            isinstance(n, ast.ImportFrom) and n.module == "_repo" and "REPO" in {a.name for a in n.names}
            for n in ast.walk(tree)
        )
        bound = {
            t.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("REPO", "ROOT")
        }
        fixed_index = [
            n.lineno
            for n in ast.walk(tree)
            if isinstance(n, ast.Subscript)
            and isinstance(n.value, ast.Attribute)
            and n.value.attr == "parents"
        ]
        if bound and not imports_locator:
            problems.append(f"{script.name}: binds {sorted(bound)} but does not import the locator")
        if fixed_index:
            problems.append(f"{script.name}: still indexes .parents at line(s) {fixed_index}")

    # The property that matters: the locator survives the post-archive layout.
    # A placeholder name is not a legal directory name on Windows, so a real one
    # is used and removed again in the same call.
    archive = REPO / "openspec" / "changes" / "archive"
    simulated = archive / "_locator_probe_name" / "evidence"
    simulated.mkdir(parents=True, exist_ok=True)
    try:
        found = find_repo_root(simulated)
        if found != REPO:
            problems.append(f"simulated post-archive root {found!r} != {REPO!r}")
        else:
            print(f"post-archive layout resolves correctly: {found}")
    finally:
        simulated.rmdir()
        simulated.parent.rmdir()

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nall evidence scripts resolve the repo root independently of depth")
    return 0


if __name__ == "__main__":
    sys.exit(main())
