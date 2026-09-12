"""
Intelligent Categorized Retriever.
Builds TF-IDF indices for categorized chunks and provides category-aware
retrieval (e.g., retrieving only from 'Projects' or 'Required Skills') to ensure
the interviewer asks deeply contextual, specific questions rather than generic ones.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class CategorizedRagIndex:
    """
    In-memory categorized RAG index powered by TF-IDF & Cosine Similarity.
    Maintains both unified index and category-partitioned subsets.
    """

    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = None
        self.matrix = None
        self._build_index()

    def _build_index(self):
        if not self.chunks:
            return

        corpus = [c["text"] for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query, categories=None, top_k=3):
        """
        Retrieves top_k chunks matching query.
        If categories list is provided (e.g. ['projects', 'experience']),
        only retrieves from chunks tagged with those categories.
        """
        if not self.chunks or not self.vectorizer or not query.strip():
            return []

        # If categories specified, filter candidate chunks
        if categories:
            matching_indices = [
                i for i, c in enumerate(self.chunks)
                if c.get("category", "").lower() in [cat.lower() for cat in categories]
            ]
        else:
            matching_indices = list(range(len(self.chunks)))

        if not matching_indices:
            # Fallback to all chunks if category filter yielded 0
            matching_indices = list(range(len(self.chunks)))

        sub_matrix = self.matrix[matching_indices]
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, sub_matrix)[0]

        ranked_sub_indices = sims.argsort()[::-1]

        results = []
        for rank_idx in ranked_sub_indices[:top_k]:
            score = sims[rank_idx]
            if score > 0.02:  # Relevancy threshold
                orig_idx = matching_indices[rank_idx]
                chunk_obj = dict(self.chunks[orig_idx])
                chunk_obj["similarity"] = round(float(score), 3)
                results.append(chunk_obj)

        return results

    def format_context_for_prompt(self, chunks_list):
        """Formats retrieved chunks into a clean, annotated string for the LLM prompt."""
        if not chunks_list:
            return "No specific document context available."

        formatted_blocks = []
        for c in chunks_list:
            cat_label = c.get("category", "General").upper()
            doc_label = c.get("doc_name", "Document")
            formatted_blocks.append(f"[{doc_label} | SECTION: {cat_label}]\n{c['text']}")

        return "\n\n---\n\n".join(formatted_blocks)


def create_rag_pipeline(text, doc_type=None, doc_name=""):
    """
    Convenience factory: parses document into categorized sections,
    chunks them, and builds a CategorizedRagIndex.
    """
    from rag.loader import parse_categorized_sections, detect_document_type
    from rag.chunker import build_categorized_chunks

    if not text or not text.strip():
        return None

    if not doc_type:
        doc_type = detect_document_type(text)

    sections = parse_categorized_sections(text, doc_type=doc_type)
    chunks = build_categorized_chunks(sections, doc_type=doc_type, doc_name=doc_name)
    return CategorizedRagIndex(chunks)
