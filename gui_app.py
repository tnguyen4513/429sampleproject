# gui_app.py
import os
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

import fitz  # PyMuPDF
from PIL import Image, ImageTk
import numpy as np

from semantic_pdf_reader.indexing import build_pdf_index, PdfIndex
from semantic_pdf_reader.search import top_k_chunks


class PdfViewer:
    """
    PDF viewer using PyMuPDF + Tkinter Canvas.
    Renders one page at a time and draws highlight rectangles on top.
    """
    def __init__(self, parent):
        self.parent = parent
        self.canvas = tk.Canvas(parent, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        # Scrollbars
        self.v_scroll = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(parent, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")

        # State
        self.doc: fitz.Document | None = None
        self.current_page_index: int = 0
        self.image_tk = None  # keep reference so Tkinter doesn't GC it
        # page_index -> list[(fitz.Rect, score_norm)]
        self.page_highlights: dict[int, list[tuple[fitz.Rect, float]]] = {}

        # Zoom factor
        self.zoom = 1.5

    def load_pdf(self, pdf_path: str):
        # Open original PDF – we never save or modify it
        if self.doc is not None:
            self.doc.close()
        self.doc = fitz.open(pdf_path)
        self.current_page_index = 0
        self.page_highlights = {}
        self.show_page()

    def set_highlights(self, page_highlights: dict[int, list[tuple[fitz.Rect, float]]]):
        """
        Only remember where highlights should be drawn. No file I/O.
        """
        self.page_highlights = page_highlights
        self.show_page()

    def show_page(self, focus_rect: fitz.Rect | None = None):
        if self.doc is None:
            return

        page = self.doc[self.current_page_index]

        # Render page to an image
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)

        self.image_tk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))

        # Draw the page image
        self.canvas.create_image(0, 0, image=self.image_tk, anchor="nw")

        # Draw highlight boxes over the page
        if self.page_highlights and self.current_page_index in self.page_highlights:
            for rect, score_norm in self.page_highlights[self.current_page_index]:
                x0 = rect.x0 * self.zoom
                y0 = rect.y0 * self.zoom
                x1 = rect.x1 * self.zoom
                y1 = rect.y1 * self.zoom

                # Color: yellow → orange depending on score
                r = 1.0
                g = 1.0 - 0.7 * score_norm
                b = 0.0
                r255 = int(r * 255)
                g255 = int(g * 255)
                b255 = int(b * 255)
                color = f"#{r255:02x}{g255:02x}{b255:02x}"

                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline=color,
                    width=2
                )

        # Optional: scroll to a specific match
        if focus_rect is not None:
            y0 = focus_rect.y0 * self.zoom
            page_height = pix.height
            target = max(0, y0 - page_height * 0.2)
            self.canvas.yview_moveto(target / max(page_height, 1))

    def next_page(self):
        if self.doc is None:
            return
        if self.current_page_index < len(self.doc) - 1:
            self.current_page_index += 1
            self.show_page()

    def prev_page(self):
        if self.doc is None:
            return
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.show_page()


class SemanticPdfGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Semantic PDF Reader (Semantic Cmd+F)")

        # Search/index state
        self.pdf_path: str | None = None
        self.index: PdfIndex | None = None
        self.current_pdf_indexed_path: str | None = None

        # Match navigation state
        self.matches: list[tuple[int, fitz.Rect, float]] = []  # (page_idx, rect, score_norm)
        self.current_match_index: int = -1
        self.last_query: str = ""

        self.build_ui()

    def build_ui(self):
        # --- Top controls ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=8, pady=8)

        self.pdf_label_var = tk.StringVar(value="No PDF selected")
        pdf_label = tk.Label(top_frame, textvariable=self.pdf_label_var, anchor="w")
        pdf_label.grid(row=0, column=0, sticky="w")

        choose_btn = tk.Button(top_frame, text="Choose PDF", command=self.choose_pdf)
        choose_btn.grid(row=0, column=1, padx=(10, 0))

        tk.Label(top_frame, text="Query:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.query_entry = tk.Entry(top_frame, width=50)
        self.query_entry.grid(row=1, column=1, sticky="we", pady=(6, 0))

        # Press Enter in the query box:
        # - if query changed => new search + new highlights
        # - if same query    => jump to next match
        self.query_entry.bind("<Return>", self.on_enter)

        self.status_var = tk.StringVar(value="Choose a PDF to start.")
        status_label = tk.Label(top_frame, textvariable=self.status_var, anchor="w", fg="gray")
        status_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # --- Middle split: viewer + right panel ---
        middle_frame = tk.PanedWindow(self.root, orient="horizontal", sashrelief="raised")
        middle_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Left side: navigation + viewer
        left_frame = tk.Frame(middle_frame)
        middle_frame.add(left_frame, stretch="always")

        nav_frame = tk.Frame(left_frame)
        nav_frame.pack(side="top", fill="x")

        prev_btn = tk.Button(nav_frame, text="◀ Prev Page", command=self.prev_page)
        prev_btn.pack(side="left")

        next_btn = tk.Button(nav_frame, text="Next Page ▶", command=self.next_page)
        next_btn.pack(side="right")

        next_match_btn = tk.Button(nav_frame, text="Next Match ↵", command=self.goto_next_match)
        next_match_btn.pack(side="right", padx=(10, 0))

        self.viewer = PdfViewer(left_frame)

        # Right side: text snippets
        right_frame = tk.Frame(middle_frame)
        middle_frame.add(right_frame, stretch="always")

        tk.Label(right_frame, text="Top Matches:").pack(anchor="w")
        self.results_box = scrolledtext.ScrolledText(right_frame, height=15)
        self.results_box.pack(fill="both", expand=True)

    # --- File selection & indexing ---

    def choose_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return

        self.pdf_path = path
        self.pdf_label_var.set(f"PDF: {os.path.basename(path)}")
        self.status_var.set("PDF selected. Loading...")
        self.index = None
        self.current_pdf_indexed_path = None
        self.matches = []
        self.current_match_index = -1

        try:
            self.viewer.load_pdf(self.pdf_path)
            self.status_var.set("PDF loaded. Enter a query and press Enter.")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load PDF:\n{e}")
            self.status_var.set("Error loading PDF.")

    def ensure_index(self):
        if not self.pdf_path:
            raise RuntimeError("No PDF selected.")

        if self.index is not None and self.current_pdf_indexed_path == self.pdf_path:
            return

        self.status_var.set("Building semantic index (this may take a bit)...")
        self.root.update_idletasks()

        self.index = build_pdf_index(self.pdf_path)
        self.current_pdf_indexed_path = self.pdf_path

        self.status_var.set("Index built. Ready to search.")
        self.root.update_idletasks()

    # --- Semantic search + highlight computation ---

    def run_search(self, query: str):
        if not self.pdf_path:
            messagebox.showwarning("No PDF", "Please choose a PDF first.")
            return
        if not query:
            messagebox.showwarning("No query", "Please enter a query.")
            return

        self.ensure_index()

        self.status_var.set("Running hybrid semantic search...")
        self.root.update_idletasks()

        results = top_k_chunks(query, self.index, k=20)

        # Show text snippets
        self.results_box.delete("1.0", tk.END)
        for i, (chunk, score) in enumerate(results[:10], start=1):
            snippet = chunk.text[:200].replace("\n", " ")
            self.results_box.insert(
                tk.END,
                f"{i}. Page {chunk.page + 1} | score={score:.3f}\n  {snippet}\n\n"
            )

        # Compute highlights & match list
        self.status_var.set("Computing highlights...")
        self.root.update_idletasks()

        page_highlights, matches = self.compute_page_highlights(results)
        self.matches = matches
        self.current_match_index = -1
        self.viewer.set_highlights(page_highlights)

        if self.matches:
            self.status_var.set(f"{len(self.matches)} matches. Press Enter to jump between them.")
            self.goto_next_match()
        else:
            self.status_var.set("No matches found.")

        self.last_query = query

    def compute_page_highlights(self, results):
        """
        Convert (chunk, score) into:
          - page_highlights: {page_index: [(Rect, score_norm), ...]}
          - matches: [(page_index, Rect, score_norm), ...]
        All in-memory – no file writing.
        """
        scores = [score for (_, score) in results]
        if not scores:
            return {}, []

        arr = np.array(scores)
        s_min, s_max = arr.min(), arr.max()
        if s_max - s_min < 1e-10:
            scores_norm = [0.0] * len(scores)
        else:
            scores_norm = ((arr - s_min) / (s_max - s_min)).tolist()

        page_highlights: dict[int, list[tuple[fitz.Rect, float]]] = {}
        matches: list[tuple[int, fitz.Rect, float]] = []

        doc = fitz.open(self.pdf_path)
        try:
            for (chunk, score), s_norm in zip(results, scores_norm):
                page_idx = chunk.page
                page = doc[page_idx]
                words = page.get_text("words")

                ws = max(0, chunk.word_start)
                we = min(len(words), chunk.word_end)
                if ws >= we:
                    continue

                for w in words[ws:we]:
                    rect = fitz.Rect(w[0], w[1], w[2], w[3])
                    page_highlights.setdefault(page_idx, []).append((rect, s_norm))
                    matches.append((page_idx, rect, s_norm))
        finally:
            doc.close()

        return page_highlights, matches

    # --- Match navigation ---

    def goto_next_match(self):
        if not self.matches:
            return

        self.current_match_index = (self.current_match_index + 1) % len(self.matches)
        page_idx, rect, score_norm = self.matches[self.current_match_index]

        self.viewer.current_page_index = page_idx
        self.viewer.show_page(focus_rect=rect)

        self.status_var.set(
            f"Match {self.current_match_index + 1}/{len(self.matches)} "
            f"on page {page_idx + 1}"
        )

    def on_enter(self, event):
        """
        Enter key behavior:
        - if query changed: new search
        - else: jump to next match
        """
        query = self.query_entry.get().strip()
        if query != self.last_query:
            self.run_search(query)
        else:
            self.goto_next_match()

    # --- Page navigation buttons ---

    def next_page(self):
        self.viewer.next_page()

    def prev_page(self):
        self.viewer.prev_page()


def main():
    root = tk.Tk()
    root.geometry("1100x700")
    app = SemanticPdfGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
