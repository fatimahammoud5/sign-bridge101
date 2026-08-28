from __future__ import annotations

import csv
import os
import re
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path

import cv2


# ============================================================
# PATHS
# ============================================================

# sign_bridge/backend
BACKEND_ROOT = Path(__file__).resolve().parent

# Final dictionary data used by Flask / Flutter
DICTIONARY_DIR = BACKEND_ROOT / "dictionary_data"
DICTIONARY_VIDEOS_DIR = DICTIONARY_DIR / "videos"
DICTIONARY_DB_PATH = DICTIONARY_DIR / "dictionary.db"


# ============================================================
# ASL CITIZEN WORKSPACE
# ============================================================

# Default workspace created outside the project:
# C:\Users\<USER>\Documents\ASL_Citizen_Dictionary
#
# You can override it without editing this file by setting:
# ASL_CITIZEN_DICTIONARY_DIR

DEFAULT_ASL_CITIZEN_WORKSPACE = (
    Path.home()
    / "Documents"
    / "ASL_Citizen_Dictionary"
)

ASL_CITIZEN_WORKSPACE = Path(
    os.environ.get(
        "ASL_CITIZEN_DICTIONARY_DIR",
        str(DEFAULT_ASL_CITIZEN_WORKSPACE),
    )
).expanduser().resolve()

SOURCE_VIDEOS_DIR = ASL_CITIZEN_WORKSPACE / "videos"
MANIFEST_PATH = ASL_CITIZEN_WORKSPACE / "dictionary_manifest.csv"

DATASET_NAME = "ASL Citizen"


# ============================================================
# HELPERS
# ============================================================

def normalize_word(value: str) -> str:
    value = str(value).strip().upper()

    return re.sub(
        r"[^A-Z0-9]+",
        "",
        value,
    )


def extract_letter(word: str) -> str:
    word = normalize_word(word)

    if not word:
        return "#"

    first = word[0]

    if "A" <= first <= "Z":
        return first

    return "#"


def video_is_valid(video_path: Path) -> bool:
    try:
        if not video_path.exists():
            return False

        if video_path.stat().st_size < 10_000:
            return False

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():
            capture.release()
            return False

        success, frame = capture.read()

        capture.release()

        if not success:
            return False

        if frame is None:
            return False

        return True

    except Exception:
        return False


# ============================================================
# DATABASE
# ============================================================

def create_database() -> None:
    DICTIONARY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    DICTIONARY_VIDEOS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DICTIONARY_DB_PATH
    )

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dictionary_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                word TEXT NOT NULL,

                normalized_word TEXT
                    NOT NULL UNIQUE,

                letter TEXT NOT NULL,

                video_filename TEXT
                    NOT NULL,

                original_dataset TEXT
                    NOT NULL DEFAULT 'ASL Citizen',

                original_split TEXT
                    NOT NULL DEFAULT '',

                original_folder TEXT
                    NOT NULL DEFAULT '',

                original_video_name TEXT
                    NOT NULL DEFAULT '',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # Migrate an older dictionary database safely.
        # ----------------------------------------------------

        columns = connection.execute(
            """
            PRAGMA table_info(dictionary_signs)
            """
        ).fetchall()

        existing_columns = {
            row[1]
            for row in columns
        }

        migrations = {
            "original_dataset":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_dataset TEXT
                NOT NULL DEFAULT 'ASL Citizen'
                """,

            "original_split":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_split TEXT
                NOT NULL DEFAULT ''
                """,

            "original_folder":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_folder TEXT
                NOT NULL DEFAULT ''
                """,

            "original_video_name":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_video_name TEXT
                NOT NULL DEFAULT ''
                """,

            "created_at":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN created_at TIMESTAMP
                """,
        }

        for column_name, sql in migrations.items():
            if column_name not in existing_columns:
                print(
                    "Migrating dictionary column:",
                    column_name,
                )

                connection.execute(sql)

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_dictionary_signs_word
            ON dictionary_signs(normalized_word)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_dictionary_signs_letter
            ON dictionary_signs(letter)
            """
        )

        connection.commit()

    finally:
        connection.close()


