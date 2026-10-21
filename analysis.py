"""
analysis.py - Core Analysis Calculations for QuizLens

This module provides simple, beginner-friendly functions to analyze:
1. Overall class performance
2. Individual student performance
3. Question-level difficulty and error rates
4. Topic-level strengths and weaknesses
5. Quiz-to-quiz comparisons
6. Rule-based diagnostic flags
"""

from database import get_connection

# ==========================================
# Configurable Rule Thresholds
# ==========================================
# A question is flagged if 50% or more students answered it incorrectly.
FLAG_QUESTION_INCORRECT_RATE_THRESHOLD = 50.0

# A topic is flagged if class accuracy is below 60%.
FLAG_TOPIC_ACCURACY_THRESHOLD = 60.0

# Minimum sample size required before drawing firm conclusions or flags
MINIMUM_SAMPLE_SIZE = 5


def safe_percentage(part, total):
    """
    Safely calculates percentage without ZeroDivisionError.
    Returns 0.0 if total is 0 or invalid.
    """
    if total is None or total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def get_class_summary(conn=None):
    """
    Calculates overall class summary metrics:
    - Total students
    - Total quizzes
    - Total questions
    - Total responses
    - Class average score (out of 45)
    - Overall class accuracy percentage
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM students;")
    total_students = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM quizzes;")
    total_quizzes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM questions;")
    total_questions = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM responses;")
    total_responses = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(correctness) AS correct, SUM(marks_awarded) AS marks FROM responses;")
    row = cursor.fetchone()
    total_correct = row["correct"] or 0
    total_marks_awarded = row["marks"] or 0

    cursor.execute("SELECT SUM(marks) AS max_marks FROM questions;")
    single_run_max = cursor.fetchone()["max_marks"] or 0
    total_possible_marks = single_run_max * total_students

    class_accuracy = safe_percentage(total_correct, total_responses)
    avg_score_per_student = round(total_marks_awarded / total_students, 2) if total_students > 0 else 0.0

    if close_at_end:
        conn.close()

    return {
        "total_students": total_students,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "total_responses": total_responses,
        "total_correct": total_correct,
        "total_marks_awarded": total_marks_awarded,
        "class_accuracy": class_accuracy,
        "avg_score_per_student": avg_score_per_student,
        "max_possible_per_student": single_run_max,
    }


def get_student_performances(conn=None):
    """
    Calculates performance for every student across all quizzes:
    - Total marks obtained
    - Percentage
    - Correct count
    - Incorrect count
    - Average response time
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    # Get max possible marks across all quizzes
    cursor.execute("SELECT SUM(marks) AS max_marks FROM questions;")
    max_marks = cursor.fetchone()["max_marks"] or 0

    query = """
        SELECT s.id,
               s.student_code,
               s.name,
               COUNT(r.id) AS total_answered,
               SUM(r.correctness) AS correct_answers,
               (COUNT(r.id) - SUM(r.correctness)) AS incorrect_answers,
               SUM(r.marks_awarded) AS total_marks,
               AVG(r.response_time_seconds) AS avg_time
        FROM students s
        LEFT JOIN responses r ON s.id = r.student_id
        GROUP BY s.id, s.student_code, s.name
        ORDER BY total_marks DESC, s.name ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    student_list = []
    for row in rows:
        total_answered = row["total_answered"] or 0
        correct = row["correct_answers"] or 0
        incorrect = row["incorrect_answers"] or 0
        marks = row["total_marks"] or 0
        pct = safe_percentage(marks, max_marks)
        avg_time = round(row["avg_time"], 1) if row["avg_time"] else 0.0

        student_list.append({
            "id": row["id"],
            "student_code": row["student_code"],
            "name": row["name"],
            "total_answered": total_answered,
            "correct_answers": correct,
            "incorrect_answers": incorrect,
            "total_marks": marks,
            "max_marks": max_marks,
            "percentage": pct,
            "avg_time": avg_time,
        })

    if close_at_end:
        conn.close()

    return student_list


def get_student_detail(student_id, conn=None):
    """
    Returns in-depth performance analysis for a single student:
    - Basic student info
    - Breakdown by quiz
    - Breakdown by topic
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    # Student info
    cursor.execute("SELECT id, student_code, name FROM students WHERE id = ?;", (student_id,))
    student = cursor.fetchone()
    if not student:
        if close_at_end:
            conn.close()
        return None

    # Quiz breakdown
    cursor.execute("""
        SELECT qz.id AS quiz_id,
               qz.title AS quiz_title,
               qz.total_marks,
               COUNT(r.id) AS questions_answered,
               SUM(r.correctness) AS correct_count,
               SUM(r.marks_awarded) AS score,
               AVG(r.response_time_seconds) AS avg_time
        FROM quizzes qz
        JOIN questions q ON q.quiz_id = qz.id
        LEFT JOIN responses r ON r.question_id = q.id AND r.student_id = ?
        GROUP BY qz.id, qz.title, qz.total_marks
        ORDER BY qz.id ASC;
    """, (student_id,))
    quiz_rows = cursor.fetchall()

    quiz_breakdown = []
    for q in quiz_rows:
        answered = q["questions_answered"] or 0
        score = q["score"] or 0
        total_possible = q["total_marks"] or 0
        pct = safe_percentage(score, total_possible)
        avg_time = round(q["avg_time"], 1) if q["avg_time"] else 0.0

        quiz_breakdown.append({
            "quiz_id": q["quiz_id"],
            "quiz_title": q["quiz_title"],
            "questions_answered": answered,
            "score": score,
            "total_marks": total_possible,
            "percentage": pct,
            "avg_time": avg_time,
        })

    # Topic breakdown for this student
    cursor.execute("""
        SELECT q.topic,
               COUNT(r.id) AS total_questions,
               SUM(r.correctness) AS correct_count
        FROM responses r
        JOIN questions q ON r.question_id = q.id
        WHERE r.student_id = ?
        GROUP BY q.topic
        ORDER BY q.topic ASC;
    """, (student_id,))
    topic_rows = cursor.fetchall()

    topic_breakdown = []
    for t in topic_rows:
        tot = t["total_questions"] or 0
        corr = t["correct_count"] or 0
        acc = safe_percentage(corr, tot)
        topic_breakdown.append({
            "topic": t["topic"],
            "total_questions": tot,
            "correct_count": corr,
            "accuracy": acc,
            "is_weak": acc < FLAG_TOPIC_ACCURACY_THRESHOLD,
        })

    if close_at_end:
        conn.close()

    return {
        "student": dict(student),
        "quizzes": quiz_breakdown,
        "topics": topic_breakdown,
    }


