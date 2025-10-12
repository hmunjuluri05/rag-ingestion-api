# RAG Ingestion API - Enhanced v1/ingestion Implementation Stories

**Project**: RAG Ingestion API v1 Enhancement
**Epic**: Document Processing Pipeline with Enhanced v1/ingestion Endpoint
**Sprint Duration**: 2 weeks
**Context**: Enhancing existing v1/ingestion API on AKS and GKE with hybrid storage and unified worker architecture

**Architecture**: One story per layer, with all configuration and dependencies bundled

---

## Story 1: Object Storage Layer - Azure Blob and GCS Setup

**Story Title**: Setup Object Storage providers (Azure Blob and GCS) for document storage

**Story Points**: 5

**Description**:
Setup Object Storage layer for permanent document storage using Azure Blob Storage and GCS. Includes storage provider interface, implementations for both cloud providers, factory pattern for provider selection, and configuration. Documents are stored permanently in Object Storage as part of the hybrid storage architecture (74% cost savings vs MongoDB-only). MongoDB chunk storage already exists.

**Acceptance Criteria**:

**1. Configuration**:
- [ ] Update existing Settings class with:
  - Object Storage config: `OBJECT_STORAGE_PROVIDER` (azure_blob/gcs)
  - Azure Blob: `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_KEY`, `AZURE_STORAGE_CONTAINER`
  - GCS: `GCP_PROJECT_ID`, `GCP_STORAGE_BUCKET`, `GCP_CREDENTIALS_PATH`
  - Note: MongoDB connection settings already exist
- [ ] Update `.env.example` with new Object Storage variables
- [ ] Configuration validates on application startup

**2. Object Storage Implementation**:
- [ ] Create `src/rag_ingestion_api/services/storage/object_storage.py`:
  - `IObjectStorageProvider` interface with methods:
    - `upload_document(job_id: str, filename: str, content: bytes) -> str` (returns path)
    - `download_document(file_path: str) -> bytes`
    - `delete_document(file_path: str) -> None`
  - `AzureBlobStorageProvider` implementation
  - `GCSStorageProvider` implementation
  - `ObjectStorageFactory` returns provider based on `OBJECT_STORAGE_PROVIDER` config
  - Path structure: `jobs/{job_id}/document.*` (permanent storage)

**3. Cloud Storage Bucket Setup**:
- [ ] Create Azure Blob Storage container (via Azure Portal or CLI)
- [ ] Create GCS bucket (via GCP Console or gcloud CLI)
- [ ] Configure access credentials for both providers
- [ ] Document bucket naming conventions and retention policies

**4. Testing**:
- [ ] Unit tests with mocked Azure SDK and GCS SDK
- [ ] Integration tests with real Azure Blob Storage and GCS
- [ ] Test coverage >80%
- [ ] Error handling for cloud API failures (connection, authentication, upload/download)

**5. Documentation**:
- [ ] Logging for all storage operations
- [ ] Configuration documentation
- [ ] Cloud provider setup guide (Azure Blob and GCS bucket creation)
- [ ] Architecture documentation (hybrid storage benefits)

**Dependencies**: None

---

## Story 2: Extraction Layer - Document Extraction with Unstructured Library

**Story Title**: Implement complete extraction layer with Unstructured library (automatic cleaning included)

**Story Points**: 13

