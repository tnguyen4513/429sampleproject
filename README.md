How to run:
cd 429sampleproject

# 1. Create a venv
python3 -m venv .venv

# 2. Activate it on Mac
source .venv/bin/activate

# 2. Activate it on Windows
.\.venv\Scripts\activate

# 3. Install packages inside the venv
pip install --upgrade pip
pip install "numpy<2" pymupdf sentence-transformers scikit-learn


# 4. Install pyinstaller to create app
pip install pyinstaller==6.6.0

(optional)
pip install jaraco
pip install --upgrade setuptools 

# 5. Create app using pyinstaller: (it may take up to 15 minutes)
pyinstaller run_reader.spec

# faster install - Not in onefile:
python.exe -m PyInstaller run_reader.py --onefile --windowed


# 6. if app can not run 
remove the build and dist folders then rebuild step 5
    Remove-Item -Recurse -Force build
    Remove-Item -Recurse -Force dist
    Remove-Item -Force *.spec

# Run the reader for testing
python3 run_reader.py <input_file> <search_term> <output_file>
example run: 
python3 run_reader.py test.pdf "pixels" highlighted.pdf