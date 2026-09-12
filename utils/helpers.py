"""
Helper utilities for InterviewAI.
Includes speech/voice analysis (WPM, filler words, clarity scoring),
filler word highlighting/removal, styling helpers, and the complete design
tokens matching code.html (Tailwind CSS, Outfit/Inter/JetBrains Mono fonts, Material Symbols).
"""

import re
import html


FILLER_WORDS = [
    r"\bum\b",
    r"\buh\b",
    r"\ber\b",
    r"\bah\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bi mean\b",
    r"\bso yeah\b",
]


def analyze_voice_metrics(transcript_text, duration_seconds=None):
    """
    Analyzes an audio transcription for speech metrics:
    - Speaking pace in Words Per Minute (WPM)
    - Filler word count and detected occurrences
    - Answer duration
    - Speech clarity indicator (1-10 scale)
    """
    if not transcript_text or not transcript_text.strip():
        return {
            "word_count": 0,
            "speaking_pace_wpm": 0,
            "filler_words_count": 0,
            "filler_words_found": [],
            "duration_seconds": 0,
            "clarity_score": 0.0,
            "pace_rating": "N/A",
        }

    words = re.findall(r"\b\w+\b", transcript_text.lower())
    word_count = len(words)

    # Detect filler words
    found_fillers = []
    lower_text = transcript_text.lower()
    for pattern in FILLER_WORDS:
        matches = re.findall(pattern, lower_text)
        if matches:
            found_fillers.extend(matches)

    filler_count = len(found_fillers)

    # Duration and WPM calculation
    if duration_seconds and duration_seconds > 0:
        actual_duration = float(duration_seconds)
    else:
        # Realistic fallback estimation: average spoken English is ~140 WPM (2.33 words/sec)
        actual_duration = max(word_count / 2.33, 4.0)

    minutes = actual_duration / 60.0
    wpm = int(round(word_count / minutes)) if minutes > 0 else 0

    # Rate speaking pace
    if 120 <= wpm <= 160:
        pace_rating = "Optimal (120-160 WPM) 🟢"
    elif wpm < 120:
        pace_rating = "Deliberate / Slow (<120 WPM) 🟡"
    else:
        pace_rating = "Fast / Rushed (>160 WPM) 🟡"

    # Compute speech clarity score (1 to 10)
    filler_ratio = (filler_count / word_count) if word_count > 0 else 0
    base_clarity = 9.5

    if filler_ratio > 0.08:
        base_clarity -= 3.0
    elif filler_ratio > 0.04:
        base_clarity -= 1.8
    elif filler_ratio > 0.01:
        base_clarity -= 0.8

    if wpm > 185 or (wpm < 90 and word_count > 15):
        base_clarity -= 1.0

    clarity_score = round(max(min(base_clarity, 10.0), 3.0), 1)

    return {
        "word_count": word_count,
        "speaking_pace_wpm": wpm,
        "filler_words_count": filler_count,
        "filler_words_found": found_fillers[:10],
        "duration_seconds": round(actual_duration, 1),
        "clarity_score": clarity_score,
        "pace_rating": pace_rating,
    }


def highlight_filler_words(text):
    """
    Wraps detected filler words in amber highlighting tags
    matching code.html style.
    """
    if not text:
        return ""
    result = html.escape(text)
    for pattern in FILLER_WORDS:
        # Match case-insensitively and wrap
        result = re.sub(
            pattern,
            lambda m: f'<span class="bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-medium">{m.group(0)}</span>',
            result,
            flags=re.IGNORECASE,
        )
    return result