**Description**:
Implement complete extraction layer using Unstructured library with automatic document cleaning and normalization. Includes Pydantic models for extraction config/results, configuration, extractor implementation, and factory pattern. Supports multiple document formats and returns cleaned, normalized text ready for chunking.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/extraction.py`:
  - `ExtractionLibrary` enum (UNSTRUCTURED) - only Unstructured for MVP
  - `ExtractionConfig` model with `library` field (default: "unstructured")
  - `ExtractionResult` model (text, metadata, warnings, extraction_time)
  - `ExtractionMetadata` model (page_count, file_size, format, etc.)
  - All models have `extra = "forbid"` in Config
  - Note: No `CleaningConfig` - cleaning is automatic in extraction

**2. Configuration**:
- [ ] Update existing Settings class with:
  - `EXTRACTION_DEFAULT_LIBRARY` (default: "unstructured")
  - `EXTRACTION_TIMEOUT_SECONDS` (default: 300)
  - `EXTRACTION_MAX_FILE_SIZE_MB` (default: 100)
- [ ] Update `.env.example` with extraction settings
- [ ] Configuration validates on application startup

**3. Extractor Interface**:
- [ ] Create `src/rag_ingestion_api/services/extraction/base.py`:
  - `IExtractor` ABC with methods:
    - `extract(source: bytes, filename: str, config: ExtractionConfig) -> ExtractionResult`
    - `supports_format(file_extension: str) -> bool`

**4. Unstructured Implementation**:
- [ ] Create `src/rag_ingestion_api/services/extraction/unstructured_extractor.py`:
  - `UnstructuredExtractor` implementation
  - Supports: .pdf, .docx, .doc, .pptx, .html, .htm, .md, .txt
  - Extracts text with automatic cleaning (7 cleaning steps built-in):
    - Whitespace normalization, character cleanup, layout flattening
    - Dehyphenation, section merging, HTML tag removal
    - Metadata enrichment (filename, page numbers, coordinates, category)
  - Returns `ExtractionResult` with cleaned text and metadata
  - File format detection from filename extension
  - Error handling for unsupported/corrupted/empty documents

**5. Factory Pattern**:
- [ ] Create `src/rag_ingestion_api/services/extraction/factory.py`:
  - `ExtractorFactory` class
  - `create_extractor(library: ExtractionLibrary) -> IExtractor` method
  - Returns `UnstructuredExtractor` for `ExtractionLibrary.UNSTRUCTURED`
  - Uses dependency injection for configuration

**6. Testing**:
- [ ] Unit tests with sample documents for each format
- [ ] Integration tests with real documents
- [ ] Performance tests (extraction + cleaning time per document)
- [ ] Error scenario tests (unsupported formats, corrupted files, empty documents)
- [ ] Test coverage >80%

**7. Documentation**:
- [ ] Supported formats documented
- [ ] Automatic cleaning steps documented
- [ ] Performance logging implementation
- [ ] Configuration guide

**Dependencies**: Story 1 (Storage Layer)

---

## Story 3: Chunking Layer - Text Chunking with Multiple Strategies

**Story Title**: Implement complete chunking layer with multiple strategies and factory pattern

**Story Points**: 12

**Description**:
Implement complete chunking layer with recursive, semantic, sentence, and paragraph strategies. Includes Pydantic models for chunks and chunking config, all chunker implementations, and factory pattern for single strategy selection. Chunks are designed for storage in MongoDB with rich metadata.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/storage.py`:
  - `Chunk` model (id, text, metadata, position, job_id, created_at)
  - `ChunkMetadata` model (source document info, page_number, position, total_chunks)
  - All models have `extra = "forbid"` in Config
  - Field validations with proper types
- [ ] Create `src/rag_ingestion_api/models/chunking.py`:
  - `ChunkingStrategy` enum (RECURSIVE, SEMANTIC, SENTENCE, PARAGRAPH)
  - `ChunkingConfig` model with:
    - `strategy: str` (single selection, not list)
    - `chunk_size: int = 512` (ge=1, le=8192)
    - `chunk_overlap: int = 50` (ge=0)
  - All models have `extra = "forbid"` in Config
  - Field validations with ranges

**2. Configuration**:
- [ ] Update existing Settings class with:
  - `CHUNKING_DEFAULT_STRATEGY` (default: "recursive")
  - `CHUNKING_DEFAULT_SIZE` (default: 512)
  - `CHUNKING_DEFAULT_OVERLAP` (default: 50)
  - `CHUNKING_MAX_CHUNK_SIZE` (default: 8192)
- [ ] Update `.env.example` with chunking settings
- [ ] Configuration validates on application startup

**3. Chunker Interface**:
- [ ] Create `src/rag_ingestion_api/services/chunking/base.py`:
  - `IChunker` ABC with `chunk(text: str, config: ChunkingConfig, job_id: str) -> List[Chunk]`

