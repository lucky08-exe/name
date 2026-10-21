"""
database.py - Database setup and connection helper for QuizLens.

This module initializes the SQLite database and creates the four required tables:
1. students
2. quizzes
3. questions
4. responses
"""

import sqlite3

DATABASE_NAME = "quizlens.db"


def get_connection():
    """Returns a connection to the SQLite database with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_NAME)
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    # Return rows as sqlite3.Row so columns can be accessed by name
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates database tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        );
    """)

    # 2. Quizzes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            total_marks INTEGER NOT NULL
        );
    """)

    # 3. Questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            topic TEXT NOT NULL,
            marks INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
        );
    """)

    # 4. Responses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            submitted_answer TEXT NOT NULL,
            correctness INTEGER NOT NULL, -- 1 for correct, 0 for incorrect
            marks_awarded INTEGER NOT NULL,
            response_time_seconds INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
