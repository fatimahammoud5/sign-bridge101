from __future__ import annotations

import csv
import hashlib
import os
import shutil
import tempfile
import time

from collections import defaultdict, deque
from pathlib import Path
from zipfile import ZipInfo

import cv2
import mediapipe as mp
import numpy as np

from remotezip import RemoteZip


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "ASL_Citizen_subset"
)

REPORT_PATH = (
    DATASET_ROOT
    / "target_word_report.csv"
)

OUTPUT_FEATURES_ROOT = (
    PROJECT_ROOT
    / "data"
    / "WLASL100"
    / "features_v2"
)

MANIFEST_PATH = (
    DATASET_ROOT
    / "streamed_features_manifest.csv"
)

FAILURE_LOG_PATH = (
    DATASET_ROOT
    / "streamed_features_failures.txt"
)


# ============================================================
# OFFICIAL REMOTE DATASET
# ============================================================

DATASET_URL = (
    "https://download.microsoft.com/download/"
    "b/8/8/"
    "b88c0bae-e6c1-43e1-8726-98cf5af36ca4/"
    "ASL_Citizen.zip"
)


# ============================================================
# TARGET WORDS AVAILABLE IN ASL CITIZEN
# ============================================================

AVAILABLE_TARGETS = [
    "computer",
    "yes",
    "no",
    "help",
    "need",
    "who",
    "now",
]


# ============================================================
# MAXIMUM NUMBER OF VIDEOS
# ============================================================

LIMITS_PER_SPLIT = {
    "train": 14,
    "val": 3,
    "test": 3,
}


# ============================================================
# FEATURE CONFIGURATION
# ============================================================

SEQUENCE_LENGTH = 30

RAW_FEATURES = 126

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
}


# ============================================================
# NETWORK SETTINGS
# ============================================================

DOWNLOAD_RETRIES = 3

RETRY_DELAY_SECONDS = 3

COPY_BUFFER_SIZE = 1024 * 1024


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
        PROJECT_ROOT
        / "models_v2"
        / "mediapipe"
        / "hand_landmarker.task"
    ),
    (
        PROJECT_ROOT
        / "models_v2"
        / "hand_landmarker.task"
    ),
    (
        PROJECT_ROOT
        / "hand_landmarker.task"
    ),
]


# ============================================================
# HELPERS
# ============================================================

def normalize_archive_path(
    value: str,
) -> str:
    return (
        str(value)
        .strip()
        .replace("\\", "/")
        .lstrip("/")
        .lower()
    )


def safe_text(
    value: object,
) -> str:
    return str(value or "").strip()


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
# MEDIAPIPE DETECTOR
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


def create_detector():
    options = HandLandmarkerOptions(
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

    return (
        HandLandmarker
        .create_from_options(
            options
        )
    )


# ============================================================
# READ TARGET REPORT
# ============================================================

def load_report_rows() -> list[dict[str, str]]:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            "Target report does not exist:\n"
            f"{REPORT_PATH}\n\n"
            "Run 00_inspect_asl_citizen_remote.py first."
        )

    rows: list[dict[str, str]] = []

    with REPORT_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            cleaned = {
                str(key).strip():
                    safe_text(value)
                for key, value in row.items()
                if key is not None
            }

            target = cleaned.get(
                "target",
                "",
            ).lower()

            split = cleaned.get(
                "split",
                "",
            ).lower()

            filename = cleaned.get(
                "filename",
                "",
            )

            if target not in AVAILABLE_TARGETS:
                continue

            if split not in LIMITS_PER_SPLIT:
                continue

            if not filename:
                continue

            cleaned["target"] = target
            cleaned["split"] = split

            rows.append(cleaned)

    if not rows:
        raise ValueError(
            "No usable ASL Citizen rows "
            "were found in the report."
        )

    return rows


# ============================================================
# DIVERSE SELECTION
# ============================================================

def select_diverse_rows(
    rows: list[dict[str, str]],
    limit: int,
) -> list[dict[str, str]]:
    """
    Select videos from different participants first.

    If a participant has multiple videos, the second video is
    selected only after every participant contributed once.
    """

    grouped: dict[
        str,
        deque[dict[str, str]]
    ] = {}

    for row in sorted(
        rows,
        key=lambda item: (
            item.get("user", ""),
            item.get("filename", ""),
        ),
    ):
        user = (
            row.get("user", "").strip()
            or "unknown-user"
        )

        grouped.setdefault(
            user,
            deque(),
        ).append(row)

    users = sorted(
        grouped.keys()
    )

    selected: list[
        dict[str, str]
    ] = []

    while (
        len(selected) < limit
        and users
    ):
        remaining_users: list[str] = []

        for user in users:
            queue = grouped[user]

            if queue:
                selected.append(
                    queue.popleft()
                )

            if queue:
                remaining_users.append(
                    user
                )

            if len(selected) >= limit:
                break

        users = remaining_users

    return selected