**4. Chunker Implementations**:
- [ ] Create `src/rag_ingestion_api/services/chunking/recursive_chunker.py`:
  - `RecursiveChunker` using LangChain `RecursiveCharacterTextSplitter`
  - Respects `chunk_size` and `chunk_overlap` from config
  - Generates chunk IDs: `{job_id}_chunk_{position:04d}`
  - Each `Chunk` includes: id, text, metadata (position, total_chunks, source document info), position
- [ ] Create `src/rag_ingestion_api/services/chunking/semantic_chunker.py`:
  - Context-aware splitting using semantic similarity
- [ ] Create `src/rag_ingestion_api/services/chunking/sentence_chunker.py`:
  - Split by sentence boundaries using NLTK or spaCy
- [ ] Create `src/rag_ingestion_api/services/chunking/paragraph_chunker.py`:
  - Split by paragraph boundaries (double newlines)

**5. Factory Pattern**:
- [ ] Create `src/rag_ingestion_api/services/chunking/factory.py`:
  - `ChunkerFactory.create_chunker(strategy: str) -> IChunker`
  - Strategy options: "recursive", "semantic", "sentence", "paragraph"
  - Default to "recursive" if strategy not recognized
  - Note: Only ONE strategy selected per job via API config

**6. Edge Cases**:
- [ ] Empty text → return empty list
- [ ] Text smaller than chunk_size → return single chunk
- [ ] Very large documents (>10MB) → process in batches

**7. Testing**:
- [ ] Unit tests for each chunking strategy
- [ ] Comparison tests showing output differences between strategies
- [ ] Performance tests with large documents
- [ ] Edge case tests
- [ ] Test coverage >80%

**8. Documentation**:
- [ ] When to use each strategy
- [ ] Chunk size recommendations
- [ ] Performance characteristics

**Dependencies**: None (Chunk models included in this story)

---

## Story 4: Task Processing Layer - Unified Celery Ingestion Task

**Story Title**: Implement complete task processing layer with Celery configuration and unified ingestion task

**Story Points**: 13

