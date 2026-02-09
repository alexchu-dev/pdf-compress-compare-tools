#!/usr/bin/env python3
"""
PDF Compression Tool

A command-line and GUI utility to compress PDF files using Ghostscript or PyPDF.
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Callable, Optional


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    return os.path.getsize(filepath) / (1024 * 1024)


def compress_with_ghostscript(
    input_path: str,
    output_path: str,
    quality: str = "ebook"
) -> tuple[bool, Optional[str]]:
    """
    Compress PDF using Ghostscript.
    
    Quality settings:
    - screen: lowest quality, smallest size (72 dpi)
    - ebook: medium quality, good for reading (150 dpi)
    - printer: high quality (300 dpi)
    - prepress: highest quality, largest size (300 dpi, color preserving)
    
    Returns:
        Tuple of (success, error_message)
    """
    # Check if ghostscript is available
    # Include common installation paths for bundled apps that don't inherit PATH
    gs_cmd = None
    
    # First try standard PATH lookup
    for cmd in ["gs", "gswin64c", "gswin32c"]:
        if shutil.which(cmd):
            gs_cmd = cmd
            break
    
    # If not found, try common installation paths (for bundled macOS/Linux apps)
    if not gs_cmd:
        common_paths = [
            "/opt/homebrew/bin/gs",      # macOS Homebrew (Apple Silicon)
            "/usr/local/bin/gs",          # macOS Homebrew (Intel) / Linux
            "/usr/bin/gs",                # Linux system install
            "/opt/local/bin/gs",          # MacPorts
            "C:\\Program Files\\gs\\gs10.02.1\\bin\\gswin64c.exe",  # Windows
            "C:\\Program Files (x86)\\gs\\gs10.02.1\\bin\\gswin32c.exe",
        ]
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                gs_cmd = path
                break
    
    if not gs_cmd:
        return False, "Ghostscript not found. Install it for better compression."
    
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
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"Ghostscript error: {error_msg}", file=sys.stderr)
        return False, f"Ghostscript error: {error_msg}"


def compress_with_pypdf(input_path: str, output_path: str) -> tuple[bool, Optional[str]]:
    """
    Compress PDF using PyPDF library.
    
    This provides basic compression by removing redundant objects
    and compressing streams.
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except ImportError:
            error_msg = "Neither pypdf nor PyPDF2 is installed. Install with: pip install pypdf"
            print(error_msg, file=sys.stderr)
            return False, error_msg
    
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
        
        return True, None
    except Exception as e:
        error_msg = f"PyPDF error: {e}"
        print(error_msg, file=sys.stderr)
        return False, error_msg


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
    last_error = ""
    
    if not force_pypdf:
        print("Attempting compression with Ghostscript...")
        gs_success, gs_error = compress_with_ghostscript(input_path, output_path, quality)
        if gs_success:
            success = True
            method = "Ghostscript"
        else:
            last_error = gs_error or "Ghostscript not available"
    
    if not success:
        print("Attempting compression with PyPDF...")
        pypdf_success, pypdf_error = compress_with_pypdf(input_path, output_path)
        if pypdf_success:
            success = True
            method = "PyPDF"
        else:
            last_error = pypdf_error or "PyPDF compression failed"
    
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
        
        return True, output_path, None
    else:
        print(f"\n✗ Compression failed: {last_error}", file=sys.stderr)
        return False, "", last_error


