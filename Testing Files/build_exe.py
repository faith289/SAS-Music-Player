#!/usr/bin/env python3
"""
Build script for SAS Music Player EXE with VLC bundling
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def find_vlc_installation():
    """Find VLC installation directory"""
    possible_paths = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
        os.path.expanduser(r"~\AppData\Local\Programs\VideoLAN\VLC"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def copy_vlc_files(vlc_path, target_dir):
    """Copy required VLC files to target directory"""
    if not vlc_path:
        print("❌ VLC installation not found!")
        print("Please install VLC or provide the path manually.")
        return False
    
    target_vlc_dir = os.path.join(target_dir, "vlc")
    os.makedirs(target_vlc_dir, exist_ok=True)
    
    # Required DLLs
    required_dlls = [
        "libvlc.dll",
        "libvlccore.dll",
        "libvlc.dll.old",
        "libvlccore.dll.old",
    ]
    
    # Copy DLLs
    for dll in required_dlls:
        src = os.path.join(vlc_path, dll)
        dst = os.path.join(target_vlc_dir, dll)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Copied {dll}")
        else:
            print(f"⚠️  {dll} not found in VLC directory")
    
    # Copy plugins directory
    plugins_src = os.path.join(vlc_path, "plugins")
    plugins_dst = os.path.join(target_vlc_dir, "plugins")
    
    if os.path.exists(plugins_src):
        if os.path.exists(plugins_dst):
            shutil.rmtree(plugins_dst)
        shutil.copytree(plugins_src, plugins_dst)
        print("✅ Copied plugins directory")
    else:
        print("⚠️  plugins directory not found in VLC directory")
    
    return True

def update_spec_file():
    """Update the spec file with VLC file paths"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
'''
    
    with open('muuusic.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Updated muuusic.spec file")

def build_exe():
    """Build the EXE using PyInstaller"""
    try:
        result = subprocess.run(['pyinstaller', 'muuusic.spec'], 
                              capture_output=True, text=True, check=True)
        print("✅ EXE built successfully!")
        print("📁 Check the 'dist' folder for your executable.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Please install PyInstaller: pip install pyinstaller")
        return False

def main():
    print("🎵 SAS Music Player EXE Builder")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('muuusic.py'):
        print("❌ muuusic.py not found!")
        print("Please run this script from the 'Testing version' directory.")
        return
    
    # Step 1: Find and copy VLC files
    print("\n1️⃣  Setting up VLC files...")
    vlc_path = find_vlc_installation()
    
    if vlc_path:
        print(f"📁 Found VLC at: {vlc_path}")
        if copy_vlc_files(vlc_path, '.'):
            print("✅ VLC files copied successfully!")
        else:
            print("❌ Failed to copy VLC files!")
            return
    else:
        print("⚠️  VLC not found in standard locations.")
        print("Please copy VLC DLLs and plugins manually to a 'vlc' folder.")
        print("Required files:")
        print("  - vlc/libvlc.dll")
        print("  - vlc/libvlccore.dll") 
        print("  - vlc/plugins/ (entire folder)")
        
        if not os.path.exists('vlc'):
            print("❌ 'vlc' folder not found. Please set up VLC files first.")
            return
    
    # Step 2: Update spec file
    print("\n2️⃣  Updating spec file...")
    update_spec_file()
    
    # Step 3: Build EXE
    print("\n3️⃣  Building EXE...")
    if build_exe():
        print("\n🎉 Build completed successfully!")
        print("📁 Your EXE is in the 'dist' folder.")
        print("🚀 You can now run 'SAS_Music_Player.exe' without needing VLC installed!")
    else:
        print("\n❌ Build failed!")

if __name__ == "__main__":
    main() 