from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SEQUENCE_LENGTH = 30
RAW_FEATURES = 126
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}


def find_data_root() -> Path:
    candidates = [
        PROJECT_ROOT / "WLASL100",
        PROJECT_ROOT / "data" / "WLASL100",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "لم أجد مجلد WLASL100.\n"
        "ضعيه إما هنا:\n"
        f"  {PROJECT_ROOT / 'WLASL100'}\n"
        "أو هنا:\n"
        f"  {PROJECT_ROOT / 'data' / 'WLASL100'}"
    )


def contains_videos(root: Path) -> bool:
    for split in ("train", "val", "test"):
        split_dir = root / split
        if not split_dir.exists():
            continue

        for path in split_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                return True

    return False


def find_video_root(data_root: Path) -> Path:
    candidates = [
        data_root / "split_videos",
        data_root,
    ]

    for candidate in candidates:
        if candidate.exists() and contains_videos(candidate):
            return candidate

    if (data_root / "split_videos").exists():
        return data_root / "split_videos"

    return data_root


DATA_ROOT = find_data_root()
VIDEO_ROOT = find_video_root(DATA_ROOT)

CLASSES_FILE = DATA_ROOT / "classes_v2.txt"
FEATURES_ROOT = DATA_ROOT / "features_v2"

MODELS_ROOT = PROJECT_ROOT / "models_v2"
MODEL_PATH = MODELS_ROOT / "asl_v2.keras"
LABELS_PATH = MODELS_ROOT / "labels_v2.json"
CONFIG_PATH = MODELS_ROOT / "config_v2.json"

HAND_MODEL_PATH = (
    PROJECT_ROOT / "models" / "mediapipe" / "hand_landmarker.task"
)


def load_classes(path: Path = CLASSES_FILE) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"ملف الأصناف غير موجود: {path}\n"
            "أنشئي classes_v2.txt وضعي فيه كلمة واحدة في كل سطر."
        )

    classes = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if len(classes) < 2:
        raise ValueError("يجب أن يحتوي classes_v2.txt على فئتين على الأقل.")

    if len(set(classes)) != len(classes):
        raise ValueError("يوجد اسم مكرر داخل classes_v2.txt.")

    return classes


def list_video_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []

    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def create_video_detector() -> vision.HandLandmarker:
    if not HAND_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"نموذج MediaPipe غير موجود: {HAND_MODEL_PATH}"
        )

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(
            model_asset_path=str(HAND_MODEL_PATH)
        ),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    return vision.HandLandmarker.create_from_options(options)


def result_to_vector(result) -> tuple[np.ndarray, bool, list[str]]:
    """
    Fixed feature order:
      Right hand = first 63 values
      Left hand  = second 63 values
    """
    hands = np.zeros((2, 21, 3), dtype=np.float32)
    labels_found: list[str] = []

    for index, landmarks in enumerate(result.hand_landmarks):
        if index >= len(result.handedness):
            continue

        handedness = result.handedness[index]
        if not handedness:
            continue

        label = handedness[0].category_name.strip().lower()

        points = np.asarray(
            [[lm.x, lm.y, lm.z] for lm in landmarks],
            dtype=np.float32,
        )

        if points.shape != (21, 3):
            continue

        if label == "right":
            slot = 0
            labels_found.append("Right")
        elif label == "left":
            slot = 1
            labels_found.append("Left")
        else:
            continue

        hands[slot] = points

    return hands.reshape(RAW_FEATURES), bool(labels_found), labels_found


