from pathlib import Path
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent

OLD_DATASET = BASE_DIR / "dataset"
NEW_DATASET = BASE_DIR / "dataset_v2"


# ============================================================
# COPY EXISTING TRAINING DATA INTO V2
# ============================================================

EXISTING_CLASSES = [
    "explosion",
    "drone",
    "aircraft",
    "siren",
    "dog_bark",
    "other",
]


def copy_class(class_name: str):
    source = OLD_DATASET / class_name
    destination = NEW_DATASET / class_name

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not source.exists():
        print(
            f"[WARNING] Missing old folder: {source}"
        )
        return

    copied = 0
    skipped = 0

    for file_path in source.iterdir():
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in {
            ".wav",
            ".mp3",
            ".flac",
            ".ogg",
            ".m4a",
        }:
            continue

        output_path = destination / file_path.name

        if output_path.exists():
            skipped += 1
            continue

        shutil.copy2(
            file_path,
            output_path,
        )

        copied += 1

    print(
        f"{class_name:12s} "
        f"copied={copied:4d} "
        f"skipped={skipped:4d}"
    )


def print_counts():
    print()
    print("=" * 70)
    print("DATASET V2 COUNTS")
    print("=" * 70)

    classes = [
        "explosion",
        "drone",
        "aircraft",
        "siren",
        "dog_bark",
        "cat",
        "bird",
        "baby_cry",
        "glass_break",
        "car_horn",
        "doorbell",
        "speech",
        "music",
        "other",
    ]

    total = 0

    for class_name in classes:
        folder = NEW_DATASET / class_name

        if not folder.exists():
            count = 0
        else:
            count = sum(
                1
                for path in folder.iterdir()
                if path.is_file()
                and path.suffix.lower()
                in {
                    ".wav",
                    ".mp3",
                    ".flac",
                    ".ogg",
                    ".m4a",
                }
            )

        total += count

        print(
            f"{class_name:12s}: {count}"
        )

    print("-" * 70)
    print(
        f"{'TOTAL':12s}: {total}"
    )


def main():
    print("=" * 70)
    print("SIGNBRIDGE - PREPARE DATASET V2")
    print("=" * 70)

    NEW_DATASET.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Create all target directories.
    all_classes = [
        "explosion",
        "drone",
        "aircraft",
        "siren",
        "dog_bark",
        "cat",
        "bird",
        "baby_cry",
        "glass_break",
        "car_horn",
        "doorbell",
        "speech",
        "music",
        "other",
    ]

    for class_name in all_classes:
        (
            NEW_DATASET / class_name
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

    print()
    print(
        "Copying old dataset..."
    )
    print()

    for class_name in EXISTING_CLASSES:
        copy_class(
            class_name
        )

    print_counts()

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

    print()
    print(
        "Old dataset was NOT modified."
    )

    print(
        "New dataset is:"
    )

    print(
        NEW_DATASET
    )


if __name__ == "__main__":
    main()