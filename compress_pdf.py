#!/usr/bin/env python3
"""
PDF Compression Tool

A command-line utility to compress PDF files using Ghostscript or PyPDF.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)


def compress_with_ghostscript(
    input_path: str,
    output_path: str,
    quality: str = "ebook"
) -> bool:
    """
    Compress PDF using Ghostscript.
    
    Quality settings:
    - screen: lowest quality, smallest size (72 dpi)
    - ebook: medium quality, good for reading (150 dpi)
    - printer: high quality (300 dpi)
    - prepress: highest quality, largest size (300 dpi, color preserving)
    """
    # Check if ghostscript is available
    gs_cmd = None
    for cmd in ["gs", "gswin64c", "gswin32c"]:
        if shutil.which(cmd):
            gs_cmd = cmd
            break
    
    if not gs_cmd:
        return False
    
    quality_settings = {
        "screen": "/screen",
        "ebook": "/ebook",
        "printer": "/printer",
        "prepress": "/prepress",
    }
    
    pdfsettings = quality_settings.get(quality, "/ebook")
    
    try:
        subprocess.run(
            [
                gs_cmd,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={pdfsettings}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dCompressFonts=true",
                "-dSubsetFonts=true",
                "-dColorImageDownsampleType=/Bicubic",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dMonoImageDownsampleType=/Bicubic",
                f"-sOutputFile={output_path}",
                input_path,
            ],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ghostscript error: {e.stderr.decode()}", file=sys.stderr)
        return False


def compress_with_pypdf(input_path: str, output_path: str) -> bool:
    """
    Compress PDF using PyPDF library.
    
    This provides basic compression by removing redundant objects
    and compressing streams.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except ImportError:
            print("Neither pypdf nor PyPDF2 is installed.", file=sys.stderr)
            print("Install with: pip install pypdf", file=sys.stderr)
            return False
    
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        # Copy metadata
        if reader.metadata:
            writer.add_metadata(reader.metadata)
        
        # Write with compression
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return True
    except Exception as e:
        print(f"PyPDF error: {e}", file=sys.stderr)
        return False


def compress_pdf(
    input_path: str,
    output_path: str | None = None,
    quality: str = "ebook",
    force_pypdf: bool = False,
) -> tuple[bool, str]:
    """
    Compress a PDF file.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path for the output file (optional)
        quality: Compression quality (screen, ebook, printer, prepress)
        force_pypdf: Force using PyPDF instead of Ghostscript
    
    Returns:
        Tuple of (success, output_path)
    """
    input_path = os.path.abspath(input_path)
    
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return False, ""
    
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_compressed{ext}"
    
    output_path = os.path.abspath(output_path)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    original_size = get_file_size_mb(input_path)
    print(f"Input file: {input_path}")
    print(f"Original size: {original_size:.2f} MB")
    print(f"Quality setting: {quality}")
    
    success = False
    method = ""
    
    if not force_pypdf:
        print("Attempting compression with Ghostscript...")
        success = compress_with_ghostscript(input_path, output_path, quality)
        if success:
            method = "Ghostscript"
    
    if not success:
        print("Attempting compression with PyPDF...")
        success = compress_with_pypdf(input_path, output_path)
        if success:
            method = "PyPDF"
    
    if success and os.path.exists(output_path):
        compressed_size = get_file_size_mb(output_path)
        reduction = ((original_size - compressed_size) / original_size) * 100
        
        print(f"\n✓ Compression successful using {method}!")
        print(f"Output file: {output_path}")
        print(f"Compressed size: {compressed_size:.2f} MB")
        print(f"Size reduction: {reduction:.1f}%")
        
        if compressed_size >= original_size:
            print("\n⚠ Warning: Compressed file is not smaller than original.")
            print("  The original PDF may already be well-optimized.")
        
        return True, output_path
    else:
        print("\n✗ Compression failed.", file=sys.stderr)
        return False, ""


def main():
    parser = argparse.ArgumentParser(
        description="Compress PDF files to reduce file size.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality settings (for Ghostscript):
  screen   - Lowest quality, smallest size (72 dpi)
  ebook    - Medium quality, good balance (150 dpi) [default]
  printer  - High quality for printing (300 dpi)
  prepress - Highest quality, color preserving (300 dpi)

Examples:
  %(prog)s input.pdf
  %(prog)s input.pdf -o output.pdf
  %(prog)s input.pdf -q screen
  %(prog)s *.pdf --quality printer
        """,
    )
    
    parser.add_argument(
        "input",
        nargs="+",
        help="Input PDF file(s) to compress",
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (only for single file input)",
    )
    
    parser.add_argument(
        "-q", "--quality",
        choices=["screen", "ebook", "printer", "prepress"],
        default="ebook",
        help="Compression quality (default: ebook)",
    )
    
    parser.add_argument(
        "--pypdf",
        action="store_true",
        help="Force using PyPDF instead of Ghostscript",
    )
    
    parser.add_argument(
        "-r", "--replace",
        action="store_true",
        help="Replace original files with compressed versions",
    )
    
    args = parser.parse_args()
    
    if args.output and len(args.input) > 1:
        print("Error: --output can only be used with a single input file", file=sys.stderr)
        sys.exit(1)
    
    success_count = 0
    fail_count = 0
    
    for input_file in args.input:
        # Handle glob patterns
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            fail_count += 1
            continue
        
        if not input_path.suffix.lower() == ".pdf":
            print(f"Warning: Skipping non-PDF file: {input_file}", file=sys.stderr)
            continue
        
        output_path = args.output
        
        if args.replace:
            # Compress to temp file, then replace original
            temp_output = str(input_path.with_suffix(".pdf.tmp"))
            success, _ = compress_pdf(
                str(input_path),
                temp_output,
                args.quality,
                args.pypdf,
            )
            if success:
                os.replace(temp_output, str(input_path))
                print(f"Replaced original file: {input_path}")
                success_count += 1
            else:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                fail_count += 1
        else:
            success, _ = compress_pdf(
                str(input_path),
                output_path,
                args.quality,
                args.pypdf,
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print()  # Empty line between files
    
    # Summary for multiple files
    if len(args.input) > 1:
        print(f"Summary: {success_count} succeeded, {fail_count} failed")
    
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
