"""
QuizLens - simple terminal interface.

Run with: python quizlens_cli.py
The calculations are kept in analysis.py.
"""

from database import get_connection
from analysis import (
    get_class_summary,
    get_student_performances,
    get_student_detail,
    get_quiz_comparisons,
    get_question_analysis,
    get_topic_analysis,
    FLAG_QUESTION_INCORRECT_RATE_THRESHOLD,
    FLAG_TOPIC_ACCURACY_THRESHOLD,
)


def show_summary():
    summary = get_class_summary()
    print("\nCLASS SUMMARY")
    print("-------------")
    print(f"Students:          {summary['total_students']}")
    print(f"Quizzes:           {summary['total_quizzes']}")
    print(f"Questions:         {summary['total_questions']}")
    print(f"Responses:         {summary['total_responses']}")
    print(f"Class accuracy:    {summary['class_accuracy']}%")
    print(
        f"Average score:     {summary['avg_score_per_student']} "
        f"/ {summary['max_possible_per_student']}"
    )


def show_quizzes():
    quizzes = get_quiz_comparisons()
    print("\nQUIZ COMPARISON")
    print("---------------")
    for quiz in quizzes:
        print(f"\n{quiz['title']}")
        print(f"  Average score: {quiz['avg_student_score']} / {quiz['total_marks']}")
        print(f"  Accuracy:      {quiz['accuracy_pct']}%")
        print(f"  Average time:  {quiz['avg_time_sec']} seconds")


def show_topics():
    topics = get_topic_analysis()
    print("\nTOPIC PERFORMANCE")
    print("-----------------")
    print(f"Topics below {FLAG_TOPIC_ACCURACY_THRESHOLD}% accuracy are marked WEAK.\n")
    for topic in topics:
        status = "WEAK - needs revision" if topic["is_flagged"] else "OK"
        print(
            f"{topic['topic']}: {topic['accuracy_pct']}% accuracy "
            f"({topic['correct_count']} correct, {topic['incorrect_count']} wrong) - {status}"
        )


def show_flagged_questions():
    questions = get_question_analysis()
    flagged = [question for question in questions if question["is_flagged"]]

    print("\nQUESTIONS THAT NEED REVIEW")
    print("--------------------------")
    print(
        f"Questions with an incorrect rate of "
        f"{FLAG_QUESTION_INCORRECT_RATE_THRESHOLD}% or more are shown here.\n"
    )

    if not flagged:
        print("No questions were flagged.")
        return

    for question in flagged:
        print(f"\nQuestion {question['id']} - {question['topic']}")
        print(f"Quiz: {question['quiz_title']}")
        print(f"Question: {question['question_text']}")
        print(f"Correct answer: {question['correct_answer']}")
        print(
            f"Correct: {question['correct_count']} | "
            f"Wrong: {question['incorrect_count']} | "
            f"Incorrect rate: {question['incorrect_rate_pct']}%"
        )


def show_all_questions():
    questions = get_question_analysis()
    print("\nALL QUESTIONS")
    print("-------------")
    for question in questions:
        status = "FLAGGED" if question["is_flagged"] else "OK"
        print(
            f"\nQ{question['id']} | Quiz {question['quiz_id']} | "
            f"{question['topic']} | Correct answer: {question['correct_answer']}"
        )
        print(f"  {question['question_text']}")
        print(
            f"  Correct: {question['correct_count']}, "
            f"wrong: {question['incorrect_count']}, "
            f"incorrect rate: {question['incorrect_rate_pct']}% ({status})"
        )


def show_students():
    students = get_student_performances()
    print("\nSTUDENT PERFORMANCE")
    print("-------------------")
    for rank, student in enumerate(students, start=1):
        print(
            f"{rank}. {student['name']} ({student['student_code']}) - "
            f"{student['total_marks']}/{student['max_marks']} marks, "
            f"{student['percentage']}%, average time {student['avg_time']} seconds"
        )


def show_student_detail():
    search = input("\nEnter a student ID or code (for example, 1 or STU001): ").strip()
    if not search:
        print("Please enter a student ID or code.")
        return

    student_id = None
    if search.isdigit():
        student_id = int(search)
    else:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM students WHERE UPPER(student_code) = UPPER(?)",
                (search,),
            )
            row = cursor.fetchone()
            if row:
                student_id = row["id"]
        finally:
            connection.close()

    if student_id is None:
        print(f"No student found for '{search}'.")
        return

    detail = get_student_detail(student_id)
    if not detail:
        print("Could not load that student's details.")
        return

    student = detail["student"]
    print(f"\nSTUDENT: {student['name']} ({student['student_code']})")
    print("-" * 45)

    total_score = 0
    total_possible = 0
    print("\nQuiz results:")
    for quiz in detail["quizzes"]:
        print(
            f"- {quiz['quiz_title']}: {quiz['score']}/{quiz['total_marks']} "
            f"({quiz['percentage']}%), average time {quiz['avg_time']} seconds"
        )
        total_score += quiz["score"]
        total_possible += quiz["total_marks"]

    overall = round(total_score / total_possible * 100, 2) if total_possible else 0
    print(f"\nOverall score: {total_score}/{total_possible} ({overall}%)")

    weak_topics = [
        f"{topic['topic']} ({topic['accuracy']}%)"
        for topic in detail["topics"]
        if topic["is_weak"]
    ]
    if weak_topics:
        print("Topics to revise: " + ", ".join(weak_topics))
    else:
        print("No weak topics were identified.")


def main():
    while True:
        # Do not clear the screen: previous results remain visible.
        print("\n" + "=" * 38)
        print("QUIZLENS - QUIZ PERFORMANCE ANALYSIS")
        print("=" * 38)
        print("1. Class summary")
        print("2. Compare quizzes")
        print("3. Topic performance")
        print("4. Questions that need review")
        print("5. View all questions")
        print("6. Student rankings")
        print("7. Look up one student")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_summary()
        elif choice == "2":
            show_quizzes()
        elif choice == "3":
            show_topics()
        elif choice == "4":
            show_flagged_questions()
        elif choice == "5":
            show_all_questions()
        elif choice == "6":
            show_students()
        elif choice == "7":
            show_student_detail()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 0 to 7.")


if __name__ == "__main__":
    main()
