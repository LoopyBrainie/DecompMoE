#!/usr/bin/env python3
"""Read back every artifact this change produced and check it STRUCTURALLY.

Design rules this verifier follows, each one earned:

* **It reads the written files back.** Grepping the generator's source proves
  nothing about the artifact that was actually produced.
* **It asserts COUNTS before content.** A content check over an empty list is
  vacuously true, so every "is X present" claim is preceded by "there are N of
  them".
* **It includes a NEGATIVE probe.** A guard that has never been seen to fire is
  not a guard, so the `ANNOT` duplicate-key guard is exercised against a
  deliberately corrupted copy and MUST raise.
* **It NEVER imports `_gen_listA2.py`.** That module performs its write at
  import time. Importing it to inspect a dict destroyed 436 lines of the audit
  list during this very change; see the INCIDENT section in
  `lists/opsx-changes.md` and design.md D7. The generator is read with `ast` only.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    path = os.path.abspath(start)
    while True:
        if (os.path.isdir(os.path.join(path, "openspec"))
                and os.path.isdir(os.path.join(path, ".audit"))):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError("repo root not found above %s" % start)
        path = parent


REPO = _repo_root(HERE)
AUDIT = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review")
LIST = os.path.join(AUDIT, "lists", "opsx-changes.md")
GEN = os.path.join(AUDIT, "_work", "_gen_listA2.py")
A6 = os.path.join(
    REPO, "openspec", "changes", "archive",
    "2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline", "evidence",
)
OLD_JSON = os.path.join(A6, "pin_drift_95718cf.json")
NEW_JSON = os.path.join(HERE, "drift_6593a06..95718cf.json")

BASELINE_RE = re.compile(r"^\s*[-*]?\s*\**`?基线`?\**\s*[:：]\s*(\S+)", re.M)

out: list[str] = []
failures: list[str] = []
_checks = 0


def check(label: str, ok: bool, detail: str = "") -> bool:
    global _checks
    _checks += 1
    out.append("%-4s %s%s" % ("PASS" if ok else "FAIL", label,
                              ("  -- " + detail) if detail else ""))
    if not ok:
        failures.append(label)
    return ok


def read(path: str) -> str:
    with io.open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


# ---------------------------------------------------------------- F-3
def check_artifacts():
    out.append("== F-3: regenerated drift table ==")
    if not check("new artifact exists", os.path.exists(NEW_JSON)):
        return
    if not check("archived original still present (untouched)", os.path.exists(OLD_JSON)):
        return
    new = json.loads(read(NEW_JSON))
    old = json.loads(read(OLD_JSON))

    # filename must agree with its own payload
    expect_name = "drift_%s..%s.json" % (new["pin"][:7], new["head"][:7])
    check("filename matches its pin/head payload", os.path.basename(NEW_JSON) == expect_name,
          "file=%s payload=%s" % (os.path.basename(NEW_JSON), expect_name))
    check("pin/head equal the archived original's",
          (new["pin"], new["head"]) == (old["pin"], old["head"]),
          "new=%s/%s old=%s/%s" % (new["pin"], new["head"], old["pin"], old["head"]))

    # key-by-key on all three views -- comparing file sizes would prove nothing
    for view in ("drift", "inserted", "modified"):
        n_new = len(new[view])
        n_old = len(old[view])
        iv_new = sum(len(v) for v in new[view].values())
        iv_old = sum(len(v) for v in old[view].values())
        same = new[view] == old[view]
        check("%-9s identical key-by-key (%d keys / %d intervals both sides)"
              % (view, n_new, iv_new), same and n_new == n_old and iv_new == iv_old,
              "new=%d/%d old=%d/%d" % (n_new, iv_new, n_old, iv_old))


# ---------------------------------------------------------------- F-2
def check_self_check_reports_key_sets():
    out.append("== F-2: self_check reports key-set differences ==")
    script = os.path.join(HERE, "build_pin_drift.py")
    r = subprocess.run([sys.executable, script, "--self-check"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=REPO)
    combined = (r.stdout or "") + (r.stderr or "")
    check("self-check exits 0 on the real tables", r.returncode == 0,
          "exit=%d" % r.returncode)
    check("reports interval equality with a number", "interval equality" in combined)
    check("states the key sets are NOT identical", "KEY SETS ARE NOT IDENTICAL" in combined)
    check("lists the extra keys individually",
          combined.count("only-in-mine (empty intervals):") == 12,
          "count=%d" % combined.count("only-in-mine (empty intervals):"))
    check("no longer prints the misleading bare 'files=' number",
          "files," not in combined and "(60 files" not in combined)
    check("declares key-count equality is not asserted",
          "not asserted" in combined)

    # NEGATIVE: the guard must reject a non-empty only-in-mine key. Exercised
    # through the pure `compare()` function, so no file has to be mutated.
    # `build_pin_drift.py` is safe to import -- it writes only inside main(),
    # unlike `_gen_listA2.py`. `compare()` is pure, so the negative cases can be
    # driven directly without mutating any file.
    spec = importlib.util.spec_from_file_location("bpd", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    base = {"pin": "p", "head": "h", "commits": [], "drift": {"a": [[1, 2]]}}
    benign = {"pin": "p", "head": "h", "commits": [],
              "drift": {"a": [[1, 2]], "b": []}}
    hostile = {"pin": "p", "head": "h", "commits": [],
               "drift": {"a": [[1, 2]], "b": [[7, 9]]}}
    lost = {"pin": "p", "head": "h", "commits": [], "drift": {}}

    p_benign, s_benign = mod.compare(base, benign)
    check("NEGATIVE PROBE 1: an extra EMPTY key is accepted as benign",
          not p_benign, "problems=%r" % p_benign)
    check("  ... and is still reported in stats, not swallowed",
          s_benign["only_mine"] == ["b"] and s_benign["only_mine_nonempty"] == [])

    p_hostile, s_hostile = mod.compare(base, hostile)
    check("NEGATIVE PROBE 2: an extra NON-EMPTY key is REJECTED",
          len(p_hostile) == 1 and "NON-EMPTY" in p_hostile[0], "problems=%r" % p_hostile)
    check("  ... and is named in stats", s_hostile["only_mine_nonempty"] == ["b"])

    p_lost, s_lost = mod.compare(base, lost)
    check("NEGATIVE PROBE 3: a LOST key is rejected",
          len(p_lost) == 1 and "MISSING" in p_lost[0], "problems=%r" % p_lost)
    check("  ... and is named in stats", s_lost["only_original"] == ["a"])


# ---------------------------------------------------------------- ANNOT
def _annot_literal(path):
    tree = ast.parse(read(path), filename=path)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ANNOT":
                    return node.value
    return None


def check_annot():
    out.append("== ANNOT duplicate keys (read with ast; the module is NEVER imported) ==")
    node = _annot_literal(GEN)
    if not check("ANNOT literal located in the generator source", node is not None):
        return
    keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
    n = len(keys)
    check("ANNOT declares 19 keys (merged, none dropped)", n == 19, "count=%d" % n)
    check("ANNOT has NO duplicate keys", len(set(keys)) == n,
          "dupes=%r" % [k for k in set(keys) if keys.count(k) > 1])

    # both merged segments survived -- the whole point of merging instead of
    # letting the later duplicate win
    text = read(GEN)
    for label, needle in {
        "AC-28 [边界保留]": "check-completeness 将本条列为 borderline",
        "AC-28 [溯源缺口]": "D1-03 由本条与 AC-04 / AC-15 共同承载",
        "AC-29 [分桶存疑]": "D3 未能证明 Jensen 单向界本身",
        "AC-29 [溯源缺口已消]": "溯源缺口已消 + 位置已更正",
    }.items():
        check("%s segment present in the generator source" % label, needle in text)

    # NEGATIVE PROBE: the guard must fire on a corrupted copy. The guard reads
    # `__file__`, so it is exec'd with __file__ pointed at the corrupted copy --
    # the real generator is never touched and never imported.
    with tempfile.TemporaryDirectory() as tmp:
        corrupt = os.path.join(tmp, "gen_corrupt.py")
        inject_at = text.index('    "AC-28": ')
        with io.open(corrupt, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text[:inject_at] + '    "AC-28": "[PROBE]",\n' + text[inject_at:])
        check("probe copy really does contain a duplicate key",
              _annot_literal(corrupt) is not None
              and len([k.value for k in _annot_literal(corrupt).keys]) == n + 1)

        guard_src = None
        for node_ in ast.parse(read(GEN)).body:
            if isinstance(node_, ast.FunctionDef) and node_.name == "_assert_no_duplicate_annot_keys":
                guard_src = ast.get_source_segment(read(GEN), node_)
        if not check("guard function found in the generator", guard_src is not None):
            return
        ns: dict = {"__file__": GEN, "__name__": "guard_under_test"}
        exec(compile(guard_src, GEN, "exec"), ns)
        guard = ns["_assert_no_duplicate_annot_keys"]

        check("guard passes on the REAL generator", guard() == 19, "count=%r" % guard())

        ns_bad: dict = {"__file__": corrupt, "__name__": "guard_under_test"}
        exec(compile(guard_src, corrupt, "exec"), ns_bad)
        try:
            ns_bad["_assert_no_duplicate_annot_keys"]()
            raised = False
            msg = ""
        except AssertionError as exc:
            raised = True
            msg = str(exc)
        check("NEGATIVE PROBE: the guard RAISES on a duplicate key", raised, msg[:120])
        check("  ... and the message names the offending key", "AC-28" in msg, msg[:120])


# ---------------------------------------------------------------- write guard
def check_generator_refuses_live():
    out.append("== generator refuses to overwrite the live list ==")
    r = subprocess.run([sys.executable, GEN, LIST],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=REPO)
    combined = (r.stdout or "") + (r.stderr or "")
    check("exits non-zero when pointed at the live list", r.returncode != 0,
          "exit=%d" % r.returncode)
    check("says why", "REFUSING" in combined and "Errata" in combined)
    # and the refusal must not have damaged anything
    check("live list still has 5 Errata sections afterwards",
          sum(1 for l in read(LIST).split("\n") if l.startswith("## Errata")) == 5)


# ---------------------------------------------------------------- the list
def check_list():
    out.append("== lists/opsx-changes.md (read back from disk) ==")
    text = read(LIST)
    lines = text.split("\n")

    errata_heads = [l for l in lines if l.startswith("## Errata")]
    n_errata = len(errata_heads)
    check("5 Errata sections", n_errata == 5, "count=%d" % n_errata)
    # Identify headings by their ASCII prefix, never by a hand-typed CJK literal:
    # typing 溯/段/侧 wrong produces a false failure on correct data (it did, once).
    # The four pre-existing sections are `## Errata`, `(A-2 ...)`, `(A-4 ...)` and
    # `(A-6 ...)`; THIS change adds a second `(A-6 ...)`.
    check("one bare `## Errata` plus four parenthesised ones",
          sum(1 for h in errata_heads if h == "## Errata") == 1
          and sum(1 for h in errata_heads if h.startswith("## Errata (")) == 4,
          "heads=%d" % n_errata)
    for tag in ("A-2", "A-4", "A-6"):
        got = sum(1 for h in errata_heads if h.startswith("## Errata (%s " % tag))
        want = 2 if tag == "A-6" else 1
        check("exactly %d `(%s ...)` Errata section(s)" % (want, tag), got == want,
              "count=%d" % got)
    # this change's section, located by an ASCII-only token unique to its body
    check("this change's Errata content is present",
          "_assert_no_duplicate_annot_keys" in text
          and "INCIDENT" in text)

    # 基线 declarations: assert the COUNT first, then the tally
    decls = BASELINE_RE.findall(text)
    check("108 基线 declarations", len(decls) == 108, "count=%d" % len(decls))
    tally = {}
    for d in decls:
        key = d.rstrip("`.,;。，、")
        tally[key] = tally.get(key, 0) + 1
    check("tally is 23 / 72 / 13 (design D1)",
          tally.get("`touched-since-pin") == 23
          and tally.get("`unchanged-since-pin") == 72
          and tally.get("`unverifiable") == 13, "tally=%r" % tally)

    # The corrected 口径 wording must be in the BODY. What must be gone from the
    # body is the OLD PASSAGE presenting the misleading figure as current fact --
    # not the phrase itself, which the corrected passage deliberately quotes when
    # explaining what changed. Assert on the passage, not on a fragment.
    body_end = text.index("## Errata")
    body = text[:body_end]
    old_passage = "105 区间 / 0 差异）作为自检。"
    check("old 口径 passage (old figure stated as current fact) is gone from the body",
          old_passage not in body)
    check("corrected 口径 wording states the two facts separately",
          "48 个共有键" in body and "12 个键" in body
          and "键数相等不是被断言的不变量" in body)
    check("the old figure is still quoted somewhere, as the corrected thing",
          "60 文件 / 105 区间 / 0 差异" in text)

    # the restored AC-28 segment must appear in the product, exactly once
    needle = "check-completeness 将本条列为 borderline"
    check("restored AC-28 [边界保留] segment appears exactly once",
          text.count(needle) == 1, "count=%d" % text.count(needle))


def check_a6_verifier_state():
    """Pin the A-6 verifier's known-stale check, so a REAL regression is visible.

    The A-6 change's own `verify_a6_errata.py` has a check named `F-errata` whose
    expectation is "all FOUR Errata sections survive". This change deliberately
    adds a FIFTH, so that check now fails -- by design, not by regression.

    Left unpinned, the next person to run it sees 1 red, cannot tell it apart
    from a real breakage, and the tempting "fix" is to delete the new Errata.
    So the expected outcome is asserted EXACTLY here: 65 checks, exactly one
    failure, and that failure must be `F-errata`. Any other failure is a real
    regression in the A-6 corrections and must go red.
    """
    out.append("== A-6 verifier: exactly one known-stale failure, no others ==")
    script = os.path.join(A6, "verify_a6_errata.py")
    r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=REPO)
    combined = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"checks=(\d+) passed=(\d+) failed=(\d+)", combined)
    if not check("A-6 verifier prints its tally", m is not None,
                 combined.strip()[-120:]):
        return
    total, passed, failed = (int(g) for g in m.groups())
    check("A-6 verifier still runs 65 checks", total == 65,
          "actual=%d" % total)
    check("64 of 65 A-6 checks pass (the A-6 field corrections are intact)",
          passed == 64, "actual=%d" % passed)
    check("exactly ONE A-6 check fails", failed == 1, "actual=%d" % failed)

    fails = re.findall(r"FAIL\s+(\S+)", combined)
    check("the single failure is F-errata, and nothing else",
          fails == ["F-errata"], "failures=%r" % fails)
    check("F-errata's own message shows the section count is 5, not a content problem",
          "sections=5" in combined, "")


def main():
    check_artifacts()
    check_self_check_reports_key_sets()
    check_annot()
    check_generator_refuses_live()
    check_list()
    check_a6_verifier_state()

    out.append("")
    out.append("RESULT: %d check(s), %d failure(s)" % (_checks, len(failures)))
    for f in failures:
        out.append("  FAILED: %s" % f)
    report = "\n".join(out) + "\n"
    with io.open(os.path.join(HERE, "verify_artifacts_report.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    print("checks=%d failures=%d" % (_checks, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
