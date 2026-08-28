from __future__ import annotations

import json
import sqlite3

from pathlib import Path


# ============================================================
# PATHS
# ============================================================

# sign_bridge/backend
BACKEND_ROOT = (
    Path(__file__).resolve().parent
)

EDUCATION_DIR = (
    BACKEND_ROOT
    / "education_data"
)

EDUCATION_DB_PATH = (
    EDUCATION_DIR
    / "education.db"
)

EDUCATION_IMAGES_DIR = (
    EDUCATION_DIR
    / "images"
)

EDUCATION_VIDEOS_DIR = (
    EDUCATION_DIR
    / "videos"
)


# ============================================================
# LEVELS
# ============================================================

LEVELS = [
    {
        "id": 1,

        "title":
            "Introduce Yourself",

        "subtitle":
            "Start communicating about who you are.",

        "description":
            "Learn useful complete sentences for "
            "introducing yourself and meeting people.",

        "primary_color":
            "#2196F3",

        "secondary_color":
            "#81D4FA",

        "hero_image_filename":
            "level_1_intro_hero.png",

        "locked_by_default":
            0,

        "sort_order":
            1,
    },

    {
        "id": 2,

        "title":
            "Family & Home",

        "subtitle":
            "Talk about the people and places close to you.",

        "description":
            "Learn complete sentences about family, "
            "relationships and home life.",

        "primary_color":
            "#7E57C2",

        "secondary_color":
            "#D1C4E9",

        "hero_image_filename":
            "level_2_family_hero.png",

        "locked_by_default":
            1,

        "sort_order":
            2,
    },

    {
        "id": 3,

        "title":
            "Daily Life & Needs",

        "subtitle":
            "Communicate what you need every day.",

        "description":
            "Practice useful sentences for food, "
            "activities, requests and daily routines.",

        "primary_color":
            "#FF8A65",

        "secondary_color":
            "#FFCCBC",

        "hero_image_filename":
            "level_3_daily_hero.png",

        "locked_by_default":
            1,

        "sort_order":
            3,
    },

    {
        "id": 4,

        "title":
            "Social & Outside",

        "subtitle":
            "Communicate confidently outside your home.",

        "description":
            "Learn sentences for meeting people, "
            "places, directions and social situations.",

        "primary_color":
            "#00ACC1",

        "secondary_color":
            "#80DEEA",

        "hero_image_filename":
            "level_4_social_hero.png",

        "locked_by_default":
            1,

        "sort_order":
            4,
    },

    {
        "id": 5,

        "title":
            "Health & Safety",

        "subtitle":
            "Communicate clearly when it matters most.",

        "description":
            "Learn important sentences for health, "
            "emergencies and personal safety.",

        "primary_color":
            "#EF5350",

        "secondary_color":
            "#FFAB91",

        "hero_image_filename":
            "level_5_health_hero.png",

        "locked_by_default":
            1,

        "sort_order":
            5,
    },
]


# ============================================================
# LEVEL 1 SENTENCES
# ============================================================

SENTENCES = [
    {
        "level_id":
            1,

        "english_text":
            "My name is Lina.",

        "asl_gloss":
            "",

        "meaning":
            "Use this sentence to tell someone your name.",

        "scenario":
            "You are meeting someone for the first time.",

        "image_filename":
            "l1_01_my_name_lina.png",

        "video_filename":
            "l1_01_my_name_lina.mp4",

        "build_tokens":
            [],

        "sort_order":
            1,
    },

    {
        "level_id":
            1,

        "english_text":
            "What is your name?",

        "asl_gloss":
            "",

        "meaning":
            "Use this sentence to ask another person "
            "for their name.",

        "scenario":
            "You have just met someone and want to know "
            "their name.",

        "image_filename":
            "l1_02_what_is_your_name.png",

        "video_filename":
            "l1_02_what_is_your_name.mp4",

        "build_tokens":
            [],

        "sort_order":
            2,
    },

    {
        "level_id":
            1,

        "english_text":
            "Nice to meet you.",

        "asl_gloss":
            "",

        "meaning":
            "A friendly sentence used when meeting "
            "someone for the first time.",

        "scenario":
            "You have just introduced yourself to "
            "another person.",

        "image_filename":
            "l1_03_nice_to_meet_you.png",

        "video_filename":
            "l1_03_nice_to_meet_you.mp4",

        "build_tokens":
            [],

        "sort_order":
            3,
    },

    {
        "level_id":
            1,

        "english_text":
            "I am 20 years old.",

        "asl_gloss":
            "",

        "meaning":
            "Use this sentence to communicate your age.",

        "scenario":
            "Someone asks how old you are.",

        "image_filename":
            "l1_04_age_20.png",

        "video_filename":
            "l1_04_age_20.mp4",

        "build_tokens":
            [],

        "sort_order":
            4,
    },

    {
        "level_id":
            1,

        "english_text":
            "I am Deaf.",

        "asl_gloss":
            "",

        "meaning":
            "Use this sentence when you want to tell "
            "someone that you are Deaf.",

        "scenario":
            "You need to explain that you are Deaf "
            "during a conversation.",

        "image_filename":
            "l1_05_i_am_deaf.png",

        "video_filename":
            "l1_05_i_am_deaf.mp4",

        "build_tokens":
            [],

        "sort_order":
            5,
    },

    {
        "level_id":
            1,

        "english_text":
            "I live in Beirut.",

        "asl_gloss":
            "",

        "meaning":
            "Use this sentence to tell someone where "
            "you live.",

        "scenario":
            "Someone asks where you live.",

        "image_filename":
            "l1_06_live_beirut.png",

        "video_filename":
            "l1_06_live_beirut.mp4",

        "build_tokens":
            [],

        "sort_order":
            6,
    },
]


