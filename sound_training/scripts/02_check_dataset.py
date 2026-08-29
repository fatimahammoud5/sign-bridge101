from pathlib import Path

import librosa


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

CLASSES = [
    "explosion",
    "drone",
    "dog_bark",
    "aircraft",
    "siren",
    "other",
]

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}


def main():
    print("=" * 70)
    print("SIGNBRIDGE - DATASET CHECK")
    print("=" * 70)

    total_files = 0
    total_valid = 0
    total_failed = 0

    for class_name in CLASSES:
        class_dir = DATASET_DIR / class_name

        print()
        print("-" * 70)
        print(f"CLASS: {class_name}")
        print(f"PATH : {class_dir}")
        print("-" * 70)

        if not class_dir.exists():
            print("Folder does not exist.")
            continue

        audio_files = [
            path
            for path in class_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        audio_files.sort()

        print(f"Audio files found: {len(audio_files)}")

        total_files += len(audio_files)

        class_valid = 0
        class_failed = 0

        durations = []
        sample_rates = set()

        for index, audio_path in enumerate(
            audio_files,
            start=1,
        ):
            try:
                audio, sample_rate = librosa.load(
                    audio_path,
                    sr=None,
                    mono=True,
                )

                if len(audio) == 0:
                    raise ValueError("Empty audio file")

                duration = len(audio) / sample_rate

                durations.append(duration)
                sample_rates.add(sample_rate)

                class_valid += 1
                total_valid += 1

                if index <= 5:
                    print(
                        f"[OK] {audio_path.name} | "
                        f"{duration:.2f}s | "
                        f"{sample_rate} Hz"
                    )

            except Exception as error:
                class_failed += 1
                total_failed += 1

                print(
                    f"[FAILED] {audio_path.name}"
                )
                print(
                    f"         {error}"
                )

        print()
        print(f"Valid : {class_valid}")
        print(f"Failed: {class_failed}")

        if durations:
            print(
                f"Shortest duration: "
                f"{min(durations):.2f}s"
            )

            print(
                f"Longest duration : "
                f"{max(durations):.2f}s"
            )

            print(
                f"Average duration : "
                f"{sum(durations) / len(durations):.2f}s"
            )

        if sample_rates:
            print(
                "Sample rates:",
                sorted(sample_rates),
            )

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"Total files : {total_files}")
    print(f"Valid files : {total_valid}")
    print(f"Failed files: {total_failed}")

    print()
    print("Files per class:")

    for class_name in CLASSES:
        class_dir = DATASET_DIR / class_name

        if not class_dir.exists():
            count = 0
        else:
            count = len(
                [
                    path
                    for path in class_dir.rglob("*")
                    if path.is_file()
                    and path.suffix.lower()
                    in SUPPORTED_EXTENSIONS
                ]
            )

        print(
            f"{class_name:12s}: {count}"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()