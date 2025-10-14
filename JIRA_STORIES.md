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
    - `upload_document(task_id: str, filename: str, content: bytes) -> str` (returns path)
    - `download_document(file_path: str) -> bytes`
    - `delete_document(file_path: str) -> None`
  - `AzureBlobStorageProvider` implementation
  - `GCSStorageProvider` implementation
  - `ObjectStorageFactory` returns provider based on `OBJECT_STORAGE_PROVIDER` config
  - Path structure: `tasks/{task_id}/document.*` (permanent storage)

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
- [ ] Create `src/rag_ingestion_api/models/ingestion/chunking.py`:
  - `ChunkingStrategy` enum (RECURSIVE, SEMANTIC, SENTENCE, PARAGRAPH)
  - `ChunkingConfig` model with:
    - `strategy: str` (single selection, not list)
    - `chunk_size: int = 512` (ge=1, le=8192)
    - `chunk_overlap: int = 50` (ge=0)
  - `Chunk` model (basic chunking output):
    - `id: str` (generated by chunker)
    - `text: str` (chunk text)
    - `metadata: Dict[str, Any]` (source document info, position, etc.)
    - `position: int` (chunk position in document)
  - `ChunkMetadata` model (embedded in Chunk.metadata):
    - Source document info (filename, file_path, format)
    - `page_number: Optional[int]`
    - `position: int` (chunk position)
    - `total_chunks: int`
  - All models have `extra = "forbid"` in Config
  - Field validations with proper types and ranges

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
  - `IChunker` ABC with `chunk(text: str, config: ChunkingConfig, metadata: Dict[str, Any]) -> List[Chunk]`
  - Note: Chunkers don't need task_id (that's a storage concern), they just need source metadata

**4. Chunker Implementations**:
- [ ] Create `src/rag_ingestion_api/services/chunking/recursive_chunker.py`:
  - `RecursiveChunker` using LangChain `RecursiveCharacterTextSplitter`
  - Respects `chunk_size` and `chunk_overlap` from config
  - Generates chunk IDs: `chunk_{uuid4()}` (storage layer will add task_id prefix)
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

**Dependencies**: None (Basic Chunk models for chunking output included in this story)

---

## Story 4: Task Processing Layer - Unified Celery Task (Complete Pipeline)

**Story Title**: Implement complete task processing layer with Celery configuration and single unified task

**Story Points**: 15