**Description**:
Implement complete task processing layer including Celery configuration for single queue architecture and unified ingestion task that performs atomic pipeline (extract → chunk → store). Includes job status models, Redis-based job manager, Celery configuration, and the main ingestion task with transaction support.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/jobs.py`:
  - `JobStatus` enum (QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED)
  - `JobResponse` model (job_id, status, submitted_at, filename)
  - `JobStatusResponse` model (job_id, status, progress, stats)
  - `JobProgress` model (current_step, percent_complete)
  - `JobStats` model (extraction_time, chunks_created, file_size, document_storage_path)
  - All models have `extra = "forbid"` in Config

**2. Configuration**:
- [ ] Update existing Settings class with:
  - Celery config: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (Redis already exists)
  - Task config: `TASK_SOFT_TIMEOUT` (default: 900s), `TASK_HARD_TIMEOUT` (default: 1200s)
  - Retry config: `TASK_MAX_RETRIES` (default: 3), `TASK_RETRY_BACKOFF` (default: 4s)
  - Job config: `JOB_STATUS_TTL_DAYS` (default: 7)
- [ ] Update `.env.example` with task settings
- [ ] Configuration validates on application startup

**3. MongoDB Chunk Storage Implementation**:
- [ ] Create `src/rag_ingestion_api/services/storage/chunk_storage.py`:
  - `IChunkStore` interface with methods:
    - `store_chunks(job_id: str, chunks: List[Chunk]) -> int` (returns count)
    - `get_chunks(job_id: str, filters: Optional[Dict]) -> List[Chunk]`
    - `delete_chunks(job_id: str) -> int`
  - `MongoDBChunkStore` implementation with:
    - Connection to existing MongoDB infrastructure
    - Stores chunks with indexes on job_id, metadata fields, created_at
    - Rich query support for RAG retrieval
    - Transaction support for atomic operations

**4. Job Status Manager**:
- [ ] Create `src/rag_ingestion_api/services/job_manager.py`:
  - `JobStatusManager` class
  - `create_job(job_id, filename, config) -> JobResponse` - stores initial state in Redis
  - `update_status(job_id, status, progress, stats)` - updates job in Redis
  - `get_job(job_id) -> JobStatusResponse` - retrieves job info
  - `delete_job(job_id)` - removes job from Redis
  - Job data structure in Redis: Key `job:{job_id}`, Value: JSON with all job info
  - Jobs expire after TTL (configurable, default 7 days)
  - Error handling for Redis connection failures (graceful degradation)
  - Note: Redis serves dual purpose as Celery broker AND job status store

**5. Celery Configuration**:
- [ ] Update Celery app configuration with:
  - Single queue: `ingest_queue`
  - Task routing: all ingestion tasks → ingest_queue
  - Default retry policy: 3 retries, exponential backoff (base=4s, max=300s)
  - Task time limits: soft=900s, hard=1200s (longer for atomic operation)
- [ ] Base task class for pipeline tasks with:
  - Automatic status updates to Redis (job status tracking)
  - Error logging with full context
  - Standardized exception handling
  - Atomic transaction support (rollback on failure)
- [ ] Worker startup configuration:
  - Unified ingestion workers (Celery) listen to `ingest_queue` - replicas: 2-10
  - Workers handle complete pipeline (extract → chunk → store)
- [ ] Celery routes configuration file

**6. Unified Ingestion Task**:
- [ ] Create `src/rag_ingestion_api/tasks/ingest_task.py`:
  - `ingest_document_task(job_id: str, file_path: str, config: dict)`
  - Downloads document from Object Storage (Azure Blob or GCS)
  - Uses `ExtractorFactory` to get extractor based on config
  - Extracts text from document (automatic cleaning included by Unstructured)
  - Uses `ChunkerFactory` to get chunker based on config (single strategy selection)
  - Splits text into chunks with metadata (position, total_chunks, source document info)
  - Stores chunks to MongoDB using `MongoDBChunkStore` with indexes
  - Updates job status: queued → processing → completed
  - Sends webhook notification if `callback_url` provided
  - Updates job status to "failed" with error details on failure
  - Task routed to `ingest_queue`
  - Atomic operation: entire pipeline succeeds or fails together
  - Progress tracking: update percent_complete in Redis (can track internal stages)
  - Webhook payload includes: job_id, status, stats (chunks_created, total_time, extraction_time)
  - MongoDB indexes created: job_id, metadata fields, created_at
  - Transaction support: rollback on failure (clean up partial chunks if MongoDB write fails)

**7. Error Handling**:
- [ ] Object Storage download failures (retry 3x)
- [ ] Extraction failures (mark failed, no retry)
- [ ] Chunking failures (mark failed, no retry)
- [ ] MongoDB storage failures (retry 3x with exponential backoff)
- [ ] Performance metrics logged (extraction time, chunking time, total time)

**8. Testing**:
- [ ] Unit tests with mocked Object Storage, extractors, chunkers, and MongoDB
- [ ] Integration tests with real Celery, Redis, Object Storage, and MongoDB
- [ ] Test atomic transaction behavior (rollback on failure)
- [ ] Test webhook notifications
- [ ] Test coverage >80%

**9. Documentation**:
- [ ] Running workers locally for v1/ingestion
- [ ] Task architecture and atomic processing
- [ ] Error handling and retry logic

**Dependencies**: Story 1 (Object Storage), Story 2 (Extraction Layer), Story 3 (Chunking Layer with Chunk models)

---

## Story 5: API Layer - FastAPI Endpoints for Job Management

**Story Title**: Implement complete API layer with job submission and status query endpoints

**Story Points**: 12

**Description**:
Implement complete REST API layer for v1/ingestion including POST /v1/ingestion for job submission and GET /v1/ingestion/{knowledge_ingestion_task_id} for status queries. Includes request/response validation, file upload handling, and integration with storage and task layers.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/api.py`:
  - `IngestionConfig` model combining extraction and chunking configs
  - `JobResponse` model (job_id, status, submitted_at, filename)
  - `TaskStatusResponse` model (task_id, status, chunks)
  - `ErrorResponse` model (error_code, message, details)
  - All models have `extra = "forbid"` in Config
  - Note: No `CleaningConfig` - cleaning is automatic in extraction

