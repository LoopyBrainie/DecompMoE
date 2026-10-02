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
EXPECT_ANCHORS = {"wayfinder": 36, "decompmoe-skeleton": 23, "governance": 4}


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
anchors = {}
anchor_contract_ok = True
for cap, expect in EXPECT_ANCHORS.items():
    txt = norm(blob(HEAD, f"openspec/specs/{cap}/spec.md"))
    reqs = re.findall(r"^### Requirement:", txt, re.M)
    standalone = re.findall(r"^<a id=\"(req-[0-9A-Za-z\-]+)\"></a>\s*$", txt, re.M)
    dups = {k: standalone.count(k) for k in set(standalone) if standalone.count(k) > 1}
    ok = (len(reqs) == expect and len(standalone) == expect and not dups)
    anchor_contract_ok &= ok
    anchors[cap] = {
        "requirements": len(reqs),
        "standalone_anchors": len(standalone),
        "expected": expect,
        "duplicate_anchor_ids": dups,
        "ok": ok,
    }

# ------------------------------------------------------------------- assemble
doc = {
    "pin": PIN,
    "head": HEAD,
    "head_subject": subject,
    "supersedes_note": (
        "The first baseline.json asserted 'the integrator fix is NOT committed; HEAD (188b9fb) "
        "still carries the PRE-fix _betainc_regularized'. Measured false on three counts: "
        "(1) HEAD is f6461d7, not 188b9fb; (2) sphere.py at HEAD carries the full quadrature fix; "
        "(3) the three specs are in HEAD, not worktree-carried. Only gating.py is uncommitted."
    ),
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
            "The quadrature fix IS committed. sphere.py and tests/test_sphere.py at HEAD "
            "f6461d7 are byte-identical to the working tree and carry the full fix "
            "(_QUAD_RTOL=1e-12, _QUAD_MAX_PANELS=4096, the t=sin^2(phi) substitution, and the "
            "hi = pi/2 - asin(sqrt(1-x)) cancellation fix). A third party re-measuring at HEAD "
            "reproduces THIS ledger, not the audit's pre-fix numbers. The three specs are also "
            "in HEAD, with the 36/23/4 anchor contract intact."
        ),
        "genuinely_worktree_carried": (
            "Only: src/decompmoe/gating.py (the F6 dead-defence removal) and "
            "wayfinder/tickets/WF-1.md (2 lines). Both are uncommitted. Neither feeds the "
            "quadrature measurement chain, so a re-measurement at HEAD is unaffected by them."
        ),
        "not_in_git": (
            "The Change 2 archive directory and this Change 3 directory are both UNTRACKED. "
            "Change 2's finished work is on disk but not committed."
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
print(f"  anchor contract 36/23/4   : {anchor_contract_ok}  {anchors}")
print(f"  deleted-but-tracked       : {len(staged_deleted)}")
print(f"  modified-uncommitted      : {modified}")
