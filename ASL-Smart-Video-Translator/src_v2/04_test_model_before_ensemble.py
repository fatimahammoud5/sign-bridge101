from __future__ import annotations

import csv
import json

import numpy as np
import tensorflow as tf

from common import (
    FEATURES_ROOT,
    MODEL_PATH,
    LABELS_PATH,
    MODELS_ROOT,
    SEQUENCE_LENGTH,
    RAW_FEATURES,
    normalize_sequence,
)


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"Labels not found: {LABELS_PATH}"
        )

    labels = json.loads(
        LABELS_PATH.read_text(encoding="utf-8")
    )
    model = tf.keras.models.load_model(MODEL_PATH)

    rows: list[list[object]] = []
    total = 0
    correct = 0

    print("=" * 90)
    print("SAVED TEST FEATURES")
    print("=" * 90)

    for true_index, true_label in enumerate(labels):
        folder = FEATURES_ROOT / "test" / true_label

        for path in sorted(folder.glob("*.npy")):
            raw = np.load(path)

            if raw.shape != (SEQUENCE_LENGTH, RAW_FEATURES):
                print(f"[SKIP] {path}: {raw.shape}")
                continue

            sequence = normalize_sequence(raw)[None, ...]
            probabilities = model.predict(
                sequence,
                verbose=0,
            )[0]

            predicted_index = int(np.argmax(probabilities))
            predicted_label = labels[predicted_index]
            confidence = float(probabilities[predicted_index])

            total += 1
            is_correct = predicted_index == true_index
            correct += int(is_correct)

            rows.append(
                [
                    path.name,
                    true_label,
                    predicted_label,
                    confidence,
                    is_correct,
                ]
            )

            marker = "OK" if is_correct else "WRONG"
            print(
                f"{marker:5s} | "
                f"true={true_label:14s} | "
                f"pred={predicted_label:14s} | "
                f"conf={confidence:.1%} | "
                f"{path.name}"
            )

    output_path = MODELS_ROOT / "test_predictions_v2.csv"
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "file",
                "true_label",
                "predicted_label",
                "confidence",
                "correct",
            ]
        )
        writer.writerows(rows)

    print("\n" + "=" * 90)
    if total:
        print(f"Accuracy: {correct}/{total} = {correct / total:.2%}")
    else:
        print("No test files were found.")
    print(f"CSV: {output_path}")
    print("=" * 90)


if __name__ == "__main__":
    main()
