from __future__ import annotations

import json
import time
from collections import Counter, deque

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from common import (
    MODEL_PATH,
    LABELS_PATH,
    CONFIG_PATH,
    SEQUENCE_LENGTH,
    create_video_detector,
    normalize_sequence,
    result_to_vector,
)


def stable_label(
    history: deque[str],
    minimum_count: int,
) -> str | None:
    if not history:
        return None

    label, count = Counter(history).most_common(1)[0]
    if label == "Unknown Sign":
        return None

    return label if count >= minimum_count else None


def draw_text(
    frame: np.ndarray,
    text: str,
    x: int,
    y: int,
    size: float = 0.65,
) -> None:
    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        size,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def open_camera() -> cv2.VideoCapture:
    # Prefer the default Windows backend; DirectShow is only a fallback.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(*"MJPG"),
    )
    return cap


def main() -> None:
    for required in (MODEL_PATH, LABELS_PATH, CONFIG_PATH):
        if not required.exists():
            raise FileNotFoundError(
                f"Required file not found: {required}"
            )

    labels = json.loads(
        LABELS_PATH.read_text(encoding="utf-8")
    )
    config = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )
    model = tf.keras.models.load_model(MODEL_PATH)

    confidence_threshold = float(
        config.get("confidence_threshold", 0.60)
    )
    margin_threshold = float(
        config.get("margin_threshold", 0.12)
    )
    detection_interval = int(
        config.get("detection_interval", 1)
    )
    prediction_interval = int(
        config.get("prediction_interval", 3)
    )
    smoothing_window = int(
        config.get("smoothing_window", 4)
    )
    stable_count = int(
        config.get("stable_count", 2)
    )
    detector_width = int(
        config.get("detector_width", 320)
    )
    no_hand_reset_frames = int(
        config.get("no_hand_reset_frames", 8)
    )

    cap = open_camera()

    sequence: deque[np.ndarray] = deque(
        maxlen=SEQUENCE_LENGTH
    )
    history: deque[str] = deque(
        maxlen=smoothing_window
    )
    sentence: list[str] = []

    prediction = "Waiting..."
    candidate = "Waiting..."
    confidence = 0.0
    margin = 0.0

    display_count = 0
    processed_count = 0
    no_hand_count = 0
    hand_detected = False

    start_time = time.monotonic()
    previous_timestamp = -1
    fps_count = 0
    fps_value = 0.0
    fps_start = time.monotonic()

    with create_video_detector() as detector:
        while True:
            success, frame = cap.read()
            if not success:
                break

            display_count += 1

            if display_count % detection_interval == 0:
                height, width = frame.shape[:2]
                detector_height = max(
                    1,
                    int(height * detector_width / width),
                )
                small = cv2.resize(
                    frame,
                    (detector_width, detector_height),
                    interpolation=cv2.INTER_AREA,
                )
                rgb = cv2.cvtColor(
                    small,
                    cv2.COLOR_BGR2RGB,
                )
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb,
                )

                timestamp_ms = int(
                    (time.monotonic() - start_time) * 1000
                )
                if timestamp_ms <= previous_timestamp:
                    timestamp_ms = previous_timestamp + 1
                previous_timestamp = timestamp_ms

                result = detector.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
                vector, hand_detected, _ = result_to_vector(
                    result
                )
                processed_count += 1

                if hand_detected:
                    no_hand_count = 0
                    sequence.append(vector)
                else:
                    no_hand_count += 1
                    if no_hand_count >= no_hand_reset_frames:
                        sequence.clear()
                        history.clear()
                        prediction = "No hand"
                        candidate = "No hand"
                        confidence = 0.0
                        margin = 0.0

                if (
                    hand_detected
                    and len(sequence) == SEQUENCE_LENGTH
                    and processed_count % prediction_interval == 0
                ):
                    normalized = normalize_sequence(
                        np.asarray(sequence, dtype=np.float32)
                    )
                    probabilities = model(
                        normalized[None, ...],
                        training=False,
                    ).numpy()[0]

                    order = np.argsort(probabilities)[::-1]
                    best_index = int(order[0])
                    second_index = int(order[1])

                    candidate = labels[best_index]
                    confidence = float(
                        probabilities[best_index]
                    )
                    second_confidence = float(
                        probabilities[second_index]
                    )
                    margin = confidence - second_confidence

                    accepted = (
                        confidence >= confidence_threshold
                        and margin >= margin_threshold
                    )
                    history.append(
                        candidate if accepted else "Unknown Sign"
                    )

                    new_prediction = stable_label(
                        history,
                        stable_count,
                    )
                    if new_prediction is not None:
                        prediction = new_prediction
                    elif not accepted:
                        prediction = "Unknown Sign"

            fps_count += 1
            now = time.monotonic()
            elapsed = now - fps_start
            if elapsed >= 1.0:
                fps_value = fps_count / elapsed
                fps_count = 0
                fps_start = now

            display = cv2.flip(frame, 1)
            h, w = display.shape[:2]
            cv2.rectangle(
                display,
                (0, 0),
                (w, 205),
                (20, 20, 20),
                -1,
            )

            buffer_percent = int(
                len(sequence) / SEQUENCE_LENGTH * 100
            )
            draw_text(display, f"Prediction: {prediction}", 20, 38, 0.80)
            draw_text(display, f"Candidate: {candidate}", 20, 74)
            draw_text(display, f"Confidence: {confidence:.1%}", 20, 108)
            draw_text(display, f"Margin: {margin:.1%}", 20, 140)
            draw_text(
                display,
                (
                    f"Buffer: {buffer_percent}% | "
                    f"FPS: {fps_value:.1f} | "
                    f"Hand: {'yes' if hand_detected else 'no'}"
                ),
                20,
                172,
                0.55,
            )
            draw_text(
                display,
                "Sentence: " + " ".join(sentence),
                20,
                199,
                0.55,
            )
            draw_text(
                display,
                "SPACE add | R reset sign | C clear | B delete | Q quit",
                20,
                h - 18,
                0.52,
            )

            cv2.imshow(
                "ASL Translator V3 - Motion",
                display,
            )
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == 32:
                if prediction not in {
                    "Waiting...",
                    "No hand",
                    "Unknown Sign",
                }:
                    if not sentence or sentence[-1] != prediction:
                        sentence.append(prediction)
            elif key == ord("r"):
                sequence.clear()
                history.clear()
                prediction = "Waiting..."
                candidate = "Waiting..."
                confidence = 0.0
                margin = 0.0
            elif key == ord("c"):
                sentence.clear()
                sequence.clear()
                history.clear()
                prediction = "Waiting..."
                candidate = "Waiting..."
                confidence = 0.0
                margin = 0.0
            elif key == ord("b") and sentence:
                sentence.pop()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
