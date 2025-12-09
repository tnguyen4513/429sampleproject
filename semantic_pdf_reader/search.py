# search.py
from typing import List, Tuple
import numpy as np

from .config import Chunk, DEFAULT_HYBRID_ALPHA
from .indexing import PdfIndex

# Normalize scores to [0, 1] for hybrid scoring combination
def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    """
    Normalize a score vector into [0, 1].
    """
    s_min = scores.min()
    s_max = scores.max()
    if s_max - s_min < 1e-10:
        # All scores are equal - return 0.5 for all (middle value)
        return np.full_like(scores, 0.5)
    return (scores - s_min) / (s_max - s_min)

# Lexical scoring using TF-IDF cosine similarity
def lexical_scores(query: str, index: PdfIndex) -> np.ndarray:
    q_vec = index.vectorizer.transform([query])
    # cosine similarity with tfidf_matrix (L2 not guaranteed, but it's fine as a score)
    scores = (index.tfidf_matrix @ q_vec.T).toarray().ravel()
    return scores


# Semantic scoring using cosine similarity with embeddings
def semantic_scores(query: str, index: PdfIndex) -> np.ndarray:
    model = index.embedding_model
    q_emb = model.encode([query], convert_to_numpy=True)[0]
    q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-10)
    scores = index.embedding_matrix @ q_emb  # cosine similarity
    return scores

# Hybrid scoring combining lexical and semantic scores
def hybrid_scores(
    query: str,
    index: PdfIndex,
    alpha: float = DEFAULT_HYBRID_ALPHA
) -> np.ndarray:
    lex = lexical_scores(query, index)
    sem = semantic_scores(query, index)

    lex_n = _normalize_scores(lex)
    sem_n = _normalize_scores(sem)

    return alpha * lex_n + (1.0 - alpha) * sem_n

# Retrieve top-k chunks(top-k chunks means the most relevant sections of the PDF) based on hybrid scores
def top_k_chunks(
    query: str,
    index: PdfIndex,
    k: int = 20,
    alpha: float = DEFAULT_HYBRID_ALPHA
) -> List[Tuple[Chunk, float]]:
    """
    Return the top-k chunks and their scores for a user query.
    """
    scores = hybrid_scores(query, index, alpha=alpha)
    order = np.argsort(scores)[::-1]  # descending
    top_idxs = order[:k]

    results: List[Tuple[Chunk, float]] = []
    for i in top_idxs:
        chunk = index.chunks[i]
        score = float(scores[i])
        chunk.score = score
        results.append((chunk, score))
    return results
