#!/usr/bin/env python3
"""
PDF Comparison Tool with GUI

A graphical utility to compare two PDF files side by side.
Supports text-based and visual comparison.
"""

import difflib
import io
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

try:
    from PIL import Image, ImageTk
    import fitz  # PyMuPDF for rendering PDF pages
    HAS_VISUAL_COMPARE = True
except ImportError:
    HAS_VISUAL_COMPARE = False


class PDFComparer:
    """Class to handle PDF comparison logic."""
    
    def __init__(self, pdf1_path: str, pdf2_path: str):
        self.pdf1_path = pdf1_path
        self.pdf2_path = pdf2_path
        self.pdf1_reader: Optional[PdfReader] = None
        self.pdf2_reader: Optional[PdfReader] = None
        
    def load_pdfs(self) -> tuple[bool, str]:
        """Load both PDF files."""
        try:
            self.pdf1_reader = PdfReader(self.pdf1_path)
            self.pdf2_reader = PdfReader(self.pdf2_path)
            return True, "PDFs loaded successfully"
        except Exception as e:
            return False, f"Error loading PDFs: {str(e)}"
    
    def get_metadata_comparison(self) -> dict:
        """Compare metadata of both PDFs."""
        if not self.pdf1_reader or not self.pdf2_reader:
            return {}
        
        def get_metadata(reader: PdfReader) -> dict:
            meta = reader.metadata or {}
            return {
                "Title": meta.get("/Title", "N/A"),
                "Author": meta.get("/Author", "N/A"),
                "Subject": meta.get("/Subject", "N/A"),
                "Creator": meta.get("/Creator", "N/A"),
                "Producer": meta.get("/Producer", "N/A"),
                "Pages": len(reader.pages),
            }
        
        return {
            "pdf1": get_metadata(self.pdf1_reader),
            "pdf2": get_metadata(self.pdf2_reader),
        }
    
    def extract_text(self, reader: PdfReader) -> list[str]:
        """Extract text from all pages of a PDF."""
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return texts
    
    def compare_text(self) -> list[dict]:
        """Compare text content page by page."""
        if not self.pdf1_reader or not self.pdf2_reader:
            return []
        
        text1 = self.extract_text(self.pdf1_reader)
        text2 = self.extract_text(self.pdf2_reader)
        
        max_pages = max(len(text1), len(text2))
        comparisons = []
        
        for i in range(max_pages):
            page_text1 = text1[i] if i < len(text1) else ""
            page_text2 = text2[i] if i < len(text2) else ""
            
            # Calculate similarity ratio
            matcher = difflib.SequenceMatcher(None, page_text1, page_text2)
            similarity = matcher.ratio() * 100
            
            # Generate diff
            diff = list(difflib.unified_diff(
                page_text1.splitlines(keepends=True),
                page_text2.splitlines(keepends=True),
                fromfile=f"PDF1 - Page {i+1}",
                tofile=f"PDF2 - Page {i+1}",
                lineterm=""
            ))
            
            comparisons.append({
                "page": i + 1,
                "text1": page_text1,
                "text2": page_text2,
                "similarity": similarity,
                "diff": diff,
                "identical": page_text1 == page_text2,
            })
        
        return comparisons
    
    def get_summary(self) -> dict:
        """Get a summary of the comparison."""
        if not self.pdf1_reader or not self.pdf2_reader:
            return {}
        
        comparisons = self.compare_text()
        total_pages = len(comparisons)
        identical_pages = sum(1 for c in comparisons if c["identical"])
        avg_similarity = sum(c["similarity"] for c in comparisons) / total_pages if total_pages > 0 else 0
        
        return {
            "total_pages_pdf1": len(self.pdf1_reader.pages),
            "total_pages_pdf2": len(self.pdf2_reader.pages),
            "identical_pages": identical_pages,
            "different_pages": total_pages - identical_pages,
            "average_similarity": avg_similarity,
            "files_identical": identical_pages == total_pages and len(self.pdf1_reader.pages) == len(self.pdf2_reader.pages),
        }


