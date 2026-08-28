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
    / "best_beginner_test_validation.csv"
)


# ============================================================
# SEARCH TOPICS
# ============================================================

TOPICS = {

    "GREETING": [
        "hello",
        "hi",
        "good morning",
        "good afternoon",
        "good evening",
    ],

    "INTRODUCTION": [
        "my name is",
        "my name",
    ],

    "HOW_ARE_YOU": [
        "how are you",
        "how are you doing",
        "how do you feel",
    ],

    "FINE": [
        "i am fine",
        "i'm fine",
        "i am good",
        "i'm good",
    ],

    "THANKS": [
        "thank you",
        "thanks",
    ],

    "PLEASE": [
        "please",
    ],

    "SORRY": [
        "i'm sorry",
        "i am sorry",
        "sorry",
    ],

    "EXCUSE_ME": [
        "excuse me",
        "excuse",
    ],

    "WELCOME": [
        "welcome",
        "you're welcome",
        "you are welcome",
    ],

    "HELP": [
        "can you help",
        "help me",
        "need help",
    ],

    "NEED": [
        "i need",
    ],

    "WANT": [
        "i want",
        "i would like",
        "i'd like",
    ],

    "UNDERSTAND": [
        "i understand",
        "i don't understand",
        "do you understand",
    ],

    "REPEAT": [
        "repeat",
        "say that again",
        "again please",
    ],

    "WHERE": [
        "where is",
        "where are",
        "where can",
    ],

    "WHAT": [
        "what is",
        "what's",
    ],

    "YES_NO": [
        "yes",
        "no",
    ],

    "GOODBYE": [
        "goodbye",
        "good bye",
        "bye",
        "see you soon",
        "see you later",
        "see you",
        "take care",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value: str) -> str:
    value = str(value or "").lower()

    value = value.replace("’", "'")
    value = value.replace("‘", "'")
    value = value.replace("“", '"')
    value = value.replace("”", '"')

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_column(value: str) -> str:
    value = str(value or "").upper().strip()

    value = re.sub(
        r"[^A-Z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def phrase_exists(
    sentence: str,
    phrase: str,
) -> bool:

    sentence_words = re.findall(
        r"[a-z0-9']+",
        normalize_text(sentence),
    )

    phrase_words = re.findall(
        r"[a-z0-9']+",
        normalize_text(phrase),
    )

    if not phrase_words:
        return False

    sentence_clean = " ".join(sentence_words)
    phrase_clean = " ".join(phrase_words)

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

    return "\t"


def get_value(
    row: dict,
    name: str,
) -> str:

    target = normalize_column(name)

    for key, value in row.items():

        if normalize_column(key) == target:
            return str(value or "").strip()

    return ""


def detect_split(
    file_path: Path,
) -> str:

    text = str(file_path).lower()

    if "validation" in text:
        return "validation"

    if "test" in text:
        return "test"

    if "train" in text:
        return "train"

    return "unknown"


# ============================================================
# SCORE
# ============================================================

def score_sentence(
    sentence: str,
    phrases: list[str],
) -> tuple[int, list[str]]:

    matches = []
    score = 0

    for phrase in phrases:

        if phrase_exists(
            sentence,
            phrase,
        ):
            matches.append(phrase)

            score += (
                20
                + len(phrase.split()) * 12
            )

    if not matches:
        return 0, []

    words = re.findall(
        r"[a-z0-9']+",
        normalize_text(sentence),
    )

    word_count = len(words)

    # Strongly prefer short everyday phrases.
    if 1 <= word_count <= 3:
        score += 30

    elif 4 <= word_count <= 6:
        score += 25

    elif 7 <= word_count <= 9:
        score += 12

    elif 10 <= word_count <= 12:
        score += 4

    elif word_count > 15:
        score -= 25

    # Penalize obvious instructional/tutorial context.
    unwanted = [
        "hair",
        "paint",
        "yoga",
        "golf",
        "horse",
        "cooking",
        "recipe",
        "computer",
        "software",
        "excel",
        "tutorial",
        "segment",
        "video",
        "aquarium",
        "massage",
        "swimming",
        "vehicle",
        "tire",
    ]

    for word in unwanted:

        if phrase_exists(
            sentence,
            word,
        ):
            score -= 15

    return score, matches


# ============================================================
# FIND METADATA
# ============================================================

def find_files() -> list[Path]:

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

        if "candidate" in path.name.lower():
            continue

        if "beginner" in path.name.lower():
            continue

        split = detect_split(path)

        # IMPORTANT:
        # Skip train completely.
        if split not in {
            "validation",
            "test",
        }:
            continue

        files.append(path)

    return sorted(
        files,
        key=lambda p: str(p).lower(),
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 84)
    print(
        "SIGNBRIDGE - HOW2SIGN BEGINNER SEARCH"
    )
    print("=" * 84)

    source_files = find_files()

    print()
    print(
        f"Test/Validation files found: "
        f"{len(source_files)}"
    )

    if not source_files:

        print(
            "[ERROR] No Test or Validation metadata found."
        )
        return

    results = {
        topic: []
        for topic in TOPICS
    }

    for source_file in source_files:

        split = detect_split(
            source_file
        )

        delimiter = detect_delimiter(
            source_file
        )

        print()
        print(
            f"Reading: {source_file.name}"
        )

        print(
            f"Split  : {split}"
        )

        with source_file.open(
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

                sentence = get_value(
                    row,
                    "SENTENCE",
                )

                if not sentence:
                    continue

                for topic, phrases in TOPICS.items():

                    score, matches = score_sentence(
                        sentence,
                        phrases,
                    )

                    if score <= 0:
                        continue

                    results[topic].append(
                        {
                            "topic": topic,
                            "score": score,
                            "sentence": sentence,
                            "split": split,

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

                            "row_number":
                                row_number,
                        }
                    )

    # ========================================================
    # SORT + DEDUPLICATE
    # ========================================================

    final = {}

    for topic, items in results.items():

        items.sort(
            key=lambda x: (
                -x["score"],
                len(x["sentence"].split()),
                x["sentence"].lower(),
            )
        )

        unique = []
        seen = set()

        for item in items:

            key = (
                normalize_text(
                    item["sentence"]
                ),
                item["sentence_name"],
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

            if len(unique) >= 20:
                break

        final[topic] = unique

    # ========================================================
    # PRINT
    # ========================================================

    for topic in TOPICS:

        items = final.get(
            topic,
            [],
        )

        print()
        print("=" * 84)
        print(
            f"TOPIC: {topic}"
        )
        print("=" * 84)

        if not items:
            print(
                "No useful candidates found."
            )
            continue

        for index, item in enumerate(
            items[:10],
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

    # ========================================================
    # SAVE
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
            ],
        )

        writer.writeheader()

        for topic in TOPICS:

            for item in final.get(
                topic,
                [],
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
                    }
                )

    print()
    print("=" * 84)
    print("FINISHED")
    print("=" * 84)

    print()
    print(
        "Saved:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()