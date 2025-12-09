# indexing.py
from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

from .config import Chunk, DEFAULT_EMBEDDING_MODEL


class PdfIndex:
    """
    Holds all data structures required to perform hybrid semantic search
    on a single PDF.
    """
    def __init__(
        self,
        chunks: List[Chunk],
        vectorizer: TfidfVectorizer,
        tfidf_matrix,
        embedding_matrix: np.ndarray,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.chunks = chunks
        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.embedding_matrix = embedding_matrix  # normalized embeddings
        self.embedding_model_name = embedding_model_name

        # SentenceTransformer model is loaded lazily (not stored in pickle)
        self._embedding_model: SentenceTransformer | None = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model


def build_tfidf_index(chunks: List[Chunk]) -> Tuple[TfidfVectorizer, Any]:
    if not chunks:
        raise ValueError("Cannot build TF-IDF index from empty chunks list")
    texts = [c.text for c in chunks]
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=50000,
        stop_words="english"
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix


def build_semantic_index(
    chunks: List[Chunk],
    model_name: str = DEFAULT_EMBEDDING_MODEL
) -> Tuple[str, np.ndarray]:
    if not chunks:
        raise ValueError("Cannot build semantic index from empty chunks list")
    model = SentenceTransformer(model_name)
    texts = [c.text for c in chunks]
    emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    # L2-normalize for cosine similarity via dot product
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
    emb_norm = emb / norms
    return model_name, emb_norm


def build_pdf_index(
    pdf_path: str,
    max_words: int = 60,
    model_name: str = DEFAULT_EMBEDDING_MODEL
) -> PdfIndex:
    """
    Full pipeline: load PDF, extract chunks, build TF-IDF + embedding index.
    """
    from .pdf_processing import extract_chunks_with_word_spans

    chunks = extract_chunks_with_word_spans(pdf_path, max_words=max_words)
    vectorizer, tfidf_matrix = build_tfidf_index(chunks)
    embedding_model_name, embedding_matrix = build_semantic_index(chunks, model_name)

    return PdfIndex(
        chunks=chunks,
        vectorizer=vectorizer,
        tfidf_matrix=tfidf_matrix,
        embedding_matrix=embedding_matrix,
        embedding_model_name=embedding_model_name,
    )


# --- Optional: save / load (index metadata + matrices) -----------------------

import pickle
import pathlib


def save_pdf_index(index: PdfIndex, path: str) -> None:
    """
    Save index metadata and matrices to disk.
    NOTE: We do NOT pickle the SentenceTransformer model itself,
    only its name + precomputed embeddings.
    """
    path = pathlib.Path(path)
    data = {
        "chunks": index.chunks,
        "vectorizer": index.vectorizer,
        "tfidf_matrix": index.tfidf_matrix,
        "embedding_matrix": index.embedding_matrix,
        "embedding_model_name": index.embedding_model_name,
    }
    with path.open("wb") as f:
        pickle.dump(data, f)


def load_pdf_index(path: str) -> PdfIndex:
    """
    Load index data from disk and create a PdfIndex object.
    The SentenceTransformer model is reloaded lazily by name.
    """
    path = pathlib.Path(path)
    with path.open("rb") as f:
        data = pickle.load(f)

    index = PdfIndex(
        chunks=data["chunks"],
        vectorizer=data["vectorizer"],
        tfidf_matrix=data["tfidf_matrix"],
        embedding_matrix=data["embedding_matrix"],
        embedding_model_name=data["embedding_model_name"],
    )
    return index
