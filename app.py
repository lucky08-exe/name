"""
app.py - Flask Web Application for QuizLens

Provides beginner-friendly routes for the web dashboard:
- /                  : Main Dashboard with KPI cards, Chart.js graphs, and flagged areas
- /students          : Overall student rankings and performance list
- /students/<id>     : Individual student diagnostic report
- /quizzes           : Quiz performance and comparison trends
- /questions         : Question-level difficulty, response times, and error rates
- /topics            : Topic accuracy breakdown and curriculum review flags
- /export/<type>     : CSV export for students, questions, and topics
"""

import csv
import io
from flask import Flask, render_template, request, Response, abort
from database import init_db
from analysis import (
    get_class_summary,
    get_student_performances,
    get_student_detail,
    get_quiz_comparisons,
    get_question_analysis,
    get_topic_analysis,
)

app = Flask(__name__)


@app.route("/")
def dashboard():
    """Renders the main analytics dashboard with KPI cards and charts."""
    summary = get_class_summary()
    quizzes = get_quiz_comparisons()
    questions = get_question_analysis()
    topics = get_topic_analysis()

    # Filter flagged items for the alert sections
    flagged_questions = [q for q in questions if q["is_flagged"]]
    flagged_topics = [t for t in topics if t["is_flagged"]]

    # Prepare data arrays for Chart.js
    quiz_labels = [q["title"].split(":")[0] for q in quizzes]
    quiz_scores = [q["avg_student_score"] for q in quizzes]

    topic_labels = [t["topic"] for t in topics]
    topic_accuracies = [t["accuracy_pct"] for t in topics]

    return render_template(
        "index.html",
        active_page="dashboard",
        summary=summary,
        quizzes=quizzes,
        flagged_questions=flagged_questions,
        flagged_topics=flagged_topics,
        quiz_labels=quiz_labels,
        quiz_scores=quiz_scores,
        topic_labels=topic_labels,
        topic_accuracies=topic_accuracies,
    )


@app.route("/students")
def students():
    """Renders the list of all students and their scores."""
    student_list = get_student_performances()
    return render_template(
        "students.html",
        active_page="students",
        students=student_list
    )


@app.route("/students/<int:student_id>")
def student_detail(student_id):
    """Renders in-depth analysis for a single student."""
    detail = get_student_detail(student_id)
    if detail is None:
        abort(404, description="Student not found")

    return render_template(
        "student_detail.html",
        active_page="students",
        detail=detail
    )


@app.route("/quizzes")
def quizzes():
    """Renders the quiz comparison overview."""
    quiz_list = get_quiz_comparisons()
    return render_template(
        "quizzes.html",
        active_page="quizzes",
        quizzes=quiz_list
    )


@app.route("/questions")
def questions():
    """Renders question-level analytics with filtering options."""
    quiz_id_param = request.args.get("quiz_id")
    show_flagged = request.args.get("flagged") == "1"

    selected_quiz_id = int(quiz_id_param) if quiz_id_param and quiz_id_param.isdigit() else None
    question_list = get_question_analysis(quiz_id=selected_quiz_id)

    if show_flagged:
        question_list = [q for q in question_list if q["is_flagged"]]

    return render_template(
        "questions.html",
        active_page="questions",
        questions=question_list,
        selected_quiz_id=selected_quiz_id,
        show_flagged_only=show_flagged,
    )


@app.route("/topics")
def topics():
    """Renders topic-level accuracy and weakness breakdown."""
    topic_list = get_topic_analysis()
    return render_template(
        "topics.html",
        active_page="topics",
        topics=topic_list
    )


@app.route("/export/<report_type>")
def export_csv(report_type):
    """Exports clean CSV files for offline analysis or spreadsheet import."""
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "students":
        data = get_student_performances()
        filename = "quizlens_students_report.csv"
        writer.writerow(["Student Code", "Name", "Total Answered", "Correct", "Incorrect", "Total Marks", "Max Marks", "Percentage", "Avg Time (sec)"])
        for s in data:
            writer.writerow([
                s["student_code"],
                s["name"],
                s["total_answered"],
                s["correct_answers"],
                s["incorrect_answers"],
                s["total_marks"],
                s["max_marks"],
                s["percentage"],
                s["avg_time"]
            ])

    elif report_type == "questions":
        data = get_question_analysis()
        filename = "quizlens_questions_report.csv"
        writer.writerow(["Question ID", "Quiz", "Topic", "Question Text", "Correct Answer", "Total Responses", "Correct", "Incorrect", "Incorrect Rate (%)", "Avg Time (sec)", "Flagged"])
        for q in data:
            writer.writerow([
                q["id"],
                q["quiz_title"],
                q["topic"],
                q["question_text"],
                q["correct_answer"],
                q["total_responses"],
                q["correct_count"],
                q["incorrect_count"],
                q["incorrect_rate_pct"],
                q["avg_time_sec"],
                "YES" if q["is_flagged"] else "NO"
            ])

    elif report_type == "topics":
        data = get_topic_analysis()
        filename = "quizlens_topics_report.csv"
        writer.writerow(["Topic", "Questions Count", "Total Responses", "Correct", "Incorrect", "Accuracy (%)", "Avg Time (sec)", "Flagged"])
        for t in data:
            writer.writerow([
                t["topic"],
                t["question_count"],
                t["total_responses"],
                t["correct_count"],
                t["incorrect_count"],
                t["accuracy_pct"],
                t["avg_time_sec"],
                "YES" if t["is_flagged"] else "NO"
            ])
    else:
        abort(404, description="Unknown export report type")

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    init_db()
    print("Starting QuizLens Web Server on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