# ============================================================
# LEVEL 1 QUIZ
# ============================================================

QUIZ_QUESTIONS = [
    {
        "level_id":
            1,

        "question_type":
            "scenario_choice",

        "question":
            "You meet someone for the first time. "
            "Which sentence introduces your name?",

        "image_filename":
            "l1_01_my_name_lina.png",

        "video_filename":
            "",

        "options": [
            "My name is Lina.",
            "I live in Beirut.",
            "I am 20 years old.",
        ],

        "correct_answer":
            "My name is Lina.",

        "explanation":
            "Use 'My name is Lina.' to introduce yourself.",

        "sort_order":
            1,
    },

    {
        "level_id":
            1,

        "question_type":
            "meaning_choice",

        "question":
            "Which sentence asks another person "
            "for their name?",

        "image_filename":
            "l1_02_what_is_your_name.png",

        "video_filename":
            "",

        "options": [
            "Nice to meet you.",
            "What is your name?",
            "I am Deaf.",
        ],

        "correct_answer":
            "What is your name?",

        "explanation":
            "This sentence is used to ask for "
            "someone's name.",

        "sort_order":
            2,
    },

    {
        "level_id":
            1,

        "question_type":
            "scenario_choice",

        "question":
            "Which sentence communicates your age?",

        "image_filename":
            "l1_04_age_20.png",

        "video_filename":
            "",

        "options": [
            "I am 20 years old.",
            "My name is Lina.",
            "I live in Beirut.",
        ],

        "correct_answer":
            "I am 20 years old.",

        "explanation":
            "This sentence tells another person "
            "your age.",

        "sort_order":
            3,
    },

    {
        "level_id":
            1,

        "question_type":
            "scenario_choice",

        "question":
            "Which sentence tells someone that "
            "you are Deaf?",

        "image_filename":
            "l1_05_i_am_deaf.png",

        "video_filename":
            "",

        "options": [
            "I am Deaf.",
            "Nice to meet you.",
            "What is your name?",
        ],

        "correct_answer":
            "I am Deaf.",

        "explanation":
            "This sentence communicates that "
            "you are Deaf.",

        "sort_order":
            4,
    },

    {
        "level_id":
            1,

        "question_type":
            "scenario_choice",

        "question":
            "Someone asks where you live. "
            "Which sentence answers them?",

        "image_filename":
            "l1_06_live_beirut.png",

        "video_filename":
            "",

        "options": [
            "I live in Beirut.",
            "I am Deaf.",
            "Nice to meet you.",
        ],

        "correct_answer":
            "I live in Beirut.",

        "explanation":
            "This sentence tells another person "
            "where you live.",

        "sort_order":
            5,
    },
]


# ============================================================
# CREATE FOLDERS
# ============================================================

