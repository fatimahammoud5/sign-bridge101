from __future__ import annotations

import csv
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parent

HOW2SIGN_ROOT = (
    BACKEND_ROOT
    / "education_source"
    / "How2Sign"
)

OUTPUT_FILE = (
    HOW2SIGN_ROOT
    / "signbridge_level1_all_candidates.csv"
)


# ============================================================
# SETTINGS
# ============================================================

MAX_RESULTS_PER_TOPIC = 50
PRINT_RESULTS_PER_TOPIC = 20


# ============================================================
# LEVEL 1 TOPICS
# ============================================================

TOPICS = {

    "HELLO": [
        "hello",
        "hi",
        "good morning",
        "good afternoon",
        "good evening",
    ],

    "NAME": [
        "my name is",
        "my name",
        "what is your name",
        "what's your name",
        "your name",
        "name is",
    ],

    "MEETING": [
        "nice to meet you",
        "nice meeting you",
        "good to meet you",
        "pleased to meet you",
        "meet you",
    ],

    "DEAF": [
        "i am deaf",
        "i'm deaf",
        "deaf",
        "hard of hearing",
    ],

    "FROM": [
        "where are you from",
        "where do you come from",
        "i am from",
        "i'm from",
        "come from",
    ],

    "LIVE": [
        "where do you live",
        "where you live",
        "i live in",
        "i live",
        "live in",
    ],

    "AGE": [
        "how old are you",
        "how old",
        "years old",
        "year old",
    ],

    "THANK": [
        "thank you",
        "thanks",
        "thank",
    ],

    "PLEASE": [
        "please",
    ],

    "HELP": [
        "can you help me",
        "can you help",
        "help me",
        "i need help",
        "need help",
    ],

    "NEED": [
        "i need",
        "do you need",
        "need",
    ],

    "GOODBYE": [
        "goodbye",
        "good bye",
        "bye",
        "see you later",
        "see you",
    ],
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value: str) -> str:

    value = str(
        value or ""
    )

    value = value.replace(
        "’",
        "'",
    )

    value = value.replace(
        "‘",
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

    value = value.lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_column(value: str) -> str:

    value = str(
        value or ""
    ).strip().upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# SAFE PHRASE MATCHING
# ============================================================

def phrase_exists(
    sentence: str,
    phrase: str,
) -> bool:

    sentence = normalize_text(
        sentence
    )

    phrase = normalize_text(
        phrase
    )

    sentence_words = re.findall(
        r"[a-z0-9']+",
        sentence,
    )

    phrase_words = re.findall(
        r"[a-z0-9']+",
        phrase,
    )

    if not phrase_words:
        return False

    sentence_clean = " ".join(
        sentence_words
    )

    phrase_clean = " ".join(
        phrase_words
    )

    pattern = (
        r"(?<![a-z0-9'])"
        + re.escape(
            phrase_clean
        )
        + r"(?![a-z0-9'])"
    )

    return (
        re.search(
            pattern,
            sentence_clean,
        )
        is not None
    )


# ============================================================
# FIND SOURCE FILES
# ============================================================

def find_source_files() -> list[Path]:

    if not HOW2SIGN_ROOT.exists():
        return []

    files = []

    for path in HOW2SIGN_ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".csv",
            ".tsv",
            ".txt",
        }:
            continue

        # Ignore our own generated results
        if (
            "candidate"
            in path.name.lower()
        ):
            continue

        files.append(
            path
        )

    files.sort(
        key=lambda p: str(
            p
        ).lower()
    )

    return files


# ============================================================
# DETECT DELIMITER
# ============================================================

def detect_delimiter(
    file_path: Path,
) -> str:

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
    ) as file:

        first_line = (
            file.readline()
        )

    tab_count = (
        first_line.count("\t")
    )

    comma_count = (
        first_line.count(",")
    )

    semicolon_count = (
        first_line.count(";")
    )

    if tab_count >= 2:
        return "\t"

    if comma_count >= 2:
        return ","

    if semicolon_count >= 2:
        return ";"

    return "\t"


# ============================================================
# READ FILE
# ============================================================

