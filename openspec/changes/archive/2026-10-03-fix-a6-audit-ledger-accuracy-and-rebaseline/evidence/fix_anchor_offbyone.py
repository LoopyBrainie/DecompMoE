# -*- coding: utf-8 -*-
"""Correct two of this change's own line anchors.

The first pass took pin-state line numbers from a PowerShell pipeline that
silently dropped a blank line, shifting every label by one. Python's own
`git show` view agrees with `git grep -n` (which put `router_per_layer == 32_896`
at L69), so it is authoritative:

  * AC-26: the assertion message carrying `actual=` is pin L**178** (L177 is the
    `assert` line). 177 was wrong.
  * AC-50: pin `wayfinder/spec.md:383` **is** the Req 17 body. The original
    pointer was already correct; "L383 is blank, body is L382" was wrong, so the
    "correction" to 382 must be reverted.

Also fixes the report's total line count (1676 -> 1677) in AC-29's text.
"""
import io
import json
import sys

CLASSIFIED = (
    r"D:/myProject/DecompMoE/.audit/wayfinder-opsx-code-review/_work/classified.json"
)

SCALAR = {
    "AC-26": {"location_line": (177, 178)},
    "AC-50": {"location_line": (382, 383)},
}

# text fixes keyed by (bucket_id, field) -> (old_substring, new_substring, count)
TEXT = {
    ("AC-26", "evidence_ref"): [
        ("已改锚到该函数内实际承载 `actual=` 的断言行 pin L177。",
         "已改锚到该函数内实际承载 `actual=` 的断言消息行 pin L178（L177 是 `assert` 行本身）。", 1),
    ],
    ("AC-50", "problem"): [
        ("原记位置 `spec.md:383` 是空行，Req 17 正文在 L382（标题 L380）。",
         "位置复核结论：pin `spec.md:383` **就是 Req 17 正文**（anchor L379、标题 L381），原指针正确，"
         "故不改动——一次基于错误行号的「更正」曾把它改到 L382（空行），已撤回。", 1),
    ],
    ("AC-29", "problem"): [
        ("（1676 行，随审计会话变动，不受 pin 约束）",
         "（1677 行，随审计会话变动，不受 pin 约束）", 1),
    ],
}


def main():
    with io.open(CLASSIFIED, encoding="utf-8") as handle:
        data = json.load(handle)

    index = {}
    for bucket in ("opsx-change", "user-decision"):
        for item in data[bucket]:
            index.setdefault(item["bucket_id"], item)

    problems, applied = [], []
    for bid, fields in SCALAR.items():
        item = index[bid]
        for field, (want, new) in fields.items():
            got = item.get(field)
            if got != want:
                problems.append("%s.%s: expected %r, found %r" % (bid, field, want, got))
            else:
                item[field] = new
                applied.append("%s.%s %r -> %r" % (bid, field, want, new))

    for (bid, field), pairs in TEXT.items():
        item = index[bid]
        current = item.get(field) or ""
        for old, new, count in pairs:
            if current.count(old) != count:
                problems.append("%s.%s: expected %d occurrence(s) of %r, found %d" % (
                    bid, field, count, old[:40], current.count(old)))
            else:
                current = current.replace(old, new)
                applied.append("%s.%s text fixed (%r...)" % (bid, field, old[:34]))
        item[field] = current

    if problems:
        print("ABORTED -- %d problem(s)" % len(problems))
        for line in problems:
            print("  " + line)
        return 1

    with io.open(CLASSIFIED, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    with io.open(CLASSIFIED, encoding="utf-8") as handle:
        reread = json.load(handle)
    verify = []
    again = {}
    for bucket in ("opsx-change", "user-decision"):
        for item in reread[bucket]:
            again.setdefault(item["bucket_id"], item)
    for bid, fields in SCALAR.items():
        for field, (_w, new) in fields.items():
            if again[bid].get(field) != new:
                verify.append("%s.%s = %r (want %r)" % (bid, field, again[bid].get(field), new))
    for (bid, field), pairs in TEXT.items():
        for old, new, _c in pairs:
            if old in (again[bid].get(field) or ""):
                verify.append("%s.%s still contains the old text" % (bid, field))
    if verify:
        print("READ-BACK FAILED:")
        for line in verify:
            print("  " + line)
        return 1

    print("applied %d correction(s):" % len(applied))
    for line in applied:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
