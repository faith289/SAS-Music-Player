# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['muuusic.py'],
    pathex=[],
    binaries=[
        ('vlc/libvlc.dll', '.'),
        ('vlc/libvlccore.dll', '.'),
    ],
    datas=[
        ('assets', 'assets'),
        ('vlc/plugins', 'plugins'),
    ],
    hiddenimports=[
        'win32gui',
        'win32con', 
        'win32api',
        'win32com.client',
        'ctypes',
        'vlc',
        'mutagen',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SAS_Music_Player',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
