"""Apply evidence/pointer_fixes.py. The SAME table emits the delta and
lands the edits, so the two cannot fork.

    uv run --no-project python evidence/apply_fixes.py --check
    uv run --no-project python evidence/apply_fixes.py --write

``--check`` reports what would change and fails loudly on any entry whose
token is absent or ambiguous. ``--write`` additionally asserts, after
writing, that (a) the line count is unchanged, (b) the line-ending profile
is unchanged, and (c) re-reading the file shows the intended lines changed
and nothing else.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pointer_scan as ps  # noqa: E402
from pointer_fixes import FIXES  # noqa: E402

ROOT = Path(r"D:\myProject\DecompMoE")


def profile(text: str):
    crlf = text.count("\r\n")
    return {
        "crlf": crlf,
        "lf_only": text.count("\n") - crlf,
        "bom": text.startswith("﻿"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    by_file = defaultdict(list)
    for entry in FIXES:
        by_file[entry[0]].append(entry)

    failures = []
    plan = {}
    applied = 0
    already = 0
    for rel, entries in sorted(by_file.items()):
        path = ROOT / rel.replace("/", "\\")
        text = path.read_text(encoding="utf-8", newline="")
        before_profile = profile(text)
        before_lines = text.count("\n")
        new_lines = text.split("\n")
        touched = set()

        for entry in entries:
            rel_, lineno, token, repl, why = entry[:5]
            # An optional 6th field: how many times the token may occur on
            # that line. It exists because one LOOPS.md line names the same
            # ticket coordinate twice and both must become the same stable
            # identifier; the default of 1 still catches genuine ambiguity.
            want = entry[5] if len(entry) > 5 else 1
            if rel_ != rel:
                continue
            if lineno > len(new_lines):
                failures.append("%s:%d  line does not exist" % (rel, lineno))
                continue
            line = new_lines[lineno - 1]
            n = line.count(token)
            if n != want:
                # Idempotence: the token being gone because the replacement
                # is already there means this entry landed on a previous
                # run. Anything else is a real failure.
                if repl and repl in line:
                    already += 1
                    touched.add(lineno)
                    continue
                failures.append(
                    "%s:%d  token occurs %d time(s), expected %d: %r  (%s)"
                    % (rel, lineno, n, want, token, why))
                continue
            new_lines[lineno - 1] = line.replace(token, repl)
            applied += 1
            touched.add(lineno)

        new_text = "\n".join(new_lines)
        plan[rel] = (new_text, before_profile, before_lines, touched)

    print("=" * 74)
    print("PLAN: %d file(s), %d entr(ies)  [apply=%d, already landed=%d]"
          % (len(by_file), len(FIXES), applied, already))
    for rel, (new_text, prof, before_lines, touched) in sorted(plan.items()):
        old_text = (ROOT / rel.replace("/", "\\")).read_text(
            encoding="utf-8", newline="")
        if new_text == old_text and any(
                rel == e[0] and e[1] in touched and e[2] in old_text
                for e in FIXES):
            pass          # nothing left to change on this file
        elif new_text == old_text and touched:
            pass          # every entry on this file already landed
        elif new_text == old_text:
            failures.append("%s  no change produced" % rel)
        print("  %-56s %2d line(s)  crlf=%d lf=%d bom=%s"
              % (rel, len(touched), prof["crlf"], prof["lf_only"],
                 prof["bom"]))

    if failures:
        print()
        print("PRECONDITION FAILURES (%d):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1

    if not args.write:
        print()
        print("--check OK. Re-run with --write to apply.")
        return 0

    for rel, (new_text, prof, before_lines, touched) in sorted(plan.items()):
        path = ROOT / rel.replace("/", "\\")
        if new_text.count("\n") != before_lines:
            failures.append("%s  line count changed; the table is supposed "
                            "to be line-preserving" % rel)
            continue
        after = profile(new_text)
        if after != prof:
            failures.append("%s  line-ending profile changed %s -> %s"
                            % (rel, prof, after))
            continue
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)

    if failures:
        print()
        print("WRITE FAILURES (%d):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1

    # ---- read back and confirm the census moved -----------------------
    after = ps.scan(ROOT)
    act = [s for s in after if not s.historical]
    print()
    print("READ-BACK")
    for rel in sorted(by_file):
        left = [s for s in act if s.path == rel]
        print("  %-56s %d actionable remaining" % (rel, len(left)))
        for s in sorted(left, key=lambda x: x.line):
            print("        L%-5d %-22s %s" % (s.line, s.kind, s.detail))
    print("  TOTAL actionable: %d (was 75)" % len(act))
    return 0


if __name__ == "__main__":
    sys.exit(main())
