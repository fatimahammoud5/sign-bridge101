from __future__ import annotations

import argparse
import numpy as np

from common import (
    DATA_ROOT,
    VIDEO_ROOT,
    FEATURES_ROOT,
    SEQUENCE_LENGTH,
    RAW_FEATURES,
    extract_video_sequence,
    list_video_files,
    load_classes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-extract files that already exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    classes = load_classes()
    FEATURES_ROOT.mkdir(parents=True, exist_ok=True)

    total = 0
    saved = 0
    skipped = 0
    failed = 0
    failures: list[str] = []

    print("=" * 70)
    print("FEATURE EXTRACTION V2")
    print("=" * 70)
    print(f"Videos: {VIDEO_ROOT}")
    print(f"Output: {FEATURES_ROOT}")
    print(f"Shape:  ({SEQUENCE_LENGTH}, {RAW_FEATURES})")

    for split in ["train", "val", "test"]:
        print(f"\n--- {split.upper()} ---")

        for class_name in classes:
            input_folder = VIDEO_ROOT / split / class_name
            output_folder = FEATURES_ROOT / split / class_name
            output_folder.mkdir(parents=True, exist_ok=True)

            videos = list_video_files(input_folder)
            print(f"{class_name:18s}: {len(videos)} video(s)")

            for video_path in videos:
                total += 1

                relative_name = video_path.relative_to(input_folder)
                safe_stem = "__".join(
                    relative_name.with_suffix("").parts
                )
                output_path = output_folder / f"{safe_stem}.npy"

                if output_path.exists() and not args.overwrite:
                    skipped += 1
                    continue

                try:
                    sequence = extract_video_sequence(video_path)

                    if sequence is None:
                        failed += 1
                        failures.append(str(video_path))
                        print(f"  [FAILED] {video_path.name}")
                        continue

                    if sequence.shape != (
                        SEQUENCE_LENGTH,
                        RAW_FEATURES,
                    ):
                        failed += 1
                        failures.append(str(video_path))
                        print(
                            f"  [BAD SHAPE] {video_path.name}: "
                            f"{sequence.shape}"
                        )
                        continue

                    if not np.isfinite(sequence).all():
                        failed += 1
                        failures.append(str(video_path))
                        print(f"  [NAN/INF] {video_path.name}")
                        continue

                    np.save(output_path, sequence)
                    saved += 1

                except Exception as exc:
                    failed += 1
                    failures.append(str(video_path))
                    print(
                        f"  [ERROR] {video_path.name}: "
                        f"{type(exc).__name__}: {exc}"
                    )

    failure_log = DATA_ROOT / "failed_features_v2.txt"
    failure_log.write_text(
        "\n".join(failures),
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print(f"Total:   {total}")
    print(f"Saved:   {saved}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")
    print(f"Failure log: {failure_log}")
    print("=" * 70)

    if saved == 0 and skipped == 0:
        raise SystemExit("No feature files were produced.")


if __name__ == "__main__":
    main()
