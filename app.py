import os
import json
import html
import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLING
# ============================================================
st.markdown(
    """
<style>
.stApp {
    background: #0F172A;
}
.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
}
.hero {
    padding: 24px;
    border-radius: 18px;
    background: linear-gradient(135deg, #1E1B4B, #312E81);
    border: 1px solid #4F46E5;
    margin-bottom: 20px;
}
.agent-card {
    padding: 18px;
    border-radius: 14px;
    margin: 10px 0;
    border: 1px solid #334155;
    background: #1E293B;
}
.interviewer {
    border-left: 5px solid #6366F1;
}
.feedback {
    border-left: 5px solid #10B981;
}
.metric-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #38BDF8;
}
.metric-label {
    color: #94A3B8;
    font-size: 12px;
    text-transform: uppercase;
}
.small-muted {
    color: #94A3B8;
    font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================
DEFAULTS = {
    "interview_started": False,
    "messages": [],
    "feedback_history": [],
    "current_question": "",
    "question_count": 0,
    "rag_chunks": [],
    "document_name": "",
    "interview_start_time": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================
def get_api_key():
    """Use Streamlit secrets first, then environment variable."""
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        secret_key = ""

    return secret_key or os.getenv("GROQ_API_KEY", "")


def get_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return Groq(api_key=api_key)


def extract_document(uploaded_file):
    """Extract text from PDF or TXT."""
    if not uploaded_file:
        return ""

    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8", errors="ignore").strip()

    return ""


def chunk_text(text, chunk_size=1200, overlap=200):
    """Simple, dependency-light chunker suitable for Streamlit Cloud."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = max(end - overlap, start + 1)

    return chunks


def build_rag_index(text):
    chunks = chunk_text(text)
    if not chunks:
        return []

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(chunks)

    return [
        {
            "text": chunk,
            "vectorizer": vectorizer,
            "matrix": matrix,
            "chunks": chunks,
        }
    ]


def retrieve_context(query, rag_index, top_k=4):
    """
    Lightweight local RAG:
    TF-IDF retrieval avoids requiring a hosted vector DB.
    This is intentionally Streamlit-Cloud friendly.
    """
    if not rag_index:
        return ""

    item = rag_index[0]
    vectorizer = item["vectorizer"]
    matrix = item["matrix"]
    chunks = item["chunks"]

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix)[0]

    best_indices = scores.argsort()[::-1][:top_k]
    selected = [
        chunks[i]
        for i in best_indices
        if scores[i] > 0
    ]

    return "\n\n--- Retrieved Context ---\n\n".join(selected)


def call_llm(client, system_prompt, user_prompt, temperature=0.5, max_tokens=700):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def generate_json_feedback(client, question, answer, target_role, experience, focus):
    system_prompt = """
You are an elite interview evaluator.

Evaluate the candidate's answer fairly and specifically.

Return ONLY valid JSON using exactly this schema:
{
  "technical_score": 1,
  "clarity_score": 1,
  "structure_score": 1,
  "depth_score": 1,
  "role_relevance_score": 1,
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "follow_up_focus": "...",
  "model_answer": "..."
}

All scores must be integers from 1 to 10.
Do not invent facts about the candidate.
The model answer should be concise but strong.
"""

    prompt = f"""
Target role: {target_role}
Experience: {experience}
Focus: {focus}

Question:
{question}

Candidate answer:
{answer}
"""

    try:
        raw = call_llm(
            client,
            system_prompt,
            prompt,
            temperature=0.2,
            max_tokens=900,
        )
        data = json.loads(raw)

        required = [
            "technical_score",
            "clarity_score",
            "structure_score",
            "depth_score",
            "role_relevance_score",
            "strengths",
            "improvements",
            "follow_up_focus",
            "model_answer",
        ]

        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        return data

    except Exception as exc:
        return {
            "technical_score": 5,
            "clarity_score": 5,
            "structure_score": 5,
            "depth_score": 5,
            "role_relevance_score": 5,
            "strengths": ["The answer was attempted."],
            "improvements": [f"Evaluation fallback was used: {exc}"],
            "follow_up_focus": "Ask the candidate to explain their reasoning in more detail.",
            "model_answer": "A model answer could not be generated because the evaluation response was invalid.",
        }


