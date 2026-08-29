from pathlib import Path
import json
import random

import librosa
import numpy as np
import tensorflow as tf

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler


# ============================================================
# SETTINGS
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

OUTPUT_DIR = BASE_DIR / "outputs_v2"
MODEL_DIR = BASE_DIR / "models_v2"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


SAMPLE_RATE = 16000
WINDOW_SIZE = 15600

RANDOM_STATE = 42


# ============================================================
# ALL CLASSES
# ============================================================

CLASSES = [
    "explosion",
    "drone",
    "aircraft",
    "siren",
    "dog_bark",
    "cat",
    "bird",
    "baby_cry",
    "glass_break",
    "car_horn",
    "doorbell",
    "speech",
    "music",
    "other",
]


# ============================================================
# LIMITS
#
# We do not want "other" to dominate everything,
# but it should still be larger than normal classes.
# ============================================================

MAX_FILES = {
    "explosion": 300,
    "drone": 300,
    "aircraft": 300,
    "siren": 300,
    "dog_bark": 300,

    "cat": 300,
    "bird": 300,
    "baby_cry": 300,
    "glass_break": 300,

    "car_horn": 300,
    "doorbell": 300,

    "speech": 300,
    "music": 300,

    "other": 700,
}


# ============================================================
# AUDIO EXTENSIONS
# ============================================================

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}


# ============================================================
# SOURCE GROUP
#
# Very important:
#
# We try to keep related files together so they do not appear
# in both train and test.
# ============================================================

