from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from common import DATA_ROOT, VIDEO_ROOT, VIDEO_EXTENSIONS


TARGET_GROUPS = {
    "hello": ["hello", "hi"],
    "thank_you": ["thank_you", "thank you", "thanks", "thank"],
    "please": ["please"],
    "sorry": ["sorry", "apologize", "apology"],
    "i_love_you": ["i_love_you", "i love you", "love"],
    "help": ["help"],
    "want": ["want"],
    "drink": ["drink"],
    "yes": ["yes"],
    "no": ["no"],
}


def normalize(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[\s\-]+", "_", value)
    value = re.sub(r"[^a-z0-9_]+", "", value)
    return value


def list_split_classes() -> set[str]:
    classes: set[str] = set()

    for split in ("train", "val", "test"):
        split_dir = VIDEO_ROOT / split
        if not split_dir.exists():
            continue

        for folder in split_dir.iterdir():
            if folder.is_dir():
                classes.add(normalize(folder.name))

    return classes


def index_local_videos() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)

    for path in DATA_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            index[path.stem].append(path)

    return index


def discover_json_files() -> list[Path]:
    candidates = sorted(DATA_ROOT.rglob("*.json"))
    project_root = Path(__file__).resolve().parents[1]

    for path in project_root.glob("*.json"):
        if path not in candidates:
            candidates.append(path)

    return candidates


def load_wlasl_entries(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
            and "gloss" in item
            and "instances" in item
        ]

    return []


def main() -> None:
    split_classes = list_split_classes()
    local_videos = index_local_videos()
    json_files = discover_json_files()

    metadata_matches: dict[str, list[dict]] = defaultdict(list)
    metadata_sources: set[Path] = set()
    normalized_alias_to_target: dict[str, str] = {}

    for target, aliases in TARGET_GROUPS.items():
        for alias in aliases:
            normalized_alias_to_target[normalize(alias)] = target

    for json_path in json_files:
        entries = load_wlasl_entries(json_path)
        if not entries:
            continue

        metadata_sources.add(json_path)

        for entry in entries:
            gloss = normalize(str(entry.get("gloss", "")))
            if gloss not in normalized_alias_to_target:
                continue

            target = normalized_alias_to_target[gloss]
            instances = entry.get("instances", [])

            video_ids: list[str] = []
            local_paths: list[Path] = []

            if isinstance(instances, list):
                for instance in instances:
                    if not isinstance(instance, dict):
                        continue

                    video_id = str(instance.get("video_id", "")).strip()
                    if not video_id:
                        continue

                    video_ids.append(video_id)
                    local_paths.extend(local_videos.get(video_id, []))

            metadata_matches[target].append(
                {
                    "gloss": entry.get("gloss"),
                    "source": str(json_path),
                    "instance_count": len(video_ids),
                    "local_paths": sorted({str(path) for path in local_paths}),
                }
            )

    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("WLASL WORD SEARCH")
    lines.append("=" * 78)
    lines.append(f"Data root:  {DATA_ROOT}")
    lines.append(f"Video root: {VIDEO_ROOT}")
    lines.append("")

    if metadata_sources:
        lines.append("WLASL metadata files found:")
        for source in sorted(metadata_sources):
            lines.append(f"  - {source}")
    else:
        lines.append("No compatible WLASL metadata JSON file was found.")

    lines.append("")
    lines.append("RESULTS")
    lines.append("-" * 78)

    for target, aliases in TARGET_GROUPS.items():
        normalized_aliases = {normalize(alias) for alias in aliases}
        split_match = sorted(
            name
            for name in split_classes
            if name in normalized_aliases
        )

        matches = metadata_matches.get(target, [])
        total_metadata_instances = sum(
            item["instance_count"] for item in matches
        )
        local_metadata_paths = sorted(
            {
                path
                for item in matches
                for path in item["local_paths"]
            }
        )

        lines.append(f"\n[{target}]")
        lines.append("  Aliases checked: " + ", ".join(aliases))
        lines.append(
            "  Present in split_videos: "
            + (", ".join(split_match) if split_match else "NO")
        )
        lines.append(f"  Metadata instances: {total_metadata_instances}")
        lines.append(
            f"  Matching local raw videos: {len(local_metadata_paths)}"
        )

        for item in matches:
            lines.append(
                f"    gloss={item['gloss']} | "
                f"instances={item['instance_count']} | "
                f"source={item['source']}"
            )

        for local_path in local_metadata_paths[:10]:
            lines.append(f"    local: {local_path}")

        if len(local_metadata_paths) > 10:
            lines.append(
                f"    ... and {len(local_metadata_paths) - 10} more"
            )

    report_path = DATA_ROOT / "wlasl_word_search_report.txt"
    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding="utf-8")

    print(report_text)
    print()
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
