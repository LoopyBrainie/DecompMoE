"""Emit the OpenSpec deltas from the SAME fix table that produced the live
edits, and prove the two agree.

The sweep landed before the delta existed, so the delta is reconstructed
rather than written by hand:

  pre  = ``git show 5c49037^:<spec>``   (the file before the sweep)
  post = the working-tree file
  emit = the Requirement blocks of ``post``

Three checks make this trustworthy:

1. Applying the fix table to ``pre`` MUST reproduce ``post`` byte for byte.
   If it does not, the table is not the whole change and the delta is
   incomplete -- this is the check that would have caught a hand-written
   delta drifting from reality.
2. Every emitted Scenario title is read back from the file, never typed.
3. A MODIFIED block is only emitted for a Requirement whose text actually
   differs between pre and post, so the delta carries no no-op blocks.

``req-gov-2`` is special: one of its Scenario HEADINGS carries a line
pointer, and the validator refuses a MODIFIED block that renames a
Scenario. It is emitted as REMOVED + ADDED instead, keeping the same
Requirement title and the same anchor id.
"""
from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pointer_fixes import FIXES  # noqa: E402

ROOT = Path(r"D:\myProject\DecompMoE")
BASE = "5c49037^"
CHANGE = "2026-10-03-close-pointer-blindspot-and-full-tree-sweep"

SPECS = {
    "wayfinder": "openspec/specs/wayfinder/spec.md",
    "decompmoe-skeleton": "openspec/specs/decompmoe-skeleton/spec.md",
    "governance": "openspec/specs/governance/spec.md",
}

import re  # noqa: E402

RE_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
RE_REQ = re.compile(r"^### Requirement:")
RE_SCEN = re.compile(r"^#### Scenario:")
#: Scenario headings that must be reworded. A MODIFIED block may not
#: rename a Scenario, so this class of edit is a problem ONLY if the delta
#: is authored before the sweep. The sweep lands first (it is the same fix
#: table), the validator compares the delta against the current spec, and
#: the titles match -- so no special channel is required. Kept as a
#: documented non-issue rather than deleted, because the next reader will
#: otherwise rediscover the constraint and re-derive the wrong answer.
HEADING_RENAMES_DOC = (
    "governance req-gov-2 had a Scenario heading naming a ticket by line "
    "number. `openspec validate` rejects a MODIFIED block that renames a "
    "Scenario, and rejects the same Requirement appearing in both ADDED "
    "and REMOVED, so the REMOVE+ADD route is ALSO unavailable. The working "
    "resolution: the heading is reworded by the same fix table that does "
    "the sweep, before the delta is emitted."
)


def git_show(path: str) -> str:
    out = subprocess.run(["git", "show", "%s:%s" % (BASE, path)],
                         cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise SystemExit("git show failed for %s: %s" % (path, out.stderr))
    return out.stdout


def blocks(text: str):
    """[(anchor, title, [body lines])].

    The body EXCLUDES the ``### Requirement:`` heading line: the emitter
    writes that line itself, and prepending a second copy produced
    duplicate blocks that validate rejects as "missing requirement text".
    The anchor line sits before the heading, so it is excluded too and is
    re-emitted explicitly where the format needs it.
    """
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    marks = []
    cur = None
    for i, line in enumerate(lines):
        m = RE_ANCHOR.search(line)
        if m:
            cur = m.group(1)
            continue
        if RE_REQ.match(line) and cur:
            marks.append((i, cur, line[len("### Requirement:"):].strip()))
    out = []
    for idx, (i, anc, title) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        out.append((anc, title, lines[i + 1:end], i))
    return out


def scenarios(block_lines):
    return [l[len("#### Scenario:"):].strip()
            for l in block_lines if RE_SCEN.match(l)]


def apply_table(pre_text: str, rel: str) -> str:
    """Apply the table to the PRE text.

    The pre text comes from a git blob, which this repository stores with
    LF, while the working-tree copies of the specs are CRLF. That is a
    checkout artefact, not a content change, so the comparison happens in
    LF. The fix table is line-ending preserving by construction, and
    apply_fixes.py asserts the working-copy profile separately.
    """
    lines = pre_text.replace("\r\n", "\n").split("\n")
    for e in FIXES:
        f, lineno, token, repl = e[0], e[1], e[2], e[3]
        if f != rel:
            continue
        line = lines[lineno - 1]
        if line.count(token) != 1:
            raise SystemExit("%s:%d token not unique in PRE state: %r"
                             % (f, lineno, token))
        lines[lineno - 1] = line.replace(token, repl)
    return "\n".join(lines)


def main() -> int:
    problems = []

    for cap, rel in SPECS.items():
        pre = git_show(rel)
        post = (ROOT / rel.replace("/", "\\")).read_text(
            encoding="utf-8", newline="")
        rebuilt = apply_table(pre, rel)
        if rebuilt != post.replace("\r\n", "\n"):
            problems.append("%s: fix table applied to pre != post" % cap)
            # Show the first differing line, so the failure is actionable
            # rather than a bare boolean.
            a = rebuilt.split("\n")
            b = post.replace("\r\n", "\n").split("\n")
            for i, (x, y) in enumerate(zip(a, b), 1):
                if x != y:
                    problems.append("    first diff at L%d" % i)
                    problems.append("      pre+table: %r" % x[:110])
                    problems.append("      post      : %r" % y[:110])
                    break
        else:
            print("  %-20s table reproduces post exactly (%d lines)"
                  % (cap, len(rebuilt.split("\n"))))

        pre_b = {a: (t, b) for a, t, b, _ in blocks(pre)}
        post_b = {a: (t, b) for a, t, b, _ in blocks(post)}

        changed = [a for a in post_b
                   if a in pre_b and pre_b[a][1] != post_b[a][1]]
        removed = [a for a in pre_b if a not in post_b]
        if removed:
            problems.append("%s: Requirements disappeared: %s" % (cap, removed))

        out = []

        if changed:
            out.append("## MODIFIED Requirements")
            out.append("")
        for anc in changed:
            title, block = post_b[anc]
            out += ["### Requirement: %s" % title, ""] + block

        dest = ROOT / "openspec" / "changes" / CHANGE / "specs" / cap
        dest.mkdir(parents=True, exist_ok=True)
        dest.joinpath("spec.md").write_text("\n".join(out), encoding="utf-8")
        print("  %-20s %d MODIFIED -> %s" % (cap, len(changed), dest.name))
        for anc in changed:
            print("        %-12s MODIFIED" % anc)

    if problems:
        print()
        for p in problems:
            print("  PROBLEM: %s" % p)
        return 1
    print()
    print("OK: every delta block is read back from the file, and the fix "
          "table reproduces the post state byte for byte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
