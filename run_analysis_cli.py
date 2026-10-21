"""
run_analysis_cli.py - Terminal verification of QuizLens calculations.

Runs all core calculations and displays formatted text summaries in the terminal.
"""

from analysis import (
    get_class_summary,
    get_quiz_comparisons,
    get_student_performances,
    get_topic_analysis,
    get_question_analysis,
    FLAG_QUESTION_INCORRECT_RATE_THRESHOLD,
    FLAG_TOPIC_ACCURACY_THRESHOLD
)


def run_cli():
    print("=" * 65)
    print("      QuizLens — Student Quiz Performance Analysis System      ")
    print("=" * 65)

    # 1. Class Summary
    summary = get_class_summary()
    print("\n[1] CLASS OVERALL SUMMARY")
    print("-" * 65)
    print(f"Total Students:        {summary['total_students']}")
    print(f"Total Quizzes:         {summary['total_quizzes']}")
    print(f"Total Questions:       {summary['total_questions']}")
    print(f"Total Responses:       {summary['total_responses']}")
    print(f"Class Accuracy:        {summary['class_accuracy']}%")
    print(f"Avg Score per Student: {summary['avg_score_per_student']} / {summary['max_possible_per_student']}")

    # 2. Quiz Comparisons
    quizzes = get_quiz_comparisons()
    print("\n[2] QUIZ COMPARISON")
    print("-" * 65)
    print(f"{'Quiz Title':<38} | {'Avg Score':<10} | {'Accuracy':<9} | {'Avg Time'}")
    print("-" * 65)
    for q in quizzes:
        print(f"{q['title']:<38} | {q['avg_student_score']:>5} / {q['total_marks']:<2} | {q['accuracy_pct']:>6}%   | {q['avg_time_sec']}s")

    # 3. Topic Analysis with Rule-Based Flags
    topics = get_topic_analysis()
    print("\n[3] TOPIC PERFORMANCE & DIAGNOSTIC FLAGS")
    print(f"(Flag threshold: Accuracy < {FLAG_TOPIC_ACCURACY_THRESHOLD}%)")
    print("-" * 65)
    print(f"{'Topic':<22} | {'Questions':<9} | {'Sample':<7} | {'Accuracy':<9} | {'Status'}")
    print("-" * 65)
    flagged_topics_count = 0
    for t in topics:
        status = "[FLAGGED: WEAK]" if t["is_flagged"] else "Normal"
        if t["is_flagged"]:
            flagged_topics_count += 1
        print(f"{t['topic']:<22} | {t['question_count']:<9} | {t['total_responses']:<7} | {t['accuracy_pct']:>6}%   | {status}")
    print(f"\nTotal Flagged Weak Topics: {flagged_topics_count} out of {len(topics)}")

    # 4. Question Analysis - Sample of Flagged Questions
    questions = get_question_analysis()
    flagged_questions = [q for q in questions if q["is_flagged"]]
    print("\n[4] FLAGGED HIGH-ERROR QUESTIONS")
    print(f"(Flag threshold: Incorrect Rate >= {FLAG_QUESTION_INCORRECT_RATE_THRESHOLD}%)")
    print("-" * 65)
    print(f"Found {len(flagged_questions)} flagged questions out of {len(questions)} total.")
    print("-" * 65)
    for q in flagged_questions[:5]:  # Show first 5
        print(f"Q#{q['id']} [{q['quiz_title'].split(':')[0]}] Topic: {q['topic']}")
        print(f"  Text: {q['question_text']}")
        print(f"  Incorrect Rate: {q['incorrect_rate_pct']}% (Correct: {q['correct_count']}, Incorrect: {q['incorrect_count']})")
        print(f"  Avg Time: {q['avg_time_sec']}s")
        print()

    # 5. Top 5 and Bottom 5 Students
    students = get_student_performances()
    print("[5] STUDENT PERFORMANCE (TOP 5 & BOTTOM 5)")
    print("-" * 65)
    print(f"{'Code':<8} | {'Name':<20} | {'Score':<10} | {'Percentage':<10} | {'Avg Time'}")
    print("-" * 65)
    print("--- Top 5 Students ---")
    for s in students[:5]:
        print(f"{s['student_code']:<8} | {s['name']:<20} | {s['total_marks']:>2} / {s['max_marks']:<4} | {s['percentage']:>6}%    | {s['avg_time']}s")

    print("\n--- Needs Improvement (Bottom 5 Students) ---")
    for s in students[-5:]:
        print(f"{s['student_code']:<8} | {s['name']:<20} | {s['total_marks']:>2} / {s['max_marks']:<4} | {s['percentage']:>6}%    | {s['avg_time']}s")

    print("=" * 65)
    print("Verification completed successfully.")


if __name__ == "__main__":
    run_cli()
