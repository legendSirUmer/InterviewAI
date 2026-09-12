"""Database package for InterviewAI."""
from .db import (
    init_db,
    save_interview,
    get_interview_history,
    get_interview_details,
    get_performance_trends,
    delete_interview,
)

__all__ = [
    "init_db",
    "save_interview",
    "get_interview_history",
    "get_interview_details",
    "get_performance_trends",
    "delete_interview",
]
