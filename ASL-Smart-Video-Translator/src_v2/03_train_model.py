from __future__ import annotations

import csv
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from tensorflow.keras.callbacks import Callback, ReduceLROnPlateau
from tensorflow.keras.layers import (
    BatchNormalization,
    Bidirectional,
    Concatenate,
    Conv1D,
    Dense,
    Dropout,
    GaussianNoise,
    GlobalAveragePooling1D,
    GlobalMaxPooling1D,
    GRU,
    Input,
    LayerNormalization,
    SpatialDropout1D,
)
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2

from common import (
    FEATURES_ROOT,
    MODELS_ROOT,
    RAW_FEATURES,
    SEQUENCE_LENGTH,
    load_classes,
    save_runtime_files,
)


# ============================================================
# SETTINGS
# ============================================================

# ط³ظ†ط¬ط±ط¨ ط«ظ„ط§ط« ط¨ط¯ط§ظٹط§طھ طھط¯ط±ظٹط¨ ظ…ط®طھظ„ظپط©طŒ
# ط«ظ… ظ†ط­طھظپط¸ ط¨ط§ظ„ظ†ظ…ظˆط°ط¬ ط§ظ„ط£ظپط¶ظ„ ط¹ظ„ظ‰ Validation.
SEEDS = (42, 123, 2026)

EPOCHS = 100
BATCH_SIZE = 16
PATIENCE = 16

# ظ…ظˆط§ط²ظ†ط© ظƒظ„ ظƒظ„ظ…ط© ط¥ظ„ظ‰ ظ‡ط°ط§ ط§ظ„ط¹ط¯ط¯.
TARGET_PER_CLASS = 52

LEARNING_RATE = 6e-4

# 126 local landmarks
# + 6 wrist path
# + 126 landmark velocity
# + 6 wrist velocity
# + 2 hand-presence flags
MODEL_FEATURES = RAW_FEATURES * 2 + 14

EPS = 1e-8


# ============================================================
# LOAD DATA
# ============================================================

