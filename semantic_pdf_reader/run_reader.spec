# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files
import os

datas = []
binaries = []
hiddenimports = []

# Collect sentence_transformers and transformers
try:
    tmp_ret = collect_all('sentence_transformers')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception as e:
    print(f"Warning: Could not collect sentence_transformers: {e}")

try:
    tmp_ret = collect_all('transformers')
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
except Exception as e:
    print(f"Warning: Could not collect transformers: {e}")

# Collect jaraco subpackages (required for pkg_resources runtime hook)
try:
    # Try to collect all jaraco submodules from installed packages
    jaraco_modules = collect_submodules('jaraco')
    hiddenimports += jaraco_modules
    
    # Collect jaraco data files
    jaraco_datas = collect_data_files('jaraco', excludes=['*.pyc'])
    datas += jaraco_datas
except Exception as e:
    print(f"Warning: Could not collect jaraco from site-packages: {e}")

# Explicitly add jaraco packages that pkg_resources needs
hiddenimports += [
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
    'jaraco.collections',
    'jaraco',  # Add jaraco itself (will use our stub if not found)
]

# Add the jaraco_stub directory as a data source
if os.path.exists('jaraco_stub'):
    datas.append(('jaraco_stub', 'jaraco'))

# Collect sklearn
try:
    sklearn_modules = collect_submodules('sklearn')
    hiddenimports += sklearn_modules
except:
    pass

# Essential imports
hiddenimports += [
    'sentence_transformers',
    'transformers',
    'torch',
    'numpy',
    'sklearn',
    'fitz',  # PyMuPDF
    'PyMuPDF',
]

a = Analysis(
    ['../run_reader.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],  # Use current directory for custom hooks
    hooksconfig={},
    runtime_hooks=['pyi_rth_pkgres.py'],  # Use our custom runtime hook
    excludes=['pkg_resources.py2_warn'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='run_reader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid runtime issues with dependencies
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
