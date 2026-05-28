# Multi-Agent AI Operations Swarm (Syntra OS)

This module enables a multi-agent swarm architecture within Syntra OS, simulating how a team of specialized AI agents coordinates internally to complete complex operations (Finance automation, CRM sales lead enrichment, Document research, and Workflow execution).

---

## 🏗️ Architecture Overview

The Multi-Agent Swarm operates on a pub/sub communication model with a shared memory layer backed by PostgreSQL:

```
                  ┌──────────────────────┐
                  │      User Goal       │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │  Coordinator Agent   │
                  └──────────┬───────────┘
                             │ (Decomposes into Plan Steps)
                  ┌──────────▼───────────┐
                  │  Delegation Engine   │
                  └────┬───────────┬─────┘
                       │           │
     ┌─────────────────▼─┐       ┌─▼─────────────────┐
     │   Finance Agent   │       │     CRM Agent     │
     └─────────┬─────────┘       └─────────┬─────────┘
               │                           │
               └─────────┬─────────────────┘
                         │ (Read/Write Memory, Post Logs)
     ┌───────────────────▼───────────────────┐
     │  Communication Bus & Shared Memory   │
     └───────────────────────────────────────┘
```

---

## 📂 Code Structure & Components

* **`models.py`**: Declares SQLAlchemy models for persisting execution runs (`AgentWorkflowRun`), logs (`AgentLog`), and key-value memory records (`AgentMemory`).
* **`agent_registry.py`**: Manages capabilities, names, prompts, and default configurations of standard agents.
* **`communication_bus.py`**: Handles publishing log messages across agents, persisting them to the database for live tracking.
* **`memory_manager.py`**: Implements reading, writing, and listing values in the shared workspace memory table.
* **`delegation_engine.py`**: Matches a required capability to an agent and executes real mock operations (e.g. searching documents, scanning invoice anomalies, scoring CRM leads, or running workflow templates).
* **`agent_manager.py`**: Manages LLM prompts, generates structured tool-use payloads, and acts as the execution wrapper for individual agents.
* **`task_coordinator.py`**: Controls execution flow: decomposes the user's high-level goal, maps steps to agent capabilities, coordinates sequential runs, updates memory, and builds the final synthesis report.
* **`router.py`**: Exposes FastAPI endpoints for launching swarm runs, retrieving histories, showing logs, and registering agents.

---

## 🗄️ Database Schemas

### 1. `agent_workflow_runs`
Tracks active swarm runs.
* `id` (UUID, PK)
* `goal` (TEXT)
* `status` (VARCHAR) — `pending`, `running`, `success`, `failed`
* `execution_plan` (JSONB) — list of tasks and target capabilities.
* `shared_memory` (JSONB) — final key-value workspace output.
* `started_at` (TIMESTAMP)
* `completed_at` (TIMESTAMP)
* `error_message` (TEXT)

### 2. `agent_logs`
Tracks messages passing through the communication bus.
* `id` (UUID, PK)
* `run_id` (UUID, FK)
* `sender` (VARCHAR)
* `recipient` (VARCHAR)
* `message_type` (VARCHAR) — e.g. `task_call`, `task_result`, `system_event`
* `content` (TEXT)
* `created_at` (TIMESTAMP)

### 3. `agent_memory`
Key-value workspace storage.
* `run_id` (UUID, PK, FK)
* `key` (VARCHAR, PK)
* `val_json` (JSONB)
* `updated_at` (TIMESTAMP)

---

## 🚀 API Endpoints

All endpoints are prefix-configured at `/api/v1/agents`:

* **`POST /run-task`**: Initiates a swarm execution run.
  * *Request Body*: `{"goal": "...", "context": {}}`
  * *Response*: `{"run_id": "...", "plan": [...]}`
* **`GET /agents`**: Returns a list of currently registered agents.
* **`POST /register`**: Registers a new custom agent.
  * *Request Body*: `{"key": "...", "name": "...", "role": "...", "description": "...", "capabilities": [...], "system_prompt": "..."}`
* **`GET /workflows`**: Returns history of execution runs.
* **`GET /logs`**: Retrieves the live log timeline for a specific execution run.

---

## 🧪 Testing

To run the integration tests for the multi-agent operations module:
```bash
pytest modules/multi_agent_system/test_multi_agent.py
```
