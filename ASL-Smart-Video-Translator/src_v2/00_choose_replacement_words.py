from __future__ import annotations

import csv
import json
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

OUTPUT_REPORT = (
    DATASET_ROOT
    / "replacement_candidates.csv"
)

OUTPUT_SELECTION = (
    DATASET_ROOT
    / "selected_replacements.json"
)

PROPOSED_CLASSES_FILE = (
    PROJECT_ROOT
    / "classes_v2_proposed.txt"
)


# ============================================================
# CURRENT PROJECT CLASSES
# ============================================================

# These six classes have good ASL Citizen data.
KEEP_CLASSES = [
    "computer",
    "yes",
    "no",
    "help",
    "need",
    "who",
]


# now had only:
# train=6, val=0, test=0
#
# True:
#   replace now and choose 5 new words.
#
# False:
#   keep now and choose only 4 new words.

REPLACE_NOW = True


# Classes that we do not want to select again.
EXCLUDED_CLASSES = {
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
}


# ============================================================
# MINIMUM REQUIRED DATA
# ============================================================

MIN_TRAIN = 12
MIN_VAL = 3
MIN_TEST = 3

MAX_CODES_PER_WORD = 1


# ============================================================
# PREFERRED DAILY WORDS
# ============================================================

# The script checks these words in this order.
# It selects only words that exist with enough train/val/test
# samples and a single ASL-LEX code.

PREFERRED_WORDS = [
    "hello",
    "please",
    "where",
    "why",
    "stop",
    "good",
    "bad",
    "how",
    "when",
    "again",
    "finish",
    "more",
    "home",
    "school",
    "work",
    "family",
    "friend",
    "love",
    "happy",
    "sad",
    "sorry",
    "name",
    "understand",
    "go",
    "come",
    "water",
    "bathroom",
    "morning",
    "night",
    "today",
    "tomorrow",
    "yesterday",
    "mother",
    "father",
    "baby",
    "book",
    "car",
    "phone",
    "doctor",
    "teacher",
]


# ============================================================
# COLUMN NAMES
# ============================================================

GLOSS_COLUMN_CANDIDATES = [
    "Gloss",
    "gloss",
    "Label",
    "label",
    "Word",
    "word",
]

VIDEO_COLUMN_CANDIDATES = [
    "Video file",
    "video_file",
    "Video",
    "video",
    "Filename",
    "filename",
]

PARTICIPANT_COLUMN_CANDIDATES = [
    "Participant ID",
    "participant_id",
    "Participant",
    "participant",
    "User",
    "user",
]

CODE_COLUMN_CANDIDATES = [
    "ASL-LEX Code",
    "asl_lex_code",
    "ASLLEX Code",
    "code",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value: object) -> str:
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


def class_name_from_gloss(
    gloss: str,
) -> str:
    """
    Convert a dataset gloss into a safe class-folder name.
    """

    normalized = normalize_text(gloss)

    return normalized.replace(
        " ",
        "_",
    )


def normalized_column(
    value: str,
) -> str:
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
        normalized_column(name): name
        for name in fieldnames
    }

    for candidate in candidates:
        key = normalized_column(
            candidate
        )

        if key in normalized_fields:
            return normalized_fields[key]

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
# FIND METADATA FILES
# ============================================================

def find_metadata_files() -> list[Path]:
    if not METADATA_ROOT.exists():
        raise FileNotFoundError(
            "Metadata folder was not found:\n"
            f"{METADATA_ROOT}"
        )

    files = []

    for path in METADATA_ROOT.rglob(
        "*.csv"
    ):
        if detect_split(path):
            files.append(path)

    files.sort(
        key=lambda path: str(path)
    )

    if not files:
        raise FileNotFoundError(
            "No train.csv, val.csv or test.csv "
            "files were found under:\n"
            f"{METADATA_ROOT}"
        )

    return files


# ============================================================
# READ METADATA
# ============================================================

