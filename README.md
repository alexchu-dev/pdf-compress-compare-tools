# PDF Tools

These PDF Tools are created using vibe coding with Claude Opus 4.5.

Don't want to pay for PDF compression and comparison? Scared of downloading free tools with malware? Follow this guide and build your own PDF compress/ compare tool with Python for both Windows and Mac OS platform.

## Features

### PDF Compression
- **GUI Interface**: User-friendly graphical interface for compression
- **Multiple compression backends**: Uses Ghostscript for best compression, falls back to PyPDF
- **Quality presets**: Choose from screen, ebook, printer, or prepress quality
- **Batch processing**: Compress multiple PDF files at once
- **Replace mode**: Option to replace original files with compressed versions
- **Progress tracking**: Real-time progress bar and detailed logs

### PDF Comparison
- **GUI Interface**: User-friendly graphical interface for comparing PDFs
- **Text comparison**: Page-by-page text extraction and diff analysis
- **Similarity scoring**: Percentage-based similarity for each page
- **Multiple views**: Summary, side-by-side, and unified diff views
- **Export reports**: Export comparison results to Markdown or HTML with color-coded diffs

## Installation

1. Install the Python dependencies:

```bash
pip install pypdf
```

2. For best compression results, install Ghostscript:

**macOS (Homebrew):**
```bash
brew install ghostscript
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ghostscript
```

**Windows:**
Download from https://ghostscript.com/releases/gsdnld.html

## Usage

### GUI Mode (Recommended for most users)

Launch the graphical interface:
```bash
python compress_pdf.py
```

Or explicitly:
```bash
python compress_pdf.py --gui
```

The GUI allows you to:
- Add multiple files or entire folders
- Choose quality presets with radio buttons
- See real-time progress and compression statistics
- View detailed logs for each file

### Command Line Usage

#### Basic usage

Compress a single PDF (creates `filename_compressed.pdf`):
```bash
python compress_pdf.py input.pdf
```

### Specify output file

```bash
python compress_pdf.py input.pdf -o output.pdf
```

### Quality settings

| Quality   | DPI | Use case                          |
|-----------|-----|-----------------------------------|
| screen    | 72  | Smallest size, screen viewing     |
| ebook     | 150 | Good balance (default)            |
| printer   | 300 | High quality printing             |
| prepress  | 300 | Highest quality, color preserving |

```bash
python compress_pdf.py input.pdf -q screen    # Maximum compression
python compress_pdf.py input.pdf -q printer   # High quality
```

### Batch processing

Compress multiple files:
```bash
python compress_pdf.py file1.pdf file2.pdf file3.pdf
```

### Replace original files

```bash
python compress_pdf.py input.pdf -r
```

### Force PyPDF (skip Ghostscript)

```bash
python compress_pdf.py input.pdf --pypdf
```

## Examples

```bash
# Compress with maximum compression
python compress_pdf.py large_document.pdf -q screen

# Compress for printing
python compress_pdf.py presentation.pdf -q printer -o presentation_print.pdf

# Batch compress all PDFs in current directory
python compress_pdf.py *.pdf

# Replace originals with compressed versions
python compress_pdf.py *.pdf -r -q ebook
```

## How it works

1. **Ghostscript** (preferred): Uses industry-standard PDF processing with configurable quality settings
2. **PyPDF** (fallback): Compresses content streams and removes redundant objects

Ghostscript typically provides better compression ratios, especially for PDFs with images.

---

## PDF Comparison Tool

### Usage

#### GUI Mode (default)

Launch the graphical interface:
```bash
python compare_pdf.py
```

Or explicitly:
```bash
python compare_pdf.py --gui
```

#### Command Line Mode

Compare two PDFs and print results:
```bash
python compare_pdf.py file1.pdf file2.pdf
```

#### Programmatic Usage

```python
from compare_pdf import compare_pdfs

results = compare_pdfs("file1.pdf", "file2.pdf")
print(f"Files identical: {results['summary']['files_identical']}")
print(f"Average similarity: {results['summary']['average_similarity']:.1f}%")
```

### GUI Features

| Tab | Description |
|-----|-------------|
| **Summary** | Overview of comparison results, metadata, and per-page similarity |
| **Page Comparison** | Side-by-side text view with navigation |
| **Diff View** | Unified diff with color-coded additions/removals |

### Export Options

- **Export to Markdown**: Creates a `.md` file with diff code blocks and collapsible colored sections
- **Export to HTML**: Creates a styled HTML report viewable in any browser

---

## Building Standalone Executables

You can create standalone executables for users who don't have Python installed.

### Requirements

```bash
pip install pyinstaller
```

### Build Commands

Build both tools at once:
```bash
python build.py
```

Or build individually:
```bash
python build.py --compress   # Build only PDFCompress
python build.py --compare    # Build only PDFCompare
```

### Output Files

| Platform | PDFCompress | PDFCompare |
|----------|-------------|------------|
| **macOS** | `dist/PDFCompress.app` | `dist/PDFCompare.app` |
| **Windows** | `dist/PDFCompress.exe` | `dist/PDFCompare.exe` |
| **Linux** | `dist/pdfcompress` | `dist/pdfcompare` |

### Creating DMG Installers (macOS)

To create `.dmg` installers for easy distribution:

```bash
# Install create-dmg
brew install create-dmg

# Create DMG files
create-dmg dist/PDFCompress.app dist/
create-dmg dist/PDFCompare.app dist/
```

### Cross-Platform Notes

- PyInstaller builds for the **current OS only**
- To create a Windows `.exe`, run the build on a Windows machine
- To create a macOS `.app`, run the build on a Mac
- Consider using GitHub Actions for automated multi-platform builds

---

## License

MIT License
