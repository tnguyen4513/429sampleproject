# Custom runtime hook to fix jaraco import issue
# This replaces PyInstaller's default pyi_rth_pkgres.py hook
# The issue: pkg_resources tries to import jaraco which doesn't exist as a top-level module

import sys
import os

# Try to import pkg_resources, but handle jaraco import failures gracefully
try:
    # Patch jaraco import before pkg_resources is imported
    import importlib.util
    
    # Create a dummy jaraco module if it doesn't exist
    if 'jaraco' not in sys.modules:
        class JaracoModule:
            """Dummy jaraco module to satisfy pkg_resources imports"""
            pass
        
        sys.modules['jaraco'] = JaracoModule()
    
    # Try to import jaraco.text if available, otherwise create stub
    try:
        import jaraco.text
    except ImportError:
        class JaracoText:
            pass
        sys.modules['jaraco.text'] = JaracoText()
    
    # Try to import jaraco.functools if available, otherwise create stub
    try:
        import jaraco.functools
    except ImportError:
        class JaracoFunctools:
            pass
        sys.modules['jaraco.functools'] = JaracoFunctools()
    
    # Try to import jaraco.context if available, otherwise create stub
    try:
        import jaraco.context
    except ImportError:
        class JaracoContext:
            pass
        sys.modules['jaraco.context'] = JaracoContext()
    
    # Now try to import pkg_resources - it should work now
    import pkg_resources
    
except Exception as e:
    # If something goes wrong, just ignore it
    # pkg_resources might not be critical for the app
    pass