def clear_dictionary() -> None:
    connection = sqlite3.connect(
        DICTIONARY_DB_PATH
    )

    try:
        connection.execute(
            """
            DELETE FROM dictionary_signs
            """
        )

        # Reset AUTOINCREMENT so the rebuilt dictionary starts
        # from id = 1 again.
        connection.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name = 'dictionary_signs'
            """
        )

        connection.commit()

    finally:
        connection.close()

    # Remove every old dictionary video, including the WLASL ones.
    if DICTIONARY_VIDEOS_DIR.exists():
        for file in DICTIONARY_VIDEOS_DIR.iterdir():
            if not file.is_file():
                continue

            try:
                file.unlink()
            except OSError:
                pass


def insert_sign(
    connection: sqlite3.Connection,
    *,
    word: str,
    video_filename: str,
    original_split: str,
    original_folder: str,
    original_video_name: str,
) -> None:
    connection.execute(
        """
        INSERT INTO dictionary_signs (
            word,
            normalized_word,
            letter,
            video_filename,
            original_dataset,
            original_split,
            original_folder,
            original_video_name
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            word,
            normalize_word(word),
            extract_letter(word),
            video_filename,
            DATASET_NAME,
            original_split,
            original_folder,
            original_video_name,
        ),
    )


# ============================================================
# MANIFEST
# ============================================================

def load_manifest() -> list[dict[str, str]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            "Dictionary manifest was not found:\n"
            f"{MANIFEST_PATH}\n\n"
            "Run 03_download_dictionary_words.py first."
        )

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        fieldnames = set(
            reader.fieldnames or []
        )

        required = {
            "word",
            "video_filename",
        }

        missing = required - fieldnames

        if missing:
            raise RuntimeError(
                "dictionary_manifest.csv is missing columns: "
                + ", ".join(sorted(missing))
            )

        rows = []

        for row in reader:
            word = str(
                row.get("word", "")
            ).strip().upper()

            video_filename = str(
                row.get("video_filename", "")
            ).strip()

            if not word or not video_filename:
                continue

            rows.append(
                {
                    "word": word,
                    "video_filename": video_filename,
                    "split": str(
                        row.get("split", "")
                    ).strip(),
                    "original_video": str(
                        row.get("original_video", "")
                    ).strip(),
                    "gloss": str(
                        row.get("gloss", "")
                    ).strip(),
                }
            )

    # One dictionary entry per normalized word.
    unique_rows: dict[str, dict[str, str]] = {}

    for row in rows:
        key = normalize_word(
            row["word"]
        )

        if not key:
            continue

        unique_rows.setdefault(
            key,
            row,
        )

    result = list(
        unique_rows.values()
    )

    result.sort(
        key=lambda item: item["word"]
    )

    return result


# ============================================================
# PREPARE FINAL PROJECT DICTIONARY
# ============================================================

