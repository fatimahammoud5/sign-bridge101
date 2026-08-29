from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
import time

from collections import deque
from pathlib import Path

# Reduce TensorFlow console messages.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_ROOT = (
    PROJECT_ROOT
    / "src_v2"
)

MODELS_ROOT = (
    PROJECT_ROOT
    / "models_v2"
)

TRAIN_FILE = (
    SRC_ROOT
    / "03_train_model.py"
)

MODEL_PATH = (
    MODELS_ROOT
    / "asl_v2_improved.keras"
)

CALIBRATION_PATH = (
    MODELS_ROOT
    / "calibration_v2.json"
)


# ============================================================
# MEDIAPIPE MODEL LOCATIONS
# ============================================================

HAND_MODEL_CANDIDATES = [
    (
        PROJECT_ROOT
        / "models"
        / "mediapipe"
        / "hand_landmarker.task"
    ),
    (
        MODELS_ROOT
        / "mediapipe"
        / "hand_landmarker.task"
    ),
    (
        MODELS_ROOT
        / "hand_landmarker.task"
    ),
    (
        PROJECT_ROOT
        / "hand_landmarker.task"
    ),
]


# ============================================================
# CAMERA SETTINGS
# ============================================================

CAMERA_INDEX = 0

CAMERA_WIDTH = 640

CAMERA_HEIGHT = 480

CAMERA_FPS = 30


# ============================================================
# AUTOMATIC SIGN SEGMENTATION
# ============================================================

# Frames preserved before movement begins.
PRE_ROLL_FRAMES = 6

# Minimum number of captured frames.
MIN_CAPTURE_FRAMES = 13

# Maximum capture length.
MAX_CAPTURE_FRAMES = 48

# Number of moving frames required to start.
START_MOTION_FRAMES = 2

# Number of nearly still frames required to finish.
END_STILL_FRAMES = 7

# Movement necessary to begin recording.
START_MOTION_THRESHOLD = 0.0038

# Movement below this value means the sign is ending.
STOP_MOTION_THRESHOLD = 0.0018

# Brief pause before accepting a new sign.
RESULT_COOLDOWN_SECONDS = 0.45


# ============================================================
# LIVE REJECTION SETTINGS
# ============================================================

# These are deliberately stricter than the validation values.
# This reduces random predictions.

MIN_LIVE_CONFIDENCE = 0.50

MIN_LIVE_MARGIN = 0.06

# Number of temporal versions evaluated for each captured sign.
# Three predictions are made in one TensorFlow batch.
USE_TEMPORAL_VOTING = True


# ============================================================
# LOAD TRAINING FUNCTIONS
# ============================================================

def load_training_module():
    """
    Load make_motion_features() and the project configuration
    from 03_train_model.py without running training again.
    """

    sys.path.insert(
        0,
        str(SRC_ROOT),
    )

    specification = (
        importlib.util.spec_from_file_location(
            "asl_training_runtime",
            TRAIN_FILE,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Could not load:\n"
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


training = load_training_module()


# ============================================================
# JSON
# ============================================================

def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        return {}

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        value = json.load(file)

    if not isinstance(
        value,
        dict,
    ):
        return {}

    return value


# ============================================================
# LOAD CLASSES
# ============================================================

CLASSES = training.load_classes()

EXPECTED_CLASSES = [
    "computer",
    "yes",
    "no",
    "help",
    "need",
    "who",
    "hello",
    "please",
    "where",
    "why",
    "stop",
]


if CLASSES != EXPECTED_CLASSES:
    raise ValueError(
        "The loaded classes are not the final classes.\n"
        f"Loaded:   {CLASSES}\n"
        f"Expected: {EXPECTED_CLASSES}"
    )


# ============================================================
# LOAD CALIBRATION
# ============================================================

calibration = load_json(
    CALIBRATION_PATH
)

calibrated_confidence = float(
    calibration.get(
        "confidence_threshold",
        0.35,
    )
)

calibrated_margin = float(
    calibration.get(
        "margin_threshold",
        0.03,
    )
)

CONFIDENCE_THRESHOLD = max(
    calibrated_confidence,
    MIN_LIVE_CONFIDENCE,
)

MARGIN_THRESHOLD = max(
    calibrated_margin,
    MIN_LIVE_MARGIN,
)

per_class_thresholds = calibration.get(
    "per_class_thresholds",
    {},
)

if not isinstance(
    per_class_thresholds,
    dict,
):
    per_class_thresholds = {}


# ============================================================
# LOAD MODEL
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Improved model was not found:\n"
        f"{MODEL_PATH}"
    )


model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False,
)


