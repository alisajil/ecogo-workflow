#!/usr/bin/env python3
"""Deterministic knowledge-base lint checks.

Finds three classes of structural issue in a `wiki/` directory:

- DEAD_LINK       : [[wikilink]] targets that do not resolve to a file
- ORPHAN          : pages with no inbound wikilinks (index.md and log.md excluded)
- MISSING_SECTION : concept pages lacking a `Counter-Arguments and Gaps` section

Usage:
    python3 lint-kb.py <path-to-wiki-dir>

Exit code is always 0 (so the caller does not treat lint findings as errors);
findings are printed to stdout, one per line, in a `CLASS: detail` format.
"""

from __future__ import annotations

import os
import re
import sys


WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
SKIP_SLUGS = {"index", "log"}


def md_files(root: str) -> dict[str, str]:
    """Return {slug: relative_path} for every .md under root, recursing."""
    out: dict[str, str] = {}
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            slug = os.path.splitext(name)[0]
            out[slug] = rel
    return out


def extract_targets(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as fp:
        return WIKILINK.findall(fp.read())


def has_section(path: str, needle: str) -> bool:
    with open(path, "r", encoding="utf-8") as fp:
        return needle.lower() in fp.read().lower()


def lint(wiki_dir: str) -> int:
    if not os.path.isdir(wiki_dir):
        print(f"error: {wiki_dir} is not a directory", file=sys.stderr)
        return 1

    files = md_files(wiki_dir)
    inbound: dict[str, set[str]] = {slug: set() for slug in files}
    findings: list[str] = []

    # Pass 1 — resolve every wikilink; flag dead ones; build inbound index
    for slug, rel in files.items():
        for target in extract_targets(os.path.join(wiki_dir, rel)):
            target_slug = target.strip().lower()
            resolved = [s for s in files if s.lower() == target_slug]
            if not resolved:
                findings.append(f"DEAD_LINK: [[{target}]] in {rel}")
                continue
            for r in resolved:
                inbound[r].add(slug)

    # Pass 2 — orphan detection (excluding index + log)
    for slug, rel in files.items():
        if slug in SKIP_SLUGS:
            continue
        if not inbound.get(slug):
            findings.append(f"ORPHAN: {rel} has no inbound links")

    # Pass 3 — missing Counter-Arguments section on concept pages
    for slug, rel in files.items():
        if slug in SKIP_SLUGS:
            continue
        path = os.path.join(wiki_dir, rel)
        if has_section(path, "Counter-Arguments and Gaps"):
            continue
        with open(path, "r", encoding="utf-8") as fp:
            body = fp.read()
        if "type: concept" in body:
            findings.append(f"MISSING_SECTION: {rel} lacks 'Counter-Arguments and Gaps'")

    if not findings:
        print("OK: no issues found")
        return 0

    for line in sorted(findings):
        print(line)
    print(f"\nTotal: {len(findings)} issue(s)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <wiki-directory>", file=sys.stderr)
        sys.exit(1)
    sys.exit(lint(sys.argv[1]))
