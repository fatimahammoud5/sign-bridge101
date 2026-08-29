from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "ASL_Citizen_subset"
)

METADATA_ROOT = (
    DATASET_ROOT
    / "metadata"
)

PROPOSED_CLASSES_FILE = (
    PROJECT_ROOT
    / "classes_v2_proposed.txt"
)

OUTPUT_REPORT = (
    DATASET_ROOT
    / "final_target_word_report.csv"
)


# ============================================================
# POSSIBLE COLUMN NAMES
# ============================================================

GLOSS_COLUMNS = [
    "Gloss",
    "gloss",
    "Label",
    "label",
    "Word",
    "word",
]

VIDEO_COLUMNS = [
    "Video file",
    "video_file",
    "Video",
    "video",
    "Filename",
    "filename",
    "file",
]

PARTICIPANT_COLUMNS = [
    "Participant ID",
    "participant_id",
    "Participant",
    "participant",
    "User",
    "user",
    "Signer",
    "signer",
]

CODE_COLUMNS = [
    "ASL-LEX Code",
    "asl_lex_code",
    "ASLLEX Code",
    "asllex_code",
    "Code",
    "code",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()

    text = text.replace(
        "_",
        " ",
    )

    text = text.replace(
        "-",
        " ",
    )

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


def normalize_column(value: object) -> str:
    return normalize_text(
        value
    ).replace(
        " ",
        "_",
    )


def find_column(
    fieldnames: list[str],
    candidates: list[str],
) -> str | None:
    normalized_fields = {
        normalize_column(name): name
        for name in fieldnames
    }

    for candidate in candidates:
        normalized_candidate = (
            normalize_column(
                candidate
            )
        )

        if normalized_candidate in normalized_fields:
            return normalized_fields[
                normalized_candidate
            ]

    return None


# ============================================================
# SPLIT DETECTION
# ============================================================

def detect_split(
    path: Path,
) -> str | None:
    name = normalize_text(
        path.stem
    )

    if name in {
        "train",
        "training",
    }:
        return "train"

    if name in {
        "val",
        "valid",
        "validation",
        "dev",
    }:
        return "val"

    if name in {
        "test",
        "testing",
    }:
        return "test"

    return None


# ============================================================
# LOAD FINAL CLASSES
# ============================================================

def load_final_classes() -> list[str]:
    if not PROPOSED_CLASSES_FILE.exists():
        raise FileNotFoundError(
            "Missing proposed classes file:\n"
            f"{PROPOSED_CLASSES_FILE}"
        )

    classes = [
        line.strip().lower()
        for line in (
            PROPOSED_CLASSES_FILE
            .read_text(
                encoding="utf-8-sig"
            )
            .splitlines()
        )
        if line.strip()
    ]

    if len(classes) != 11:
        raise ValueError(
            "Expected 11 proposed classes, "
            f"but found {len(classes)}."
        )

    if len(set(classes)) != len(classes):
        raise ValueError(
            "Duplicate class names were found."
        )

    return classes


# ============================================================
# FIND METADATA FILES
# ============================================================

def find_metadata_files() -> list[Path]:
    if not METADATA_ROOT.exists():
        raise FileNotFoundError(
            "Metadata folder was not found:\n"
            f"{METADATA_ROOT}"
        )

    paths = []

    for path in METADATA_ROOT.rglob(
        "*.csv"
    ):
        if detect_split(path) is not None:
            paths.append(path)

    paths.sort(
        key=lambda item: str(item)
    )

    if not paths:
        raise FileNotFoundError(
            "No train.csv, val.csv or test.csv "
            "files were found."
        )

    return paths


# ============================================================
# BUILD REPORT
# ============================================================

def build_report(
    classes: list[str],
) -> list[dict[str, str]]:
    target_map = {
        normalize_text(class_name):
            class_name
        for class_name in classes
    }

    report_rows: list[
        dict[str, str]
    ] = []

    seen_rows: set[
        tuple[str, str, str, str]
    ] = set()

    metadata_files = (
        find_metadata_files()
    )

    print("Metadata files:")

    for path in metadata_files:
        print(
            " -",
            path,
        )

    for path in metadata_files:
        split = detect_split(
            path
        )

        if split is None:
            continue

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(
                file
            )

            fieldnames = [
                str(name).strip()
                for name in (
                    reader.fieldnames
                    or []
                )
                if name is not None
            ]

            gloss_column = find_column(
                fieldnames,
                GLOSS_COLUMNS,
            )

            video_column = find_column(
                fieldnames,
                VIDEO_COLUMNS,
            )

            participant_column = find_column(
                fieldnames,
                PARTICIPANT_COLUMNS,
            )

            code_column = find_column(
                fieldnames,
                CODE_COLUMNS,
            )

            if gloss_column is None:
                print(
                    "[SKIP] Missing gloss column:",
                    path,
                )
                continue

            if video_column is None:
                print(
                    "[SKIP] Missing video column:",
                    path,
                )
                continue

            print()
            print(
                f"Reading {split}: {path.name}"
            )

            print(
                "  Gloss:",
                gloss_column,
            )

            print(
                "  Video:",
                video_column,
            )

            print(
                "  Participant:",
                participant_column,
            )

            print(
                "  Code:",
                code_column,
            )

            for source_row in reader:
                gloss = str(
                    source_row.get(
                        gloss_column,
                        "",
                    )
                    or ""
                ).strip()

                normalized_gloss = normalize_text(
                    gloss
                )

                target = target_map.get(
                    normalized_gloss
                )

                if target is None:
                    continue

                filename = str(
                    source_row.get(
                        video_column,
                        "",
                    )
                    or ""
                ).strip()

                if not filename:
                    continue

                participant = (
                    str(
                        source_row.get(
                            participant_column,
                            "",
                        )
                        or ""
                    ).strip()
                    if participant_column
                    else ""
                )

                code = (
                    str(
                        source_row.get(
                            code_column,
                            "",
                        )
                        or ""
                    ).strip()
                    if code_column
                    else ""
                )

                unique_key = (
                    target,
                    split,
                    filename,
                    participant,
                )

                if unique_key in seen_rows:
                    continue

                seen_rows.add(
                    unique_key
                )

                report_rows.append(
                    {
                        "target":
                            target,

                        "split":
                            split,

                        "gloss":
                            gloss,

                        "code":
                            code,

                        "filename":
                            filename,

                        "user":
                            participant,

                        "metadata_file":
                            str(path),
                    }
                )

    report_rows.sort(
        key=lambda item: (
            classes.index(
                item["target"]
            ),
            (
                "train",
                "val",
                "test",
            ).index(
                item["split"]
            ),
            item["user"],
            item["filename"],
        )
    )

    return report_rows


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    rows: list[dict[str, str]],
) -> None:
    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "target",
        "split",
        "gloss",
        "code",
        "filename",
        "user",
        "metadata_file",
    ]

    with OUTPUT_REPORT.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# ============================================================