def normalize_sequence(sequence: np.ndarray) -> np.ndarray:
    """
    Hybrid normalization that keeps motion information.

    For each hand and frame:
    - landmark 0 stores the wrist's absolute image position (x, y),
      centered to approximately [-1, 1].
    - landmarks 1..20 store wrist-relative hand shape, scaled by hand size.

    The older normalization subtracted the wrist from every landmark,
    including landmark 0. That made the wrist equal to zero in every
    frame and removed the hand's path through the image.
    """
    sequence = np.asarray(sequence, dtype=np.float32)

    if sequence.shape != (SEQUENCE_LENGTH, RAW_FEATURES):
        raise ValueError(
            f"Expected {(SEQUENCE_LENGTH, RAW_FEATURES)}, "
            f"received {sequence.shape}"
        )

    hands = sequence.reshape(SEQUENCE_LENGTH, 2, 21, 3).copy()
    output = np.zeros_like(hands, dtype=np.float32)

    for frame_index in range(SEQUENCE_LENGTH):
        for hand_index in range(2):
            hand = hands[frame_index, hand_index]

            if not np.any(hand):
                continue

            wrist = hand[0].copy()
            relative = hand - wrist

            distances = np.linalg.norm(relative[:, :2], axis=1)
            scale = float(np.max(distances))

            if scale > 1e-6:
                relative /= scale

            output[frame_index, hand_index] = relative

            # Preserve global wrist position so the GRU can learn motion.
            output[frame_index, hand_index, 0, 0] = (wrist[0] - 0.5) * 2.0
            output[frame_index, hand_index, 0, 1] = (wrist[1] - 0.5) * 2.0
            output[frame_index, hand_index, 0, 2] = 0.0

    normalized = output.reshape(SEQUENCE_LENGTH, RAW_FEATURES)

    if not np.isfinite(normalized).all():
        raise ValueError("Normalization produced NaN or Inf values.")

    return normalized.astype(np.float32)

def extract_video_sequence(video_path: Path) -> np.ndarray | None:
    """
    Extract one video.

    Important:
    A NEW MediaPipe VIDEO detector is created for each video.
    VIDEO mode requires timestamps to increase for the lifetime of one
    detector. Resetting timestamps while reusing the same detector caused:
    'Input timestamp must be monotonically increasing.'
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))

    if total_frames <= 0:
        cap.release()
        return None

    if not np.isfinite(fps) or fps <= 0:
        fps = 25.0

    target_indices = np.linspace(
        0,
        total_frames - 1,
        SEQUENCE_LENGTH,
    ).round().astype(int)

    sequence: list[np.ndarray] = []
    previous_timestamp = -1
    any_hand_detected = False

    # New detector for this video, so timestamps can safely start from zero.
    with create_video_detector() as detector:
        for sample_number, frame_index in enumerate(target_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            success, frame = cap.read()

            if not success:
                sequence.append(
                    np.zeros(RAW_FEATURES, dtype=np.float32)
                )
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb,
            )

            # Use the sampled frame number to guarantee strict monotonicity,
            # even when a very short video produces duplicate frame indices.
            timestamp_ms = sample_number * 40

            if timestamp_ms <= previous_timestamp:
                timestamp_ms = previous_timestamp + 1

            previous_timestamp = timestamp_ms

            result = detector.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            vector, detected, _ = result_to_vector(result)
            any_hand_detected = any_hand_detected or detected
            sequence.append(vector)

    cap.release()

    if len(sequence) != SEQUENCE_LENGTH or not any_hand_detected:
        return None

    array = np.asarray(sequence, dtype=np.float32)

    if array.shape != (SEQUENCE_LENGTH, RAW_FEATURES):
        return None

    if not np.isfinite(array).all():
        return None

    return array


def save_runtime_files(classes: Iterable[str]) -> None:
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)

    labels = list(classes)
    LABELS_PATH.write_text(
        json.dumps(labels, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    config = {
        "sequence_length": SEQUENCE_LENGTH,
        "raw_features": RAW_FEATURES,
        "confidence_threshold": 0.60,
        "margin_threshold": 0.12,
        "detection_interval": 1,
        "prediction_interval": 3,
        "smoothing_window": 4,
        "stable_count": 2,
        "detector_width": 320,
        "no_hand_reset_frames": 8,
    }

    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
