"""
InterviewAI Studio Cockpit — Next-Gen AI Interview Coach.
UI faithfully referenced and mapped from code.html using Tailwind CSS,
Material Symbols Outlined, Google Fonts (Outfit, Inter, JetBrains Mono),
and Streamlit as the interactive execution frontend.
"""

import os
import re
import uuid
import json
import html
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Custom modules
from database.db import (
    init_db,
    save_interview,
    get_interview_history,
    get_interview_details,
    get_performance_trends,
)
from utils.helpers import (
    analyze_voice_metrics,
    highlight_filler_words,
    remove_filler_words,
    format_duration,
    get_score_color,
)
from utils.coding_problems import get_all_problems, get_problem_by_id
from rag.loader import extract_raw_text, detect_document_type
from rag.retriever import create_rag_pipeline
from services.groq_service import (
    get_api_key,
    get_groq_client,
    transcribe_speech,
)
from services.resume_service import (
    analyze_job_description,
    analyze_resume,
    compare_resume_with_jd,
)
from services.report_service import (
    generate_markdown_report,
    generate_html_report,
)
from agents.interviewer import (
    generate_interview_question,
    PERSONALITY_PROMPTS,
    INTERVIEW_TYPE_GUIDES,
)
from agents.evaluator import evaluate_response, evaluate_code_submission
from agents.manager import AdaptiveInterviewManager, DIFFICULTY_LEVELS


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="InterviewAI Studio Cockpit",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# Streamlit container styling to make Studio Cockpit the full-screen control surface
st.markdown(
    """
    <style>
    [data-testid="stHeader"], header[data-testid="stHeader"], .stApp > header {
        display: none !important;
    }
    [data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
        width: 100% !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
DEFAULTS = {
    "session_id": "sess-8f3a",
    "interview_started": False,
    "candidate_name": "Alex Chen",
    "target_role": "Backend Software Eng",
    "experience_level": "Mid-Level",
    "personality": "FAANG-Style",
    "interview_type": "Technical & System Design",
    "messages": [],
    "feedback_history": [],
    "current_question": "You mentioned deploying Django applications with Docker. Walk me through how you containerized the application, managed multi-stage builds, and handled production configuration & secrets without baking them into image layers.",
    "question_count": 3,
    "total_questions": 6,
    "audio_transcript": "So for our container pipeline, um we started with a multi-stage Alpine Dockerfile. In the build stage, we compiled wheels, and in the runtime stage, we copied only wheels... like avoiding gcc bloat. We also passed environment secrets via AWS Secrets Manager at task startup so they were not baked into layers.",
    "voice_metrics": {
        "speaking_pace_wpm": 142,
        "filler_words_count": 2,
        "filler_words_found": ["um", "like"],
        "duration_seconds": 84,
        "clarity_score": 9.2,
        "pace_rating": "Optimal 🟢",
    },
    "interview_state": {
        "difficulty": "Hard",
        "question_number": 3,
        "skills_tested": ["Docker", "Django", "Secrets Isolation"],
        "weak_areas": ["BuildKit Secret Mounting", "Non-Root Daemon UID"],
        "strong_areas": ["Multi-Stage Separation", "Runtime Secret Isolation"],
        "recent_scores": [8.2, 8.5],
        "interview_plan": [],
    },
    "rag_index": None,
    "document_name": "RESUME_V4_FINAL.PDF",
    "document_text": "",
    "doc_type": "resume",
    "jd_text": "",
    "jd_analysis": None,
    "resume_analysis": None,
    "jd_match_result": None,
    "active_code_solution": "",
    "active_code_eval": {
        "correctness_score": 9.0,
        "time_complexity": "O(1) Amortized",
        "space_complexity": "O(N Clients)",
        "code_quality_score": 8.5,
        "follow_up_question": "Can you optimize memory consumption to prevent unbounded dictionary growth during traffic spikes when thousands of unique one-time IPs never return?",
    },
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

client = get_groq_client()


# ============================================================
# STUDIO COCKPIT CONTROL SURFACE (IN-APP)
# Control Deck completely superseded by Studio Cockpit in code.html:
# - Grok / Groq API configuration & live status
# - 👤 Candidate & Role Setup (Name, Role, Level, Personas, Vectors, Escalation)
# - 📄 Document RAG & ATS Parser (Resume/JD upload, 14 chunks vector index, ATS fit)
# ============================================================


# ============================================================
# DYNAMIC HTML GENERATOR MAPPED DIRECTLY FROM code.html
# ============================================================
def build_cockpit_html():
    """
    Reads code.html and dynamically injects the live session data,
    active question, candidate answer transcript with highlighted filler words,
    speech metrics, 6-D evaluation scores, SQLite table, and SVG graphics.
    """
    with open("code.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract dynamic session values
    candidate = html.escape(st.session_state.candidate_name)
    role = html.escape(st.session_state.target_role)
    persona = html.escape(st.session_state.personality)
    sess_id = html.escape(st.session_state.session_id)
    diff = html.escape(st.session_state.interview_state.get("difficulty", "Hard"))
    q_num = st.session_state.question_count
    total_q = st.session_state.total_questions

    # Inject Groq API key and session bootstrap
    api_k = get_api_key()
    bootstrap_js = f"""
    <script>
      window.GROQ_API_KEY = "{api_k}";
      window.SESSION_BOOTSTRAP = {{
        candidateName: "{candidate}",
        targetRole: "{role}",
        difficulty: "{diff}",
        questionNum: {q_num},
        totalQuestions: {total_q}
      }};
    </script>
    """
    html_content = html_content.replace("</head>", f"{bootstrap_js}</head>")

    # 1. Update Header and Cockpit Sidebar
    html_content = re.sub(r"#sess-8f3a", f"#{sess_id}", html_content)
    html_content = re.sub(r"Backend Software Eng", role, html_content)
    html_content = re.sub(r"FAANG-Style", persona, html_content)
    html_content = re.sub(r"Hard L5", f"{diff} L5", html_content)
    html_content = re.sub(r"Alex Chen", candidate, html_content)

    # 2. Update Active Question
    q_text = html.escape(st.session_state.current_question)
    # Target the prompt paragraph inside the technical escalation card
    html_content = re.sub(
        r"“You mentioned deploying Django applications with Docker.*?without baking them into image layers\.”",
        f"“{q_text}”",
        html_content,
        flags=re.DOTALL,
    )
    html_content = re.sub(r"Question 3 of 6", f"Question {q_num} of {total_q}", html_content)

    # 3. Update Transcript & Filler Highlighting
    raw_transcript = st.session_state.audio_transcript
    highlighted_tr = highlight_filler_words(raw_transcript)
    html_content = re.sub(
        r"So for our container pipeline, <span class=\"bg-amber-500/20 text-amber-300.*?not baked into layers\.",
        highlighted_tr,
        html_content,
        flags=re.DOTALL,
    )

    # 4. Update Voice Metrics
    vm = st.session_state.voice_metrics
    wpm_val = vm.get("speaking_pace_wpm", 142)
    fillers_val = vm.get("filler_words_count", 2)
    duration_str = format_duration(vm.get("duration_seconds", 84))
    clarity_val = vm.get("clarity_score", 9.2)

    html_content = re.sub(r">142 <span", f">{wpm_val} <span", html_content)
    html_content = re.sub(r">2 <span class=\"font-body-sm text-body-sm\">detected</span>", f">{fillers_val} <span class=\"font-body-sm text-body-sm\">detected</span>", html_content)
    html_content = re.sub(r">1m 24s<", f">{duration_str}<", html_content)
    html_content = re.sub(r">9\.2<span", f">{clarity_val}<span", html_content)

    # 5. Update Evaluation Scores (Tab 2) if available
    if st.session_state.feedback_history:
        latest = st.session_state.feedback_history[-1]
        fb = latest.get("feedback", {})
        t_sc = fb.get("technical_score", 8.5)
        c_sc = fb.get("completeness_score", 7.5)
        d_sc = fb.get("depth_score", 8.0)
        cm_sc = fb.get("communication_score", 9.0)
        p_sc = fb.get("problem_solving_score", 8.0)
        r_sc = fb.get("role_relevance_score", 9.5)

        avg_sc = round((t_sc + c_sc + d_sc + cm_sc + p_sc + r_sc) / 6.0, 1)

        html_content = re.sub(r"OVERALL SCORE: 8\.4 / 10", f"OVERALL SCORE: {avg_sc} / 10", html_content)
        html_content = re.sub(r">8\.5<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", f">{t_sc}<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", html_content)
        html_content = re.sub(r">7\.5<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", f">{c_sc}<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", html_content)
        html_content = re.sub(r">8\.0<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", f">{d_sc}<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", html_content)
        html_content = re.sub(r">9\.0<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", f">{cm_sc}<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", html_content)
        html_content = re.sub(r">9\.5<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", f">{r_sc}<span class=\"font-body-sm text-body-sm text-on-surface-variant\">/10</span>", html_content)

        if fb.get("model_answer"):
            m_ans = html.escape(fb["model_answer"])
            html_content = re.sub(r"“We architected a 2-stage build.*?rolling updates\.”", f"“{m_ans}”", html_content, flags=re.DOTALL)

    # 6. Update Code Evaluation Telemetry (Tab 5)
    code_ev = st.session_state.active_code_eval
    if code_ev:
        html_content = re.sub(r">9\.0 / 10<", f">{code_ev.get('correctness_score', 9.0)} / 10<", html_content)
        html_content = re.sub(r">O\(1\) Amortized<", f">{code_ev.get('time_complexity', 'O(1) Amortized')}<", html_content)
        html_content = re.sub(r">O\(N Clients\)<", f">{code_ev.get('space_complexity', 'O(N Clients)')}<", html_content)
        html_content = re.sub(r">8\.5 / 10<", f">{code_ev.get('code_quality_score', 8.5)} / 10<", html_content)
        if code_ev.get("follow_up_question"):
            fu_q = html.escape(code_ev["follow_up_question"])
            html_content = re.sub(r"“Can you optimize memory consumption.*?never return\?”", f"“{fu_q}”", html_content)

    # 7. Update SQLite Telemetry Table (Tab 6)
    db_rows = get_interview_history(limit=5)
    if db_rows:
        tbody_html = ""
        for r in db_rows:
            tbody_html += f"""
            <tr class="hover:bg-surface-container-high/40 transition-colors">
                <td class="p-space-sm font-mono text-secondary">#{r['session_id']}</td>
                <td class="p-space-sm font-medium">{r['target_role']}</td>
                <td class="p-space-sm">{r['difficulty']}</td>
                <td class="p-space-sm text-tertiary font-bold font-mono">{r['overall_score']}%</td>
                <td class="p-space-sm"><span class="px-2 py-0.5 rounded bg-tertiary/20 text-tertiary font-label-code-sm text-label-code-sm">Completed</span></td>
                <td class="p-space-sm font-mono text-on-surface-variant">{r['timestamp']}</td>
            </tr>
            """
        html_content = re.sub(
            r"<tbody class=\"divide-y divide-surface-container-highest/20 text-on-surface\">.*?</tbody>",
            f'<tbody class="divide-y divide-surface-container-highest/20 text-on-surface">{tbody_html}</tbody>',
            html_content,
            flags=re.DOTALL,
        )

    return html_content


# ============================================================
# RENDER FULL-SCREEN BREATHTAKING COCKPIT (MATCHING code.html)
# ============================================================
cockpit_html = build_cockpit_html()
components.html(cockpit_html, height=1380, scrolling=True)