def build_selected_dataset(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    grouped: dict[
        tuple[str, str],
        list[dict[str, str]]
    ] = defaultdict(list)

    for row in rows:
        key = (
            row["target"],
            row["split"],
        )

        grouped[key].append(row)

    selected: list[
        dict[str, str]
    ] = []

    print()
    print("Selected ASL Citizen subset:")
    print("-" * 62)

    for target in AVAILABLE_TARGETS:
        for split in (
            "train",
            "val",
            "test",
        ):
            available = grouped[
                (target, split)
            ]

            limit = LIMITS_PER_SPLIT[
                split
            ]

            chosen = select_diverse_rows(
                available,
                limit,
            )

            selected.extend(chosen)

            print(
                f"{target:12s} "
                f"{split:5s}: "
                f"{len(chosen):2d} selected "
                f"from {len(available):2d}"
            )

    print("-" * 62)
    print(
        "Total videos selected:",
        len(selected),
    )

    return selected


# ============================================================
# ARCHIVE INDEX
# ============================================================

def is_video_entry(
    info: ZipInfo,
) -> bool:
    if info.is_dir():
        return False

    return (
        Path(
            info.filename
        ).suffix.lower()
        in VIDEO_EXTENSIONS
    )


def build_archive_indexes(
    archive_entries: list[ZipInfo],
) -> tuple[
    dict[str, str],
    dict[str, list[str]],
]:
    """
    Build indexes without downloading video contents.
    """

    exact_index: dict[
        str,
        str
    ] = {}

    basename_index: dict[
        str,
        list[str]
    ] = defaultdict(list)

    video_count = 0

    for info in archive_entries:
        if not is_video_entry(info):
            continue

        member_name = info.filename

        normalized = normalize_archive_path(
            member_name
        )

        basename = Path(
            normalized
        ).name

        exact_index[normalized] = (
            member_name
        )

        basename_index[
            basename
        ].append(
            member_name
        )

        video_count += 1

    print(
        "Video entries indexed:",
        video_count,
    )

    return (
        exact_index,
        basename_index,
    )


# ============================================================
# RESOLVE METADATA FILENAME TO ZIP MEMBER
# ============================================================

def resolve_archive_member(
    row: dict[str, str],
    exact_index: dict[str, str],
    basename_index: dict[str, list[str]],
) -> str | None:
    raw_filename = normalize_archive_path(
        row.get(
            "filename",
            "",
        )
    )

    if not raw_filename:
        return None

    direct_candidates = [
        raw_filename,
        f"asl_citizen/{raw_filename}",
        f"asl_citizen/videos/{raw_filename}",
        f"asl_citizen/video/{raw_filename}",
    ]

    for candidate in direct_candidates:
        if candidate in exact_index:
            return exact_index[candidate]

    basename = Path(
        raw_filename
    ).name

    possible_members = list(
        basename_index.get(
            basename,
            [],
        )
    )

    if not possible_members:
        return None

    # Prefer an exact suffix match.
    suffix_matches = [
        member
        for member in possible_members
        if (
            normalize_archive_path(
                member
            ).endswith(
                "/" + raw_filename
            )
            or normalize_archive_path(
                member
            ) == raw_filename
        )
    ]

    if len(suffix_matches) == 1:
        return suffix_matches[0]

    if suffix_matches:
        possible_members = suffix_matches

    # Use participant ID to resolve duplicate filenames.
    user = normalize_archive_path(
        row.get(
            "user",
            "",
        )
    )

    if user:
        user_matches = [
            member
            for member in possible_members
            if user in normalize_archive_path(
                member
            )
        ]

        if len(user_matches) == 1:
            return user_matches[0]

        if user_matches:
            possible_members = user_matches

    if len(possible_members) == 1:
        return possible_members[0]

    print(
        "[AMBIGUOUS]",
        row.get("filename", ""),
        "->",
        len(possible_members),
        "archive matches",
    )

    return None


# ============================================================
# TEMPORARY VIDEO DOWNLOAD
# ============================================================

def copy_remote_video_to_temp(
    remote_zip: RemoteZip,
    archive_member: str,
) -> Path:
    suffix = (
        Path(archive_member).suffix.lower()
        or ".mp4"
    )

    file_descriptor, temporary_name = (
        tempfile.mkstemp(
            prefix="asl_citizen_",
            suffix=suffix,
        )
    )

    os.close(file_descriptor)

    temporary_path = Path(
        temporary_name
    )

    try:
        with remote_zip.open(
            archive_member
        ) as source:
            with temporary_path.open(
                "wb"
            ) as destination:
                shutil.copyfileobj(
                    source,
                    destination,
                    length=COPY_BUFFER_SIZE,
                )

        if (
            not temporary_path.exists()
            or temporary_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "Downloaded temporary video is empty."
            )

        return temporary_path

    except Exception:
        temporary_path.unlink(
            missing_ok=True
        )

        raise


# ============================================================
# EXTRACT THE SAME 30 × 126 FEATURES
# ============================================================

def extract_video_features(
    video_path: Path,
) -> np.ndarray | None:
    capture = cv2.VideoCapture(
        str(video_path)
    )

    if not capture.isOpened():
        capture.release()
        return None

    try:
        total_frames = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        if total_frames <= 0:
            return None

        if (
            fps <= 0
            or not np.isfinite(fps)
        ):
            fps = 25.0

        target_indices = np.linspace(
            0,
            total_frames - 1,
            SEQUENCE_LENGTH,
        ).astype(int)

        target_index_set = set(
            target_indices.tolist()
        )

        selected_frames: dict[
            int,
            np.ndarray
        ] = {}

        frame_index = 0

        while True:
            success, frame = capture.read()

            if not success:
                break

            if frame_index in target_index_set:
                selected_frames[
                    frame_index
                ] = frame.copy()

            frame_index += 1

    finally:
        capture.release()

    if not selected_frames:
        return None

    detector = create_detector()

    sequence: list[
        np.ndarray
    ] = []

    previous_right = np.zeros(
        (21, 3),
        dtype=np.float32,
    )

    previous_left = np.zeros(
        (21, 3),
        dtype=np.float32,
    )

    previous_timestamp = -1

    detected_frames = 0

    try:
        for frame_index in sorted(
            selected_frames.keys()
        ):
            frame = selected_frames[
                frame_index
            ]

            if (
                frame is None
                or frame.size == 0
            ):
                continue

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            mp_image = mp.Image(
                image_format=(
                    mp.ImageFormat.SRGB
                ),
                data=rgb,
            )

            timestamp_ms = int(
                (
                    frame_index
                    / fps
                )
                * 1000
            )

            if (
                timestamp_ms
                <= previous_timestamp
            ):
                timestamp_ms = (
                    previous_timestamp
                    + 1
                )

            previous_timestamp = (
                timestamp_ms
            )

            result = (
                detector.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
            )

            current_right = None
            current_left = None

            for (
                hand_index,
                hand_landmarks,
            ) in enumerate(
                result.hand_landmarks
            ):
                if hand_index >= len(
                    result.handedness
                ):
                    continue

                handedness_list = (
                    result.handedness[
                        hand_index
                    ]
                )

                if not handedness_list:
                    continue

                hand_label = (
                    handedness_list[0]
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
                        for point
                        in hand_landmarks
                    ],
                    dtype=np.float32,
                )

                if landmarks.shape != (
                    21,
                    3,
                ):
                    continue

                if hand_label == "right":
                    current_right = landmarks

                elif hand_label == "left":
                    current_left = landmarks

            if current_right is not None:
                previous_right = (
                    current_right
                )

            if current_left is not None:
                previous_left = (
                    current_left
                )

            if (
                current_right is not None
                or current_left is not None
            ):
                detected_frames += 1

            frame_features = np.concatenate(
                [
                    previous_right.flatten(),
                    previous_left.flatten(),
                ]
            ).astype(np.float32)

            if frame_features.shape != (
                RAW_FEATURES,
            ):
                continue

            sequence.append(
                frame_features
            )

    finally:
        detector.close()

    if not sequence:
        return None

    if detected_frames == 0:
        return None

    sequence_array = np.asarray(
        sequence,
        dtype=np.float32,
    )

    if len(sequence_array) < SEQUENCE_LENGTH:
        missing_count = (
            SEQUENCE_LENGTH
            - len(sequence_array)
        )

        padding = np.repeat(
            sequence_array[-1:],
            missing_count,
            axis=0,
        )

        sequence_array = np.concatenate(
            [
                sequence_array,
                padding,
            ],
            axis=0,
        )

    elif len(sequence_array) > SEQUENCE_LENGTH:
        sequence_array = (
            sequence_array[
                :SEQUENCE_LENGTH
            ]
        )

    if sequence_array.shape != (
        SEQUENCE_LENGTH,
        RAW_FEATURES,
    ):
        return None

    if not np.all(
        np.isfinite(
            sequence_array
        )
    ):
        return None

    return sequence_array


