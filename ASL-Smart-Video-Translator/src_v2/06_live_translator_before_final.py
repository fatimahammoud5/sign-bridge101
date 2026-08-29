from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

SRC = ROOT / "src_v2"

MODELS = ROOT / "models_v2"

TRAIN_FILE = (
    SRC
    / "03_train_model.py"
)

RUNTIME_FILE = (
    MODELS
    / "runtime_selection_v2.json"
)

CALIBRATION_FILE = (
    MODELS
    / "calibration_runtime_v2.json"
)

HAND_MODEL_PATHS = [
    (
        ROOT
        / "models"
        / "mediapipe"
        / "hand_landmarker.task"
    ),
    (
        MODELS
        / "mediapipe"
        / "hand_landmarker.task"
    ),
    (
        MODELS
        / "hand_landmarker.task"
    ),
    (
        ROOT
        / "hand_landmarker.task"
    ),
]


# ============================================================
# CAMERA AND CAPTURE SETTINGS
# ============================================================

CAMERA_INDEX = 0

CAMERA_WIDTH = 640

CAMERA_HEIGHT = 480

CAMERA_FPS = 30


# Start recording after detecting a hand
# for this number of consecutive frames.

START_HAND_FRAMES = 2


# Finish the sign after the hands disappear
# for this number of consecutive frames.

END_NO_HAND_FRAMES = 5


# Reject captures that are too short.

MIN_CAPTURE_FRAMES = 10


# Automatically stop captures that are too long.

MAX_CAPTURE_FRAMES = 65


# Conservative limits:
# fewer random words, more Unknown results.

SAFE_CONFIDENCE = 0.55

SAFE_MARGIN = 0.08

MIN_MOTION = 0.0015


# Both selected AI models must predict
# the same word before it can be accepted.

REQUIRE_MODEL_AGREEMENT = True


# ============================================================
# LOAD SHARED TRAINING FUNCTIONS
# ============================================================

def load_training_module():

    sys.path.insert(
        0,
        str(SRC),
    )

    specification = (
        importlib.util.spec_from_file_location(
            "training_runtime",
            TRAIN_FILE,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Cannot load training file:\n"
            f"{TRAIN_FILE}"
        )

    module = (
        importlib.util.module_from_spec(
            specification
        )
    )

    specification.loader.exec_module(
        module
    )

    return module


def read_json(
    path: Path,
) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            "Missing file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(
            file
        )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Expected a JSON object:\n"
            f"{path}"
        )

    return data


training = load_training_module()

runtime = read_json(
    RUNTIME_FILE
)

calibration = read_json(
    CALIBRATION_FILE
)


labels = [
    str(item)
    for item in runtime.get(
        "classes",
        [],
    )
]

model_names = [
    str(item)
    for item in runtime.get(
        "models",
        [],
    )
]


if len(labels) != 11:
    raise ValueError(
        "Expected 11 labels, "
        f"but found {len(labels)}."
    )


if not model_names:
    raise ValueError(
        "No models were listed in "
        "runtime_selection_v2.json."
    )


if int(
    runtime.get(
        "model_features",
        -1,
    )
) != int(
    training.MODEL_FEATURES
):
    raise ValueError(
        "Runtime feature configuration "
        "does not match 03_train_model.py."
    )


confidence_limit = max(
    float(
        calibration.get(
            "confidence_threshold",
            0.50,
        )
    ),
    SAFE_CONFIDENCE,
)


margin_limit = max(
    float(
        calibration.get(
            "margin_threshold",
            0.03,
        )
    ),
    SAFE_MARGIN,
)


class_limits = calibration.get(
    "per_class_thresholds",
    {},
)


if not isinstance(
    class_limits,
    dict,
):
    class_limits = {}


# ============================================================
# LOAD SELECTED ENSEMBLE MODELS
# ============================================================

models: list[
    tf.keras.Model
] = []


print()

print(
    "=" * 70
)

print(
    "ASL SMART TRANSLATOR "
    "- FAST ENSEMBLE"
)

print(
    "=" * 70
)

print(
    "Selected AI models:"
)


