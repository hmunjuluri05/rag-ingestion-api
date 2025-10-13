# RAG Ingestion API - v2/ingestion Implementation Stories

**Project**: RAG Ingestion API v2 Implementation
**Epic**: Document Processing Pipeline with New v2/ingestion Endpoint
**Sprint Duration**: 2 weeks
**Context**: Implementing new v2/ingestion API on AKS and GKE with hybrid storage and unified worker architecture (v1 remains unchanged for existing users)

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

## Story 4: Task Processing Layer - Chained Celery Tasks (Ingest → Embed → Index)

**Story Title**: Implement complete task processing layer with Celery configuration and three chained tasks

**Story Points**: 18

**Description**:
Implement complete task processing layer including Celery configuration for three-queue architecture with chained tasks (ingest → embed → index). Includes job status models, Redis-based job manager, Celery configuration, three separate tasks (ingestion, embedding, indexing), and task chaining support. Each task operates independently and chains to the next task upon completion.

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
  - Three queues:
    - `ingest_queue` - ingestion tasks (extract + chunk)
    - `embedding_queue` - embedding tasks (generate embeddings)
    - `indexing_queue` - indexing tasks (index to vector DB)
  - Task routing configuration:
    - `ingest_document_task` → `ingest_queue`
    - `embedding_task` → `embedding_queue`
    - `indexing_task` → `indexing_queue`
  - Default retry policy per queue: 3 retries, exponential backoff (base=4s, max=300s)
  - Task time limits per task type:
    - Ingestion: soft=900s, hard=1200s
    - Embedding: soft=1200s, hard=1800s (longer for ML workload)
    - Indexing: soft=600s, hard=900s
- [ ] Base task class for pipeline tasks with:
  - Automatic status updates to Redis (job status tracking with stage info)
  - Error logging with full context
  - Standardized exception handling
  - Task chaining support (queue next task on success)
- [ ] Worker startup configuration:
  - Ingestion workers (Celery) listen to `ingest_queue` - replicas: 2-10
  - Embedding workers (Celery) listen to `embedding_queue` - replicas: 2-10
  - Indexing workers (Celery) listen to `indexing_queue` - replicas: 2-10
- [ ] Celery routes configuration file with three queue mappings

**6. Task 1 - Ingestion Task (ingest_queue)**:
- [ ] Create `src/rag_ingestion_api/tasks/ingest_task.py`:
  - `ingest_document_task(job_id: str, file_path: str, config: dict)`
  - Routed to `ingest_queue`, consumed by Ingestion Workers
  - Updates job status to "processing - extracting"
  - Downloads document from Object Storage (Azure Blob or GCS)
  - Uses `ExtractorFactory` to get extractor based on config
  - Extracts text from document (automatic cleaning included by Unstructured)
  - Updates job status to "processing - chunking"
  - Uses `ChunkerFactory` to get chunker based on config (single strategy selection)
  - Splits text into chunks with metadata (position, total_chunks, source document info)
  - Stores chunks to MongoDB using `MongoDBChunkStore` with indexes
  - MongoDB indexes created: job_id, metadata fields, created_at
  - On success: Queue `embedding_task` to `embedding_queue` with chunk IDs
  - On failure: Update job status to "failed" with error details
  - Returns: `{job_id, chunk_ids, config}` for next task

**7. Task 2 - Embedding Task (embedding_queue)**:
- [ ] Create `src/rag_ingestion_api/tasks/embedding_task.py`:
  - `embedding_task(result: dict)` - receives output from ingestion task
  - Routed to `embedding_queue`, consumed by Embedding Workers
  - Updates job status to "processing - embedding"
  - Fetches chunks from MongoDB using job_id
  - Generates embeddings for each chunk (using existing embedding service or API)
  - Stores embeddings back to MongoDB (update chunk documents with embedding field)
  - On success: Queue `indexing_task` to `indexing_queue` with chunk IDs
  - On failure: Update job status to "failed" with error details
  - Returns: `{job_id, chunk_ids, embeddings_count}` for next task