# ============================================================
# OUTPUT NAMES
# ============================================================

def create_output_path(
    row: dict[str, str],
    archive_member: str,
) -> Path:
    target = row["target"]
    split = row["split"]

    identifier = hashlib.sha1(
        archive_member.encode(
            "utf-8"
        )
    ).hexdigest()[:12]

    original_stem = Path(
        row.get(
            "filename",
            "video",
        )
    ).stem

    safe_stem = "".join(
        character
        if (
            character.isalnum()
            or character in {
                "-",
                "_",
            }
        )
        else "_"
        for character in original_stem
    )

    if not safe_stem:
        safe_stem = "video"

    output_folder = (
        OUTPUT_FEATURES_ROOT
        / split
        / target
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        output_folder
        / (
            f"aslc_{safe_stem}_"
            f"{identifier}.npy"
        )
    )


# ============================================================
# MANIFEST
# ============================================================

MANIFEST_COLUMNS = [
    "target",
    "split",
    "user",
    "gloss",
    "code",
    "metadata_filename",
    "archive_member",
    "feature_path",
    "status",
    "message",
]


def append_manifest(
    item: dict[str, str],
) -> None:
    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_header = (
        not MANIFEST_PATH.exists()
        or MANIFEST_PATH.stat().st_size == 0
    )

    with MANIFEST_PATH.open(
        "a",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=MANIFEST_COLUMNS,
        )

        if write_header:
            writer.writeheader()

        writer.writerow(
            {
                column:
                    item.get(
                        column,
                        "",
                    )
                for column
                in MANIFEST_COLUMNS
            }
        )