def create_folders():
    EDUCATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EDUCATION_IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EDUCATION_VIDEOS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():
    connection = sqlite3.connect(
        EDUCATION_DB_PATH
    )

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS education_levels (
                id INTEGER PRIMARY KEY,

                title TEXT NOT NULL,

                subtitle TEXT
                    NOT NULL DEFAULT '',

                description TEXT
                    NOT NULL DEFAULT '',

                primary_color TEXT
                    NOT NULL DEFAULT '#2196F3',

                secondary_color TEXT
                    NOT NULL DEFAULT '#81D4FA',

                hero_image_filename TEXT
                    NOT NULL DEFAULT '',

                locked_by_default INTEGER
                    NOT NULL DEFAULT 1,

                sort_order INTEGER
                    NOT NULL DEFAULT 0
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS education_sentences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                level_id INTEGER NOT NULL,

                english_text TEXT NOT NULL,

                asl_gloss TEXT
                    NOT NULL DEFAULT '',

                meaning TEXT
                    NOT NULL DEFAULT '',

                scenario TEXT
                    NOT NULL DEFAULT '',

                image_filename TEXT
                    NOT NULL DEFAULT '',

                video_filename TEXT
                    NOT NULL DEFAULT '',

                build_tokens_json TEXT
                    NOT NULL DEFAULT '[]',

                sort_order INTEGER
                    NOT NULL DEFAULT 0,

                FOREIGN KEY(level_id)
                    REFERENCES education_levels(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS education_quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                level_id INTEGER NOT NULL,

                question_type TEXT
                    NOT NULL DEFAULT '',

                question TEXT NOT NULL,

                image_filename TEXT
                    NOT NULL DEFAULT '',

                video_filename TEXT
                    NOT NULL DEFAULT '',

                options_json TEXT
                    NOT NULL DEFAULT '[]',

                correct_answer TEXT
                    NOT NULL DEFAULT '',

                explanation TEXT
                    NOT NULL DEFAULT '',

                sort_order INTEGER
                    NOT NULL DEFAULT 0,

                FOREIGN KEY(level_id)
                    REFERENCES education_levels(id)
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# RESET DATA
# ============================================================

def clear_existing_data(
    connection,
):
    connection.execute(
        """
        DELETE FROM education_quiz_questions
        """
    )

    connection.execute(
        """
        DELETE FROM education_sentences
        """
    )

    connection.execute(
        """
        DELETE FROM education_levels
        """
    )


# ============================================================
# INSERT LEVELS
# ============================================================

def insert_levels(
    connection,
):
    for level in LEVELS:
        connection.execute(
            """
            INSERT INTO education_levels (
                id,
                title,
                subtitle,
                description,
                primary_color,
                secondary_color,
                hero_image_filename,
                locked_by_default,
                sort_order
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                level["id"],
                level["title"],
                level["subtitle"],
                level["description"],
                level["primary_color"],
                level["secondary_color"],
                level[
                    "hero_image_filename"
                ],
                level[
                    "locked_by_default"
                ],
                level["sort_order"],
            ),
        )


# ============================================================
# INSERT SENTENCES
# ============================================================

def insert_sentences(
    connection,
):
    for sentence in SENTENCES:
        connection.execute(
            """
            INSERT INTO education_sentences (
                level_id,
                english_text,
                asl_gloss,
                meaning,
                scenario,
                image_filename,
                video_filename,
                build_tokens_json,
                sort_order
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sentence["level_id"],
                sentence["english_text"],
                sentence["asl_gloss"],
                sentence["meaning"],
                sentence["scenario"],
                sentence[
                    "image_filename"
                ],
                sentence[
                    "video_filename"
                ],
                json.dumps(
                    sentence[
                        "build_tokens"
                    ]
                ),
                sentence["sort_order"],
            ),
        )


# ============================================================
# INSERT QUIZ
# ============================================================

def insert_quiz(
    connection,
):
    for question in QUIZ_QUESTIONS:
        connection.execute(
            """
            INSERT INTO education_quiz_questions (
                level_id,
                question_type,
                question,
                image_filename,
                video_filename,
                options_json,
                correct_answer,
                explanation,
                sort_order
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question["level_id"],
                question[
                    "question_type"
                ],
                question["question"],
                question[
                    "image_filename"
                ],
                question[
                    "video_filename"
                ],
                json.dumps(
                    question["options"]
                ),
                question[
                    "correct_answer"
                ],
                question[
                    "explanation"
                ],
                question[
                    "sort_order"
                ],
            ),
        )


# ============================================================
# PREPARE EDUCATION
# ============================================================

def prepare_education():
    print()
    print("=" * 72)
    print(
        "SIGNBRIDGE EDUCATION PREPARATION"
    )
    print("=" * 72)

    print()
    print("Backend root:")
    print(BACKEND_ROOT)

    print()
    print("Education database:")
    print(EDUCATION_DB_PATH)

    print()

    create_folders()

    create_database()

    connection = sqlite3.connect(
        EDUCATION_DB_PATH
    )

    try:
        clear_existing_data(
            connection
        )

        insert_levels(
            connection
        )

        insert_sentences(
            connection
        )

        insert_quiz(
            connection
        )

        connection.commit()

    finally:
        connection.close()

    connection = sqlite3.connect(
        EDUCATION_DB_PATH
    )

    try:
        levels = connection.execute(
            """
            SELECT COUNT(*)
            FROM education_levels
            """
        ).fetchone()[0]

        sentences = connection.execute(
            """
            SELECT COUNT(*)
            FROM education_sentences
            """
        ).fetchone()[0]

        quiz = connection.execute(
            """
            SELECT COUNT(*)
            FROM education_quiz_questions
            """
        ).fetchone()[0]

    finally:
        connection.close()

    print()
    print("=" * 72)
    print(
        "SIGNBRIDGE EDUCATION DATABASE READY"
    )
    print("=" * 72)

    print()
    print(
        f"Levels          : {levels}"
    )

    print(
        f"Sentences       : {sentences}"
    )

    print(
        f"Quiz questions  : {quiz}"
    )

    print()

    print("Database:")
    print(EDUCATION_DB_PATH)

    print()

    print("3D Images folder:")
    print(EDUCATION_IMAGES_DIR)

    print()

    print("Sentence Videos folder:")
    print(EDUCATION_VIDEOS_DIR)

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    prepare_education()