expected_model_input = (
    training.SEQUENCE_LENGTH,
    training.MODEL_FEATURES,
)

actual_model_input = tuple(
    model.input_shape[1:]
)

if actual_model_input != expected_model_input:
    raise ValueError(
        "Model input does not match training features.\n"
        f"Model:    {actual_model_input}\n"
        f"Expected: {expected_model_input}"
    )


if int(
    model.output_shape[-1]
) != len(CLASSES):
    raise ValueError(
        "Model output count does not match classes."
    )


# Warm up TensorFlow before opening the camera.
dummy_input = tf.zeros(
    (
        1,
        training.SEQUENCE_LENGTH,
        training.MODEL_FEATURES,
    ),
    dtype=tf.float32,
)

_ = model(
    dummy_input,
    training=False,
)


# ============================================================
# FIND HAND LANDMARKER MODEL
# ============================================================

def find_hand_model() -> Path:
    for path in HAND_MODEL_CANDIDATES:
        if path.exists():
            return path

    searched = "\n".join(
        f" - {path}"
        for path in HAND_MODEL_CANDIDATES
    )

    raise FileNotFoundError(
        "hand_landmarker.task was not found.\n"
        f"Searched:\n{searched}"
    )


HAND_MODEL_PATH = find_hand_model()


# ============================================================
# MEDIAPIPE CONFIGURATION
# ============================================================

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = (
    mp.tasks.vision.HandLandmarker
)

HandLandmarkerOptions = (
    mp.tasks.vision.HandLandmarkerOptions
)

RunningMode = (
    mp.tasks.vision.RunningMode
)


hand_options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(
            HAND_MODEL_PATH
        )
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.50,
    min_hand_presence_confidence=0.50,
    min_tracking_confidence=0.50,
)


# ============================================================
# LATEST-FRAME CAMERA
# ============================================================

class LatestFrameCamera:
    """
    Continuously reads the camera in a separate thread.

    The main program always receives the newest frame instead
    of processing delayed frames stored in the camera buffer.
    """

    def __init__(
        self,
        camera_index: int,
    ):
        self.capture = cv2.VideoCapture(
            camera_index,
            cv2.CAP_DSHOW,
        )

        if not self.capture.isOpened():
            self.capture.release()

            self.capture = cv2.VideoCapture(
                camera_index
            )

        if not self.capture.isOpened():
            raise RuntimeError(
                "Could not open the camera."
            )

        self.capture.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(
                *"MJPG"
            ),
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH,
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT,
        )

        self.capture.set(
            cv2.CAP_PROP_FPS,
            CAMERA_FPS,
        )

        self.capture.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )

        self.lock = threading.Lock()

        self.running = True

        self.frame = None

        self.frame_number = 0

        self.thread = threading.Thread(
            target=self._reader,
            daemon=True,
        )

        self.thread.start()


    def _reader(self):
        while self.running:
            success, frame = (
                self.capture.read()
            )

            if not success:
                time.sleep(0.01)
                continue

            with self.lock:
                self.frame = frame
                self.frame_number += 1


    def read(
        self,
    ) -> tuple[
        int,
        np.ndarray | None,
    ]:
        with self.lock:
            if self.frame is None:
                return (
                    self.frame_number,
                    None,
                )

            return (
                self.frame_number,
                self.frame.copy(),
            )


    def release(self):
        self.running = False

        if self.thread.is_alive():
            self.thread.join(
                timeout=1.0
            )

        self.capture.release()