for model_name in model_names:

    model_path = (
        MODELS
        / model_name
    )

    if not model_path.exists():
        raise FileNotFoundError(
            "Selected model was not found:\n"
            f"{model_path}"
        )

    model = (
        tf.keras.models.load_model(
            model_path,
            compile=False,
        )
    )

    expected_input = (
        training.SEQUENCE_LENGTH,
        training.MODEL_FEATURES,
    )

    actual_input = tuple(
        model.input_shape[
            1:
        ]
    )

    if actual_input != expected_input:
        raise ValueError(
            f"{model_name} expects "
            f"{actual_input}, "
            f"not {expected_input}."
        )

    output_count = int(
        model.output_shape[
            -1
        ]
    )

    if output_count != len(
        labels
    ):
        raise ValueError(
            f"{model_name} outputs "
            f"{output_count} classes, "
            f"but {len(labels)} labels "
            "were loaded."
        )

    models.append(
        model
    )

    print(
        " -",
        model_name,
    )


print()

print(
    "Classes:"
)


for index, label in enumerate(
    labels
):
    print(
        f"{index:02d} -> "
        f"{label}"
    )


print()

print(
    "Confidence limit: "
    f"{confidence_limit:.2f}"
)

print(
    "Margin limit:     "
    f"{margin_limit:.2f}"
)

print(
    "Model agreement:  required"
)


# Warm up models before opening camera.
# This avoids a delay on the first sign.

dummy_input = tf.zeros(
    (
        1,
        training.SEQUENCE_LENGTH,
        training.MODEL_FEATURES,
    ),
    dtype=tf.float32,
)


for model in models:

    _ = model(
        dummy_input,
        training=False,
    )


print(
    "AI models warmed up."
)


# ============================================================
# MEDIAPIPE
# ============================================================

def find_hand_model() -> Path:

    for path in HAND_MODEL_PATHS:

        if path.exists():
            return path

    searched = "\n".join(
        f" - {path}"
        for path in HAND_MODEL_PATHS
    )

    raise FileNotFoundError(
        "hand_landmarker.task "
        "was not found.\n"
        f"Searched:\n{searched}"
    )


hand_model_path = (
    find_hand_model()
)


BaseOptions = (
    mp.tasks.BaseOptions
)

HandLandmarker = (
    mp.tasks.vision
    .HandLandmarker
)

HandLandmarkerOptions = (
    mp.tasks.vision
    .HandLandmarkerOptions
)

RunningMode = (
    mp.tasks.vision
    .RunningMode
)


hand_options = (
    HandLandmarkerOptions(

        base_options=BaseOptions(
            model_asset_path=str(
                hand_model_path
            )
        ),

        running_mode=(
            RunningMode.VIDEO
        ),

        num_hands=2,

        min_hand_detection_confidence=0.50,

        min_hand_presence_confidence=0.50,

        min_tracking_confidence=0.50,
    )
)


# ============================================================
# CAMERA
# ============================================================

def open_camera():

    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW,
    )

    if not camera.isOpened():

        camera.release()

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )

    if not camera.isOpened():

        raise RuntimeError(
            "Cannot open camera."
        )

    camera.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(
            *"MJPG"
        ),
    )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH,
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT,
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        CAMERA_FPS,
    )

    camera.set(
        cv2.CAP_PROP_BUFFERSIZE,
        1,
    )

    return camera


# ============================================================
# FIXED RIGHT / LEFT HAND ORDER
# ============================================================

class HandTracker:

    def __init__(self):

        self.right = np.zeros(
            (
                21,
                3,
            ),
            dtype=np.float32,
        )

        self.left = np.zeros(
            (
                21,
                3,
            ),
            dtype=np.float32,
        )


    def reset(self):

        self.right.fill(
            0.0
        )

        self.left.fill(
            0.0
        )


    def extract(
        self,
        result,
    ):

        current_right = None

        current_left = None

        detected_count = 0


        for (
            hand_index,
            hand_landmarks,
        ) in enumerate(
            result.hand_landmarks
        ):

            if hand_index >= len(
                result.handedness
            ):
                continue

            handedness = (
                result.handedness[
                    hand_index
                ]
            )

            if not handedness:
                continue

            hand_name = (
                handedness[0]
                .category_name
                .strip()
                .lower()
            )

            landmarks = np.asarray(
                [
                    [
                        point.x,
                        point.y,
                        point.z,
                    ]
                    for point
                    in hand_landmarks
                ],
                dtype=np.float32,
            )

            if landmarks.shape != (
                21,
                3,
            ):
                continue

            detected_count += 1

            if hand_name == "right":

                current_right = (
                    landmarks
                )

            elif hand_name == "left":

                current_left = (
                    landmarks
                )


        if current_right is not None:

            self.right = (
                current_right
            )


        if current_left is not None:

            self.left = (
                current_left
            )


        features = np.concatenate(
            [
                self.right.ravel(),
                self.left.ravel(),
            ]
        ).astype(
            np.float32
        )


        expected_shape = (
            training.RAW_FEATURES,
        )


        if features.shape != expected_shape:

            raise ValueError(
                "Invalid feature shape: "
                f"{features.shape}"
            )


        return (
            features,
            detected_count > 0,
            detected_count,
        )


