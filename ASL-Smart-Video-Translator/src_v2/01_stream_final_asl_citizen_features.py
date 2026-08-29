from __future__ import annotations

import importlib.util
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_ROOT = (
    PROJECT_ROOT
    / "src_v2"
)

DATASET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "ASL_Citizen_subset"
)

BASE_STREAM_SCRIPT = (
    SRC_ROOT
    / "01_stream_asl_citizen_features.py"
)

FINAL_CLASSES_FILE = (
    PROJECT_ROOT
    / "classes_v2_proposed.txt"
)

FINAL_REPORT_PATH = (
    DATASET_ROOT
    / "final_target_word_report.csv"
)

FINAL_MANIFEST_PATH = (
    DATASET_ROOT
    / "final_streamed_features_manifest.csv"
)

FINAL_FAILURE_LOG_PATH = (
    DATASET_ROOT
    / "final_streamed_features_failures.txt"
)


# ============================================================
# LOAD EXISTING STREAM SCRIPT
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
            "Could not load base stream script."
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
            "Expected 11 final classes, "
            f"but found {len(classes)}."
        )

    return classes


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not FINAL_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Final target report was not found:\n"
            f"{FINAL_REPORT_PATH}\n\n"
            "Run 00_build_final_target_report.py first."
        )

    classes = load_final_classes()

    stream = load_stream_module()

    # Override the old report and target classes.
    stream.REPORT_PATH = (
        FINAL_REPORT_PATH
    )

    stream.AVAILABLE_TARGETS = (
        classes
    )

    stream.MANIFEST_PATH = (
        FINAL_MANIFEST_PATH
    )

    stream.FAILURE_LOG_PATH = (
        FINAL_FAILURE_LOG_PATH
    )

    # Keep the same small balanced limits.
    stream.LIMITS_PER_SPLIT = {
        "train": 14,
        "val": 3,
        "test": 3,
    }

    print("=" * 88)
    print(
        "FINAL 11-WORD ASL CITIZEN STREAM"
    )
    print("=" * 88)

    print(
        "Classes:"
    )

    for index, class_name in enumerate(
        classes
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    print()
    print(
        "Existing ASL Citizen features "
        "will be skipped."
    )

    print(
        "Only missing replacement-word "
        "videos will be downloaded."
    )

    print()

    stream.main()


if __name__ == "__main__":
    main()