def generate_question(
    client,
    target_role,
    experience,
    focus,
    difficulty,
    question_number,
    previous_question="",
    previous_answer="",
    previous_feedback=None,
    rag_context="",
):
    previous_feedback = previous_feedback or {}

    system_prompt = """
You are the Interviewer Agent in an adaptive mock interview.

Your job is ONLY to ask one interview question.
Never provide feedback, scoring, or the answer.

Rules:
- Ask exactly ONE question.
- Make it realistic for the target role.
- Adapt difficulty based on the candidate's previous performance.
- If the candidate mentioned a project, technology, trade-off, or decision,
  probe that exact topic when useful.
- Avoid repeating previous questions.
- Keep questions focused and interview-ready.
"""

    prompt = f"""
Target role: {target_role}
Experience level: {experience}
Interview focus: {focus}
Difficulty: {difficulty}
Question number: {question_number}

Relevant resume/JD context:
{rag_context or "No document context available."}

Previous question:
{previous_question or "None"}

Previous candidate answer:
{previous_answer or "None"}

Previous evaluation:
{json.dumps(previous_feedback, ensure_ascii=False) if previous_feedback else "None"}

Generate the next question now.
"""

    return call_llm(
        client,
        system_prompt,
        prompt,
        temperature=0.65,
        max_tokens=300,
    )


def calculate_overall_score(history):
    if not history:
        return 0

    dimensions = [
        "technical_score",
        "clarity_score",
        "structure_score",
        "depth_score",
        "role_relevance_score",
    ]

    values = []
    for item in history:
        fb = item["feedback"]
        values.extend(
            float(fb.get(d, 0))
            for d in dimensions
            if isinstance(fb.get(d, 0), (int, float))
        )

    return round(sum(values) / len(values), 1) if values else 0


def recommendation(score):
    if score >= 8.5:
        return "Excellent — strong interview readiness."
    if score >= 7:
        return "Good — interview ready with some targeted improvement."
    if score >= 5.5:
        return "Developing — practice the highlighted weak areas."
    return "Needs improvement — focus on fundamentals and structured answers."