# ============================================================
# RESAMPLE VARIABLE SIGN TO 30 FRAMES
# ============================================================

def resample_sequence(
    captured_frames,
    target_length,
):

    source = np.asarray(
        captured_frames,
        dtype=np.float32,
    )

    if (
        source.ndim != 2
        or source.shape[1]
        != training.RAW_FEATURES
    ):
        raise ValueError(
            "Invalid captured shape: "
            f"{source.shape}"
        )

    old_positions = np.arange(
        len(source),
        dtype=np.float32,
    )

    new_positions = np.linspace(
        0,
        len(source) - 1,
        target_length,
        dtype=np.float32,
    )

    output = np.empty(
        (
            target_length,
            source.shape[1],
        ),
        dtype=np.float32,
    )


    for feature_index in range(
        source.shape[1]
    ):

        output[
            :,
            feature_index,
        ] = np.interp(
            new_positions,
            old_positions,
            source[
                :,
                feature_index,
            ],
        )


    return output


# ============================================================
# MOTION CHECK
# ============================================================

def calculate_motion_score(
    sequence,
):

    hands = sequence.reshape(
        len(sequence),
        2,
        21,
        3,
    )

    differences = np.diff(
        hands,
        axis=0,
    )

    movement = np.linalg.norm(
        differences,
        axis=3,
    )

    movement = movement[
        movement > 1e-7
    ]

    if len(movement) == 0:
        return 0.0

    return float(
        np.median(
            movement
        )
    )


# ============================================================
# ENSEMBLE AI PREDICTION
# ============================================================

def predict_sign(
    captured_frames,
):

    raw_sequence = (
        resample_sequence(
            captured_frames,
            training.SEQUENCE_LENGTH,
        )
    )

    motion = (
        calculate_motion_score(
            raw_sequence
        )
    )

    engineered_features = (
        training
        .make_motion_features(
            raw_sequence
        )
    )

    model_input = (
        tf.convert_to_tensor(
            engineered_features[
                None,
                ...,
            ],
            dtype=tf.float32,
        )
    )


    individual_probabilities = [

        model(
            model_input,
            training=False,
        ).numpy()[0]

        for model in models
    ]


    average_probabilities = np.mean(
        np.stack(
            individual_probabilities,
            axis=0,
        ),
        axis=0,
    )


    sorted_indices = np.argsort(
        average_probabilities
    )[::-1]


    first_index = int(
        sorted_indices[0]
    )

    second_index = int(
        sorted_indices[1]
    )


    label = labels[
        first_index
    ]

    second_label = labels[
        second_index
    ]


    confidence = float(
        average_probabilities[
            first_index
        ]
    )

    second_confidence = float(
        average_probabilities[
            second_index
        ]
    )

    margin = (
        confidence
        - second_confidence
    )


    votes = [

        labels[
            int(
                np.argmax(
                    probabilities
                )
            )
        ]

        for probabilities
        in individual_probabilities
    ]


    agreement = (
        len(
            set(votes)
        )
        == 1
        and votes[0]
        == label
    )


    required_confidence = max(
        confidence_limit,
        float(
            class_limits.get(
                label,
                confidence_limit,
            )
        ),
    )


    accepted = (

        confidence
        >= required_confidence

        and margin
        >= margin_limit

        and motion
        >= MIN_MOTION

        and (
            agreement
            or not
            REQUIRE_MODEL_AGREEMENT
        )
    )


    if motion < MIN_MOTION:

        reason = (
            "not enough movement"
        )

    elif (
        REQUIRE_MODEL_AGREEMENT
        and not agreement
    ):

        reason = (
            "models disagree"
        )

    elif confidence < required_confidence:

        reason = (
            "low confidence"
        )

    elif margin < margin_limit:

        reason = (
            "small margin"
        )

    else:

        reason = (
            "accepted"
        )


    return {

        "accepted":
            accepted,

        "label":
            label,

        "second":
            second_label,

        "confidence":
            confidence,

        "margin":
            margin,

        "required":
            required_confidence,

        "reason":
            reason,
    }


# ============================================================
# USER INTERFACE
# ============================================================

