from __future__ import annotations

import argparse
import inspect
from pathlib import Path

import numpy as np

from common import (
    DATA_ROOT,
    FEATURES_ROOT,
    RAW_FEATURES,
    SEQUENCE_LENGTH,
    VIDEO_EXTENSIONS,
    create_video_detector,
    extract_video_sequence,
    load_classes,
)

WEBCAM_ROOT = DATA_ROOT / "webcam_videos_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def extract_one_video(video_path: Path) -> np.ndarray | None:
    parameter_count = len(inspect.signature(extract_video_sequence).parameters)
    if parameter_count == 1:
        return extract_video_sequence(video_path)
    if parameter_count == 2:
        with create_video_detector() as detector:
            return extract_video_sequence(video_path, detector)
    raise RuntimeError("صيغة extract_video_sequence غير متوقعة داخل common.py")


def list_videos(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)


def main() -> None:
    args = parse_args()
    classes = load_classes()
    total = saved = skipped = failed = 0
    failures: list[str] = []

    print("=" * 70)
    print("EXTRACT WEBCAM FEATURES")
    print("=" * 70)
    print(f"Videos:   {WEBCAM_ROOT}")
    print(f"Features: {FEATURES_ROOT}")
    print(f"Shape:    ({SEQUENCE_LENGTH}, {RAW_FEATURES})")

    for split in ("train", "val", "test"):
        print(f"\n--- {split.upper()} ---")
        for class_name in classes:
            input_folder = WEBCAM_ROOT / split / class_name
            output_folder = FEATURES_ROOT / split / class_name
            output_folder.mkdir(parents=True, exist_ok=True)
            videos = list_videos(input_folder)
            print(f"{class_name:18s}: {len(videos)} webcam video(s)")

            for video_path in videos:
                total += 1
                output_path = output_folder / f"webcam__{video_path.stem}.npy"
                if output_path.exists() and not args.overwrite:
                    skipped += 1
                    continue

                try:
                    sequence = extract_one_video(video_path)
                    if sequence is None:
                        raise ValueError("No usable hand sequence")
                    if sequence.shape != (SEQUENCE_LENGTH, RAW_FEATURES):
                        raise ValueError(f"Bad shape: {sequence.shape}")
                    if not np.isfinite(sequence).all():
                        raise ValueError("NaN or Inf detected")
                    np.save(output_path, sequence)
                    saved += 1
                except Exception as exc:
                    failed += 1
                    failures.append(str(video_path))
                    print(f"  [FAILED] {video_path.name}: {type(exc).__name__}: {exc}")

    failure_log = DATA_ROOT / "failed_webcam_features_v2.txt"
    failure_log.write_text("\n".join(failures), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"Total:   {total}")
    print(f"Saved:   {saved}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")
    print(f"Failure log: {failure_log}")
    print("=" * 70)

    if total == 0:
        raise SystemExit("لم يجد أي تسجيلات. شغلي الملف 07 أولًا.")


if __name__ == "__main__":
    main()