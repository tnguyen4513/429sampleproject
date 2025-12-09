import sys
import tkinter as tk
from pathlib import Path

# Add current directory to path so we can import gui_app
sys.path.insert(0, str(Path(__file__).parent))

from gui_app import SemanticPdfGUI

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    app = SemanticPdfGUI(root)
    root.mainloop()
