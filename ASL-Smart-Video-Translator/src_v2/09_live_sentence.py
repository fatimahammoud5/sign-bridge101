from __future__ import annotations

import json
import time

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from common import (
    LABELS_PATH,
    MODEL_PATH,
    RAW_FEATURES,
    SEQUENCE_LENGTH,
    create_video_detector,
    normalize_sequence,
    result_to_vector,
)


MIN_SIGN_FRAMES = 12
END_GAP_FRAMES = 6
DETECTION_INTERVAL = 2
DETECTOR_WIDTH = 320
CONFIDENCE_THRESHOLD = 0.58
MARGIN_THRESHOLD = 0.10


ARABIC_WORDS = {
    "hello": "مرحبًا",
    "thank_you": "شكرًا",
    "please": "من فضلك",
    "sorry": "عذرًا",
    "yes": "نعم",
    "no": "لا",
    "i_love_you": "أحبك",
    "help": "ساعدني",
    "want": "أريد",
    "drink": "شراب",
}


def resample_sequence(
    frames: list[np.ndarray],
    target_length: int = SEQUENCE_LENGTH,
) -> np.ndarray:
    array = np.asarray(frames, dtype=np.float32)

    if array.ndim != 2 or array.shape[1] != RAW_FEATURES:
        raise ValueError(f"Bad sign shape: {array.shape}")

    source_positions = np.linspace(
        0,
        len(array) - 1,
        target_length,
    )
    low = np.floor(source_positions).astype(int)
    high = np.ceil(source_positions).astype(int)
    weights = source_positions - low

    output = (
        array[low] * (1.0 - weights[:, None])
        + array[high] * weights[:, None]
    )
    return output.astype(np.float32)


def natural_sentence(tokens: list[str]) -> tuple[str, str]:
    key = tuple(tokens)

    templates = {
        ("hello",): (
            "Hello.",
            "مرحبًا.",
        ),
        ("thank_you",): (
            "Thank you.",
            "شكرًا لك.",
        ),
        ("please",): (
            "Please.",
            "من فضلك.",
        ),
        ("sorry",): (
            "Sorry.",
            "عذرًا.",
        ),
        ("yes",): (
            "Yes.",
            "نعم.",
        ),
        ("no",): (
            "No.",
            "لا.",
        ),
        ("i_love_you",): (
            "I love you.",
            "أحبك.",
        ),
        ("help",): (
            "Help me.",
            "ساعدني.",
        ),
        ("want", "drink"): (
            "I want a drink.",
            "أريد أن أشرب.",
        ),
        ("please", "help"): (
            "Please help me.",
            "من فضلك ساعدني.",
        ),
        ("hello", "thank_you"): (
            "Hello, thank you.",
            "مرحبًا، شكرًا لك.",
        ),
        ("no", "thank_you"): (
            "No, thank you.",
            "لا، شكرًا.",
        ),
    }

    if key in templates:
        return templates[key]

    english = " ".join(
        token.replace("_", " ")
        for token in tokens
    )
    arabic = " ".join(
        ARABIC_WORDS.get(token, token)
        for token in tokens
    )
    return english, arabic


def put_text(
    frame: np.ndarray,
    text: str,
    y: int,
    size: float = 0.62,
) -> None:
    cv2.putText(
        frame,
        text,
        (18, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        size,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def open_camera() -> cv2.VideoCapture:
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
    labels = json.loads(
        LABELS_PATH.read_text(encoding="utf-8")
    )
    model = tf.keras.models.load_model(MODEL_PATH)

    cap = open_camera()

    sign_frames: list[np.ndarray] = []
    sentence_tokens: list[str] = []

    no_hand_count = 0
    display_count = 0
    collecting = False
    status = "Show a sign"
    last_prediction = "-"
    last_confidence = 0.0
    last_margin = 0.0

    start_time = time.monotonic()
    previous_timestamp = -1

    with create_video_detector() as detector:
        while True:
            ok, frame = cap.read()

            if not ok:
                break

            display_count += 1

            if display_count % DETECTION_INTERVAL == 0:
                height, width = frame.shape[:2]
                small_height = max(
                    1,
                    int(height * DETECTOR_WIDTH / width),
                )
                small = cv2.resize(
                    frame,
                    (DETECTOR_WIDTH, small_height),
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

                if hand_detected:
                    collecting = True
                    no_hand_count = 0
                    sign_frames.append(vector)
                    status = (
                        f"Recording sign: {len(sign_frames)} frames"
                    )

                elif collecting:
                    no_hand_count += 1
                    status = "Finishing sign..."

                    if no_hand_count >= END_GAP_FRAMES:
                        collecting = False
                        no_hand_count = 0

                        if len(sign_frames) >= MIN_SIGN_FRAMES:
                            sequence = resample_sequence(
                                sign_frames
                            )
                            normalized = normalize_sequence(
                                sequence
                            )

                            probabilities = model(
                                normalized[None, ...],
                                training=False,
                            ).numpy()[0]

                            order = np.argsort(
                                probabilities
                            )[::-1]
                            best = int(order[0])
                            second = int(order[1])

                            last_prediction = labels[best]
                            last_confidence = float(
                                probabilities[best]
                            )
                            last_margin = float(
                                probabilities[best]
                                - probabilities[second]
                            )

                            accepted = (
                                last_confidence
                                >= CONFIDENCE_THRESHOLD
                                and last_margin
                                >= MARGIN_THRESHOLD
                            )

                            if accepted:
                                if (
                                    not sentence_tokens
                                    or sentence_tokens[-1]
                                    != last_prediction
                                ):
                                    sentence_tokens.append(
                                        last_prediction
                                    )
                                status = (
                                    f"Added: {last_prediction}"
                                )
                            else:
                                status = (
                                    "Rejected: low confidence"
                                )
                        else:
                            status = (
                                "Rejected: sign too short"
                            )

                        sign_frames.clear()

            english, _ = natural_sentence(
                sentence_tokens
            )

            display = cv2.flip(frame, 1)
            h, w = display.shape[:2]

            cv2.rectangle(
                display,
                (0, 0),
                (w, 190),
                (20, 20, 20),
                -1,
            )

            put_text(
                display,
                f"Status: {status}",
                34,
            )
            put_text(
                display,
                (
                    f"Last: {last_prediction} "
                    f"({last_confidence:.1%}, "
                    f"margin {last_margin:.1%})"
                ),
                68,
                0.53,
            )
            put_text(
                display,
                "Words: "
                + " ".join(sentence_tokens),
                103,
                0.56,
            )
            put_text(
                display,
                "Sentence: " + english,
                139,
                0.56,
            )
            put_text(
                display,
                "Lower hands briefly between signs",
                173,
                0.50,
            )
            put_text(
                display,
                (
                    "ENTER print Arabic | "
                    "B delete | C clear | Q quit"
                ),
                h - 18,
                0.48,
            )

            cv2.imshow(
                "ASL Daily Phrases",
                display,
            )
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key in (10, 13):
                english, arabic = natural_sentence(
                    sentence_tokens
                )
                print("\nEnglish:", english)
                print("Arabic: ", arabic)
                print()

            elif key == ord("b") and sentence_tokens:
                sentence_tokens.pop()
                status = "Deleted last word"

            elif key == ord("c"):
                sentence_tokens.clear()
                sign_frames.clear()
                status = "Sentence cleared"
                last_prediction = "-"
                last_confidence = 0.0
                last_margin = 0.0

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
