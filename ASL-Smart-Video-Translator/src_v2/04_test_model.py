from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


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


# ============================================================
# TRAINED CANDIDATES
# ============================================================

CANDIDATE_PATHS = [
    MODELS_ROOT
    / "asl_v2_candidate_42.keras",

    MODELS_ROOT
    / "asl_v2_candidate_123.keras",

    MODELS_ROOT
    / "asl_v2_candidate_2026.keras",
]


# ============================================================
# LOAD FUNCTIONS FROM 03_train_model.py
# ============================================================

def load_training_module():
    """
    Load the feature conversion and utility functions from the
    improved training file without starting training again.
    """

    sys.path.insert(
        0,
        str(SRC_ROOT),
    )

    specification = (
        importlib.util.spec_from_file_location(
            "improved_training_v2",
            TRAIN_FILE,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Could not load training file:\n"
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


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    class_count: int,
) -> tuple[float, float]:

    predictions = np.argmax(
        probabilities,
        axis=1,
    )

    accuracy = float(
        accuracy_score(
            y_true,
            predictions,
        )
    )

    macro_f1 = float(
        f1_score(
            y_true,
            predictions,
            labels=np.arange(
                class_count
            ),
            average="macro",
            zero_division=0,
        )
    )

    return accuracy, macro_f1


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    training = load_training_module()

    classes = training.load_classes()
    class_count = len(classes)

    if class_count != 11:
        raise ValueError(
            "Expected 11 classes, "
            f"but found {class_count}."
        )

    label_map = {
        class_name: index
        for index, class_name
        in enumerate(classes)
    }

    existing_candidates = [
        path
        for path in CANDIDATE_PATHS
        if path.exists()
    ]

    if len(existing_candidates) < 2:
        searched = "\n".join(
            str(path)
            for path in CANDIDATE_PATHS
        )

        raise FileNotFoundError(
            "At least two candidate models "
            "are required.\n"
            f"Searched:\n{searched}"
        )

    print("=" * 72)
    print(
        "MODEL ENSEMBLE SELECTION "
        "- 11 CLASSES"
    )
    print("=" * 72)

    print("Classes:")

    for index, class_name in enumerate(
        classes
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    # --------------------------------------------------------
    # LOAD VALIDATION AND TEST
    # --------------------------------------------------------

    (
        X_val_raw,
        y_val,
        _,
    ) = training.load_split(
        "val",
        classes,
        label_map,
    )

    (
        X_test_raw,
        y_test,
        test_paths,
    ) = training.load_split(
        "test",
        classes,
        label_map,
    )

    print(
        "\nBuilding the same 266 "
        "motion features..."
    )

    X_val = training.convert_dataset(
        X_val_raw
    )

    X_test = training.convert_dataset(
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

    # --------------------------------------------------------
    # GET PROBABILITIES FROM EVERY CANDIDATE
    # --------------------------------------------------------

    model_data: list[dict] = []

    for path in existing_candidates:
        print(
            "\nLoading:",
            path.name,
        )

        model = tf.keras.models.load_model(
            path,
            compile=False,
        )

        expected_input = (
            training.SEQUENCE_LENGTH,
            training.MODEL_FEATURES,
        )

        model_input = tuple(
            model.input_shape[1:]
        )

        if model_input != expected_input:
            raise ValueError(
                f"{path.name} expects "
                f"{model_input}, not "
                f"{expected_input}."
            )

        val_probabilities = model.predict(
            X_val,
            verbose=0,
        )

        test_probabilities = model.predict(
            X_test,
            verbose=0,
        )

        (
            val_accuracy,
            val_macro_f1,
        ) = calculate_metrics(
            y_val,
            val_probabilities,
            class_count,
        )

        print(
            "Validation accuracy: "
            f"{val_accuracy:.2%}"
        )

        print(
            "Validation macro-F1: "
            f"{val_macro_f1:.4f}"
        )

        model_data.append(
            {
                "path": path,
                "val_probabilities":
                    val_probabilities,
                "test_probabilities":
                    test_probabilities,
                "val_accuracy":
                    val_accuracy,
                "val_macro_f1":
                    val_macro_f1,
            }
        )

        del model

        tf.keras.backend.clear_session()

    # --------------------------------------------------------
    # TEST EVERY POSSIBLE COMBINATION
    # --------------------------------------------------------

    combinations: list[dict] = []

    for combination_size in range(
        1,
        len(model_data) + 1,
    ):
        for indices in itertools.combinations(
            range(len(model_data)),
            combination_size,
        ):
            val_probabilities = np.mean(
                np.stack(
                    [
                        model_data[index][
                            "val_probabilities"
                        ]
                        for index in indices
                    ],
                    axis=0,
                ),
                axis=0,
            )

            test_probabilities = np.mean(
                np.stack(
                    [
                        model_data[index][
                            "test_probabilities"
                        ]
                        for index in indices
                    ],
                    axis=0,
                ),
                axis=0,
            )

            (
                val_accuracy,
                val_macro_f1,
            ) = calculate_metrics(
                y_val,
                val_probabilities,
                class_count,
            )

            combinations.append(
                {
                    "indices":
                        list(indices),

                    "model_names":
                        [
                            model_data[index][
                                "path"
                            ].name
                            for index in indices
                        ],

                    "val_accuracy":
                        val_accuracy,

                    "val_macro_f1":
                        val_macro_f1,

                    "val_probabilities":
                        val_probabilities,

                    "test_probabilities":
                        test_probabilities,
                }
            )

    # Select only using Validation.
    # The Test set is not used for selection.
    combinations.sort(
        key=lambda item: (
            item["val_macro_f1"],
            item["val_accuracy"],
            -len(item["indices"]),
        ),
        reverse=True,
    )

    print(
        "\nAll validation combinations:"
    )

    for item in combinations:
        names = "+".join(
            item["model_names"]
        )

        print(
            f"{names}: "
            f"accuracy="
            f"{item['val_accuracy']:.2%}, "
            f"macro-F1="
            f"{item['val_macro_f1']:.4f}"
        )

    selected = combinations[0]

    # --------------------------------------------------------
    # FINAL TEST OF THE SELECTED RUNTIME COMBINATION
    # --------------------------------------------------------

    test_probabilities = selected[
        "test_probabilities"
    ]

    test_predictions = np.argmax(
        test_probabilities,
        axis=1,
    )

    (
        test_accuracy,
        test_macro_f1,
    ) = calculate_metrics(
        y_test,
        test_probabilities,
        class_count,
    )

    report = classification_report(
        y_test,
        test_predictions,
        labels=np.arange(
            class_count
        ),
        target_names=classes,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        test_predictions,
        labels=np.arange(
            class_count
        ),
    )

    # --------------------------------------------------------
    # CALIBRATION FOR UNKNOWN-SIGN REJECTION
    # --------------------------------------------------------

    calibration = (
        training
        .calculate_rejection_settings(
            selected[
                "val_probabilities"
            ],
            y_val,
            classes,
        )
    )

    runtime_selection = {
        "feature_version":
            "motion_266_v1",

        "sequence_length":
            training.SEQUENCE_LENGTH,

        "model_features":
            training.MODEL_FEATURES,

        "classes":
            classes,

        "models":
            selected["model_names"],

        "validation_accuracy":
            selected[
                "val_accuracy"
            ],

        "validation_macro_f1":
            selected[
                "val_macro_f1"
            ],

        "test_accuracy":
            test_accuracy,

        "test_macro_f1":
            test_macro_f1,
    }

    # --------------------------------------------------------
    # SAVE RUNTIME SETTINGS
    # --------------------------------------------------------

    runtime_selection_path = (
        MODELS_ROOT
        / "runtime_selection_v2.json"
    )

    runtime_selection_path.write_text(
        json.dumps(
            runtime_selection,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    calibration_path = (
        MODELS_ROOT
        / "calibration_runtime_v2.json"
    )

    calibration_path.write_text(
        json.dumps(
            calibration,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report_path = (
        MODELS_ROOT
        / "classification_report_runtime_v2.txt"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    np.save(
        MODELS_ROOT
        / "confusion_matrix_runtime_v2.npy",
        matrix,
    )

    training.save_confusion_csv(
        matrix,
        classes,
        MODELS_ROOT
        / "confusion_matrix_runtime_v2.csv",
    )

    training.save_predictions_csv(
        y_test,
        test_probabilities,
        classes,
        test_paths,
        MODELS_ROOT
        / "test_predictions_runtime_v2.csv",
    )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 72
    )

    print(
        "SELECTED RUNTIME MODELS:"
    )

    for model_name in selected[
        "model_names"
    ]:
        print(
            f" - {model_name}"
        )

    print(
        "\nValidation accuracy: "
        f"{selected['val_accuracy']:.2%}"
    )

    print(
        "Validation macro-F1: "
        f"{selected['val_macro_f1']:.4f}"
    )

    print(
        "\n"
        + report
    )

    print(
        "Test accuracy:       "
        f"{test_accuracy:.2%}"
    )

    print(
        "Test macro-F1:       "
        f"{test_macro_f1:.4f}"
    )

    print(
        "Confidence threshold: "
        f"{calibration['confidence_threshold']:.3f}"
    )

    print(
        "Margin threshold:     "
        f"{calibration['margin_threshold']:.3f}"
    )

    print(
        "\nRuntime selection: "
        f"{runtime_selection_path}"
    )

    print(
        "Runtime calibration: "
        f"{calibration_path}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()