# AI Interview Prep Coach

An adaptive AI mock-interview application built with Streamlit and Groq.

## Features

- Adaptive Interviewer Agent
- AI Evaluation Agent
- Resume / Job Description RAG
- PDF and TXT upload
- Technical, clarity, structure, depth and role-relevance scoring
- Adaptive follow-up questions
- Performance analytics
- Competency radar
- Final Markdown report
- Streamlit Cloud friendly architecture

## Local setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Add this secret:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Do not commit your API key to GitHub.

## RAG

The app uses lightweight TF-IDF retrieval. This keeps deployment simple because it does not require a separate hosted vector database.
