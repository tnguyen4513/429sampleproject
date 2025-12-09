#!/usr/bin/env python3
"""
Direct PDF search and highlight tool.
Reads a PDF, searches for a query, and highlights results directly in the original file.

Usage:
    python search_and_highlight.py <pdf_path> <query> [--no-backup]

Example:
    python search_and_highlight.py document.pdf "termination clause"
    python search_and_highlight.py document.pdf "termination clause" --no-backup
"""

import sys
import argparse
from pathlib import Path

from semantic_pdf_reader.indexing import build_pdf_index
from semantic_pdf_reader.search import top_k_chunks
from semantic_pdf_reader.highlighting import highlight_chunks_in_pdf_inplace


def main():
    parser = argparse.ArgumentParser(
        description="Search and highlight semantic matches directly in a PDF file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf "termination clause"
  %(prog)s report.pdf "financial analysis" --no-backup
  %(prog)s contract.pdf "liability" --k 30 --threshold 0.3
        """
    )
    
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to the PDF file to search and highlight'
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Search query to find semantic matches'
    )
    
    parser.add_argument(
        '--k',
        type=int,
        default=20,
        help='Number of top chunks to highlight (default: 20)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.0,
        help='Minimum normalized score threshold to highlight (0.0-1.0, default: 0.0 = highlight all)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create a backup of the original file before modifying'
    )
    
    parser.add_argument(
        '--show-results',
        action='store_true',
        default=True,
        help='Show top matching results in console (default: True)'
    )
    
    args = parser.parse_args()

    pdf_path = args.pdf_path
    query = args.query

    # Validate PDF file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Check if file is writable
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.is_file():
        print(f"Error: Path is not a file: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Building index for {pdf_path}...")
    try:
        index = build_pdf_index(pdf_path)
    except Exception as e:
        print(f"Error building index: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Running semantic search for query: '{query}'")
    try:
        results = top_k_chunks(query, index, k=args.k)
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No results found for the query.")
        sys.exit(0)

    if args.show_results:
        print(f"\nTop {min(10, len(results))} matches:")
        print("-" * 80)
        for i, (chunk, score) in enumerate(results[:10], 1):
            print(f"{i}. Page {chunk.page + 1}, score={score:.3f}")
            snippet = chunk.text[:200].replace("\n", " ")
            print(f"   {snippet}")
            print()

    print(f"Highlighting {len(results)} chunks directly in: {pdf_path}")
    if not args.no_backup:
        print("(A backup will be created automatically)")
    
    try:
        highlight_chunks_in_pdf_inplace(
            pdf_path,
            results,
            score_threshold=args.threshold,
            backup=not args.no_backup
        )
        print("Done! The PDF has been updated with highlights.")
    except Exception as e:
        print(f"Error highlighting PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

