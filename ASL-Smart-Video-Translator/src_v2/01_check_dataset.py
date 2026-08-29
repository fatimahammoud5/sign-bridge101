from __future__ import annotations

from pathlib import Path


VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".mpeg",
    ".mpg",
}


def find_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_data_root(project_root: Path) -> Path:
    candidates = [
        project_root / "data" / "WLASL100",
        project_root / "WLASL100",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "لم يتم العثور على مجلد WLASL100 داخل المشروع."
    )


def find_video_root(data_root: Path) -> Path:
    candidates = [
        data_root / "split_videos",
        data_root,
    ]

    for candidate in candidates:
        if all(
            (candidate / split).exists()
            for split in ("train", "val", "test")
        ):
            return candidate

    raise FileNotFoundError(
        "لم يتم العثور على train/val/test داخل "
        f"{data_root / 'split_videos'} أو {data_root}"
    )


def load_classes(data_root: Path) -> list[str]:
    classes_path = data_root / "classes_v2.txt"

    if not classes_path.exists():
        raise FileNotFoundError(
            f"ملف الكلمات غير موجود: {classes_path}"
        )

    classes = [
        line.strip()
        for line in classes_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if not classes:
        raise ValueError(
            f"ملف الكلمات فارغ: {classes_path}"
        )

    return classes


def count_videos(folder: Path) -> int:
    if not folder.exists():
        return 0

    return sum(
        1
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def main() -> None:
    project_root = find_project_root()
    data_root = find_data_root(project_root)
    video_root = find_video_root(data_root)
    classes = load_classes(data_root)

    print("=" * 70)
    print("DATASET CHECK")
    print("=" * 70)
    print(f"Data root:  {data_root}")
    print(f"Video root: {video_root}")
    print(f"Classes: {classes}")
    print()
    print(f"{'Class':20s} {'Train':>8s} {'Val':>8s} {'Test':>8s}")
    print("-" * 50)

    blocking_problems = 0
    total_train = 0
    total_val = 0
    total_test = 0

    for class_name in classes:
        counts = {}

        for split in ("train", "val", "test"):
            class_folder = (
                video_root
                / split
                / class_name
            )
            counts[split] = count_videos(
                class_folder
            )

        total_train += counts["train"]
        total_val += counts["val"]
        total_test += counts["test"]

        print(
            f"{class_name:20s} "
            f"{counts['train']:8d} "
            f"{counts['val']:8d} "
            f"{counts['test']:8d}"
        )

        if counts["train"] == 0:
            print(
                f"  [BLOCKING] {class_name}: "
                "train is empty."
            )
            blocking_problems += 1
        elif counts["train"] < 4:
            print(
                f"  [WARNING] {class_name}: "
                "train has fewer than 4 videos."
            )

        if counts["val"] == 0:
            print(
                f"  [BLOCKING] {class_name}: "
                "val is empty."
            )
            blocking_problems += 1

        if counts["test"] == 0:
            print(
                f"  [BLOCKING] {class_name}: "
                "test is empty."
            )
            blocking_problems += 1

    print("-" * 50)
    print(
        f"{'TOTAL':20s} "
        f"{total_train:8d} "
        f"{total_val:8d} "
        f"{total_test:8d}"
    )
    print()

    if blocking_problems:
        print(
            f"Found {blocking_problems} "
            "blocking problem(s)."
        )
        raise SystemExit(1)

    print(
        "Dataset paths and selected classes are valid."
    )


if __name__ == "__main__":
    main()