def load_dataset_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

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
        split = detect_split(path)

        if split is None:
            continue

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

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
                GLOSS_COLUMN_CANDIDATES,
            )

            video_column = find_column(
                fieldnames,
                VIDEO_COLUMN_CANDIDATES,
            )

            participant_column = find_column(
                fieldnames,
                PARTICIPANT_COLUMN_CANDIDATES,
            )

            code_column = find_column(
                fieldnames,
                CODE_COLUMN_CANDIDATES,
            )

            if gloss_column is None:
                print(
                    "[SKIP] No gloss column:",
                    path,
                )
                continue

            print()
            print(
                f"Reading {split}: {path.name}"
            )

            print(
                "  Gloss column:",
                gloss_column,
            )

            print(
                "  Video column:",
                video_column,
            )

            print(
                "  Participant column:",
                participant_column,
            )

            print(
                "  Code column:",
                code_column,
            )

            for source_row in reader:
                gloss_original = str(
                    source_row.get(
                        gloss_column,
                        "",
                    )
                    or ""
                ).strip()

                gloss_normalized = (
                    normalize_text(
                        gloss_original
                    )
                )

                if not gloss_normalized:
                    continue

                rows.append(
                    {
                        "split":
                            split,

                        "gloss":
                            gloss_original,

                        "normalized_gloss":
                            gloss_normalized,

                        "class_name":
                            class_name_from_gloss(
                                gloss_original
                            ),

                        "video":
                            (
                                str(
                                    source_row.get(
                                        video_column,
                                        "",
                                    )
                                    or ""
                                ).strip()
                                if video_column
                                else ""
                            ),

                        "participant":
                            (
                                str(
                                    source_row.get(
                                        participant_column,
                                        "",
                                    )
                                    or ""
                                ).strip()
                                if participant_column
                                else ""
                            ),

                        "code":
                            (
                                str(
                                    source_row.get(
                                        code_column,
                                        "",
                                    )
                                    or ""
                                ).strip()
                                if code_column
                                else ""
                            ),
                    }
                )

    if not rows:
        raise ValueError(
            "No metadata rows were loaded."
        )

    return rows


# ============================================================
# BUILD WORD STATISTICS
# ============================================================

def build_statistics(
    rows: list[dict[str, str]],
) -> dict[str, dict]:
    statistics: dict[
        str,
        dict
    ] = {}

    for row in rows:
        word = row[
            "normalized_gloss"
        ]

        if word not in statistics:
            statistics[word] = {
                "normalized_gloss":
                    word,

                "class_name":
                    row["class_name"],

                "original_glosses":
                    set(),

                "codes":
                    set(),

                "participants":
                    set(),

                "videos":
                    set(),

                "counts": {
                    "train": 0,
                    "val": 0,
                    "test": 0,
                },

                "participants_by_split": {
                    "train": set(),
                    "val": set(),
                    "test": set(),
                },
            }

        item = statistics[word]

        item[
            "original_glosses"
        ].add(
            row["gloss"]
        )

        if row["code"]:
            item["codes"].add(
                row["code"]
            )

        if row["participant"]:
            item[
                "participants"
            ].add(
                row["participant"]
            )

            item[
                "participants_by_split"
            ][
                row["split"]
            ].add(
                row["participant"]
            )

        if row["video"]:
            video_key = (
                row["split"],
                row["video"],
            )

            # Do not count duplicate metadata rows twice.
            if video_key in item[
                "videos"
            ]:
                continue

            item[
                "videos"
            ].add(
                video_key
            )

        item[
            "counts"
        ][
            row["split"]
        ] += 1

    return statistics


# ============================================================
# VALID CANDIDATE CHECK
# ============================================================