**8. Task 3 - Indexing Task (indexing_queue)**:
- [ ] Create `src/rag_ingestion_api/tasks/indexing_task.py`:
  - `indexing_task(result: dict)` - receives output from embedding task
  - Routed to `indexing_queue`, consumed by Indexing Workers
  - Updates job status to "processing - indexing"
  - Fetches chunks with embeddings from MongoDB
  - Indexes embeddings to vector database (using existing indexing service or API)
  - Updates job status to "completed"
  - Sends webhook notification if `callback_url` provided
  - Webhook payload includes: job_id, status, stats (chunks_created, embeddings_generated, vectors_indexed, total_time)
  - On failure: Update job status to "failed" with error details
  - Returns: `{job_id, status: "completed"}` as final result

**9. Custom Exception Classes**:
- [ ] Create `src/rag_ingestion_api/exceptions.py`:
  - `ExtractionError` (base class for extraction failures)
  - `UnsupportedFormatError` (invalid file format)
  - `CorruptedFileError` (cannot parse document)
  - `ChunkingError` (chunking failure)
  - `EmbeddingError` (embedding generation failure)
  - `IndexingError` (vector indexing failure)
  - `ObjectStorageError` (Blob/GCS storage failure)
  - `MongoDBError` (MongoDB chunk storage failure)
  - `VectorDBError` (Vector database failure)

**10. Error Handling & Retry Logic**:
- [ ] Implement retry logic for transient errors (per task):
  - Object Storage failures: 3 retries with exponential backoff (ingestion task)
  - MongoDB failures: 3 retries with exponential backoff (all tasks)
  - Network errors: 3 retries (all tasks)
  - Embedding API failures: 3 retries with backoff (embedding task)
  - Vector DB failures: 3 retries with backoff (indexing task)
  - Rate limiting: retry with backoff (all tasks)
- [ ] Non-retryable errors logged and job marked as failed:
  - Unsupported format, corrupted file, invalid config (ingestion task)
  - Malformed embedding data (embedding task)
  - Invalid vector dimensions (indexing task)
- [ ] Error details stored in job status:
  - error_message, error_type, failed_at timestamp, failed_stage
- [ ] Stage-specific rollback: Each task handles its own cleanup on failure
- [ ] Performance metrics logged per stage (extraction time, chunking time, embedding time, indexing time, total time)

**11. Testing**:
- [ ] Unit tests with mocked Object Storage, extractors, chunkers, embedding service, indexing service, and MongoDB
- [ ] Integration tests with real Celery, Redis, Object Storage, MongoDB, and task chaining
- [ ] Test task chaining behavior (ingest → embed → index)
- [ ] Test independent task failure and retry (each stage can fail independently)
- [ ] Test webhook notifications (sent only from final indexing task)
- [ ] Test error scenarios for each exception type in each task
- [ ] Test retry behavior for transient vs permanent errors per stage
- [ ] Test queue routing (tasks go to correct queues)
- [ ] Test coverage >80%

**12. Documentation**:
- [ ] Running three worker types locally for v2/ingestion
- [ ] Task architecture and chained processing (ingest → embed → index)
- [ ] Error handling and retry logic per stage
- [ ] Queue configuration and routing

**Dependencies**: Story 1 (Object Storage), Story 2 (Extraction Layer), Story 3 (Chunking Layer with Chunk models)

---

## Story 5: API Layer - FastAPI Endpoints for Job Management

**Story Title**: Implement complete API layer with job submission and status query endpoints

**Story Points**: 10