class PDFCompareGUI:
    """GUI for PDF comparison."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Comparison Tool")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        self.pdf1_path: Optional[str] = None
        self.pdf2_path: Optional[str] = None
        self.comparer: Optional[PDFComparer] = None
        self.comparisons: list[dict] = []
        self.current_page = 0
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Select PDF Files", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # PDF 1 selection
        pdf1_frame = ttk.Frame(file_frame)
        pdf1_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pdf1_frame, text="PDF 1:", width=8).pack(side=tk.LEFT)
        self.pdf1_entry = ttk.Entry(pdf1_frame)
        self.pdf1_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(pdf1_frame, text="Browse...", command=lambda: self._browse_file(1)).pack(side=tk.LEFT)
        
        # PDF 2 selection
        pdf2_frame = ttk.Frame(file_frame)
        pdf2_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pdf2_frame, text="PDF 2:", width=8).pack(side=tk.LEFT)
        self.pdf2_entry = ttk.Entry(pdf2_frame)
        self.pdf2_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(pdf2_frame, text="Browse...", command=lambda: self._browse_file(2)).pack(side=tk.LEFT)
        
        # Compare button and Export button
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Compare PDFs", command=self._compare_pdfs).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Export to Markdown", command=self._export_markdown).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Export to HTML", command=self._export_html).pack(side=tk.LEFT)
        
        # Notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.summary_frame, text="Summary")
        
        self.summary_text = tk.Text(self.summary_frame, wrap=tk.WORD, font=("Courier", 11))
        summary_scroll = ttk.Scrollbar(self.summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Page comparison tab
        self.page_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.page_frame, text="Page Comparison")
        
        # Page navigation
        nav_frame = ttk.Frame(self.page_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(nav_frame, text="◀ Previous", command=self._prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(nav_frame, text="Next ▶", command=self._next_page).pack(side=tk.LEFT)
        
        self.similarity_label = ttk.Label(nav_frame, text="Similarity: --%")
        self.similarity_label.pack(side=tk.RIGHT)
        
        # Side by side text comparison
        text_compare_frame = ttk.Frame(self.page_frame)
        text_compare_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        text_compare_frame.columnconfigure(0, weight=1)
        text_compare_frame.columnconfigure(1, weight=1)
        text_compare_frame.rowconfigure(1, weight=1)
        
        # PDF 1 text
        ttk.Label(text_compare_frame, text="PDF 1", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.text1_widget = tk.Text(text_compare_frame, wrap=tk.WORD, font=("Courier", 10))
        scroll1 = ttk.Scrollbar(text_compare_frame, orient=tk.VERTICAL, command=self.text1_widget.yview)
        self.text1_widget.configure(yscrollcommand=scroll1.set)
        self.text1_widget.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        scroll1.grid(row=1, column=0, sticky="nse", padx=(0, 5))
        
        # PDF 2 text
        ttk.Label(text_compare_frame, text="PDF 2", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        self.text2_widget = tk.Text(text_compare_frame, wrap=tk.WORD, font=("Courier", 10))
        scroll2 = ttk.Scrollbar(text_compare_frame, orient=tk.VERTICAL, command=self.text2_widget.yview)
        self.text2_widget.configure(yscrollcommand=scroll2.set)
        self.text2_widget.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        scroll2.grid(row=1, column=1, sticky="nse")
        
        # Diff tab
        self.diff_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.diff_frame, text="Diff View")
        
        self.diff_text = tk.Text(self.diff_frame, wrap=tk.NONE, font=("Courier", 10))
        diff_scrolly = ttk.Scrollbar(self.diff_frame, orient=tk.VERTICAL, command=self.diff_text.yview)
        diff_scrollx = ttk.Scrollbar(self.diff_frame, orient=tk.HORIZONTAL, command=self.diff_text.xview)
        self.diff_text.configure(yscrollcommand=diff_scrolly.set, xscrollcommand=diff_scrollx.set)
        
        diff_scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        diff_scrollx.pack(side=tk.BOTTOM, fill=tk.X)
        self.diff_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure diff text tags for coloring
        self.diff_text.tag_configure("added", foreground="green", background="#e6ffe6")
        self.diff_text.tag_configure("removed", foreground="red", background="#ffe6e6")
        self.diff_text.tag_configure("header", foreground="blue", font=("Courier", 10, "bold"))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select two PDF files to compare")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def _browse_file(self, pdf_num: int):
        """Open file dialog to select a PDF."""
        filepath = filedialog.askopenfilename(
            title=f"Select PDF {pdf_num}",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if filepath:
            if pdf_num == 1:
                self.pdf1_path = filepath
                self.pdf1_entry.delete(0, tk.END)
                self.pdf1_entry.insert(0, filepath)
            else:
                self.pdf2_path = filepath
                self.pdf2_entry.delete(0, tk.END)
                self.pdf2_entry.insert(0, filepath)
                
    def _compare_pdfs(self):
        """Perform the PDF comparison."""
        # Get paths from entries
        self.pdf1_path = self.pdf1_entry.get().strip()
        self.pdf2_path = self.pdf2_entry.get().strip()
        
        if not self.pdf1_path or not self.pdf2_path:
            messagebox.showerror("Error", "Please select both PDF files.")
            return
        
        if not os.path.exists(self.pdf1_path):
            messagebox.showerror("Error", f"PDF 1 not found: {self.pdf1_path}")
            return
            
        if not os.path.exists(self.pdf2_path):
            messagebox.showerror("Error", f"PDF 2 not found: {self.pdf2_path}")
            return
        
        self.status_var.set("Comparing PDFs...")
        self.root.update()
        
        try:
            self.comparer = PDFComparer(self.pdf1_path, self.pdf2_path)
            success, message = self.comparer.load_pdfs()
            
            if not success:
                messagebox.showerror("Error", message)
                self.status_var.set("Comparison failed")
                return
            
            # Get comparisons
            self.comparisons = self.comparer.compare_text()
            self.current_page = 0
            
            # Update summary
            self._update_summary()
            
            # Update page view
            self._update_page_view()
            
            # Update diff view
            self._update_diff_view()
            
            self.status_var.set("Comparison complete!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed: {str(e)}")
            self.status_var.set("Comparison failed")
            
    def _update_summary(self):
        """Update the summary tab."""
        if not self.comparer:
            return
            
        summary = self.comparer.get_summary()
        metadata = self.comparer.get_metadata_comparison()
        
        self.summary_text.delete(1.0, tk.END)
        
        # File info
        self.summary_text.insert(tk.END, "=" * 60 + "\n")
        self.summary_text.insert(tk.END, "PDF COMPARISON SUMMARY\n")
        self.summary_text.insert(tk.END, "=" * 60 + "\n\n")
        
        self.summary_text.insert(tk.END, f"PDF 1: {os.path.basename(self.pdf1_path)}\n")
        self.summary_text.insert(tk.END, f"       {self.pdf1_path}\n")
        self.summary_text.insert(tk.END, f"       Size: {os.path.getsize(self.pdf1_path) / 1024:.1f} KB\n\n")
        
        self.summary_text.insert(tk.END, f"PDF 2: {os.path.basename(self.pdf2_path)}\n")
        self.summary_text.insert(tk.END, f"       {self.pdf2_path}\n")
        self.summary_text.insert(tk.END, f"       Size: {os.path.getsize(self.pdf2_path) / 1024:.1f} KB\n\n")
        
        # Comparison results
        self.summary_text.insert(tk.END, "-" * 60 + "\n")
        self.summary_text.insert(tk.END, "COMPARISON RESULTS\n")
        self.summary_text.insert(tk.END, "-" * 60 + "\n\n")
        
        if summary.get("files_identical"):
            self.summary_text.insert(tk.END, "✓ THE FILES ARE IDENTICAL\n\n")
        else:
            self.summary_text.insert(tk.END, "✗ THE FILES ARE DIFFERENT\n\n")
        
        self.summary_text.insert(tk.END, f"Pages in PDF 1:       {summary.get('total_pages_pdf1', 0)}\n")
        self.summary_text.insert(tk.END, f"Pages in PDF 2:       {summary.get('total_pages_pdf2', 0)}\n")
        self.summary_text.insert(tk.END, f"Identical pages:      {summary.get('identical_pages', 0)}\n")
        self.summary_text.insert(tk.END, f"Different pages:      {summary.get('different_pages', 0)}\n")
        self.summary_text.insert(tk.END, f"Average similarity:   {summary.get('average_similarity', 0):.1f}%\n\n")
        
        # Metadata comparison
        self.summary_text.insert(tk.END, "-" * 60 + "\n")
        self.summary_text.insert(tk.END, "METADATA COMPARISON\n")
        self.summary_text.insert(tk.END, "-" * 60 + "\n\n")
        
        meta1 = metadata.get("pdf1", {})
        meta2 = metadata.get("pdf2", {})
        
        self.summary_text.insert(tk.END, f"{'Property':<15} {'PDF 1':<30} {'PDF 2':<30}\n")
        self.summary_text.insert(tk.END, "-" * 75 + "\n")
        
        for key in ["Title", "Author", "Subject", "Creator", "Producer", "Pages"]:
            val1 = str(meta1.get(key, "N/A"))[:28]
            val2 = str(meta2.get(key, "N/A"))[:28]
            self.summary_text.insert(tk.END, f"{key:<15} {val1:<30} {val2:<30}\n")
        
        # Per-page similarity
        self.summary_text.insert(tk.END, "\n" + "-" * 60 + "\n")
        self.summary_text.insert(tk.END, "PAGE-BY-PAGE SIMILARITY\n")
        self.summary_text.insert(tk.END, "-" * 60 + "\n\n")
        
        for comp in self.comparisons:
            status = "✓" if comp["identical"] else "✗"
            self.summary_text.insert(tk.END, f"Page {comp['page']:3}: {comp['similarity']:5.1f}% {status}\n")
            
    def _update_page_view(self):
        """Update the page comparison view."""
        if not self.comparisons:
            return
            
        if self.current_page >= len(self.comparisons):
            self.current_page = len(self.comparisons) - 1
        if self.current_page < 0:
            self.current_page = 0
            
        comp = self.comparisons[self.current_page]
        
        # Update navigation
        self.page_label.config(text=f"Page {self.current_page + 1} / {len(self.comparisons)}")
        self.similarity_label.config(text=f"Similarity: {comp['similarity']:.1f}%")
        
        # Update text widgets
        self.text1_widget.delete(1.0, tk.END)
        self.text1_widget.insert(1.0, comp["text1"])
        
        self.text2_widget.delete(1.0, tk.END)
        self.text2_widget.insert(1.0, comp["text2"])
        
    def _update_diff_view(self):
        """Update the diff view."""
        self.diff_text.delete(1.0, tk.END)
        
        for comp in self.comparisons:
            self.diff_text.insert(tk.END, f"\n{'='*60}\n", "header")
            self.diff_text.insert(tk.END, f"Page {comp['page']} - Similarity: {comp['similarity']:.1f}%\n", "header")
            self.diff_text.insert(tk.END, f"{'='*60}\n\n", "header")
            
            if comp["identical"]:
                self.diff_text.insert(tk.END, "(Pages are identical)\n\n")
            else:
                for line in comp["diff"]:
                    if line.startswith("+") and not line.startswith("+++"):
                        self.diff_text.insert(tk.END, line + "\n", "added")
                    elif line.startswith("-") and not line.startswith("---"):
                        self.diff_text.insert(tk.END, line + "\n", "removed")
                    elif line.startswith("@@"):
                        self.diff_text.insert(tk.END, line + "\n", "header")
                    else:
                        self.diff_text.insert(tk.END, line + "\n")
                        
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_view()
            
    def _next_page(self):
        """Go to next page."""
        if self.current_page < len(self.comparisons) - 1:
            self.current_page += 1
            self._update_page_view()
    
    def _export_markdown(self):
        """Export the comparison results to a Markdown file."""
        if not self.comparisons:
            messagebox.showwarning("Warning", "No comparison results to export. Please compare PDFs first.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save Markdown Report",
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")],
            initialfile=f"pdf_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        
        if not filepath:
            return
        
        try:
            summary = self.comparer.get_summary()
            metadata = self.comparer.get_metadata_comparison()
            
            md_content = self._generate_markdown(summary, metadata)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            messagebox.showinfo("Success", f"Report exported to:\n{filepath}")
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def _generate_markdown(self, summary: dict, metadata: dict) -> str:
        """Generate Markdown content with colored diff."""
        lines = []
        
        # Header
        lines.append("# PDF Comparison Report")
        lines.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # File Information
        lines.append("## File Information\n")
        lines.append(f"| Property | PDF 1 | PDF 2 |")
        lines.append(f"|----------|-------|-------|")
        lines.append(f"| **File** | `{os.path.basename(self.pdf1_path)}` | `{os.path.basename(self.pdf2_path)}` |")
        lines.append(f"| **Size** | {os.path.getsize(self.pdf1_path) / 1024:.1f} KB | {os.path.getsize(self.pdf2_path) / 1024:.1f} KB |")
        lines.append(f"| **Pages** | {summary.get('total_pages_pdf1', 0)} | {summary.get('total_pages_pdf2', 0)} |")
        lines.append("")
        
        # Summary
        lines.append("## Comparison Summary\n")
        if summary.get("files_identical"):
            lines.append("✅ **THE FILES ARE IDENTICAL**\n")
        else:
            lines.append("❌ **THE FILES ARE DIFFERENT**\n")
        
        lines.append(f"- **Identical pages:** {summary.get('identical_pages', 0)}")
        lines.append(f"- **Different pages:** {summary.get('different_pages', 0)}")
        lines.append(f"- **Average similarity:** {summary.get('average_similarity', 0):.1f}%\n")
        
        # Metadata Comparison
        lines.append("## Metadata Comparison\n")
        meta1 = metadata.get("pdf1", {})
        meta2 = metadata.get("pdf2", {})
        
        lines.append("| Property | PDF 1 | PDF 2 | Match |")
        lines.append("|----------|-------|-------|-------|")
        for key in ["Title", "Author", "Subject", "Creator", "Producer"]:
            val1 = str(meta1.get(key, "N/A"))
            val2 = str(meta2.get(key, "N/A"))
            match = "✅" if val1 == val2 else "❌"
            lines.append(f"| {key} | {val1} | {val2} | {match} |")
        lines.append("")
        
        # Page-by-Page Comparison
        lines.append("## Page-by-Page Comparison\n")
        lines.append("| Page | Similarity | Status |")
        lines.append("|------|------------|--------|")
        for comp in self.comparisons:
            status = "✅ Identical" if comp["identical"] else "❌ Different"
            lines.append(f"| {comp['page']} | {comp['similarity']:.1f}% | {status} |")
        lines.append("")
        
        # Detailed Diff
        lines.append("## Detailed Differences\n")
        lines.append("> **Legend:** ")
        lines.append("> - 🟢 <span style=\"color: green;\">Green text</span> = Added in PDF 2")
        lines.append("> - 🔴 <span style=\"color: red;\">Red text</span> = Removed from PDF 1\n")
        
        for comp in self.comparisons:
            lines.append(f"### Page {comp['page']} (Similarity: {comp['similarity']:.1f}%)\n")
            
            if comp["identical"]:
                lines.append("*Pages are identical*\n")
            else:
                lines.append("```diff")
                for line in comp["diff"]:
                    # Escape any backticks in the line
                    escaped_line = line.replace("`", "'")
                    lines.append(escaped_line)
                lines.append("```\n")
                
                # Also add HTML-colored version for better rendering
                lines.append("<details>")
                lines.append("<summary>View colored diff</summary>\n")
                for line in comp["diff"]:
                    escaped = line.replace("<", "&lt;").replace(">", "&gt;")
                    if line.startswith("+") and not line.startswith("+++"):
                        lines.append(f'<span style="color: green; background-color: #e6ffe6;">🟢 {escaped}</span><br>')
                    elif line.startswith("-") and not line.startswith("---"):
                        lines.append(f'<span style="color: red; background-color: #ffe6e6;">🔴 {escaped}</span><br>')
                    elif line.startswith("@@"):
                        lines.append(f'<span style="color: blue; font-weight: bold;">{escaped}</span><br>')
                    else:
                        lines.append(f'{escaped}<br>')
                lines.append("\n</details>\n")
        
        return "\n".join(lines)
    
    def _export_html(self):
        """Export the comparison results to an HTML file with full styling."""
        if not self.comparisons:
            messagebox.showwarning("Warning", "No comparison results to export. Please compare PDFs first.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save HTML Report",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
            initialfile=f"pdf_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        
        if not filepath:
            return
        
        try:
            summary = self.comparer.get_summary()
            metadata = self.comparer.get_metadata_comparison()
            
            html_content = self._generate_html(summary, metadata)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            messagebox.showinfo("Success", f"Report exported to:\n{filepath}")
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def _generate_html(self, summary: dict, metadata: dict) -> str:
        """Generate HTML content with styled diff."""
        meta1 = metadata.get("pdf1", {})
        meta2 = metadata.get("pdf2", {})
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Comparison Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        h2 {{ color: #007acc; margin-top: 30px; }}
        h3 {{ color: #555; }}
        .summary-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }}
        .identical {{ color: green; font-weight: bold; font-size: 1.2em; }}
        .different {{ color: red; font-weight: bold; font-size: 1.2em; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #007acc; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .diff-block {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: 'Consolas', 'Monaco', monospace; overflow-x: auto; margin: 10px 0; }}
        .diff-added {{ color: #4ec9b0; background: rgba(78, 201, 176, 0.1); display: block; }}
        .diff-removed {{ color: #f14c4c; background: rgba(241, 76, 76, 0.1); display: block; }}
        .diff-header {{ color: #569cd6; font-weight: bold; display: block; }}
        .page-status {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 0.9em; }}
        .status-identical {{ background: #d4edda; color: #155724; }}
        .status-different {{ background: #f8d7da; color: #721c24; }}
        .timestamp {{ color: #888; font-style: italic; }}
    </style>
</head>
<body>
    <h1>📄 PDF Comparison Report</h1>
    <p class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary-box">
        <h2>📊 Summary</h2>
        <p class="{"identical" if summary.get("files_identical") else "different"}">
            {"✅ THE FILES ARE IDENTICAL" if summary.get("files_identical") else "❌ THE FILES ARE DIFFERENT"}
        </p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Pages in PDF 1</td><td>{summary.get('total_pages_pdf1', 0)}</td></tr>
            <tr><td>Pages in PDF 2</td><td>{summary.get('total_pages_pdf2', 0)}</td></tr>
            <tr><td>Identical Pages</td><td>{summary.get('identical_pages', 0)}</td></tr>
            <tr><td>Different Pages</td><td>{summary.get('different_pages', 0)}</td></tr>
            <tr><td>Average Similarity</td><td>{summary.get('average_similarity', 0):.1f}%</td></tr>
        </table>
    </div>
    
    <div class="summary-box">
        <h2>📁 File Information</h2>
        <table>
            <tr><th>Property</th><th>PDF 1</th><th>PDF 2</th></tr>
            <tr><td>Filename</td><td><code>{os.path.basename(self.pdf1_path)}</code></td><td><code>{os.path.basename(self.pdf2_path)}</code></td></tr>
            <tr><td>Size</td><td>{os.path.getsize(self.pdf1_path) / 1024:.1f} KB</td><td>{os.path.getsize(self.pdf2_path) / 1024:.1f} KB</td></tr>
            <tr><td>Title</td><td>{meta1.get('Title', 'N/A')}</td><td>{meta2.get('Title', 'N/A')}</td></tr>
            <tr><td>Author</td><td>{meta1.get('Author', 'N/A')}</td><td>{meta2.get('Author', 'N/A')}</td></tr>
        </table>
    </div>
    
    <div class="summary-box">
        <h2>📄 Page-by-Page Results</h2>
        <table>
            <tr><th>Page</th><th>Similarity</th><th>Status</th></tr>
'''
        
        for comp in self.comparisons:
            status_class = "status-identical" if comp["identical"] else "status-different"
            status_text = "✅ Identical" if comp["identical"] else "❌ Different"
            html += f'''            <tr>
                <td>Page {comp['page']}</td>
                <td>{comp['similarity']:.1f}%</td>
                <td><span class="page-status {status_class}">{status_text}</span></td>
            </tr>
'''
        
        html += '''        </table>
    </div>
    
    <div class="summary-box">
        <h2>🔍 Detailed Differences</h2>
        <p><strong>Legend:</strong> 
            <span class="diff-added">+ Added in PDF 2</span> 
            <span class="diff-removed">- Removed from PDF 1</span>
        </p>
'''
        
        for comp in self.comparisons:
            html += f'''        <h3>Page {comp['page']} (Similarity: {comp['similarity']:.1f}%)</h3>
'''
            if comp["identical"]:
                html += '''        <p><em>Pages are identical</em></p>
'''
            else:
                html += '''        <div class="diff-block">
'''
                for line in comp["diff"]:
                    escaped = line.replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                    if line.startswith("+") and not line.startswith("+++"):
                        html += f'            <span class="diff-added">{escaped}</span>\n'
                    elif line.startswith("-") and not line.startswith("---"):
                        html += f'            <span class="diff-removed">{escaped}</span>\n'
                    elif line.startswith("@@"):
                        html += f'            <span class="diff-header">{escaped}</span>\n'
                    else:
                        html += f'            <span>{escaped}</span>\n'
                html += '''        </div>
'''
        
        html += '''    </div>
</body>
</html>'''
        
        return html
            
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def compare_pdfs(pdf1_path: str, pdf2_path: str) -> dict:
    """
    Compare two PDF files and return comparison results.
    
    Args:
        pdf1_path: Path to the first PDF file
        pdf2_path: Path to the second PDF file
        
    Returns:
        Dictionary containing comparison results with keys:
        - summary: Overall comparison summary
        - metadata: Metadata comparison
        - pages: Page-by-page comparison results
    """
    comparer = PDFComparer(pdf1_path, pdf2_path)
    success, message = comparer.load_pdfs()
    
    if not success:
        raise ValueError(message)
    
    return {
        "summary": comparer.get_summary(),
        "metadata": comparer.get_metadata_comparison(),
        "pages": comparer.compare_text(),
    }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare two PDF files")
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")
    parser.add_argument("pdf1", nargs="?", help="First PDF file")
    parser.add_argument("pdf2", nargs="?", help="Second PDF file")
    
    args = parser.parse_args()
    
    if args.gui or (not args.pdf1 and not args.pdf2):
        # Launch GUI mode
        app = PDFCompareGUI()
        app.run()
    else:
        # Command line mode
        if not args.pdf1 or not args.pdf2:
            parser.error("Both PDF files are required in command-line mode")
        
        try:
            results = compare_pdfs(args.pdf1, args.pdf2)
            summary = results["summary"]
            
            print("\n" + "=" * 50)
            print("PDF COMPARISON RESULTS")
            print("=" * 50)
            print(f"\nFiles identical: {'Yes' if summary['files_identical'] else 'No'}")
            print(f"Pages in PDF 1: {summary['total_pages_pdf1']}")
            print(f"Pages in PDF 2: {summary['total_pages_pdf2']}")
            print(f"Identical pages: {summary['identical_pages']}")
            print(f"Different pages: {summary['different_pages']}")
            print(f"Average similarity: {summary['average_similarity']:.1f}%")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
