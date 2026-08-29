from pathlib import Path
import hashlib
import json
import random
import re

import librosa
import numpy as np
import tensorflow as tf

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

DATASET_DIR = BASE_DIR / "dataset_v2"

YAMNET_MODEL = (
    PROJECT_DIR
    / "assets"
    / "models"
    / "yamnet_classification.tflite"
)

MODEL_DIR = (
    BASE_DIR
    / "models_v3"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs_v3"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# AUDIO SETTINGS
# ============================================================

SAMPLE_RATE = 16000

WINDOW_SIZE = 15600

RANDOM_STATE = 42


AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}


# ============================================================
# CUSTOM AI CLASSES
#
# IMPORTANT:
#
# Only classes that need specialized discrimination are here.
#
# Cat/Bird/Glass/etc will become hard-negative examples
# for "other".
#
# When Flutter receives "other", it will use normal YAMNet.
# ============================================================

CLASSES = [
    "explosion",
    "drone",
    "aircraft",
    "siren",
    "dog_bark",
    "other",
]


CLASS_TO_INDEX = {
    name: index
    for index, name
    in enumerate(CLASSES)
}


# ============================================================
# SPECIAL POSITIVE CLASSES
# ============================================================

POSITIVE_FOLDERS = [
    "explosion",
    "drone",
    "aircraft",
    "siren",
    "dog_bark",
]


# ============================================================
# HARD NEGATIVE FOLDERS
#
# ALL of these will train as:
#
# other
#
# This teaches the AI:
#
# Cat != Explosion
# Glass != Explosion
# Bird != Drone
# Car horn != Siren
# etc.
# ============================================================

NEGATIVE_FOLDERS = [
    "other",
    "cat",
    "bird",
    "baby_cry",
    "glass_break",
    "car_horn",
    "doorbell",
    "speech",
    "music",
]


# ============================================================
# FILE LIMITS
# ============================================================

MAX_POSITIVE_FILES = 250


NEGATIVE_LIMITS = {
    # Broad hard-negative pool
    "other": 700,

    # Use all available files up to these limits.
    "cat": 120,
    "bird": 160,
    "baby_cry": 120,
    "glass_break": 120,
    "car_horn": 120,
    "doorbell": 120,

    "speech": 150,
    "music": 150,
}


# ============================================================
# AUDIO HASH
#
# Prevent exact duplicate files from entering the dataset
# multiple times under different filenames.
# ============================================================

def file_hash(path: Path):
    hasher = hashlib.sha1()

    with open(path, "rb") as file:
        while True:
            block = file.read(
                1024 * 1024
            )

            if not block:
                break

            hasher.update(
                block
            )

    return hasher.hexdigest()


# ============================================================
# SOURCE GROUP
#
# Critical for avoiding train/test leakage.
# ============================================================

