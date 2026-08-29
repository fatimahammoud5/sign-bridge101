from pathlib import Path
import csv
import shutil


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_V2 = BASE_DIR / "dataset_v2"

# Put the ESC-50 repository/folder here:
ESC50_ROOT = BASE_DIR / "ESC-50-master"

ESC50_AUDIO = ESC50_ROOT / "audio"
ESC50_META = ESC50_ROOT / "meta" / "esc50.csv"


# ============================================================
# MAP ESC-50 CLASSES -> OUR CLASSES
# ============================================================

CLASS_MAP = {
    # --------------------------------------------------------
    # MAIN CLASSES
    # --------------------------------------------------------

    "dog": "dog_bark",

    "cat": "cat",

    "chirping_birds": "bird",
    "crow": "bird",

    "crying_baby": "baby_cry",

    "glass_breaking": "glass_break",

    "car_horn": "car_horn",

    "door_wood_knock": "doorbell",

    "airplane": "aircraft",
    "helicopter": "aircraft",

    "siren": "siren",

    "fireworks": "explosion",

    # --------------------------------------------------------
    # OTHER / HARD NEGATIVES
    # --------------------------------------------------------

    "rain": "other",
    "sea_waves": "other",
    "crackling_fire": "other",
    "crickets": "other",
    "water_drops": "other",
    "wind": "other",
    "pouring_water": "other",
    "toilet_flush": "other",
    "thunderstorm": "other",

    "sneezing": "other",
    "clapping": "other",
    "breathing": "other",
    "coughing": "other",
    "footsteps": "other",
    "laughing": "other",
    "brushing_teeth": "other",
    "snoring": "other",
    "drinking_sipping": "other",

    "mouse_click": "other",
    "keyboard_typing": "other",
    "door_wood_creaks": "other",
    "can_opening": "other",
    "washing_machine": "other",
    "vacuum_cleaner": "other",
    "clock_alarm": "other",
    "clock_tick": "other",

    "chainsaw": "other",
    "engine": "other",
    "train": "other",
    "church_bells": "other",
    "hand_saw": "other",

    # --------------------------------------------------------
    # OTHER ANIMALS
    #
    # Important:
    # Since our current classifier does not yet have separate
    # classes for these, keep them as "other".
    # --------------------------------------------------------

    "rooster": "other",
    "pig": "other",
    "cow": "other",
    "frog": "other",
    "hen": "other",
    "insects": "other",
    "sheep": "other",
}


# ============================================================
# CHECK DATASET
# ============================================================

def check_paths():
    if not ESC50_ROOT.exists():
        raise FileNotFoundError(
            "\nESC-50 folder was not found:\n"
            f"{ESC50_ROOT}\n\n"
            "Download/extract ESC-50 first and make sure "
            "the folder is named ESC-50-master."
        )

    if not ESC50_AUDIO.exists():
        raise FileNotFoundError(
            f"Missing audio folder:\n{ESC50_AUDIO}"
        )

    if not ESC50_META.exists():
        raise FileNotFoundError(
            f"Missing metadata:\n{ESC50_META}"
        )


# ============================================================
# COPY ONE FILE
# ============================================================

def copy_file(
    source: Path,
    target_class: str,
    esc_category: str,
):
    target_dir = (
        DATASET_V2 /
        target_class
    )

    target_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Prefix prevents collisions and tells us where it came from.
    target_name = (
        f"esc50_{esc_category}_{source.name}"
    )

    target_path = (
        target_dir /
        target_name
    )

    if target_path.exists():
        return False

    shutil.copy2(
        source,
        target_path,
    )

    return True


# ============================================================
# COUNT FILES
# ============================================================

def count_audio(folder: Path):
    if not folder.exists():
        return 0

    return sum(
        1
        for path in folder.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in {
                ".wav",
                ".mp3",
                ".flac",
                ".ogg",
                ".m4a",
            }
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 75)
    print("SIGNBRIDGE - ADD ESC-50 TO DATASET V2")
    print("=" * 75)

    check_paths()

    DATASET_V2.mkdir(
        parents=True,
        exist_ok=True,
    )

    copied_counts = {}
    skipped_counts = {}
    source_counts = {}

    # ========================================================
    # READ OFFICIAL ESC-50 METADATA
    # ========================================================

    with open(
        ESC50_META,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:
            filename = (
                row["filename"]
                .strip()
            )

            category = (
                row["category"]
                .strip()
            )

            if category not in CLASS_MAP:
                continue

            target_class = (
                CLASS_MAP[category]
            )

            source = (
                ESC50_AUDIO /
                filename
            )

            if not source.exists():
                print(
                    f"[WARNING] Missing: {source}"
                )
                continue

            source_counts[category] = (
                source_counts.get(
                    category,
                    0,
                ) + 1
            )

            copied = copy_file(
                source=source,
                target_class=target_class,
                esc_category=category,
            )

            if copied:
                copied_counts[target_class] = (
                    copied_counts.get(
                        target_class,
                        0,
                    ) + 1
                )
            else:
                skipped_counts[target_class] = (
                    skipped_counts.get(
                        target_class,
                        0,
                    ) + 1
                )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 75)
    print("ESC-50 SOURCE COUNTS")
    print("=" * 75)

    for category in sorted(
        source_counts.keys()
    ):
        print(
            f"{category:25s}: "
            f"{source_counts[category]}"
        )

    print()
    print("=" * 75)
    print("COPIED INTO DATASET V2")
    print("=" * 75)

    target_classes = [
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

    for class_name in target_classes:
        folder = (
            DATASET_V2 /
            class_name
        )

        count = count_audio(
            folder
        )

        total += count

        copied = (
            copied_counts.get(
                class_name,
                0,
            )
        )

        skipped = (
            skipped_counts.get(
                class_name,
                0,
            )
        )

        print(
            f"{class_name:13s}: "
            f"total={count:4d} "
            f"new={copied:4d} "
            f"skipped={skipped:4d}"
        )

    print("-" * 75)

    print(
        f"{'TOTAL':13s}: "
        f"{total}"
    )

    print()
    print("=" * 75)
    print("DONE")
    print("=" * 75)

    print()
    print(
        "ESC-50 files were COPIED."
    )

    print(
        "Original ESC-50 files were not modified."
    )


if __name__ == "__main__":
    main()