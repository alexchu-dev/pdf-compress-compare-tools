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


def build_app(name: str, script: str, description: str):
    """Build a standalone executable for a specific tool."""
    
    system = platform.system().lower()
    if system == "windows":
        output_name = f"{name}.exe"
    elif system == "darwin":
        output_name = f"{name}.app"
    else:
        output_name = name.lower()
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable file
        "--windowed",          # No console window (GUI app)
        "--name", name,
        # Hidden imports for conditional imports that PyInstaller can't detect
        "--hidden-import", "pypdf",
        "--hidden-import", "PyPDF2",
        "--hidden-import", "PIL",
        "--hidden-import", "fitz",
        # Collect all submodules
        "--collect-submodules", "pypdf",
        # Icon (optional - uncomment and provide icon file)
        # "--icon", f"{name.lower()}.ico",
        script
    ]
    
    print("=" * 60)
    print(f"Building {description}")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print(f"Output: dist/{output_name}")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ {name} built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False


def build_all():
    """Build all PDF tools."""
    
    apps = [
        ("PDFCompress", "compress_pdf.py", "PDF Compression Tool"),
        ("PDFCompare", "compare_pdf.py", "PDF Comparison Tool"),
    ]
    
    print("\n" + "=" * 60)
    print("PDF Tools Build Script")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Building {len(apps)} applications...")
    print("=" * 60 + "\n")
    
    results = []
    for name, script, description in apps:
        success = build_app(name, script, description)
        results.append((name, success))
        print()
    
    # Summary
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    
    system = platform.system().lower()
    ext = ".exe" if system == "windows" else (".app" if system == "darwin" else "")
    
    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {name}{ext}: {status}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\n{success_count}/{len(apps)} builds completed successfully.")
    
    if success_count > 0:
        print(f"\nExecutables are in: dist/")
        print("You can distribute these files to users without Python installed.")
        
        if system == "darwin":
            print("\nTo create a DMG installer (macOS):")
            print("  1. Install create-dmg: brew install create-dmg")
            print("  2. Run: create-dmg dist/PDFCompress.app dist/")
            print("  3. Run: create-dmg dist/PDFCompare.app dist/")
    
    return all(s for _, s in results)


def build_executable():
    """Build the standalone executables (legacy function for compatibility)."""
    return build_all()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build PDF Tools executables")
    parser.add_argument("--compress", action="store_true", help="Build only PDFCompress")
    parser.add_argument("--compare", action="store_true", help="Build only PDFCompare")
    
    args = parser.parse_args()
    
    if args.compress:
        success = build_app("PDFCompress", "compress_pdf.py", "PDF Compression Tool")
    elif args.compare:
        success = build_app("PDFCompare", "compare_pdf.py", "PDF Comparison Tool")
    else:
        success = build_all()
    
    sys.exit(0 if success else 1)
if __name__ == "__main__":
    build_executable()
