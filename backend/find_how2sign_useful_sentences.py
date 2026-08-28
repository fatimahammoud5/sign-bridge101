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
    / "signbridge_useful_sentences.csv"
)


# ============================================================
# SETTINGS
# ============================================================

MAX_RESULTS_PER_TOPIC = 60
PRINT_RESULTS_PER_TOPIC = 25


# ============================================================
# TOPICS
# ============================================================

TOPICS = {

    # --------------------------------------------------------
    # LEVEL 1 CANDIDATE
    # --------------------------------------------------------

    "INTRODUCTIONS": [
        "hello",
        "hi",
        "good morning",
        "good afternoon",
        "good evening",
        "my name is",
        "i'm",
        "i am",
        "welcome",
    ],

    # --------------------------------------------------------
    # GENERAL DAILY COMMUNICATION
    # --------------------------------------------------------

    "DAILY_COMMUNICATION": [
        "thank you",
        "thanks",
        "please",
        "sorry",
        "excuse me",
        "you're welcome",
        "you are welcome",
        "okay",
        "that's okay",
        "no problem",
        "no big deal",
        "see you",
        "goodbye",
        "bye",
        "take care",
    ],

    # --------------------------------------------------------
    # NEEDS / REQUESTS
    # --------------------------------------------------------

    "REQUESTS_AND_NEEDS": [
        "i need",
        "i want",
        "i would like",
        "i'd like",
        "can i",
        "can you",
        "could you",
        "would you",
        "help me",
        "can you help",
        "i need help",
        "give me",
        "show me",
        "tell me",
        "wait",
        "wait for me",
    ],

    # --------------------------------------------------------
    # QUESTIONS
    # --------------------------------------------------------

    "QUESTIONS": [
        "where is",
        "where are",
        "where can",
        "what is",
        "what's",
        "who is",
        "who are",
        "when is",
        "when are",
        "how do",
        "how can",
        "how much",
        "how many",
        "which one",
    ],

    # --------------------------------------------------------
    # FOOD / DRINK
    # --------------------------------------------------------

    "FOOD_AND_DRINK": [
        "i want water",
        "i need water",
        "water",
        "drink",
        "food",
        "eat",
        "hungry",
        "thirsty",
        "coffee",
        "tea",
        "breakfast",
        "lunch",
        "dinner",
        "restaurant",
        "menu",
    ],

    # --------------------------------------------------------
    # PLACES / DIRECTIONS
    # --------------------------------------------------------

    "PLACES_AND_DIRECTIONS": [
        "this way",
        "where is",
        "go there",
        "go straight",
        "turn left",
        "turn right",
        "left",
        "right",
        "here",
        "there",
        "home",
        "hospital",
        "doctor",
        "school",
        "store",
        "restaurant",
        "bathroom",
        "office",
    ],

    # --------------------------------------------------------
    # HELP / SAFETY
    # --------------------------------------------------------

    "HELP_AND_SAFETY": [
        "help",
        "help me",
        "i need help",
        "doctor",
        "hospital",
        "emergency",
        "call",
        "police",
        "fire",
        "danger",
        "careful",
        "safe",
        "stay safe",
        "hurt",
        "pain",
        "sick",
        "problem",
    ],

    # --------------------------------------------------------
    # FEELINGS / STATE
    # --------------------------------------------------------

    "FEELINGS_AND_STATE": [
        "i am happy",
        "i'm happy",
        "happy",
        "sad",
        "angry",
        "tired",
        "scared",
        "afraid",
        "worried",
        "fine",
        "i'm fine",
        "i am fine",
        "good",
        "i'm good",
        "feel",
        "feeling",
    ],

    # --------------------------------------------------------
    # UNDERSTANDING / CONVERSATION
    # --------------------------------------------------------

    "UNDERSTANDING": [
        "i understand",
        "i don't understand",
        "do you understand",
        "understand",
        "again",
        "repeat",
        "say that again",
        "slow down",
        "speak slowly",
        "show me",
    ],
}


# ============================================================
# WORDS / CONTEXT TO AVOID
# ============================================================

