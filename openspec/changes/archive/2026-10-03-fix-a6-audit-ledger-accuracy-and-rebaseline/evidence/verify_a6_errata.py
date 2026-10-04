# -*- coding: utf-8 -*-
"""Independently re-derive every A-6 claim from git and check it against what the
artifacts now say. Nothing here trusts the checklist, the errata, or classified.json:
each expected value is recomputed, then compared.

Covers acceptance B (7/7 fields), C (arithmetic), G (no dead origin keys), and the
structural counts from acceptance F. Any mismatch exits 1.

Output is UTF-8 to a report file; the console gets ASCII only (this host's console
is GBK and would raise on the Chinese text these artifacts contain).
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = r"D:/myProject/DecompMoE"
CHANGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(CHANGE, "evidence")
AUDIT = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review")
LIST_A = os.path.join(AUDIT, "lists", "opsx-changes.md")
LIST_B = os.path.join(AUDIT, "lists", "direct-fixes.md")
CLASSIFIED = os.path.join(AUDIT, "_work", "classified.json")
LOCK = os.path.join(EVIDENCE, "a6_expected.json")
REPORT = os.path.join(EVIDENCE, "verify_a6_errata_report.md")

PIN = "6593a06"
FROZEN = "95718cfa0b7e417935d2fbdd873eb7fec06ebb9b"
REPORT_MD = (
    "C:/Users/LamKo/.claude/projects/D--myProject-DecompMoE/"
    "a553f54e-8635-46b2-a435-55d871698d88/audit/_final_report_full.md"
)
VERDICTS = (
    "C:/Users/LamKo/.claude/projects/D--myProject-DecompMoE/"
    "a553f54e-8635-46b2-a435-55d871698d88/audit/_handoff_verdicts_all.json"
)

results = []   # (check_id, description, ok, detail)


def check(cid, desc, ok, detail=""):
    results.append((cid, desc, bool(ok), detail))
    return ok


def git(*args):
    return subprocess.run(
        ["git"] + list(args), cwd=REPO, capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")


def blob(rev, path):
    return git("rev-parse", "%s:%s" % (rev, path)).strip()


def show(rev, path):
    return git("show", "%s:%s" % (rev, path)).split("\n")


def at(rev, path, line):
    """1-based line lookup."""
    lines = show(rev, path)
    if line < 1 or line > len(lines):
        return None
    return lines[line - 1]


def main():
    lock = json.load(io.open(LOCK, encoding="utf-8"))
    items = lock["items"]
    classified = json.load(io.open(CLASSIFIED, encoding="utf-8"))
    verdicts = json.load(io.open(VERDICTS, encoding="utf-8"))
    list_a = io.open(LIST_A, encoding="utf-8").read()
    list_b = io.open(LIST_B, encoding="utf-8").read()
    drift = json.load(io.open(os.path.join(EVIDENCE, "pin_drift_95718cf.json"), encoding="utf-8"))

    # ---------------------------------------------------------- AC-06
    line67 = at(PIN, "src/decompmoe/sphere.py", 67)
    check("B-AC06-anchor", "pin sphere.py:67 is the _betainc_regularized def",
          line67 is not None and line67.startswith("def _betainc_regularized"),
          repr(line67))
    line68 = at(PIN, "src/decompmoe/sphere.py", 68)
    check("B-AC06-pinstate", "pin docstring says the single 8-point panel",
          line68 is not None and "Gauss" in line68 and "8-point" in line68, repr(line68))
    sphere_head = io.open(os.path.join(REPO, "src", "decompmoe", "sphere.py"), encoding="utf-8").read()
    check("B-AC06-fixed", "HEAD integrator is adaptive and quotes the pre-fix numbers",
          "adaptive 8/16-point" in sphere_head
          and "8.29e-07" in sphere_head and "1.57e-01" in sphere_head)
    check("B-AC06-commit", "f6461d7 is a descendant of pin (post-pin fix)",
          subprocess.run(["git", "merge-base", "--is-ancestor", "f6461d7", PIN],
                         cwd=REPO, capture_output=True).returncode != 0)

    # ---------------------------------------------------------- AC-26
    b_pin = blob(PIN, "tests/test_loss.py")
    b_fix = blob("b272787", "tests/test_loss.py")
    b_prefix = blob("8f50659", "tests/test_loss.py")
    b_parent = git("rev-parse", "%s~1" % PIN).strip()
    b_parent_file = blob(b_parent, "tests/test_loss.py")
    check("B-AC26-norevert", "pin blob == b272787 blob, and pin parent already had it",
          b_pin == b_fix == b_parent_file,
          "pin=%s fix=%s parent=%s" % (b_pin[:8], b_fix[:8], b_parent_file[:8]))
    check("B-AC26-prefix-absent", "8f50659's blob never appears in the pin state",
          b_prefix != b_pin, "8f50659 blob=%s" % b_prefix[:8])
    actual_pin = sum(1 for l in show(PIN, "tests/test_loss.py") if "actual=" in l)
    check("B-AC26-actual", "pin test_loss.py has 10 actual= occurrences (not 0)",
          actual_pin == 10, "count=%d" % actual_pin)
    line166 = at(PIN, "tests/test_loss.py", 167)
    line177 = at(PIN, "tests/test_loss.py", 178)
    check("B-AC26-anchor", "L167 was prose, L178 carries actual=",
          line166 is not None and "actual=" not in line166
          and line177 is not None and "actual=" in line177,
          "L167=%r L178=%r" % (line166, line177))
    v = verdicts.get("rv:main45:math", {})
    check("B-AC26-verdict", "rv:main45:math verdict is FIXED_BY_COMMIT, not STILL_REAL",
          v.get("verdict") == "FIXED_BY_COMMIT", repr(v.get("verdict")))
    e50 = git("merge-base", "--is-ancestor", PIN, "e50cc02",
              capture_output=False) if False else None
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", PIN, "e50cc02"],
                         cwd=REPO, capture_output=True).returncode
    check("B-AC26-timing", "e50cc02 is a descendant of pin, so it cannot define pin state",
          rc == 0, "merge-base --is-ancestor pin e50cc02 rc=%d" % rc)

    # ---------------------------------------------------------- AC-27
    numstat = git("diff", "--numstat", "33f7cc9~1", "33f7cc9", "--",
                  "openspec/specs/wayfinder/spec.md",
                  "openspec/specs/decompmoe-skeleton/spec.md",
                  "openspec/specs/governance/spec.md").strip().split("\n")
    want = {
        "openspec/specs/wayfinder/spec.md": (3, 2),
        "openspec/specs/decompmoe-skeleton/spec.md": (14, 1),
        "openspec/specs/governance/spec.md": (9, 1),
    }
    ok = True
    detail = []
    for row in numstat:
        parts = row.split("\t")
        path, adds, dels = parts[2], int(parts[0]), int(parts[1])
        detail.append("%s=%d/%d" % (path.split("/")[-2], adds, dels))
        if (adds, dels) != want[path]:
            ok = False
    check("B-AC27-numbers", "33f7cc9 net change is +1/+13/+8 (as the list claims)",
          ok, "; ".join(detail))
    nets = []
    for path, (adds, dels) in want.items():
        old = len(show("33f7cc9~1", path))
        new = len(show("33f7cc9", path))
        nets.append((path, new - old, adds - dels))
    check("B-AC27-crosscheck", "real line counts agree with numstat on all three specs",
          all(n == d for _p, n, d in nets),
          "; ".join("%s net=%d" % (p.split("/")[-2], n) for p, n, _d in nets))
    skel = drift["drift"]["openspec/specs/decompmoe-skeleton/spec.md"]
    inside = [iv for iv in skel if iv[0] <= 122 <= iv[1]]
    check("B-AC27-baseline", "skeleton:122 is inside no drift interval => unchanged-since-pin",
          inside == [], "intervals=%s" % skel)
    touched_in_range = git("log", "--oneline", "7bf77af..%s" % PIN,
                           "--", "openspec/specs/").strip().split("\n")
    check("B-AC27-single-cause", "exactly one commit in the range touches openspec/specs/",
          len([t for t in touched_in_range if t]) == 1,
          touched_in_range[0] if touched_in_range else "")

    # ---------------------------------------------------------- AC-29
    report_lines = io.open(REPORT_MD, encoding="utf-8").read().split("\n")
    honest = [i + 1 for i, l in enumerate(report_lines) if "诚实边界" in l]
    check("B-AC29-line", "「诚实边界」 is at report L1336 and not L1367",
          1336 in honest and 1367 not in honest, "hits=%s" % honest[:4])
    check("B-AC29-outofrepo", "the report is outside the repo, so it has no pin baseline",
          not os.path.exists(os.path.join(REPO, "_final_report_full.md")))
    check("B-AC29-deadkey", "rv:main18:math does not exist in the 197-key json",
          "rv:main18:math" not in verdicts, "key count=%d" % len(verdicts))
    check("B-AC29-livekey", "rv:main48:math (the key we kept) does exist",
          "rv:main48:math" in verdicts)

    # ---------------------------------------------------------- AC-30
    line90 = at(PIN, "src/decompmoe/extraction.py", 90)
    check("B-AC30-anchor", "pin extraction.py:90 is `class CentroidDriver`",
          line90 is not None and line90.startswith("class CentroidDriver"), repr(line90))
    sched = io.open(os.path.join(REPO, ".audit", "wayfinder-opsx-code-review", "_work", "classified.json"),
                    encoding="utf-8").read()
    pin_sched = "\n".join(show(PIN, "src/decompmoe/schedule.py"))
    check("B-AC30-wrongfile", "schedule.py at pin defines no CentroidDriver class",
          "class CentroidDriver" not in pin_sched,
          "mentions=%d" % pin_sched.count("CentroidDriver"))
    ext = io.open(os.path.join(REPO, "src", "decompmoe", "extraction.py"), encoding="utf-8").read()
    check("B-AC30-fixed", "HEAD made mask required and documents the old default",
          "requires an explicit per-expert" in ext
          and "mask: Tensor | None = None" in ext)
    check("B-AC30-key", "grv:gap0:math exists and rv:gap0:math does not",
          "grv:gap0:math" in verdicts and "rv:gap0:math" not in verdicts)
    check("B-AC30-commit", "a97e3a7 is a descendant of pin",
          subprocess.run(["git", "merge-base", "--is-ancestor", "a97e3a7", PIN],
                         cwd=REPO, capture_output=True).returncode != 0)

    # ---------------------------------------------------------- AC-50
    l383 = at(PIN, "openspec/specs/wayfinder/spec.md", 383)
    l382 = at(PIN, "openspec/specs/wayfinder/spec.md", 382)
    l379 = at(PIN, "openspec/specs/wayfinder/spec.md", 379)
    l381 = at(PIN, "openspec/specs/wayfinder/spec.md", 381)
    check("B-AC50-anchor", "pin L383 IS the Req 17 body (so the original pointer was right)",
          l383 is not None and "FLOPs" in l383 and l382 is not None and l382.strip() == "",
          "L383=%r" % (l383 or "")[:60])
    check("B-AC50-anchor-ctx", "L379 is the req-17 anchor and L381 the Requirement heading",
          l379 is not None and 'id="req-17"' in l379
          and l381 is not None and l381.startswith("### Requirement:"))
    macs = 32896 + 128 + 128 + 16
    flops = macs * 2
    pct_new = flops / 33554432 * 100
    pct_old = 66048 / 33554432 * 100
    pct_436 = (flops / 66048 - 1) * 100
    check("C-AC50-arith", "33168 MACs / 66336 FLOPs / 0.197697% / 0.196838% / 0.4361%",
          macs == 33168 and flops == 66336
          and abs(pct_new - 0.197697) < 1e-6 and abs(pct_old - 0.196838) < 1e-6
          and abs(pct_436 - 0.436) < 1e-3,
          "macs=%d flops=%d new=%.6f old=%.6f 436=%.6f" % (macs, flops, pct_new, pct_old, pct_436))
    check("G-AC50-keys", "rv:main42:{source,math,impact} all exist",
          all("rv:main42:%s" % k in verdicts for k in ("source", "math", "impact")))

    # ---------------------------------------------------------- AC-51
    l69 = at(PIN, "tests/test_config.py", 69)
    check("B-AC51-anchor", "pin test_config.py:69 is the bare == assertion (1-based)",
          l69 is not None and "router_per_layer == 32_896" in l69
          and "pytest.approx" not in l69, repr(l69))
    l70 = at(PIN, "tests/test_config.py", 70)
    check("B-AC51-base", "the same assertion is NOT at L70 (so the base is 1-based)",
          l70 is None or "router_per_layer == 32_896" not in l70, repr(l70))
    hits = git("grep", "-n", "0.0476", PIN, "--", "src/", "tests/").strip().split("\n")
    src_hits = [h for h in hits if h and "src/" in h.split(":")[1] if h.count(":") >= 2]
    check("B-AC51-grep", "0.0476 appears only in a tests docstring, never in src/",
          len(hits) == 1 and "tests/" in hits[0] and not src_hits,
          "hits=%s" % (hits if hits else ["<none>"]))
    check("G-AC51-key", "grv:gap25:math exists and rv:grv:gap25:math does not",
          "grv:gap25:math" in verdicts and "rv:grv:gap25:math" not in verdicts)

    # ---------------------------------------------------------- G: no dead keys
    for bid, want_item in items.items():
        dead = [k for k in want_item["origin_ids"] if k not in verdicts]
        check("G-%s-keys" % bid, "%s origin_ids all resolve" % bid, not dead,
              "dead=%s" % dead)

    # ---------------------------------------------------------- F: structure
    a_base = len(re.findall(r"\*\*基线\*\*", list_a))
    b_base = len(re.findall(r"\*\*基线\*\*", list_b))
    check("F-counts", "基线 field counts are 108 (A) and 15 (B)",
          a_base == 108 and b_base == 15, "A=%d B=%d" % (a_base, b_base))
    errata = re.findall(r"^## Errata", list_a, re.M)
    check("F-errata", "all four Errata sections survive (A-1, A-2, A-4, A-6)",
          len(errata) == 4, "sections=%d" % len(errata))
    fix_lines = re.findall(r"\*\*修复 commit\*\*", list_a)
    check("F-fixing", "exactly 3 修复 commit lines (AC-06 / AC-26 / AC-30)",
          len(fix_lines) == 3, "count=%d" % len(fix_lines))
    for bid, want_item in items.items():
        idx = list_a.find("### %s " % bid)
        block = list_a[idx:idx + 4000] if idx >= 0 else ""
        # verdicts render as `**裁决**：VALUE` (no backticks); baseline as
        # `**基线**：`VALUE``; location as `:LINE` inside the 位置 line.
        expectations = {
            "verdict_class": "**裁决**：%s" % want_item["verdict_class"],
            "baseline_status": "**基线**：`%s`" % want_item["baseline_status"],
            "location_line": ":%d" % want_item["location_line"],
        }
        for field, needle in expectations.items():
            check("F-%s-%s" % (bid, field), "%s renders %s" % (bid, field),
                  needle in block, "expected %r" % needle)
        if want_item.get("fixing_commit"):
            check("F-%s-fixing" % bid, "%s renders its 修复 commit" % bid,
                  "**修复 commit**：`%s`" % want_item["fixing_commit"] in block)

    # ---------------------------------------------------------- report
    passed = sum(1 for _c, _d, ok, _x in results if ok)
    failed = len(results) - passed
    lines = ["# verify_a6_errata report", "",
             "Frozen head: `%s`" % FROZEN, "Pin: `%s`" % PIN, "",
             "**%d checks, %d passed, %d failed**" % (len(results), passed, failed), "",
             "| check | result | detail |", "|---|---|---|"]
    for cid, desc, ok, detail in results:
        lines.append("| `%s` | %s | %s |" % (
            cid, "PASS" if ok else "**FAIL**",
            (detail or "").replace("|", "\\|")[:160]))
    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")

    print("checks=%d passed=%d failed=%d" % (len(results), passed, failed))
    for cid, desc, ok, detail in results:
        if not ok:
            print("  FAIL %-22s %s | %s" % (cid, desc[:60], detail[:100]))
    print("report: %s" % REPORT)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
