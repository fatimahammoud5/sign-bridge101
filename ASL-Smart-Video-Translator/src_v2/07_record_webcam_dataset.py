from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

import cv2

from common import DATA_ROOT, load_classes

OUTPUT_ROOT = DATA_ROOT / "webcam_videos_v2"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30.0
CLIP_SECONDS = 2.0
COUNTDOWN_SECONDS = 2.0
TARGET_COUNTS = {"train": 12, "val": 3, "test": 3}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    return parser.parse_args()


def open_camera(index: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("تعذر فتح الكاميرا. أغلقي أي برنامج آخر يستخدمها.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    return cap


def count_recordings(split: str, class_name: str) -> int:
    folder = OUTPUT_ROOT / split / class_name
    if not folder.exists():
        return 0
    return len([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".avi", ".mp4", ".mov", ".mkv"}])


def create_writer(path: Path) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        FPS,
        (FRAME_WIDTH, FRAME_HEIGHT),
    )
    if not writer.isOpened():
        raise RuntimeError(f"تعذر إنشاء الفيديو: {path}")
    return writer


def draw_text(frame, text: str, y: int, size: float = 0.62) -> None:
    cv2.putText(frame, text, (18, y), cv2.FONT_HERSHEY_SIMPLEX, size, (255, 255, 255), 2, cv2.LINE_AA)


def main() -> None:
    args = parse_args()
    classes = load_classes()
    if len(classes) != 10:
        raise ValueError(f"يجب أن يحتوي classes_v2.txt على 10 فئات. الموجود: {classes}")

    split_keys = {ord("t"): "train", ord("v"): "val", ord("e"): "test"}
    class_index = 0
    split = "train"
    countdown_started: float | None = None
    recording_started = 0.0
    writer: cv2.VideoWriter | None = None
    output_path: Path | None = None
    last_status = "READY"

    cap = open_camera(args.camera)

    print("1=hello 2=thank_you 3=please 4=sorry 5=yes")
    print("6=no 7=i_love_you 8=help 9=want 0=drink")
    print("T=train V=val E=test SPACE=record Q=quit")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        now = time.monotonic()
        class_name = classes[class_index]
        target = TARGET_COUNTS[split]
        existing = count_recordings(split, class_name)
        status = last_status

        if countdown_started is not None:
            remaining = COUNTDOWN_SECONDS - (now - countdown_started)
            if remaining > 0:
                status = f"GET READY: {remaining:.1f}"
            else:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_path = OUTPUT_ROOT / split / class_name / f"{class_name}_{stamp}.avi"
                writer = create_writer(output_path)
                recording_started = now
                countdown_started = None
                status = "RECORDING"

        if writer is not None:
            writer.write(frame)  # Save unmirrored frames.
            elapsed = now - recording_started
            status = f"RECORDING: {elapsed:.1f}/{CLIP_SECONDS:.1f}s"
            if elapsed >= CLIP_SECONDS:
                writer.release()
                writer = None
                last_status = "SAVED"
                status = last_status
                print(f"Saved: {output_path}")

        display = cv2.flip(frame, 1)
        cv2.rectangle(display, (0, 0), (FRAME_WIDTH, 190), (20, 20, 20), -1)
        draw_text(display, f"Class: {class_name} ({class_index + 1}/10)", 32)
        draw_text(display, f"Split: {split}", 64)
        draw_text(display, f"Saved: {existing}/{target}", 96)
        draw_text(display, f"Status: {status}", 128)
        draw_text(display, "Neutral -> sign -> neutral", 160, 0.54)
        draw_text(display, "1-9/0 class | T/V/E | SPACE record | Q quit", FRAME_HEIGHT - 18, 0.47)
        cv2.imshow("Record ASL Daily Words", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if writer is not None or countdown_started is not None:
            continue

        if ord("1") <= key <= ord("9"):
            requested = key - ord("1")
            if requested < len(classes):
                class_index = requested
                last_status = "READY"
        elif key == ord("0"):
            class_index = 9
            last_status = "READY"
        elif key in split_keys:
            split = split_keys[key]
            last_status = "READY"
        elif key == 32:
            if existing >= target:
                last_status = "TARGET COMPLETE"
            else:
                countdown_started = now
                last_status = "GET READY"

    if writer is not None:
        writer.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()