def get_quiz_comparisons(conn=None):
    """
    Compares average scores, accuracy, and response times across quizzes.
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    query = """
        SELECT qz.id,
               qz.title,
               qz.date,
               qz.total_marks,
               COUNT(DISTINCT r.student_id) AS student_count,
               COUNT(r.id) AS total_responses,
               SUM(r.correctness) AS total_correct,
               AVG(r.marks_awarded) AS avg_mark_per_q,
               AVG(r.response_time_seconds) AS avg_response_time
        FROM quizzes qz
        LEFT JOIN questions q ON q.quiz_id = qz.id
        LEFT JOIN responses r ON r.question_id = q.id
        GROUP BY qz.id, qz.title, qz.date, qz.total_marks
        ORDER BY qz.id ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    quizzes = []
    for row in rows:
        total_resp = row["total_responses"] or 0
        total_corr = row["total_correct"] or 0
        student_count = row["student_count"] or 0
        total_marks = row["total_marks"] or 0

        # Calculate average total score obtained per student on this quiz
        # (Total correct * marks) / number of students
        avg_student_score = round(total_corr / student_count, 2) if student_count > 0 else 0.0
        accuracy = safe_percentage(total_corr, total_resp)
        avg_time = round(row["avg_response_time"], 1) if row["avg_response_time"] else 0.0

        quizzes.append({
            "id": row["id"],
            "title": row["title"],
            "date": row["date"],
            "total_marks": total_marks,
            "student_count": student_count,
            "total_responses": total_resp,
            "avg_student_score": avg_student_score,
            "accuracy_pct": accuracy,
            "avg_time_sec": avg_time,
        })

    if close_at_end:
        conn.close()

    return quizzes


