#!/usr/bin/env python3
"""Pointer census for the A-4 line-pointer family.

Answers the question the A-4 audit list cannot: what is ACTUALLY referenced, and
how many inbound references does each distinct target have? Block-level anchors
may only be minted for targets with >= 2 inbound references (plan section 3.2).

Scope (plan section 3.3, C1): `openspec/specs/**`, `src/**`, `tests/**`.
`openspec/changes/**` is deliberately excluded — governance's "Archive copies are
not retro-edited" principle, plus archive copies are historical record.

Self-check (plan section 0.2): the classifier is validated against a KNOWN
POSITIVE (`wayfinder L249`, expected 10 hits in tests/test_safeguards.py) before
the full run, and the denominator is cross-checked two ways.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

# evidence/ -> <change>/ -> changes/ -> openspec/ -> repo root
REPO = Path(__file__).resolve().parents[4]
SCAN_ROOTS = ("openspec/specs", "src", "tests")
SCAN_SUFFIX = (".md", ".py")

# --- pointer detection -------------------------------------------------------
# Three shapes, per plan section 1.1.
#
# NOTE on precision (supersedes the plan's loose counting regex): the plan's
# §1.1 pattern `\bL\d{1,4}\b` is an UPPER BOUND, not a pointer detector. It also
# matches technical labels such as `d_c[L2-step2]` / `[L4-postmean]`, where "L2"
# means *layer 2*, not a line reference. Those are legitimate vocabulary and must
# NOT be migrated. A bare `L<digits>` is therefore only a pointer when it sits
# in a reference context; `L\d+` immediately followed by `-` is always a label.
# Reference forms actually used in this repo, matched with TIGHT ADJACENCY.
#
# Two failure modes had to be excluded (both observed in this repo):
#   (a) FALSE NEGATIVE of the loose plan regex's inverse: `d_c[L2-step2]`,
#       `L4-postmean` — "L2" means *layer 2*, not line 2. RE_LABEL_L strips these.
#   (b) FALSE POSITIVE of loose keyword matching: "at 16 experts", "per 4 tests".
#       So a bare L-number is a pointer ONLY when a capability / requirement
#       token sits immediately beside it. `at`, `see`, `per` alone are NOT triggers.
RE_FILE_L = re.compile(r"([A-Za-z_][\w/]*\.py):(\d{1,4})")
RE_LABEL_L = re.compile(r"\bL\d{1,4}-")  # `L2-step2`, `L4-postmean`

_POINTER_FORMS = (
    # <capability> [spec] L123   /   <capability> L123-L130
    re.compile(
        r"\b(wayfinder|skeleton|decompmoe-skeleton|spec)\s+(?:spec\s+)?L?(\d{1,4})"
        r"(?:\s*[-–]\s*L?(\d{1,4}))?",
        re.IGNORECASE,
    ),
    # req-11 L245   /   Req 20 L394
    re.compile(r"\b(?:req-(\d+)|Req\.?\s*(\d+))\s+L(\d{1,4})", re.IGNORECASE),
    # L123-L130 spec   /   L123 wayfinder
    re.compile(
        r"\bL(\d{1,4})(?:\s*[-–]\s*L?(\d{1,4}))?\s+(spec|wayfinder|skeleton)\b",
        re.IGNORECASE,
    ),
    # "line 495" — only counts when the line also names a spec target
    re.compile(r"\blines?\s+(\d{1,4})\b", re.IGNORECASE),
)

CAPABILITY_MENTION = re.compile(
    r"\b(wayfinder|skeleton|decompmoe-skeleton|governance|spec)\b", re.IGNORECASE
)
REQ_MENTION = re.compile(r"\b(?:req-\d+|Req\.?\s*\d+)\b")
# Used only to recover the Requirement hint, not to detect the pointer.
RE_REQ_L = re.compile(r"req-(\d+)\s+L\d{1,4}")
RE_REQWORD_L = re.compile(r"[Rr]eq\.?\s*(\d+)\s+L\d{1,4}")

# A line qualifies as a pointer only if it is a *reference*, not prose that
# happens to contain an L-number. Historical citations are the documented
# exemption (plan 3.3 C1): they must carry an explicit historical marker.
#
# Marker set tightened after measuring what the loose set actually did
# (`evidence/measure_marker_tightening.py`): `ex-` and `->` fire on ordinary
# vocabulary — `-> Tensor` return annotations, math arrows like
# `c in [1, 2] -> ("skip", 1.0, False)`, and the substring `ex-` inside ordinary
# words. Because the exemption is applied per LINE, one such false trigger
# silently exempted lines that also carried a live pointer, which is how a
# "0 actionable" reading could be reached while pointers remained. The
# exemption must be nameable (task 9.2), so the two loose markers are replaced
# by a prior-commit-id test, which is what an explicit historical citation
# actually looks like in this repo.
HISTORICAL_MARKERS = (
    "pre-this-change",
    "histor",
    "原",
    "was ",
    "before",
)
# A 7-40 hex token is a git object id: `at commit d3689a1`, `amended by bec147d`.
HISTORICAL_COMMIT_RE = re.compile(r"\b[0-9a-f]{7,40}\b")

# Which spec a bare `wayfinder` / `skeleton` mention refers to.
CAPABILITY_HINTS = (
    ("wayfinder", "wayfinder"),
    ("skeleton", "decompmoe-skeleton"),
    ("decompmoe-skeleton", "decompmoe-skeleton"),
    ("governance", "governance"),
)


def has_historical_marker(text: str) -> bool:
    low = text.lower()
    if any(m.lower() in low for m in HISTORICAL_MARKERS):
        return True
    return bool(HISTORICAL_COMMIT_RE.search(text))


def iter_files():
    for root in SCAN_ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in SCAN_SUFFIX:
                yield path


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def classify(line: str):
    """Return (target_capability, target_req_hint, referenced_lines, kind)."""
    file_l = RE_FILE_L.search(line)
    if file_l:
        raw_path = file_l.group(1)
        # The regex char class admits '/', so a line may already carry a full
        # path. Only prefix when the capture is a bare module name.
        if "/" in raw_path:
            code_path = raw_path
        else:
            code_path = "src/decompmoe/" + raw_path
        nums = [int(n) for n in re.findall(r":(\d{1,4})", file_l.group(0))]
        return (code_path, None, nums, "code-line")

    nums = []
    # Strip label vocabulary first: `L2-step2` is a term, never a pointer.
    stripped = RE_LABEL_L.sub(" ", line)
    for m in _POINTER_FORMS[:3]:
        for hit in m.finditer(stripped):
            for g in hit.groups():
                if g and g.isdigit():
                    nums.append(int(g))
    # `line 495` counts even without a capability token on the same line
    # (e.g. a bare `— line 495` trailing comment in schedule.py). Bias is
    # deliberately toward RECALL: over-inclusion costs a few lines of manual
    # triage, under-inclusion is exactly how this family came back five times
    # (plan 2.4). Weak hits are tagged so triage can rank them.
    weak = False
    for m in _POINTER_FORMS[3].finditer(stripped):
        nums.append(int(m.group(1)))
        if not (CAPABILITY_MENTION.search(stripped) or REQ_MENTION.search(stripped)):
            weak = True
    if not nums:
        return None

    # Requirement hint: the Req/req token nearest the pointer, else whatever
    # Requirement name the line mentions.
    hint = None
    req_l = RE_REQ_L.search(line)
    reqw = RE_REQWORD_L.search(line)
    if req_l:
        hint = "req-%s" % req_l.group(1)
    elif reqw:
        hint = "req-%s" % reqw.group(1)
    else:
        any_req = re.search(r"\breq-(\d+)\b", line)
        if any_req:
            hint = "req-%s" % any_req.group(1)

    low = line.lower()
    cap = None
    for hint_word, c in CAPABILITY_HINTS:
        if hint_word in low:
            cap = c
            break
    if cap is None:
        cap = "wayfinder"
    return (cap, hint, nums, "spec-line-weak" if weak else "spec-line")


# --- resolve a spec line number to the Requirement that owns it --------------
def build_anchor_maps() -> dict:
    """{capability: {line_no: req_id}} from the `<a id="req-N"></a>` anchors."""
    maps = {}
    for cap in ("wayfinder", "decompmoe-skeleton", "governance"):
        p = REPO / "openspec" / "specs" / cap / "spec.md"
        owner = {}
        current = None
        if not p.exists():
            maps[cap] = owner
            continue
        for lineno, line in enumerate(
            p.read_text(encoding="utf-8").splitlines(), 1
        ):
            m = re.match(r'<a id="([\w-]+)"></a>', line.strip())
            if m:
                current = m.group(1)
            if current:
                owner[lineno] = current
        maps[cap] = owner
    return maps


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-empty", action="store_true",
                    help="accept a fully swept tree (zero pointers) as a pass")
    args_allow_empty = ap.parse_args().allow_empty

    out_path = Path(__file__).resolve().parent / "pointer_census.json"
    anchors = build_anchor_maps()
    raw = []
    per_file = Counter()
    exempt = 0

    for path in iter_files():
        r = rel(path)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if "http" in line:
                continue
            target = classify(line)
            if target is None:
                continue
            cap, hint, nums, kind = target
            per_file[r] += 1

            # Resolve the referenced line to its owning Requirement so the
            # census keys on "which Requirement is being pointed INTO" rather
            # than on a bare capability bucket.
            owner = hint  # explicit `req-N` / `Req N` is authoritative
            if owner is None and kind.startswith("spec-line") and nums:
                amap = anchors.get(cap, {})
                for n in nums:
                    if n in amap:
                        owner = amap[n]
                        break

            rec = {
                "file": r,
                "line": lineno,
                "target_capability": cap,
                "target_kind": kind,
                "target_requirement": owner,
                "referenced_lines": nums,
                "exempt": None,
                "text": line.strip()[:240],
            }
            if has_historical_marker(line):
                exempt += 1
                rec["exempt"] = "historical-marker"
                rec["marker"] = next(
                    (
                        m
                        for m in (*HISTORICAL_MARKERS, "prior-commit-id")
                        if m == "prior-commit-id"
                        and HISTORICAL_COMMIT_RE.search(line)
                        or m != "prior-commit-id"
                        and m.lower() in line.lower()
                    ),
                    "?",
                )
            raw.append(rec)

    actionable = [r for r in raw if r["exempt"] is None]
    inbounds = Counter(
        (r["target_capability"], r["target_requirement"]) for r in actionable
    )
    by_target = defaultdict(list)
    for r in actionable:
        by_target[(r["target_capability"], r["target_requirement"])].append(
            "%s:%d" % (r["file"], r["line"])
        )

    census = {
        "scan_roots": list(SCAN_ROOTS),
        "scan_excludes": ["openspec/changes/**"],
        "historical_markers": list(HISTORICAL_MARKERS),
        "totals": {
            "pointer_lines": len(raw),
            "actionable": len(actionable),
            "historical_exempt": exempt,
            "distinct_targets": len(inbounds),
            "files_scanned_with_pointers": len(per_file),
        },
        "per_file": dict(sorted(per_file.items(), key=lambda kv: -kv[1])),
        "targets": {
            "%s|%s" % (k[0], k[1] or "unresolved"): {
                "inbound": v,
                "sites": sorted(by_target[k]),
            }
            for k, v in sorted(
                inbounds.items(), key=lambda kv: (-kv[1], str(kv[0]))
            )
        },
        "sites": actionable,
    }

    out_path.write_text(
        json.dumps(census, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- self-check (plan 0.2) ------------------------------------------------
    # The known positive is read from the PINNED pre-change blob, not from the
    # live tree. Against the live tree this control expires the moment the sweep
    # lands — `wayfinder L249` legitimately becomes 0 — which would make the
    # control indistinguishable from a broken classifier. Pinning keeps it a
    # permanent validity check on the classifier itself.
    pos = [r for r in raw if "wayfinder L249" in r["text"]]
    pinned = 0
    pinned_file = ""
    baseline = Path(__file__).resolve().parent / "baseline_head.txt"
    if baseline.exists():
        rev = baseline.read_text(encoding="utf-8").strip()
        pinned_file = "tests/test_safeguards.py"
        try:
            blob = subprocess.run(
                ["git", "-C", str(REPO), "show", f"{rev}:{pinned_file}"],
                capture_output=True, text=True, encoding="utf-8", check=True,
            ).stdout
            pinned = sum(1 for l in blob.splitlines() if "wayfinder L249" in l)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise SystemExit(
                "SELF-CHECK FAILED: cannot read the pinned positive from "
                f"{rev}:{pinned_file} ({exc}). The classifier is unvalidated; "
                "do NOT trust the census below."
            )
    if pinned != 10:
        raise SystemExit(
            "SELF-CHECK FAILED: pinned positive expected 10 'wayfinder L249' "
            "sites, got %d. The classifier is broken; do NOT trust the census "
            "below." % pinned
        )
    if pos and pinned == 0:
        raise SystemExit("SELF-CHECK FAILED: 'wayfinder L249' found in the live tree")
    if not raw and not args_allow_empty:
        raise SystemExit(
            "SELF-CHECK FAILED: zero pointers detected overall. Either the tree "
            "is clean (expected after the sweep) or the classifier is broken; "
            "the pinned positive above is what distinguishes the two."
        )
    unresolved = sum(1 for r in actionable if r["target_requirement"] is None)
    print("self-check OK: pinned positive 'wayfinder L249' =", pinned,
          "| live-tree occurrences =", len(pos))
    print("---")
    print("pointer lines total :", len(raw))
    print("actionable          :", len(actionable))
    print("historical exempt   :", exempt)
    print("distinct targets    :", len(inbounds))
    print("files               :", len(per_file))
    print("unresolved reqs     :", unresolved)
    print("---")
    print("pointer lines total :", len(raw))
    print("actionable          :", len(actionable))
    print("historical exempt   :", exempt)
    print("distinct targets    :", len(inbounds))
    print("files               :", len(per_file))
    print("unresolved reqs     :", unresolved)
    print("--- inbound >= 2 (block-anchor candidates) ---")
    for k, v in sorted(inbounds.items(), key=lambda kv: -kv[1]):
        if v >= 2:
            print("  %-38s inbound=%d" % ("%s|%s" % (k[0], k[1] or "?"), v))
    print("--- inbound == 1 (no anchor; use Req + label) ---")
    for k, v in sorted(inbounds.items(), key=lambda kv: str(kv[0])):
        if v == 1:
            print("  %-38s inbound=1" % ("%s|%s" % (k[0], k[1] or "?")))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