UNWANTED_TERMS = [

    # tutorial / instructional
    "tutorial",
    "segment",
    "next segment",
    "next video",
    "this video",
    "clip",
    "demonstrate",
    "demonstration",
    "we're going to show",
    "i'm going to show",
    "i'm going to teach",

    # technical
    "excel",
    "software",
    "computer",
    "macro",
    "database",

    # hobbies / specific tutorials
    "yoga",
    "golf",
    "baseball",
    "billiards",
    "swimming",
    "horse",
    "aquarium",
    "paint",
    "painting",
    "hair",
    "dandruff",
    "conditioner",
    "clay",
    "pottery",
    "tire",
    "vehicle",
    "knots",

    # cooking-specific
    "recipe",
    "tablespoon",
    "teaspoon",
    "cup of",
    "oven",
    "cook for",
]


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value: str) -> str:

    value = str(value or "")

    value = value.replace("’", "'")
    value = value.replace("‘", "'")
    value = value.replace("“", '"')
    value = value.replace("”", '"')

    value = value.lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_column(value: str) -> str:

    value = str(value or "").strip().upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# SAFE PHRASE SEARCH
# ============================================================

def phrase_exists(
    sentence: str,
    phrase: str,
) -> bool:

    sentence = normalize_text(sentence)
    phrase = normalize_text(phrase)

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
        + re.escape(phrase_clean)
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
# DELIMITER
# ============================================================

def detect_delimiter(
    file_path: Path,
) -> str:

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
    ) as file:

        first_line = file.readline()

    if first_line.count("\t") >= 2:
        return "\t"

    if first_line.count(",") >= 2:
        return ","

    if first_line.count(";") >= 2:
        return ";"

    return "\t"


# ============================================================
# SPLIT
# ============================================================

def detect_split(
    path: Path,
) -> str:

    text = str(path).lower()

    if "train" in text:
        return "train"

    if "validation" in text:
        return "validation"

    if (
        "\\val\\" in text
        or "/val/" in text
        or "_val" in text
    ):
        return "validation"

    if "test" in text:
        return "test"

    return "unknown"


# ============================================================
# GET VALUE
# ============================================================

def get_value(
    row: dict,
    expected: str,
) -> str:

    expected = normalize_column(
        expected
    )

    for key, value in row.items():

        if normalize_column(key) == expected:

            return str(
                value or ""
            ).strip()

    return ""


# ============================================================
# FIND INPUT FILES
# ============================================================

def find_metadata_files() -> list[Path]:

    found = []

    for path in HOW2SIGN_ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".csv",
            ".tsv",
            ".txt",
        }:
            continue

        name = path.name.lower()

        # Ignore files created by our scripts
        if "candidate" in name:
            continue

        if "beginner" in name:
            continue

        if "useful_sentences" in name:
            continue

        split = detect_split(
            path
        )

        if split not in {
            "train",
            "validation",
            "test",
        }:
            continue

        found.append(
            path
        )

    return sorted(
        found,
        key=lambda p: str(p).lower(),
    )


# ============================================================
# CHECK IF SENTENCE IS BAD
# ============================================================

def contains_unwanted_context(
    sentence: str,
) -> bool:

    for term in UNWANTED_TERMS:

        if phrase_exists(
            sentence,
            term,
        ):
            return True

    return False


# ============================================================
# SCORE
# ============================================================

