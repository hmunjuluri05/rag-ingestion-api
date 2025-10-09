# Test Documents

This folder contains **10 sample documents** in various formats for testing document extraction tools.

## File Inventory

### Markdown Files (2)
- `01_simple.md` - Basic markdown with headings, lists, code blocks, and tables
- `02_technical.md` - Technical documentation with code examples and YAML configs

### HTML Files (2)
- `03_simple_page.html` - Simple webpage with tables and styled content
- `04_invoice.html` - Invoice document with complex table structure

### Text Files (2)
- `05_simple.txt` - Plain text document with sections
- `06_log_file.txt` - Application log file with timestamps and events

### DOCX Files (2)
- `07_simple.docx` - Word document with headings, lists, and tables
- `08_technical_report.docx` - Technical report with formatted content

### PDF Files (2)
- `09_simple.pdf` - PDF with text, paragraphs, and tables
- `10_technical.pdf` - Benchmark report with complex layout and tables

## Usage

These documents are designed to test:
- Text extraction quality
- Table parsing capabilities
- Layout understanding
- Structure preservation
- Format-specific features

## Running the Comparison Tool

To compare extraction libraries on these documents:

```bash
python compare_extractors.py test_documents --output test_results.json
```

## Document Characteristics

| File | Format | Size | Complexity | Key Features |
|------|--------|------|------------|--------------|
| 01_simple.md | Markdown | 680 B | Low | Basic formatting |
| 02_technical.md | Markdown | 1.8 KB | Medium | Code blocks, tables |
| 03_simple_page.html | HTML | 1.9 KB | Low | Styled elements |
| 04_invoice.html | HTML | 3.3 KB | Medium | Complex tables |
| 05_simple.txt | Text | 870 B | Low | Plain text |
| 06_log_file.txt | Text | 1.7 KB | Low | Structured logs |
| 07_simple.docx | DOCX | 37 KB | Medium | Lists, tables |
| 08_technical_report.docx | DOCX | 37 KB | High | Formatted report |
| 09_simple.pdf | PDF | 2.5 KB | Medium | Text and tables |
| 10_technical.pdf | PDF | 3.6 KB | High | Complex layout |

## Regenerating Documents

To regenerate all test documents:

```bash
python generate_test_docs.py
```

This will overwrite existing files with fresh versions.
