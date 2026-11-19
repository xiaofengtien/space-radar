# -*- mode: python ; coding: utf-8 -*-
# SpaceRadar macOS PyInstaller Spec Configuration

import os
import sys

block_cipher = None

project_dir = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

a = Analysis(
    [os.path.join(project_dir, 'main.py')],
    pathex=[project_dir],
    binaries=[],
    datas=[
        (os.path.join(project_dir, 'assets'), 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'psutil',
        'watchdog',
        'watchdog.observers.fsevents',
        'watchdog.observers.kqueue',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
        'unittest',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SpaceRadar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, 'assets', 'SpaceRadar.icns'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SpaceRadar',
)

app = BUNDLE(
    coll,
    name='SpaceRadar.app',
    icon=os.path.join(project_dir, 'assets', 'SpaceRadar.icns'),
    bundle_identifier='com.xiaofengtien.spaceradar',
    info_plist={
        'CFBundleName': 'SpaceRadar',
        'CFBundleDisplayName': 'SpaceRadar · 空间雷达',
        'CFBundleExecutable': 'SpaceRadar',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleGetInfoString': 'SpaceRadar · 空间雷达 v1.0.0',
        'CFBundleIdentifier': 'com.xiaofengtien.spaceradar',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2026 SpaceRadar Team. All rights reserved.',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSRequiresAquaSystemAppearance': False,
        'NSSupportsAutomaticGraphicsSwitching': True,
    },
)
