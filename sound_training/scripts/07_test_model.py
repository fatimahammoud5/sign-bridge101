import os

# Reduce unnecessary TensorFlow messages.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

print("[1/8] Python script started.", flush=True)

from pathlib import Path
import sys

print("[2/8] Importing NumPy and Librosa...", flush=True)

import numpy as np
import librosa

print("[3/8] Importing TensorFlow...", flush=True)

import tensorflow as tf

print("[4/8] Importing TensorFlow Hub...", flush=True)

import tensorflow_hub as hub

print("[5/8] All libraries imported successfully.", flush=True)


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000

CLASSES = [
    "explosion",
    "drone",
    "dog_bark",
    "aircraft",
    "siren",
    "other",
]

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "sound_classifier.keras"
)


# ============================================================
# LOAD AUDIO
# ============================================================

def load_audio(audio_path):
    waveform, _ = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
    )

    waveform = waveform.astype(
        np.float32
    )

    if len(waveform) == 0:
        raise ValueError(
            "Audio file is empty."
        )

    return waveform


# ============================================================
# DISPLAY RESULTS
# ============================================================

def show_result(
    title,
    values,
):
    predicted_index = int(
        np.argmax(values)
    )

    predicted_label = CLASSES[
        predicted_index
    ]

    confidence = float(
        values[predicted_index]
    )

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print(
        f"Prediction : {predicted_label}"
    )

    print(
        f"Confidence : "
        f"{confidence * 100:.2f}%"
    )

    print()
    print("All class probabilities:")
    print()

    sorted_indices = np.argsort(
        values
    )[::-1]

    for index in sorted_indices:
        print(
            f"{CLASSES[index]:12s}: "
            f"{values[index] * 100:6.2f}%"
        )


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 70)
    print("SIGNBRIDGE - CUSTOM SOUND MODEL TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Check audio argument
    # --------------------------------------------------------

    if len(sys.argv) < 2:
        print()
        print(
            "ERROR: No audio file was provided."
        )

        print()
        print("Example:")

        print(
            'python scripts\\07_test_model.py '
            '"dataset\\explosion\\'
            'esc50_original_001.wav"'
        )

        return

    audio_path = Path(
        sys.argv[1]
    )

    # --------------------------------------------------------
    # Check audio file
    # --------------------------------------------------------

    print()
    print("[6/8] Checking audio file...", flush=True)

    print("Audio file:")
    print(audio_path)

    if not audio_path.exists():
        print()
        print("ERROR: File does not exist:")
        print(audio_path)
        return

    print("Audio file exists.")

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    print()
    print("Custom model:")
    print(MODEL_PATH)

    if not MODEL_PATH.exists():
        print()
        print(
            "ERROR: Custom model does not exist."
        )
        return

    # --------------------------------------------------------
    # Load YAMNet
    # --------------------------------------------------------

    print()
    print(
        "[7/8] Loading YAMNet...",
        flush=True,
    )

    yamnet = hub.load(
        "https://tfhub.dev/google/yamnet/1"
    )

    print(
        "YAMNet loaded successfully.",
        flush=True,
    )

    # --------------------------------------------------------
    # Load classifier
    # --------------------------------------------------------

    print()
    print(
        "Loading custom classifier...",
        flush=True,
    )

    classifier = tf.keras.models.load_model(
        MODEL_PATH
    )

    print(
        "Custom classifier loaded successfully.",
        flush=True,
    )

    # --------------------------------------------------------
    # Read audio
    # --------------------------------------------------------

    print()
    print(
        "Reading audio...",
        flush=True,
    )

    waveform = load_audio(
        audio_path
    )

    duration = (
        len(waveform)
        / SAMPLE_RATE
    )

    print(
        f"Duration: {duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # YAMNet embeddings
    # --------------------------------------------------------

    print()
    print(
        "Extracting YAMNet embeddings...",
        flush=True,
    )

    waveform_tensor = tf.convert_to_tensor(
        waveform,
        dtype=tf.float32,
    )

    _, embeddings, _ = yamnet(
        waveform_tensor
    )

    embeddings = (
        embeddings
        .numpy()
        .astype(np.float32)
    )

    print(
        f"Embeddings shape: "
        f"{embeddings.shape}"
    )

    if len(embeddings) == 0:
        print(
            "ERROR: YAMNet produced "
            "no embeddings."
        )
        return

    # --------------------------------------------------------
    # Custom classifier
    # --------------------------------------------------------

    print()
    print(
        "[8/8] Running custom classifier...",
        flush=True,
    )

    probabilities = classifier.predict(
        embeddings,
        verbose=0,
    )

    print(
        "Classifier finished.",
        flush=True,
    )

    # ========================================================
    # METHOD 1:
    # Average all windows
    # ========================================================

    average_probabilities = np.mean(
        probabilities,
        axis=0,
    )

    # ========================================================
    # METHOD 2:
    # Average strongest 3 windows FOR EACH CLASS
    # ========================================================

    top_k = min(
        3,
        probabilities.shape[0],
    )

    top3_probabilities = np.zeros(
        len(CLASSES),
        dtype=np.float32,
    )

    for class_index in range(
        len(CLASSES)
    ):
        class_scores = probabilities[
            :,
            class_index
        ]

        strongest_scores = np.sort(
            class_scores
        )[-top_k:]

        top3_probabilities[
            class_index
        ] = np.mean(
            strongest_scores
        )

    # Normalize so displayed values
    # approximately behave as probabilities.
    top3_sum = np.sum(
        top3_probabilities
    )

    if top3_sum > 0:
        top3_probabilities = (
            top3_probabilities
            / top3_sum
        )

    # ========================================================
    # METHOD 3:
    # Best individual audio window
    #
    # Important:
    # Choose ONE real YAMNet window,
    # rather than taking max independently
    # for every class.
    # ========================================================

    window_confidences = np.max(
        probabilities,
        axis=1,
    )

    best_window_index = int(
        np.argmax(
            window_confidences
        )
    )

    best_window_probabilities = probabilities[
        best_window_index
    ]

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    show_result(
        "AVERAGE OF ALL WINDOWS",
        average_probabilities,
    )

    show_result(
        "TOP 3 WINDOWS AVERAGE",
        top3_probabilities,
    )

    show_result(
        (
            "BEST SINGLE WINDOW "
            f"(window {best_window_index + 1})"
        ),
        best_window_probabilities,
    )

    # --------------------------------------------------------
    # Individual windows
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("INDIVIDUAL WINDOW RESULTS")
    print("=" * 70)

    for window_index, window_scores in enumerate(
        probabilities,
        start=1,
    ):
        predicted_index = int(
            np.argmax(
                window_scores
            )
        )

        confidence = float(
            window_scores[
                predicted_index
            ]
        )

        print(
            f"Window {window_index:02d}: "
            f"{CLASSES[predicted_index]:12s} "
            f"{confidence * 100:6.2f}%"
        )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()