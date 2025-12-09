# Custom runtime hook to fix jaraco import issue
# This replaces PyInstaller's default pyi_rth_pkgres.py hook

import sys

# Create dummy jaraco modules before pkg_resources tries to import them
if 'jaraco' not in sys.modules:
    class JaracoModule:
        pass
    sys.modules['jaraco'] = JaracoModule()

try:
    import jaraco.text
except ImportError:
    class JaracoText:
        pass
    sys.modules['jaraco.text'] = JaracoText()

try:
    import jaraco.functools
except ImportError:
    class JaracoFunctools:
        pass
    sys.modules['jaraco.functools'] = JaracoFunctools()

try:
    import jaraco.context
except ImportError:
    class JaracoContext:
        pass
    sys.modules['jaraco.context'] = JaracoContext()

try:
    import jaraco.collections
except ImportError:
    class JaracoCollections:
        pass
    sys.modules['jaraco.collections'] = JaracoCollections()

# Now import pkg_resources - it should work
try:
    import pkg_resources
except Exception:
    pass
