# demo_cli.py
"""
Example command-line usage:

    python -m semantic_pdf_reader.demo_cli input.pdf "termination clause" output.pdf

This will:
  1. Build an index for input.pdf
  2. Run a hybrid semantic search for the query
  3. Print top chunks to console
  4. Save a new PDF with highlights at output.pdf
"""

import sys
from pathlib import Path

from .indexing import build_pdf_index
from .search import top_k_chunks
from .highlighting import highlight_chunks_in_pdf


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m semantic_pdf_reader.demo_cli <pdf_path> <query> <output_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    query = sys.argv[2]
    output_pdf = sys.argv[3]

    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"Building index for {pdf_path} ...")
    index = build_pdf_index(pdf_path)

    print(f"Running query: {query}")
    results = top_k_chunks(query, index, k=20)

    print("\nTop matches:")
    for chunk, score in results[:10]:
        print(f"- Page {chunk.page + 1}, score={score:.3f}")
        snippet = chunk.text[:200].replace("\n", " ")
        print(f"  {snippet}")
        print("")

    print(f"Creating highlighted PDF at: {output_pdf}")
    highlight_chunks_in_pdf(pdf_path, output_pdf, results)

    print("Done.")


if __name__ == "__main__":
    main()
