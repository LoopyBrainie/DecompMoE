"""The one edit table. It drives BOTH the delta emitter and the live-spec
applier, so "what the delta describes" and "what actually lands" cannot
fork.

Every entry is a BOUNDED TOKEN SUBSTITUTION: an ASCII-only token that must
occur exactly once ON THE NAMED LINE, replaced by an ASCII-only
replacement. Surrounding prose -- including the em dashes and math glyphs
that the console mangles -- is preserved byte for byte. Whole-line
replacement built from a fragment is what silently destroyed four lines in
the previous change; this table makes that impossible.

Line numbers are stable because no entry changes a line's line count, and
the applier asserts that.

Census at 95718cf: 75 actionable sites across 44 distinct lines.
"""

BT = chr(96)          # backtick
DASH = chr(0x2013)    # en dash, as it appears in the sources


def _(s):
    """Interpolate the backtick without letting any literal swallow it."""
    return s.replace("@", BT)


# Stable identities used across the table.
REQ11 = "wayfinder `req-11` (4070 MVP Hyperparameter Set)"
REQ7 = "wayfinder `req-7` (the 12 closed forms)"
REQ10_SK = "`decompmoe-skeleton` `#req-10` (Standard SwiGLU Expert With No Shared Branch)"
REQ10_WF = "`wayfinder` `#req-10` (Territory Seeding Deferred Contract)"
BETA_CFG = "MVPConfig.beta_initial"
BETA_TEST = "tests/test_beta.py::test_beta_param_init_default"

