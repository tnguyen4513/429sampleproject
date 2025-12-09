# highlighting.py
from typing import List, Tuple
import fitz  # PyMuPDF
import numpy as np

from .config import Chunk


def _normalize_scores(scores: List[float]) -> List[float]:
    arr = np.array(scores)
    s_min = arr.min()
    s_max = arr.max()
    if s_max - s_min < 1e-10:
        # All scores are equal - return 0.5 for all (middle value)
        return [0.5 for _ in scores]
    return ((arr - s_min) / (s_max - s_min + 1e-10)).tolist()


def highlight_chunks_in_pdf(
    pdf_path: str,
    output_path: str,
    chunks_with_scores: List[Tuple[Chunk, float]],
    score_threshold: float = 0.0,
) -> None:
    """
    Given a PDF and a list of (chunk, score),
    produce a new PDF with highlight annotations.
    """
    if not chunks_with_scores:
        # nothing to do
        return

    doc = fitz.open(pdf_path)

    try:
        scores_only = [s for (_, s) in chunks_with_scores]
        scores_norm = _normalize_scores(scores_only)

        for (chunk, score), norm_score in zip(chunks_with_scores, scores_norm):
            if norm_score < score_threshold:
                continue

            # Guard: check page index is valid
            if chunk.page < 0 or chunk.page >= len(doc):
                continue

            page = doc[chunk.page]
            words = page.get_text("words")
            # guard indices
            ws = max(0, chunk.word_start)
            we = min(len(words), chunk.word_end)
            if ws >= we:
                continue

            word_span = words[ws:we]

            # Create individual highlights for each word rectangle
            for w in word_span:
                x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
                rect = fitz.Rect(x0, y0, x1, y1)
                highlight = page.add_highlight_annot(rect)

                # Color: (r, g, b) in [0,1]. Map norm_score 0-1 from yellow → red-ish.
                r = 1.0
                g = 1.0 - 0.7 * norm_score
                b = 0.0
                # For highlights, set fill color (highlight uses fill, not stroke)
                highlight.set_colors(stroke=None, fill=(r, g, b))
                highlight.update()

        # save result
        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()


def highlight_chunks_in_pdf_inplace(
    pdf_path: str,
    chunks_with_scores: List[Tuple[Chunk, float]],
    score_threshold: float = 0.0,
    backup: bool = True,
) -> None:
    """
    Highlight chunks directly in the original PDF file (in-place modification).
    
    Args:
        pdf_path: Path to the PDF file to modify
        chunks_with_scores: List of (chunk, score) tuples to highlight
        score_threshold: Minimum normalized score to highlight (0.0 = highlight all)
        backup: If True, creates a backup file before modifying
    """
    if not chunks_with_scores:
        print("No chunks to highlight.")
        return

    from pathlib import Path
    
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Create backup if requested
    if backup:
        backup_path = pdf_path_obj.with_suffix(f'.backup{pdf_path_obj.suffix}')
        import shutil
        shutil.copy2(pdf_path, backup_path)
        print(f"Backup created: {backup_path}")

    doc = fitz.open(pdf_path)

    try:
        scores_only = [s for (_, s) in chunks_with_scores]
        scores_norm = _normalize_scores(scores_only)

        highlighted_count = 0
        for (chunk, score), norm_score in zip(chunks_with_scores, scores_norm):
            if norm_score < score_threshold:
                continue

            # Guard: check page index is valid
            if chunk.page < 0 or chunk.page >= len(doc):
                continue

            page = doc[chunk.page]
            words = page.get_text("words")
            # guard indices
            ws = max(0, chunk.word_start)
            we = min(len(words), chunk.word_end)
            if ws >= we:
                continue

            word_span = words[ws:we]

            # Create individual highlights for each word rectangle
            for w in word_span:
                x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
                rect = fitz.Rect(x0, y0, x1, y1)
                highlight = page.add_highlight_annot(rect)

                # Color: (r, g, b) in [0,1]. Map norm_score 0-1 from yellow → red-ish.
                r = 1.0
                g = 1.0 - 0.7 * norm_score
                b = 0.0
                # For highlights, set fill color (highlight uses fill, not stroke)
                highlight.set_colors(stroke=None, fill=(r, g, b))
                highlight.update()
            
            highlighted_count += 1

        # Save directly to the original file
        doc.save(pdf_path, garbage=4, deflate=True)
        print(f"Highlighted {highlighted_count} chunks directly in: {pdf_path}")
    finally:
        doc.close()
