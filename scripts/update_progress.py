#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# Map test file names (or markers) to ROADMAP IDs
TEST_TO_IDS = {
    "test_memory_domain.py": ["NC-1002"],
    "test_api_memories.py": ["NC-1003"],
    "test_healthz.py": ["NC-1001"],
    "test_precommit_hooks.py": ["NC-0007"],
    "test_docker_local.py": ["NC-0009"],
    "test_openapi_schema.py": ["NC-0010"],
    "test_repo_foundations_files.py": ["NC-0004", "NC-0005", "NC-0008"],
    "test_transcript_segment.py": ["NC-1004"],
    "test_capture_session.py": ["NC-1005"],
    "test_participant.py": ["NC-1006"],
    "test_consent_record.py": ["NC-1007"],
    "test_tag_importance.py": ["NC-1008"],
    "test_retention_policy.py": ["NC-1009"],
    "test_recall_card.py": ["NC-1010"],
}

ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = ROOT / "docs" / "ROADMAP.md"

CHECKED = "- [x]"
UNCHECKED = "- [ ]"


def parse_args(argv: list[str]) -> tuple[list[str], Path | None]:
    preview_path: Path | None = None
    raw: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--preview" and i + 1 < len(argv):
            preview_path = (
                (ROOT / argv[i + 1]).resolve()
                if not argv[i + 1].startswith("/")
                else Path(argv[i + 1]).resolve()
            )
            i += 2
            continue
        raw.append(argv[i])
        i += 1
    tests: list[str] = []
    for token in raw:
        for part in token.split(","):
            part = part.strip()
            if part:
                tests.append(part)
    return tests, preview_path


def main(argv: list[str]) -> int:
    tests, preview_path = parse_args(argv)

    if not ROADMAP_PATH.exists():
        print(f"Roadmap not found: {ROADMAP_PATH}")
        return 1

    ids_to_check: set[str] = set()
    for test_name in tests:
        ids_to_check.update(TEST_TO_IDS.get(test_name, []))

    content = ROADMAP_PATH.read_text(encoding="utf-8")

    def replace_item(match: re.Match[str]) -> str:
        prefix = match.group(1)
        item_id = match.group(2)
        rest = match.group(3)
        if item_id in ids_to_check and prefix == UNCHECKED:
            return f"{CHECKED} {item_id}{rest}"
        return match.group(0)

    pattern = re.compile(
        rf"^({re.escape(UNCHECKED)}|{re.escape(CHECKED)})\s+(NC-\d{{4}})(.*)$",
        re.MULTILINE,
    )
    new_content = pattern.sub(replace_item, content)

    if preview_path:
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(new_content, encoding="utf-8")
        print(f"Preview written to {preview_path}")
        return 0

    if new_content != content:
        ROADMAP_PATH.write_text(new_content, encoding="utf-8")
        print("Updated roadmap")
    else:
        print("No changes applied to roadmap.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