def load_split(
    split: str,
    classes: list[str],
    label_map: dict[str, int],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load raw landmark sequences from features_v2.

    Expected input shape for each file:
        (30, 126)
    """

    X: list[np.ndarray] = []
    y: list[int] = []
    paths: list[str] = []

    print(f"\nLoading {split}...")

    for class_name in classes:
        folder = FEATURES_ROOT / split / class_name
        count = 0

        if not folder.exists():
            print(f"[MISSING] {folder}")
            continue

        for path in sorted(folder.glob("aslc_*.npy")):
            try:
                sequence = np.load(path).astype(np.float32)

                if sequence.shape != (
                    SEQUENCE_LENGTH,
                    RAW_FEATURES,
                ):
                    print(
                        f"[SKIP SHAPE] "
                        f"{path}: {sequence.shape}"
                    )
                    continue

                if not np.all(
                    np.isfinite(sequence)
                ):
                    print(
                        f"[SKIP INVALID] {path}"
                    )
                    continue

                X.append(sequence)
                y.append(
                    label_map[class_name]
                )
                paths.append(str(path))
                count += 1

            except Exception as exc:
                print(
                    f"[SKIP ERROR] "
                    f"{path}: {exc}"
                )

        print(
            f"{class_name:18s}: {count}"
        )

    return (
        np.asarray(
            X,
            dtype=np.float32,
        ),
        np.asarray(
            y,
            dtype=np.int32,
        ),
        paths,
    )


# ============================================================
# DATA AUGMENTATION
# ============================================================

def temporal_warp(
    sequence: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Change signing speed and temporal alignment slightly.
    """

    frames = len(sequence)

    old_time = np.arange(
        frames,
        dtype=np.float32,
    )

    speed = float(
        rng.uniform(
            0.85,
            1.15,
        )
    )

    shift = float(
        rng.uniform(
            -2.0,
            2.0,
        )
    )

    center = (
        (frames - 1) / 2.0
        + shift
    )

    half_span = (
        (frames - 1)
        * speed
        / 2.0
    )

    new_time = np.linspace(
        center - half_span,
        center + half_span,
        frames,
        dtype=np.float32,
    )

    new_time = np.clip(
        new_time,
        0.0,
        frames - 1,
    )

    result = np.empty_like(
        sequence
    )

    for feature_index in range(
        sequence.shape[1]
    ):
        result[
            :,
            feature_index,
        ] = np.interp(
            new_time,
            old_time,
            sequence[
                :,
                feature_index,
            ],
        )

    return result.astype(
        np.float32
    )


def mirror_hands(
    sequence: np.ndarray,
) -> np.ndarray:
    """
    Mirror the signer horizontally.

    Mirroring changes handedness, therefore the Right and Left
    feature slots are swapped after changing the X coordinates.
    """

    hands = sequence.reshape(
        SEQUENCE_LENGTH,
        2,
        21,
        3,
    ).copy()

    for hand_index in range(2):
        present = np.any(
            np.abs(
                hands[
                    :,
                    hand_index,
                ]
            ) > EPS,
            axis=(1, 2),
        )

        hands[
            present,
            hand_index,
            :,
            0,
        ] = (
            1.0
            - hands[
                present,
                hand_index,
                :,
                0,
            ]
        )

    # Swap Right and Left hand slots.
    hands = hands[
        :,
        [1, 0],
        :,
        :,
    ]

    return hands.reshape(
        SEQUENCE_LENGTH,
        RAW_FEATURES,
    ).astype(np.float32)


def spatial_jitter(
    sequence: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Apply small camera-position, rotation, scale and landmark noise.
    """

    hands = sequence.reshape(
        SEQUENCE_LENGTH,
        2,
        21,
        3,
    ).copy()

    angle = float(
        rng.uniform(
            -0.12,
            0.12,
        )
    )

    rotation = np.array(
        [
            [
                np.cos(angle),
                -np.sin(angle),
            ],
            [
                np.sin(angle),
                np.cos(angle),
            ],
        ],
        dtype=np.float32,
    )

    scale = float(
        rng.uniform(
            0.93,
            1.07,
        )
    )

    translation = rng.uniform(
        -0.03,
        0.03,
        size=2,
    ).astype(np.float32)

    center = np.array(
        [0.5, 0.5],
        dtype=np.float32,
    )

    for hand_index in range(2):
        present = np.any(
            np.abs(
                hands[
                    :,
                    hand_index,
                ]
            ) > EPS,
            axis=(1, 2),
        )

        if not np.any(present):
            continue

        xy = hands[
            present,
            hand_index,
            :,
            :2,
        ]

        xy = (
            xy - center
        ) @ rotation.T

        hands[
            present,
            hand_index,
            :,
            :2,
        ] = (
            xy * scale
            + center
            + translation
        )

        hands[
            present,
            hand_index,
            :,
            2,
        ] *= scale

    present = np.any(
        np.abs(hands) > EPS,
        axis=(2, 3),
    )

    noise = rng.normal(
        0.0,
        0.0025,
        size=hands.shape,
    ).astype(np.float32)

    hands += (
        noise
        * present[
            :,
            :,
            None,
            None,
        ]
    )

    return hands.reshape(
        SEQUENCE_LENGTH,
        RAW_FEATURES,
    ).astype(np.float32)


def augment(
    sequence: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Complete augmentation pipeline.
    """

    result = temporal_warp(
        sequence,
        rng,
    )

    if rng.random() < 0.45:
        result = mirror_hands(
            result
        )

    result = spatial_jitter(
        result,
        rng,
    )

    # Simulate a repeated webcam frame occasionally.
    if rng.random() < 0.25:
        frame_index = int(
            rng.integers(
                1,
                SEQUENCE_LENGTH,
            )
        )

        result[
            frame_index
        ] = result[
            frame_index - 1
        ]

    return result.astype(
        np.float32
    )


# ============================================================
# HAND SHAPE + MOTION FEATURES
# ============================================================

def make_motion_features(
    sequence: np.ndarray,
) -> np.ndarray:
    """
    Convert raw MediaPipe landmarks:

        Input:  (30, 126)
        Output: (30, 266)

    The new representation contains:

    1. Local hand shape relative to the wrist.
    2. Wrist movement through the image.
    3. Finger/landmark velocity.
    4. Wrist velocity.
    5. Right/left hand presence.
    """

    if sequence.shape != (
        SEQUENCE_LENGTH,
        RAW_FEATURES,
    ):
        raise ValueError(
            "Wrong raw sequence shape: "
            f"{sequence.shape}"
        )

    hands = sequence.reshape(
        SEQUENCE_LENGTH,
        2,
        21,
        3,
    ).astype(np.float32)

    presence = np.any(
        np.abs(hands) > EPS,
        axis=(2, 3),
    )

    local = np.zeros_like(
        hands
    )

    wrist_path = np.zeros(
        (
            SEQUENCE_LENGTH,
            2,
            3,
        ),
        dtype=np.float32,
    )

    local_velocity = np.zeros_like(
        hands
    )

    wrist_velocity = np.zeros(
        (
            SEQUENCE_LENGTH,
            2,
            3,
        ),
        dtype=np.float32,
    )

    # MCP landmarks used to estimate hand size.
    palm_indices = [
        5,
        9,
        13,
        17,
    ]

    for hand_index in range(2):
        valid_frames = np.flatnonzero(
            presence[
                :,
                hand_index,
            ]
        )

        if len(valid_frames) == 0:
            continue

        wrist = hands[
            :,
            hand_index,
            0,
            :,
        ]

        palm = hands[
            :,
            hand_index,
            palm_indices,
            :,
        ]

        distances = np.linalg.norm(
            palm
            - wrist[
                :,
                None,
                :,
            ],
            axis=2,
        )

        valid_distances = distances[
            presence[
                :,
                hand_index,
            ]
        ]

        valid_distances = (
            valid_distances[
                valid_distances > EPS
            ]
        )

        if len(valid_distances):
            hand_scale = float(
                np.median(
                    valid_distances
                )
            )
        else:
            hand_scale = 1.0

        hand_scale = max(
            hand_scale,
            1e-4,
        )

        valid = presence[
            :,
            hand_index,
        ]

        # Shape relative to the wrist.
        local[
            valid,
            hand_index,
        ] = (
            hands[
                valid,
                hand_index,
            ]
            - wrist[
                valid,
                None,
                :,
            ]
        ) / hand_scale

        # Wrist path relative to its first visible position.
        first_wrist = wrist[
            int(valid_frames[0])
        ]

        wrist_path[
            valid,
            hand_index,
        ] = (
            wrist[valid]
            - first_wrist
        ) / hand_scale

        # Frame-to-frame motion.
        for frame_index in range(
            1,
            SEQUENCE_LENGTH,
        ):
            current_present = presence[
                frame_index,
                hand_index,
            ]

            previous_present = presence[
                frame_index - 1,
                hand_index,
            ]

            if (
                current_present
                and previous_present
            ):
                local_velocity[
                    frame_index,
                    hand_index,
                ] = (
                    local[
                        frame_index,
                        hand_index,
                    ]
                    - local[
                        frame_index - 1,
                        hand_index,
                    ]
                )

                wrist_velocity[
                    frame_index,
                    hand_index,
                ] = (
                    wrist_path[
                        frame_index,
                        hand_index,
                    ]
                    - wrist_path[
                        frame_index - 1,
                        hand_index,
                    ]
                )

    # Remove extreme MediaPipe values.
    local = np.clip(
        local,
        -4.0,
        4.0,
    )

    wrist_path = np.clip(
        wrist_path,
        -6.0,
        6.0,
    )

    local_velocity = np.clip(
        local_velocity,
        -2.5,
        2.5,
    )

    wrist_velocity = np.clip(
        wrist_velocity,
        -3.0,
        3.0,
    )

    features = np.concatenate(
        [
            local.reshape(
                SEQUENCE_LENGTH,
                RAW_FEATURES,
            ),
            wrist_path.reshape(
                SEQUENCE_LENGTH,
                6,
            ),
            local_velocity.reshape(
                SEQUENCE_LENGTH,
                RAW_FEATURES,
            ),
            wrist_velocity.reshape(
                SEQUENCE_LENGTH,
                6,
            ),
            presence.astype(
                np.float32
            ),
        ],
        axis=1,
    ).astype(np.float32)

    expected_shape = (
        SEQUENCE_LENGTH,
        MODEL_FEATURES,
    )

    if features.shape != expected_shape:
        raise ValueError(
            "Wrong engineered feature shape: "
            f"{features.shape}; "
            f"expected {expected_shape}"
        )

    return features


def convert_dataset(
    X_raw: np.ndarray,
) -> np.ndarray:
    """
    Convert validation or test samples without augmentation.
    """

    return np.asarray(
        [
            make_motion_features(
                sequence
            )
            for sequence in X_raw
        ],
        dtype=np.float32,
    )


def build_balanced_training_set(
    X_raw: np.ndarray,
    y: np.ndarray,
    class_count: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Keep every original training sample and create realistic
    augmentations until every class has TARGET_PER_CLASS samples.
    """

    rng = np.random.default_rng(
        seed
    )

    X_result: list[np.ndarray] = []
    y_result: list[int] = []

    for class_index in range(
        class_count
    ):
        class_samples = X_raw[
            y == class_index
        ]

        if len(class_samples) == 0:
            raise ValueError(
                f"Class {class_index} "
                "has no training samples."
            )

        created = 0

        # Preserve original samples.
        for sequence in class_samples:
            X_result.append(
                make_motion_features(
                    sequence
                )
            )

            y_result.append(
                class_index
            )

            created += 1

        # Add balanced augmented samples.
        while created < TARGET_PER_CLASS:
            source_index = int(
                rng.integers(
                    0,
                    len(class_samples),
                )
            )

            source = class_samples[
                source_index
            ]

            augmented = augment(
                source,
                rng,
            )

            X_result.append(
                make_motion_features(
                    augmented
                )
            )

            y_result.append(
                class_index
            )

            created += 1

    X_result_array = np.asarray(
        X_result,
        dtype=np.float32,
    )

    y_result_array = np.asarray(
        y_result,
        dtype=np.int32,
    )

    order = rng.permutation(
        len(X_result_array)
    )

    return (
        X_result_array[order],
        y_result_array[order],
    )


# ============================================================
# MODEL
# ============================================================

def build_model(
    class_count: int,
) -> tf.keras.Model:
    """
    Temporal CNN + Bidirectional GRU classifier.
    """

    regularizer = l2(
        2e-4
    )

    inputs = Input(
        shape=(
            SEQUENCE_LENGTH,
            MODEL_FEATURES,
        ),
        name="motion_features",
    )

    x = GaussianNoise(
        0.008,
        name="input_noise",
    )(inputs)

    x = Conv1D(
        filters=48,
        kernel_size=5,
        padding="same",
        activation="swish",
        kernel_regularizer=regularizer,
        name="temporal_conv",
    )(x)

    x = BatchNormalization(
        name="conv_batch_normalization"
    )(x)

    x = SpatialDropout1D(
        0.15,
        name="spatial_dropout",
    )(x)

    x = Bidirectional(
        GRU(
            32,
            return_sequences=True,
            dropout=0.15,
            kernel_regularizer=regularizer,
        ),
        name="bidirectional_gru",
    )(x)

    x = LayerNormalization(
        name="sequence_normalization"
    )(x)

    average_pool = (
        GlobalAveragePooling1D(
            name="average_pool"
        )(x)
    )

    maximum_pool = (
        GlobalMaxPooling1D(
            name="maximum_pool"
        )(x)
    )

    x = Concatenate(
        name="combined_temporal_pool"
    )(
        [
            average_pool,
            maximum_pool,
        ]
    )

    x = Dense(
        64,
        activation="swish",
        kernel_regularizer=regularizer,
        name="classifier_dense",
    )(x)

    x = Dropout(
        0.40,
        name="classifier_dropout",
    )(x)

    outputs = Dense(
        class_count,
        activation="softmax",
        name="class_probabilities",
    )(x)

    model = Model(
        inputs=inputs,
        outputs=outputs,
        name="asl_improved_motion_model",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=LEARNING_RATE,
            clipnorm=1.0,
        ),
        loss=(
            tf.keras.losses
            .CategoricalCrossentropy(
                label_smoothing=0.05
            )
        ),
        metrics=[
            "accuracy"
        ],
    )

    return model


# ============================================================
# BEST MODEL CALLBACK
# ============================================================

class BestMacroF1(Callback):
    """
    Save the epoch that recognizes all classes most evenly.

    Macro F1 is more useful than val_loss here because several
    classes have only one or two validation examples.
    """

    def __init__(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        class_count: int,
        output_path,
    ):
        super().__init__()

        self.X_val = X_val
        self.y_val = y_val
        self.class_count = (
            class_count
        )
        self.output_path = (
            output_path
        )

        self.best_f1 = -1.0
        self.best_accuracy = -1.0
        self.best_epoch = -1
        self.wait = 0

    def on_epoch_end(
        self,
        epoch,
        logs=None,
    ):
        probabilities = (
            self.model.predict(
                self.X_val,
                verbose=0,
            )
        )

        predictions = np.argmax(
            probabilities,
            axis=1,
        )

        macro_f1 = float(
            f1_score(
                self.y_val,
                predictions,
                labels=np.arange(
                    self.class_count
                ),
                average="macro",
                zero_division=0,
            )
        )

        accuracy = float(
            accuracy_score(
                self.y_val,
                predictions,
            )
        )

        improved = (
            macro_f1
            > self.best_f1
            + 1e-6
        )

        tied_and_better = (
            abs(
                macro_f1
                - self.best_f1
            )
            <= 1e-6
            and accuracy
            > self.best_accuracy
            + 1e-6
        )

        if (
            improved
            or tied_and_better
        ):
            self.best_f1 = (
                macro_f1
            )

            self.best_accuracy = (
                accuracy
            )

            self.best_epoch = (
                epoch + 1
            )

            self.wait = 0

            self.model.save(
                str(
                    self.output_path
                )
            )

            print(
                "\nSaved candidate: "
                f"val_macro_f1="
                f"{macro_f1:.4f}, "
                f"val_accuracy="
                f"{accuracy:.4f}"
            )

        else:
            self.wait += 1

            print(
                "\n"
                f"val_macro_f1="
                f"{macro_f1:.4f}, "
                f"best="
                f"{self.best_f1:.4f}, "
                f"wait="
                f"{self.wait}/"
                f"{PATIENCE}"
            )

            if self.wait >= PATIENCE:
                print(
                    "Early stopping "
                    "by validation Macro F1."
                )

                self.model.stop_training = (
                    True
                )


# ============================================================
# REPORT FILES
# ============================================================

def save_confusion_csv(
    matrix: np.ndarray,
    classes: list[str],
    path,
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "true/predicted",
                *classes,
            ]
        )

        for class_name, row in zip(
            classes,
            matrix,
        ):
            writer.writerow(
                [
                    class_name,
                    *row.tolist(),
                ]
            )


def save_predictions_csv(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    classes: list[str],
    paths: list[str],
    path,
) -> None:
    predicted = np.argmax(
        probabilities,
        axis=1,
    )

    sorted_probabilities = np.sort(
        probabilities,
        axis=1,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "file",
                "true",
                "predicted",
                "confidence",
                "margin",
                "correct",
            ]
        )

        for index in range(
            len(y_true)
        ):
            confidence = float(
                sorted_probabilities[
                    index,
                    -1,
                ]
            )

            margin = float(
                sorted_probabilities[
                    index,
                    -1,
                ]
                - sorted_probabilities[
                    index,
                    -2,
                ]
            )

            writer.writerow(
                [
                    paths[index],
                    classes[
                        int(
                            y_true[index]
                        )
                    ],
                    classes[
                        int(
                            predicted[index]
                        )
                    ],
                    confidence,
                    margin,
                    bool(
                        predicted[index]
                        == y_true[index]
                    ),
                ]
            )


# ============================================================
# UNKNOWN-SIGN REJECTION SETTINGS
# ============================================================

def calculate_rejection_settings(
    probabilities: np.ndarray,
    y_true: np.ndarray,
    classes: list[str],
) -> dict:
    """
    Learn confidence and margin limits from validation samples.

    The live translator will use these values later to show
    Unknown Sign instead of forcing a random class.
    """

    predicted = np.argmax(
        probabilities,
        axis=1,
    )

    sorted_probabilities = np.sort(
        probabilities,
        axis=1,
    )

    confidence = (
        sorted_probabilities[
            :,
            -1,
        ]
    )

    margin = (
        sorted_probabilities[
            :,
            -1,
        ]
        - sorted_probabilities[
            :,
            -2,
        ]
    )

    correct = (
        predicted == y_true
    )

    best = None

    for confidence_limit in np.arange(
        0.35,
        0.81,
        0.025,
    ):
        for margin_limit in np.arange(
            0.03,
            0.26,
            0.02,
        ):
            accepted = (
                confidence
                >= confidence_limit
            ) & (
                margin
                >= margin_limit
            )

            if np.sum(accepted) < 5:
                continue

            accepted_accuracy = float(
                np.mean(
                    correct[accepted]
                )
            )

            coverage = float(
                np.mean(accepted)
            )

            # Prefer accepted accuracy >= 75%.
            # Among those choices, prefer greater coverage.
            if accepted_accuracy >= 0.75:
                score = (
                    10.0
                    + coverage
                )
            else:
                score = (
                    accepted_accuracy
                    + 0.20
                    * coverage
                )

            if (
                best is None
                or score
                > best["score"]
            ):
                best = {
                    "confidence_threshold":
                        float(
                            confidence_limit
                        ),
                    "margin_threshold":
                        float(
                            margin_limit
                        ),
                    "accepted_accuracy":
                        accepted_accuracy,
                    "coverage":
                        coverage,
                    "score":
                        score,
                }

    if best is None:
        best = {
            "confidence_threshold": 0.55,
            "margin_threshold": 0.08,
            "accepted_accuracy": 0.0,
            "coverage": 0.0,
            "score": 0.0,
        }

    per_class = {}

    for class_index, class_name in enumerate(
        classes
    ):
        correct_confidence = confidence[
            correct
            & (
                y_true
                == class_index
            )
        ]

        if len(
            correct_confidence
        ) >= 2:
            threshold = max(
                (
                    best[
                        "confidence_threshold"
                    ]
                    * 0.90
                ),
                float(
                    np.percentile(
                        correct_confidence,
                        20,
                    )
                    - 0.04
                ),
            )

        elif len(
            correct_confidence
        ) == 1:
            threshold = max(
                best[
                    "confidence_threshold"
                ],
                float(
                    correct_confidence[0]
                    - 0.03
                ),
            )

        else:
            threshold = max(
                best[
                    "confidence_threshold"
                ],
                0.65,
            )

        per_class[
            class_name
        ] = float(
            np.clip(
                threshold,
                0.35,
                0.90,
            )
        )

    best[
        "per_class_thresholds"
    ] = per_class

    return best


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    classes = load_classes()
    class_count = len(classes)

    if class_count != 11:
        raise ValueError(
            "This training file expects "
            f"11 classes, but found "
            f"{class_count}."
        )

    label_map = {
        name: index
        for index, name in enumerate(
            classes
        )
    }

    MODELS_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Keep the current asl_v2.keras untouched.
    improved_model_path = (
        MODELS_ROOT
        / "asl_v2_improved.keras"
    )

    print("=" * 72)
    print(
        "IMPROVED TRAINING "
        "- SAME V2 PROJECT"
    )
    print("=" * 72)

    print("Class order:")

    for index, class_name in enumerate(
        classes
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    (
        X_train_raw,
        y_train,
        _,
    ) = load_split(
        "train",
        classes,
        label_map,
    )

    (
        X_val_raw,
        y_val,
        _,
    ) = load_split(
        "val",
        classes,
        label_map,
    )

    (
        X_test_raw,
        y_test,
        test_paths,
    ) = load_split(
        "test",
        classes,
        label_map,
    )

    print("\nOriginal shapes:")

    print(
        "Train:",
        X_train_raw.shape,
        y_train.shape,
    )

    print(
        "Val:  ",
        X_val_raw.shape,
        y_val.shape,
    )

    print(
        "Test: ",
        X_test_raw.shape,
        y_test.shape,
    )

    if (
        len(X_train_raw) == 0
        or len(X_val_raw) == 0
        or len(X_test_raw) == 0
    ):
        raise ValueError(
            "Train, val and test "
            "must not be empty."
        )

    expected_labels = np.arange(
        class_count
    )

    if not np.array_equal(
        np.unique(y_train),
        expected_labels,
    ):
        raise ValueError(
            "One or more classes "
            "have no training samples."
        )

    print(
        "\nBuilding stronger "
        "motion features..."
    )

    X_val = convert_dataset(
        X_val_raw
    )

    X_test = convert_dataset(
        X_test_raw
    )

    print(
        "Validation:",
        X_val.shape,
    )

    print(
        "Test:      ",
        X_test.shape,
    )

    y_val_one_hot = (
        tf.keras.utils.to_categorical(
            y_val,
            num_classes=class_count,
        )
    )

    candidates = []

    for run_number, seed in enumerate(
        SEEDS,
        start=1,
    ):
        print(
            "\n"
            + "=" * 72
        )

        print(
            f"CANDIDATE "
            f"{run_number}/"
            f"{len(SEEDS)} "
            f"- SEED {seed}"
        )

        print("=" * 72)

        tf.keras.backend.clear_session()

        np.random.seed(
            seed
        )

        tf.random.set_seed(
            seed
        )

        X_train, y_train_balanced = (
            build_balanced_training_set(
                X_train_raw,
                y_train,
                class_count,
                seed,
            )
        )

        y_train_one_hot = (
            tf.keras.utils.to_categorical(
                y_train_balanced,
                num_classes=class_count,
            )
        )

        print(
            "Balanced train:",
            X_train.shape,
        )

        print(
            "Each class:",
            TARGET_PER_CLASS,
        )

        candidate_path = (
            MODELS_ROOT
            / (
                "asl_v2_candidate_"
                f"{seed}.keras"
            )
        )

        best_callback = BestMacroF1(
            X_val,
            y_val,
            class_count,
            candidate_path,
        )

        model = build_model(
            class_count
        )

        if run_number == 1:
            model.summary()

        model.fit(
            X_train,
            y_train_one_hot,
            validation_data=(
                X_val,
                y_val_one_hot,
            ),
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            shuffle=True,
            callbacks=[
                best_callback,
                ReduceLROnPlateau(
                    monitor="val_loss",
                    factor=0.5,
                    patience=6,
                    min_lr=1e-6,
                    verbose=1,
                ),
            ],
            verbose=1,
        )

        candidate_model = (
            tf.keras.models.load_model(
                candidate_path
            )
        )

        val_probabilities = (
            candidate_model.predict(
                X_val,
                verbose=0,
            )
        )

        val_predictions = np.argmax(
            val_probabilities,
            axis=1,
        )

        result = {
            "seed": seed,
            "path": str(
                candidate_path
            ),
            "best_epoch":
                best_callback.best_epoch,
            "val_accuracy": float(
                accuracy_score(
                    y_val,
                    val_predictions,
                )
            ),
            "val_macro_f1": float(
                f1_score(
                    y_val,
                    val_predictions,
                    labels=expected_labels,
                    average="macro",
                    zero_division=0,
                )
            ),
        }

        candidates.append(
            result
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    # Select using validation only.
    candidates.sort(
        key=lambda item: (
            item["val_macro_f1"],
            item["val_accuracy"],
        ),
        reverse=True,
    )

    best_candidate = candidates[0]

    print(
        "\nBest candidate:"
    )

    print(
        json.dumps(
            best_candidate,
            indent=2,
        )
    )

    model = (
        tf.keras.models.load_model(
            best_candidate["path"]
        )
    )

    # Save without deleting the existing 11-word model.
    model.save(
        str(
            improved_model_path
        )
    )

    save_runtime_files(
        classes
    )

    feature_config = {
        "feature_version":
            "motion_266_v1",
        "sequence_length":
            SEQUENCE_LENGTH,
        "raw_features":
            RAW_FEATURES,
        "model_features":
            MODEL_FEATURES,
        "classes":
            classes,
        "selected_seed":
            best_candidate["seed"],
    }

    (
        MODELS_ROOT
        / "feature_config_v2.json"
    ).write_text(
        json.dumps(
            feature_config,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Learn confidence limits from Validation.
    val_probabilities = model.predict(
        X_val,
        verbose=0,
    )

    rejection = (
        calculate_rejection_settings(
            val_probabilities,
            y_val,
            classes,
        )
    )

    (
        MODELS_ROOT
        / "calibration_v2.json"
    ).write_text(
        json.dumps(
            rejection,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    y_test_one_hot = (
        tf.keras.utils.to_categorical(
            y_test,
            num_classes=class_count,
        )
    )

    test_loss, test_accuracy = (
        model.evaluate(
            X_test,
            y_test_one_hot,
            verbose=0,
        )
    )

    test_probabilities = model.predict(
        X_test,
        verbose=0,
    )

    test_predictions = np.argmax(
        test_probabilities,
        axis=1,
    )

    test_macro_f1 = float(
        f1_score(
            y_test,
            test_predictions,
            labels=expected_labels,
            average="macro",
            zero_division=0,
        )
    )

    report = classification_report(
        y_test,
        test_predictions,
        labels=expected_labels,
        target_names=classes,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        test_predictions,
        labels=expected_labels,
    )

    (
        MODELS_ROOT
        / "classification_report_v2.txt"
    ).write_text(
        report,
        encoding="utf-8",
    )

    np.save(
        MODELS_ROOT
        / "confusion_matrix_v2.npy",
        matrix,
    )

    save_confusion_csv(
        matrix,
        classes,
        MODELS_ROOT
        / "confusion_matrix_v2.csv",
    )

    save_predictions_csv(
        y_test,
        test_probabilities,
        classes,
        test_paths,
        MODELS_ROOT
        / "test_predictions_v2.csv",
    )

    summary = {
        "classes":
            classes,
        "model_features":
            MODEL_FEATURES,
        "candidates":
            candidates,
        "best_candidate":
            best_candidate,
        "test_loss":
            float(test_loss),
        "test_accuracy":
            float(test_accuracy),
        "test_macro_f1":
            test_macro_f1,
        "model_path":
            str(improved_model_path),
        "rejection":
            rejection,
    }

    (
        MODELS_ROOT
        / "training_summary_v2.json"
    ).write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\n"
        + "=" * 72
    )

    print(report)

    print(
        f"Test loss:      "
        f"{test_loss:.4f}"
    )

    print(
        f"Test accuracy:  "
        f"{test_accuracy:.2%}"
    )

    print(
        f"Test macro-F1:  "
        f"{test_macro_f1:.4f}"
    )

    print(
        f"Model:          "
        f"{improved_model_path}"
    )

    print(
        "Confidence threshold: "
        f"{rejection['confidence_threshold']:.3f}"
    )

    print(
        "Margin threshold:     "
        f"{rejection['margin_threshold']:.3f}"
    )

    print("=" * 72)

    print(
        "\nIMPORTANT: "
        "the improved model expects "
        f"{MODEL_FEATURES} "
        "features per frame."
    )

    print(
        "Do not run the old live translator yet. "
        "It must be updated to use the same "
        "motion-feature conversion."
    )


if __name__ == "__main__":
    main()