# ============================================================
# PROCESS ONE VIDEO
# ============================================================

def process_video(
    remote_zip: RemoteZip,
    row: dict[str, str],
    archive_member: str,
) -> str:
    output_path = create_output_path(
        row,
        archive_member,
    )

    manifest_base = {
        "target":
            row.get("target", ""),

        "split":
            row.get("split", ""),

        "user":
            row.get("user", ""),

        "gloss":
            row.get("gloss", ""),

        "code":
            row.get("code", ""),

        "metadata_filename":
            row.get("filename", ""),

        "archive_member":
            archive_member,

        "feature_path":
            str(output_path),
    }

    if output_path.exists():
        append_manifest(
            {
                **manifest_base,
                "status": "exists",
                "message":
                    "Feature file already exists.",
            }
        )

        return "exists"

    last_error = None

    for attempt in range(
        1,
        DOWNLOAD_RETRIES + 1,
    ):
        temporary_video = None

        try:
            temporary_video = (
                copy_remote_video_to_temp(
                    remote_zip,
                    archive_member,
                )
            )

            sequence = (
                extract_video_features(
                    temporary_video
                )
            )

            if sequence is None:
                raise RuntimeError(
                    "MediaPipe could not extract "
                    "a valid 30x126 sequence."
                )

            np.save(
                output_path,
                sequence,
            )

            append_manifest(
                {
                    **manifest_base,
                    "status": "saved",
                    "message":
                        f"Saved on attempt {attempt}.",
                }
            )

            return "saved"

        except Exception as exc:
            last_error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print(
                f"    Attempt "
                f"{attempt}/"
                f"{DOWNLOAD_RETRIES} "
                f"failed: {last_error}"
            )

            if attempt < DOWNLOAD_RETRIES:
                time.sleep(
                    RETRY_DELAY_SECONDS
                )

        finally:
            if temporary_video is not None:
                temporary_video.unlink(
                    missing_ok=True
                )

    append_manifest(
        {
            **manifest_base,
            "status": "failed",
            "message":
                last_error or "Unknown error.",
        }
    )

    with FAILURE_LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            f"{row.get('target', '')},"
            f"{row.get('split', '')},"
            f"{archive_member},"
            f"{last_error}\n"
        )

    return "failed"


