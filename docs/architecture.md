# System Architecture & Design Specification

This document provides a deep dive into IngestEngine's design patterns, layer configurations, and structural RAG evolution paths.

---

## 1. High-Level Data Flow

The following diagram illustrates how a file moves from drag-and-drop to text persistence:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as React UI
    participant BE as FastAPI API
    participant PR as pdfplumber Extractor
    participant DB as PostgreSQL (UUID)

    User->>FE: Drop PDF File
    FE->>FE: Validate type (PDF) & size (<20MB)
    FE->>BE: POST /upload-document (Multipart FormData)
    BE->>BE: Verify extension
    BE->>PR: Send file byte stream
    PR->>PR: Parse page structures & clean text stream
    PR-->>BE: Return extracted string content
    BE->>DB: INSERT into documents (generate UUID)
    DB-->>BE: Acknowledge & return row details
    BE-->>FE: HTTP 201 Response (JSON document object)
    FE->>User: Display success banner & append table row
```

---

## 2. Layer Architecture

### 2.1 Client Layer (Frontend SPA)
The client interface is structured around single-responsibility React components:
- **`FileUpload.tsx`**: State machine managing the dragging state, file format confirmation, payload size gating, and HTTP progress visual indicators.
- **`DocumentList.tsx`**: High-performance grid presenting system statistics and listing processed items.
- **`DocumentViewer.tsx`**: Text rendering drawer. Displays metrics like character and word count alongside raw copy commands.
- **`Dashboard.tsx` (Finance Operations)**: Control panel managing financial stats, transactional list grids, and Operational Risk compliance alerts.

### 2.2 API Layer (Backend)
- **FastAPI Framework**: Handles routing, asynchronous request handlers, and automatic validation schema generation.
- **Validation**: Enforced via Pydantic model configurations (see `schemas.py`) and programmatic math checking (see `validator.py`).
- **Invoice & Payroll Modules**: Custom services under `/modules/invoice_automation/` executing compliance validations, duplicate detections, and anomaly triggers on PostgreSQL data.
- **Processing Engine**: The text extraction process is isolated within `pdf_processor.py`, running in-memory without disk writes for increased speed and filesystem isolation.

### 2.3 Database Layer (Storage)
- **Engine**: PostgreSQL with pgvector extension enabled.
- **Container**: Runs on local Docker container (`local-postgres` mapping port `5433 -> 5432`).
- **Index Optimization**: Created `idx_documents_created_at` index on the `created_at` field, and HNSW indexes on chunk embeddings for cosine distance search.
- **Identities**: UUIDv4 keys are generated at the SQL database layer to avoid conflicts during future data syncs or vector shard divisions.

---

## 3. RAG + Vector DB Integration

The project employs a fully operational Retrieval-Augmented Generation context:

```mermaid
flowchart TD
    subgraph Ingestion Pipeline
        A[PDF Upload] --> B[Text Extracted]
        B --> C[Postgres documents]
    end

    subgraph RAG Expansion
        C --> D[Semantic Splitter]
        D --> E[Embedding API]
        E --> F[pgvector document_chunks]
        G[User Query] --> H[Query Embedding]
        F & H --> I[Similarity Search]
        I --> J[LLM prompt contextualizer]
        J --> K[AI Answer Output]
    end
    
    subgraph Invoices & Payroll Automation
        C --> L[LLM Structured Classifier]
        L --> M[Validation Engine]
        M --> N[Anomaly Scanning]
        N --> O[Postgres invoices/payroll/anomalies]
    end
```

### Key Integration Steps
1. **Vector DB Integration**: Enabling the `vector` extension inside the PostgreSQL server.
2. **Text Chunking**: Slices raw document content into 600-character windows with 150-character sentence-boundary overlaps.
3. **Embeddings Pipeline**: Generates 1536-dimensional vectors for text chunks via OpenAI or a local mock vector fallback.
4. **Auditing Sync**: Intercepts ingested text to parse invoice or payroll models, run calculations validation, and register active compliance anomalies.

---

## 4. Multi-Agent AI Operations Swarm

The swarm architecture allows specialized autonomous agents to coordinate and resolve complex workflows:

```mermaid
graph TD
    A[Task Coordinator] -->|Decomposes goal| B[Execution Pipeline]
    B -->|Resolves agent capability| C[Delegation Engine]
    C -->|Invokes| D[Core Agents: Finance, CRM, Research, Workflow]
    D -->|Publish events| E[Communication Bus]
    D -->|Read/Write context| F[Shared Memory Manager]
