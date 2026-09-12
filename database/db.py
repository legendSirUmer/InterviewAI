"""
SQLite Database Module for InterviewAI.
Handles persistent storage of interview sessions, question/answer history,
scores across 6 dimensions, voice metrics, and historical trend analytics.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = os.environ.get("INTERVIEW_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "interview_history.db"))


def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            candidate_name TEXT,
            target_role TEXT NOT NULL,
            experience_level TEXT,
            interview_type TEXT,
            difficulty TEXT,
            personality TEXT,
            overall_score REAL DEFAULT 0.0,
            total_questions INTEGER DEFAULT 0,
            summary_json TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_number INTEGER NOT NULL,
            category TEXT,
            question_text TEXT NOT NULL,
            answer_text TEXT,
            difficulty TEXT,
            technical_score REAL DEFAULT 0.0,
            completeness_score REAL DEFAULT 0.0,
            depth_score REAL DEFAULT 0.0,
            communication_score REAL DEFAULT 0.0,
            problem_solving_score REAL DEFAULT 0.0,
            role_relevance_score REAL DEFAULT 0.0,
            feedback_json TEXT,
            voice_metrics_json TEXT,
            FOREIGN KEY (session_id) REFERENCES interviews (session_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def save_interview(
    session_id,
    candidate_name,
    target_role,
    experience_level,
    interview_type,
    difficulty,
    personality,
    feedback_history,
    interview_state=None,
):
    """
    Saves or updates an interview session along with all question/answer records.
    Calculates the 6-dimensional aggregate overall score (percentage 0-100%).
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate overall score across all dimensions in feedback_history
    scores = []
    for item in feedback_history:
        fb = item.get("feedback", {})
        for dim in [
            "technical_score",
            "completeness_score",
            "depth_score",
            "communication_score",
            "problem_solving_score",
            "role_relevance_score",
        ]:
            val = fb.get(dim)
            if isinstance(val, (int, float)):
                scores.append(float(val))

    # Convert 1-10 scale to percentage (e.g. 8.2 / 10 -> 82%)
    overall_score = round((sum(scores) / len(scores)) * 10, 1) if scores else 0.0

    summary_data = {
        "interview_state": interview_state or {},
        "completed_at": datetime.now().isoformat(),
        "score_percentage": overall_score,
    }

    # Insert or replace interview session
    cursor.execute(
        """
        INSERT INTO interviews (
            session_id, timestamp, candidate_name, target_role,
            experience_level, interview_type, difficulty, personality,
            overall_score, total_questions, summary_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            candidate_name=excluded.candidate_name,
            target_role=excluded.target_role,
            overall_score=excluded.overall_score,
            total_questions=excluded.total_questions,
            summary_json=excluded.summary_json
        """,
        (
            session_id,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            candidate_name or "Candidate",
            target_role,
            experience_level,
            interview_type,
            difficulty,
            personality,
            overall_score,
            len(feedback_history),
            json.dumps(summary_data),
        ),
    )

    # Replace QA records for this session
    cursor.execute("DELETE FROM qa_records WHERE session_id = ?", (session_id,))

    for idx, item in enumerate(feedback_history, start=1):
        fb = item.get("feedback", {})
        voice_metrics = item.get("voice_metrics", {})

        cursor.execute(
            """
            INSERT INTO qa_records (
                session_id, question_number, category, question_text, answer_text,
                difficulty, technical_score, completeness_score, depth_score,
                communication_score, problem_solving_score, role_relevance_score,
                feedback_json, voice_metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                idx,
                item.get("category", "General"),
                item.get("question", ""),
                item.get("answer", ""),
                item.get("difficulty", difficulty),
                float(fb.get("technical_score", 0)),
                float(fb.get("completeness_score", 0)),
                float(fb.get("depth_score", 0)),
                float(fb.get("communication_score", 0)),
                float(fb.get("problem_solving_score", 0)),
                float(fb.get("role_relevance_score", 0)),
                json.dumps(fb),
                json.dumps(voice_metrics),
            ),
        )

    conn.commit()
    conn.close()
    return overall_score


def get_interview_history(limit=25):
    """Retrieves list of past interviews ordered by latest first."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT session_id, timestamp, candidate_name, target_role,
               experience_level, interview_type, difficulty, personality,
               overall_score, total_questions
        FROM interviews
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_interview_details(session_id):
    """Retrieves full details and QA records for a specific interview."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM interviews WHERE session_id = ?", (session_id,))
    interview = cursor.fetchone()
    if not interview:
        conn.close()
        return None

    interview_data = dict(interview)
    if interview_data.get("summary_json"):
        interview_data["summary"] = json.loads(interview_data["summary_json"])

    cursor.execute(
        """
        SELECT * FROM qa_records
        WHERE session_id = ?
        ORDER BY question_number ASC
        """,
        (session_id,),
    )
    qa_rows = cursor.fetchall()
    conn.close()

    qa_list = []
    for r in qa_rows:
        d = dict(r)
        d["feedback"] = json.loads(d["feedback_json"]) if d.get("feedback_json") else {}
        d["voice_metrics"] = json.loads(d["voice_metrics_json"]) if d.get("voice_metrics_json") else {}
        qa_list.append(d)

    interview_data["questions"] = qa_list
    return interview_data


def get_performance_trends():
    """Retrieves historical scores for plotting progress over time."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, timestamp, target_role, overall_score, total_questions
        FROM interviews
        WHERE total_questions > 0
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_interview(session_id):
    """Deletes an interview and its QA records."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM qa_records WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM interviews WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