def source_group(path: Path):
    stem = path.stem.lower()

    folder = path.parent.name.lower()

    # --------------------------------------------------------
    # DRONE
    #
    # Example:
    #
    # B_S2_D1_074-bebop_000_
    # B_S2_D1_074-bebop_001_
    #
    # Both should remain in the same split.
    # --------------------------------------------------------

    if folder == "drone":
        if "-" in stem:
            prefix = stem.split(
                "-",
                1,
            )[0]

            return (
                f"drone_session_{prefix}"
            )

    # --------------------------------------------------------
    # OLD ESC-50 ORIGINALS
    # --------------------------------------------------------

    if stem.startswith(
        "esc50_original_"
    ):
        number = stem.replace(
            "esc50_original_",
            "",
        )

        return (
            f"{folder}_oldesc_"
            f"{number}"
        )

    # --------------------------------------------------------
    # OLD ESC-50 AUGMENTATIONS
    #
    # Keep augmented files with their assumed original source.
    # --------------------------------------------------------

    if stem.startswith(
        "esc50_augmented_"
    ):
        value = stem.replace(
            "esc50_augmented_",
            "",
        )

        try:
            number = int(
                value
            )

            original_number = (
                (number - 1) % 40
            ) + 1

            return (
                f"{folder}_oldesc_"
                f"{original_number:03d}"
            )

        except ValueError:
            pass

    # --------------------------------------------------------
    # FREESOUND / ESC STYLE FILENAMES
    #
    # Example:
    # 1-115545-B-483
    #
    # 115545 identifies the original source.
    # --------------------------------------------------------

    match = re.search(
        r"(\d+)-(\d+)-([a-zA-Z])-([0-9]+)",
        stem,
    )

    if match is not None:
        source_id = (
            match.group(2)
        )

        return (
            f"source_{source_id}"
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return (
        f"{folder}_{stem}"
    )


# ============================================================
# AUDIO FILE LIST
# ============================================================

def audio_files(folder: Path):
    if not folder.exists():
        return []

    return sorted(
        [
            path
            for path in folder.iterdir()
            if (
                path.is_file()
                and
                path.suffix.lower()
                in AUDIO_EXTENSIONS
            )
        ]
    )


# ============================================================
# SELECT FILES
# ============================================================

def select_files(
    files,
    limit,
    seed,
):
    files = list(
        files
    )

    rng = random.Random(
        seed
    )

    rng.shuffle(
        files
    )

    return files[
        :limit
    ]


# ============================================================
# BUILD RECORD LIST
# ============================================================

def collect_records():
    print()
    print("=" * 75)
    print("COLLECTING HYBRID V3 DATA")
    print("=" * 75)

    records = []

    seen_hashes = {}

    duplicate_count = 0

    # ========================================================
    # POSITIVE CLASSES
    # ========================================================

    for class_index, class_name in enumerate(
        POSITIVE_FOLDERS
    ):
        folder = (
            DATASET_DIR
            / class_name
        )

        files = audio_files(
            folder
        )

        files = select_files(
            files,
            MAX_POSITIVE_FILES,
            RANDOM_STATE
            + class_index,
        )

        accepted = 0

        for path in files:
            try:
                digest = file_hash(
                    path
                )

                if digest in seen_hashes:
                    duplicate_count += 1
                    continue

                seen_hashes[digest] = str(
                    path
                )

                records.append(
                    {
                        "class_name":
                            class_name,

                        "class_index":
                            CLASS_TO_INDEX[
                                class_name
                            ],

                        "source_folder":
                            class_name,

                        "path":
                            path,

                        "group":
                            source_group(
                                path
                            ),
                    }
                )

                accepted += 1

            except Exception as error:
                print(
                    f"[HASH ERROR] "
                    f"{path.name}: "
                    f"{error}"
                )

        print(
            f"{class_name:13s}: "
            f"{accepted:4d} files"
        )

    # ========================================================
    # HARD NEGATIVES -> OTHER
    # ========================================================

    print()
    print("HARD NEGATIVES -> other")
    print("-" * 75)

    for folder_index, folder_name in enumerate(
        NEGATIVE_FOLDERS
    ):
        folder = (
            DATASET_DIR
            / folder_name
        )

        files = audio_files(
            folder
        )

        limit = NEGATIVE_LIMITS.get(
            folder_name,
            100,
        )

        files = select_files(
            files,
            limit,
            RANDOM_STATE
            + 100
            + folder_index,
        )

        accepted = 0

        for path in files:
            try:
                digest = file_hash(
                    path
                )

                if digest in seen_hashes:
                    duplicate_count += 1
                    continue

                seen_hashes[digest] = str(
                    path
                )

                records.append(
                    {
                        "class_name":
                            "other",

                        "class_index":
                            CLASS_TO_INDEX[
                                "other"
                            ],

                        "source_folder":
                            folder_name,

                        "path":
                            path,

                        "group":
                            source_group(
                                path
                            ),
                    }
                )

                accepted += 1

            except Exception as error:
                print(
                    f"[HASH ERROR] "
                    f"{path.name}: "
                    f"{error}"
                )

        print(
            f"{folder_name:13s}: "
            f"{accepted:4d} "
            f"-> other"
        )

    print()
    print(
        "TOTAL RECORDS:",
        len(records),
    )

    print(
        "EXACT DUPLICATES REMOVED:",
        duplicate_count,
    )

    return records


# ============================================================
# GLOBAL GROUP SPLIT
#
# Same source can never be in both train and test.
# ============================================================

def assign_splits(
    records,
):
    unique_groups = sorted(
        {
            record["group"]
            for record
            in records
        }
    )

    rng = random.Random(
        RANDOM_STATE
    )

    rng.shuffle(
        unique_groups
    )

    test_count = max(
        1,
        round(
            len(unique_groups)
            * 0.20
        ),
    )

    test_groups = set(
        unique_groups[
            :test_count
        ]
    )

    for record in records:
        record["split"] = (
            "test"
            if record["group"]
            in test_groups
            else "train"
        )

    print()
    print("=" * 75)
    print("GROUP SPLIT")
    print("=" * 75)

    print(
        "Unique groups:",
        len(unique_groups),
    )

    print(
        "Test groups:",
        len(test_groups),
    )

    print(
        "Train groups:",
        len(unique_groups)
        - len(test_groups),
    )

    return records


# ============================================================
# SPLIT DISTRIBUTION
# ============================================================

def print_file_distribution(
    records,
):
    print()
    print("=" * 75)
    print("FILE DISTRIBUTION")
    print("=" * 75)

    for class_name in CLASSES:
        train_count = sum(
            1
            for record in records
            if (
                record["class_name"]
                == class_name
                and
                record["split"]
                == "train"
            )
        )

        test_count = sum(
            1
            for record in records
            if (
                record["class_name"]
                == class_name
                and
                record["split"]
                == "test"
            )
        )

        print(
            f"{class_name:13s} "
            f"train={train_count:4d} "
            f"test={test_count:4d}"
        )


# ============================================================
# LOAD AUDIO
# ============================================================

def load_audio(path: Path):
    waveform, _ = librosa.load(
        str(path),
        sr=SAMPLE_RATE,
        mono=True,
    )

    waveform = waveform.astype(
        np.float32
    )

    waveform = np.nan_to_num(
        waveform,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    waveform = np.clip(
        waveform,
        -1.0,
        1.0,
    )

    return waveform


# ============================================================
# RMS
# ============================================================

def rms(waveform):
    if len(waveform) == 0:
        return 0.0

    return float(
        np.sqrt(
            np.mean(
                np.square(
                    waveform
                )
            )
        )
    )


# ============================================================
# CREATE FLUTTER-LIKE WINDOWS
# ============================================================

def create_windows(
    waveform,
):
    windows = []

    hop = (
        WINDOW_SIZE // 2
    )

    start = 0

    while start < len(
        waveform
    ):
        remaining = (
            len(waveform)
            - start
        )

        if remaining < (
            WINDOW_SIZE // 4
        ):
            break

        end = min(
            start
            + WINDOW_SIZE,
            len(waveform),
        )

        window = waveform[
            start:end
        ]

        if len(window) < (
            WINDOW_SIZE
        ):
            window = np.pad(
                window,
                (
                    0,
                    WINDOW_SIZE
                    - len(window),
                ),
            )

        window = window[
            :WINDOW_SIZE
        ].astype(
            np.float32
        )

        windows.append(
            window
        )

        if len(windows) >= 9:
            break

        start += hop

    if (
        not windows
        and
        len(waveform) > 0
    ):
        window = waveform.copy()

        if len(window) < (
            WINDOW_SIZE
        ):
            window = np.pad(
                window,
                (
                    0,
                    WINDOW_SIZE
                    - len(window),
                ),
            )

        windows.append(
            window[
                :WINDOW_SIZE
            ].astype(
                np.float32
            )
        )

    return windows


# ============================================================
# LOAD EXACT MOBILE YAMNET
# ============================================================

def load_yamnet():
    print()
    print("=" * 75)
    print("LOADING MOBILE YAMNET")
    print("=" * 75)

    print(
        YAMNET_MODEL
    )

    if not YAMNET_MODEL.exists():
        raise FileNotFoundError(
            f"Missing model:\n"
            f"{YAMNET_MODEL}"
        )

    interpreter = (
        tf.lite.Interpreter(
            model_path=str(
                YAMNET_MODEL
            )
        )
    )

    interpreter.allocate_tensors()

    input_detail = (
        interpreter
        .get_input_details()[0]
    )

    output_detail = (
        interpreter
        .get_output_details()[0]
    )

    print(
        "INPUT:",
        input_detail["shape"],
        input_detail["dtype"],
    )

    print(
        "OUTPUT:",
        output_detail["shape"],
        output_detail["dtype"],
    )

    if tuple(
        input_detail["shape"]
    ) != (WINDOW_SIZE,):
        raise RuntimeError(
            "Unexpected YAMNet input shape."
        )

    if tuple(
        output_detail["shape"]
    ) != (1, 521):
        raise RuntimeError(
            "Unexpected YAMNet output shape."
        )

    return (
        interpreter,
        input_detail,
        output_detail,
    )


# ============================================================
# YAMNET INFERENCE
# ============================================================

def run_yamnet(
    interpreter,
    input_detail,
    output_detail,
    window,
):
    interpreter.set_tensor(
        input_detail["index"],
        window.astype(
            np.float32
        ),
    )

    interpreter.invoke()

    scores = interpreter.get_tensor(
        output_detail["index"]
    )[0]

    return scores.astype(
        np.float32
    )


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(
    records,
    interpreter,
    input_detail,
    output_detail,
):
    X_train = []
    y_train = []

    X_test = []
    y_test = []

    test_groups = []

    failed = []

    total = len(
        records
    )

    print()
    print("=" * 75)
    print("EXTRACTING FEATURES")
    print("=" * 75)

    for number, record in enumerate(
        records,
        start=1,
    ):
        path = record[
            "path"
        ]

        class_name = record[
            "class_name"
        ]

        split = record[
            "split"
        ]

        print(
            f"[{number:04d}/{total:04d}] "
            f"{split:5s} "
            f"{class_name:12s} "
            f"{record['source_folder']:12s} "
            f"{path.name}"
        )

        try:
            waveform = load_audio(
                path
            )

            level = rms(
                waveform
            )

            if level < 0.0003:
                raise RuntimeError(
                    "Almost silent audio."
                )

            windows = create_windows(
                waveform
            )

            if not windows:
                raise RuntimeError(
                    "No windows."
                )

            for window in windows:
                features = run_yamnet(
                    interpreter,
                    input_detail,
                    output_detail,
                    window,
                )

                if split == "train":
                    X_train.append(
                        features
                    )

                    y_train.append(
                        record[
                            "class_index"
                        ]
                    )

                else:
                    X_test.append(
                        features
                    )

                    y_test.append(
                        record[
                            "class_index"
                        ]
                    )

                    test_groups.append(
                        record[
                            "group"
                        ]
                    )

        except Exception as error:
            failed.append(
                str(path)
            )

            print(
                f"   FAILED: {error}"
            )

    X_train = np.asarray(
        X_train,
        dtype=np.float32,
    )

    y_train = np.asarray(
        y_train,
        dtype=np.int64,
    )

    X_test = np.asarray(
        X_test,
        dtype=np.float32,
    )

    y_test = np.asarray(
        y_test,
        dtype=np.int64,
    )

    test_groups = np.asarray(
        test_groups,
    )

    print()
    print("=" * 75)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 75)

    print(
        "Train X:",
        X_train.shape,
    )

    print(
        "Test X :",
        X_test.shape,
    )

    print(
        "Failed files:",
        len(failed),
    )

    return (
        X_train,
        y_train,
        X_test,
        y_test,
        test_groups,
    )


# ============================================================
# DISTRIBUTION
# ============================================================

def print_window_distribution(
    title,
    labels,
):
    print()
    print(title)
    print("-" * 75)

    for index, class_name in enumerate(
        CLASSES
    ):
        count = int(
            np.sum(
                labels == index
            )
        )

        print(
            f"{class_name:13s}: "
            f"{count}"
        )


# ============================================================
# SOFTMAX
# ============================================================

def softmax(
    logits,
):
    shifted = (
        logits
        -
        np.max(
            logits,
            axis=1,
            keepdims=True,
        )
    )

    values = np.exp(
        shifted
    )

    return (
        values
        /
        np.sum(
            values,
            axis=1,
            keepdims=True,
        )
    )


# ============================================================
# GROUP LEVEL EVALUATION
#
# More similar to Flutter because multiple windows
# participate in one decision.
# ============================================================

def evaluate_groups(
    probabilities,
    y_test,
    test_groups,
    classifier,
):
    grouped_probabilities = {}

    grouped_labels = {}

    for index, group in enumerate(
        test_groups
    ):
        grouped_probabilities.setdefault(
            group,
            [],
        ).append(
            probabilities[index]
        )

        grouped_labels[
            group
        ] = y_test[index]

    true_labels = []
    predicted_labels = []

    for group, values in (
        grouped_probabilities.items()
    ):
        array = np.asarray(
            values
        )

        mean_scores = np.mean(
            array,
            axis=0,
        )

        peak_scores = np.max(
            array,
            axis=0,
        )

        # Combine stability + peak evidence.
        final_scores = (
            mean_scores * 0.55
            +
            peak_scores * 0.45
        )

        position = int(
            np.argmax(
                final_scores
            )
        )

        predicted_class = int(
            classifier.classes_[
                position
            ]
        )

        true_labels.append(
            int(
                grouped_labels[
                    group
                ]
            )
        )

        predicted_labels.append(
            predicted_class
        )

    true_labels = np.asarray(
        true_labels,
        dtype=np.int64,
    )

    predicted_labels = np.asarray(
        predicted_labels,
        dtype=np.int64,
    )

    report = classification_report(
        true_labels,
        predicted_labels,
        labels=list(
            range(
                len(CLASSES)
            )
        ),
        target_names=CLASSES,
        digits=4,
        zero_division=0,
    )

    print()
    print("=" * 75)
    print("GROUP / RECORDING LEVEL RESULTS")
    print("=" * 75)

    print(
        report
    )

    path = (
        OUTPUT_DIR
        / "group_report_v3.txt"
    )

    path.write_text(
        report,
        encoding="utf-8",
    )

    return report


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 75)

    print(
        "SIGNBRIDGE - HYBRID V3 TRAINING"
    )

    print("=" * 75)

    print()
    print(
        "Custom classes:"
    )

    print(
        CLASSES
    )

    print()
    print(
        "Cat/Bird/Glass/Car horn/etc "
        "are trained as hard negatives -> other."
    )

    # ========================================================
    # RECORDS
    # ========================================================

    records = collect_records()

    if not records:
        raise RuntimeError(
            "Dataset is empty."
        )

    records = assign_splits(
        records
    )

    print_file_distribution(
        records
    )

    # ========================================================
    # YAMNET
    # ========================================================

    (
        interpreter,
        input_detail,
        output_detail,
    ) = load_yamnet()

    # ========================================================
    # FEATURES
    # ========================================================

    (
        X_train,
        y_train,
        X_test,
        y_test,
        test_groups,
    ) = extract_features(
        records,
        interpreter,
        input_detail,
        output_detail,
    )

    if (
        len(X_train) == 0
        or
        len(X_test) == 0
    ):
        raise RuntimeError(
            "Train or test set is empty."
        )

    print_window_distribution(
        "TRAIN WINDOWS",
        y_train,
    )

    print_window_distribution(
        "TEST WINDOWS",
        y_test,
    )

    # ========================================================
    # VERIFY ALL SIX CLASSES EXIST
    # ========================================================

    train_classes = set(
        np.unique(
            y_train
        ).tolist()
    )

    test_classes = set(
        np.unique(
            y_test
        ).tolist()
    )

    expected = set(
        range(
            len(CLASSES)
        )
    )

    print()
    print(
        "Train classes:",
        sorted(
            train_classes
        ),
    )

    print(
        "Test classes:",
        sorted(
            test_classes
        ),
    )

    if train_classes != expected:
        raise RuntimeError(
            "Training set does not "
            "contain all 6 classes."
        )

    if test_classes != expected:
        raise RuntimeError(
            "Test set does not "
            "contain all 6 classes."
        )

    # ========================================================
    # SCALE
    # ========================================================

    print()
    print("=" * 75)
    print("STANDARDIZATION")
    print("=" * 75)

    scaler = StandardScaler()

    X_train_scaled = (
        scaler.fit_transform(
            X_train
        )
    )

    X_test_scaled = (
        scaler.transform(
            X_test
        )
    )

    # ========================================================
    # TRAIN
    #
    # No class_weight="balanced".
    #
    # The previous 14-class experiment strongly promoted
    # small classes such as glass_break and caused false
    # positives.
    # ========================================================

    print()
    print("=" * 75)
    print("TRAINING HYBRID CLASSIFIER")
    print("=" * 75)

    classifier = LogisticRegression(
        max_iter=5000,
        C=0.5,
        solver="lbfgs",
        class_weight=None,
    )

    classifier.fit(
        X_train_scaled,
        y_train,
    )

    print(
        "Classifier classes:",
        classifier.classes_,
    )

    # ========================================================
    # WINDOW LEVEL TEST
    # ========================================================

    predictions = classifier.predict(
        X_test_scaled
    )

    probabilities = (
        classifier.predict_proba(
            X_test_scaled
        )
    )

    print()
    print("=" * 75)
    print("WINDOW LEVEL TEST RESULTS")
    print("=" * 75)

    report = classification_report(
        y_test,
        predictions,
        labels=list(
            range(
                len(CLASSES)
            )
        ),
        target_names=CLASSES,
        digits=4,
        zero_division=0,
    )

    print(
        report
    )

    (
        OUTPUT_DIR
        / "window_report_v3.txt"
    ).write_text(
        report,
        encoding="utf-8",
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=list(
            range(
                len(CLASSES)
            )
        ),
    )

    print(
        "Confusion matrix:"
    )

    print(
        matrix
    )

    np.savetxt(
        OUTPUT_DIR
        / "confusion_matrix_v3.csv",
        matrix,
        delimiter=",",
        fmt="%d",
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = np.max(
        probabilities,
        axis=1,
    )

    sorted_probs = np.sort(
        probabilities,
        axis=1,
    )

    margins = (
        sorted_probs[:, -1]
        -
        sorted_probs[:, -2]
    )

    correct = (
        predictions == y_test
    )

    print()
    print("=" * 75)
    print("CONFIDENCE ANALYSIS")
    print("=" * 75)

    if np.any(correct):
        print(
            "Mean confidence CORRECT:",
            f"{np.mean(confidence[correct]):.4f}",
        )

        print(
            "Mean margin CORRECT:",
            f"{np.mean(margins[correct]):.4f}",
        )

    if np.any(~correct):
        print(
            "Mean confidence WRONG:",
            f"{np.mean(confidence[~correct]):.4f}",
        )

        print(
            "Mean margin WRONG:",
            f"{np.mean(margins[~correct]):.4f}",
        )

    # ========================================================
    # RECORDING/GROUP LEVEL TEST
    # ========================================================

    evaluate_groups(
        probabilities,
        y_test,
        test_groups,
        classifier,
    )

    # ========================================================
    # EXPORT
    #
    # IMPORTANT:
    # Export in the EXACT order used by sklearn weights.
    # ========================================================

    model_class_names = [
        CLASSES[
            int(class_id)
        ]
        for class_id
        in classifier.classes_
    ]

    export = {
        "version": 3,

        "architecture":
            "yamnet_521_logistic_hybrid",

        "input_size": 521,

        "classes":
            model_class_names,

        "class_ids":
            [
                int(value)
                for value
                in classifier.classes_
            ],

        "scaler_mean":
            scaler.mean_
            .astype(float)
            .tolist(),

        "scaler_scale":
            scaler.scale_
            .astype(float)
            .tolist(),

        "weights":
            classifier.coef_
            .astype(float)
            .tolist(),

        "bias":
            classifier.intercept_
            .astype(float)
            .tolist(),
    }

    model_path = (
        MODEL_DIR
        / "mobile_sound_classifier_v3.json"
    )

    model_path.write_text(
        json.dumps(
            export,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # EXACT DART-MATH VERIFICATION
    # ========================================================

    manual_scaled = (
        (
            X_test
            - scaler.mean_
        )
        /
        scaler.scale_
    )

    manual_logits = (
        manual_scaled
        @ classifier.coef_.T
        +
        classifier.intercept_
    )

    manual_probabilities = (
        softmax(
            manual_logits
        )
    )

    manual_positions = np.argmax(
        manual_probabilities,
        axis=1,
    )

    # ========================================================
    # IMPORTANT FIX FROM SCRIPT 14:
    #
    # argmax gives a POSITION inside classifier.classes_.
    #
    # It is NOT necessarily the original class ID.
    # ========================================================

    manual_predictions = (
        classifier.classes_[
            manual_positions
        ]
    )

    match_rate = float(
        np.mean(
            manual_predictions
            ==
            predictions
        )
    )

    probability_difference = float(
        np.max(
            np.abs(
                manual_probabilities
                -
                probabilities
            )
        )
    )

    print()
    print("=" * 75)
    print("EXPORT VERIFICATION")
    print("=" * 75)

    print(
        "Prediction match:",
        f"{match_rate * 100:.2f}%",
    )

    print(
        "Maximum probability difference:",
        probability_difference,
    )

    print()
    print(
        "Expected result:"
    )

    print(
        "Prediction match: 100.00%"
    )

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if match_rate < 0.9999:
        raise RuntimeError(
            "EXPORT VERIFICATION FAILED. "
            "Do NOT use this model in Flutter."
        )

    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    summary = {
        "classes":
            model_class_names,

        "train_windows":
            int(
                len(
                    X_train
                )
            ),

        "test_windows":
            int(
                len(
                    X_test
                )
            ),

        "prediction_match":
            match_rate,

        "max_probability_difference":
            probability_difference,
    }

    (
        OUTPUT_DIR
        / "training_summary_v3.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 75)
    print("MODEL SAVED")
    print("=" * 75)

    print(
        model_path
    )

    print()
    print(
        "Do NOT copy it to Flutter yet."
    )

    print(
        "First review the V3 test results."
    )

    print()
    print("=" * 75)
    print("DONE")
    print("=" * 75)


if __name__ == "__main__":
    main()