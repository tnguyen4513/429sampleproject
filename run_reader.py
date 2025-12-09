import sys
import tkinter as tk
from pathlib import Path
import traceback

try:
    from gui_app import SemanticPdfGUI
except ImportError as e:
    # If normal import fails, try adding paths
    import os
    # Try multiple possible locations
    possible_paths = [
        os.path.dirname(__file__),  # Script directory
        os.getcwd(),  # Current working directory
        '.',  # Relative to cwd
    ]
    
    for path in possible_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    try:
        from gui_app import SemanticPdfGUI
    except ImportError as e2:
        # Show error dialog
        error_msg = f"Failed to import gui_app:\n{str(e2)}\n\nSearched paths:\n" + "\n".join(possible_paths)
        root = tk.Tk()
        root.withdraw()
        import tkinter.messagebox
        tkinter.messagebox.showerror("Import Error", error_msg)
        raise

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    try:
        app = SemanticPdfGUI(root)
        root.mainloop()
    except Exception as e:
        root.withdraw()
        import tkinter.messagebox
        import traceback
        error_details = traceback.format_exc()
        tkinter.messagebox.showerror("Error", f"Failed to start application:\n\n{error_details}")
        raise
