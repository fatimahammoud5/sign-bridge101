from __future__ import annotations

import csv
import io
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipInfo

from remotezip import RemoteZip


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "ASL_Citizen_subset"
)

METADATA_ROOT = (
    OUTPUT_ROOT
    / "metadata"
)

REPORT_PATH = (
    OUTPUT_ROOT
    / "target_word_report.csv"
)

METADATA_LIST_PATH = (
    OUTPUT_ROOT
    / "metadata_files.txt"
)


# ============================================================
# OFFICIAL MICROSOFT DATASET
# ============================================================

DATASET_URL = (
    "https://download.microsoft.com/download/"
    "b/8/8/"
    "b88c0bae-e6c1-43e1-8726-98cf5af36ca4/"
    "ASL_Citizen.zip"
)


# ============================================================
# OUR FINAL 11 WORDS
# ============================================================

TARGET_WORDS = [
    "computer",
    "yes",
    "no",
    "help",
    "want",
    "need",
    "drink",
    "eat",
    "who",
    "what",
    "now",
]


# لا نعامل الكلمات القريبة كأنها الفئة نفسها.
# تستخدم هذه القائمة للبحث الإضافي فقط، وليس للدمج التلقائي.

SEARCH_HINTS = {
    "computer": [
        "computer",
    ],
    "yes": [
        "yes",
    ],
    "no": [
        "no",
    ],
    "help": [
        "help",
    ],
    "want": [
        "want",
    ],
    "need": [
        "need",
    ],
    "drink": [
        "drink",
    ],
    "eat": [
        "eat",
    ],
    "who": [
        "who",
    ],
    "what": [
        "what",
    ],
    "now": [
        "now",
    ],
}


# ============================================================
# METADATA SETTINGS
# ============================================================

METADATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".json",
    ".txt",
}

# لا ننزل ملف metadata أكبر من 50 MB.
MAX_METADATA_SIZE = 50 * 1024 * 1024


# ============================================================
# POSSIBLE COLUMN NAMES
# ============================================================

GLOSS_COLUMNS = [
    "gloss",
    "label",
    "sign",
    "sign_gloss",
    "english",
    "word",
]

FILE_COLUMNS = [
    "filename",
    "file",
    "video",
    "video_file",
    "video_path",
    "path",
]

USER_COLUMNS = [
    "user",
    "user_id",
    "participant",
    "participant_id",
    "signer",
    "signer_id",
]

CODE_COLUMNS = [
    "code",
    "sign_code",
    "asl_lex_code",
    "asllex_code",
    "asl_lex",
]

SPLIT_COLUMNS = [
    "split",
    "dataset_split",
    "set",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value: object) -> str:
    """
    Normalize labels only for searching.

    The original gloss and Code are preserved in reports.
    """

    text = str(value or "").strip().lower()

    text = text.replace("_", " ")
    text = text.replace("-", " ")

    text = re.sub(
        r"[^a-z0-9 ]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalized_column_name(
    value: object,
) -> str:

    return normalize_text(
        value
    ).replace(
        " ",
        "_",
    )


def detect_split(
    metadata_path: Path,
    row: dict[str, str],
    split_column: str | None,
) -> str:

    if split_column:
        value = normalize_text(
            row.get(
                split_column,
                "",
            )
        )

        if value in {
            "train",
            "training",
        }:
            return "train"

        if value in {
            "val",
            "valid",
            "validation",
            "dev",
        }:
            return "val"

        if value in {
            "test",
            "testing",
        }:
            return "test"

    name = normalize_text(
        metadata_path.stem
    )

    if "train" in name:
        return "train"

    if (
        "validation" in name
        or "valid" in name
        or re.search(
            r"\bval\b",
            name,
        )
    ):
        return "val"

    if "test" in name:
        return "test"

    return "unknown"


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(
    fieldnames: list[str],
    candidates: list[str],
) -> str | None:

    normalized_map = {
        normalized_column_name(name): name
        for name in fieldnames
    }

    for candidate in candidates:
        normalized_candidate = (
            normalized_column_name(
                candidate
            )
        )

        if normalized_candidate in normalized_map:
            return normalized_map[
                normalized_candidate
            ]

    return None


# ============================================================
# REMOTE ZIP HELPERS
# ============================================================

def is_metadata_file(
    info: ZipInfo,
) -> bool:

    if info.is_dir():
        return False

    suffix = Path(
        info.filename
    ).suffix.lower()

    if suffix not in METADATA_EXTENSIONS:
        return False

    if info.file_size > MAX_METADATA_SIZE:
        return False

    return True


def safe_output_path(
    archive_name: str,
) -> Path:
    """
    Store metadata by filename while preventing directory traversal.
    """

    archive_path = Path(
        archive_name
    )

    safe_parts = [
        part
        for part in archive_path.parts
        if part not in {
            "",
            ".",
            "..",
            "/",
            "\\",
        }
    ]

    if not safe_parts:
        raise ValueError(
            f"Unsafe archive path: {archive_name}"
        )

    return METADATA_ROOT.joinpath(
        *safe_parts
    )