# PRINT COUNTS
# ============================================================

def print_counts(
    classes: list[str],
    rows: list[dict[str, str]],
) -> None:
    counts: dict[
        str,
        dict[str, int]
    ] = defaultdict(
        lambda: {
            "train": 0,
            "val": 0,
            "test": 0,
        }
    )

    participants: dict[
        str,
        set[str]
    ] = defaultdict(set)

    codes: dict[
        str,
        set[str]
    ] = defaultdict(set)

    for row in rows:
        target = row[
            "target"
        ]

        split = row[
            "split"
        ]

        counts[target][
            split
        ] += 1

        if row["user"]:
            participants[target].add(
                row["user"]
            )

        if row["code"]:
            codes[target].add(
                row["code"]
            )

    print()
    print("=" * 82)
    print("FINAL ASL CITIZEN TARGET REPORT")
    print("=" * 82)

    print(
        f"{'Word':14s}"
        f"{'Train':>9s}"
        f"{'Val':>9s}"
        f"{'Test':>9s}"
        f"{'Users':>9s}"
        f"{'Codes':>9s}"
    )

    print("-" * 82)

    blocking_errors = []

    for class_name in classes:
        values = counts[
            class_name
        ]

        print(
            f"{class_name:14s}"
            f"{values['train']:9d}"
            f"{values['val']:9d}"
            f"{values['test']:9d}"
            f"{len(participants[class_name]):9d}"
            f"{len(codes[class_name]):9d}"
        )

        if values["train"] < 12:
            blocking_errors.append(
                f"{class_name}: train "
                f"has only {values['train']}."
            )

        if values["val"] < 3:
            blocking_errors.append(
                f"{class_name}: val "
                f"has only {values['val']}."
            )

        if values["test"] < 3:
            blocking_errors.append(
                f"{class_name}: test "
                f"has only {values['test']}."
            )

        if len(codes[class_name]) != 1:
            blocking_errors.append(
                f"{class_name}: expected one "
                "ASL-LEX code, found "
                f"{len(codes[class_name])}."
            )

    print("-" * 82)

    print(
        "Total matching rows:",
        len(rows),
    )

    print(
        "Report:",
        OUTPUT_REPORT,
    )

    print("=" * 82)

    if blocking_errors:
        print()
        print("BLOCKING ERRORS:")

        for error in blocking_errors:
            print(
                " -",
                error,
            )

        raise SystemExit(1)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 82)
    print(
        "BUILD FINAL ASL CITIZEN REPORT"
    )
    print("=" * 82)

    classes = load_final_classes()

    print("Final classes:")

    for index, class_name in enumerate(
        classes
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    rows = build_report(
        classes
    )

    save_report(
        rows
    )

    print_counts(
        classes,
        rows,
    )


if __name__ == "__main__":
    main()