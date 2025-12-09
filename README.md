# Semantic PDF Reader

A GUI application for semantic search in PDF documents using AI embeddings.

## Setup & Installation

### 1. Create and activate virtual environment

**On Windows:**
```powershell
python3 -m venv .venv
.\.venv\Scripts\activate
```

**On Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install "numpy<2" pymupdf sentence-transformers scikit-learn
```

(Optional for better setuptools compatibility):
```bash
pip install jaraco
pip install --upgrade setuptools
```

## Running the Application

Run the GUI application directly with Python:

```bash
python3 run_reader.py
```

This will launch the Semantic PDF Reader GUI where you can:
- **Choose a PDF** to analyze
- **Enter search queries** to find relevant content
- **Navigate matches** with highlighting
- **View semantic results** with scores