def extract_metadata_file(
    remote_zip: RemoteZip,
    info: ZipInfo,
) -> Path:

    destination = safe_output_path(
        info.filename
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with remote_zip.open(
        info.filename
    ) as source:

        with destination.open(
            "wb"
        ) as output:

            shutil.copyfileobj(
                source,
                output,
            )

    return destination


# ============================================================
# CSV READING
# ============================================================

def detect_delimiter(
    sample: str,
    suffix: str,
) -> str:

    if suffix == ".tsv":
        return "\t"

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:
        return ","


def read_table(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    raw_bytes = path.read_bytes()

    text = raw_bytes.decode(
        "utf-8-sig",
        errors="replace",
    )

    delimiter = detect_delimiter(
        text[:8192],
        path.suffix.lower(),
    )

    stream = io.StringIO(
        text
    )

    reader = csv.DictReader(
        stream,
        delimiter=delimiter,
    )

    fieldnames = [
        str(name).strip()
        for name in (
            reader.fieldnames
            or []
        )
        if name is not None
    ]

    rows: list[
        dict[str, str]
    ] = []

    for row in reader:

        cleaned_row = {
            str(key).strip():
                str(value or "").strip()
            for key, value in row.items()
            if key is not None
        }

        rows.append(
            cleaned_row
        )

    return fieldnames, rows


# ============================================================
# MATCH DATASET ROWS
# ============================================================

def find_target_for_gloss(
    gloss: str,
) -> str | None:

    normalized_gloss = normalize_text(
        gloss
    )

    for target, hints in SEARCH_HINTS.items():

        normalized_hints = {
            normalize_text(hint)
            for hint in hints
        }

        # Exact matching only.
        if normalized_gloss in normalized_hints:
            return target

    return None


def inspect_table(
    path: Path,
) -> list[dict[str, str]]:

    fieldnames, rows = read_table(
        path
    )

    if not fieldnames:
        return []

    gloss_column = find_column(
        fieldnames,
        GLOSS_COLUMNS,
    )

    filename_column = find_column(
        fieldnames,
        FILE_COLUMNS,
    )

    user_column = find_column(
        fieldnames,
        USER_COLUMNS,
    )

    code_column = find_column(
        fieldnames,
        CODE_COLUMNS,
    )

    split_column = find_column(
        fieldnames,
        SPLIT_COLUMNS,
    )

    # The official ASL Citizen loader uses:
    # row[0] = user
    # row[1] = filename
    # row[2] = gloss
    #
    # Use that layout only when named columns were not detected.

    if (
        gloss_column is None
        and len(fieldnames) >= 3
    ):
        gloss_column = fieldnames[2]

    if (
        filename_column is None
        and len(fieldnames) >= 2
    ):
        filename_column = fieldnames[1]

    if (
        user_column is None
        and len(fieldnames) >= 1
    ):
        user_column = fieldnames[0]

    if gloss_column is None:
        return []

    matches: list[
        dict[str, str]
    ] = []

    for row in rows:

        gloss = row.get(
            gloss_column,
            "",
        ).strip()

        target = find_target_for_gloss(
            gloss
        )

        if target is None:
            continue

        split = detect_split(
            path,
            row,
            split_column,
        )

        matches.append(
            {
                "target":
                    target,

                "split":
                    split,

                "gloss":
                    gloss,

                "code":
                    (
                        row.get(
                            code_column,
                            "",
                        ).strip()
                        if code_column
                        else ""
                    ),

                "filename":
                    (
                        row.get(
                            filename_column,
                            "",
                        ).strip()
                        if filename_column
                        else ""
                    ),

                "user":
                    (
                        row.get(
                            user_column,
                            "",
                        ).strip()
                        if user_column
                        else ""
                    ),

                "metadata_file":
                    str(path),
            }
        )

    if matches:

        print()
        print(
            f"Matches in: {path.name}"
        )

        print(
            "Columns:"
        )

        print(
            f"  gloss:    {gloss_column}"
        )

        print(
            f"  filename: {filename_column}"
        )

        print(
            f"  user:     {user_column}"
        )

        print(
            f"  code:     {code_column}"
        )

        print(
            f"  split:    {split_column}"
        )

    return matches


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    matches: list[dict[str, str]],
) -> None:

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "target",
        "split",
        "gloss",
        "code",
        "filename",
        "user",
        "metadata_file",
    ]

    with REPORT_PATH.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            matches
        )


# ============================================================
# DISPLAY SUMMARY
# ============================================================

