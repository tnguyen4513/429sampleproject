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
        return [0.0 for _ in scores]
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

    scores_only = [s for (_, s) in chunks_with_scores]
    scores_norm = _normalize_scores(scores_only)

    for (chunk, score), norm_score in zip(chunks_with_scores, scores_norm):
        if score < score_threshold:
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
            highlight.set_colors(stroke=(r, g, b), fill=None)
            highlight.update()

    # save result
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
