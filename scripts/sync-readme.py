#!/usr/bin/env python3
"""Sync the topic list in README.md with the vault's top-level directories."""

import os
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
README = VAULT / "README.md"
EXCLUDE = {".obsidian", ".git", ".agents", "Clippings", "inbox", "scripts"}
START_MARKER = "<!-- topics:start -->"
END_MARKER = "<!-- topics:end -->"


def count_md_files(directory: Path) -> int:
    return sum(1 for _ in directory.rglob("*.md"))


def build_topic_list() -> str:
    topics = []
    for entry in sorted(VAULT.iterdir()):
        if not entry.is_dir() or entry.name in EXCLUDE or entry.name.startswith("."):
            continue
        count = count_md_files(entry)
        if count > 0:
            topics.append(f"**{entry.name}** ({count})")
    return " &middot; ".join(topics)


def main() -> int:
    text = README.read_text()
    start = text.index(START_MARKER) + len(START_MARKER)
    end = text.index(END_MARKER)
    topic_line = f"\n{build_topic_list()}\n"
    if text[start:end] == topic_line:
        return 0
    updated = text[:start] + topic_line + text[end:]
    README.write_text(updated)
    return 1


if __name__ == "__main__":
    sys.exit(main())