def score_sentence(
    sentence: str,
    phrases: list[str],
) -> tuple[int, list[str]]:

    normalized = normalize_text(
        sentence
    )

    words = re.findall(
        r"[a-z0-9']+",
        normalized,
    )

    word_count = len(
        words
    )

    if word_count == 0:
        return 0, []

    matched = []

    score = 0

    # ========================================================
    # MATCH TOPIC
    # ========================================================

    for phrase in phrases:

        if not phrase_exists(
            normalized,
            phrase,
        ):
            continue

        matched.append(
            phrase
        )

        phrase_length = len(
            phrase.split()
        )

        score += (
            25
            + phrase_length * 12
        )

    if not matched:
        return 0, []

    # ========================================================
    # LENGTH
    # ========================================================

    if 2 <= word_count <= 5:
        score += 50

    elif 6 <= word_count <= 8:
        score += 40

    elif 9 <= word_count <= 11:
        score += 25

    elif 12 <= word_count <= 14:
        score += 10

    elif word_count >= 20:
        score -= 60

    # ========================================================
    # CONVERSATION BONUS
    # ========================================================

    conversation_words = {
        "i",
        "i'm",
        "my",
        "me",
        "you",
        "your",
        "we",
        "us",
    }

    conversation_count = sum(
        1
        for word in words
        if word in conversation_words
    )

    score += min(
        conversation_count * 5,
        20,
    )

    # ========================================================
    # QUESTION BONUS
    # ========================================================

    if normalized.endswith("?"):
        score += 15

    # ========================================================
    # STRONG BEGINNER EXPRESSIONS
    # ========================================================

    beginner_phrases = [
        "hello",
        "my name is",
        "thank you",
        "please",
        "excuse me",
        "i need",
        "i want",
        "can you",
        "where is",
        "help me",
        "sorry",
        "see you",
    ]

    for phrase in beginner_phrases:

        if phrase_exists(
            normalized,
            phrase,
        ):
            score += 15

    # ========================================================
    # UNWANTED CONTEXT
    # ========================================================

    if contains_unwanted_context(
        normalized
    ):
        score -= 80

    return score, matched


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)

    print(
        "SIGNBRIDGE - HOW2SIGN USEFUL SENTENCE FINDER"
    )

    print("=" * 90)

    source_files = (
        find_metadata_files()
    )

    print()
    print(
        f"Metadata files found: "
        f"{len(source_files)}"
    )

    if not source_files:

        print()
        print(
            "[ERROR] No How2Sign Train/Test/Validation files found."
        )

        return

    results = {
        topic: []
        for topic in TOPICS
    }

    split_counts = {}

    total_rows = 0

    # ========================================================
    # READ FILES
    # ========================================================

    for file_path in source_files:

        split = detect_split(
            file_path
        )

        delimiter = detect_delimiter(
            file_path
        )

        print()
        print("-" * 90)

        print(
            f"Reading : {file_path.name}"
        )

        print(
            f"Split   : {split}"
        )

        print(
            "Format  : "
            + (
                "TAB"
                if delimiter == "\t"
                else "CSV"
            )
        )

        rows_in_file = 0

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

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                rows_in_file += 1
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

                    score, matches = (
                        score_sentence(
                            sentence,
                            phrases,
                        )
                    )

                    # Ignore poor matches
                    if score < 25:
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

                            "split":
                                split,

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

                            "matches":
                                matches,

                            "word_count":
                                len(
                                    re.findall(
                                        r"[a-z0-9']+",
                                        normalize_text(
                                            sentence
                                        ),
                                    )
                                ),

                            "row_number":
                                row_number,
                        }
                    )

        split_counts[
            split
        ] = (
            split_counts.get(
                split,
                0,
            )
            + rows_in_file
        )

    # ========================================================
    # SORT + DEDUPLICATE
    # ========================================================

    final_results = {}

    for topic, items in results.items():

        items.sort(
            key=lambda item: (
                -item["score"],
                item["word_count"],
                item["sentence"].lower(),
            )
        )

        unique = []

        seen_sentences = set()

        for item in items:

            normalized = normalize_text(
                item["sentence"]
            )

            # avoid repeated identical English sentence
            if normalized in seen_sentences:
                continue

            seen_sentences.add(
                normalized
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
    print("=" * 90)
    print("DATASET SUMMARY")
    print("=" * 90)

    print(
        f"Total rows scanned: "
        f"{total_rows}"
    )

    for split, count in sorted(
        split_counts.items()
    ):

        print(
            f"{split:<12}: {count}"
        )

    # ========================================================
    # SHOW RESULTS
    # ========================================================

    for topic, items in final_results.items():

        print()
        print()
        print("=" * 90)

        print(
            f"TOPIC: {topic}"
        )

        print("=" * 90)

        print(
            f"Useful candidates: "
            f"{len(items)}"
        )

        if not items:
            continue

        for index, item in enumerate(
            items[
                :PRINT_RESULTS_PER_TOPIC
            ],
            start=1,
        ):

            print()
            print(
                f"[{index:02d}] "
                f"Score: {item['score']}"
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
                f"Video Name    : "
                f"{item['video_name']}"
            )

            print(
                f"Words         : "
                f"{item['word_count']}"
            )

            print(
                f"Matched       : "
                + " | ".join(
                    item["matches"]
                )
            )

            print(
                "-" * 90
            )

    # ========================================================
    # SAVE ALL RESULTS
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
                "word_count",
                "matches",
            ],
        )

        writer.writeheader()

        for topic in TOPICS:

            for item in (
                final_results.get(
                    topic,
                    []
                )
            ):

                writer.writerow(
                    {
                        "topic":
                            item["topic"],

                        "score":
                            item["score"],

                        "sentence":
                            item["sentence"],

                        "split":
                            item["split"],

                        "sentence_id":
                            item["sentence_id"],

                        "sentence_name":
                            item["sentence_name"],

                        "video_id":
                            item["video_id"],

                        "video_name":
                            item["video_name"],

                        "start":
                            item["start"],

                        "end":
                            item["end"],

                        "word_count":
                            item["word_count"],

                        "matches":
                            " | ".join(
                                item["matches"]
                            ),
                    }
                )

    print()
    print()
    print("=" * 90)

    print(
        "SEARCH FINISHED"
    )

    print("=" * 90)

    print()
    print(
        "All useful candidates saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print(
        "Use this CSV to choose the final Education lessons."
    )


if __name__ == "__main__":
    main()