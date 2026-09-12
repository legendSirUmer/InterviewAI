"""
Intelligent Category-Aware Chunker.
Splits categorized sections into semantic chunks tagged with
category metadata (Projects, Skills, Experience, Education, Required Skills, Responsibilities).
"""

import re


def chunk_section_text(text, max_words=160, overlap=30):
    """
    Splits text into chunks respecting paragraph and sentence boundaries.
    Ensures chunks have rich context without losing semantic coherence.
    """
    if not text or not text.strip():
        return []

    # First attempt to split by paragraphs or bullet points
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.!?])\s*\n", text) if p.strip()]

    chunks = []
    current_words = []

    for para in paragraphs:
        para_words = para.split()
        if not para_words:
            continue

        if len(current_words) + len(para_words) <= max_words:
            current_words.extend(para_words)
        else:
            if current_words:
                chunks.append(" ".join(current_words))
                # retain overlap words
                current_words = current_words[-overlap:] if overlap < len(current_words) else []
            
            # If paragraph itself is larger than max_words, chunk it directly
            while len(para_words) > max_words:
                chunks.append(" ".join(para_words[:max_words]))
                para_words = para_words[max_words - overlap :]
            current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def build_categorized_chunks(sections_dict, doc_type="resume", doc_name=""):
    """
    Takes a dictionary of {category: section_text} and returns a list of
    structured chunk objects:
    {
        "id": int,
        "text": str,
        "category": str,
        "doc_type": str,
        "doc_name": str
    }
    """
    all_chunks = []
    chunk_counter = 1

    for category, content in sections_dict.items():
        text_chunks = chunk_section_text(content)
        for chunk in text_chunks:
            all_chunks.append(
                {
                    "id": chunk_counter,
                    "text": chunk,
                    "category": category,
                    "doc_type": doc_type,
                    "doc_name": doc_name,
                }
            )
            chunk_counter += 1

    return all_chunks