def remove_filler_words(text):
    """Cleanly strips common filler words from text."""
    if not text:
        return ""
    clean = text
    for pattern in FILLER_WORDS:
        clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)
    # Clean up double spaces
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def format_duration(seconds):
    """Formats seconds into human-readable duration (e.g. 1m 24s)."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs:02d}s"


def get_score_color(score_pct):
    """Returns color hex based on percentage score (0-100)."""
    if score_pct >= 80:
        return "#4edea3"  # Tertiary emerald from code.html
    if score_pct >= 65:
        return "#7bd0ff"  # Secondary azure
    return "#ffb4ab"      # Error coral


# ============================================================
# COMPLETE THEME & ASSET INJECTION FROM code.html
# ============================================================
CODE_HTML_THEME_CSS = """
<!-- Google Fonts from code.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&family=Outfit:wght@600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<!-- Tailwind CDN with exact color configuration from code.html -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "on-surface-variant": "#c7c4d7",
        "on-primary": "#1000a9",
        "secondary-container": "#00a6e0",
        "on-error-container": "#ffdad6",
        "tertiary": "#4edea3",
        "tertiary-fixed": "#6ffbbe",
        "surface-variant": "#313540",
        "on-primary-container": "#0d0096",
        "inverse-surface": "#dfe2f1",
        "inverse-on-surface": "#2c303b",
        "on-secondary-container": "#00374d",
        "on-primary-fixed-variant": "#2f2ebe",
        "on-secondary": "#00354a",
        "on-primary-fixed": "#07006c",
        "secondary-fixed": "#c4e7ff",
        "error": "#ffb4ab",
        "surface-tint": "#c0c1ff",
        "on-secondary-fixed-variant": "#004c69",
        "background": "#0f131d",
        "surface-container-lowest": "#0a0e18",
        "on-tertiary-container": "#000703",
        "inverse-primary": "#494bd6",
        "error-container": "#93000a",
        "tertiary-fixed-dim": "#4edea3",
        "on-tertiary-fixed-variant": "#005236",
        "surface": "#0f131d",
        "on-surface": "#dfe2f1",
        "secondary": "#7bd0ff",
        "primary": "#c0c1ff",
        "on-tertiary-fixed": "#002113",
        "surface-container-highest": "#313540",
        "outline-variant": "#464554",
        "on-secondary-fixed": "#001e2c",
        "surface-dim": "#0f131d",
        "surface-container": "#1c1f2a",
        "surface-container-low": "#171b26",
        "secondary-fixed-dim": "#7bd0ff",
        "on-error": "#690005",
        "primary-fixed": "#e1e0ff",
        "primary-fixed-dim": "#c0c1ff",
        "outline": "#908fa0",
        "surface-bright": "#353944",
        "surface-container-high": "#262a35",
        "on-background": "#dfe2f1",
        "tertiary-container": "#00885d",
        "primary-container": "#8083ff",
        "on-tertiary": "#003824"
      },
      fontFamily: {
        "headline-lg": ["Outfit", "sans-serif"],
        "display-lg": ["Outfit", "sans-serif"],
        "label-code-sm": ["JetBrains Mono", "monospace"],
        "headline-md": ["Outfit", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "display-sm": ["Outfit", "sans-serif"],
        "body-sm": ["Inter", "sans-serif"],
        "label-code-md": ["JetBrains Mono", "monospace"],
        "headline-sm": ["Outfit", "sans-serif"],
        "body-md": ["Inter", "sans-serif"]
      }
    }
  }
};
</script>

<style>
/* Base Streamlit Overrides to match code.html */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f131d !important;
    color: #dfe2f1 !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1480px !important;
    padding-top: 1rem !important;
    padding-bottom: 2.5rem !important;
}

/* Sidebar styling to match aside from code.html */
[data-testid="stSidebar"] {
    background-color: #171b26 !important;
    border-right: 1px solid #313540 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: #dfe2f1 !important;
}

/* Custom Streamlit Tabs to match code.html button tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: rgba(23, 27, 38, 0.9) !important;
    backdrop-filter: blur(16px) !important;
    padding: 6px !important;
    border-radius: 16px !important;
    border: 1px solid #313540 !important;
    margin-bottom: 24px !important;
}
.stTabs [data-baseweb="tab"] {
    height: 44px !important;
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #c7c4d7 !important;
    border: none !important;
    padding: 0 16px !important;
    background-color: transparent !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #dfe2f1 !important;
    background-color: #262a35 !important;
}
.stTabs [aria-selected="true"] {
    background: #8083ff !important;
    color: #0d0096 !important;
    box-shadow: 0 0 20px rgba(128, 131, 255, 0.35) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Streamlit Buttons to match code.html gradient & surface buttons */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    border: 1px solid #313540 !important;
    background-color: #1c1f2a !important;
    color: #dfe2f1 !important;
}
.stButton > button:hover {
    background-color: #262a35 !important;
    border-color: #7bd0ff !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(to right, #8083ff, #c0c1ff, #7bd0ff) !important;
    color: #1000a9 !important;
    border: none !important;
    box-shadow: 0 0 24px rgba(128, 131, 255, 0.4) !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.1) !important;
    box-shadow: 0 0 32px rgba(128, 131, 255, 0.6) !important;
}

/* Text Areas and Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #0a0e18 !important;
    border: 1px solid #313540 !important;
    border-radius: 12px !important;
    color: #dfe2f1 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #8083ff !important;
    box-shadow: 0 0 0 1px #8083ff !important;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: #171b26 !important;
    border: 1px solid #313540 !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* Material Symbols alignment helper */
.material-symbols-outlined {
    vertical-align: middle;
    line-height: 1;
}

/* Waveform pulse animation */
@keyframes wavePulse {
    0%, 100% { transform: scaleY(0.4); }
    50% { transform: scaleY(1.0); }
}
.wave-bar {
    transform-origin: bottom;
    animation: wavePulse 1.2s infinite ease-in-out;
}
</style>
"""

APP_CUSTOM_CSS = CODE_HTML_THEME_CSS