# (file, 1-based line, token, replacement, why)
FIXES = [
    # ================= decompmoe-skeleton ==============================
    ("openspec/specs/decompmoe-skeleton/spec.md", 277,
     "at " + _("@src/decompmoe/safeguards.py:93-94@"),
     "at " + _("@safeguards.py::should_resurrect@") + " (the rate_limit_steps branch)",
     "drifted: :93-94 is now the docstring; the branch is at 99-100"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 277,
     _("flipping @src/decompmoe/safeguards.py:93@"),
     _("flipping @safeguards.py::should_resurrect@"),
     "a SECOND citation of the same locator 1400 chars later; dedup "
     "reported it as the same site, so the first fix left it behind"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 277,
     _("(@safeguards.py:95-96@)"),
     _("(@safeguards.py::should_resurrect@, the consec branch)"),
     "drifted: the consec check is at 101-102"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 277,
     _("(@:100-101@)"),
     _("(@safeguards.py::should_resurrect@, the per-step f_i < threshold branch)"),
     "antecedent colon range, already stale"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 334,
     _("@wayfinder/spec.md@ L83, req-6:"),
     _("@wayfinder@ @#req-6@ (Req 6 C Extraction Differentiability And "
       "Centroid Lifecycle):"),
     "path form the old regex could not match"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 334,
     "the phase table at L617, req-27 records",
     "the phase table under " + _("@wayfinder@ @#req-27@ (Req 27 "
     "CentroidDriver Dual-Channel Architecture Contract)") + " records",
     "bare line pointer to the phase table"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 442,
     "(see " + _("@src/decompmoe/safeguards.py:30-31@)"),
     "(see " + _("@safeguards.py::DEAD_EXPERT_CONSEC_STEPS@ and "
       "@safeguards.py::RESURRECTION_RATE_LIMIT_STEPS@)"),
     "the sentence already names both constants"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 490,
     "canonical export per " + _("@src/decompmoe/beta.py:50@"),
     "canonical export per " + _("@beta.py::MAX_GRAD_PER_GAMMA_PHASE4@"),
     "the symbol is named in the very next code span"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 639,
     ", " + _("@openspec/specs/decompmoe-skeleton/spec.md@ L500-518)"),
     ")",
     "the Requirement is already named as #req-22 one clause earlier"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 642,
     "- L515 explicitly mirrors",
     "- The Req 22 closed-form row explicitly mirrors",
     "bare line pointer with no reference token"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 642,
     _("@wayfinder/spec.md@ L413"),
     _("@wayfinder@ @#req-20-mci@"),
     "block anchor minted by the previous change"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 644,
     _("@ spec.md L413)"),
     " " + _("@#req-20-mci@)"),
     "path form the old regex could not match"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 645,
     _("@A8-2.md@ L70 + L74"),
     _("@wayfinder/tickets/A8-2.md@ supersede annotations"),
     "names the annotations, not their coordinates"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 645,
     "Req-22 mirror of the L413 closed-form",
     "Req-22 mirror of the MCI closed-form",
     "bare line pointer inside a sentence that already says MCI"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 651,
     "**WHEN** " + _("@openspec/specs/decompmoe-skeleton/spec.md@ Req 22 (L500-518) is read"),
     "**WHEN** " + _("@decompmoe-skeleton@ @#req-22@ is read"),
     "resolve to the anchor rather than a range"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 652,
     "the text at L515 verbatim", "the Req 22 text verbatim",
     "bare line pointer"),
    ("openspec/specs/decompmoe-skeleton/spec.md", 652,
     "wayfinder spec.md L413 verbatim",
     "wayfinder " + _("@#req-20-mci@") + " verbatim",
     "path form the old regex could not match"),

    # ================= governance ======================================
    ("openspec/specs/governance/spec.md", 76,
     "Ticket A8-2 L70 + L74 annotations follow",
     "Ticket A8-2 supersede annotations follow",
     "a Scenario HEADING. A MODIFIED block may not rename a Scenario, but "
     "the live spec is swept by the same table BEFORE the delta is emitted, "
     "so the validator -- which compares the delta against the current "
     "spec -- sees matching titles and the special REMOVE+ADD channel is "
     "not needed."),
    ("openspec/specs/governance/spec.md", 78,
     _("@wayfinder/tickets/A8-2.md@ L70 + L74"),
     _("@wayfinder/tickets/A8-2.md@ supersede annotations"),
     "the Scenario names the annotations, not their coordinates"),
    ("openspec/specs/governance/spec.md", 78,
     "spec req-20 L413",
     "spec req-20 <Requirement title> (#req-20)",
     "the canonical form this Scenario mandates; the L413 variant is the "
     "legacy one the spec forbids in NEW annotations"),
    ("openspec/specs/governance/spec.md", 81,
     _("@.audit/spec-math-audit.md@ L524 +"),
     _("@.audit/spec-math-audit.md@ verify-14 entry +"),
     "identifies the entry instead of the line"),
    ("openspec/specs/governance/spec.md", 81,
     "(per " + _("@.audit/README.md@ L3)"),
     "(per " + _("@.audit/README.md@)"),
     ".audit/ is gitignored, so a line pointer there is unresolvable anyway"),
    ("openspec/specs/governance/spec.md", 82,
     "existing " + _("@req-gov-1@ anchor at L7 unchanged"),
     "existing " + _("@req-gov-1@ anchor unchanged"),
     "the anchor id is the identity; the line is not"),
    ("openspec/specs/governance/spec.md", 141,
     "reads ticket A6b-1 L100",
     "reads ticket " + _("@wayfinder/tickets/A6b-1.md@"),
     "bare ticket id plus a line locator"),
    ("openspec/specs/governance/spec.md", 174,
     "cycle-7 audit-verification L581 meta",
     "cycle-7 audit-verification meta",
     "the source field cites CLAUDE.md §8, which is the real source"),

    # ================= wayfinder =======================================
    ("openspec/specs/wayfinder/spec.md", 377,
     _("@wayfinder/tickets/A6b-2.md@ L52 and L89" + DASH + "L92 "
       "as the per-expert orthogonality baseline"),
     _("@wayfinder/tickets/A6b-2.md@ (Layer-2 advisory-signal definition) "
       "as the per-expert orthogonality baseline"),
     "the ticket is the address; its internal lines are not stable"),

    # ================= LOOPS.md (audit log, rewritten not exempted) ====
    ("LOOPS.md", 184, "spec L185", REQ11, "audit-log citation of what it found"),
    # Corrective: the two entries below already landed and produced
    # "MVPConfig.beta_initial docstring docstring", because the original
    # token was followed by its own " docstring".
    ("LOOPS.md", 194, "docstring docstring", "docstring",
     "corrective: de-duplicate the word my own replacement introduced"),
    ("LOOPS.md", 196, "docstring docstring", "docstring",
     "corrective: de-duplicate the word my own replacement introduced"),
    ("LOOPS.md", 184, "A5-3 L62",
     _("@wayfinder/tickets/A5-3.md@ (theta_Voronoi annotation)"),
     "bare ticket id plus a line locator", 2),
    ("LOOPS.md", 191, "ticket A5-3 L62",
     "ticket " + _("@wayfinder/tickets/A5-3.md@"),
     "same"),
    ("LOOPS.md", 191, "A4-1 L58",
     _("@wayfinder/tickets/A4-1.md@"), "same"),
    ("LOOPS.md", 191, "MVPConfig L54", BETA_CFG, "symbol plus a line locator"),
    ("LOOPS.md", 191, "test_beta.py L38", BETA_TEST, "path plus a line locator"),
    ("LOOPS.md", 192, "spec L184/L185", REQ11, "audit-log citation"),
    ("LOOPS.md", 192, "A5-3 L62",
     _("@wayfinder/tickets/A5-3.md@"), "same"),
    ("LOOPS.md", 192, "A1-1 L97",
     _("@wayfinder/tickets/A1-1.md@"), "same"),
    ("LOOPS.md", 194, "MVPConfig L51", BETA_CFG + " docstring",
     "symbol plus a line locator"),
    ("LOOPS.md", 195, "spec L122", REQ7, "audit-log citation"),
    ("LOOPS.md", 195, "MVPConfig L54", BETA_CFG, "symbol plus a line locator"),
    ("LOOPS.md", 195, "A4-1 L58",
     _("@wayfinder/tickets/A4-1.md@"), "same"),
    ("LOOPS.md", 196, "tests/test_beta.py:37-38", BETA_TEST, "code-line form"),
    ("LOOPS.md", 196, "config.py L54", BETA_CFG, "path plus a line locator"),
    ("LOOPS.md", 196, "test_beta.py L38", BETA_TEST, "path plus a line locator"),
    ("LOOPS.md", 196, "config.py L50-53", BETA_CFG + " docstring",
     "path plus a line range"),
    ("LOOPS.md", 197, "A4-1 L58",
     _("@wayfinder/tickets/A4-1.md@"), "bare ticket id plus a line locator", 2),
    ("LOOPS.md", 197, "A5-3 L62",
     _("@wayfinder/tickets/A5-3.md@"), "same"),
    ("LOOPS.md", 197, "MVPConfig L54", BETA_CFG, "symbol plus a line locator"),
    ("LOOPS.md", 197, "test_beta.py L38", BETA_TEST, "path plus a line locator"),
    ("LOOPS.md", 198, "spec L122/L115", REQ7, "audit-log citation"),
    ("LOOPS.md", 198, "spec L122 在",
     "wayfinder " + _("@req-7@") + " 在", "second mention on the same line"),
    ("LOOPS.md", 198, "spec L115 在",
     "wayfinder " + _("@req-7@") + " 在", "third mention on the same line"),
    ("LOOPS.md", 198, "A4-1 L58",
     _("@wayfinder/tickets/A4-1.md@"), "same"),
    ("LOOPS.md", 199, "spec L115/L122/L126", REQ7, "audit-log citation"),
    ("LOOPS.md", 199, "A4-1 L39/L42/L50/L58/L65-67",
     _("@wayfinder/tickets/A4-1.md@ beta_0 closed-form rows"),
     "path plus a line-list"),
    ("LOOPS.md", 199, "MVPConfig L50-54", BETA_CFG, "symbol plus a line range"),
    ("LOOPS.md", 200, "A5-3 L62",
     _("@wayfinder/tickets/A5-3.md@"), "bare ticket id plus a line locator"),
    ("LOOPS.md", 200, "A4-1 L58",
     _("@wayfinder/tickets/A4-1.md@"), "same"),
    ("LOOPS.md", 200, "MVPConfig L54", BETA_CFG, "symbol plus a line locator"),
    ("LOOPS.md", 200, "test_beta.py L38", BETA_TEST, "path plus a line locator"),
    ("LOOPS.md", 200, "spec L122", REQ7, "audit-log citation"),

    # ================= apply-checklist.md ==============================
    ("apply-checklist.md", 42, "at lines 122 and 133",
     "in the FFN FLOPs term", "weak form: no reference token"),
    ("apply-checklist.md", 42, "at lines 121/132",
     "in the attention FLOPs term", "weak form: no reference token"),
    ("apply-checklist.md", 102, "(lines 139-142)",
     "(the EMA branch of the same helper)", "weak form: no reference token"),
    ("apply-checklist.md", 103, "(line 144-145)",
     "(the Phase 4 branch of that helper)", "weak form: no reference token"),
    ("apply-checklist.md", 112,
     "signature mirrors " + _("@src/decompmoe/safeguards.py:105-133@"),
     "signature mirrors " + _("@safeguards.py::resurrection_perturb_distribution@"),
     "code-line form; the signature is the identifier"),

    # ================= docs template ===================================
    ("docs/templates/post-review-remediation.md", 90, "(lines 160, 171)",
     "(both try/except call sites)", "weak form: no reference token"),

    # ================= tests ===========================================
    ("tests/test_metrics.py", 357, "req-20 coverage at L286-310",
     "req-20 coverage", "req id plus a line range"),
    ("tests/test_safeguards.py", 620,
     "at " + _("@decompmoe-skeleton@ L206:"),
     "in " + REQ10_SK + ":", "capability word plus a line locator"),
    ("tests/test_safeguards.py", 867, "Code L265 uses",
     "Code " + _("@safeguards.py::resurrect_expert@") + " uses",
     "stale: :265 is now the trailing-axis contract comment"),
    ("tests/test_safeguards.py", 892, "Code L259 uses",
     "Code " + _("@safeguards.py::resurrect_expert@") + " uses",
     "stale: :259 is now the IndexError message"),
    ("tests/test_safeguards.py", 942, "Code L72 fallback",
     "The " + _("@consecutive_nan >= 1@") + " branch fallback",
     "names the branch instead of the line"),
    ("tests/test_safeguards.py", 971, "The current code (L71-80)",
     "The current code (the averaging window)",
     "weak form: no reference token"),
    ("tests/test_safeguards.py", 1011,
     "Per spec req-13 (anchor " + _("@<a id=\"req-13\">@ at L264, body at L268):"),
     "Per spec req-13 (anchor " + _("@<a id=\"req-13\">@):"),
     "the anchor id is the identity; the lines are not"),
    ("tests/test_safeguards.py", 1022, "Spec req-13 / L268 + L770 closes",
     "Spec req-13 closes", "req id plus line locators"),
    ("tests/test_schedule.py", 64, "wayfinder/spec.md L83, req-6:",
     "wayfinder " + _("@#req-6@ (Req 6 C Extraction Differentiability And "
     "Centroid Lifecycle):"),
     "path form the old regex could not match"),
    ("tests/test_schedule.py", 66, "wayfinder/spec.md L617, req-27:",
     "wayfinder " + _("@#req-27@ (Req 27 CentroidDriver Dual-Channel "
     "Architecture Contract):"),
     "path form the old regex could not match"),
    ("tests/test_sphere.py", 883, "wayfinder/spec.md L236-L237 4dp",
     _("@wayfinder@ @#req-10@ (Territory Seeding Deferred Contract) 4dp"),
     "path form plus a line range"),
    ("tests/test_sphere.py", 909, "per wayfinder/spec.md L235",
     "per " + _("@wayfinder@ @#req-10@"),
     "path form the old regex could not match"),
]
