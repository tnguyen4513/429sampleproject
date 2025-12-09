# config.py
from dataclasses import dataclass
from typing import List, Optional

# Default model for sentence embeddings (local, small, fast)
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# How many tokens/words per chunk when splitting PDFs
DEFAULT_MAX_WORDS_PER_CHUNK = 60

# Default hybrid weight: alpha * lexical + (1 - alpha) * semantic
DEFAULT_HYBRID_ALPHA = 0.5

@dataclass
class Chunk:
    """
    Represents a small piece of text from the PDF with its location info.
    word_start / word_end are indices into the page's word list (PyMuPDF).
    """
    page: int
    text: str
    word_start: int
    word_end: int
    # Optional: store score for a given query (not persisted)
    score: Optional[float] = None
