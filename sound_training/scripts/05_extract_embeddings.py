from pathlib import Path
import json

import librosa
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000
MAX_FILES_PER_CLASS = 100

CLASSES = [
    "explosion",
    "drone",
    "dog_bark",
    "aircraft",
    "siren",
    "other",
]

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"
OUTPUT_DIR = BASE_DIR / "outputs"

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npz"
METADATA_FILE = OUTPUT_DIR / "embeddings_metadata.json"


# ============================================================
# LOAD YAMNET
# ============================================================

def load_yamnet():
    print("=" * 70)
    print("LOADING YAMNET")
    print("=" * 70)

    model = hub.load(
        "https://tfhub.dev/google/yamnet/1"
    )

    print("YAMNet loaded successfully.")

    return model


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
# EXTRACT ONE AUDIO FILE
# ============================================================

def extract_file_embeddings(
    yamnet,
    audio_path,
):
    waveform = load_audio(
        audio_path
    )

    waveform_tensor = tf.convert_to_tensor(
        waveform,
        dtype=tf.float32,
    )

    scores, embeddings, spectrogram = yamnet(
        waveform_tensor
    )

    embeddings = embeddings.numpy()

    if embeddings.ndim != 2:
        raise ValueError(
            f"Unexpected embedding shape: "
            f"{embeddings.shape}"
        )

    if embeddings.shape[1] != 1024:
        raise ValueError(
            f"Expected 1024 features, "
            f"got {embeddings.shape[1]}"
        )

    return embeddings


# ============================================================
# SOURCE ID
# ============================================================

def get_source_id(
    class_name,
    filename,
):
    stem = Path(
        filename
    ).stem.lower()

    # ESC-50 original
    if stem.startswith(
        "esc50_original_"
    ):
        number = stem.replace(
            "esc50_original_",
            "",
        )

        return (
            f"{class_name}_esc50_"
            f"{number}"
        )

    # ESC-50 augmentation
    if stem.startswith(
        "esc50_augmented_"
    ):
        number_text = stem.replace(
            "esc50_augmented_",
            "",
        )

        try:
            number = int(
                number_text
            )

            original_number = (
                (number - 1) % 40
            ) + 1

            return (
                f"{class_name}_esc50_"
                f"{original_number:03d}"
            )

        except ValueError:
            pass

    # Other datasets:
    # treat each file as its own source
    return (
        f"{class_name}_{stem}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("SIGNBRIDGE - YAMNET EMBEDDING EXTRACTION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    yamnet = load_yamnet()

    all_embeddings = []
    all_labels = []
    all_files = []
    all_source_ids = []

    failed_files = []
    class_counts = {}

    for class_index, class_name in enumerate(
        CLASSES
    ):
        class_dir = (
            DATASET_DIR
            / class_name
        )

        print()
        print("=" * 70)
        print(
            f"CLASS {class_index}: "
            f"{class_name}"
        )
        print("=" * 70)

        if not class_dir.exists():
            print(
                f"Missing folder: "
                f"{class_dir}"
            )

            class_counts[
                class_name
            ] = 0

            continue

        audio_files = sorted(
            [
                path
                for path in class_dir.rglob("*")
                if (
                    path.is_file()
                    and path.suffix.lower()
                    in SUPPORTED_EXTENSIONS
                )
            ]
        )

        # Keep first training prototype balanced
        audio_files = audio_files[
            :MAX_FILES_PER_CLASS
        ]

        print(
            f"Files selected: "
            f"{len(audio_files)}"
        )

        successful = 0

        for index, audio_path in enumerate(
            audio_files,
            start=1,
        ):
            print(
                f"[{index:03d}/"
                f"{len(audio_files):03d}] "
                f"{audio_path.name}"
            )

            try:
                embeddings = (
                    extract_file_embeddings(
                        yamnet,
                        audio_path,
                    )
                )

                source_id = get_source_id(
                    class_name,
                    audio_path.name,
                )

                for embedding in embeddings:
                    all_embeddings.append(
                        embedding.astype(
                            np.float32
                        )
                    )

                    all_labels.append(
                        class_index
                    )

                    all_files.append(
                        str(
                            audio_path.relative_to(
                                DATASET_DIR
                            )
                        )
                    )

                    all_source_ids.append(
                        source_id
                    )

                successful += 1

                print(
                    f"    OK - "
                    f"{len(embeddings)} embeddings"
                )

            except Exception as error:
                print(
                    f"    FAILED: {error}"
                )

                failed_files.append(
                    {
                        "class": class_name,
                        "file": str(audio_path),
                        "error": str(error),
                    }
                )

        class_counts[
            class_name
        ] = successful

        print()
        print(
            f"Successful files: "
            f"{successful}"
        )

    if not all_embeddings:
        print()
        print(
            "ERROR: no embeddings "
            "were extracted."
        )
        return

    X = np.stack(
        all_embeddings
    ).astype(
        np.float32
    )

    y = np.asarray(
        all_labels,
        dtype=np.int64,
    )

    files = np.asarray(
        all_files
    )

    source_ids = np.asarray(
        all_source_ids
    )

    print()
    print("=" * 70)
    print("FINAL EMBEDDING SHAPES")
    print("=" * 70)

    print(
        f"X shape: {X.shape}"
    )

    print(
        f"y shape: {y.shape}"
    )

    print(
        f"Feature dimension: "
        f"{X.shape[1]}"
    )

    np.savez_compressed(
        EMBEDDINGS_FILE,
        X=X,
        y=y,
        files=files,
        source_ids=source_ids,
    )

    metadata = {
        "classes": CLASSES,
        "sample_rate": SAMPLE_RATE,
        "max_files_per_class":
            MAX_FILES_PER_CLASS,
        "embedding_dimension": int(
            X.shape[1]
        ),
        "embedding_count": int(
            len(X)
        ),
        "class_file_counts":
            class_counts,
        "failed_files":
            failed_files,
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("Saved:")
    print(
        EMBEDDINGS_FILE
    )
    print(
        METADATA_FILE
    )

    print()
    print(
        f"Failed files: "
        f"{len(failed_files)}"
    )

    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()