```

### Components:
* **Registry & Coordination**: The Task Coordinator maps goal statements to capabilities.
* **Shared Memory & Context**: Agents communicate asynchronously by writing capability summaries to the database-backed shared memory layer.
* **Pub/Sub Logging**: All message exchanges are routed through the Communication Bus to persist trace histories for live developer auditing.

---

## 5. Real-Time Event Bus & Asynchronous Job Processing

Syntra OS integrates a distributed-ready, event-driven infrastructure enabling decoupled module communication and resilient asynchronous background task execution.

```mermaid
graph TD
    A[Publishers: Upload, Agents, Workflows] -->|publish_event| B[Event Bus]
    B -->|Persists EventRecord| C[(PostgreSQL)]
    B -->|Triggers| D[Event Dispatcher]
    D -->|Executes Callback| E[Event Registry]
    E -->|Synchronous Handler| F[Immediate Reaction]
    E -->|Asynchronous Handler| G[Enqueue EventJob]
    G -->|Priority Ordering| H[(Job Queue)]
    H -->|Pulls Task| I[Async Workers Daemon]
    I -->|Executes Task| J[Heavy Workload: AI, Extraction]
    I -->|Error / Retry| K[Retry Scheduler]
    K -->|Exponential Backoff| H
    K -->|Exceeds max_retries| L[Dead Letter Queue DLQ]
```

### Components
* **Central Event Bus**: Collects events, correlates them with trace contexts, publishes telemetry metrics, and persists them database-wide.
* **Registry & Dispatcher**: Manages module event subscriptions and coordinates reactions.
* **Priority Job Queue**: Supports atomic task reservation (avoiding worker race conditions) and processes critical operations before standard tasks.
* **Retry Engine & DLQ**: Ensures robustness by retrying failed tasks with exponential backoff delays, and moves terminally failed processes to a quarantined review container.
* **SSE Telemetry Streaming**: Live updates the frontend operations dashboard using Server-Sent Events (SSE).

---

## 6. Enterprise Notification & Communication Hub

Syntra OS incorporates an intelligent communication layer that handles multi-channel alerts routing, user preferences matching, incident escalations, and AI summarizations.

```mermaid
graph TD
    A[Event Sources / Swarm Agents] -->|publish_event| B[Event Bus]
    B -->|triggers| C[Notification Manager]
    C -->|checks| D[Preference Manager]
    C -->|templates| E[AI Template Engine]
    C -->|resolves| F[Channel Router]
    F -->|sends| G[Delivery Engine]
    G -->|In-App / Email / Slack / SMS| H[Recipient Targets]
    G -->|pushes| I[Realtime Gateway]
    I -->|SSE Stream| J[Frontend Notification Center]
    
    H -->|Unresolved Alert| K[Escalation Notifier]
    K -->|Escalate target & critical level| G
```

### Components
* **Notification Manager**: Orchestrator that binds events, triggers templating, computes channels, executes deliveries, and manages state updates.
* **Preference Manager**: Evaluates routing filters, channel settings, and module subscriptions for recipients.
* **AI Template Engine**: Integrates with LLMs to summarize raw system JSON payloads into beginner-friendly sentences.
* **Channel Router & Delivery Engine**: Route notifications across multiple simulated channels (In-app, SMTP Email, Slack webhooks, Twilio SMS) and log confirmation latency traces.
* **Escalation Notifier**: Raises unresolved notifications to `critical` priority and re-routes to secondary management stakeholders.
* **Realtime Gateway**: Implements SSE streams `/api/v1/notifications/stream` for live updates on the client UI.

---

## 7. Enterprise Authentication & Role-Based Access Control (RBAC) System

Syntra OS enforces security compliance and operational boundaries via a custom Identity & Access Management (IAM) engine.

```mermaid
graph TD
    A[Client Request + JWT] --> B[API Router]
    B -->|FastAPI Dependency| C[get_current_user]
    C -->|JWT Verify| D[Verify JWT Token]
    D -->|Invalid / Expired| E[401 Unauthorized]
    D -->|Valid| F[Fetch User + Session]
    F --> G[PermissionGuard]
    G -->|Checks Role Capabilities| H[Role Manager]
    G -->|Enforces Department Locks| I[Permission Engine]
    H & I -->|Matches Policy| J[Route Access Granted]
    H & I -->|Violation| K[Raise 403 Forbidden]
    K -->|Security Logger| L[Security Audit Log]
    L -->|Event Bus| M[Publish security_alert]