# ============================================================
# SUMMARY
# ============================================================

def count_asl_citizen_features() -> None:
    print()
    print("=" * 72)
    print("ASL CITIZEN FEATURE COUNTS")
    print("=" * 72)

    grand_total = 0

    for target in AVAILABLE_TARGETS:
        values = []

        for split in (
            "train",
            "val",
            "test",
        ):
            folder = (
                OUTPUT_FEATURES_ROOT
                / split
                / target
            )

            count = (
                len(
                    list(
                        folder.glob(
                            "aslc_*.npy"
                        )
                    )
                )
                if folder.exists()
                else 0
            )

            values.append(count)
            grand_total += count

        print(
            f"{target:12s} "
            f"train={values[0]:2d} "
            f"val={values[1]:2d} "
            f"test={values[2]:2d} "
            f"total={sum(values):2d}"
        )

    print("-" * 72)
    print(
        "Total ASL Citizen features:",
        grand_total,
    )
    print("=" * 72)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    DATASET_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 88)
    print(
        "ASL CITIZEN REMOTE STREAMING "
        "AND FEATURE EXTRACTION"
    )
    print("=" * 88)

    print(
        "The complete 42.8 GB archive "
        "will NOT be downloaded."
    )

    print(
        "Each selected video is downloaded "
        "temporarily, processed, then deleted."
    )

    print(
        "Saved output consists only of "
        "30x126 .npy feature files."
    )

    print()
    print(
        "MediaPipe model:",
        HAND_MODEL_PATH,
    )

    rows = load_report_rows()

    selected_rows = (
        build_selected_dataset(
            rows
        )
    )

    saved_count = 0
    existing_count = 0
    failed_count = 0
    unresolved_count = 0

    with RemoteZip(
        DATASET_URL
    ) as remote_zip:
        archive_entries = (
            remote_zip.infolist()
        )

        (
            exact_index,
            basename_index,
        ) = build_archive_indexes(
            archive_entries
        )

        total = len(
            selected_rows
        )

        for index, row in enumerate(
            selected_rows,
            start=1,
        ):
            print()
            print(
                f"[{index}/{total}] "
                f"{row['split']}/"
                f"{row['target']} "
                f"| {row.get('filename', '')}"
            )

            archive_member = (
                resolve_archive_member(
                    row,
                    exact_index,
                    basename_index,
                )
            )

            if archive_member is None:
                unresolved_count += 1

                message = (
                    "Could not resolve metadata "
                    "filename inside remote ZIP."
                )

                print(
                    "  [UNRESOLVED]",
                    message,
                )

                append_manifest(
                    {
                        "target":
                            row.get("target", ""),

                        "split":
                            row.get("split", ""),

                        "user":
                            row.get("user", ""),

                        "gloss":
                            row.get("gloss", ""),

                        "code":
                            row.get("code", ""),

                        "metadata_filename":
                            row.get("filename", ""),

                        "archive_member":
                            "",

                        "feature_path":
                            "",

                        "status":
                            "unresolved",

                        "message":
                            message,
                    }
                )

                continue

            print(
                "  Remote member:",
                archive_member,
            )

            status = process_video(
                remote_zip,
                row,
                archive_member,
            )

            if status == "saved":
                saved_count += 1
                print(
                    "  [SAVED] Feature extracted."
                )

            elif status == "exists":
                existing_count += 1
                print(
                    "  [EXISTS] Already processed."
                )

            else:
                failed_count += 1
                print(
                    "  [FAILED] See failure log."
                )

    print()
    print("=" * 88)
    print("REMOTE EXTRACTION COMPLETE")
    print("=" * 88)
    print(
        f"Selected:   "
        f"{len(selected_rows)}"
    )
    print(
        f"Saved:      "
        f"{saved_count}"
    )
    print(
        f"Existing:   "
        f"{existing_count}"
    )
    print(
        f"Failed:     "
        f"{failed_count}"
    )
    print(
        f"Unresolved: "
        f"{unresolved_count}"
    )
    print(
        "Manifest:",
        MANIFEST_PATH,
    )
    print(
        "Failures:",
        FAILURE_LOG_PATH,
    )
    print("=" * 88)

    count_asl_citizen_features()


if __name__ == "__main__":
    main()
    