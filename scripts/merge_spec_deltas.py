"""Apply OpenSpec delta files to master spec files.

Originally written as a Windows recovery tool (CLI `openspec archive` EPERMed
on `Move-Item` rename for this repo). Promoted to a parameterized helper
that:
  - parses MODIFIED / ADDED blocks from a delta spec,
  - splices MODIFIED blocks into the corresponding master requirement slot,
  - appends ADDED blocks at the file tail,
  - assigns `<a id="req-N"></a>` anchors to ADDED blocks (numbered from the
    next unused slot after the master's highest existing anchor).

Boundary convention: a MODIFIED block ends at the next `### Requirement: `
header line OR the next `<a id="req-N"></a>` anchor line (NOT at `---`
separators, which the delta uses between MODIFIED blocks but the master
may not).

Usage:
    python scripts/merge_spec_deltas.py \
        --delta openspec/changes/archive/<change>/specs/<cap>/spec.md \
        --master openspec/specs/<cap>/spec.md \
        --capability <cap>

Exit 0 on success (and prints applied/modified counts); non-zero if any
MODIFIED title is missing from the master (means the delta is out of sync
with the master — refuse to silently drop).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_delta_blocks(delta_text: str):
    # Splits the delta into a flat list of (header_label, body) pairs.
    # header_label is "MODIFIED Requirements" or "ADDED Requirements"
    # (None for the preamble before the first ## header).
    pieces = re.split(
        r"^## (MODIFIED Requirements|ADDED Requirements)\s*$",
        delta_text,
        flags=re.MULTILINE,
    )
    # pieces is [preamble, label1, body1, label2, body2, ...]
    sections: list[tuple[str | None, str]] = []
    sections.append((None, pieces[0]))
    i = 1
    while i + 1 < len(pieces):
        sections.append((pieces[i], pieces[i + 1]))
        i += 2

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

    mod_blocks: dict[str, str] = {}
    added_blocks: list[str] = []
    for label, body in sections:
        if label == "MODIFIED Requirements":
            for title, block in split_requirements(body):
                mod_blocks[title] = block
        elif label == "ADDED Requirements":
            for _, block in split_requirements(body):
                added_blocks.append(block)

    return mod_blocks, added_blocks


def strip_trailing_separators(block: str) -> str:
    """Remove trailing `---` lines from a MODIFIED block so we don't
    accumulate separators when splicing back into the master."""
    lines = block.rstrip("\n").split("\n")
    while lines and lines[-1].strip() == "---":
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def highest_existing_anchor(master_text: str) -> int:
    """Return the highest `req-N` number present in the master, or 0."""
    nums = [int(m) for m in re.findall(r'<a id="req-(\d+)"></a>', master_text)]
    return max(nums) if nums else 0


def ensure_block_anchor(block: str, anchor_id: str) -> str:
    """Prepend `<a id="anchor_id"></a>` to a block if it doesn't start with
    one. Returns the block unchanged when it already has an anchor."""
    if re.match(r'^<a id="req-\d+"></a>', block):
        return block
    return f'<a id="{anchor_id}"></a>\n\n{block}'


def merge_into_master(
    master_path: Path,
    delta_path: Path,
    capability_label: str,
) -> tuple[list[str], list[str], int]:
    delta_text = delta_path.read_text(encoding="utf-8")
    master_text = master_path.read_text(encoding="utf-8")

    modified, added = parse_delta_blocks(delta_text)
    print(
        f"[{capability_label}] delta has "
        f"{len(modified)} MODIFIED + {len(added)} ADDED Requirements"
    )

    applied_modified: list[str] = []
    missing_modified: list[str] = []

    end_pattern = re.compile(
        r"^(### Requirement: |<a id=\"req-)", re.MULTILINE
    )

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

        rest = master_text[start_match.end():]
        end_match = end_pattern.search(rest)
        end_pos_in_rest = end_match.start() if end_match else len(rest)
        master_end = start_match.end() + end_pos_in_rest

        clean_block = strip_trailing_separators(block)
        master_text = (
            master_text[: start_match.start()]
            + clean_block
            + master_text[master_end:]
        )
        applied_modified.append(title)

    next_anchor = highest_existing_anchor(master_text) + 1
    assigned = 0

    if added:
        if not master_text.endswith("\n"):
            master_text += "\n"
        master_text += "\n---\n\n"
        for block in added:
            anchor_id = f"req-{next_anchor + assigned}"
            block_with_anchor = ensure_block_anchor(block, anchor_id)
            master_text += block_with_anchor + "\n\n"
            assigned += 1

    master_path.write_text(master_text, encoding="utf-8")

    print(f"[{capability_label}] applied MODIFIED: {applied_modified}")
    if missing_modified:
        print(
            f"[{capability_label}] MISSING MODIFIED titles "
            f"(not found in master): {missing_modified}"
        )
    print(f"[{capability_label}] appended {len(added)} ADDED Requirements")
    return applied_modified, missing_modified, assigned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--delta", required=True, type=Path)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--capability", required=True)
    args = parser.parse_args()

    if not args.delta.exists():
        print(f"!! delta not found: {args.delta}", file=sys.stderr)
        return 2
    if not args.master.exists():
        print(f"!! master not found: {args.master}", file=sys.stderr)
        return 2

    _applied, missing, _assigned = merge_into_master(
        args.master, args.delta, args.capability
    )
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())