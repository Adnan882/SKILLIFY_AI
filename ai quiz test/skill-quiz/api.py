"""
Skill Quiz API - Backend module for app integration.

Usage:
    from api import SkillQuizAPI

    quiz = SkillQuizAPI()

    # Start a quiz
    session = quiz.start_quiz("python")

    # session contains:
    # {
    #   "session_id": "abc123",
    #   "skill": "python",
    #   "total_questions": 20,
    #   "questions": [
    #     {
    #       "question_number": 1,
    #       "question": "What is 2+2?",
    #       "type": "mcq",
    #       "type_label": "Multiple Choice",
    #       "options": ["2", "4", "6", "8"],
    #       "option_letters": ["a", "b", "c", "d"]
    #     },
    #     ...
    #   ]
    # }

    # Submit answer for question 1
    result = quiz.submit_answer(session["session_id"], 1, "b")
    # result: {"correct": true, "points": 1, "correct_answer": "4", ...}

    # Get final results after all answers
    final = quiz.get_results(session["session_id"])
    # final: {"acquired": true, "accuracy": 90.0, "message": "Congratulations!...", ...}
"""

import uuid
import time
from quiz_engine import (
    load_questions,
    select_quiz,
    format_question_for_user,
    grade_answer,
    calculate_results,
    get_review_data,
    ACCURACY_THRESHOLD,
    QUIZ_SIZE,
    QUESTION_TIME_LIMIT,
    QUIZ_TIME_LIMIT,
    VALID_SKILLS,
    normalize_skill,
)


class SkillQuizAPI:
    def __init__(self):
        self._sessions = {}

    def get_available_skills(self) -> list[str]:
        return VALID_SKILLS.copy()

    def start_quiz(self, skill: str) -> dict:
        skill_key = normalize_skill(skill)
        if not skill_key:
            raise ValueError(f"Unknown skill: '{skill}'. Choose from: {', '.join(VALID_SKILLS)}")

        questions = load_questions(skill_key)
        quiz = select_quiz(questions)

        session_id = str(uuid.uuid4())[:8]
        session = {
            "session_id": session_id,
            "skill": skill_key,
            "total_questions": len(quiz),
            "questions": quiz,
            "answers": [],
            "current_index": 0,
            "finished": False,
            "start_time": time.time(),
        }
        self._sessions[session_id] = session

        formatted_questions = [
            format_question_for_user(q, i, len(quiz))
            for i, q in enumerate(quiz)
        ]

        return {
            "session_id": session_id,
            "skill": skill_key,
            "total_questions": len(quiz),
            "threshold": ACCURACY_THRESHOLD,
            "question_time_limit": QUESTION_TIME_LIMIT,
            "quiz_time_limit": QUIZ_TIME_LIMIT,
            "questions": formatted_questions,
        }

    def get_question(self, session_id: str, question_number: int) -> dict:
        session = self._get_session(session_id)
        idx = question_number - 1
        if idx < 0 or idx >= len(session["questions"]):
            raise ValueError(f"Invalid question number: {question_number}")

        return format_question_for_user(
            session["questions"][idx], idx, session["total_questions"]
        )

    def submit_answer(self, session_id: str, question_number: int, answer: str) -> dict:
        session = self._get_session(session_id)
        idx = question_number - 1
        if idx < 0 or idx >= len(session["questions"]):
            raise ValueError(f"Invalid question number: {question_number}")

        question = session["questions"][idx]
        result = grade_answer(answer, question)
        result["question_number"] = question_number
        result["question"] = question["q"]
        result["type"] = question["type"]

        session["answers"].append(result)
        return result

    def get_results(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        if session["finished"]:
            return session["cached_results"]

        results = calculate_results(session["answers"], session["total_questions"])
        results["skill"] = session["skill"]
        results["session_id"] = session_id
        results["answers"] = session["answers"]
        results["review"] = get_review_data(session["answers"])
        results["time_taken"] = round(time.time() - session["start_time"], 1)
        session["finished"] = True
        session["cached_results"] = results
        return results

    def get_time_remaining(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        elapsed = time.time() - session["start_time"]
        remaining = max(0, QUIZ_TIME_LIMIT - elapsed) if QUIZ_TIME_LIMIT > 0 else None
        return {
            "session_id": session_id,
            "elapsed": round(elapsed, 1),
            "remaining": round(remaining, 1) if remaining is not None else None,
            "timed_out": remaining is not None and remaining <= 0,
        }

    def get_progress(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        answered = len(session["answers"])
        correct = sum(1 for a in session["answers"] if a["correct"])
        return {
            "session_id": session_id,
            "skill": session["skill"],
            "answered": answered,
            "total": session["total_questions"],
            "correct_so_far": correct,
            "remaining": session["total_questions"] - answered,
        }

    def _get_session(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            raise ValueError(f"Invalid session_id: '{session_id}'")
        return self._sessions[session_id]


quiz_api = SkillQuizAPI()
