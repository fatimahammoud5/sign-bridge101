from __future__ import annotations

import csv
import importlib.util
from collections import defaultdict
from pathlib import Path

from remotezip import RemoteZip


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_ROOT = PROJECT_ROOT / "src_v2"

DATASET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "ASL_Citizen_subset"
)

BASE_STREAM_SCRIPT = (
    SRC_ROOT
    / "01_stream_asl_citizen_features.py"
)

FINAL_REPORT_PATH = (
    DATASET_ROOT
    / "final_target_word_report.csv"
)

FINAL_CLASSES_FILE = (
    PROJECT_ROOT
    / "classes_v2_proposed.txt"
)

FILL_MANIFEST_PATH = (
    DATASET_ROOT
    / "fill_missing_manifest.csv"
)

FILL_FAILURE_LOG_PATH = (
    DATASET_ROOT
    / "fill_missing_failures.txt"
)


# ============================================================
# REQUIRED COUNTS
# ============================================================

LIMITS = {
    "train": 14,
    "val": 3,
    "test": 3,
}


# ============================================================
# LOAD BASE STREAMING MODULE
# ============================================================

def load_stream_module():
    if not BASE_STREAM_SCRIPT.exists():
        raise FileNotFoundError(
            "Base streaming script was not found:\n"
            f"{BASE_STREAM_SCRIPT}"
        )

    specification = (
        importlib.util.spec_from_file_location(
            "asl_citizen_stream_base",
            BASE_STREAM_SCRIPT,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Could not load the base "
            "streaming script."
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
# LOAD FINAL CLASSES
# ============================================================

def load_final_classes() -> list[str]:
    if not FINAL_CLASSES_FILE.exists():
        raise FileNotFoundError(
            "Final proposed classes file "
            "was not found:\n"
            f"{FINAL_CLASSES_FILE}"
        )

    classes = [
        line.strip().lower()
        for line in (
            FINAL_CLASSES_FILE
            .read_text(
                encoding="utf-8-sig"
            )
            .splitlines()
        )
        if line.strip()
    ]

    if len(classes) != 11:
        raise ValueError(
            "Expected 11 classes, "
            f"but found {len(classes)}."
        )

    if len(set(classes)) != len(classes):
        raise ValueError(
            "Duplicate classes were found."
        )

    return classes


# ============================================================
# LOAD FINAL REPORT
# ============================================================

def load_report_rows(
    classes: list[str],
) -> list[dict[str, str]]:
    if not FINAL_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Final report was not found:\n"
            f"{FINAL_REPORT_PATH}"
        )

    rows: list[dict[str, str]] = []

    with FINAL_REPORT_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for source_row in reader:
            row = {
                str(key).strip():
                    str(value or "").strip()
                for key, value
                in source_row.items()
                if key is not None
            }

            target = row.get(
                "target",
                "",
            ).lower()

            split = row.get(
                "split",
                "",
            ).lower()

            filename = row.get(
                "filename",
                "",
            )

            if target not in classes:
                continue

            if split not in LIMITS:
                continue

            if not filename:
                continue

            row["target"] = target
            row["split"] = split

            rows.append(row)

    if not rows:
        raise ValueError(
            "No usable rows were found "
            "in the final report."
        )

    return rows


# ============================================================
# COUNT EXISTING FEATURES
# ============================================================

def count_existing_features(
    stream,
    target: str,
    split: str,
) -> int:
    folder = (
        stream.OUTPUT_FEATURES_ROOT
        / split
        / target
    )

    if not folder.exists():
        return 0

    return len(
        list(
            folder.glob(
                "aslc_*.npy"
            )
        )
    )


# ============================================================
# PRINT CURRENT COUNTS
# ============================================================

def print_counts(
    stream,
    classes: list[str],
    available_counts: dict[
        tuple[str, str],
        int,
    ],
) -> int:
    print()
    print("=" * 78)
    print("FINAL ASL CITIZEN FEATURE COUNTS")
    print("=" * 78)

    print(
        f"{'Word':14s}"
        f"{'Train':>9s}"
        f"{'Val':>9s}"
        f"{'Test':>9s}"
        f"{'Total':>9s}"
    )

    print("-" * 78)

    grand_total = 0
    missing_total = 0

    for target in classes:
        values = {}

        for split in (
            "train",
            "val",
            "test",
        ):
            count = count_existing_features(
                stream,
                target,
                split,
            )

            values[split] = count

            available = available_counts.get(
                (target, split),
                0,
            )

            goal = min(
                LIMITS[split],
                available,
            )

            if count < goal:
                missing_total += (
                    goal - count
                )

        total = (
            values["train"]
            + values["val"]
            + values["test"]
        )

        grand_total += total

        print(
            f"{target:14s}"
            f"{values['train']:9d}"
            f"{values['val']:9d}"
            f"{values['test']:9d}"
            f"{total:9d}"
        )

    print("-" * 78)

    print(
        "Total feature files:",
        grand_total,
    )

    print(
        "Still missing:",
        missing_total,
    )

    print("=" * 78)

    return missing_total


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 88)
    print(
        "FILL MISSING ASL CITIZEN FEATURES"
    )
    print("=" * 88)

    classes = load_final_classes()

    stream = load_stream_module()

    stream.AVAILABLE_TARGETS = classes

    stream.MANIFEST_PATH = (
        FILL_MANIFEST_PATH
    )

    stream.FAILURE_LOG_PATH = (
        FILL_FAILURE_LOG_PATH
    )

    rows = load_report_rows(
        classes
    )

    grouped: dict[
        tuple[str, str],
        list[dict[str, str]],
    ] = defaultdict(list)

    for row in rows:
        grouped[
            (
                row["target"],
                row["split"],
            )
        ].append(row)

    available_counts = {
        key: len(value)
        for key, value
        in grouped.items()
    }

    initial_missing = print_counts(
        stream,
        classes,
        available_counts,
    )

    if initial_missing == 0:
        print()
        print(
            "Nothing is missing. "
            "The dataset is already complete."
        )

        return

    print()
    print(
        "Opening the remote ASL Citizen archive..."
    )

    saved_count = 0
    failed_count = 0
    unresolved_count = 0

    with RemoteZip(
        stream.DATASET_URL
    ) as remote_zip:
        archive_entries = (
            remote_zip.infolist()
        )

        (
            exact_index,
            basename_index,
        ) = stream.build_archive_indexes(
            archive_entries
        )

        for target in classes:
            for split in (
                "train",
                "val",
                "test",
            ):
                candidates = grouped.get(
                    (target, split),
                    [],
                )

                if not candidates:
                    continue

                goal = min(
                    LIMITS[split],
                    len(candidates),
                )

                existing = count_existing_features(
                    stream,
                    target,
                    split,
                )

                needed = max(
                    0,
                    goal - existing,
                )

                if needed == 0:
                    continue

                print()
                print(
                    "-" * 72
                )

                print(
                    f"{target}/{split}: "
                    f"existing={existing}, "
                    f"goal={goal}, "
                    f"needed={needed}"
                )

                print(
                    "-" * 72
                )

                ordered_candidates = (
                    stream.select_diverse_rows(
                        candidates,
                        len(candidates),
                    )
                )

                for row in ordered_candidates:
                    current_count = (
                        count_existing_features(
                            stream,
                            target,
                            split,
                        )
                    )

                    if current_count >= goal:
                        break

                    archive_member = (
                        stream.resolve_archive_member(
                            row,
                            exact_index,
                            basename_index,
                        )
                    )

                    if archive_member is None:
                        unresolved_count += 1

                        print(
                            "[UNRESOLVED]",
                            row.get(
                                "filename",
                                "",
                            ),
                        )

                        continue

                    output_path = (
                        stream.create_output_path(
                            row,
                            archive_member,
                        )
                    )

                    if output_path.exists():
                        continue

                    print()
                    print(
                        f"Trying {target}/{split}:"
                    )

                    print(
                        "  Participant:",
                        row.get(
                            "user",
                            "",
                        ),
                    )

                    print(
                        "  Video:",
                        row.get(
                            "filename",
                            "",
                        ),
                    )

                    print(
                        "  Remote:",
                        archive_member,
                    )

                    status = stream.process_video(
                        remote_zip,
                        row,
                        archive_member,
                    )

                    if status == "saved":
                        saved_count += 1

                        print(
                            "  [SAVED]"
                        )

                    elif status == "failed":
                        failed_count += 1

                        print(
                            "  [FAILED] Trying "
                            "another available video."
                        )

    print()
    print("=" * 88)
    print("FILL OPERATION COMPLETE")
    print("=" * 88)

    print(
        "Saved:",
        saved_count,
    )

    print(
        "Failed attempts:",
        failed_count,
    )

    print(
        "Unresolved:",
        unresolved_count,
    )

    final_missing = print_counts(
        stream,
        classes,
        available_counts,
    )

    if final_missing:
        print()
        print(
            "Some required positions are "
            "still missing."
        )

        print(
            "Run this file again, or send "
            "the final output."
        )

        raise SystemExit(1)

    print()
    print(
        "SUCCESS: The final 11-class "
        "dataset is complete."
    )


if __name__ == "__main__":
    main()