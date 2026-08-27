"""
Skill Quiz - FastAPI Server
Wraps the quiz API into HTTP endpoints for the Skillify app.

Run:
    uvicorn server:app --reload --port 8001

Endpoints:
    GET  /api/quiz/skills              → available skills
    POST /api/quiz/start               → start quiz for a skill
    GET  /api/quiz/{session_id}/question/{num} → get question
    POST /api/quiz/{session_id}/answer  → submit answer
    GET  /api/quiz/{session_id}/results → final results
    GET  /api/quiz/{session_id}/progress → progress
    GET  /api/quiz/{session_id}/time    → time remaining
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api import SkillQuizAPI

app = FastAPI(title="Skillify Quiz API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

quiz_api = SkillQuizAPI()


class StartQuiz(BaseModel):
    skill: str


class SubmitAnswer(BaseModel):
    question_number: int
    answer: str


@app.get("/api/quiz/skills")
def list_skills():
    return {"skills": quiz_api.get_available_skills()}


@app.post("/api/quiz/start")
def start_quiz(req: StartQuiz):
    try:
        return quiz_api.start_quiz(req.skill)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/quiz/{session_id}/question/{question_number}")
def get_question(session_id: str, question_number: int):
    try:
        return quiz_api.get_question(session_id, question_number)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/api/quiz/{session_id}/answer")
def submit_answer(session_id: str, req: SubmitAnswer):
    try:
        return quiz_api.submit_answer(session_id, req.question_number, req.answer)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/quiz/{session_id}/results")
def get_results(session_id: str):
    try:
        return quiz_api.get_results(session_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/api/quiz/{session_id}/progress")
def get_progress(session_id: str):
    try:
        return quiz_api.get_progress(session_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/api/quiz/{session_id}/time")
def get_time(session_id: str):
    try:
        return quiz_api.get_time_remaining(session_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/health")
def health():
    return {"status": "ok", "service": "skill-quiz"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
