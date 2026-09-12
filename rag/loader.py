"""
Document Loader and Intelligent Section Parser.
Extracts raw text from PDF and TXT files, detects whether the document
is a Resume or Job Description, and partitions it into structured categories:
- Resume: Projects, Skills, Experience, Education
- Job Description: Required Skills, Responsibilities, Qualifications
"""

import re
from io import BytesIO
from pypdf import PdfReader


RESUME_HEADERS = {
    "projects": [r"projects?", r"key projects", r"technical projects", r"portfolio", r"personal projects"],
    "skills": [r"skills?", r"technical skills", r"competencies", r"core skills", r"technologies", r"tools & technologies"],
    "experience": [r"experience", r"work experience", r"professional experience", r"employment history", r"career summary"],
    "education": [r"education", r"academic background", r"qualifications", r"degrees", r"certifications"],
}

JD_HEADERS = {
    "required_skills": [r"required skills", r"requirements", r"must have", r"technical requirements", r"skills required", r"what you need"],
    "responsibilities": [r"responsibilities", r"what you'?ll do", r"key duties", r"job description", r"day-to-day", r"scope of work"],
    "qualifications": [r"qualifications", r"preferred qualifications", r"nice to have", r"desired skills", r"minimum qualifications"],
}


def extract_raw_text(uploaded_file):
    """Extracts raw text from an uploaded Streamlit file or file-like object."""
    if not uploaded_file:
        return ""

    file_name = getattr(uploaded_file, "name", "").lower()

    try:
        if file_name.endswith(".pdf") or getattr(uploaded_file, "type", "") == "application/pdf":
            reader = PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages).strip()

        if file_name.endswith(".txt") or getattr(uploaded_file, "type", "") == "text/plain":
            if hasattr(uploaded_file, "read"):
                raw = uploaded_file.read()
                if isinstance(raw, bytes):
                    return raw.decode("utf-8", errors="ignore").strip()
                return str(raw).strip()

        # Fallback if raw bytes passed
        if isinstance(uploaded_file, bytes):
            return uploaded_file.decode("utf-8", errors="ignore").strip()

    except Exception as exc:
        print(f"Document extraction error: {exc}")
        return ""

    return ""


def detect_document_type(text):
    """Infers whether the text is a Resume or a Job Description."""
    lower = text.lower()
    resume_score = sum(len(re.findall(pat, lower)) for patterns in RESUME_HEADERS.values() for pat in patterns)
    jd_score = sum(len(re.findall(pat, lower)) for patterns in JD_HEADERS.values() for pat in patterns)

    if jd_score > resume_score and ("responsibilities" in lower or "what you'll do" in lower or "requirements" in lower):
        return "job_description"
    return "resume"


def parse_categorized_sections(text, doc_type=None):
    """
    Parses document text into categorized sections.
    Returns a dict mapping category name to section text.
    """
    if not text or not text.strip():
        return {}

    if not doc_type:
        doc_type = detect_document_type(text)

    header_rules = JD_HEADERS if doc_type == "job_description" else RESUME_HEADERS

    # Compile regex pattern to match any known section headers at start of lines
    all_header_patterns = []
    category_by_pattern = {}

    for cat, patterns in header_rules.items():
        for pat in patterns:
            # Matches header line e.g., "## EXPERIENCE", "Projects:", "SKILLS"
            regex_str = rf"(?i)(?:^|\n)[ \t]*(?:#+\s*|\*+\s*)?({pat})[ \t]*[:\-\—]?[ \t]*(?:\r?\n|$)"
            all_header_patterns.append(regex_str)
            category_by_pattern[pat] = cat

    # Find all header matches with their positions
    matches = []
    for pat_str in all_header_patterns:
        for m in re.finditer(pat_str, text):
            matched_header = m.group(1).lower().strip()
            # Map back to category
            assigned_cat = "general"
            for rule_pat, cat_name in category_by_pattern.items():
                if re.match(rf"^{rule_pat}$", matched_header, re.IGNORECASE):
                    assigned_cat = cat_name
                    break
            matches.append((m.start(), m.end(), assigned_cat, matched_header))

    # Sort matches by start position
    matches.sort(key=lambda x: x[0])

    sections = {}
    if not matches:
        # Fallback: assign entire content to main category
        primary_cat = "responsibilities" if doc_type == "job_description" else "experience"
        sections[primary_cat] = text.strip()
        return sections

    # First chunk before any header (e.g. header/contact info/summary)
    intro = text[: matches[0][0]].strip()
    if intro:
        sections["overview"] = intro

    # Extract text between consecutive matches
    for i in range(len(matches)):
        start_pos = matches[i][1]
        end_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        cat = matches[i][2]
        chunk_content = text[start_pos:end_pos].strip()

        if chunk_content:
            if cat in sections:
                sections[cat] += "\n\n" + chunk_content
            else:
                sections[cat] = chunk_content

    return sections
