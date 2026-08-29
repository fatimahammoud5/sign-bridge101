import json
import math
import random
from pathlib import Path

import librosa
import numpy as np
import tensorflow as tf

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler


# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

DATASET_DIR = BASE_DIR / "dataset"

YAMNET_MODEL = (
    PROJECT_DIR
    / "assets"
    / "models"
    / "yamnet_classification.tflite"
)

OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_DIR = BASE_DIR / "models"

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

CLASSES = [
    "explosion",
    "drone",
    "dog_bark",
    "aircraft",
    "siren",
    "other",
]

MAX_FILES_PER_CLASS = 100

RANDOM_STATE = 42


# ============================================================
# SOURCE GROUP
#
# Keep augmented ESC-50 versions from leaking between
# train and test as much as possible.
# ============================================================

def source_group(file_path: Path) -> str:
    stem = file_path.stem.lower()

    # --------------------------------------------------------
    # ESC-50 originals
    # --------------------------------------------------------

    if stem.startswith("esc50_original_"):
        number_text = stem.replace(
            "esc50_original_",
            "",
        )

        try:
            number = int(number_text)

            return (
                f"{file_path.parent.name}"
                f"_esc50_{number:03d}"
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # ESC-50 augmentations
    #
    # Our augmentations were created from the original
    # ESC-50 files. Map them back to one of 40 originals.
    # --------------------------------------------------------

    if stem.startswith("esc50_augmented_"):
        number_text = stem.replace(
            "esc50_augmented_",
            "",
        )

        try:
            number = int(number_text)

            original_number = (
                (number - 1) % 40
            ) + 1

            return (
                f"{file_path.parent.name}"
                f"_esc50_{original_number:03d}"
            )
        except ValueError:
            pass

    # Drone / other files:
    # treat each physical recording as its own group.
    return (
        f"{file_path.parent.name}_"
        f"{file_path.stem}"
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

    waveform = np.clip(
        waveform,
        -1.0,
        1.0,
    )

    return waveform


# ============================================================
# CREATE SAME WINDOWS AS FLUTTER
# ============================================================

def create_windows(waveform):
    windows = []

    hop_size = WINDOW_SIZE // 2

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
        ].astype(np.float32)

        windows.append(window)

        # Same limit as Flutter.
        if len(windows) >= 9:
            break

        start += hop_size

    if (
        len(windows) == 0
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

        windows.append(
            window[
                :WINDOW_SIZE
            ].astype(np.float32)
        )

    return windows


# ============================================================
# LOAD THE EXACT MOBILE YAMNET
# ============================================================

def load_yamnet():
    print()
    print("Loading mobile YAMNet:")
    print(YAMNET_MODEL)

    if not YAMNET_MODEL.exists():
        raise FileNotFoundError(
            f"Model not found:\n"
            f"{YAMNET_MODEL}"
        )

    interpreter = tf.lite.Interpreter(
        model_path=str(
            YAMNET_MODEL
        )
    )

    interpreter.allocate_tensors()

    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()

    print()
    print("YAMNet input:")
    print(
        inputs[0]["shape"],
        inputs[0]["dtype"],
    )

    print("YAMNet output:")
    print(
        outputs[0]["shape"],
        outputs[0]["dtype"],
    )

    if tuple(
        inputs[0]["shape"]
    ) != (WINDOW_SIZE,):
        raise RuntimeError(
            "Unexpected YAMNet input shape."
        )

    if tuple(
        outputs[0]["shape"]
    ) != (1, 521):
        raise RuntimeError(
            "Unexpected YAMNet output shape."
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

    scores = interpreter.get_tensor(
        output_detail["index"]
    )[0]

    return scores.astype(
        np.float32
    )


# ============================================================
# COLLECT FILES
# ============================================================

def collect_files():
    result = []

    random.seed(
        RANDOM_STATE
    )

    for class_index, class_name in enumerate(
        CLASSES
    ):
        folder = (
            DATASET_DIR
            / class_name
        )

        if not folder.exists():
            raise FileNotFoundError(
                f"Missing class folder:\n"
                f"{folder}"
            )

        files = []

        for extension in [
            "*.wav",
            "*.mp3",
            "*.flac",
            "*.ogg",
            "*.m4a",
        ]:
            files.extend(
                folder.glob(
                    extension
                )
            )

        files = sorted(
            set(files)
        )

        random.Random(
            RANDOM_STATE +
            class_index
        ).shuffle(files)

        files = files[
            :MAX_FILES_PER_CLASS
        ]

        print(
            f"{class_name:12s}: "
            f"{len(files)} files"
        )

        for path in files:
            result.append(
                (
                    class_index,
                    class_name,
                    path,
                )
            )

    return result


# ============================================================
# EXTRACT 521-D FEATURES
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
    names = []

    failed = []

    total = len(files)

    for number, (
        class_index,
        class_name,
        path,
    ) in enumerate(
        files,
        start=1,
    ):
        print(
            f"[{number:03d}/{total:03d}] "
            f"{class_name:12s} "
            f"{path.name}"
        )

        try:
            waveform = load_audio(
                path
            )

            windows = create_windows(
                waveform
            )

            if not windows:
                raise RuntimeError(
                    "No audio windows."
                )

            group = source_group(
                path
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Each audio window becomes a training example.
            #
            # This matches what Flutter will see in real time.
            # ------------------------------------------------

            for window in windows:
                scores = run_yamnet(
                    interpreter,
                    input_detail,
                    output_detail,
                    window,
                )

                X.append(scores)

                y.append(
                    class_index
                )

                groups.append(
                    group
                )

                names.append(
                    str(path)
                )

        except Exception as error:
            print(
                f"FAILED: {error}"
            )

            failed.append(
                str(path)
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
    print("=" * 70)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        "X shape:",
        X.shape,
    )

    print(
        "y shape:",
        y.shape,
    )

    print(
        "Groups:",
        len(
            np.unique(groups)
        ),
    )

    print(
        "Failed files:",
        len(failed),
    )

    return (
        X,
        y,
        groups,
        names,
    )


# ============================================================
# GROUPED TRAIN / TEST SPLIT
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

    train_index, test_index = next(
        splitter.split(
            X,
            y,
            groups,
        )
    )

    return (
        X[train_index],
        X[test_index],
        y[train_index],
        y[test_index],
    )


# ============================================================
# SOFTMAX CHECK
# ============================================================

def softmax(logits):
    logits = logits - np.max(
        logits,
        axis=1,
        keepdims=True,
    )

    exp_values = np.exp(
        logits
    )

    return (
        exp_values /
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
    print("=" * 70)
    print(
        "SIGNBRIDGE - TRAIN MOBILE "
        "521-INPUT SOUND CLASSIFIER"
    )
    print("=" * 70)

    print()
    print(
        "This classifier uses the SAME "
        "YAMNet TFLite model as Flutter."
    )

    print()

    (
        interpreter,
        input_detail,
        output_detail,
    ) = load_yamnet()

    print()
    print("=" * 70)
    print("DATASET")
    print("=" * 70)

    files = collect_files()

    print()
    print(
        "Total selected files:",
        len(files),
    )

    print()
    print("=" * 70)
    print("EXTRACTING MOBILE YAMNET FEATURES")
    print("=" * 70)

    X, y, groups, names = (
        extract_features(
            interpreter,
            input_detail,
            output_detail,
            files,
        )
    )

    if len(X) == 0:
        raise RuntimeError(
            "No features extracted."
        )

    print()
    print("=" * 70)
    print("TRAIN / TEST SPLIT")
    print("=" * 70)

    (
        X_train,
        X_test,
        y_train,
        y_test,
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

    # ========================================================
    # STANDARDIZE
    # ========================================================

    print()
    print("=" * 70)
    print("STANDARDIZING")
    print("=" * 70)

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
    # TRAIN LEARNED CLASSIFIER
    # ========================================================

    print()
    print("=" * 70)
    print("TRAINING CLASSIFIER")
    print("=" * 70)

    classifier = LogisticRegression(
        max_iter=3000,
        C=1.0,
        class_weight="balanced",
        solver="lbfgs",
    )

    classifier.fit(
        X_train_scaled,
        y_train,
    )

    print()
    print("Training complete.")

    # ========================================================
    # TEST
    # ========================================================

    predictions = classifier.predict(
        X_test_scaled
    )

    print()
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    report = classification_report(
        y_test,
        predictions,
        target_names=CLASSES,
        digits=4,
        zero_division=0,
    )

    print(report)

    report_path = (
        OUTPUT_DIR
        / "mobile_classifier_report.txt"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    # ========================================================
    # EXPORT TO PURE DART PARAMETERS
    #
    # LogisticRegression is:
    #
    # scaled = (x - mean) / scale
    # logits = scaled @ W.T + bias
    # softmax(logits)
    #
    # Dart can perform this directly.
    # ========================================================

    export_data = {
        "version": 1,

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

    json_path = (
        MODEL_DIR
        / "mobile_sound_classifier.json"
    )

    json_path.write_text(
        json.dumps(
            export_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # VERIFY THAT JSON MATH MATCHES SCIKIT-LEARN
    # ========================================================

    manual_scaled = (
        (
            X_test -
            scaler.mean_
        ) /
        scaler.scale_
    )

    manual_logits = (
        manual_scaled
        @ classifier.coef_.T
        + classifier.intercept_
    )

    manual_probabilities = softmax(
        manual_logits
    )

    manual_predictions = np.argmax(
        manual_probabilities,
        axis=1,
    )

    sklearn_predictions = (
        classifier.predict(
            X_test_scaled
        )
    )

    match_rate = np.mean(
        manual_predictions ==
        sklearn_predictions
    )

    print()
    print("=" * 70)
    print("DART EXPORT VERIFICATION")
    print("=" * 70)

    print(
        "Prediction match:",
        f"{match_rate * 100:.2f}%",
    )

    print()
    print("Saved model parameters:")
    print(json_path)

    print()
    print("Saved report:")
    print(report_path)

    print()

    if match_rate > 0.999:
        print(
            "SUCCESS: exported model math "
            "matches trained classifier."
        )
    else:
        print(
            "WARNING: export verification "
            "did not perfectly match."
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()