def source_group(path: Path) -> str:
    stem = path.stem.lower()
    class_name = path.parent.name

    # --------------------------------------------------------
    # Old ESC50 augmented data:
    #
    # esc50_augmented_001
    # esc50_original_001
    # --------------------------------------------------------

    if stem.startswith("esc50_original_"):
        number = stem.replace(
            "esc50_original_",
            "",
        )

        return (
            f"{class_name}_oldesc_{number}"
        )

    if stem.startswith("esc50_augmented_"):
        number_text = stem.replace(
            "esc50_augmented_",
            "",
        )

        try:
            number = int(
                number_text
            )

            # Previous augmentation scheme was derived
            # from a smaller number of source clips.
            original = (
                (number - 1) % 40
            ) + 1

            return (
                f"{class_name}_oldesc_"
                f"{original:03d}"
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # New official ESC-50 files.
    #
    # Example:
    # esc50_cat_1-100032-A-0.wav
    #
    # ESC-50 filenames:
    # fold-source-take-target.wav
    #
    # Clips with the same source identifier should stay
    # grouped together.
    # --------------------------------------------------------

    if stem.startswith("esc50_"):
        parts = stem.split("_", 2)

        if len(parts) == 3:
            original_name = parts[2]

            dash_parts = (
                original_name.split("-")
            )

            if len(dash_parts) >= 2:
                source_id = (
                    dash_parts[1]
                )

                return (
                    f"{class_name}_esc50_"
                    f"{source_id}"
                )

    # --------------------------------------------------------
    # Drone dataset
    #
    # Example:
    # B_S2_D1_074-bebop_000_
    #
    # Multiple snippets may come from the same session.
    # Group them using the recording prefix before "-".
    # --------------------------------------------------------

    if (
        class_name == "drone"
        and "-" in stem
    ):
        prefix = stem.split(
            "-",
            1,
        )[0]

        return (
            f"drone_{prefix}"
        )

    # --------------------------------------------------------
    # Generic files:
    # each original file is its own source.
    # --------------------------------------------------------

    return (
        f"{class_name}_{stem}"
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
# WINDOWS
#
# Must match Flutter as closely as possible.
# ============================================================

def create_windows(waveform):
    result = []

    hop = WINDOW_SIZE // 2

    start = 0

    while start < len(waveform):
        remaining = (
            len(waveform) - start
        )

        if remaining < WINDOW_SIZE // 4:
            break

        end = min(
            start + WINDOW_SIZE,
            len(waveform),
        )

        window = waveform[
            start:end
        ]

        if len(window) < WINDOW_SIZE:
            window = np.pad(
                window,
                (
                    0,
                    WINDOW_SIZE -
                    len(window),
                ),
            )

        window = window[
            :WINDOW_SIZE
        ].astype(
            np.float32
        )

        result.append(
            window
        )

        if len(result) >= 9:
            break

        start += hop

    if (
        len(result) == 0
        and len(waveform) > 0
    ):
        window = waveform.copy()

        if len(window) < WINDOW_SIZE:
            window = np.pad(
                window,
                (
                    0,
                    WINDOW_SIZE -
                    len(window),
                ),
            )

        result.append(
            window[
                :WINDOW_SIZE
            ].astype(
                np.float32
            )
        )

    return result


# ============================================================
# LOAD MOBILE YAMNET
# ============================================================

def load_yamnet():
    print()
    print(
        "Loading exact Flutter YAMNet:"
    )

    print(
        YAMNET_MODEL
    )

    if not YAMNET_MODEL.exists():
        raise FileNotFoundError(
            YAMNET_MODEL
        )

    interpreter = tf.lite.Interpreter(
        model_path=str(
            YAMNET_MODEL
        )
    )

    interpreter.allocate_tensors()

    inputs = (
        interpreter
        .get_input_details()
    )

    outputs = (
        interpreter
        .get_output_details()
    )

    print()
    print(
        "INPUT :",
        inputs[0]["shape"],
        inputs[0]["dtype"],
    )

    print(
        "OUTPUT:",
        outputs[0]["shape"],
        outputs[0]["dtype"],
    )

    if tuple(
        inputs[0]["shape"]
    ) != (WINDOW_SIZE,):
        raise RuntimeError(
            "Unexpected YAMNet input."
        )

    if tuple(
        outputs[0]["shape"]
    ) != (1, 521):
        raise RuntimeError(
            "Unexpected YAMNet output."
        )

    return (
        interpreter,
        inputs[0],
        outputs[0],
    )


# ============================================================
# RUN YAMNET
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

    output = interpreter.get_tensor(
        output_detail["index"]
    )[0]

    return output.astype(
        np.float32
    )


# ============================================================
# DATASET FILES
# ============================================================

def collect_files():
    print()
    print("=" * 75)
    print("DATASET V2")
    print("=" * 75)

    all_files = []

    rng = random.Random(
        RANDOM_STATE
    )

    for (
        class_index,
        class_name,
    ) in enumerate(
        CLASSES
    ):
        folder = (
            DATASET_DIR /
            class_name
        )

        if not folder.exists():
            raise FileNotFoundError(
                f"Missing folder: "
                f"{folder}"
            )

        files = [
            path
            for path
            in folder.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in AUDIO_EXTENSIONS
            )
        ]

        files = sorted(
            files
        )

        # Separate random generator
        # to keep reproducibility.
        class_rng = random.Random(
            RANDOM_STATE
            + class_index
        )

        class_rng.shuffle(
            files
        )

        limit = MAX_FILES[
            class_name
        ]

        files = files[
            :limit
        ]

        print(
            f"{class_name:13s}: "
            f"{len(files):4d}"
        )

        for path in files:
            all_files.append(
                (
                    class_index,
                    class_name,
                    path,
                )
            )

    rng.shuffle(
        all_files
    )

    print("-" * 75)

    print(
        "Selected files:",
        len(all_files),
    )

    return all_files


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(
    interpreter,
    input_detail,
    output_detail,
    files,
):
    X = []
    y = []
    groups = []

    failed = []

    class_windows = {
        class_name: 0
        for class_name
        in CLASSES
    }

    total = len(files)

    print()
    print("=" * 75)
    print(
        "EXTRACTING 521-D MOBILE FEATURES"
    )
    print("=" * 75)

    for number, (
        class_index,
        class_name,
        path,
    ) in enumerate(
        files,
        start=1,
    ):
        print(
            f"[{number:04d}/{total:04d}] "
            f"{class_name:13s} "
            f"{path.name}"
        )

        try:
            waveform = load_audio(
                path
            )

            audio_rms = rms(
                waveform
            )

            # Skip broken / almost silent files.
            if audio_rms < 0.0003:
                raise RuntimeError(
                    "Audio is almost silent."
                )

            windows = create_windows(
                waveform
            )

            if not windows:
                raise RuntimeError(
                    "No windows."
                )

            group_name = source_group(
                path
            )

            for window in windows:
                scores = run_yamnet(
                    interpreter,
                    input_detail,
                    output_detail,
                    window,
                )

                X.append(
                    scores
                )

                y.append(
                    class_index
                )

                groups.append(
                    group_name
                )

                class_windows[
                    class_name
                ] += 1

        except Exception as error:
            failed.append(
                str(path)
            )

            print(
                f"   FAILED: {error}"
            )

    X = np.asarray(
        X,
        dtype=np.float32,
    )

    y = np.asarray(
        y,
        dtype=np.int64,
    )

    groups = np.asarray(
        groups,
    )

    print()
    print("=" * 75)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 75)

    print(
        "X:",
        X.shape,
    )

    print(
        "y:",
        y.shape,
    )

    print(
        "Unique groups:",
        len(
            np.unique(groups)
        ),
    )

    print(
        "Failed:",
        len(failed),
    )

    print()
    print("WINDOWS PER CLASS")
    print("-" * 75)

    for class_name in CLASSES:
        print(
            f"{class_name:13s}: "
            f"{class_windows[class_name]}"
        )

    return (
        X,
        y,
        groups,
    )


