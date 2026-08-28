from __future__ import annotations

import csv
import re

from pathlib import Path


# ============================================================
# PATHS
# ============================================================

# sign_bridge/backend
BACKEND_ROOT = Path(__file__).resolve().parent

# sign_bridge/backend/education_source/OpenASL
OPENASL_ROOT = (
    BACKEND_ROOT
    / "education_source"
    / "OpenASL"
)

# Main OpenASL metadata file
OPENASL_TSV = (
    OPENASL_ROOT
    / "data"
    / "openasl-v1.0.tsv"
)

# Save the best candidates here
OUTPUT_CSV = (
    OPENASL_ROOT
    / "signbridge_level1_candidates.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# How many candidates to keep for each topic
MAX_RESULTS_PER_TOPIC = 25

# How many to print in the terminal
PRINT_RESULTS_PER_TOPIC = 10


# ============================================================
# LEVEL 1 TOPICS
# ============================================================

# We do NOT require the exact old sentences.
# We search for useful complete sentences that actually exist
# inside OpenASL.

TOPICS = {
    "NAME": {
        "phrases": [
            "my name is",
            "my name",
            "your name",
            "what is your name",
            "what's your name",
            "what is the name",
        ],
        "keywords": [
            "name",
        ],
    },

    "MEETING": {
        "phrases": [
            "nice to meet you",
            "nice meeting you",
            "meet you",
            "pleased to meet you",
            "good to meet you",
        ],
        "keywords": [
            "meet",
        ],
    },

    "INTRODUCTION": {
        "phrases": [
            "introduce myself",
            "introduce yourself",
            "let me introduce",
            "i am",
            "i'm",
        ],
        "keywords": [
            "introduce",
            "hello",
        ],
    },

    "AGE": {
        "phrases": [
            "years old",
            "year old",
            "how old are you",
            "how old",
            "my age",
        ],
        "keywords": [
            "age",
            "old",
        ],
    },

    "DEAF": {
        "phrases": [
            "i am deaf",
            "i'm deaf",
            "am deaf",
            "deaf person",
        ],
        "keywords": [
            "deaf",
        ],
    },

    "LIVE": {
        "phrases": [
            "i live in",
            "i live",
            "where do you live",
            "where you live",
            "live in",
        ],
        "keywords": [
            "live",
        ],
    },

    "FROM": {
        "phrases": [
            "i am from",
            "i'm from",
            "where are you from",
            "where do you come from",
            "come from",
        ],
        "keywords": [
            "from",
        ],
    },

    "HELLO": {
        "phrases": [
            "hello",
            "hi there",
            "good morning",
            "good afternoon",
            "good evening",
        ],
        "keywords": [
            "hello",
            "hi",
        ],
    },
}


# ============================================================
# HELPERS
# ============================================================

def normalize_text(
    value: str,
) -> str:
    """
    Normalize English text for easier searching.
    """

    value = str(value or "").lower()

    value = value.replace(
        "’",
        "'",
    )

    value = value.replace(
        "“",
        '"',
    )

    value = value.replace(
        "”",
        '"',
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_column_name(
    value: str,
) -> str:
    value = str(
        value or ""
    ).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# DETECT TEXT COLUMN
# ============================================================

def detect_text_column(
    fieldnames: list[str],
) -> str | None:
    """
    OpenASL versions / derived files may use slightly different
    names. Detect the English sentence column automatically.
    """

    normalized_map = {
        normalize_column_name(name): name
        for name in fieldnames
    }

    # Most likely names first.
    exact_candidates = [
        "raw_text",
        "text",
        "sentence",
        "translation",
        "english",
        "english_text",
        "transcript",
        "caption",
        "subtitle",
    ]

    for candidate in exact_candidates:
        if candidate in normalized_map:
            return normalized_map[
                candidate
            ]

    # Partial fallback.
    partial_candidates = [
        "text",
        "sentence",
        "translation",
        "english",
        "transcript",
        "caption",
    ]

    for original_name in fieldnames:
        normalized = normalize_column_name(
            original_name
        )

        for candidate in partial_candidates:
            if candidate in normalized:
                return original_name

    return None


# ============================================================
# DETECT OPTIONAL METADATA COLUMN
# ============================================================

def find_column(
    fieldnames: list[str],
    candidates: list[str],
) -> str | None:

    normalized_map = {
        normalize_column_name(name): name
        for name in fieldnames
    }

    for candidate in candidates:
        normalized_candidate = (
            normalize_column_name(
                candidate
            )
        )

        if normalized_candidate in normalized_map:
            return normalized_map[
                normalized_candidate
            ]

    return None


# ============================================================
# SCORE SENTENCE
# ============================================================

def score_sentence(
    sentence: str,
    topic_config: dict,
) -> tuple[int, list[str]]:
    """
    Higher score = more suitable for our beginner Education level.
    """

    normalized = normalize_text(
        sentence
    )

    if not normalized:
        return 0, []

    words = normalized.split()

    word_count = len(
        words
    )

    score = 0

    matched = []

    # --------------------------------------------------------
    # Exact useful phrases
    # --------------------------------------------------------

    for phrase in topic_config[
        "phrases"
    ]:
        normalized_phrase = (
            normalize_text(
                phrase
            )
        )

        if normalized_phrase in normalized:
            score += 20

            matched.append(
                phrase
            )

    # --------------------------------------------------------
    # Useful keywords
    # --------------------------------------------------------

    for keyword in topic_config[
        "keywords"
    ]:
        normalized_keyword = (
            normalize_text(
                keyword
            )
        )

        pattern = (
            r"\b"
            + re.escape(
                normalized_keyword
            )
            + r"\b"
        )

        if re.search(
            pattern,
            normalized,
        ):
            score += 5

            if keyword not in matched:
                matched.append(
                    keyword
                )

    # No match at all -> ignore.
    if score == 0:
        return 0, []

    # --------------------------------------------------------
    # Prefer short / medium sentences
    # --------------------------------------------------------

    if 3 <= word_count <= 8:
        score += 12

    elif 9 <= word_count <= 12:
        score += 8

    elif 13 <= word_count <= 16:
        score += 3

    elif word_count > 22:
        score -= 12

    # --------------------------------------------------------
    # Beginner communication bonus
    # --------------------------------------------------------

    padded = (
        f" {normalized} "
    )

    beginner_patterns = [
        " i ",
        " i'm ",
        " my ",
        " you ",
        " your ",
        " we ",
    ]

    for pattern in beginner_patterns:
        if pattern in padded:
            score += 2

    # --------------------------------------------------------
    # Penalize sentences that look too complex
    # --------------------------------------------------------

    complex_markers = [
        "however",
        "therefore",
        "although",
        "according to",
        "government",
        "president",
        "congress",
        "international",
    ]

    for marker in complex_markers:
        if marker in normalized:
            score -= 5

    return score, matched


# ============================================================
# SAFE VALUE
# ============================================================

def get_value(
    row: dict,
    column: str | None,
) -> str:

    if not column:
        return ""

    return str(
        row.get(
            column,
            "",
        )
        or ""
    ).strip()


# ============================================================
# PRINT RESULT
# ============================================================

def print_candidate(
    number: int,
    item: dict,
):
    print(
        f"[{number:02d}] "
        f"Score: {item['score']}"
    )

    print(
        "Sentence:"
    )

    print(
        f"  {item['sentence']}"
    )

    print(
        "Matched:"
    )

    print(
        "  "
        + ", ".join(
            item["matches"]
        )
    )

    if item["split"]:
        print(
            f"Split : {item['split']}"
        )

    if item["vid"]:
        print(
            f"VID   : {item['vid']}"
        )

    if item["yid"]:
        print(
            f"YID   : {item['yid']}"
        )

    if item["start"]:
        print(
            f"Start : {item['start']}"
        )

    if item["end"]:
        print(
            f"End   : {item['end']}"
        )

    print(
        f"TSV row: {item['row_number']}"
    )

    print("-" * 72)


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 76)
    print(
        "SIGNBRIDGE - OPENASL LEVEL 1 SENTENCE FINDER"
    )
    print("=" * 76)

    print()
    print("OpenASL metadata:")
    print(OPENASL_TSV)

    print()

    print(
        "Metadata exists:",
        OPENASL_TSV.exists(),
    )

    if not OPENASL_TSV.exists():
        print()
        print(
            "[ERROR] openasl-v1.0.tsv was not found."
        )

        print()
        print("Expected path:")
        print(OPENASL_TSV)

        return

    # ========================================================
    # READ TSV
    # ========================================================

    with OPENASL_TSV.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file,
            delimiter="\t",
        )

        fieldnames = (
            reader.fieldnames
            or []
        )

        # ----------------------------------------------------
        # PRINT COLUMNS
        # ----------------------------------------------------

        print()
        print("=" * 76)
        print("OPENASL COLUMNS")
        print("=" * 76)

        for index, name in enumerate(
            fieldnames,
            start=1,
        ):
            print(
                f"{index:02d}. {name}"
            )

        print()

        # ----------------------------------------------------
        # DETECT COLUMNS
        # ----------------------------------------------------

        text_column = detect_text_column(
            fieldnames
        )

        vid_column = find_column(
            fieldnames,
            [
                "vid",
                "video_id",
                "clip_id",
            ],
        )

        yid_column = find_column(
            fieldnames,
            [
                "yid",
                "youtube_id",
                "youtube_video_id",
            ],
        )

        start_column = find_column(
            fieldnames,
            [
                "start",
                "start_time",
                "begin",
            ],
        )

        end_column = find_column(
            fieldnames,
            [
                "end",
                "end_time",
                "stop",
            ],
        )

        split_column = find_column(
            fieldnames,
            [
                "split",
                "subset",
                "partition",
            ],
        )

        # ----------------------------------------------------
        # SHOW DETECTED COLUMNS
        # ----------------------------------------------------

        print("=" * 76)
        print("DETECTED COLUMNS")
        print("=" * 76)

        print(
            "English text:",
            text_column,
        )

        print(
            "VID         :",
            vid_column,
        )

        print(
            "YouTube ID  :",
            yid_column,
        )

        print(
            "Start       :",
            start_column,
        )

        print(
            "End         :",
            end_column,
        )

        print(
            "Split       :",
            split_column,
        )

        print()

        if text_column is None:
            print(
                "[ERROR] Could not find the English "
                "sentence column automatically."
            )

            print()
            print(
                "Send me the OPENASL COLUMNS printed above."
            )

            return

        # ====================================================
        # PREPARE RESULT STORAGE
        # ====================================================

        all_results = {
            topic: []
            for topic in TOPICS
        }

        total_rows = 0
        rows_with_text = 0

        # ====================================================
        # SCAN DATASET
        # ====================================================

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            total_rows += 1

            sentence = get_value(
                row,
                text_column,
            )

            if not sentence:
                continue

            rows_with_text += 1

            for topic, config in TOPICS.items():

                (
                    score,
                    matches,
                ) = score_sentence(
                    sentence,
                    config,
                )

                if score <= 0:
                    continue

                candidate = {
                    "topic":
                        topic,

                    "score":
                        score,

                    "sentence":
                        sentence,

                    "matches":
                        matches,

                    "row_number":
                        row_number,

                    "vid":
                        get_value(
                            row,
                            vid_column,
                        ),

                    "yid":
                        get_value(
                            row,
                            yid_column,
                        ),

                    "start":
                        get_value(
                            row,
                            start_column,
                        ),

                    "end":
                        get_value(
                            row,
                            end_column,
                        ),

                    "split":
                        get_value(
                            row,
                            split_column,
                        ),
                }

                all_results[
                    topic
                ].append(
                    candidate
                )

    # ========================================================
    # SORT + REMOVE DUPLICATES
    # ========================================================

    final_results = {}

    for topic, candidates in all_results.items():

        candidates.sort(
            key=lambda item: (
                -item["score"],
                len(
                    item["sentence"].split()
                ),
                item["sentence"].lower(),
            )
        )

        unique = []

        seen_sentences = set()

        for candidate in candidates:

            normalized_sentence = (
                normalize_text(
                    candidate[
                        "sentence"
                    ]
                )
            )

            if normalized_sentence in seen_sentences:
                continue

            seen_sentences.add(
                normalized_sentence
            )

            unique.append(
                candidate
            )

            if (
                len(unique)
                >= MAX_RESULTS_PER_TOPIC
            ):
                break

        final_results[
            topic
        ] = unique

    # ========================================================
    # DATASET SUMMARY
    # ========================================================

    print()
    print("=" * 76)
    print("DATASET SUMMARY")
    print("=" * 76)

    print(
        f"Total TSV rows     : {total_rows}"
    )

    print(
        f"Rows with English  : {rows_with_text}"
    )

    print()

    # ========================================================
    # PRINT BEST RESULTS
    # ========================================================

    for topic in TOPICS:

        results = final_results.get(
            topic,
            [],
        )

        print()
        print("=" * 76)
        print(
            f"TOPIC: {topic}"
        )
        print("=" * 76)

        print(
            f"Candidates found: {len(results)}"
        )

        print()

        if not results:
            print(
                "No candidates found."
            )

            continue

        for index, candidate in enumerate(
            results[
                :PRINT_RESULTS_PER_TOPIC
            ],
            start=1,
        ):
            print_candidate(
                index,
                candidate,
            )

    # ========================================================
    # SAVE RESULTS TO CSV
    # ========================================================

    output_rows = []

    for topic in TOPICS:
        output_rows.extend(
            final_results.get(
                topic,
                [],
            )
        )

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "topic",
                "score",
                "sentence",
                "matches",
                "split",
                "vid",
                "yid",
                "start",
                "end",
                "row_number",
            ],
        )

        writer.writeheader()

        for item in output_rows:
            writer.writerow(
                {
                    "topic":
                        item[
                            "topic"
                        ],

                    "score":
                        item[
                            "score"
                        ],

                    "sentence":
                        item[
                            "sentence"
                        ],

                    "matches":
                        " | ".join(
                            item[
                                "matches"
                            ]
                        ),

                    "split":
                        item[
                            "split"
                        ],

                    "vid":
                        item[
                            "vid"
                        ],

                    "yid":
                        item[
                            "yid"
                        ],

                    "start":
                        item[
                            "start"
                        ],

                    "end":
                        item[
                            "end"
                        ],

                    "row_number":
                        item[
                            "row_number"
                        ],
                }
            )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 76)
    print("SEARCH FINISHED")
    print("=" * 76)

    print()
    print(
        "Candidates file:"
    )

    print(
        OUTPUT_CSV
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "No videos were downloaded."
    )

    print(
        "We only searched the OpenASL metadata."
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()