def print_summary(
    matches: list[dict[str, str]],
) -> None:

    counts: dict[
        str,
        Counter[str],
    ] = defaultdict(
        Counter
    )

    codes: dict[
        str,
        set[str],
    ] = defaultdict(
        set
    )

    glosses: dict[
        str,
        set[str],
    ] = defaultdict(
        set
    )

    users: dict[
        str,
        set[str],
    ] = defaultdict(
        set
    )

    for item in matches:

        target = item[
            "target"
        ]

        counts[target][
            item["split"]
        ] += 1

        if item["code"]:
            codes[target].add(
                item["code"]
            )

        if item["gloss"]:
            glosses[target].add(
                item["gloss"]
            )

        if item["user"]:
            users[target].add(
                item["user"]
            )

    print()
    print("=" * 88)
    print("ASL CITIZEN TARGET-WORD REPORT")
    print("=" * 88)

    print(
        f"{'Word':12s}"
        f"{'Train':>9s}"
        f"{'Val':>9s}"
        f"{'Test':>9s}"
        f"{'Unknown':>10s}"
        f"{'Users':>9s}"
        f"{'Codes':>8s}"
    )

    print("-" * 88)

    for target in TARGET_WORDS:

        target_counts = counts[
            target
        ]

        print(
            f"{target:12s}"
            f"{target_counts['train']:9d}"
            f"{target_counts['val']:9d}"
            f"{target_counts['test']:9d}"
            f"{target_counts['unknown']:10d}"
            f"{len(users[target]):9d}"
            f"{len(codes[target]):8d}"
        )

        if glosses[target]:
            print(
                "  Glosses:",
                ", ".join(
                    sorted(
                        glosses[target]
                    )
                ),
            )

        if codes[target]:
            print(
                "  ASL-LEX Codes:",
                ", ".join(
                    sorted(
                        codes[target]
                    )
                ),
            )

    print("-" * 88)

    print(
        "Total matching rows:",
        len(matches),
    )

    print(
        "Report:",
        REPORT_PATH,
    )

    print("=" * 88)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    METADATA_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 88)
    print("ASL CITIZEN - REMOTE METADATA INSPECTION")
    print("=" * 88)

    print(
        "This script does not download "
        "the 42.8 GB archive."
    )

    print(
        "It attempts to read the ZIP index "
        "and extract metadata files only."
    )

    print()

    try:

        with RemoteZip(
            DATASET_URL
        ) as remote_zip:

            archive_entries = (
                remote_zip.infolist()
            )

            print(
                "Remote ZIP opened successfully."
            )

            print(
                "Archive entries:",
                len(archive_entries),
            )

            metadata_infos = [
                info
                for info in archive_entries
                if is_metadata_file(
                    info
                )
            ]

            print(
                "Small metadata files found:",
                len(metadata_infos),
            )

            if not metadata_infos:

                raise RuntimeError(
                    "No small CSV/TSV/JSON/TXT "
                    "files were found inside "
                    "the archive."
                )

            metadata_lines = []

            extracted_paths: list[
                Path
            ] = []

            for info in metadata_infos:

                metadata_lines.append(
                    (
                        f"{info.file_size:12d}  "
                        f"{info.filename}"
                    )
                )

                print(
                    "Downloading metadata:",
                    info.filename,
                    (
                        f"({info.file_size / 1024:.1f} KB)"
                    ),
                )

                extracted_path = (
                    extract_metadata_file(
                        remote_zip,
                        info,
                    )
                )

                extracted_paths.append(
                    extracted_path
                )

            METADATA_LIST_PATH.write_text(
                "\n".join(
                    metadata_lines
                )
                + "\n",
                encoding="utf-8",
            )

    except Exception as exc:

        print()
        print("=" * 88)
        print("SELECTIVE REMOTE ACCESS FAILED")
        print("=" * 88)

        print(
            type(exc).__name__
            + ": "
            + str(exc)
        )

        print()
        print(
            "This usually means that the "
            "download server did not allow "
            "the byte-range requests required "
            "to read individual ZIP members."
        )

        print(
            "Do not download the full archive yet."
        )

        print(
            "Send this complete error output "
            "so we can switch to the next "
            "small-download method."
        )

        raise SystemExit(
            1
        )

    all_matches: list[
        dict[str, str]
    ] = []

    print()
    print(
        "Inspecting extracted CSV/TSV files..."
    )

    for path in extracted_paths:

        if path.suffix.lower() not in {
            ".csv",
            ".tsv",
        }:
            continue

        try:

            matches = inspect_table(
                path
            )

            all_matches.extend(
                matches
            )

        except Exception as exc:

            print(
                f"[SKIP TABLE] {path}: {exc}"
            )

    save_report(
        all_matches
    )

    print_summary(
        all_matches
    )

    if not all_matches:

        print()
        print(
            "Metadata was downloaded, but no exact "
            "matches were found for the 11 words."
        )

        print(
            "The next step will inspect all available "
            "gloss names and ASL-LEX Codes."
        )


if __name__ == "__main__":
    main()