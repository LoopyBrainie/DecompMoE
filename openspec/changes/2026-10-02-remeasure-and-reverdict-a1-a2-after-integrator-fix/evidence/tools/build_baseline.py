"""Change 3 / task 0.1 -- regenerate evidence/baseline.json from measurement.

Supersedes the first baseline, whose `asymmetry` block asserted the quadrature
fix was uncommitted. Measured false: `sphere.py` at HEAD carries the full fix
(_QUAD_RTOL=1e-12, _QUAD_MAX_PANELS=4096, the sin^2 substitution and the
hi-cancellation fix). The genuinely worktree-carried set is much narrower.

The other lesson folded in here: a naive raw-sha256 HEAD-vs-worktree compare
reports SIX false positives, because the worktree carries CRLF where the HEAD
blob carries LF. `git hash-object` and `git diff` normalise line endings, raw
sha256 does not -- so a byte-level verdict must be labelled as byte-level, and
the ledger may only cite a content-level verdict.

Every number below is computed, not transcribed. Run twice: the output is
byte-identical (task 0.1 verification).
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
OUT = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence/baseline.json"
PIN = "6593a06"

TRACKED = [
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/specs/governance/spec.md",
    "src/decompmoe/sphere.py",
    "src/decompmoe/gating.py",
    "src/decompmoe/loss.py",
    "src/decompmoe/schedule.py",
    "src/decompmoe/metrics.py",
    "src/decompmoe/config.py",
    "src/decompmoe/extraction.py",
    "src/decompmoe/safeguards.py",
    "src/decompmoe/distance.py",
    "src/decompmoe/beta.py",
    # --- A-3 bucket evidence (added for task 3.1) ---
    # Without these, "the file was not touched" has no proof for AC-45
    # (contracts.py) and AC-78 (__init__.py), and the four test files that
    # A-3 findings cite as their evidence location are unmeasured.
    "src/decompmoe/__init__.py",
    "src/decompmoe/contracts.py",
    "tests/test_safeguards.py",
    "tests/test_extraction_phase.py",
    "tests/test_schedule.py",
    "tests/test_contracts.py",
    "tests/test_sphere.py",
    "tests/test_gating.py",
    "tests/test_loss.py",
    "tests/test_config.py",
    "tests/test_extraction.py",
    "tests/test_metrics.py",
    "tests/test_beta.py",
]

# Anchor contract recomputed at Change 2 completion (36 / 23 / 4, 100% coverage).
# Recorded at the commit named in `EXPECT_ANCHORS_AS_OF`. The absolute numbers
# move whenever a Requirement is legitimately added; only coverage is an
# invariant. wayfinder went 36 -> 37 at 1afac58 ("narrow Req 23 to Phase 1-4;
# make territory_collapse and req-15 Layer 2 explicit deferrals"), which added
# one Requirement with its anchor. That is a correct change, so the gate is red
# for bookkeeping reasons only -- `coverage_ok` is the structural verdict.
EXPECT_ANCHORS = {"wayfinder": 37, "decompmoe-skeleton": 23, "governance": 4}
EXPECT_ANCHORS_AS_OF = "1afac58 (wayfinder 37), pre-1afac58 for the other two"


def git(*a, text=False):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=text, check=False)


def blob(rev, path):
    p = git("cat-file", "blob", f"{rev}:{path}")
    return None if p.returncode != 0 else p.stdout


def norm(b):
    return b.replace(b"\r\n", b"\n").decode("utf-8", "replace")


HEAD = git("rev-parse", "HEAD", text=True).stdout.strip()
subject = git("log", "-1", "--format=%s", HEAD, text=True).stdout.strip()

# ---------------------------------------------------------------- pin blobs
pin_blobs = {}
missing_pin = []
for p in TRACKED:
    b = blob(PIN, p)
    if b is None:
        missing_pin.append(p)
        continue
    pin_blobs[p] = {
        "sha256": hashlib.sha256(b).hexdigest(),
        "bytes": len(b),
        "content_sha256_lf_normalised": hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(),
    }

# ------------------------------------------------- HEAD vs worktree, 3 methods
files = {}
byte_only_diff = []
content_diff = []
for p in TRACKED:
    b, w = blob(HEAD, p), (ROOT / p).read_bytes()
    raw_same = b == w
    content_same = b.replace(b"\r\n", b"\n") == w.replace(b"\r\n", b"\n")
    g1 = git("rev-parse", f"{HEAD}:{p}", text=True)
    g2 = git("hash-object", p, text=True)
    diff_clean = git("diff", "--quiet", HEAD, "--", p).returncode == 0
    if raw_same:
        verdict = "IDENTICAL"
    elif content_same:
        verdict = "CRLF_ONLY"
        byte_only_diff.append(p)
    else:
        verdict = "CONTENT_DIFF"
        content_diff.append(p)
    files[p] = {
        "verdict": verdict,
        "head_bytes": len(b),
        "worktree_bytes": len(w),
        "head_sha256": hashlib.sha256(b).hexdigest(),
        "worktree_sha256": hashlib.sha256(w).hexdigest(),
        "head_content_sha256_lf": hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(),
        "worktree_content_sha256_lf": hashlib.sha256(w.replace(b"\r\n", b"\n")).hexdigest(),
        "head_crlf_count": b.count(b"\r\n"),
        "worktree_crlf_count": w.count(b"\r\n"),
        "git_blob_sha_head": g1.stdout.strip() if g1.returncode == 0 else None,
        "git_blob_sha_worktree": g2.stdout.strip() if g2.returncode == 0 else None,
        "git_diff_quiet_clean": diff_clean,
    }
    # M2/M3 normalise line endings; they must agree with the content verdict.
    assert diff_clean == content_same, f"method disagreement (M2/M3 vs bytes) on {p}"
    if g1.returncode == 0 and g2.returncode == 0:
        assert (g1.stdout.strip() == g2.stdout.strip()) == content_same, f"M2 disagrees on {p}"

# ------------------------------------------------------------- worktree state
porcelain = git("status", "--porcelain", text=True).stdout.splitlines()
staged_deleted, modified, untracked = [], [], []
for line in porcelain:
    xy, path = line[:2], line[3:]
    if xy == " D":
        staged_deleted.append(path)
    elif xy == " M":
        modified.append(path)
    elif xy == "??":
        untracked.append(path)
    else:
        modified.append(f"{xy} {path}")

# ------------------------------------------- anchor contract, recomputed live
# Structure is: <a id="req-N"></a> / blank / ### Requirement: ... / body.
#
# M (review findings, confirmed): this used to be `len(reqs) == expect and
# len(standalone) == expect and not dups`, i.e. an ABSOLUTE count pinned to a
# constant, plus prose asserting the contract was "intact". Two things then go
# wrong at once: a parallel session legitimately adding a Requirement turns the
# gate red with no structural defect anywhere, and the CRLF/anchor snapshots in
# the design docs drift without anyone noticing which commit they described.
#
# The structural invariant is COVERAGE, and it moves with the spec:
#     every Requirement has exactly one standalone anchor, no anchor twice.
# The absolute count is still checked, but against a value recorded together with
# the commit it was read at, and a mismatch is reported as drift rather than
# silently absorbed.
#
# `quoted` counts anchor tags that appear INSIDE prose. This repo deliberately
# cross-references Requirements by anchor instead of by line number (change
# 2026-09-28-fix-a7-flops-attribution-and-stale-ref, Decision 2), so those tags
# are part of the text, not part of the structure. Counting them is how you get
# two phantom "duplicate" anchors -- req-17 and req-20 -- that do not exist.
anchors = {}
anchor_contract_ok = True
anchor_drift = []
for cap, expect in EXPECT_ANCHORS.items():
    txt = norm(blob(HEAD, f"openspec/specs/{cap}/spec.md"))
    reqs = re.findall(r"^### Requirement:", txt, re.M)
    standalone = re.findall(r"^<a id=\"(req-[0-9A-Za-z\-]+)\"></a>\s*$", txt, re.M)
    quoted = len(re.findall(r"<a id=\"req-[0-9A-Za-z\-]+\"></a>", txt)) - len(standalone)
    dups = {k: standalone.count(k) for k in set(standalone) if standalone.count(k) > 1}
    # structural: coverage and uniqueness
    ok = (len(reqs) == len(standalone)) and not dups
    # absolute: recorded expectation, drift is reported not hidden
    drift = len(reqs) != expect
    if drift:
        anchor_drift.append(f"{cap}: {len(reqs)} requirements, recorded expectation {expect}")
    anchor_contract_ok &= ok
    anchors[cap] = {
        "requirements": len(reqs),
        "standalone_anchors": len(standalone),
        "anchors_quoted_in_prose": quoted,
        "recorded_expectation": expect,
        "absolute_drift": drift,
        "duplicate_anchor_ids": dups,
        "coverage_ok": ok,
        "ok": ok and not drift,
    }

# ------------------------------------------------------------------- assemble
doc = {
    "pin": PIN,
    "head": HEAD,
    "head_subject": subject,
    "supersedes_note": (
        "The first baseline.json asserted 'the integrator fix is NOT committed; HEAD (188b9fb) "
        "still carries the PRE-fix _betainc_regularized'. Measured false on three counts: "
        "(1) HEAD was f6461d7, not 188b9fb, at the time of that measurement; "
        "(2) sphere.py at HEAD carries the full quadrature fix; "
        "(3) the three specs are in HEAD, not worktree-carried. Only gating.py was uncommitted. "
        "This field is a record of a past measurement and does NOT assert anything about the "
        "current HEAD -- read `head` / `head_subject` for that. The prose used to name f6461d7 "
        "as if it were still HEAD, which it stopped being once a parallel session committed "
        "on top of it; a snapshot is not a fact about the present."
    ),
    "anchor_expectation_as_of": EXPECT_ANCHORS_AS_OF,
    "pin_to_head_commits": [
        f"{c[:7]} {s}".strip()
        for c, s in (
            ln.split(" ", 1) for ln in git(
                "log", "--format=%h %s", f"{PIN}..{HEAD}", text=True).stdout.splitlines()
        )
    ],
    "pin_blobs": pin_blobs,
    "pin_blobs_missing": missing_pin,
    "head_vs_worktree": files,
    "verdict_legend": {
        "IDENTICAL": "raw bytes equal",
        "CRLF_ONLY": "bytes differ ONLY by line endings; content identical after LF normalisation",
        "CONTENT_DIFF": "real content difference",
    },
    "line_ending_caveat": (
        "The worktree stores CRLF where HEAD blobs store LF. Raw sha256 therefore reports "
        f"{len(byte_only_diff)} false positives: {byte_only_diff}. Only a CONTENT-level verdict may be "
        "cited in the ledger. git hash-object and git diff normalise line endings; raw hashing does not."
    ),
    "byte_only_diff_files": byte_only_diff,
    "content_diff_files": content_diff,
    "spec_anchor_contract": anchors,
    "spec_anchor_contract_ok": anchor_contract_ok,
    "worktree_state": {
        "deleted_but_tracked_at_head": staged_deleted,
        "modified_but_uncommitted": modified,
        "untracked": untracked,
    },
    "asymmetry": {
        "statement": (
            "The quadrature fix IS committed. sphere.py and tests/test_sphere.py were "
            "byte-identical to the working tree at f6461d7 and carried the full fix "
            "(_QUAD_RTOL=1e-12, _QUAD_MAX_PANELS=4096, the t=sin^2(phi) substitution, and the "
            "hi = pi/2 - asin(sqrt(1-x)) cancellation fix). A third party re-measuring at the "
            "current HEAD reproduces THIS ledger, not the audit's pre-fix numbers. The three "
            "specs are in HEAD and anchor coverage is complete at every capability "
            "(see spec_anchor_contract.*.coverage_ok; the absolute counts move as "
            "Requirements are added, coverage does not)."
        ),
        "snapshot_caveat": (
            "Every number in this file describes the worktree and HEAD AT THE TIME OF THIS RUN. "
            "The CRLF false-positive count in particular is not a property of the repo: it was "
            "measured as 6, then 10, then 9 across successive runs as a parallel session "
            "committed and the line-ending population shifted. Cite it with the `head` field, "
            "never as a standing fact."
        ),
        "genuinely_worktree_carried": (
            "At the last run: src/decompmoe/gating.py (the F6 dead-defence removal) and "
            "wayfinder/tickets/WF-1.md. Neither feeds the quadrature measurement chain, so a "
            "re-measurement at HEAD is unaffected by them."
        ),
        "not_in_git": (
            "Corrected: as of commit b05c727 the Change 2 archive and this change's evidence/ "
            "tools are IN version control. D11 had required that and it was outstanding until "
            "then; this field used to claim both directories were untracked, which was true "
            "when first written and stopped being true without anyone updating it."
        ),
        "danger_if_handled_wrong": (
            "git add -A would silently delete four tracked files that the working tree no longer "
            "has: the proposal.md/tasks.md of 2026-09-26-followup-spec-wording-bugs-after-"
            "precision-disclosure and of fix-review-findings-voronoi-precision-and-lineage."
        ),
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size} B)")
print(f"  pin blobs recorded        : {len(pin_blobs)}  missing: {len(missing_pin)}")
print(f"  IDENTICAL                 : {sum(1 for f in files.values() if f['verdict'] == 'IDENTICAL')}/{len(files)}")
print(f"  CRLF_ONLY (false positive): {len(byte_only_diff)}")
print(f"  CONTENT_DIFF (real)       : {len(content_diff)} -> {content_diff}")
cov_ok = all(a["coverage_ok"] for a in anchors.values())
drift = [f"{c} {a['requirements']} vs recorded {a['recorded_expectation']}"
         for c, a in anchors.items() if a["absolute_drift"]]
print(f"  anchor coverage           : {cov_ok}  "
      f"({'/'.join(str(a['requirements']) for a in anchors.values())} requirements, "
      f"each with exactly one standalone anchor, no duplicates)")
for c, a in anchors.items():
    print(f"    {c:<20} reqs={a['requirements']:>3} standalone={a['standalone_anchors']:>3} "
          f"quoted_in_prose={a['anchors_quoted_in_prose']:>2} "
          f"recorded={a['recorded_expectation']:>3} coverage_ok={a['coverage_ok']} "
          f"drift={a['absolute_drift']}")
if drift:
    print(f"  absolute drift vs the recorded expectation: {drift}")
    print(f"    (recorded as of: {EXPECT_ANCHORS_AS_OF} -- a new Requirement moves this; "
          f"it is not a coverage defect)")
print(f"  anchor contract {cov_ok and not drift}  (coverage={cov_ok}, absolute={not drift})")
print(f"  deleted-but-tracked       : {len(staged_deleted)}")
print(f"  modified-uncommitted      : {modified}")