# ============================================================
# GROUPED SPLIT
# ============================================================

def split_dataset(
    X,
    y,
    groups,
):
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_STATE,
    )

    train_idx, test_idx = next(
        splitter.split(
            X,
            y,
            groups,
        )
    )

    return (
        X[train_idx],
        X[test_idx],
        y[train_idx],
        y[test_idx],
        groups[train_idx],
        groups[test_idx],
    )


# ============================================================
# PRINT CLASS DISTRIBUTION
# ============================================================

def print_distribution(
    title,
    y,
):
    print()
    print(title)
    print("-" * 75)

    for (
        class_index,
        class_name,
    ) in enumerate(
        CLASSES
    ):
        count = int(
            np.sum(
                y == class_index
            )
        )

        print(
            f"{class_name:13s}: "
            f"{count}"
        )


# ============================================================
# SOFTMAX
# ============================================================

def softmax(logits):
    shifted = (
        logits
        - np.max(
            logits,
            axis=1,
            keepdims=True,
        )
    )

    exp_values = np.exp(
        shifted
    )

    return (
        exp_values
        /
        np.sum(
            exp_values,
            axis=1,
            keepdims=True,
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 75)

    print(
        "SIGNBRIDGE - DATASET V2 "
        "MULTICLASS TRAINING"
    )

    print("=" * 75)

    (
        interpreter,
        input_detail,
        output_detail,
    ) = load_yamnet()

    files = collect_files()

    (
        X,
        y,
        groups,
    ) = extract_features(
        interpreter,
        input_detail,
        output_detail,
        files,
    )

    if len(X) == 0:
        raise RuntimeError(
            "No features were created."
        )

    print()
    print("=" * 75)
    print("GROUPED TRAIN / TEST SPLIT")
    print("=" * 75)

    (
        X_train,
        X_test,
        y_train,
        y_test,
        groups_train,
        groups_test,
    ) = split_dataset(
        X,
        y,
        groups,
    )

    print(
        "Train:",
        X_train.shape,
    )

    print(
        "Test :",
        X_test.shape,
    )

    # Verify no group leakage.
    train_groups = set(
        groups_train.tolist()
    )

    test_groups = set(
        groups_test.tolist()
    )

    overlap = (
        train_groups
        .intersection(
            test_groups
        )
    )

    print(
        "Group leakage:",
        len(overlap),
    )

    if overlap:
        raise RuntimeError(
            "Train/test group leakage detected."
        )

    print_distribution(
        "TRAIN DISTRIBUTION",
        y_train,
    )

    print_distribution(
        "TEST DISTRIBUTION",
        y_test,
    )

    # ========================================================
    # STANDARDIZATION
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
    # ========================================================

    print()
    print("=" * 75)
    print(
        "TRAINING 14-CLASS CLASSIFIER"
    )
    print("=" * 75)

    classifier = LogisticRegression(
        max_iter=5000,
        C=0.7,
        class_weight="balanced",
        solver="lbfgs",
    )

    classifier.fit(
        X_train_scaled,
        y_train,
    )

    print(
        "Training complete."
    )

    # ========================================================
    # TEST
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
    print("TEST RESULTS")
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

    report_path = (
        OUTPUT_DIR
        / "classification_report_v2.txt"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=list(
            range(
                len(CLASSES)
            )
        ),
    )

    cm_path = (
        OUTPUT_DIR
        / "confusion_matrix_v2.csv"
    )

    np.savetxt(
        cm_path,
        cm,
        delimiter=",",
        fmt="%d",
    )

    print()
    print(
        "Confusion matrix:"
    )

    print(
        cm
    )

    # ========================================================
    # CONFIDENCE ANALYSIS
    # ========================================================

    top_probability = (
        np.max(
            probabilities,
            axis=1,
        )
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
        predictions ==
        y_test
    )

    print()
    print("=" * 75)
    print("CONFIDENCE ANALYSIS")
    print("=" * 75)

    if np.any(correct):
        print(
            "Mean confidence CORRECT:",
            f"{np.mean(top_probability[correct]):.4f}",
        )

        print(
            "Mean margin CORRECT:",
            f"{np.mean(margins[correct]):.4f}",
        )

    if np.any(~correct):
        print(
            "Mean confidence WRONG:",
            f"{np.mean(top_probability[~correct]):.4f}",
        )

        print(
            "Mean margin WRONG:",
            f"{np.mean(margins[~correct]):.4f}",
        )

    # ========================================================
    # EXPORT MODEL
    # ========================================================

    export = {
        "version": 2,

        "input_size": 521,

        "classes": CLASSES,

        "scaler_mean": (
            scaler.mean_
            .astype(float)
            .tolist()
        ),

        "scaler_scale": (
            scaler.scale_
            .astype(float)
            .tolist()
        ),

        "weights": (
            classifier.coef_
            .astype(float)
            .tolist()
        ),

        "bias": (
            classifier.intercept_
            .astype(float)
            .tolist()
        ),
    }

    model_path = (
        MODEL_DIR
        / "mobile_sound_classifier_v2.json"
    )

    model_path.write_text(
        json.dumps(
            export,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # VERIFY DART MATH
    # ========================================================

    scaled_manual = (
        (
            X_test
            - scaler.mean_
        )
        /
        scaler.scale_
    )

    logits = (
        scaled_manual
        @ classifier.coef_.T
        + classifier.intercept_
    )

    manual_probabilities = (
        softmax(
            logits
        )
    )

    manual_predictions = (
        np.argmax(
            manual_probabilities,
            axis=1,
        )
    )

    match_rate = np.mean(
        manual_predictions
        ==
        predictions
    )

    print()
    print("=" * 75)
    print("EXPORT VERIFICATION")
    print("=" * 75)

    print(
        "Prediction match:",
        f"{match_rate * 100:.2f}%",
    )

    print()
    print(
        "Model saved:"
    )

    print(
        model_path
    )

    print()
    print(
        "Report saved:"
    )

    print(
        report_path
    )

    print()
    print(
        "Confusion matrix saved:"
    )

    print(
        cm_path
    )

    print()
    print("=" * 75)
    print("DONE")
    print("=" * 75)


if __name__ == "__main__":
    main()