```

### Components
* **Cryptographic Engine**: Secures user credential storage using standard PBKDF2 hashing, and signs access tokens using an in-house HS256 JWT builder.
* **Session Lifecycle Manager**: Manages session state persistence, tracks token expiration bounds, and implements global token invalidations.
* **Role Capability Engine**: Houses mapping matrices associating roles (e.g. `admin`, `finance_manager`, `sales_rep`, `compliance_officer`) with granular permissions (e.g. `invoices:read`, `crm_records:write`, `anomaly_overrides:execute`).
* **Boundary Permission Engine**: Enforces strict departmental partitions (e.g., `sales`, `finance`, `compliance`) preventing cross-department access except for global roles.
* **FastAPI Security Guards**: Decorates api routes with dependency-injected filters that authorize operations and raise structured errors.
* **Security Audit Logger**: Traces all authentication occurrences to database logs and routes security violations to the Event Bus, triggering immediate administrator alerts.

---

## 8. Unified Operations Dashboard (Control Center)

Syntra OS integrates a centralized corporate command console pulling analytics, alerts, approvals, and live telemetry across all modules.

```mermaid
graph TD
    A[React Control Center] -->|HTTP / SSE| B[Dashboard Router]
    B -->|Query / Aggregate| C[Metrics Aggregator]
    B -->|SSE Stream| D[Activity Feed]
    B -->|Fetch Inbox| E[Alert Collector]
    B -->|Generate summary| F[AI Summary Compiler]
    C -->|Reads DB| G[(Database: Workflows, Agents, CRM, Finance, Reviews, Errors, Events)]
    D -->|SSE Listeners| H[Event Bus dispatcher hook]
```

### Components
* **Metrics Aggregator Layer**: Calculates status widget values (active workflows, running agents, approvals, and failed jobs) and calculates a real-time system health score.
* **Alert Collector**: Unifies approval review cards and notification flags into a consolidated operations inbox.
* **Activity Feed Engine**: Merges historical logs and streams published events to active SSE client queues.
* **AI Summary Compiler**: Generates natural language executive summaries based on system telemetry.
* **Quick Action Dispatcher**: Executes commands (approvals, custom RAG searches, workflow executions) matching RBAC boundaries.

---

## 9. AI Copilot Control Center (Natural Language Ops Interface)

Syntra OS features a natural language operations console that parses intents, verifies access constraints via security guardrails, runs multi-system operations, and returns rich UI components.

```mermaid
graph TD
    A[User / Copilot Console] -->|Submit query| B[Copilot Router]
    B -->|Parse intent & entities| C[Intent Parser]
    C -->|Extracts intent JSON| D[Safety Guardrails]
    D -->|Verify RBAC rules & boundaries| E{Permitted?}
    E -->|No| F[Security Audit / 403 Forbidden]
    E -->|Yes| G[Tool Executor]
    G -->|Executes API actions| H[Subsystems: Workflows, Finance, CRM, Agents, Reviews]
    H -->|Results| I[Response Generator]
    I -->|Returns formatted markdown + card items| J[Copilot Chat Output]
```

### Components
* **Intent Parser**: Normalizes input messages and classifies them into structured intents (e.g. `QUERY_FINANCE`, `EXECUTE_WORKFLOW`, `TRIGGER_AGENT`, `QUERY_RAG`, `PROCESS_REVIEW`, `GET_DIAGNOSTICS`) using pattern heuristics and AI matching.
* **Safety Guardrails**: Cross-references parsed intents against the user's role and department profile to enforce access control (e.g. only Finance department can query financial transactions, only Admin/Manager can trigger manual workflows or execute approvals).
* **Tool Executor**: Interacts programmatically with core Syntra OS operations (executing jobs on the Event Bus, querying PostgreSQL/SQLite database tables, initializing multi-agent swarm routines, modifying approvals status).
* **Response Generator**: Assembles user-facing responses with structured data layout recommendations, markdown messages, and suggested next steps to create dynamic action cards on the frontend interface.




