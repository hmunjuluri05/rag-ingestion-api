# RAG Ingestion API

Multi-cloud RAG (Retrieval-Augmented Generation) ingestion pipeline with document extraction, chunking, deduplication, and indexing capabilities. Supports deployment on Azure (AKS) and GCP (GKE).

## Features

- **Multi-cloud architecture** - Azure and GCP support with unified configuration
- **Advanced document extraction** - Support for PDF, DOCX, HTML, Markdown, and more
- **Smart chunking** - Recursive and semantic text splitting strategies
- **Deduplication** - MinHash and SimHash-based duplicate detection
- **Asynchronous processing** - Celery-based task queue for scalability
- **Extraction comparison tool** - Benchmark Unstructured vs Azure Document Intelligence
- **Test document generator** - Create sample documents for testing

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rag-ingetion-api

# Install dependencies with UV
uv sync

# Or with pip
pip install -e .
```

### Optional Dependencies

```bash
# Install OCR support
uv sync --extra ocr

# Install development tools
uv sync --extra dev

# Install everything
uv sync --extra all
```

## Usage

### 1. Generate Test Documents

Create sample documents for testing:

```bash
# Using UV
uv run generate-test-docs

# Or directly
python src/rag_ingetion_api/generate_test_docs.py
```

This creates 10 test documents in `test_documents/`:
- 2 Markdown files
- 2 HTML files
- 2 Text files
- 2 DOCX files
- 2 PDF files

### 2. Compare Document Extractors

Benchmark **Unstructured** vs **Azure Document Intelligence**:

```bash
# Using UV (recommended)
uv run compare-extractors test_documents

# Specify output file
uv run compare-extractors test_documents --output results.json

# With Azure credentials
uv run compare-extractors test_documents \
    --azure-endpoint "https://your-resource.cognitiveservices.azure.com/" \
    --azure-key "your-api-key"
```

Or set environment variables:

```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"
uv run compare-extractors test_documents
```

The tool will:
- Extract documents using both libraries
- Measure extraction time and success rate
- Compare text quality and chunk counts
- Generate a detailed JSON report
- Display summary comparison

### 3. Review Results

Example output:

```
================================================================================
COMPARISON SUMMARY
================================================================================

Unstructured Library:
  Success Rate: 100.0% (10/10)
  Avg Extraction Time: 1.15s
  Avg Text Length: 8543 chars

Azure Document Intelligence:
  Success Rate: 100.0% (10/10)
  Avg Extraction Time: 2.18s
  Avg Text Length: 8621 chars

================================================================================
WINNER: UNSTRUCTURED
Reason: Faster average extraction time (1.15s vs 2.18s)
================================================================================
```

## Project Structure

```
rag-ingetion-api/
├── src/
│   └── rag_ingetion_api/
│       ├── __init__.py
│       ├── compare_extractors.py    # Extraction comparison tool
│       └── generate_test_docs.py    # Test document generator
├── test_documents/                   # Generated test files
├── docs/
│   └── DESIGN.md                    # Complete design documentation
├── pyproject.toml                   # UV/pip dependencies
├── uv.lock                          # Dependency lock file
├── README.md                        # This file
└── EXTRACTOR_COMPARISON.md          # Detailed comparison guide
```

## Documentation

- **[DESIGN.md](docs/DESIGN.md)** - Complete system architecture and design
  - Multi-cloud deployment strategies
  - Component architecture (Extract, Chunk, Dedup)
  - Technology stack comparison
  - **Document extraction library comparison table**
  - Implementation patterns and best practices

- **[EXTRACTOR_COMPARISON.md](EXTRACTOR_COMPARISON.md)** - Extraction tool usage guide
  - Installation and setup
  - Usage examples
  - Output format
  - Troubleshooting

## Extraction Library Comparison

| Feature | Unstructured | Azure Document Intelligence |
|---------|-------------|----------------------------|
| **Cost** | Free (open-source) | Pay-per-page API usage |
| **Speed** | Fast (~1.3s) | Moderate (~2-3s) |
| **Deployment** | Local | Cloud API |
| **OCR** | Tesseract (optional) | Built-in high-quality |
| **Table Extraction** | Basic | Advanced |
| **Handwriting** | Limited | AI-powered |
| **Privacy** | Full control | Data to Azure |

See [DESIGN.md](docs/DESIGN.md#document-extraction-library-comparison) for the complete comparison table.

## Technology Stack

### Core Dependencies

- **API**: FastAPI, Uvicorn, Pydantic
- **Task Queue**: Celery, Flower, Redis
- **Cloud Storage**: Azure Blob Storage, Google Cloud Storage
- **Document Extraction**: Unstructured, Azure AI Document Intelligence
- **Text Processing**: LangChain, tiktoken, markdownify
- **Deduplication**: datasketch (MinHash/SimHash)

### Development Tools

- **Package Manager**: UV
- **Code Quality**: Black, Ruff, mypy
- **Testing**: pytest, pytest-asyncio, pytest-cov

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Type checking
uv run mypy src/
```

### Adding Dependencies

```bash
# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update dependencies
uv lock --upgrade
```

## Environment Variables

```bash
# Azure Document Intelligence (optional)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"

# Azure Blob Storage (for production)
AZURE_STORAGE_ACCOUNT="your-storage-account"
AZURE_STORAGE_KEY="your-storage-key"

# GCP Storage (for production)
GCP_PROJECT_ID="your-project-id"
GCP_STORAGE_BUCKET="your-bucket-name"

# Redis/Celery (for production)
REDIS_HOST="your-redis-host"
REDIS_PORT="6379"
```

## Deployment

See [DESIGN.md](docs/DESIGN.md) for detailed deployment instructions:

- Multi-cloud Kubernetes setup (AKS/GKE)
- Celery worker configuration
- Auto-scaling strategies
- Monitoring and observability

## Roadmap

- [ ] Implement FastAPI endpoints for document ingestion
- [ ] Set up Celery workers for extraction, chunking, deduplication
- [ ] Add embedding generation with OpenAI/Azure OpenAI
- [ ] Implement vector database integration (Pinecone/Weaviate)
- [ ] Add Kubernetes deployment manifests
- [ ] Set up Prometheus/Grafana monitoring
- [ ] Add authentication and rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Format and lint code (`uv run black . && uv run ruff check .`)
5. Run tests (`uv run pytest`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
