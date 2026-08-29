from __future__ import annotations

import csv
from pathlib import Path

from common import DATA_ROOT, VIDEO_ROOT, VIDEO_EXTENSIONS


MIN_TRAIN = 4
MIN_VAL = 1
MIN_TEST = 1

DAILY_PRIORITY = [
    "hello", "hi", "thanks", "thank", "please", "sorry",
    "yes", "no", "help", "want", "need", "drink",
    "eat", "water", "food", "who", "what", "where",
    "when", "why", "now", "finish", "change", "go",
    "come", "stop", "wait", "good", "bad", "love",
    "friend", "family", "mother", "father", "computer",
]


def count_videos(folder: Path) -> int:
    if not folder.exists():
        return 0

    return sum(
        1
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def discover_classes() -> list[str]:
    names: set[str] = set()

    for split in ("train", "val", "test"):
        split_root = VIDEO_ROOT / split

        if not split_root.exists():
            continue

        for folder in split_root.iterdir():
            if folder.is_dir():
                names.add(folder.name)

    return sorted(names, key=str.lower)


def main() -> None:
    classes = discover_classes()

    if not classes:
        raise SystemExit(
            f"لم يتم العثور على مجلدات أصناف داخل: {VIDEO_ROOT}"
        )

    rows: list[dict[str, object]] = []

    for class_name in classes:
        train_count = count_videos(VIDEO_ROOT / "train" / class_name)
        val_count = count_videos(VIDEO_ROOT / "val" / class_name)
        test_count = count_videos(VIDEO_ROOT / "test" / class_name)

        usable = (
            train_count >= MIN_TRAIN
            and val_count >= MIN_VAL
            and test_count >= MIN_TEST
        )

        rows.append(
            {
                "class": class_name,
                "train": train_count,
                "val": val_count,
                "test": test_count,
                "total": train_count + val_count + test_count,
                "usable": usable,
            }
        )

    usable_names = {
        str(row["class"])
        for row in rows
        if bool(row["usable"])
    }

    recommended: list[str] = []

    for name in DAILY_PRIORITY:
        if name in usable_names and name not in recommended:
            recommended.append(name)

        if len(recommended) == 10:
            break

    if len(recommended) < 10:
        remaining = sorted(
            (
                row
                for row in rows
                if bool(row["usable"])
                and str(row["class"]) not in recommended
            ),
            key=lambda row: (
                -int(row["total"]),
                str(row["class"]).lower(),
            ),
        )

        for row in remaining:
            recommended.append(str(row["class"]))

            if len(recommended) == 10:
                break

    csv_path = DATA_ROOT / "available_classes_v2.csv"
    txt_path = DATA_ROOT / "available_classes_v2.txt"
    usable_path = DATA_ROOT / "usable_classes_v2.txt"
    suggested_path = DATA_ROOT / "classes_v2_suggested.txt"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["class", "train", "val", "test", "total", "usable"],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = ["Class, Train, Val, Test, Total, Usable", "-" * 60]

    for row in rows:
        lines.append(
            f"{str(row['class']):20s} "
            f"{int(row['train']):5d} "
            f"{int(row['val']):5d} "
            f"{int(row['test']):5d} "
            f"{int(row['total']):6d} "
            f"{'YES' if bool(row['usable']) else 'NO'}"
        )

    txt_path.write_text("\n".join(lines), encoding="utf-8")
    usable_path.write_text(
        "\n".join(sorted(usable_names, key=str.lower)),
        encoding="utf-8",
    )
    suggested_path.write_text(
        "\n".join(recommended),
        encoding="utf-8",
    )

    print("=" * 72)
    print("AVAILABLE WLASL CLASSES")
    print("=" * 72)
    print(f"Video root: {VIDEO_ROOT}")
    print(f"All classes: {len(rows)}")
    print(f"Usable classes: {len(usable_names)}")
    print()
    print(
        f"Usable means: train >= {MIN_TRAIN}, "
        f"val >= {MIN_VAL}, test >= {MIN_TEST}"
    )
    print()
    print("Suggested 10 classes for a quick daily-use MVP:")

    for index, name in enumerate(recommended, start=1):
        row = next(item for item in rows if item["class"] == name)
        print(
            f"{index:02d}. {name:18s} "
            f"train={row['train']} "
            f"val={row['val']} "
            f"test={row['test']}"
        )

    print()
    print("Files created:")
    print(f"  {csv_path}")
    print(f"  {txt_path}")
    print(f"  {usable_path}")
    print(f"  {suggested_path}")


if __name__ == "__main__":
    main()
