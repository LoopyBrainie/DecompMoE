"""Replace -- or, with a 4th argument, insert after -- one tasks.md line.

The `edit` tool refused an exact match on a line it had just displayed, which
means the line carries a character the read view normalises away. Matching on a
stable prefix is the robust way to patch these CJK-heavy task lines.

  usage: python patch_tasks_line.py <tasks.md> <line-prefix> <replacement-file> [after]

The prefix-uniqueness guard is load-bearing, not decoration: an empty prefix
aborts on 82 matches rather than rewriting 82 lines. The `after` mode inserts
the replacement file's text as its own block after the matched line, which is
how a new task is added to a section without renumbering anything.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) not in (4, 5):
    print(__doc__)
    sys.exit(2)
tasks, prefix, newfile = sys.argv[1], sys.argv[2], sys.argv[3]
mode = sys.argv[4] if len(sys.argv) == 5 else "replace"

p = Path(tasks)
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
if len(hits) != 1:
    print(f"ABORT: prefix {prefix!r} matched {len(hits)} lines")
    sys.exit(1)

new = Path(newfile).read_text(encoding="utf-8")
if not new.endswith("\n"):
    new += "\n"

if mode == "after":
    lines[hits[0] + 1:hits[0] + 1] = [new]
    what = f"inserted after line {hits[0] + 1}"
else:
    lines[hits[0]] = new
    what = f"replaced line {hits[0] + 1}"

p.write_text("".join(lines), encoding="utf-8", newline="")
print(f"{what} via prefix {prefix!r}: {len(new)} chars, {new.count(chr(10))} newlines")