def read_file(
    file_path: Path,
):

    delimiter = detect_delimiter(
        file_path
    )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file,
            delimiter=delimiter,
        )

        fieldnames = (
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    return (
        delimiter,
        fieldnames,
        rows,
    )


# ============================================================
# GET COLUMN
# ============================================================

def get_value(
    row: dict,
    expected_name: str,
) -> str:

    expected = normalize_column(
        expected_name
    )

    for key, value in (
        row.items()
    ):

        if normalize_column(
            key
        ) == expected:

            return str(
                value or ""
            ).strip()

    return ""


# ============================================================
# SCORE
# ============================================================

def score_sentence(
    sentence: str,
    phrases: list[str],
):

    normalized = normalize_text(
        sentence
    )

    if not normalized:
        return 0, []

    matched = []
    score = 0

    for phrase in phrases:

        if not phrase_exists(
            normalized,
            phrase,
        ):
            continue

        matched.append(
            phrase
        )

        phrase_word_count = len(
            phrase.split()
        )

        score += (
            20
            + phrase_word_count * 12
        )

    if not matched:
        return 0, []

    words = re.findall(
        r"[a-z0-9']+",
        normalized,
    )

    word_count = len(
        words
    )

    # --------------------------------------------------------
    # Prefer simple lessons
    # --------------------------------------------------------

    if 1 <= word_count <= 3:
        score += 20

    elif 4 <= word_count <= 6:
        score += 25

    elif 7 <= word_count <= 10:
        score += 15

    elif 11 <= word_count <= 15:
        score += 5

    elif word_count > 20:
        score -= 20

    # --------------------------------------------------------
    # Beginner conversation bonus
    # --------------------------------------------------------

    useful_words = {
        "i",
        "i'm",
        "my",
        "me",
        "you",
        "your",
    }

    for word in words:

        if word in useful_words:
            score += 2

    # --------------------------------------------------------
    # Penalize tutorial-specific text
    # --------------------------------------------------------

    unwanted_terms = [
        "tutorial",
        "excel",
        "software",
        "aquarium",
        "paint",
        "conditioner",
        "diagnose",
        "president",
        "congress",
        "government",
        "recipe",
        "hair",
    ]

    for term in unwanted_terms:

        if phrase_exists(
            normalized,
            term,
        ):
            score -= 10

    return (
        score,
        matched,
    )


# ============================================================
# DETECT SPLIT
# ============================================================

def detect_split(
    file_path: Path,
) -> str:

    path_text = str(
        file_path
    ).lower()

    if "validation" in path_text:
        return "validation"

    if (
        "\\val\\" in path_text
        or "/val/" in path_text
    ):
        return "validation"

    if "train" in path_text:
        return "train"

    if "test" in path_text:
        return "test"

    return "unknown"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 84)

    print(
        "SIGNBRIDGE - HOW2SIGN LEVEL 1 "
        "SENTENCE FINDER V3"
    )

    print("=" * 84)

    print()
    print(
        "How2Sign root:"
    )

    print(
        HOW2SIGN_ROOT
    )

    source_files = (
        find_source_files()
    )

    print()
    print(
        f"Metadata files found: "
        f"{len(source_files)}"
    )

    if not source_files:

        print()
        print(
            "[ERROR] No metadata files found."
        )

        return

    # ========================================================
    # RESULTS
    # ========================================================

    results = {
        topic: []
        for topic in TOPICS
    }

    total_rows = 0

    split_counts = {}

    # ========================================================
    # PROCESS EACH FILE
    # ========================================================

    for source_file in source_files:

        split = detect_split(
            source_file
        )

        (
            delimiter,
            fieldnames,
            rows,
        ) = read_file(
            source_file
        )

        delimiter_name = (
            "TAB"
            if delimiter == "\t"
            else "COMMA"
            if delimiter == ","
            else "SEMICOLON"
        )

        print()
        print("=" * 84)

        print(
            f"READING: "
            f"{source_file.name}"
        )

        print(
            f"Split: {split}"
        )

        print(
            f"Delimiter: "
            f"{delimiter_name}"
        )

        print(
            f"Rows: "
            f"{len(rows)}"
        )

        print(
            "Columns:"
        )

        for index, column in enumerate(
            fieldnames,
            start=1,
        ):

            print(
                f"  {index:02d}. "
                f"{column}"
            )

        normalized_columns = {
            normalize_column(
                column
            )
            for column in fieldnames
        }

        required_columns = {
            "VIDEO_ID",
            "VIDEO_NAME",
            "SENTENCE_ID",
            "SENTENCE_NAME",
            "START",
            "END",
            "SENTENCE",
        }

        missing = (
            required_columns
            - normalized_columns
        )

        if missing:

            print()
            print(
                "[SKIPPED] Missing required columns:"
            )

            for item in sorted(
                missing
            ):
                print(
                    f"  - {item}"
                )

            continue

        split_counts[
            split
        ] = (
            split_counts.get(
                split,
                0,
            )
            + len(rows)
        )

        # ====================================================
        # SEARCH ROWS
        # ====================================================

        for row_number, row in enumerate(
            rows,
            start=2,
        ):

            total_rows += 1

            sentence = get_value(
                row,
                "SENTENCE",
            )

            if not sentence:
                continue

            for topic, phrases in (
                TOPICS.items()
            ):

                (
                    score,
                    matches,
                ) = score_sentence(
                    sentence,
                    phrases,
                )

                if score <= 0:
                    continue

                results[
                    topic
                ].append(
                    {
                        "topic":
                            topic,

                        "score":
                            score,

                        "sentence":
                            sentence,

                        "sentence_id":
                            get_value(
                                row,
                                "SENTENCE_ID",
                            ),

                        "sentence_name":
                            get_value(
                                row,
                                "SENTENCE_NAME",
                            ),

                        "video_id":
                            get_value(
                                row,
                                "VIDEO_ID",
                            ),

                        "video_name":
                            get_value(
                                row,
                                "VIDEO_NAME",
                            ),

                        "start":
                            get_value(
                                row,
                                "START",
                            ),

                        "end":
                            get_value(
                                row,
                                "END",
                            ),

                        "split":
                            split,

                        "source_file":
                            source_file.name,

                        "row_number":
                            row_number,

                        "matches":
                            matches,
                    }
                )

    # ========================================================
    # SORT / DEDUPLICATE
    # ========================================================

    final_results = {}

    for topic, candidates in (
        results.items()
    ):

        candidates.sort(
            key=lambda item: (
                -item["score"],
                len(
                    item[
                        "sentence"
                    ].split()
                ),
                item[
                    "sentence"
                ].lower(),
            )
        )

        unique = []

        seen = set()

        for item in candidates:

            key = (
                normalize_text(
                    item[
                        "sentence"
                    ]
                ),
                item[
                    "sentence_name"
                ],
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                item
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
    # SUMMARY
    # ========================================================

    print()
    print("=" * 84)

    print(
        "DATASET SUMMARY"
    )

    print("=" * 84)

    print(
        f"Total rows scanned: "
        f"{total_rows}"
    )

    for split, count in sorted(
        split_counts.items()
    ):

        print(
            f"{split:<12}: "
            f"{count}"
        )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    for topic in TOPICS:

        candidates = (
            final_results.get(
                topic,
                [],
            )
        )

        print()
        print("=" * 84)

        print(
            f"TOPIC: {topic}"
        )

        print("=" * 84)

        print(
            f"Candidates found: "
            f"{len(candidates)}"
        )

        print()

        if not candidates:

            print(
                "No candidates found."
            )

            continue

        for index, item in enumerate(
            candidates[
                :PRINT_RESULTS_PER_TOPIC
            ],
            start=1,
        ):

            print(
                f"[{index:02d}] "
                f"Score: "
                f"{item['score']}"
            )

            print(
                f"Sentence      : "
                f"{item['sentence']}"
            )

            print(
                f"Split         : "
                f"{item['split']}"
            )

            print(
                f"Sentence ID   : "
                f"{item['sentence_id']}"
            )

            print(
                f"Sentence Name : "
                f"{item['sentence_name']}"
            )

            print(
                f"Video ID      : "
                f"{item['video_id']}"
            )

            print(
                f"Video Name    : "
                f"{item['video_name']}"
            )

            print(
                f"Start         : "
                f"{item['start']}"
            )

            print(
                f"End           : "
                f"{item['end']}"
            )

            print(
                "Matched       : "
                + ", ".join(
                    item[
                        "matches"
                    ]
                )
            )

            print(
                "-" * 84
            )

    # ========================================================
    # SAVE CSV
    # ========================================================

    with OUTPUT_FILE.open(
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
                "split",
                "sentence_id",
                "sentence_name",
                "video_id",
                "video_name",
                "start",
                "end",
                "matches",
                "source_file",
                "row_number",
            ],
        )

        writer.writeheader()

        for topic in TOPICS:

            for item in (
                final_results.get(
                    topic,
                    [],
                )
            ):

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

                        "split":
                            item[
                                "split"
                            ],

                        "sentence_id":
                            item[
                                "sentence_id"
                            ],

                        "sentence_name":
                            item[
                                "sentence_name"
                            ],

                        "video_id":
                            item[
                                "video_id"
                            ],

                        "video_name":
                            item[
                                "video_name"
                            ],

                        "start":
                            item[
                                "start"
                            ],

                        "end":
                            item[
                                "end"
                            ],

                        "matches":
                            " | ".join(
                                item[
                                    "matches"
                                ]
                            ),

                        "source_file":
                            item[
                                "source_file"
                            ],

                        "row_number":
                            item[
                                "row_number"
                            ],
                    }
                )

    print()
    print("=" * 84)

    print(
        "SEARCH FINISHED"
    )

    print("=" * 84)

    print()
    print(
        "Candidates file:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "No videos were downloaded."
    )


if __name__ == "__main__":
    main()