**2. Configuration**:
- [ ] Update existing Settings class with:
  - `API_MAX_FILE_SIZE_MB` (default: 100)
  - `API_SUPPORTED_FORMATS` (list: [".pdf", ".docx", ".doc", ".pptx", ".html", ".htm", ".md", ".txt"])
  - `API_ENABLE_WEBHOOKS` (default: True)
- [ ] Update `.env.example` with API settings
- [ ] Configuration validates on application startup

**3. POST /v1/ingestion Endpoint**:
- [ ] Create `src/rag_ingestion_api/api/v1/ingestion.py`:
  - POST `/v1/ingestion` endpoint
  - Accepts `multipart/form-data` with fields:
    - `file`: UploadFile (required)
    - `config`: JSON string (optional, uses defaults if not provided)
    - `metadata`: JSON object (optional)
    - `callback_url`: string (optional)
  - Validates `config` with `IngestionConfig` Pydantic model (no cleaning config - automatic)
  - File size limit from config (default: 100MB)
  - Format validation from config
  - Workflow:
    - Generate unique `job_id` (UUID4)
    - Upload file to Object Storage (Azure Blob or GCS) permanently
    - Create job in Redis with status "queued" using `JobStatusManager`
    - Dispatch `ingest_document_task` to Celery (unified task for complete pipeline)
    - Return 202 Accepted with `JobResponse` (job_id, status, submitted_at, filename)
  - Error responses:
    - 400: Invalid config, missing file, unsupported format
    - 413: File too large
    - 500: Object Storage failure, queue failure

**4. GET /v1/ingestion/{knowledge_ingestion_task_id} Endpoint**:
- [ ] Add to `src/rag_ingestion_api/api/v1/ingestion.py`:
  - GET `/v1/ingestion/{knowledge_ingestion_task_id}` endpoint
  - Queries Redis/MongoDB for task status and chunks
  - Returns `TaskStatusResponse` with:
    - task_id: str
    - status: str (processing, completed, failed)
    - chunks: List[str] (array of chunk IDs)
  - Error responses:
    - 404: Task ID not found
    - 500: Redis/MongoDB connection failure

**5. Testing**:
- [ ] Unit tests with mocked Object Storage, Celery, and JobStatusManager
- [ ] Integration tests: submit job, verify task dispatched, file in Object Storage
- [ ] Request validation tests (invalid inputs)
- [ ] Test status queries with various task IDs
- [ ] Test chunks retrieval
- [ ] Test coverage >80%

**6. Documentation**:
- [ ] OpenAPI documentation auto-generated
- [ ] Request/response examples for both endpoints
- [ ] Error code documentation

**Dependencies**: Story 1 (Object Storage), Story 4 (Task Processing Layer with MongoDB chunk storage)

---

## Story 6: Testing Layer - Integration Tests and Error Handling

**Story Title**: Implement comprehensive integration tests and error handling for complete pipeline

**Story Points**: 13

**Description**:
Create comprehensive end-to-end integration tests for complete v1/ingestion pipeline and implement robust error handling with custom exceptions and retry logic. Test atomic processing, various document types, configurations, and failure scenarios.

**Acceptance Criteria**:

**1. Custom Exception Classes**:
- [ ] Create `src/rag_ingestion_api/exceptions.py`:
  - `ExtractionError` (base class for extraction failures, includes automatic cleaning)
  - `UnsupportedFormatError` (invalid file format)
  - `CorruptedFileError` (cannot parse document)
  - `ChunkingError` (chunking failure)
  - `ObjectStorageError` (Blob/GCS storage failure)
  - `MongoDBError` (MongoDB chunk storage failure)
  - Note: No `CleaningError` - cleaning is automatic in extraction step

