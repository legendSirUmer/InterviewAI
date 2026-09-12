# 🎯 InterviewAI — Next-Generation Intelligent Mock Interview Platform

An agentic, multi-modal AI interview coaching platform built with **Streamlit**, **Groq Llama-3.3-70B / Whisper**, and **SQLite**. Designed for high-calibration technical and behavioral interview preparation.

---

## 🌟 Core Innovations & Architecture

```
InterviewAI/
├── app.py                      # Main Streamlit UI & Tab Orchestration
├── agents/                     # Multi-Agent Coordination
│   ├── interviewer.py          # 6 Personalities, Dynamic Context Questioning
│   ├── evaluator.py            # 6-Dimensional Rubric & Big-O Code Evaluator
│   ├── manager.py              # Adaptive State Machine (Difficulty Scaling)
│   └── feedback.py             # Side-by-Side Comparative Feedback UI
├── rag/                        # Intelligent Categorized RAG
│   ├── loader.py               # Section-Aware Parser (Projects, Skills, Exp)
│   ├── chunker.py              # Semantic Categorized Chunker
│   └── retriever.py            # TF-IDF Category Vector Index
├── services/                   # Core AI & Business Services
│   ├── groq_service.py         # Groq LLM Client & Whisper Transcription
│   ├── resume_service.py       # JD Planner & Resume ATS Gap Analyzer
│   └── report_service.py       # Comprehensive Markdown & HTML Reports
├── database/                   # Zero-Config SQLite Persistence
│   └── db.py                   # Historical Sessions & Performance Tracking
└── utils/                      # Utilities & Problem Bank
    ├── helpers.py              # Speech Metrics (WPM, Fillers, Clarity)
    └── coding_problems.py      # Curated Coding Challenges
```

---

## 🚀 Key Features (The 12 Pillars)

### 1. Intelligent Categorized RAG
Unlike generic chunking, documents are automatically parsed into distinct categories:
- **Resume**: *Projects*, *Skills*, *Experience*, *Education*
- **Job Description**: *Required Skills*, *Responsibilities*, *Qualifications*

The Interviewer Agent retrieves from appropriate categories to ask razor-sharp questions:
> *"You mentioned deploying Django applications with Docker. Walk me through how you containerized the application and handled production configuration."*

### 2. Job Description → Custom Curriculum
Upload any target Job Description to automatically extract:
- Weighted skill distribution bars (e.g. Python 20%, Django 20%, REST APIs 15%, Databases 15%, System Design 15%, Behavioral 15%).
- A tailored 4-part interview plan with target competencies.

### 3. Stateful Adaptive Interview Agent
Maintains real-time state (`difficulty`, `skills_tested`, `weak_areas`, `strong_areas`, `recent_scores`):
- **High performance (>=8.0/10)**: Escalates difficulty (Easy → Medium → Hard → Expert).
- **Gaps detected (<6.0/10)**: Flags weak areas and triggers adaptive follow-up drill-downs to test the concept from a different angle.

### 4. 6-Dimensional Evaluation & Comparative Review
Scores every answer across 6 dimensions:
1. **Technical Accuracy** (1–10)
2. **Completeness** (1–10)
3. **Depth & Nuance** (1–10)
4. **Communication & Conciseness** (1–10)
5. **Problem Solving & Reasoning** (1–10)
6. **Role Relevance** (1–10)

Presents an interactive 4-way comparison:
`YOUR ANSWER` &bull; `AI EVALUATION` &bull; `IDEAL MODEL ANSWER` &bull; `WHAT WAS MISSED`

### 5. Resume & ATS Gap Analyzer
- Audits resumes across Technical Skills, Projects, Impact, ATS Readiness, and Role Alignment.
- Converts weak bullet points into high-impact Google XYZ / STAR rewrites.
- Computes compatibility match % with strong matches (✓) vs missing gaps (⚠).

### 6. Voice Interview Mode with Speech Analytics
Speak your answers naturally using live microphone or uploaded audio. Powered by Groq Whisper and real-time speech analytics:
- **Speaking Pace**: Words Per Minute (WPM) gauge (120–160 WPM optimal).
- **Filler Word Counter**: Detects `um`, `uh`, `like`, `you know`, `actually`, etc.
- **Answer Duration & Clarity Score** (1–10).

### 7. Coding Interview Mode
Practice algorithmic coding directly in the browser:
- Real-world challenges (Two Sum, LRU Cache, Sliding Window Rate Limiter, Group Anagrams).
- Evaluates **Correctness**, **Big-O Time Complexity**, **Big-O Space Complexity**, **Code Quality**, and edge case coverage.
- Auto-generates follow-up optimization challenges.

### 8. Executive Analytics Dashboard
- 6-Dimensional competency radar chart.
- Question-by-question trajectory line chart.
- Actionable preparation matrix: 🔥 **High Priority**, ⚠ **Medium Priority**, ✓ **Strong / Interview Ready**.

### 9. SQLite Persistent Interview History
- Sessions, transcripts, scores, and speech metrics are stored locally in SQLite (`interview_history.db`).
- Visualizes performance progression over time (e.g. `68% → 71% → 76% → 82%`).

### 10. AI Interview Performance Reports
- Personalized 3–5 hour study roadmaps.
- One-click downloads in both **Markdown (`.md`)** and **Printable Styled HTML (`.html`)**.

### 11. 6 Selectable Interviewer Personalities
- **Friendly & Encouraging** (Warm, supportive, guided)
- **Professional & Structured** (Senior hiring manager calibration)
- **Strict & Demanding** (Production stress-testing, skeptical of buzzwords)
- **FAANG-Style** (Distributed systems, Big-O trade-offs, high-concurrency)
- **Startup CTO** (Pragmatic execution, velocity vs tech debt, scrappiness)
- **HR Manager** (Culture fit, team collaboration, conflict resolution)

### 12. 6 Selectable Interview Types
- Technical & System Design
- Behavioral (STAR Method)
- HR & Culture Fit
- System Design
- Coding & Algorithms
- Mixed Technical & Behavioral

---

## 🛠️ Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/legendSirUmer/InterviewAI.git
   cd InterviewAI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your Groq API Key:**
   - Either set an environment variable:
     ```bash
     export GROQ_API_KEY="your_api_key_here"  # Linux/macOS
     set GROQ_API_KEY="your_api_key_here"     # Windows CMD
     $env:GROQ_API_KEY="your_api_key_here"    # Windows PowerShell
     ```
   - Or enter it directly in the app sidebar when launched.

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Streamlit Cloud Deployment

1. Push your repository to GitHub.
2. Connect the repository in [Streamlit Cloud](https://share.streamlit.io).
3. Under **App Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Deploy! The lightweight TF-IDF and SQLite architecture ensures zero external database overhead.
