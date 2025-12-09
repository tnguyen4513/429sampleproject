How to run:
cd 429sampleproject

# 1. Create a venv
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate

# 3. Install packages inside the venv
pip install --upgrade pip
pip install "numpy<2" pymupdf sentence-transformers scikit-learn

example run: 
python3 run_reader.py test.pdf "pixels" highlighted.pdf

to create .app or .exe:

test the app first: 
python3 gui_app.py

create app using pyinstaller:
pyinstaller --windowed --name "SemanticPDFGUI" gui_app.py