**2. Retry Logic**:
- [ ] Implement retry logic for transient errors:
  - Object Storage failures: 3 retries with exponential backoff
  - MongoDB failures: 3 retries with exponential backoff
  - Network errors: 3 retries
  - Rate limiting: retry with backoff
- [ ] Non-retryable errors logged and job marked as failed:
  - Unsupported format, corrupted file, invalid config
- [ ] Error details stored in job status:
  - error_message, error_type, failed_at timestamp
- [ ] Atomic transaction support: rollback on failure (clean up partial chunks)

**3. Integration Tests**:
- [ ] Create `tests/integration/test_v1_ingestion.py`:
  - Test: Submit PDF → verify file in Object Storage → verify chunks in MongoDB with correct metadata
  - Test: Submit DOCX → verify atomic processing (extract + chunk + store)
  - Test: Submit HTML → verify automatic cleaning applied
  - Test: Submit with custom chunk config (single strategy) → verify chunk size respected
  - Test: Submit with callback_url → verify webhook called
  - Test: Submit invalid format → verify 400 error
  - Test: Submit oversized file → verify 413 error
  - Test: Task status query returns correct status and chunks
  - Test: Query with invalid task_id → verify 404 error
  - Test: Multiple concurrent jobs (no interference)
  - Test: Atomic failure behavior (if chunking fails, no partial chunks stored)
- [ ] Test fixtures for sample documents
- [ ] Tests verify Object Storage (Blob/GCS) contains documents
- [ ] Tests verify MongoDB contains chunks with correct indexes
- [ ] Tests run in CI/CD pipeline
- [ ] Test coverage >80% for v1/ingestion code

**4. Error Scenario Tests**:
- [ ] Unit tests for each error scenario
- [ ] Integration tests for retry behavior with Object Storage and MongoDB
- [ ] Test graceful degradation on Redis failures

**5. Documentation**:
- [ ] Running integration tests locally
- [ ] Error types and troubleshooting guide
- [ ] Retry behavior documentation

**Dependencies**: Story 5 (API Layer)

---

## Story 7: Deployment Layer - Documentation, Kubernetes, and Monitoring

**Story Title**: Complete deployment layer with API documentation, Kubernetes manifests, and monitoring

**Story Points**: 13

**Description**:
Complete deployment layer including comprehensive API documentation, Kubernetes deployment manifests for AKS/GKE with hybrid storage support, and Prometheus metrics with Grafana dashboards for monitoring the v1/ingestion pipeline.

**Acceptance Criteria**:

**1. API Documentation**:
- [ ] Update or create `docs/API_V1_INGESTION.md`:
  - Endpoint description and purpose
  - Request format with all parameters explained
  - Configuration options:
    - Extraction library selection (unstructured with automatic cleaning)
    - Chunking strategy (single selection, not list)
    - Chunk size recommendations by use case
  - Hybrid storage architecture explanation:
    - Documents stored permanently in Object Storage (Blob/GCS)
    - Chunks stored in MongoDB with indexes
    - Cost savings vs MongoDB-only approach
  - Response format and status codes
  - Error codes with troubleshooting
  - Webhook callback format and payload
- [ ] Code examples in Python and cURL:
  - Basic job submission (POST /v1/ingestion)
  - Custom configuration (single chunking strategy)
  - With metadata and callback
  - Query task status (GET /v1/ingestion/{knowledge_ingestion_task_id})
- [ ] Task lifecycle diagram (queued → processing → completed)
- [ ] Configuration best practices (no cleaning config needed, single chunking strategy)
- [ ] OpenAPI spec updated with descriptions
- [ ] README.md updated with enhanced v1/ingestion section

**2. Kubernetes Deployments**:
- [ ] Deploy enhanced v1/ingestion API code (no changes to API pod deployment configuration)
- [ ] Create unified ingestion worker deployment (Celery):
  - Queue: `ingest_queue` (single queue for entire pipeline)
  - Replicas: 2-10 with HPA based on queue length
  - Resource requests: CPU 1000m, Memory 2Gi
  - Resource limits: CPU 2000m, Memory 4Gi
  - Object Storage access (Azure Blob or GCS)
  - MongoDB connection string configured (existing infrastructure)
  - Handles complete pipeline (extract → chunk → store)