**Description**:
Implement complete REST API layer for v2/ingestion including POST /v2/ingestion for job submission and GET /v2/ingestion/{knowledge_ingestion_task_id} for status queries. The API endpoint ONLY validates metadata, uploads documents to Object Storage, queues the first task, and returns 202 immediately. All processing (extract, chunk, embed, index) happens asynchronously in separate worker pools. Includes request/response validation and file upload handling.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/api.py`:
  - `ExtractionConfig` model (library: str = "unstructured")
  - `ChunkingConfig` model (strategy, chunk_size, chunk_overlap)
  - `EmbeddingConfig` model (metadata: Dict[str, Any] for embedding stage)
  - `IngestionConfig` model combining extraction, chunking, and embedding configs
  - `JobResponse` model (job_id, status, submitted_at, filename, knowledge_set_id)
  - `TaskStatusResponse` model (task_id, status, chunks)
  - `ErrorResponse` model (error_code, message, details)
  - All models have `extra = "forbid"` in Config
  - Note: Metadata is part of embedding config, validated against Knowledge Set schema

**2. Configuration**:
- [ ] Update existing Settings class with:
  - `API_MAX_FILE_SIZE_MB` (default: 100)
  - `API_SUPPORTED_FORMATS` (list: [".pdf", ".docx", ".doc", ".pptx", ".html", ".htm", ".md", ".txt"])
  - `API_ENABLE_WEBHOOKS` (default: True)
- [ ] Update `.env.example` with API settings
- [ ] Configuration validates on application startup

**3. POST /v2/ingestion Endpoint**:
- [ ] Create `src/rag_ingestion_api/api/v2/ingestion.py`:
  - POST `/v2/ingestion` endpoint
  - Accepts `multipart/form-data` with fields:
    - `file`: UploadFile (required)
    - `knowledge_set_id`: UUID string (required) - references existing Knowledge Set entity
    - `config`: JSON string (optional, uses defaults if not provided)
      - Contains `extraction`, `chunking`, and `embedding` sections
      - `embedding.metadata`: JSON object validated against Knowledge Set schema
    - `callback_url`: string (optional)
  - Validates `config` with `IngestionConfig` Pydantic model (no cleaning config - automatic)
  - File size limit from config (default: 100MB)
  - Format validation from config
  - Workflow (API ONLY does these steps - NO processing):
    - Validate `knowledge_set_id` exists (call Knowledge Set CRUD API)
    - Validate `config.embedding.metadata` against Knowledge Set schema **BEFORE** file upload
    - Generate unique `job_id` (UUID4)
    - Upload file to Object Storage (Azure Blob or GCS) permanently
    - Create job in Redis with status "queued" using `JobStatusManager`
    - Queue `ingest_document_task` to `ingest_queue` (first task in chain)
    - Return 202 Accepted immediately with `JobResponse` (job_id, status, submitted_at, filename, knowledge_set_id)
    - **NO extraction, chunking, embedding, or indexing happens in API** - all processing is asynchronous in workers
  - Success response:
    - 202 Accepted: Job queued successfully with `JobResponse` (task_id, status, submitted_at, filename, knowledge_set_id)
  - Error responses:
    - 422: Request validation failed (FastAPI/Pydantic validation errors with detail array: loc, msg, type)
    - 400: Invalid config, missing file, unsupported format, missing knowledge_set_id, invalid knowledge_set_id, metadata validation failed (schema mismatch)
    - 404: Knowledge Set ID does not exist
    - 413: File too large
    - 500: Object Storage failure, queue failure, Knowledge Set service unavailable

**4. GET /v2/ingestion/{knowledge_ingestion_task_id} Endpoint**:
- [ ] Add to `src/rag_ingestion_api/api/v2/ingestion.py`:
  - GET `/v2/ingestion/{knowledge_ingestion_task_id}` endpoint
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

**6. End-to-End Integration Tests**:
- [ ] Create `tests/integration/test_v2_ingestion_e2e.py`:
  - Test: Submit PDF → verify file in Object Storage → verify chunks in MongoDB with correct metadata
  - Test: Submit DOCX → verify atomic processing (extract + chunk + store)
  - Test: Submit HTML → verify automatic cleaning applied
  - Test: Submit with custom chunk config (single strategy) → verify chunk size respected
  - Test: Submit with callback_url → verify webhook called
  - Test: Submit with valid metadata (config.embedding.metadata) → verify metadata validation passes
  - Test: Submit with invalid metadata (schema mismatch) → verify 400 error with metadata validation details
  - Test: Submit without knowledge_set_id → verify 400 error (missing required field)
  - Test: Submit with non-existent knowledge_set_id → verify 400 error (invalid knowledge_set_id)
  - Test: Submit invalid format → verify 400 error
  - Test: Submit oversized file → verify 413 error
  - Test: Task status query returns correct status and chunks
  - Test: Query with invalid task_id → verify 404 error
  - Test: Multiple concurrent jobs (no interference)
  - Test: Atomic failure behavior (if chunking fails, no partial chunks stored)
- [ ] Test fixtures for sample documents (PDF, DOCX, HTML, TXT)
- [ ] Tests verify Object Storage (Blob/GCS) contains documents
- [ ] Tests verify MongoDB contains chunks with correct indexes
- [ ] Test graceful degradation on Redis failures
- [ ] Tests run in CI/CD pipeline

**8. Documentation**:
- [ ] OpenAPI documentation auto-generated
- [ ] Request/response examples for both endpoints
- [ ] Error code documentation
- [ ] Running integration tests locally
- [ ] Error types and troubleshooting guide

**Dependencies**: Story 1 (Object Storage), Story 4 (Task Processing Layer with MongoDB chunk storage and exceptions)

---

## Story 6: Deployment Layer - Documentation, Kubernetes, and Monitoring

**Story Title**: Complete deployment layer with API documentation, Kubernetes manifests, and monitoring

**Story Points**: 13

**Description**:
Complete deployment layer including comprehensive API documentation, Kubernetes deployment manifests for AKS/GKE with hybrid storage support, and Prometheus metrics with Grafana dashboards for monitoring the v2/ingestion pipeline.

**Acceptance Criteria**:

**1. API Documentation**:
- [ ] Create `docs/API_V2_INGESTION.md`:
  - Endpoint description and purpose
  - Request format with all parameters explained
  - Configuration options:
    - Extraction library selection (unstructured with automatic cleaning)
    - Chunking strategy (single selection, not list)
    - Chunk size recommendations by use case
  - Hybrid storage architecture explanation:
    - Documents stored permanently in Object Storage (Blob/GCS)
    - Chunks stored in MongoDB with indexes (separate instance per cloud)
    - Cost savings vs MongoDB-only approach
  - Response format and status codes
  - Error codes with troubleshooting
  - Webhook callback format and payload
- [ ] Code examples in Python and cURL:
  - Basic job submission (POST /v2/ingestion)
  - Custom configuration (single chunking strategy)
  - With metadata and callback
  - Query task status (GET /v2/ingestion/{knowledge_ingestion_task_id})
- [ ] Task lifecycle diagram (queued → processing → completed)
- [ ] Configuration best practices (no cleaning config needed, single chunking strategy)
- [ ] OpenAPI spec updated with descriptions
- [ ] README.md updated with new v2/ingestion section (v1 remains unchanged)

**2. Kubernetes Deployments**:
- [ ] Deploy new v2/ingestion API code (no changes to API pod deployment configuration, v1 endpoints remain unchanged)
- [ ] Create Ingestion Worker deployment (Celery):
  - Queue: `ingest_queue` (extract + chunk + store)
  - Replicas: 2-10 with HPA based on queue length
  - Resource requests: CPU 1000m, Memory 2Gi
  - Resource limits: CPU 2000m, Memory 4Gi
  - Object Storage access (Azure Blob or GCS)
  - MongoDB connection string configured (existing infrastructure)
  - Handles extraction and chunking stages
- [ ] Create Embedding Worker deployment (Celery):
  - Queue: `embedding_queue` (generate embeddings)
  - Replicas: 2-10 with HPA based on queue length
  - Resource requests: CPU 2000m, Memory 4Gi (more resources for ML workload)
  - Resource limits: CPU 4000m, Memory 8Gi
  - MongoDB connection string configured
  - Handles embedding generation stage
- [ ] Create Indexing Worker deployment (Celery):
  - Queue: `indexing_queue` (index to vector DB)
  - Replicas: 2-10 with HPA based on queue length
  - Resource requests: CPU 500m, Memory 1Gi
  - Resource limits: CPU 1000m, Memory 2Gi
  - MongoDB and Vector DB connection configured
  - Handles indexing stage
- [ ] Update ConfigMap with new environment variables:
  - Object Storage configuration (Blob/GCS)
  - MongoDB settings reference (existing: MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_CHUNKS_COLLECTION)
  - Redis configuration (Celery broker and job status)
  - Extraction, chunking, embedding, and indexing defaults
  - Vector DB configuration
- [ ] Update Secrets for:
  - Azure Blob Storage credentials
  - GCS service account credentials
  - MongoDB credentials (existing)
  - Vector DB credentials
- [ ] HPA scaling rules:
  - Ingestion workers: scale up at >10 messages in ingest_queue per worker
  - Embedding workers: scale up at >5 messages in embedding_queue per worker (ML tasks are heavier)
  - Indexing workers: scale up at >10 messages in indexing_queue per worker
  - Scale down after 5 minutes of low queue depth
- [ ] Deployment scripts for AKS and GKE
- [ ] Smoke test on staging environment (verify full pipeline: upload → extract → chunk → embed → index)
- [ ] Rollout plan and rollback procedure documented
- [ ] Note: Three separate worker deployments (chained architecture)

**3. Monitoring and Metrics**:
- [ ] Add metrics to existing `/metrics` endpoint:
  - `v2_ingest_jobs_total{status}` - counter (submitted, completed, failed, cancelled)
  - `v2_ingest_job_duration_seconds{stage}` - histogram (extraction, chunking, embedding, indexing, total)
  - `v2_ingest_documents_processed_total{format}` - counter (pdf, docx, html, etc.)
  - `v2_ingest_chunks_created_total` - counter
  - `v2_ingest_embeddings_generated_total` - counter
  - `v2_ingest_vectors_indexed_total` - counter
  - `v2_ingest_errors_total{stage, error_type}` - counter (stage: extraction, chunking, embedding, indexing)
  - `v2_ingest_queue_length{queue}` - gauge (ingest_queue, embedding_queue, indexing_queue)
  - `v2_ingest_file_size_bytes` - histogram
  - `v2_ingest_object_storage_uploads_total{cloud}` - counter (azure, gcp)
  - `v2_ingest_mongodb_writes_total{operation}` - counter (chunk_storage, embedding_storage)
  - `v2_ingest_vectordb_operations_total{operation}` - counter (index, search)
  - `v2_ingest_worker_utilization{worker_type}` - gauge (ingestion, embedding, indexing)
- [ ] Create Grafana dashboard `v2-ingest-pipeline.json`:
  - Job submission rate and status breakdown
  - Pipeline stage duration trends (extraction, chunking, embedding, indexing)
  - Three queue depths (ingest, embedding, indexing) and worker utilization per type
  - Error rates by stage and type (extraction, chunking, embedding, indexing errors)
  - Throughput (documents/hour, chunks/hour, embeddings/hour, vectors indexed/hour)
  - Object Storage, MongoDB, and Vector DB operation metrics
  - Worker pool utilization (ingestion, embedding, indexing workers)
- [ ] Alert rules defined:
  - High error rate (>5% failed jobs per stage)
  - Queue backlog (>100 pending jobs in any queue for >15min)
  - Slow processing (>5min avg per stage)
  - Object Storage, MongoDB, or Vector DB failures
  - Worker pool underutilization or overload (per worker type)
- [ ] Dashboard deployed to AKS and GKE monitoring stacks

**4. Documentation**:
- [ ] Deployment guide
- [ ] Monitoring and alerting guide
- [ ] Troubleshooting runbook

**Dependencies**: Story 5 (API Layer with end-to-end tests)

---

## Backlog: Future Enhancements

### Story 7: Azure Document Intelligence Integration (FUTURE)

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

**Total Stories**: 6 MVP stories + 1 backlog story
**Estimated Story Points**: ~71 points for MVP (84 with backlog)
**Estimated Timeline**: 4-6 sprints (8-12 weeks)

**Architecture**: Layered approach with one story per layer, testing integrated into each story

**Key Architecture Decisions**:
- **New API Version**: v2/ingestion endpoints (v1 remains unchanged for existing users)
- **API Only Dispatches**: FastAPI endpoint only validates, uploads to Object Storage, queues first task, returns 202 in <100ms
- **Simplified API**: Only 2 endpoints (POST /v2/ingestion, GET /v2/ingestion/{knowledge_ingestion_task_id})
- **No Job Cancellation**: Removed DELETE endpoint for simpler implementation
- **Three Worker Pools**: Separate worker types for ingestion, embedding, and indexing
- **Three Queues**: `ingest_queue`, `embedding_queue`, `indexing_queue` for independent scaling
- **Chained Processing**: Extract + Chunk → Embed → Index (three separate tasks)
- **Independent Scaling**: Each worker pool scales based on its queue depth and resource utilization
- **Hybrid Storage**: Object Storage (Blob/GCS) for documents, MongoDB for chunks and embeddings (74% cost savings)
- **Separate MongoDB**: Each cloud environment has its own MongoDB instance for data isolation
- **No Separate Cleaning**: Automatic in Unstructured library during extraction
- **Single Chunking Strategy**: Per-job selection (not multiple strategies)
- **Always-Running Workers**: Min 2 replicas per worker type (not scale-to-zero) for fast response
- **Existing Infrastructure**: MongoDB connection settings already exist
- **Testing Integrated**: Unit and integration tests part of each layer (no separate testing story)

**Recommended Sprint Breakdown**:
- **Sprint 1**: Story 1 (Object Storage Layer) - 5 points
- **Sprint 2**: Story 2 (Extraction Layer) - 13 points
- **Sprint 3**: Story 3 (Chunking Layer) - 12 points
- **Sprint 4**: Story 4 (Task Processing Layer + Chained Tasks) - 18 points
- **Sprint 5**: Story 5 (API Layer + E2E Tests) - 10 points
- **Sprint 6**: Story 6 (Deployment Layer + Three Worker Types) - 13 points

**Alternative 2-week Sprint Breakdown** (if team has capacity for larger stories):
- **Sprint 1**: Story 1 + Story 2 (Object Storage + Extraction) - 18 points
- **Sprint 2**: Story 3 + Story 4 (Chunking + Chained Tasks) - 30 points
- **Sprint 3**: Story 5 + Story 6 (API + E2E Tests + Deployment) - 23 points

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
- MongoDB chunk storage implementation in Story 4 (Task Processing Layer) where it's used
- Chunk Pydantic models in Story 3 (Chunking Layer) where they're created
- Custom exception classes in Story 4 (Task Processing Layer) where they're used
- End-to-end integration tests in Story 5 (API Layer) where they test the complete flow
- Azure Document Intelligence removed from MVP - moved to backlog (Story 7)
- Each story includes all models, configuration, implementation, tests, and documentation for that layer
- Testing is integrated into each story's Definition of Done (no separate testing story)
- Focus is on implementing new v2/ingestion API (v1 remains unchanged for existing users)
- Hybrid storage provides significant cost savings (74%) vs MongoDB-only approach
- Separate MongoDB instances per cloud for data isolation
