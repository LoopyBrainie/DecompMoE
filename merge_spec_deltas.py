"""Apply OpenSpec delta files to master spec files (v2: fixed boundary handling).

Boundary: a MODIFIED block ends at the next `### Requirement: ` header line
OR the next `<a id="req-N"></a>` anchor line (NOT at `---` separators,
which the delta uses between MODIFIED blocks but the master may not).
"""

import re
import sys
from pathlib import Path


REPO_ROOT = Path(".")
DELTA_ROOT = REPO_ROOT / "openspec" / "changes" / "archive" / "2026-08-23-fix-math-consistency-audit-2026-08"
MASTER_ROOT = REPO_ROOT / "openspec" / "specs"

CAPS = [("wayfinder", "wayfinder"), ("decompmoe-skeleton", "decompmoe-skeleton")]


def parse_delta_blocks(delta_text: str):
    sections = re.split(r"^## (MODIFIED Requirements|ADDED Requirements)\s*$", delta_text, flags=re.MULTILINE)

    def split_requirements(body):
        blocks = re.split(r"(?=^### Requirement: )", body, flags=re.MULTILINE)
        for block in blocks:
            block = block.strip("\n")
            if not block.startswith("### Requirement:"):
                continue
            first_line, _, _ = block.partition("\n")
            m = re.match(r"^### Requirement: (.+?)\s*$", first_line)
            if not m:
                continue
            title = m.group(1)
            yield title, block.rstrip() + "\n"

    modified = {}
    if len(sections) >= 3:
        for title, block in split_requirements(sections[2]):
            modified[title] = block
    added = []
    if len(sections) >= 5:
        for _, block in split_requirements(sections[4]):
            added.append(block)
    return modified, added


def strip_trailing_separators(block: str) -> str:
    """Remove trailing `---` lines from a MODIFIED block so we don't accumulate
    separators when splicing back into the master."""
    lines = block.rstrip("\n").split("\n")
    while lines and lines[-1].strip() == "---":
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def merge_into_master(master_path: Path, delta_path: Path, capability_label: str):
    delta_text = delta_path.read_text(encoding="utf-8")
    master_text = master_path.read_text(encoding="utf-8")

    modified, added = parse_delta_blocks(delta_text)

    print(f"[{capability_label}] delta has {len(modified)} MODIFIED + {len(added)} ADDED Requirements")

    applied_modified = []
    missing_modified = []

    end_pattern = re.compile(r"^(### Requirement: |<a id=\"req-)", re.MULTILINE)

    for title, block in modified.items():
        escaped_title = re.escape(title)
        start_pattern = re.compile(
            r"^### Requirement: " + escaped_title + r"\s*$",
            re.MULTILINE,
        )
        start_match = start_pattern.search(master_text)
        if not start_match:
            missing_modified.append(title)
            continue

        # Find end: next "### Requirement: " or anchor <a id="req-N">
        # Look forward in master from start_match.end()
        rest = master_text[start_match.end():]
        end_match = end_pattern.search(rest)
        if end_match:
            end_pos_in_rest = end_match.start()
        else:
            end_pos_in_rest = len(rest)
        master_end = start_match.end() + end_pos_in_rest

        # Strip any trailing `---` from the replacement block
        clean_block = strip_trailing_separators(block)

        master_text = master_text[:start_match.start()] + clean_block + master_text[master_end:]
        applied_modified.append(title)

    if added:
        if not master_text.endswith("\n"):
            master_text += "\n"
        master_text += "\n---\n\n"
        for block in added:
            master_text += block + "\n\n"

    master_path.write_text(master_text, encoding="utf-8")

    print(f"[{capability_label}] applied MODIFIED: {applied_modified}")
    if missing_modified:
        print(f"[{capability_label}] MISSING MODIFIED titles (not found in master): {missing_modified}")
    print(f"[{capability_label}] appended {len(added)} ADDED Requirements")
    return applied_modified, missing_modified


def main():
    summary = {}
    for delta_cap, master_cap in CAPS:
        delta_path = DELTA_ROOT / "specs" / delta_cap / "spec.md"
        master_path = MASTER_ROOT / master_cap / "spec.md"
        if not delta_path.exists():
            print(f"!! delta not found: {delta_path}")
            continue
        if not master_path.exists():
            print(f"!! master not found: {master_path}")
            continue
        applied, missing = merge_into_master(master_path, delta_path, delta_cap)
        summary[delta_cap] = {"applied": applied, "missing": missing}

    print("\n=== FINAL ===")
    any_missing = False
    for cap, r in summary.items():
        print(f"[{cap}] applied {len(r['applied'])} MODIFIED")
        if r["missing"]:
            any_missing = True
            print(f"  MISSING: {r['missing']}")
    if any_missing:
        sys.exit(1)


if __name__ == "__main__":
    main()