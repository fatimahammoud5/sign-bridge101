from __future__ import annotations

import json
import sqlite3

from pathlib import Path

from flask import (
    Blueprint,
    jsonify,
    send_from_directory,
    url_for,
)


# ============================================================
# BLUEPRINT
# ============================================================

education_bp = Blueprint(
    "education",
    __name__,
)


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
# FOLDERS
# ============================================================

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
# DEBUG
# ============================================================

print()
print("=" * 72)
print("EDUCATION BACKEND PATH CHECK")
print("=" * 72)

print("Education backend:")
print(Path(__file__).resolve())

print()
print("Education database:")
print(EDUCATION_DB_PATH)

print(
    "Education database exists:",
    EDUCATION_DB_PATH.exists(),
)

print()
print("Education images:")
print(EDUCATION_IMAGES_DIR)

print()
print("Education videos:")
print(EDUCATION_VIDEOS_DIR)

print("=" * 72)
print()


# ============================================================
# ACTIVITIES
# ============================================================

EDUCATION_ACTIVITIES = [
    {
        "id":
            "learn_watch",

        "title":
            "Learn & Watch",

        "description":
            "Understand complete ASL sentences "
            "through visual context and signing.",
    },

    {
        "id":
            "build_sentence",

        "title":
            "Build the Sentence",

        "description":
            "Arrange sentence parts to understand "
            "ASL sentence structure.",
    },

    {
        "id":
            "real_life",

        "title":
            "Real-Life Practice",

        "description":
            "Choose the best sentence for a "
            "real-life communication situation.",
    },
]


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    if not EDUCATION_DB_PATH.exists():
        raise FileNotFoundError(
            "Education database not found: "
            f"{EDUCATION_DB_PATH}"
        )

    connection = sqlite3.connect(
        EDUCATION_DB_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


# ============================================================
# HELPERS
# ============================================================

def safe_json_loads(
    value,
    default,
):
    if value is None:
        return default

    if isinstance(
        value,
        (
            list,
            dict,
        ),
    ):
        return value

    text = str(value).strip()

    if not text:
        return default

    try:
        return json.loads(
            text
        )

    except Exception:
        return default


def file_exists(
    folder: Path,
    filename: str,
) -> bool:
    if not filename:
        return False

    return (
        folder
        / filename
    ).exists()


# ============================================================
# SERIALIZE LEVEL
# ============================================================

def serialize_level(
    row,
):
    hero_filename = (
        row["hero_image_filename"]
        or ""
    )

    hero_available = file_exists(
        EDUCATION_IMAGES_DIR,
        hero_filename,
    )

    hero_url = ""

    if hero_filename:
        hero_url = url_for(
            "education.education_image",
            filename=hero_filename,
            _external=True,
        )

    return {
        "id":
            int(row["id"]),

        "title":
            row["title"],

        "subtitle":
            row["subtitle"],

        "description":
            row["description"],

        "primary_color":
            row["primary_color"],

        "secondary_color":
            row["secondary_color"],

        "hero_image_filename":
            hero_filename,

        "hero_image_url":
            hero_url,

        "hero_image_available":
            hero_available,

        "locked_by_default":
            bool(
                row["locked_by_default"]
            ),

        "sort_order":
            int(row["sort_order"]),
    }


# ============================================================
# SERIALIZE SENTENCE
# ============================================================

def serialize_sentence(
    row,
):
    image_filename = (
        row["image_filename"]
        or ""
    )

    video_filename = (
        row["video_filename"]
        or ""
    )

    image_available = file_exists(
        EDUCATION_IMAGES_DIR,
        image_filename,
    )

    video_available = file_exists(
        EDUCATION_VIDEOS_DIR,
        video_filename,
    )

    image_url = ""

    if image_filename:
        image_url = url_for(
            "education.education_image",
            filename=image_filename,
            _external=True,
        )

    video_url = ""

    if video_filename:
        video_url = url_for(
            "education.education_video",
            filename=video_filename,
            _external=True,
        )

    return {
        "id":
            int(row["id"]),

        "level_id":
            int(row["level_id"]),

        "english_text":
            row["english_text"],

        "asl_gloss":
            row["asl_gloss"]
            or "",

        "meaning":
            row["meaning"]
            or "",

        "scenario":
            row["scenario"]
            or "",

        "image_filename":
            image_filename,

        "image_url":
            image_url,

        "image_available":
            image_available,

        "video_filename":
            video_filename,

        "video_url":
            video_url,

        "video_available":
            video_available,

        "build_tokens":
            safe_json_loads(
                row["build_tokens_json"],
                [],
            ),

        "sort_order":
            int(row["sort_order"]),
    }


# ============================================================
# SERIALIZE QUIZ
# ============================================================

def serialize_quiz(
    row,
):
    image_filename = (
        row["image_filename"]
        or ""
    )

    video_filename = (
        row["video_filename"]
        or ""
    )

    image_available = file_exists(
        EDUCATION_IMAGES_DIR,
        image_filename,
    )

    video_available = file_exists(
        EDUCATION_VIDEOS_DIR,
        video_filename,
    )

    image_url = ""

    if image_filename:
        image_url = url_for(
            "education.education_image",
            filename=image_filename,
            _external=True,
        )

    video_url = ""

    if video_filename:
        video_url = url_for(
            "education.education_video",
            filename=video_filename,
            _external=True,
        )

    return {
        "id":
            int(row["id"]),

        "level_id":
            int(row["level_id"]),

        "question_type":
            row["question_type"],

        "question":
            row["question"],

        "image_filename":
            image_filename,

        "image_url":
            image_url,

        "image_available":
            image_available,

        "video_filename":
            video_filename,

        "video_url":
            video_url,

        "video_available":
            video_available,

        "options":
            safe_json_loads(
                row["options_json"],
                [],
            ),

        "correct_answer":
            row["correct_answer"],

        "explanation":
            row["explanation"]
            or "",

        "sort_order":
            int(row["sort_order"]),
    }


# ============================================================
# HEALTH
# ============================================================

@education_bp.get(
    "/api/education/health"
)
def education_health():
    try:
        connection = (
            get_connection()
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

        return jsonify(
            {
                "success":
                    True,

                "message":
                    "Education API is running",

                "levels":
                    int(levels),

                "sentences":
                    int(sentences),

                "quiz_questions":
                    int(quiz),

                "database":
                    str(
                        EDUCATION_DB_PATH
                    ),
            }
        )

    except Exception as error:
        print(
            "Education health error:",
            repr(error),
        )

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),

                "database":
                    str(
                        EDUCATION_DB_PATH
                    ),

                "database_exists":
                    EDUCATION_DB_PATH.exists(),
            }
        ), 500