def build_report(target_role, experience, focus, history):
    score = calculate_overall_score(history)

    lines = [
        "# AI Interview Coaching Report",
        "",
        f"**Target Role:** {target_role}",
        f"**Experience:** {experience}",
        f"**Focus:** {focus}",
        f"**Overall Score:** {score}/10",
        f"**Recommendation:** {recommendation(score)}",
        "",
        "---",
        "",
    ]

    for i, item in enumerate(history, start=1):
        fb = item["feedback"]
        lines.extend(
            [
                f"## Question {i}",
                "",
                f"**Question:** {item['question']}",
                "",
                f"**Your Answer:** {item['answer']}",
                "",
                f"- Technical: {fb.get('technical_score', 0)}/10",
                f"- Clarity: {fb.get('clarity_score', 0)}/10",
                f"- Structure: {fb.get('structure_score', 0)}/10",
                f"- Depth: {fb.get('depth_score', 0)}/10",
                f"- Role Relevance: {fb.get('role_relevance_score', 0)}/10",
                "",
                "**Strengths**",
            ]
        )

        for strength in fb.get("strengths", []):
            lines.append(f"- {strength}")

        lines.extend(["", "**Improvements**"])

        for improvement in fb.get("improvements", []):
            lines.append(f"- {improvement}")

        lines.extend(
            [
                "",
                "**Model Answer**",
                fb.get("model_answer", ""),
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🎯 Interview Coach")
    st.caption("Adaptive AI mock interview platform")

    st.markdown("---")
    st.subheader("📋 Interview Setup")

    target_role = st.text_input(
        "Target Role",
        value="Data Scientist",
        placeholder="Backend Engineer, AI Engineer...",
    )

    experience_level = st.selectbox(
        "Experience Level",
        [
            "Junior (0–2 yrs)",
            "Mid-Level (3–5 yrs)",
            "Senior (5+ yrs)",
            "Lead / Management",
        ],
    )

    interview_type = st.selectbox(
        "Focus Area",
        [
            "Technical & System Design",
            "Behavioral (STAR Method)",
            "Mixed Technical & Behavioral",
            "Data / SQL",
            "AI / Machine Learning",
            "Software Engineering",
        ],
    )

    difficulty = st.select_slider(
        "Difficulty",
        options=["Easy", "Medium", "Hard", "Expert"],
        value="Medium",
    )

    question_limit = st.slider(
        "Questions",
        min_value=3,
        max_value=15,
        value=8,
    )

    st.markdown("---")
    st.subheader("📄 Resume / JD RAG")

    uploaded_file = st.file_uploader(
        "Upload Resume or Job Description",
        type=["pdf", "txt"],
    )

    if uploaded_file:
        if (
            st.session_state.document_name != uploaded_file.name
            or not st.session_state.rag_chunks
        ):
            document_text = extract_document(uploaded_file)
            st.session_state.rag_chunks = build_rag_index(document_text)
            st.session_state.document_name = uploaded_file.name

        if st.session_state.rag_chunks:
            st.success(
                f"RAG ready: {uploaded_file.name}"
            )
        else:
            st.warning("Could not extract usable text.")

    if st.session_state.document_name:
        st.caption(
            f"Loaded document: {st.session_state.document_name}"
        )

    st.markdown("---")

    api_key = get_api_key()

    if api_key:
        st.success("Groq API configured")
    else:
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Optional if GROQ_API_KEY is configured in Streamlit Secrets.",
        )
        if groq_api_key:
            # Keep the key only for this running session.
            os.environ["GROQ_API_KEY"] = groq_api_key
            st.success("API key loaded for this session.")

    if st.button(
        "🚀 Start New Interview",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.interview_started = True
        st.session_state.messages = []
        st.session_state.feedback_history = []
        st.session_state.current_question = ""
        st.session_state.question_count = 0
        st.session_state.interview_start_time = datetime.now()
        st.rerun()

    if st.session_state.interview_started:
        if st.button("🔄 Reset Interview", use_container_width=True):
            for key, value in DEFAULTS.items():
                st.session_state[key] = value
            st.rerun()


# ============================================================
# HEADER
# ============================================================
st.markdown(
    """
<div class="hero">
    <h1>🎯 AI Interview Prep Coach</h1>
    <p>
        Adaptive interviewer + AI evaluator + lightweight RAG +
        performance analytics
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# LANDING PAGE
# ============================================================
if not st.session_state.interview_started:
    st.info(
        "Configure your interview in the sidebar and click "
        "**Start New Interview**."
    )

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("🤖", "Adaptive Interviewer", "Dynamic follow-up questions"),
        ("🧠", "AI Evaluator", "Five-dimensional scoring"),
        ("📚", "RAG Context", "Resume/JD-aware questions"),
        ("📊", "Analytics", "Track performance over time"),
    ]

    for col, (icon, title, text) in zip(
        [c1, c2, c3, c4], cards
    ):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div style="font-size:30px">{icon}</div>
                    <b>{title}</b>
                    <div class="small-muted">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("How the enhanced system works")

    st.markdown(
        """
        1. **Upload a resume or job description** (optional).
        2. The app extracts and chunks the document.
        3. Relevant chunks are retrieved for each question.
        4. The **Interviewer Agent** asks one adaptive question.
        5. The **Evaluator Agent** scores the answer.
        6. The next question adapts to the candidate's performance.
        7. Analytics identify strengths and recurring weaknesses.
        8. A complete Markdown report can be exported.
        """
    )

    st.stop()


# ============================================================
# CLIENT CHECK
# ============================================================
client = get_client()

if not client:
    st.error(
        "🔑 Groq API key is required. Add GROQ_API_KEY to "
        "Streamlit Secrets or enter it in the sidebar."
    )
    st.stop()


# ============================================================
# INITIAL QUESTION
# ============================================================
if not st.session_state.current_question:
    rag_context = retrieve_context(
        f"{target_role} {interview_type}",
        st.session_state.rag_chunks,
        top_k=4,
    )

    with st.spinner("🤖 Interviewer Agent is preparing your first question..."):
        q = generate_question(
            client,
            target_role,
            experience_level,
            interview_type,
            difficulty,
            1,
            rag_context=rag_context,
        )

    st.session_state.current_question = q
    st.session_state.question_count = 1
    st.session_state.messages.append(
        {"role": "assistant", "content": q}
    )


# ============================================================
# TABS
# ============================================================
tab_interview, tab_analytics, tab_report = st.tabs(
    [
        "💬 Live Interview",
        "📊 Analytics",
        "📄 Final Report",
    ]
)


# ============================================================
# LIVE INTERVIEW
# ============================================================
with tab_interview:
    completed = len(st.session_state.feedback_history)

    progress = min(completed / question_limit, 1.0)

    st.progress(
        progress,
        text=f"Progress: {completed}/{question_limit} questions completed",
    )

    st.markdown(
        f"""
        <div class="agent-card interviewer">
            <div class="small-muted">
                🎙️ INTERVIEWER AGENT · QUESTION #{st.session_state.question_count}
            </div>
            <h3>{html.escape(st.session_state.current_question)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if completed >= question_limit:
        st.success(
            "🎉 Interview complete! Open the Analytics or Final Report tab."
        )
    else:
        with st.form(
            "answer_form",
            clear_on_submit=True,
        ):
            answer = st.text_area(
                "Your Answer",
                height=180,
                placeholder=(
                    "Answer as if you were in a real interview. "
                    "Explain your reasoning and give concrete examples."
                ),
            )

            submit = st.form_submit_button(
                "Submit Answer & Evaluate 🚀",
                use_container_width=True,
                type="primary",
            )

        if submit:
            if not answer.strip():
                st.warning("Please enter an answer first.")
            else:
                question = st.session_state.current_question

                with st.spinner("🧠 Evaluation Agent is analyzing your answer..."):
                    feedback = generate_json_feedback(
                        client,
                        question,
                        answer,
                        target_role,
                        experience_level,
                        interview_type,
                    )

                st.session_state.messages.append(
                    {"role": "user", "content": answer}
                )

                st.session_state.feedback_history.append(
                    {
                        "question": question,
                        "answer": answer,
                        "feedback": feedback,
                    }
                )

                if len(st.session_state.feedback_history) < question_limit:
                    previous_context = retrieve_context(
                        question + " " + answer,
                        st.session_state.rag_chunks,
                        top_k=4,
                    )

                    with st.spinner(
                        "🤖 Interviewer Agent is adapting the next question..."
                    ):
                        next_question = generate_question(
                            client,
                            target_role,
                            experience_level,
                            interview_type,
                            difficulty,
                            st.session_state.question_count + 1,
                            previous_question=question,
                            previous_answer=answer,
                            previous_feedback=feedback,
                            rag_context=previous_context,
                        )

                    st.session_state.current_question = next_question
                    st.session_state.question_count += 1
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": next_question,
                        }
                    )

                else:
                    st.session_state.current_question = ""

                st.rerun()

    # Feedback history
    if st.session_state.feedback_history:
        st.markdown("---")
        st.subheader("📝 Evaluation History")

        for idx, item in enumerate(
            reversed(st.session_state.feedback_history),
            start=1,
        ):
            fb = item["feedback"]

            with st.expander(
                f"Q{len(st.session_state.feedback_history) - idx + 1}: "
                f"{item['question'][:90]}",
                expanded=(idx == 1),
            ):
                s1, s2, s3, s4, s5 = st.columns(5)

                s1.metric("Technical", f"{fb.get('technical_score', 0)}/10")
                s2.metric("Clarity", f"{fb.get('clarity_score', 0)}/10")
                s3.metric("Structure", f"{fb.get('structure_score', 0)}/10")
                s4.metric("Depth", f"{fb.get('depth_score', 0)}/10")
                s5.metric(
                    "Relevance",
                    f"{fb.get('role_relevance_score', 0)}/10",
                )

                st.markdown("**💪 Strengths**")
                for strength in fb.get("strengths", []):
                    st.write(f"• {strength}")

                st.markdown("**🔧 Improvements**")
                for improvement in fb.get("improvements", []):
                    st.write(f"• {improvement}")

                st.markdown("**🎯 Suggested Follow-up Focus**")
                st.write(fb.get("follow_up_focus", ""))

                st.markdown(
                    '<div class="agent-card feedback">'
                    "<b>✨ Model Answer</b><br>"
                    + html.escape(fb.get("model_answer", ""))
                    + "</div>",
                    unsafe_allow_html=True,
                )


# ============================================================
# ANALYTICS
# ============================================================
with tab_analytics:
    st.subheader("📊 Performance Dashboard")

    if not st.session_state.feedback_history:
        st.info("Complete at least one question to unlock analytics.")
    else:
        history = st.session_state.feedback_history
        overall = calculate_overall_score(history)

        df = pd.DataFrame(
            [
                {
                    "Question": f"Q{i}",
                    "Technical": x["feedback"].get("technical_score", 0),
                    "Clarity": x["feedback"].get("clarity_score", 0),
                    "Structure": x["feedback"].get("structure_score", 0),
                    "Depth": x["feedback"].get("depth_score", 0),
                    "Role Relevance": x["feedback"].get(
                        "role_relevance_score", 0
                    ),
                }
                for i, x in enumerate(history, start=1)
            ]
        )

        a, b, c, d = st.columns(4)

        a.metric("Overall Score", f"{overall}/10")
        b.metric("Questions", len(history))
        b.metric if False else None
        c.metric(
            "Best Dimension",
            df.drop(columns=["Question"]).mean().idxmax(),
        )
        d.metric(
            "Recommendation",
            "Excellent" if overall >= 8.5
            else "Good" if overall >= 7
            else "Developing" if overall >= 5.5
            else "Needs Work",
        )

        st.markdown(
            f"### {recommendation(overall)}"
        )

        st.markdown("---")

        chart1, chart2 = st.columns(2)

        with chart1:
            fig = px.line(
                df,
                x="Question",
                y=[
                    "Technical",
                    "Clarity",
                    "Structure",
                    "Depth",
                    "Role Relevance",
                ],
                markers=True,
                title="Performance Across Questions",
            )
            fig.update_layout(
                yaxis_range=[0, 10],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart2:
            means = df.drop(columns=["Question"]).mean()

            radar = go.Figure(
                data=[
                    go.Scatterpolar(
                        r=means.values,
                        theta=means.index,
                        fill="toself",
                    )
                ]
            )

            radar.update_layout(
                title="Competency Radar",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10],
                    )
                ),
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                radar,
                use_container_width=True,
            )

        st.subheader("📌 Dimension Averages")

        avg_df = (
            df.drop(columns=["Question"])
            .mean()
            .round(2)
            .sort_values(ascending=False)
            .rename("Average")
            .to_frame()
        )

        st.dataframe(
            avg_df,
            use_container_width=True,
        )

        st.subheader("🔍 Areas to Practice")

        weakest = avg_df.sort_values("Average").head(3)

        for dimension, row in weakest.iterrows():
            st.warning(
                f"**{dimension}** — average {row['Average']}/10. "
                "Prioritize this area in your next practice session."
            )


# ============================================================
# REPORT
# ============================================================
with tab_report:
    st.subheader("📄 Final Interview Report")

    if not st.session_state.feedback_history:
        st.info("Complete interview questions to generate your report.")
    else:
        score = calculate_overall_score(
            st.session_state.feedback_history
        )

        st.metric("Final Interview Score", f"{score}/10")
        st.write(recommendation(score))

        report = build_report(
            target_role,
            experience_level,
            interview_type,
            st.session_state.feedback_history,
        )

        st.download_button(
            "💾 Download Markdown Report",
            data=report,
            file_name=(
                f"interview_{target_role.replace(' ', '_').lower()}.md"
            ),
            mime="text/markdown",
            use_container_width=True,
        )

        with st.expander("Preview Report"):
            st.markdown(report)