def prepare_dictionary() -> None:
    print()
    print("=" * 72)
    print("SIGNBRIDGE - ASL CITIZEN DICTIONARY IMPORT")
    print("=" * 72)

    print()
    print("ASL Citizen workspace:")
    print(ASL_CITIZEN_WORKSPACE)

    print()
    print("Source videos:")
    print(SOURCE_VIDEOS_DIR)

    print()
    print("Manifest:")
    print(MANIFEST_PATH)

    print()
    print("Final backend videos:")
    print(DICTIONARY_VIDEOS_DIR)

    print()
    print("Final database:")
    print(DICTIONARY_DB_PATH)

    print()

    if not ASL_CITIZEN_WORKSPACE.exists():
        print("[ERROR] ASL Citizen workspace does not exist.")
        return

    if not SOURCE_VIDEOS_DIR.exists():
        print("[ERROR] Source videos folder does not exist.")
        return

    if not MANIFEST_PATH.exists():
        print("[ERROR] dictionary_manifest.csv does not exist.")
        print("Run 03_download_dictionary_words.py first.")
        return

    manifest_rows = load_manifest()

    print(
        "Manifest words:",
        len(manifest_rows),
    )

    if not manifest_rows:
        print("[ERROR] Manifest contains no words.")
        return

    # --------------------------------------------------------
    # Validate source videos BEFORE deleting old dictionary.
    # --------------------------------------------------------

    valid_rows = []
    invalid_rows = []

    print()
    print("Checking downloaded ASL Citizen videos...")
    print()

    for index, row in enumerate(
        manifest_rows,
        start=1,
    ):
        source_path = (
            SOURCE_VIDEOS_DIR
            / row["video_filename"]
        )

        print(
            f"[{index:03d}/{len(manifest_rows):03d}] "
            f"{row['word']:<18}",
            end=" ",
        )

        if not source_path.exists():
            print("MISSING")
            invalid_rows.append(
                (row, "missing")
            )
            continue

        if not video_is_valid(source_path):
            print("INVALID")
            invalid_rows.append(
                (row, "invalid")
            )
            continue

        print("OK")
        valid_rows.append(row)

    print()
    print(
        "Valid videos  :",
        len(valid_rows),
    )
    print(
        "Invalid/missing:",
        len(invalid_rows),
    )

    if not valid_rows:
        print()
        print("[ERROR] No valid videos to import.")
        print("Old dictionary was NOT deleted.")
        return

    # We allow a few failed items, but show them clearly.
    if invalid_rows:
        print()
        print("The following words will NOT be imported:")

        for row, reason in invalid_rows:
            print(
                f"  - {row['word']} ({reason})"
            )

    # --------------------------------------------------------
    # Rebuild final backend dictionary.
    # --------------------------------------------------------

    create_database()
    clear_dictionary()

    connection = sqlite3.connect(
        DICTIONARY_DB_PATH
    )

    imported_count = 0
    distribution: dict[str, list[str]] = defaultdict(list)

    try:
        for index, row in enumerate(
            valid_rows,
            start=1,
        ):
            word = row["word"]

            source_path = (
                SOURCE_VIDEOS_DIR
                / row["video_filename"]
            )

            # Keep all final videos together in ONE folder.
            destination_name = (
                normalize_word(word).lower()
                + source_path.suffix.lower()
            )

            if not source_path.suffix:
                destination_name = (
                    normalize_word(word).lower()
                    + ".mp4"
                )

            destination = (
                DICTIONARY_VIDEOS_DIR
                / destination_name
            )

            print(
                f"[{index:03d}/{len(valid_rows):03d}] "
                f"{word:<18}",
                end=" ",
            )

            shutil.copy2(
                source_path,
                destination,
            )

            insert_sign(
                connection,
                word=word,
                video_filename=destination_name,
                original_split=row["split"],
                original_folder="ASL_Citizen_Dictionary/videos",
                original_video_name=(
                    row["original_video"]
                    or row["video_filename"]
                ),
            )

            imported_count += 1

            distribution[
                extract_letter(word)
            ].append(word)

            print(
                f"COPIED -> {destination_name}"
            )

        connection.commit()

    finally:
        connection.close()

    # --------------------------------------------------------
    # Verify final DB.
    # --------------------------------------------------------

    connection = sqlite3.connect(
        DICTIONARY_DB_PATH
    )

    try:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM dictionary_signs
            """
        ).fetchone()

        database_count = (
            int(row[0])
            if row
            else 0
        )

    finally:
        connection.close()

    final_video_count = len(
        [
            path
            for path in DICTIONARY_VIDEOS_DIR.iterdir()
            if path.is_file()
        ]
    )

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("FINAL A-Z DISTRIBUTION")
    print("=" * 72)

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        words = distribution.get(
            letter,
            [],
        )

        print()
        print(
            f"{letter}: {len(words)}"
        )

        if words:
            print(
                "   "
                + ", ".join(words)
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("DONE")
    print("=" * 72)

    print(
        "Imported database rows :",
        database_count,
    )

    print(
        "Final video files      :",
        final_video_count,
    )

    print(
        "Dataset source         :",
        DATASET_NAME,
    )

    print()
    print("Database:")
    print(DICTIONARY_DB_PATH)

    print()
    print("Videos:")
    print(DICTIONARY_VIDEOS_DIR)

    print()
    print(
        "All dictionary videos are now inside ONE backend folder."
    )

    print("=" * 72)
    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    prepare_dictionary()