from pathlib import Path
import csv
import io
import random
import urllib.request
import urllib.parse

import numpy as np
import soundfile as sf


# ============================================================
# SETTINGS
# ============================================================

TARGET_COUNT = 100
TARGET_SAMPLE_RATE = 16000

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

CLASS_MAP = {
    "dog_bark": "dog",
    "siren": "siren",
    "aircraft": "airplane",
    "explosion": "fireworks",
}

META_URL = (
    "https://raw.githubusercontent.com/"
    "karolpiczak/ESC-50/master/meta/esc50.csv"
)

AUDIO_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "karolpiczak/ESC-50/master/audio/"
)

random.seed(42)
np.random.seed(42)


# ============================================================
# DOWNLOAD UTILITIES
# ============================================================

def download_bytes(url, retries=5):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "SignBridge-Dataset-Downloader"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=120,
            ) as response:
                return response.read()

        except Exception as error:
            last_error = error

            print(
                f"Request failed "
                f"({attempt}/{retries})"
            )
            print(error)

    raise last_error


# ============================================================
# AUDIO PROCESSING
# ============================================================

def normalize_audio(audio):
    audio = np.asarray(
        audio,
        dtype=np.float32,
    )

    peak = np.max(
        np.abs(audio)
    )

    if peak > 0:
        audio = audio / peak

    return audio


def augment_audio(audio, variation):
    audio = np.asarray(
        audio,
        dtype=np.float32,
    ).copy()

    mode = variation % 5

    if mode == 0:
        result = audio

    elif mode == 1:
        result = audio * 0.75

    elif mode == 2:
        result = audio * 1.10

    elif mode == 3:
        shift = int(
            len(audio) * 0.08
        )

        result = np.roll(
            audio,
            shift,
        )

    else:
        noise = np.random.normal(
            0.0,
            0.003,
            size=len(audio),
        ).astype(np.float32)

        result = audio + noise

    return np.clip(
        result,
        -1.0,
        1.0,
    ).astype(np.float32)


def save_audio(path, audio):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sf.write(
        str(path),
        audio,
        TARGET_SAMPLE_RATE,
        subtype="PCM_16",
    )


# ============================================================
# LOAD ESC-50 METADATA
# ============================================================

def load_metadata():
    print()
    print("Downloading ESC-50 metadata...")

    data = download_bytes(
        META_URL
    )

    text = data.decode(
        "utf-8"
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    rows = list(reader)

    print(
        f"Metadata rows found: {len(rows)}"
    )

    return rows


# ============================================================
# DOWNLOAD ORIGINAL FILES
# ============================================================

def download_class_files(
    rows,
    our_class,
    esc_category,
):
    print()
    print("=" * 70)
    print(
        f"PROCESSING: {our_class}"
    )
    print(
        f"ESC-50 category: {esc_category}"
    )
    print("=" * 70)

    output_dir = (
        DATASET_DIR
        / our_class
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    matching = [
        row
        for row in rows
        if row["category"]
        == esc_category
    ]

    print(
        f"Original clips found: "
        f"{len(matching)}"
    )

    original_paths = []

    for index, row in enumerate(
        matching,
        start=1,
    ):
        filename = row["filename"]

        destination = (
            output_dir
            / f"esc50_original_{index:03d}.wav"
        )

        original_paths.append(
            destination
        )

        if (
            destination.exists()
            and destination.stat().st_size > 0
        ):
            print(
                f"[{index:02d}/{len(matching):02d}] "
                f"SKIP {destination.name}"
            )
            continue

        url = (
            AUDIO_BASE_URL
            + urllib.parse.quote(
                filename
            )
        )

        print(
            f"[{index:02d}/{len(matching):02d}] "
            f"Downloading {filename}"
        )

        try:
            audio_bytes = download_bytes(
                url
            )

            temp_path = (
                output_dir
                / "_temp_download.wav"
            )

            temp_path.write_bytes(
                audio_bytes
            )

            audio, sr = sf.read(
                str(temp_path),
                dtype="float32",
            )

            temp_path.unlink(
                missing_ok=True
            )

            if audio.ndim > 1:
                audio = np.mean(
                    audio,
                    axis=1,
                )

            if sr != TARGET_SAMPLE_RATE:
                import librosa

                audio = librosa.resample(
                    audio,
                    orig_sr=sr,
                    target_sr=TARGET_SAMPLE_RATE,
                )

            audio = normalize_audio(
                audio
            )

            save_audio(
                destination,
                audio,
            )

            print(
                f"     OK -> "
                f"{destination.name}"
            )

        except Exception as error:
            print(
                f"     FAILED: {error}"
            )

    return original_paths


# ============================================================
# CREATE AUGMENTED FILES
# ============================================================

def create_augmented_files(
    our_class,
    original_paths,
):
    output_dir = (
        DATASET_DIR
        / our_class
    )

    valid_originals = [
        path
        for path in original_paths
        if path.exists()
    ]

    if not valid_originals:
        print(
            f"No valid originals for "
            f"{our_class}"
        )
        return

    current_count = len(
        valid_originals
    )

    print()
    print(
        f"Creating augmentations "
        f"until {TARGET_COUNT} files..."
    )

    augmentation_index = 1

    while (
        current_count
        < TARGET_COUNT
    ):
        source_path = valid_originals[
            (augmentation_index - 1)
            % len(valid_originals)
        ]

        audio, sr = sf.read(
            str(source_path),
            dtype="float32",
        )

        if audio.ndim > 1:
            audio = np.mean(
                audio,
                axis=1,
            )

        if sr != TARGET_SAMPLE_RATE:
            import librosa

            audio = librosa.resample(
                audio,
                orig_sr=sr,
                target_sr=TARGET_SAMPLE_RATE,
            )

        augmented = augment_audio(
            audio,
            augmentation_index,
        )

        destination = (
            output_dir
            / (
                f"esc50_augmented_"
                f"{augmentation_index:03d}.wav"
            )
        )

        if not destination.exists():
            save_audio(
                destination,
                augmented,
            )

        current_count += 1

        print(
            f"[{current_count:03d}/"
            f"{TARGET_COUNT:03d}] "
            f"{destination.name}"
        )

        augmentation_index += 1

    print()
    print(
        f"DONE: {our_class}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print(
        "SIGNBRIDGE - ESC-50 "
        "SELECTIVE DOWNLOADER"
    )
    print("=" * 70)

    rows = load_metadata()

    for (
        our_class,
        esc_category,
    ) in CLASS_MAP.items():

        originals = download_class_files(
            rows=rows,
            our_class=our_class,
            esc_category=esc_category,
        )

        create_augmented_files(
            our_class=our_class,
            original_paths=originals,
        )

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    for class_name in CLASS_MAP:
        folder = (
            DATASET_DIR
            / class_name
        )

        count = len(
            list(
                folder.glob(
                    "*.wav"
                )
            )
        )

        print(
            f"{class_name:12s}: "
            f"{count} WAV files"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()