# ============================================================
# LEVELS
# ============================================================

@education_bp.get(
    "/api/education/levels"
)
def education_levels():
    try:
        connection = (
            get_connection()
        )

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM education_levels

                ORDER BY sort_order, id
                """
            ).fetchall()

            result = []

            for row in rows:
                item = serialize_level(
                    row
                )

                sentence_count = (
                    connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM education_sentences

                        WHERE level_id = ?
                        """,
                        (
                            row["id"],
                        ),
                    ).fetchone()[0]
                )

                quiz_count = (
                    connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM education_quiz_questions

                        WHERE level_id = ?
                        """,
                        (
                            row["id"],
                        ),
                    ).fetchone()[0]
                )

                item[
                    "sentence_count"
                ] = int(
                    sentence_count
                )

                item[
                    "quiz_count"
                ] = int(
                    quiz_count
                )

                item[
                    "activities"
                ] = EDUCATION_ACTIVITIES

                result.append(
                    item
                )

        finally:
            connection.close()

        return jsonify(
            {
                "success":
                    True,

                "count":
                    len(result),

                "levels":
                    result,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# LEVEL DETAILS
# ============================================================

@education_bp.get(
    "/api/education/levels/<int:level_id>"
)
def education_level_details(
    level_id: int,
):
    try:
        connection = (
            get_connection()
        )

        try:
            row = connection.execute(
                """
                SELECT *
                FROM education_levels

                WHERE id = ?

                LIMIT 1
                """,
                (
                    level_id,
                ),
            ).fetchone()

            if row is None:
                return jsonify(
                    {
                        "success":
                            False,

                        "message":
                            "Level not found.",
                    }
                ), 404

            level = serialize_level(
                row
            )

            sentence_count = (
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM education_sentences

                    WHERE level_id = ?
                    """,
                    (
                        level_id,
                    ),
                ).fetchone()[0]
            )

            quiz_count = (
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM education_quiz_questions

                    WHERE level_id = ?
                    """,
                    (
                        level_id,
                    ),
                ).fetchone()[0]
            )

            level[
                "sentence_count"
            ] = int(
                sentence_count
            )

            level[
                "quiz_count"
            ] = int(
                quiz_count
            )

            level[
                "activities"
            ] = EDUCATION_ACTIVITIES

        finally:
            connection.close()

        return jsonify(
            {
                "success":
                    True,

                "level":
                    level,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# LEVEL SENTENCES
# ============================================================

@education_bp.get(
    "/api/education/levels/<int:level_id>/sentences"
)
def education_level_sentences(
    level_id: int,
):
    try:
        connection = (
            get_connection()
        )

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM education_sentences

                WHERE level_id = ?

                ORDER BY sort_order, id
                """,
                (
                    level_id,
                ),
            ).fetchall()

        finally:
            connection.close()

        sentences = [
            serialize_sentence(
                row
            )
            for row in rows
        ]

        return jsonify(
            {
                "success":
                    True,

                "level_id":
                    level_id,

                "count":
                    len(sentences),

                "sentences":
                    sentences,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# SENTENCE DETAILS
# ============================================================

@education_bp.get(
    "/api/education/sentences/<int:sentence_id>"
)
def education_sentence_details(
    sentence_id: int,
):
    try:
        connection = (
            get_connection()
        )

        try:
            row = connection.execute(
                """
                SELECT *
                FROM education_sentences

                WHERE id = ?

                LIMIT 1
                """,
                (
                    sentence_id,
                ),
            ).fetchone()

        finally:
            connection.close()

        if row is None:
            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Sentence not found.",
                }
            ), 404

        return jsonify(
            {
                "success":
                    True,

                "sentence":
                    serialize_sentence(
                        row
                    ),
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# QUIZ
# ============================================================

@education_bp.get(
    "/api/education/levels/<int:level_id>/quiz"
)
def education_level_quiz(
    level_id: int,
):
    try:
        connection = (
            get_connection()
        )

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM education_quiz_questions

                WHERE level_id = ?

                ORDER BY sort_order, id
                """,
                (
                    level_id,
                ),
            ).fetchall()

        finally:
            connection.close()

        questions = [
            serialize_quiz(
                row
            )
            for row in rows
        ]

        return jsonify(
            {
                "success":
                    True,

                "level_id":
                    level_id,

                "count":
                    len(questions),

                "questions":
                    questions,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# IMAGES
# ============================================================

@education_bp.get(
    "/api/education/images/<path:filename>"
)
def education_image(
    filename: str,
):
    return send_from_directory(
        EDUCATION_IMAGES_DIR,
        filename,
        conditional=True,
    )


# ============================================================
# VIDEOS
# ============================================================

@education_bp.get(
    "/api/education/videos/<path:filename>"
)
def education_video(
    filename: str,
):
    return send_from_directory(
        EDUCATION_VIDEOS_DIR,
        filename,
        conditional=True,
    )