def get_question_analysis(quiz_id=None, conn=None):
    """
    Calculates error rate, accuracy, and average response time for questions.
    Applies rule-based flags for questions with >= 50% incorrect rate.
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    base_query = """
        SELECT q.id,
               q.quiz_id,
               qz.title AS quiz_title,
               q.question_text,
               q.correct_answer,
               q.topic,
               q.marks,
               COUNT(r.id) AS total_responses,
               SUM(r.correctness) AS correct_count,
               (COUNT(r.id) - SUM(r.correctness)) AS incorrect_count,
               AVG(r.response_time_seconds) AS avg_time
        FROM questions q
        JOIN quizzes qz ON q.quiz_id = qz.id
        LEFT JOIN responses r ON q.id = r.question_id
    """
    params = []
    if quiz_id:
        base_query += " WHERE q.quiz_id = ? "
        params.append(quiz_id)

    base_query += """
        GROUP BY q.id, q.quiz_id, qz.title, q.question_text, q.correct_answer, q.topic, q.marks
        ORDER BY q.id ASC;
    """

    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    questions = []
    for row in rows:
        total = row["total_responses"] or 0
        correct = row["correct_count"] or 0
        incorrect = row["incorrect_count"] or 0
        avg_time = round(row["avg_time"], 1) if row["avg_time"] else 0.0

        incorrect_rate = safe_percentage(incorrect, total)
        accuracy = safe_percentage(correct, total)

        # Rule-based flag check
        is_flagged = False
        flag_reason = ""
        if total >= MINIMUM_SAMPLE_SIZE:
            if incorrect_rate >= FLAG_QUESTION_INCORRECT_RATE_THRESHOLD:
                is_flagged = True
                flag_reason = f"High error rate ({incorrect_rate}% >= {FLAG_QUESTION_INCORRECT_RATE_THRESHOLD}%)"
        else:
            flag_reason = f"Sample too small ({total} < {MINIMUM_SAMPLE_SIZE})"

        questions.append({
            "id": row["id"],
            "quiz_id": row["quiz_id"],
            "quiz_title": row["quiz_title"],
            "question_text": row["question_text"],
            "correct_answer": row["correct_answer"],
            "topic": row["topic"],
            "marks": row["marks"],
            "total_responses": total,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "incorrect_rate_pct": incorrect_rate,
            "accuracy_pct": accuracy,
            "avg_time_sec": avg_time,
            "is_flagged": is_flagged,
            "flag_reason": flag_reason,
        })

    if close_at_end:
        conn.close()

    return questions


def get_topic_analysis(conn=None):
    """
    Aggregates student performance by topic:
    - Total questions in topic
    - Total responses (sample size)
    - Correct & incorrect counts
    - Topic accuracy %
    - Average response time
    - Rule-based flag (< 60% accuracy)
    """
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    cursor = conn.cursor()

    query = """
        SELECT q.topic,
               COUNT(DISTINCT q.id) AS question_count,
               COUNT(r.id) AS total_responses,
               SUM(r.correctness) AS correct_count,
               (COUNT(r.id) - SUM(r.correctness)) AS incorrect_count,
               AVG(r.response_time_seconds) AS avg_time
        FROM questions q
        LEFT JOIN responses r ON q.id = r.question_id
        GROUP BY q.topic
        ORDER BY correct_count * 1.0 / MAX(COUNT(r.id), 1) ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    topics = []
    for row in rows:
        q_count = row["question_count"] or 0
        total_resp = row["total_responses"] or 0
        correct = row["correct_count"] or 0
        incorrect = row["incorrect_count"] or 0
        avg_time = round(row["avg_time"], 1) if row["avg_time"] else 0.0

        accuracy = safe_percentage(correct, total_resp)

        # Rule-based flag check
        is_flagged = False
        flag_reason = ""
        if total_resp >= MINIMUM_SAMPLE_SIZE:
            if accuracy < FLAG_TOPIC_ACCURACY_THRESHOLD:
                is_flagged = True
                flag_reason = f"Low accuracy ({accuracy}% < {FLAG_TOPIC_ACCURACY_THRESHOLD}%)"
        else:
            flag_reason = f"Sample too small ({total_resp} < {MINIMUM_SAMPLE_SIZE})"

        topics.append({
            "topic": row["topic"],
            "question_count": q_count,
            "total_responses": total_resp,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "accuracy_pct": accuracy,
            "avg_time_sec": avg_time,
            "is_flagged": is_flagged,
            "flag_reason": flag_reason,
        })

    if close_at_end:
        conn.close()

    return topics