- [ ] Update ConfigMap with new environment variables:
  - Object Storage configuration (Blob/GCS)
  - MongoDB settings reference (existing: MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_CHUNKS_COLLECTION)
  - Redis configuration (Celery broker and job status)
  - Extraction and chunking defaults
- [ ] Update Secrets for:
  - Azure Blob Storage credentials
  - GCS service account credentials
  - MongoDB credentials (existing)
- [ ] HPA scaling rules:
  - Ingestion workers: scale up at >10 messages per worker
  - Scale down after 5 minutes of low queue depth
- [ ] Deployment scripts for AKS and GKE
- [ ] Smoke test on staging environment (verify Object Storage upload and MongoDB chunk storage)
- [ ] Rollout plan and rollback procedure documented
- [ ] Note: Single worker deployment (unified architecture)

**3. Monitoring and Metrics**:
- [ ] Add metrics to existing `/metrics` endpoint:
  - `v1_ingest_jobs_total{status}` - counter (submitted, completed, failed, cancelled)
  - `v1_ingest_job_duration_seconds{stage}` - histogram (extraction, chunking, storage, total)
  - `v1_ingest_documents_processed_total{format}` - counter (pdf, docx, html, etc.)
  - `v1_ingest_chunks_created_total` - counter
  - `v1_ingest_errors_total{stage, error_type}` - counter
  - `v1_ingest_queue_length` - gauge (single ingest_queue)
  - `v1_ingest_file_size_bytes` - histogram
  - `v1_ingest_object_storage_uploads_total{cloud}` - counter (azure, gcp)
  - `v1_ingest_mongodb_writes_total` - counter (chunk storage)
  - `v1_ingest_atomic_failures_total` - counter (rollback operations)
- [ ] Create Grafana dashboard `v1-ingest-pipeline.json`:
  - Job submission rate and status breakdown
  - Pipeline stage duration trends (extraction, chunking, storage)
  - Single queue depth and worker utilization
  - Error rates by stage and type
  - Throughput (documents/hour, chunks/hour)
  - Object Storage and MongoDB operation metrics
  - Atomic failure/rollback rate
- [ ] Alert rules defined:
  - High error rate (>5% failed jobs)
  - Queue backlog (>100 pending jobs for >15min)
  - Slow processing (>5min avg per job)
  - Object Storage or MongoDB failures
  - High rollback rate (>1% atomic failures)
- [ ] Dashboard deployed to AKS and GKE monitoring stacks

**4. Documentation**:
- [ ] Deployment guide
- [ ] Monitoring and alerting guide
- [ ] Troubleshooting runbook

**Dependencies**: Story 6 (Testing Layer)

---

## Backlog: Future Enhancements

### Story 8: Azure Document Intelligence Integration (FUTURE)

**Story Title**: Add Azure Document Intelligence as extraction library option

**Story Points**: 13

**Description**:
Implement Azure Document Intelligence as an alternative extraction library for advanced OCR, table extraction, and handwriting recognition. Create `AzureDocumentIntelligenceExtractor` implementing the `IExtractor` interface. Azure DI also performs automatic cleaning like Unstructured.

**Acceptance Criteria**:
- [ ] Azure AI Document Intelligence SDK integrated
- [ ] Create `src/rag_ingestion_api/services/extraction/azure_di_extractor.py`:
  - `AzureDocumentIntelligenceExtractor` class implementing `IExtractor`
  - Supports same formats as Unstructured
  - Extracts text, tables, and layout information with automatic cleaning
  - Returns structured `ExtractionResult` (text is pre-cleaned)
- [ ] Update `ExtractionLibrary` enum to include AZURE_DI
- [ ] Update `ExtractorFactory` to return Azure DI extractor when configured
- [ ] Add configuration to Settings:
  - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
  - `AZURE_DOCUMENT_INTELLIGENCE_KEY`
