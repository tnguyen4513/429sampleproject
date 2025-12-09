# PyInstaller hook for pkg_resources to fix jaraco import issue
# This file should be placed in a hooks directory or in the same directory as the spec file

# The issue: PyInstaller's pyi_rth_pkgres runtime hook tries to import jaraco
# but jaraco doesn't exist as a top-level module - only subpackages exist

# Solution: Ensure jaraco.text and other jaraco subpackages are collected
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all jaraco submodules
hiddenimports = collect_submodules('jaraco')

# Collect jaraco data files
datas = collect_data_files('jaraco', excludes=['*.pyc'])

# Add common jaraco subpackages explicitly
hiddenimports += [
    'jaraco.text',
    'jaraco.functools', 
    'jaraco.context',
    'jaraco.collections',
]