def is_valid_candidate(
    item: dict,
) -> bool:
    class_name = item[
        "class_name"
    ]

    if class_name in EXCLUDED_CLASSES:
        return False

    counts = item[
        "counts"
    ]

    if counts["train"] < MIN_TRAIN:
        return False

    if counts["val"] < MIN_VAL:
        return False

    if counts["test"] < MIN_TEST:
        return False

    code_count = len(
        item["codes"]
    )

    if (
        code_count == 0
        or code_count > MAX_CODES_PER_WORD
    ):
        return False

    return True


# ============================================================
# SAVE FULL REPORT
# ============================================================

def save_candidates_report(
    candidates: list[dict],
) -> None:
    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "rank",
        "class_name",
        "gloss",
        "train",
        "val",
        "test",
        "total",
        "participants",
        "asl_lex_codes",
        "preferred",
    ]

    preferred_set = {
        normalize_text(word)
        for word in PREFERRED_WORDS
    }

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

        for rank, item in enumerate(
            candidates,
            start=1,
        ):
            counts = item["counts"]

            writer.writerow(
                {
                    "rank":
                        rank,

                    "class_name":
                        item["class_name"],

                    "gloss":
                        " | ".join(
                            sorted(
                                item[
                                    "original_glosses"
                                ]
                            )
                        ),

                    "train":
                        counts["train"],

                    "val":
                        counts["val"],

                    "test":
                        counts["test"],

                    "total":
                        (
                            counts["train"]
                            + counts["val"]
                            + counts["test"]
                        ),

                    "participants":
                        len(
                            item[
                                "participants"
                            ]
                        ),

                    "asl_lex_codes":
                        " | ".join(
                            sorted(
                                item["codes"]
                            )
                        ),

                    "preferred":
                        (
                            item[
                                "normalized_gloss"
                            ]
                            in preferred_set
                        ),
                }
            )


# ============================================================
# SELECT REPLACEMENTS
# ============================================================

