# Document Extraction Comparison Tool

This tool compares document extraction performance between **Unstructured** and **AzureAIDocumentIntelligenceLoader** libraries.

## Installation

### Install Required Libraries

```bash
# For Unstructured
pip install unstructured
pip install "unstructured[pdf]"  # For PDF support
pip install "unstructured[docx]"  # For DOCX support

# For Azure Document Intelligence
pip install langchain-community
pip install azure-ai-documentintelligence
```

### Azure Document Intelligence Setup

1. Create an Azure Document Intelligence resource in Azure Portal
2. Get your endpoint and API key
3. Set environment variables:

```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"
```

Or on Windows:
```cmd
set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
set AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key
```

## Usage

### Basic Usage

```bash
python compare_extractors.py /path/to/documents/folder
```

### Specify Output File

```bash
python compare_extractors.py /path/to/documents/folder --output my_report.json
```

### Provide Azure Credentials via CLI

```bash
python compare_extractors.py /path/to/documents/folder \
    --azure-endpoint "https://your-resource.cognitiveservices.azure.com/" \
    --azure-key "your-api-key"
```

## Output

The tool generates:

1. **Console Output**: Real-time progress and summary comparison
2. **JSON Report**: Detailed results saved to file (default: `comparison_report.json`)

### Sample Output

```
================================================================================
Document Extraction Comparison
================================================================================
Folder: ./test_documents
Files found: 5
================================================================================

[1/5] Processing: document1.pdf
  → Unstructured... ✓ (1.23s)
  → Azure DI... ✓ (2.45s)

[2/5] Processing: report.docx
  → Unstructured... ✓ (0.87s)
  → Azure DI... ✓ (1.92s)

================================================================================
COMPARISON SUMMARY
================================================================================

Unstructured Library:
  Success Rate: 100.0% (5/5)
  Avg Extraction Time: 1.15s
  Avg Text Length: 8543 chars

Azure Document Intelligence:
  Success Rate: 100.0% (5/5)
  Avg Extraction Time: 2.18s
  Avg Text Length: 8621 chars

================================================================================
WINNER: UNSTRUCTURED
Reason: Faster average extraction time (1.15s vs 2.18s)
================================================================================
```

## Report Format

The JSON report contains:

```json
{
  "timestamp": "2025-10-09T10:30:00",
  "total_files": 5,
  "unstructured_results": [
    {
      "filename": "document1.pdf",
      "file_size_bytes": 245632,
      "extractor": "unstructured",
      "success": true,
      "extraction_time_seconds": 1.23,
      "text_length": 12543,
      "chunk_count": 45,
      "metadata": {...}
    }
  ],
  "azure_di_results": [...],
  "summary": {
    "unstructured": {...},
    "azure_di": {...},
    "winner": "unstructured",
    "winner_reason": "Faster average extraction time"
  }
}
```

## Supported File Formats

- PDF (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- PowerPoint (`.pptx`)
- Text (`.txt`)
- HTML (`.html`)
- Markdown (`.md`)

## Troubleshooting

### "Unstructured library not available"

Install unstructured with appropriate extras:
```bash
pip install "unstructured[all-docs]"
```

### "Azure DI not available: Missing endpoint or key"

Ensure environment variables are set or pass credentials via CLI arguments.

### Import Errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt  # If you have a requirements file
```

Or install individually:
```bash
pip install unstructured langchain-community azure-ai-documentintelligence
```

## Performance Considerations

- **Unstructured**: Generally faster for local processing, no API calls required
- **Azure DI**: Requires network calls, may be slower but provides advanced features like layout analysis and table extraction
- **Cost**: Unstructured is free (open-source), Azure DI has usage-based pricing

## Integration with RAG Pipeline

Both extractors can be integrated into the RAG ingestion pipeline. See `docs/DESIGN.md` for the comparison table and recommendations.