**Description**:
Implement complete task processing layer including Celery configuration for single-queue architecture with unified task. Includes task status models, Redis-based job manager, Celery configuration, and single unified task that handles complete pipeline (extract → chunk → embed → index). All processing including embedding and indexing code runs inside worker pods in Kubernetes. MongoDB serves as both document store and vector database.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/ingestion/tasks.py`:
  - `TaskStatus` enum (QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED)
  - `TaskResponse` model (task_id, status, submitted_at, filename)
  - `TaskStatusResponse` model (task_id, status, progress, stats)
  - `TaskProgress` model (current_step, percent_complete)
  - `TaskStats` model (extraction_time, chunks_created, file_size, document_storage_path)
  - All models have `extra = "forbid"` in Config
- [ ] Create `src/rag_ingestion_api/models/ingestion/storage.py`:
  - `StoredChunk` model (MongoDB storage schema):
    - `id: str` (format: `{task_id}_chunk_{position:04d}`)
    - `task_id: str` (links to ingestion task)
    - `text: str` (chunk text)
    - `metadata: Dict[str, Any]` (source document info, position, etc.)
    - `position: int` (chunk position in document)
    - `created_at: datetime` (timestamp)
    - `embedding: Optional[List[float]]` (added by embedding stage)
    - `indexed: bool = False` (set to True after vector indexing)
  - All models have `extra = "forbid"` in Config
  - Note: StoredChunk extends the basic Chunk from chunking.py with storage-specific fields

**2. Configuration**:
- [ ] Update existing Settings class with:
  - Celery config: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (Redis already exists)
  - Task config: `TASK_SOFT_TIMEOUT` (default: 900s), `TASK_HARD_TIMEOUT` (default: 1200s)
  - Retry config: `TASK_MAX_RETRIES` (default: 3), `TASK_RETRY_BACKOFF` (default: 4s)
  - Task config: `JOB_STATUS_TTL_DAYS` (default: 7)
- [ ] Update `.env.example` with task settings
- [ ] Configuration validates on application startup

**3. MongoDB Chunk Storage Implementation**:
- [ ] Create `src/rag_ingestion_api/services/storage/chunk_storage.py`:
  - `IChunkStore` interface with methods:
    - `store_chunks(task_id: str, chunks: List[Chunk]) -> int` (returns count)
      - Converts basic Chunk models to StoredChunk with task_id, created_at, and storage fields
    - `get_chunks(task_id: str, filters: Optional[Dict]) -> List[StoredChunk]`
    - `delete_chunks(task_id: str) -> int`
    - `update_chunk_embedding(chunk_id: str, embedding: List[float]) -> None`
    - `mark_chunk_indexed(chunk_id: str) -> None`
  - `MongoDBChunkStore` implementation with:
    - Connection to existing MongoDB infrastructure
    - Stores chunks as StoredChunk documents with indexes on task_id, metadata fields, created_at
    - Rich query support for RAG retrieval
    - Transaction support for atomic operations
    - Methods to update embedding and indexed fields during pipeline stages

**4. Task Status Manager**:
- [ ] Create `src/rag_ingestion_api/services/job_manager.py`:
  - `TaskStatusManager` class
  - `create_job(task_id, filename, config) -> TaskResponse` - stores initial state in Redis
  - `update_status(task_id, status, progress, stats)` - updates job in Redis
  - `get_job(task_id) -> TaskStatusResponse` - retrieves task info
  - `delete_job(task_id)` - removes job from Redis
  - Task data structure in Redis: Key `task:{task_id}`, Value: JSON with all task info
  - Tasks expire after TTL (configurable, default 7 days)
  - Error handling for Redis connection failures (graceful degradation)
  - Note: Redis serves dual purpose as Celery broker AND task status store

**5. Celery Configuration**:
- [ ] Update Celery app configuration with:
  - Single queue:
    - `ingest_queue` - all ingestion tasks (extract + chunk + embed + index)
  - Task routing configuration:
    - `ingest_document_task` → `ingest_queue`
  - Default retry policy: 3 retries, exponential backoff (base=4s, max=300s)
  - Task time limits:
    - soft=1800s, hard=2400s (covers complete pipeline including embedding)
- [ ] Base task class for pipeline tasks with:
  - Automatic status updates to Redis (task status tracking with stage info)
  - Error logging with full context
  - Standardized exception handling
  - Stage-specific progress tracking (extracting, chunking, embedding, indexing)
- [ ] Worker startup configuration:
  - Unified Ingestion workers (Celery) listen to `ingest_queue` - replicas: 2-10
  - Workers run embedding and indexing code inside pods
  - Higher resource allocation (CPU 2000m, Memory 4Gi) to handle complete pipeline

**6. Unified Ingestion Task (ingest_queue)**:
- [ ] Create `src/rag_ingestion_api/tasks/ingest_task.py`:
  - `ingest_document_task(task_id: str, file_path: str, config: dict)`
  - Routed to `ingest_queue`, consumed by Unified Ingestion Workers
  - **Stage 1 - Extraction**:
    - Updates task status to "processing - extracting"
    - Downloads document from Object Storage (Azure Blob or GCS)
    - Uses `ExtractorFactory` to get extractor based on config
    - Extracts text from document (automatic cleaning included by Unstructured)
  - **Stage 2 - Chunking**:
    - Updates task status to "processing - chunking"
    - Uses `ChunkerFactory` to get chunker based on config (single strategy selection)
    - Splits text into chunks with metadata (position, total_chunks, source document info)
    - Stores chunks to MongoDB using `MongoDBChunkStore` with indexes
    - MongoDB indexes created: task_id, metadata fields, created_at
  - **Stage 3 - Embedding**:
    - Updates task status to "processing - embedding"
    - Runs embedding code inside worker pod (not external service)
    - Generates embeddings for each chunk
    - Stores embeddings to MongoDB (update chunk documents with embedding field)
  - **Stage 4 - Indexing**:
    - Updates task status to "processing - indexing"
    - Runs indexing code inside worker pod (not external service)
    - Creates vector indexes in MongoDB (MongoDB serves as vector database)
    - Updates task status to "completed"
  - **Completion**:
    - Sends webhook notification if `callback_url` provided
    - Webhook payload includes: task_id, status, stats (chunks_created, embeddings_generated, vectors_indexed, total_time)
  - On failure at any stage: Update task status to "failed" with error details and failed stage
  - Returns: `{task_id, status: "completed", stats: {...}}` as final result

**7. Custom Exception Classes**:
- [ ] Create `src/rag_ingestion_api/exceptions.py`:
  - `ExtractionError` (base class for extraction failures)
  - `UnsupportedFormatError` (invalid file format)
  - `CorruptedFileError` (cannot parse document)
  - `ChunkingError` (chunking failure)
  - `EmbeddingError` (embedding generation failure)
  - `IndexingError` (vector indexing failure in MongoDB)
  - `ObjectStorageError` (Blob/GCS storage failure)
  - `MongoDBError` (MongoDB storage and vector operations failure)

**8. Error Handling & Retry Logic**:
- [ ] Implement retry logic for transient errors:
  - Object Storage failures: 3 retries with exponential backoff
  - MongoDB failures: 3 retries with exponential backoff
  - Network errors: 3 retries
  - Rate limiting: retry with backoff
- [ ] Non-retryable errors logged and job marked as failed:
  - Unsupported format, corrupted file, invalid config (extraction stage)
  - Malformed embedding data (embedding stage)
  - Invalid vector dimensions (indexing stage)
- [ ] Error details stored in task status:
  - error_message, error_type, failed_at timestamp, failed_stage
- [ ] Stage-specific progress tracking: Task status includes current stage
- [ ] Performance metrics logged per stage (extraction time, chunking time, embedding time, indexing time, total time)

**9. Testing**:
- [ ] Unit tests with mocked Object Storage, extractors, chunkers, embedding code, indexing code, and MongoDB
- [ ] Integration tests with real Celery, Redis, Object Storage, and MongoDB
- [ ] Test complete pipeline execution (extract → chunk → embed → index)
- [ ] Test stage-specific failure and retry (each stage can fail independently)
- [ ] Test webhook notifications (sent after completion)
- [ ] Test error scenarios for each exception type at each stage
- [ ] Test retry behavior for transient vs permanent errors per stage
- [ ] Test coverage >80%

**10. Documentation**:
- [ ] Running unified worker locally for v2/ingestion
- [ ] Task architecture and pipeline stages (extract → chunk → embed → index)
- [ ] Error handling and retry logic per stage
- [ ] Embedding and indexing code runs inside worker pods
- [ ] MongoDB as vector database

**Dependencies**: Story 1 (Object Storage), Story 2 (Extraction Layer), Story 3 (Chunking Layer with Chunk models)

---

## Story 5: API Layer - FastAPI Endpoints for Task Management

**Story Title**: Implement complete API layer with task submission and status query endpoints

**Story Points**: 10

**Description**:
Implement complete REST API layer for v2/ingestion including POST /v2/ingestion for task submission and GET /v2/ingestion/{knowledge_ingestion_task_id} for status queries. The API endpoint ONLY validates metadata, uploads documents to Object Storage, queues the unified task, and returns 202 immediately. All processing (extract, chunk, embed, index) happens asynchronously in unified worker pods. Includes request/response validation and file upload handling.

**Acceptance Criteria**:

**1. Pydantic Models**:
- [ ] Create `src/rag_ingestion_api/models/api.py`:
  - `ExtractionConfig` model (library: str = "unstructured")
  - `ChunkingConfig` model (strategy, chunk_size, chunk_overlap)
  - `EmbeddingConfig` model (metadata: Dict[str, Any] for embedding stage)
  - `IngestionConfig` model combining extraction, chunking, and embedding configs
  - `TaskResponse` model (task_id, status, submitted_at, filename, knowledge_set_id)
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
    - Generate unique `task_id` (UUID4)
    - Upload file to Object Storage (Azure Blob or GCS) permanently
    - Create job in Redis with status "queued" using `TaskStatusManager`
    - Queue `ingest_document_task` to `ingest_queue` (unified task handles complete pipeline)
    - Return 202 Accepted immediately with `TaskResponse` (task_id, status, submitted_at, filename, knowledge_set_id)
    - **NO extraction, chunking, embedding, or indexing happens in API** - all processing is asynchronous in unified worker pods
  - Success response:
    - 202 Accepted: Task queued successfully with `TaskResponse` (task_id, status, submitted_at, filename, knowledge_set_id)
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
- [ ] Unit tests with mocked Object Storage, Celery, and TaskStatusManager
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
  - Test: Multiple concurrent tasks (no interference)
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
  - Basic task submission (POST /v2/ingestion)
  - Custom configuration (single chunking strategy)
  - With metadata and callback
  - Query task status (GET /v2/ingestion/{knowledge_ingestion_task_id})
- [ ] Task lifecycle diagram (queued → processing → completed)
- [ ] Configuration best practices (no cleaning config needed, single chunking strategy)
- [ ] OpenAPI spec updated with descriptions
- [ ] README.md updated with new v2/ingestion section (v1 remains unchanged)

**2. Kubernetes Deployments**:
- [ ] Deploy new v2/ingestion API code (no changes to API pod deployment configuration, v1 endpoints remain unchanged)
- [ ] Create Unified Ingestion Worker deployment (Celery):
  - Queue: `ingest_queue` (complete pipeline: extract + chunk + embed + index)
  - Replicas: 2-10 with HPA based on queue length
  - Resource requests: CPU 2000m, Memory 4Gi (higher resources for complete pipeline)
  - Resource limits: CPU 4000m, Memory 8Gi
  - Object Storage access (Azure Blob or GCS)
  - MongoDB connection string configured (existing infrastructure, serves as vector DB)
  - Embedding and indexing code runs inside worker pods
  - Handles all stages: extraction, chunking, embedding, and indexing
- [ ] Update ConfigMap with new environment variables:
  - Object Storage configuration (Blob/GCS)
  - MongoDB settings reference (existing: MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_CHUNKS_COLLECTION)
  - Redis configuration (Celery broker and task status)
  - Extraction, chunking, embedding, and indexing defaults
- [ ] Update Secrets for:
  - Azure Blob Storage credentials
  - GCS service account credentials
  - MongoDB credentials (existing)
- [ ] HPA scaling rules:
  - Unified Ingestion workers: scale up at >10 messages in ingest_queue per worker
  - Scale down after 5 minutes of low queue depth
- [ ] Deployment scripts for AKS and GKE
- [ ] Smoke test on staging environment (verify full pipeline: upload → extract → chunk → embed → index)
- [ ] Rollout plan and rollback procedure documented
- [ ] Note: Single unified worker deployment (simplified architecture)

**3. Monitoring and Metrics**:
- [ ] Add metrics to existing `/metrics` endpoint:
  - `v2_ingest_tasks_total{status}` - counter (submitted, completed, failed, cancelled)
  - `v2_ingest_job_duration_seconds{stage}` - histogram (extraction, chunking, embedding, indexing, total)
  - `v2_ingest_documents_processed_total{format}` - counter (pdf, docx, html, etc.)
  - `v2_ingest_chunks_created_total` - counter
  - `v2_ingest_embeddings_generated_total` - counter
  - `v2_ingest_vectors_indexed_total` - counter
  - `v2_ingest_errors_total{stage, error_type}` - counter (stage: extraction, chunking, embedding, indexing)
  - `v2_ingest_queue_length{queue}` - gauge (ingest_queue - single queue)
  - `v2_ingest_file_size_bytes` - histogram
  - `v2_ingest_object_storage_uploads_total{cloud}` - counter (azure, gcp)
  - `v2_ingest_mongodb_operations_total{operation}` - counter (chunk_storage, embedding_storage, vector_index, vector_search)
  - `v2_ingest_worker_utilization` - gauge (unified ingestion workers)
- [ ] Create Grafana dashboard `v2-ingest-pipeline.json`:
  - Task submission rate and status breakdown
  - Pipeline stage duration trends (extraction, chunking, embedding, indexing)
  - Single queue depth (ingest_queue) and unified worker utilization
  - Error rates by stage and type (extraction, chunking, embedding, indexing errors)
  - Throughput (documents/hour, chunks/hour, embeddings/hour, vectors indexed/hour)
  - Object Storage and MongoDB operation metrics (including vector operations)
  - Worker pool utilization (unified ingestion workers)
- [ ] Alert rules defined:
  - High error rate (>5% failed tasks per stage)
  - Queue backlog (>100 pending tasks in ingest_queue for >15min)
  - Slow processing (>5min avg per stage)
  - Object Storage or MongoDB failures (including vector operations)
  - Worker pool underutilization or overload
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
  - Migration guide for existing tasks
- [ ] Note: No separate cleaning step needed - automatic in Azure DI like Unstructured

**Dependencies**: Story 2 (Extraction Layer)

---

## Summary

**Total Stories**: 6 MVP stories + 1 backlog story
**Estimated Story Points**: ~65 points for MVP (78 with backlog)
**Estimated Timeline**: 4-6 sprints (8-12 weeks)

**Architecture**: Layered approach with one story per layer, testing integrated into each story

**Key Architecture Decisions**:
- **New API Version**: v2/ingestion endpoints (v1 remains unchanged for existing users)
- **API Only Dispatches**: FastAPI endpoint only validates, uploads to Object Storage, queues unified task, returns 202 in <100ms
- **Simplified API**: Only 2 endpoints (POST /v2/ingestion, GET /v2/ingestion/{knowledge_ingestion_task_id})
- **No Task Cancellation**: Removed DELETE endpoint for simpler implementation
- **Single Worker Pool**: Unified workers handle complete pipeline (extract + chunk + embed + index)
- **Single Queue**: `ingest_queue` for all ingestion tasks (simplified architecture)
- **Unified Processing**: Single task handles complete pipeline inside worker pods
- **Code Inside Workers**: Embedding and indexing code runs inside Celery worker pods in Kubernetes
- **MongoDB as Vector DB**: MongoDB serves as both document store and vector database (no separate vector DB)
- **Hybrid Storage**: Object Storage (Blob/GCS) for documents, MongoDB for chunks, embeddings, and vector indexes (74% cost savings)
- **Separate MongoDB**: Each cloud environment has its own MongoDB instance for data isolation
- **No Separate Cleaning**: Automatic in Unstructured library during extraction
- **Single Chunking Strategy**: Per-job selection (not multiple strategies)
- **Always-Running Workers**: Min 2 replicas (not scale-to-zero) for fast response
- **Existing Infrastructure**: MongoDB connection settings already exist
- **Testing Integrated**: Unit and integration tests part of each layer (no separate testing story)

**Recommended Sprint Breakdown**:
- **Sprint 1**: Story 1 (Object Storage Layer) - 5 points
- **Sprint 2**: Story 2 (Extraction Layer) - 13 points
- **Sprint 3**: Story 3 (Chunking Layer) - 12 points
- **Sprint 4**: Story 4 (Task Processing Layer + Unified Task) - 15 points
- **Sprint 5**: Story 5 (API Layer + E2E Tests) - 10 points
- **Sprint 6**: Story 6 (Deployment Layer + Unified Worker) - 13 points

**Alternative 2-week Sprint Breakdown** (if team has capacity for larger stories):
- **Sprint 1**: Story 1 + Story 2 (Object Storage + Extraction) - 18 points
- **Sprint 2**: Story 3 + Story 4 (Chunking + Unified Task) - 27 points
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