# ============================================================
# FIXED RIGHT / LEFT FEATURE EXTRACTION
# ============================================================

class HandFeatureExtractor:
    """
    Extract features in exactly this order:

        Right hand: 63 values
        Left hand:  63 values

    Missing landmarks retain the last detected position during
    a sign, matching the ASL Citizen extraction pipeline.
    """

    def __init__(self):
        self.right = np.zeros(
            (21, 3),
            dtype=np.float32,
        )

        self.left = np.zeros(
            (21, 3),
            dtype=np.float32,
        )


    def reset(self):
        self.right.fill(0.0)
        self.left.fill(0.0)


    def extract(
        self,
        result,
    ) -> tuple[
        np.ndarray,
        bool,
        int,
    ]:
        current_right = None

        current_left = None

        detected_hands = 0

        for hand_index, landmarks_list in enumerate(
            result.hand_landmarks
        ):
            if hand_index >= len(
                result.handedness
            ):
                continue

            handedness_items = (
                result.handedness[
                    hand_index
                ]
            )

            if not handedness_items:
                continue

            hand_name = (
                handedness_items[0]
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
                    for point in landmarks_list
                ],
                dtype=np.float32,
            )

            if landmarks.shape != (
                21,
                3,
            ):
                continue

            detected_hands += 1

            if hand_name == "right":
                current_right = landmarks

            elif hand_name == "left":
                current_left = landmarks

        if current_right is not None:
            self.right = current_right

        if current_left is not None:
            self.left = current_left

        features = np.concatenate(
            [
                self.right.reshape(-1),
                self.left.reshape(-1),
            ]
        ).astype(np.float32)

        if features.shape != (
            training.RAW_FEATURES,
        ):
            raise ValueError(
                "Unexpected raw feature shape: "
                f"{features.shape}"
            )

        return (
            features,
            detected_hands > 0,
            detected_hands,
        )


# ============================================================
# FRAME MOTION
# ============================================================

def calculate_frame_motion(
    previous_features: np.ndarray | None,
    current_features: np.ndarray,
) -> float:
    """
    Measure landmark displacement between two camera frames.

    The upper quarter of landmark movements is used so that
    movement from one active hand is not hidden by a still hand.
    """

    if previous_features is None:
        return 0.0

    previous = previous_features.reshape(
        2,
        21,
        3,
    )

    current = current_features.reshape(
        2,
        21,
        3,
    )

    previous_present = np.any(
        np.abs(previous) > 1e-8,
        axis=(1, 2),
    )

    current_present = np.any(
        np.abs(current) > 1e-8,
        axis=(1, 2),
    )

    common_hands = (
        previous_present
        & current_present
    )

    movements: list[np.ndarray] = []

    for hand_index in range(2):
        if not common_hands[
            hand_index
        ]:
            continue

        difference = (
            current[
                hand_index,
                :,
                :2,
            ]
            - previous[
                hand_index,
                :,
                :2,
            ]
        )

        distances = np.linalg.norm(
            difference,
            axis=1,
        )

        movements.append(
            distances
        )

    if not movements:
        return 0.0

    values = np.concatenate(
        movements
    )

    values = values[
        np.isfinite(values)
    ]

    if len(values) == 0:
        return 0.0

    return float(
        np.percentile(
            values,
            75,
        )
    )


# ============================================================
# TEMPORAL RESAMPLING
# ============================================================