def put_text(
    frame,
    text,
    x,
    y,
    scale=0.55,
    thickness=2,
):

    cv2.putText(
        frame,
        text,
        (
            x,
            y,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (
            255,
            255,
            255,
        ),
        thickness,
        cv2.LINE_AA,
    )


def draw_interface(
    frame,
    state,
    result,
    captured_count,
    sentence_words,
    hand_count,
    fps,
):

    height, width = (
        frame.shape[
            :2
        ]
    )


    cv2.rectangle(
        frame,
        (
            0,
            0,
        ),
        (
            width,
            215,
        ),
        (
            22,
            22,
            22,
        ),
        -1,
    )


    put_text(
        frame,
        f"State: {state}",
        15,
        31,
        0.68,
    )


    put_text(
        frame,
        (
            f"Hands: {hand_count} | "
            f"Frames: {captured_count} | "
            f"FPS: {fps:.1f}"
        ),
        15,
        62,
        0.52,
    )


    if result is None:

        shown_prediction = (
            "Waiting..."
        )

        confidence_text = (
            "Confidence: --"
        )

        details_text = (
            "Show one sign, "
            "then lower your hands."
        )

    else:

        if result[
            "accepted"
        ]:

            shown_prediction = (
                result[
                    "label"
                ]
            )

        else:

            shown_prediction = (
                "Unknown Sign"
            )


        confidence_text = (

            f"Confidence: "
            f"{result['confidence']:.1%} | "

            f"Required: "
            f"{result['required']:.1%}"
        )


        details_text = (

            f"Top: "
            f"{result['label']} | "

            f"Second: "
            f"{result['second']} | "

            f"Margin: "
            f"{result['margin']:.1%} | "

            f"{result['reason']}"
        )


    put_text(
        frame,
        (
            "Prediction: "
            + shown_prediction
        ),
        15,
        101,
        0.78,
    )


    put_text(
        frame,
        confidence_text,
        15,
        136,
        0.54,
    )


    put_text(
        frame,
        details_text,
        15,
        169,
        0.45,
        1,
    )


    sentence_text = " ".join(
        sentence_words
    )


    if len(
        sentence_text
    ) > 58:

        sentence_text = (
            sentence_text[
                -58:
            ]
        )


    put_text(
        frame,
        (
            "Sentence: "
            + sentence_text
        ),
        15,
        203,
        0.56,
    )


    cv2.rectangle(
        frame,
        (
            0,
            height - 44,
        ),
        (
            width,
            height,
        ),
        (
            22,
            22,
            22,
        ),
        -1,
    )


    put_text(
        frame,
        (
            "SPACE Add | "
            "B Delete | "
            "C Clear | "
            "R Reset | "
            "Q Quit"
        ),
        12,
        height - 15,
        0.46,
        1,
    )


    if hand_count:

        indicator_color = (
            0,
            220,
            0,
        )

    else:

        indicator_color = (
            0,
            0,
            220,
        )


    cv2.circle(
        frame,
        (
            width - 23,
            26,
        ),
        9,
        indicator_color,
        -1,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    camera = open_camera()

    tracker = HandTracker()


    sentence_words = []

    captured_frames = []

    current_result = None


    recording = False

    locked = False


    hand_streak = 0

    no_hand_streak = 0


    state = (
        "WAITING"
    )


    start_time = (
        time.perf_counter()
    )

    previous_timestamp = -1


    fps = 0.0

    fps_frames = 0

    fps_start = (
        time.perf_counter()
    )


    print()

    print(
        "Usage:"
    )

    print(
        "1. Keep hands outside the frame."
    )

    print(
        "2. Perform one sign."
    )

    print(
        "3. Lower hands to finish."
    )

    print(
        "4. SPACE adds an accepted word."
    )

    print(
        "5. Q quits."
    )

    print()


    try:

        with (
            HandLandmarker
            .create_from_options(
                hand_options
            )
        ) as detector:


            while True:

                success, raw_frame = (
                    camera.read()
                )


                if not success:

                    print(
                        "ERROR: "
                        "Cannot read camera frame."
                    )

                    break


                fps_frames += 1

                now = (
                    time.perf_counter()
                )


                if (
                    now - fps_start
                    >= 1.0
                ):

                    fps = (
                        fps_frames
                        / (
                            now
                            - fps_start
                        )
                    )

                    fps_frames = 0

                    fps_start = now


                # Detection uses original frame,
                # matching the training videos.

                rgb_frame = cv2.cvtColor(
                    raw_frame,
                    cv2.COLOR_BGR2RGB,
                )


                mp_image = mp.Image(
                    image_format=(
                        mp.ImageFormat.SRGB
                    ),
                    data=rgb_frame,
                )


                timestamp = int(
                    (
                        time.perf_counter()
                        - start_time
                    )
                    * 1000
                )


                if timestamp <= (
                    previous_timestamp
                ):

                    timestamp = (
                        previous_timestamp
                        + 1
                    )


                previous_timestamp = (
                    timestamp
                )


                detection = (
                    detector.detect_for_video(
                        mp_image,
                        timestamp,
                    )
                )


                (
                    features,
                    has_hand,
                    hand_count,
                ) = tracker.extract(
                    detection
                )


                # --------------------------------------------
                # HANDS ARE VISIBLE
                # --------------------------------------------

                if has_hand:

                    hand_streak += 1

                    no_hand_streak = 0


                    if locked:

                        state = (
                            "LOWER HANDS"
                        )


                    elif (
                        not recording
                        and hand_streak
                        >= START_HAND_FRAMES
                    ):

                        recording = True

                        captured_frames = []

                        current_result = None

                        state = (
                            "RECORDING"
                        )


                    if recording:

                        captured_frames.append(
                            features.copy()
                        )

                        state = (
                            "RECORDING"
                        )


                        if (
                            len(
                                captured_frames
                            )
                            >= MAX_CAPTURE_FRAMES
                        ):

                            current_result = (
                                predict_sign(
                                    captured_frames
                                )
                            )

                            recording = False

                            locked = True


                            if current_result[
                                "accepted"
                            ]:

                                state = (
                                    "ACCEPTED"
                                )

                            else:

                                state = (
                                    "UNKNOWN"
                                )


                # --------------------------------------------
                # HANDS ARE NOT VISIBLE
                # --------------------------------------------

                else:

                    hand_streak = 0

                    no_hand_streak += 1


                    if recording:

                        state = (
                            "FINISHING"
                        )


                        if (
                            no_hand_streak
                            >= END_NO_HAND_FRAMES
                        ):


                            if (
                                len(
                                    captured_frames
                                )
                                >= MIN_CAPTURE_FRAMES
                            ):

                                current_result = (
                                    predict_sign(
                                        captured_frames
                                    )
                                )


                                if current_result[
                                    "accepted"
                                ]:

                                    state = (
                                        "ACCEPTED"
                                    )

                                else:

                                    state = (
                                        "UNKNOWN"
                                    )


                            else:

                                current_result = {

                                    "accepted":
                                        False,

                                    "label":
                                        "",

                                    "second":
                                        "",

                                    "confidence":
                                        0.0,

                                    "margin":
                                        0.0,

                                    "required":
                                        confidence_limit,

                                    "reason":
                                        "sign too short",
                                }

                                state = (
                                    "TOO SHORT"
                                )


                            recording = False

                            captured_frames = []

                            locked = False

                            tracker.reset()


                    elif (
                        no_hand_streak
                        >= END_NO_HAND_FRAMES
                    ):

                        locked = False

                        tracker.reset()


                        if current_result is None:

                            state = (
                                "WAITING"
                            )


                # Mirror display only.
                # MediaPipe detection was not mirrored.

                display_frame = cv2.flip(
                    raw_frame,
                    1,
                )


                draw_interface(
                    display_frame,
                    state,
                    current_result,
                    len(
                        captured_frames
                    ),
                    sentence_words,
                    hand_count,
                    fps,
                )


                cv2.imshow(
                    (
                        "ASL Smart Translator "
                        "- Fast Ensemble"
                    ),
                    display_frame,
                )


                key = (
                    cv2.waitKey(
                        1
                    )
                    & 0xFF
                )


                # Quit

                if key == ord(
                    "q"
                ):

                    break


                # Reset recognition

                if key == ord(
                    "r"
                ):

                    recording = False

                    locked = False

                    hand_streak = 0

                    no_hand_streak = 0

                    captured_frames = []

                    current_result = None

                    tracker.reset()

                    state = (
                        "WAITING"
                    )


                # Clear sentence

                elif key == ord(
                    "c"
                ):

                    sentence_words.clear()


                # Delete last word

                elif key == ord(
                    "b"
                ):

                    if sentence_words:

                        sentence_words.pop()


                # Add accepted word

                elif key == 32:

                    if (
                        current_result
                        is not None

                        and current_result[
                            "accepted"
                        ]
                    ):

                        word = (
                            current_result[
                                "label"
                            ]
                        )


                        if (
                            not sentence_words

                            or sentence_words[
                                -1
                            ]
                            != word
                        ):

                            sentence_words.append(
                                word
                            )

                            print(
                                "Added:",
                                word,
                            )


    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":

    main()