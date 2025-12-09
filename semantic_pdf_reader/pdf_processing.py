# pdf_processing.py
import fitz  # PyMuPDF
from typing import List
from .config import Chunk, DEFAULT_MAX_WORDS_PER_CHUNK


def extract_chunks_with_word_spans(
    pdf_path: str,
    max_words: int = DEFAULT_MAX_WORDS_PER_CHUNK
) -> List[Chunk]:
    """
    Open a PDF and split it into small chunks, each associated with
    a continuous span of words on a page.

    This makes it easy later to highlight those chunks back on the PDF.
    """
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    
    doc = fitz.open(pdf_path)
    all_chunks: List[Chunk] = []

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            words = page.get_text("words")
            # words: list of (x0, y0, x1, y1, "text", block_no, line_no, word_no)
            tokens = [w[4] for w in words]

            start = 0
            while start < len(tokens):
                end = min(start + max_words, len(tokens))
                text = " ".join(tokens[start:end]).strip()
                if text:
                    chunk = Chunk(
                        page=page_idx,
                        text=text,
                        word_start=start,
                        word_end=end
                    )
                    all_chunks.append(chunk)
                start = end
    finally:
        doc.close()
    
    return all_chunks