class PDFCompressGUI:
    """GUI for PDF compression."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Compression Tool")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        self.files: list[str] = []
        self.is_compressing = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Select PDF Files", padding="10")
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Buttons for file selection
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Add Files...", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Add Folder...", command=self._add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All", command=self._clear_files).pack(side=tk.LEFT)
        
        # File listbox with scrollbar
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(file_frame, text="Remove Selected", command=self._remove_selected).pack(anchor=tk.W, pady=(10, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Compression Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quality selection
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT)
        
        self.quality_var = tk.StringVar(value="ebook")
        qualities = [
            ("Screen (72 dpi) - Smallest", "screen"),
            ("Ebook (150 dpi) - Balanced", "ebook"),
            ("Printer (300 dpi) - High Quality", "printer"),
            ("Prepress (300 dpi) - Best Quality", "prepress"),
        ]
        
        for text, value in qualities:
            ttk.Radiobutton(quality_frame, text=text, variable=self.quality_var, value=value).pack(side=tk.LEFT, padx=10)
        
        # Output options
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill=tk.X)
        
        self.replace_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(output_frame, text="Replace original files", variable=self.replace_var).pack(side=tk.LEFT)
        
        self.pypdf_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(output_frame, text="Force PyPDF (skip Ghostscript)", variable=self.pypdf_var).pack(side=tk.LEFT, padx=20)
        
        # Compress button
        self.compress_btn = ttk.Button(main_frame, text="Compress PDFs", command=self._start_compression)
        self.compress_btn.pack(pady=10)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W)
        
        # Log text
        self.log_text = tk.Text(progress_frame, height=10, font=("Courier", 13), state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure log tags
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="blue")
        
    def _add_files(self):
        """Add PDF files via file dialog."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, f)
        self._update_file_count()
                
    def _add_folder(self):
        """Add all PDFs from a folder."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            for f in Path(folder).glob("*.pdf"):
                filepath = str(f)
                if filepath not in self.files:
                    self.files.append(filepath)
                    self.file_listbox.insert(tk.END, filepath)
        self._update_file_count()
                    
    def _clear_files(self):
        """Clear all files from the list."""
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self._update_file_count()
        
    def _remove_selected(self):
        """Remove selected files from the list."""
        selected = list(self.file_listbox.curselection())
        selected.reverse()  # Remove from bottom up
        for i in selected:
            del self.files[i]
            self.file_listbox.delete(i)
        self._update_file_count()
            
    def _update_file_count(self):
        """Update the file count in the UI."""
        count = len(self.files)
        self.compress_btn.config(text=f"Compress {count} PDF{'s' if count != 1 else ''}" if count > 0 else "Compress PDFs")
        
    def _log(self, message: str, tag: Optional[str] = None):
        """Add a message to the log."""
        self.log_text.config(state=tk.NORMAL)
        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def _start_compression(self):
        """Start the compression process in a background thread."""
        if not self.files:
            messagebox.showwarning("Warning", "Please add PDF files to compress.")
            return
            
        if self.is_compressing:
            return
            
        self.is_compressing = True
        self.compress_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Run compression in background thread
        thread = threading.Thread(target=self._compress_files, daemon=True)
        thread.start()
        
    def _compress_files(self):
        """Compress all files (runs in background thread)."""
        quality = self.quality_var.get()
        replace = self.replace_var.get()
        force_pypdf = self.pypdf_var.get()
        
        total = len(self.files)
        success_count = 0
        fail_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        for i, filepath in enumerate(self.files):
            filename = os.path.basename(filepath)
            self.root.after(0, lambda f=filename, n=i+1, t=total: self.progress_label.config(text=f"Processing {n}/{t}: {f}"))
            self.root.after(0, lambda p=(i / total) * 100: self.progress_var.set(p))
            
            original_size = get_file_size_mb(filepath)
            total_original_size += original_size
            
            try:
                if replace:
                    temp_output = filepath + ".tmp"
                    success, output_path, error_msg = compress_pdf(filepath, temp_output, quality, force_pypdf)
                    if success:
                        os.replace(temp_output, filepath)
                        output_path = filepath
                else:
                    base, ext = os.path.splitext(filepath)
                    output_path = f"{base}_compressed{ext}"
                    success, output_path, error_msg = compress_pdf(filepath, output_path, quality, force_pypdf)
                
                if success and os.path.exists(output_path):
                    compressed_size = get_file_size_mb(output_path)
                    total_compressed_size += compressed_size
                    reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
                    
                    self.root.after(0, lambda f=filename, r=reduction: self._log(f"✓ {f}: {r:.1f}% reduction", "success"))
                    success_count += 1
                else:
                    error_display = error_msg if error_msg else "Unknown error"
                    self.root.after(0, lambda f=filename, e=error_display: self._log(f"✗ {f}: {e}", "error"))
                    fail_count += 1
                    
            except Exception as e:
                self.root.after(0, lambda f=filename, e=str(e): self._log(f"✗ {f}: {e}", "error"))
                fail_count += 1
                
        # Summary
        total_reduction = ((total_original_size - total_compressed_size) / total_original_size) * 100 if total_original_size > 0 else 0
        
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.progress_label.config(text="Complete!"))
        self.root.after(0, lambda: self._log(f"\n{'='*50}", "info"))
        self.root.after(0, lambda s=success_count, f=fail_count: self._log(f"Completed: {s} succeeded, {f} failed", "info"))
        self.root.after(0, lambda o=total_original_size, c=total_compressed_size, r=total_reduction: 
                        self._log(f"Total: {o:.2f} MB → {c:.2f} MB ({r:.1f}% reduction)", "info"))
        
        self.root.after(0, lambda: self.compress_btn.config(state=tk.NORMAL))
        self.is_compressing = False
        
        if success_count > 0:
            self.root.after(0, lambda s=success_count: messagebox.showinfo("Complete", f"Successfully compressed {s} file(s)!"))
        
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


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
  %(prog)s --gui                    # Launch GUI
  %(prog)s input.pdf
  %(prog)s input.pdf -o output.pdf
  %(prog)s input.pdf -q screen
  %(prog)s *.pdf --quality printer
        """,
    )
    
    parser.add_argument(
        "input",
        nargs="*",
        help="Input PDF file(s) to compress",
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical user interface",
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
    
    # Launch GUI if requested or if no input files provided
    if args.gui or not args.input:
        app = PDFCompressGUI()
        app.run()
        return
    
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
            success, _, error_msg = compress_pdf(
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
            success, _, error_msg = compress_pdf(
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