def select_replacements(
    valid_candidates: list[dict],
    count: int,
) -> list[dict]:
    candidate_map = {
        item["normalized_gloss"]:
            item
        for item in valid_candidates
    }

    selected: list[dict] = []

    # First choose useful daily words in our preferred order.
    for preferred_word in PREFERRED_WORDS:
        normalized = normalize_text(
            preferred_word
        )

        item = candidate_map.get(
            normalized
        )

        if item is None:
            continue

        if item in selected:
            continue

        selected.append(item)

        if len(selected) >= count:
            break

    return selected


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 86)
    print(
        "ASL CITIZEN "
        "- CHOOSE REPLACEMENT WORDS"
    )
    print("=" * 86)

    print(
        f"Minimum counts: "
        f"train={MIN_TRAIN}, "
        f"val={MIN_VAL}, "
        f"test={MIN_TEST}"
    )

    print(
        "Maximum ASL-LEX codes:",
        MAX_CODES_PER_WORD,
    )

    rows = load_dataset_rows()

    print()
    print(
        "Metadata rows loaded:",
        len(rows),
    )

    statistics = build_statistics(
        rows
    )

    valid_candidates = [
        item
        for item in statistics.values()
        if is_valid_candidate(item)
    ]

    preferred_rank = {
        normalize_text(word): index
        for index, word in enumerate(
            PREFERRED_WORDS
        )
    }

    valid_candidates.sort(
        key=lambda item: (
            preferred_rank.get(
                item[
                    "normalized_gloss"
                ],
                1_000_000,
            ),
            -item["counts"]["train"],
            -item["counts"]["val"],
            -item["counts"]["test"],
            item["class_name"],
        )
    )

    save_candidates_report(
        valid_candidates
    )

    replacement_count = (
        5
        if REPLACE_NOW
        else 4
    )

    selected = select_replacements(
        valid_candidates,
        replacement_count,
    )

    print()
    print("=" * 86)
    print("PREFERRED AVAILABLE WORDS")
    print("=" * 86)

    shown = 0

    for item in valid_candidates:
        if (
            item["normalized_gloss"]
            not in preferred_rank
        ):
            continue

        counts = item["counts"]

        print(
            f"{item['class_name']:18s} "
            f"train={counts['train']:2d} "
            f"val={counts['val']:2d} "
            f"test={counts['test']:2d} "
            f"users={len(item['participants']):2d} "
            f"code={next(iter(item['codes']))}"
        )

        shown += 1

        if shown >= 25:
            break

    print("=" * 86)

    if len(selected) < replacement_count:
        print()
        print(
            "Not enough preferred words "
            "met the requirements."
        )

        print(
            f"Required: {replacement_count}"
        )

        print(
            f"Found:    {len(selected)}"
        )

        print()
        print(
            "Review the full candidate report:"
        )

        print(
            OUTPUT_REPORT
        )

        raise SystemExit(1)

    selected_classes = [
        item["class_name"]
        for item in selected
    ]

    if REPLACE_NOW:
        final_classes = [
            *KEEP_CLASSES,
            *selected_classes,
        ]
    else:
        final_classes = [
            *KEEP_CLASSES,
            "now",
            *selected_classes,
        ]

    selection_data = {
        "replace_now":
            REPLACE_NOW,

        "minimum_counts": {
            "train": MIN_TRAIN,
            "val": MIN_VAL,
            "test": MIN_TEST,
        },

        "kept_classes":
            (
                KEEP_CLASSES
                if REPLACE_NOW
                else [
                    *KEEP_CLASSES,
                    "now",
                ]
            ),

        "removed_classes":
            (
                [
                    "want",
                    "drink",
                    "eat",
                    "what",
                    "now",
                ]
                if REPLACE_NOW
                else [
                    "want",
                    "drink",
                    "eat",
                    "what",
                ]
            ),

        "selected_replacements": [
            {
                "class_name":
                    item["class_name"],

                "normalized_gloss":
                    item[
                        "normalized_gloss"
                    ],

                "glosses":
                    sorted(
                        item[
                            "original_glosses"
                        ]
                    ),

                "asl_lex_codes":
                    sorted(
                        item["codes"]
                    ),

                "train":
                    item["counts"]["train"],

                "val":
                    item["counts"]["val"],

                "test":
                    item["counts"]["test"],

                "participants":
                    len(
                        item[
                            "participants"
                        ]
                    ),
            }
            for item in selected
        ],

        "final_classes":
            final_classes,
    }

    OUTPUT_SELECTION.write_text(
        json.dumps(
            selection_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    PROPOSED_CLASSES_FILE.write_text(
        "\n".join(
            final_classes
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 86)
    print("SELECTED REPLACEMENTS")
    print("=" * 86)

    for index, item in enumerate(
        selected,
        start=1,
    ):
        counts = item["counts"]

        print(
            f"{index}. "
            f"{item['class_name']:16s} "
            f"train={counts['train']:2d} "
            f"val={counts['val']:2d} "
            f"test={counts['test']:2d} "
            f"users={len(item['participants']):2d}"
        )

        print(
            "   Gloss:",
            ", ".join(
                sorted(
                    item[
                        "original_glosses"
                    ]
                )
            ),
        )

        print(
            "   Code:",
            ", ".join(
                sorted(
                    item["codes"]
                )
            ),
        )

    print()
    print("PROPOSED FINAL 11 CLASSES:")
    print("-" * 40)

    for index, class_name in enumerate(
        final_classes
    ):
        print(
            f"{index:02d} -> "
            f"{class_name}"
        )

    print("-" * 40)

    print(
        "Candidate report:"
    )

    print(
        OUTPUT_REPORT
    )

    print()
    print(
        "Selection JSON:"
    )

    print(
        OUTPUT_SELECTION
    )

    print()
    print(
        "Proposed classes file:"
    )

    print(
        PROPOSED_CLASSES_FILE
    )

    print()
    print(
        "The current classes_v2.txt "
        "was NOT modified."
    )

    print("=" * 86)


if __name__ == "__main__":
    main()