- [ ] Update `.env.example` with Azure DI settings
- [ ] Cost estimation logging (pages processed)
- [ ] Unit tests with mocked Azure DI API
- [ ] Integration test with real Azure DI (optional, manual)
- [ ] Performance comparison: Azure DI vs Unstructured (extraction time, quality)
- [ ] Documentation:
  - When to use Azure DI vs Unstructured
  - Cost comparison (Azure DI is paid API, Unstructured is free)
  - Configuration guide
  - Migration guide for existing jobs
- [ ] Note: No separate cleaning step needed - automatic in Azure DI like Unstructured

**Dependencies**: Story 2 (Extraction Layer)

---

## Summary

**Total Stories**: 7 MVP stories + 1 backlog story
**Estimated Story Points**: ~81 points for MVP (94 with backlog)
**Estimated Timeline**: 5-6 sprints (10-12 weeks)

**Architecture**: Layered approach with one story per layer

**Key Architecture Decisions**:
- **Simplified API**: Only 2 endpoints (POST /v1/ingestion, GET /v1/ingestion/{knowledge_ingestion_task_id})
- **No Job Cancellation**: Removed DELETE endpoint for simpler implementation
- **Unified Worker Pool**: Single worker type handles complete pipeline (simplified architecture)
- **Single Queue**: `ingest_queue` for all ingestion tasks (no task chaining complexity)
- **Atomic Processing**: Extract → Chunk → Store in single task (all-or-nothing)
- **Hybrid Storage**: Object Storage (Blob/GCS) for documents, MongoDB for chunks (74% cost savings)
- **No Separate Cleaning**: Automatic in Unstructured library during extraction
- **Single Chunking Strategy**: Per-job selection (not multiple strategies)
- **Always-Running Workers**: Min 2 replicas (not scale-to-zero) for fast response
- **Existing Infrastructure**: MongoDB connection settings already exist

**Recommended Sprint Breakdown**:
- **Sprint 1**: Story 1 (Object Storage Layer) - 5 points
- **Sprint 2**: Story 2 (Extraction Layer) - 13 points
- **Sprint 3**: Story 3 (Chunking Layer) - 12 points
- **Sprint 4**: Story 4 (Task Processing Layer) - 13 points
- **Sprint 5**: Story 5 (API Layer) - 12 points
- **Sprint 6**: Story 6 (Testing Layer) - 13 points
- **Sprint 7**: Story 7 (Deployment Layer) - 13 points

**Alternative 2-week Sprint Breakdown** (if team has capacity for larger stories):
- **Sprint 1**: Story 1 + Story 2 (Object Storage + Extraction) - 18 points
- **Sprint 2**: Story 3 + Story 4 (Chunking + Tasks) - 25 points
- **Sprint 3**: Story 5 (API Layer) - 12 points
- **Sprint 4**: Story 6 + Story 7 (Testing + Deployment) - 26 points

**Definition of Done**:
- Code reviewed and approved
- Unit tests passing with >80% coverage
- Integration tests passing (including Object Storage and MongoDB)
- Documentation updated (inline, README, API docs)
- Configuration validated and `.env.example` updated
- Deployed to staging and smoke tested
- No critical or high-priority bugs

**Notes**:
- This scope assumes existing infrastructure (AKS, GKE, Redis, MongoDB, API framework) is already in place
- MongoDB connection settings already exist - no need to recreate them
- Story 1 focuses only on Object Storage setup (Azure Blob and GCS buckets)
- MongoDB chunk storage implementation moved to Story 4 (Task Processing Layer) where it's used
- Chunk Pydantic models moved to Story 3 (Chunking Layer) where they're created
- Azure Document Intelligence removed from MVP - moved to backlog (Story 8)
- Each story includes all models, configuration, implementation, tests, and documentation for that layer
- Focus is on enhancing existing v1/ingestion API (no v2 needed since v1 has no users)
- Hybrid storage provides significant cost savings (74%) vs MongoDB-only approach
