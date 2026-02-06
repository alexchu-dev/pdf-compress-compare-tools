#!/usr/bin/env python3
"""
Build script for creating standalone executables.

This script uses PyInstaller to create standalone executables
for Windows, macOS, and Linux.
"""

import os
import platform
import subprocess
import sys


def build_executable():
    """Build the standalone executable."""
    
    # Determine the output name based on platform
    system = platform.system().lower()
    if system == "windows":
        output_name = "PDFCompare.exe"
    elif system == "darwin":
        output_name = "PDFCompare"
    else:
        output_name = "pdf_compare"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable file
        "--windowed",          # No console window (GUI app)
        "--name", "PDFCompare",
        "--add-data", f"README.md{os.pathsep}.",  # Include README
        # Icon (optional - uncomment and provide icon file)
        # "--icon", "icon.ico",
        "compare_pdf.py"
    ]
    
    print("=" * 60)
    print("Building PDF Compare Tool")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print(f"Output: {output_name}")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"\nExecutable created in: dist/{output_name}")
        print("\nYou can distribute this file to users without Python installed.")
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\nPyInstaller not found. Install it with:")
        print("  pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