def resample_sequence(
    frames: list[np.ndarray],
    target_length: int,
) -> np.ndarray:
    source = np.asarray(
        frames,
        dtype=np.float32,
    )

    if (
        source.ndim != 2
        or source.shape[1]
        != training.RAW_FEATURES
    ):
        raise ValueError(
            "Invalid captured sequence shape: "
            f"{source.shape}"
        )

    if len(source) == 1:
        return np.repeat(
            source,
            target_length,
            axis=0,
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
            training.RAW_FEATURES,
        ),
        dtype=np.float32,
    )

    for feature_index in range(
        training.RAW_FEATURES
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
# TEMPORAL VERSIONS
# ============================================================

def create_temporal_versions(
    captured_frames: list[np.ndarray],
) -> list[np.ndarray]:
    """
    Evaluate several slightly different temporal boundaries.

    This reduces sensitivity to one extra still frame at the
    beginning or end of a sign.
    """

    versions = [
        resample_sequence(
            captured_frames,
            training.SEQUENCE_LENGTH,
        )
    ]

    if (
        USE_TEMPORAL_VOTING
        and len(captured_frames) >= 18
    ):
        trim_small = max(
            1,
            int(
                len(captured_frames)
                * 0.06
            ),
        )

        if (
            len(captured_frames)
            - 2 * trim_small
            >= MIN_CAPTURE_FRAMES
        ):
            versions.append(
                resample_sequence(
                    captured_frames[
                        trim_small:
                        -trim_small
                    ],
                    training.SEQUENCE_LENGTH,
                )
            )

        trim_start = max(
            1,
            int(
                len(captured_frames)
                * 0.10
            ),
        )

        if (
            len(captured_frames)
            - trim_start
            >= MIN_CAPTURE_FRAMES
        ):
            versions.append(
                resample_sequence(
                    captured_frames[
                        trim_start:
                    ],
                    training.SEQUENCE_LENGTH,
                )
            )

    return versions


# ============================================================
# AI PREDICTION
# ============================================================

def predict_sign(
    captured_frames: list[np.ndarray],
) -> dict:
    versions = create_temporal_versions(
        captured_frames
    )

    engineered = np.asarray(
        [
            training.make_motion_features(
                version
            )
            for version in versions
        ],
        dtype=np.float32,
    )

    tensor = tf.convert_to_tensor(
        engineered,
        dtype=tf.float32,
    )

    all_probabilities = model(
        tensor,
        training=False,
    ).numpy()

    probabilities = np.mean(
        all_probabilities,
        axis=0,
    )

    sorted_indices = np.argsort(
        probabilities
    )[::-1]

    first_index = int(
        sorted_indices[0]
    )

    second_index = int(
        sorted_indices[1]
    )

    third_index = int(
        sorted_indices[2]
    )

    label = CLASSES[
        first_index
    ]

    confidence = float(
        probabilities[
            first_index
        ]
    )

    second_confidence = float(
        probabilities[
            second_index
        ]
    )

    margin = (
        confidence
        - second_confidence
    )

    class_threshold = float(
        per_class_thresholds.get(
            label,
            CONFIDENCE_THRESHOLD,
        )
    )

    required_confidence = max(
        CONFIDENCE_THRESHOLD,
        class_threshold,
    )

    # Confirm that temporal versions agree.
    temporal_votes = [
        int(np.argmax(item))
        for item in all_probabilities
    ]

    vote_count = sum(
        vote == first_index
        for vote in temporal_votes
    )

    required_votes = (
        2
        if len(temporal_votes) >= 3
        else 1
    )

    accepted = (
        confidence
        >= required_confidence
        and margin
        >= MARGIN_THRESHOLD
        and vote_count
        >= required_votes
    )

    if confidence < required_confidence:
        reason = "low confidence"

    elif margin < MARGIN_THRESHOLD:
        reason = "small margin"

    elif vote_count < required_votes:
        reason = "temporal disagreement"

    else:
        reason = "accepted"

    return {
        "accepted":
            bool(accepted),

        "label":
            label,

        "confidence":
            confidence,

        "margin":
            margin,

        "required_confidence":
            required_confidence,

        "reason":
            reason,

        "votes":
            f"{vote_count}/{len(temporal_votes)}",

        "top_three": [
            (
                CLASSES[first_index],
                float(
                    probabilities[
                        first_index
                    ]
                ),
            ),
            (
                CLASSES[second_index],
                float(
                    probabilities[
                        second_index
                    ]
                ),
            ),
            (
                CLASSES[third_index],
                float(
                    probabilities[
                        third_index
                    ]
                ),
            ),
        ],
    }


# ============================================================
# DRAW HAND POINTS
# ============================================================

def draw_detected_hands(
    frame: np.ndarray,
    detection_result,
) -> None:
    height, width = frame.shape[:2]

    for hand_landmarks in (
        detection_result.hand_landmarks
    ):
        for point in hand_landmarks:
            # The display frame is mirrored.
            x = int(
                (1.0 - point.x)
                * width
            )

            y = int(
                point.y
                * height
            )

            cv2.circle(
                frame,
                (x, y),
                2,
                (0, 220, 0),
                -1,
            )


# ============================================================
# TEXT DRAWING
# ============================================================

def put_text(
    frame: np.ndarray,
    text: str,
    x: int,
    y: int,
    scale: float = 0.55,
    thickness: int = 1,
) -> None:
    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def draw_interface(
    frame: np.ndarray,
    state: str,
    result: dict | None,
    motion: float,
    captured_count: int,
    hand_count: int,
    fps: float,
    sentence: list[str],
) -> None:
    height, width = frame.shape[:2]

    cv2.rectangle(
        frame,
        (0, 0),
        (width, 218),
        (25, 25, 25),
        -1,
    )

    put_text(
        frame,
        f"State: {state}",
        15,
        28,
        0.64,
        2,
    )

    put_text(
        frame,
        (
            f"Hands: {hand_count} | "
            f"Motion: {motion:.4f} | "
            f"Frames: {captured_count} | "
            f"FPS: {fps:.1f}"
        ),
        15,
        57,
        0.45,
    )

    if result is None:
        prediction_text = "Waiting for movement..."

        confidence_text = (
            "Move naturally to perform one sign."
        )

        details_text = (
            "The sign ends automatically "
            "when movement becomes still."
        )

        top_text = ""

    else:
        if result["accepted"]:
            prediction_text = (
                result["label"]
            )
        else:
            prediction_text = (
                "Unknown Sign"
            )

        confidence_text = (
            f"Confidence: "
            f"{result['confidence']:.1%} | "
            f"Required: "
            f"{result['required_confidence']:.1%} | "
            f"Margin: "
            f"{result['margin']:.1%}"
        )

        details_text = (
            f"Status: {result['reason']} | "
            f"Temporal votes: {result['votes']}"
        )

        top_text = " | ".join(
            (
                f"{label}:"
                f"{probability:.0%}"
            )
            for label, probability
            in result["top_three"]
        )

    put_text(
        frame,
        f"Prediction: {prediction_text}",
        15,
        96,
        0.78,
        2,
    )

    put_text(
        frame,
        confidence_text,
        15,
        128,
        0.50,
    )

    put_text(
        frame,
        details_text,
        15,
        157,
        0.47,
    )

    put_text(
        frame,
        top_text,
        15,
        184,
        0.43,
    )

    sentence_text = " ".join(
        sentence
    )

    if len(sentence_text) > 58:
        sentence_text = (
            sentence_text[-58:]
        )

    put_text(
        frame,
        f"Sentence: {sentence_text}",
        15,
        211,
        0.50,
    )

    cv2.rectangle(
        frame,
        (0, height - 40),
        (width, height),
        (25, 25, 25),
        -1,
    )

    put_text(
        frame,
        (
            "SPACE Add | B Delete | "
            "C Clear | R Reset | Q Quit"
        ),
        12,
        height - 14,
        0.44,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 72)

    print(
        "ASL SMART TRANSLATOR "
        "- FINAL FAST MODEL"
    )

    print("=" * 72)

    print(
        "Model:",
        MODEL_PATH,
    )

    print(
        "Hand model:",
        HAND_MODEL_PATH,
    )

    print(
        "Input:",
        model.input_shape,
    )

    print(
        "Confidence threshold:",
        f"{CONFIDENCE_THRESHOLD:.2f}",
    )

    print(
        "Margin threshold:",
        f"{MARGIN_THRESHOLD:.2f}",
    )

    print()

    print("Final classes:")

    for index, class_name in enumerate(
        CLASSES
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    print()

    print(
        "The AI model is ready."
    )

    print(
        "Start moving to perform a sign."
    )

    print(
        "The result appears when movement stops."
    )

    camera = LatestFrameCamera(
        CAMERA_INDEX
    )

    extractor = (
        HandFeatureExtractor()
    )

    pre_roll = deque(
        maxlen=PRE_ROLL_FRAMES
    )

    captured_frames: list[
        np.ndarray
    ] = []

    sentence: list[str] = []

    previous_features = None

    last_result = None

    recording = False

    movement_streak = 0

    still_streak = 0

    no_hand_streak = 0

    cooldown_until = 0.0

    state = "WAITING"

    last_camera_frame_number = -1

    previous_timestamp = -1

    start_time = time.perf_counter()

    fps = 0.0

    fps_counter = 0

    fps_start = time.perf_counter()

    try:
        with HandLandmarker.create_from_options(
            hand_options
        ) as detector:

            while True:
                (
                    camera_frame_number,
                    raw_frame,
                ) = camera.read()

                if raw_frame is None:
                    time.sleep(0.005)
                    continue

                # Do not process the same camera frame twice.
                if (
                    camera_frame_number
                    == last_camera_frame_number
                ):
                    time.sleep(0.001)
                    continue

                last_camera_frame_number = (
                    camera_frame_number
                )

                current_time = (
                    time.perf_counter()
                )

                fps_counter += 1

                if (
                    current_time
                    - fps_start
                    >= 1.0
                ):
                    fps = (
                        fps_counter
                        / (
                            current_time
                            - fps_start
                        )
                    )

                    fps_counter = 0

                    fps_start = current_time

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
                        current_time
                        - start_time
                    )
                    * 1000
                )

                if timestamp <= previous_timestamp:
                    timestamp = (
                        previous_timestamp
                        + 1
                    )

                previous_timestamp = timestamp

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
                ) = extractor.extract(
                    detection
                )

                if has_hand:
                    no_hand_streak = 0

                    motion = (
                        calculate_frame_motion(
                            previous_features,
                            features,
                        )
                    )

                    previous_features = (
                        features.copy()
                    )

                else:
                    no_hand_streak += 1

                    motion = 0.0

                # ------------------------------------------------
                # WAITING FOR SIGN MOVEMENT
                # ------------------------------------------------

                if not recording:
                    if has_hand:
                        pre_roll.append(
                            features.copy()
                        )

                        if (
                            current_time
                            >= cooldown_until
                        ):
                            if (
                                motion
                                >= START_MOTION_THRESHOLD
                            ):
                                movement_streak += 1

                            else:
                                movement_streak = max(
                                    0,
                                    movement_streak - 1,
                                )

                            if (
                                movement_streak
                                >= START_MOTION_FRAMES
                            ):
                                recording = True

                                captured_frames = list(
                                    pre_roll
                                )

                                still_streak = 0

                                movement_streak = 0

                                state = "RECORDING"

                    else:
                        movement_streak = 0

                        if no_hand_streak >= 3:
                            pre_roll.clear()

                            previous_features = None

                            extractor.reset()

                        if (
                            current_time
                            >= cooldown_until
                        ):
                            state = "WAITING"

                # ------------------------------------------------
                # RECORDING ACTIVE SIGN
                # ------------------------------------------------

                else:
                    captured_frames.append(
                        features.copy()
                    )

                    if not has_hand:
                        still_streak += 2

                    elif (
                        motion
                        <= STOP_MOTION_THRESHOLD
                    ):
                        still_streak += 1

                    else:
                        still_streak = 0

                    state = "RECORDING"

                    long_enough = (
                        len(captured_frames)
                        >= MIN_CAPTURE_FRAMES
                    )

                    ended_by_stillness = (
                        long_enough
                        and still_streak
                        >= END_STILL_FRAMES
                    )

                    ended_by_limit = (
                        len(captured_frames)
                        >= MAX_CAPTURE_FRAMES
                    )

                    if (
                        ended_by_stillness
                        or ended_by_limit
                    ):
                        # Remove most trailing still frames while
                        # retaining two frames from the final pose.

                        removable_still = max(
                            0,
                            still_streak - 2,
                        )

                        usable_length = max(
                            MIN_CAPTURE_FRAMES,
                            len(captured_frames)
                            - removable_still,
                        )

                        sign_frames = (
                            captured_frames[
                                :usable_length
                            ]
                        )

                        try:
                            last_result = (
                                predict_sign(
                                    sign_frames
                                )
                            )

                            if last_result[
                                "accepted"
                            ]:
                                state = "ACCEPTED"

                                print(
                                    "Accepted:",
                                    last_result[
                                        "label"
                                    ],
                                    (
                                        f"confidence="
                                        f"{last_result['confidence']:.1%}"
                                    ),
                                )

                            else:
                                state = "UNKNOWN"

                                print(
                                    "Rejected:",
                                    last_result[
                                        "label"
                                    ],
                                    (
                                        f"confidence="
                                        f"{last_result['confidence']:.1%}"
                                    ),
                                    (
                                        f"reason="
                                        f"{last_result['reason']}"
                                    ),
                                )

                        except Exception as exc:
                            print(
                                "Prediction error:",
                                exc,
                            )

                            last_result = None

                            state = "ERROR"

                        recording = False

                        captured_frames = []

                        pre_roll.clear()

                        movement_streak = 0

                        still_streak = 0

                        cooldown_until = (
                            current_time
                            + RESULT_COOLDOWN_SECONDS
                        )

                # ------------------------------------------------
                # DISPLAY
                # ------------------------------------------------

                display_frame = cv2.flip(
                    raw_frame,
                    1,
                )

                draw_detected_hands(
                    display_frame,
                    detection,
                )

                draw_interface(
                    display_frame,
                    state,
                    last_result,
                    motion,
                    len(captured_frames),
                    hand_count,
                    fps,
                    sentence,
                )

                cv2.imshow(
                    (
                        "ASL Smart Translator "
                        "- Final Fast Model"
                    ),
                    display_frame,
                )

                key = (
                    cv2.waitKey(1)
                    & 0xFF
                )

                if key == ord("q"):
                    break

                elif key == ord("r"):
                    pre_roll.clear()

                    captured_frames = []

                    previous_features = None

                    last_result = None

                    recording = False

                    movement_streak = 0

                    still_streak = 0

                    no_hand_streak = 0

                    cooldown_until = 0.0

                    state = "WAITING"

                    extractor.reset()

                elif key == ord("c"):
                    sentence.clear()

                elif key == ord("b"):
                    if sentence:
                        sentence.pop()

                elif key == 32:
                    if (
                        last_result is not None
                        and last_result[
                            "accepted"
                        ]
                    ):
                        word = last_result[
                            "label"
                        ]

                        if (
                            not sentence
                            or sentence[-1]
                            != word
                        ):
                            sentence.append(
                                word
                            )

                            print(
                                "Added to sentence:",
                                word,
                            )

    finally:
        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()