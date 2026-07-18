# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

MedAgent is a unified medical AI platform serving both patients and doctors through identity-based routing. It combines a RAG retrieval pipeline with an Agent orchestration engine under a monorepo structure (`backend/` + `frontend/` + `docker/`).

## Commands

```bash
# Start all services (MySQL, Redis, ChromaDB, MinIO, backend, Nginx)
cd docker && docker compose up -d

# Backend dev (without Docker — needs MySQL/Redis/ChromaDB already running)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend dev
cd frontend && npm install && npm run dev

# Frontend type check
cd frontend && npx tsc --noEmit

# Seed ChromaDB with test medical knowledge
cd backend && python scripts/seed_data.py

# Install backend dependencies (Python 3.11-3.12 required; 3.13 NOT compatible with numpy 1.x)
cd backend && pip install -r requirements.txt
cd backend && pip install -e ".[test]" aiosqlite

# Run all backend tests (asyncio_mode=auto configured in pyproject.toml)
cd backend && pytest -v

# Run a specific test tier
cd backend && pytest tests/unit/ -v           # Pure unit (no I/O)
cd backend && pytest tests/async_unit/ -v     # Async unit (mock LLM)
cd backend && pytest tests/api/ -v            # API integration (TestClient + SQLite)

# Run a single test file
cd backend && pytest tests/unit/test_bm25_index.py -v

# Run a single test function
cd backend && pytest tests/api/test_auth.py::TestRegister::test_register_success -v
```

Docker Compose is the canonical dev environment. Backend hot-reloads via the `--reload` volume mount. Frontend Vite dev server proxies `/api` to `localhost:8000` in dev mode (see `frontend/vite.config.ts`).

## Architecture

### Request flow (MVP)

```
Browser → Nginx(:80) → FastAPI(:8000)
                          ├─ /api/auth/*       → JWT login/register
                          ├─ /api/search       → RAG pipeline (non-streaming)
                          ├─ /api/chat/stream  → SSE streaming orchestrator
                          ├─ /api/mcp/tools    → MCP tool discovery (GET)
                          ├─ /api/mcp/invoke   → MCP tool invocation (POST)
                          ├─ /api/voice/transcribe  → Doubao STT (audio → text)
                          ├─ /api/voice/synthesize  → Doubao TTS (text → audio)
                          ├─ /api/report/upload     → MinIO file storage
                          ├─ /api/report/interpret/{id} → Doubao OCR + LLM interpretation
                          ├─ /api/chat/history     → Paginated chat history (GET)
                          ├─ /api/chat/history/{id} → Chat session detail (GET)
                          ├─ /api/patient/profile  → Patient profile CRUD (GET/PUT)
                          ├─ /api/patient/care-plan → Active care plans (GET)
                          └─ /api/doctor/patient/{id} → Patient record with mock HIS data (GET)

Identity routing: JWT middleware extracts user + role → RequestContext
  doctor → kb_professional + professional response template
  patient → kb_patient + layperson response template
```

### Orchestrator pipeline (ReAct-based)

`Orchestrator.run()` in `backend/app/core/agent/orchestrator.py`:
0. Memory context load (3-layer parallel read via `asyncio.gather`)
1. Intent classification (6 intents: consult, report_interpret, rehab, knowledge_search, decision_support, chitchat)
2. **ReAct loop** — LLM decides which tools to call (rag.search / MCP tools / memory.get_context / finish), max 5 iterations
3. SSE `reasoning_steps` event — emits ReAct thought/action/observation trace for doctor-facing transparency
4. Context extraction from ReAct observations → citation annotation
5. SSE stream: `data: {"type":"chunk","content":"..."}` … `data: {"type":"sources","sources":[...]}` `data: {"type":"done"}`

After streaming completes, `BackgroundTasks` saves the turn to short-term memory and persists the conversation to MySQL.

### Model adapter layer (`backend/app/core/model_adapter/`)

The central abstraction for all LLM calls. `AdapterRegistry` maintains priority chains with automatic fallback:

```
inference:  DashScopeAdapter (qwen-max, cloud) → OllamaAdapter (qwen3:14b, local)
embedding:  OllamaAdapter only (qwen3-embedding, always local)
reranker:   DashScopeAdapter (gte-rerank-v2, cloud) [when RERANKER_BACKEND=dashscope] or OllamaAdapter (qwen3:14b, local) → DashScopeAdapter (gte-rerank-v2, cloud) [when RERANKER_BACKEND=ollama]
```

Controlled by env vars: `INFERENCE_BACKEND=auto|dashscope|ollama`, `RERANKER_BACKEND=ollama|dashscope`. All modules call `get_adapter_registry()` rather than instantiating adapters directly.

Dev environment: Ollama runs natively on Windows at `localhost:11434` (NOT in Docker). Models stored on D: drive via `OLLAMA_MODELS` Windows env var. DashScope API key is configured in `backend/.env`. The `qwen3-reranker` model does not exist on Ollama — the `OllamaAdapter.rerank()` method uses `self._model` (qwen3:14b) as fallback. For cloud reranking, DashScope's `gte-rerank-v2` model is used (primary, configured via `RERANKER_BACKEND=dashscope`).

### Memory system (`backend/app/core/memory/`)

Three-layer architecture with independent degradation (each layer can fail without breaking the others):

- `memory_service.py` — `MemoryService` facade with two thin interfaces: `get_context()` and `save_turn()`. The only module the orchestrator imports.
- `memory_reader.py` — `MemoryReader` fuses all three layers in parallel via `asyncio.gather(return_exceptions=True)`. Returns `MemoryContext` with a pre-formatted Chinese prompt (`[用户画像]`, `[近期对话]`, `[相关历史]` sections).
- `short_term.py` — Redis lists, 20-turn cap, 30-minute TTL. Key pattern: `session:{session_id}:context`. Uses `get_redis()` with None guard everywhere.
- `long_term.py` — ChromaDB `user_memory` collection with `where={"user_id": user_id}` filtering. Embeddings via Qwen3-Embedding-8B through the adapter registry.
- `event_extractor.py` — LLM-based medical event extraction (symptoms, diagnosis, medications, allergies, key_events) with one retry and runtime type validation on LLM output.

**Key patterns:**
- Profile reads use `async_session()` directly (NOT `get_db()`) — `get_db()` is an async generator only usable inside FastAPI DI.
- `MemoryContext.formatted_prompt` is injected into the system prompt by `ResponseGenerator` when non-empty.
- `save_turn()` is called via `BackgroundTasks` in the chat API after SSE streaming completes (non-blocking).

### MCP framework (`backend/app/core/mcp/`)

Plugin-based tool architecture for Agent tool scheduling (Step 6 of PRD). Follows the same patterns as the model adapter layer:

- `base.py` — `BaseMCPModule` ABC defining the plugin contract: `module_name`, `get_tools() -> list[ToolDefinition]`, `async execute(tool_name, params) -> ToolCallResponse`. Each module can override `timeout` (default 10s from `settings.mcp_default_timeout`).
- `registry.py` — `MCPToolRegistry` with `register()`, `get_all_tools()`, and `async invoke()`. `invoke()` wraps execution in `asyncio.wait_for` and catches `TimeoutError`/`Exception` to return degraded `ToolCallResponse` with `TIMEOUT`/`ERROR` status. `get_mcp_registry()` is a lazy singleton that imports modules inside the function body to avoid import-time side effects.
- `patient_record.py` — `PatientRecordModule` with 3 tools (`patient_record.query_case`, `patient_record.query_visit`, `patient_record.query_prescription`). Currently uses mock HIS data keyed by user_id; `_resolve_patient()` queries the users table via `async_session()` for fuzzy name matching.
- `identity.py` — `IdentityModule` with 3 tools (`identity.verify_patient`, `identity.verify_doctor`, `identity.get_permissions`). Verifies user roles against the database and returns role-based permission lists from `ROLE_PERMISSIONS`.

**Key patterns:**
- Tool names use dot-separated namespace: `{module_name}.{tool_name}` (e.g., `identity.verify_patient`).
- Registry indexes tools in O(1) via a `_tool_index` dict mapping `tool_name -> module_name`.
- MCP modules use `async_session()` directly (same pattern as memory system) — they are not FastAPI DI contexts.
- `get_mcp_registry()` imports modules lazily inside the function body so test patches apply before module initialization.

### Agent ReAct engine (`backend/app/core/agent/`)

The ReAct (Reasoning + Acting) engine lets the LLM autonomously decide which tools to invoke before answering. It replaces the old hardcoded linear pipeline:

- `react_engine.py` — `ReActEngine.run()` loop: Thought → Action → Action Input → Observation, max `MAX_ITERATIONS` (5). Uses Chinese-format labels (思考/行动/行动输入/观察) with fullwidth colon support. LLM output parsed via line-anchored regex.
- `tool_router.py` — `ToolRouter.execute()` dispatches actions: `rag.search` → hybrid retriever + post-processor, `memory.get_context` → memory service, `finish` → empty string, anything else → MCP registry invoke.
- `orchestrator.py` — `Orchestrator.run()` wires: Intent → Memory → ReAct loop → Response generation with tool context + reasoning steps.
- `response_gen.py` — `ResponseGenerator.generate()` accepts `react_steps` to inject tool observations into the system prompt via `_build_tool_context()`.

**Key patterns:**
- `REACT_SYSTEM` template uses `{{` `}}` escaping for JSON examples (Python `.format()` double-brace escape).
- `_extract_section(text, tag)` uses `r'^{tag}\s*[：:]\s*(.+)$'` with `re.MULTILINE` — line-anchored to avoid matching tags inside Chinese words.
- `_build_tool_descriptions()` queries `get_mcp_registry().get_all_tools()` at runtime so new MCP modules auto-appear in the LLM prompt.
- ToolRouter routes ALL non-builtin actions to MCP — no `mcp.` prefix; tool names are `{module_name}.{tool_name}` directly.

### RAG pipeline (`backend/app/core/rag/`)

- `query_processor.py` — LLM-based rewrite + decomposition (short queries <40 chars skip decomposition)
- `adaptive_router.py` — role→collection mapping, complexity→strategy selection
- `bm25_index.py` — jieba Chinese tokenization + rank_bm25 Okapi
- `hybrid_retriever.py` — parallel BM25 + vector, loads docs from ChromaDB for BM25 indexing
- `post_processor.py` — RRF (k=60) fusion + Qwen3-Reranker semantic scoring
- `citation.py` — source metadata extraction into structured `SourceCitation` objects

### Database layer

Three storage backends managed in `backend/app/db/`:
- **MySQL** (SQLAlchemy 2.0 async + aiomysql) — users, profiles (PatientProfile), conversations, care_plans (CarePlan), knowledge_sources
- **Redis** (aioredis) — session context cache, rate limiting, task queues
- **ChromaDB** (HTTP client, port 8001) — 4 collections: `kb_patient`, `kb_professional`, `user_memory`, `drug_db`

### Multimodal (`backend/app/core/multimodal/`)

Voice and medical report processing via Doubao (火山引擎 ARK) API. The ARK platform provides OpenAI-compatible endpoints for STT, TTS, and vision:

- `doubao_client.py` — `DoubaoClient` wraps the ARK API (`https://ark.cn-beijing.volces.com/api/v3`). `speech_to_text()` base64-encodes audio → `/audio/transcriptions` (whisper-1 model). `text_to_speech()` → `/audio/speech` returns MP3 bytes. `ocr_image()` base64-encodes the image → `/chat/completions` with `doubao-vision-pro-32k` model. Auth via `Bearer {api_key}` header; optional `x-app-id` header. Lazy singleton via `get_doubao_client()`.
- `file_storage.py` — MinIO upload/download for report files. `upload_to_minio()` returns date-prefixed paths (`YYYY/MM/DD/uuid_filename.ext`), auto-creates the bucket on first use.
- `ocr.py` — `extract_text(file_bytes, mime_type)` → calls DoubaoClient OCR; `interpret_report(extracted_text)` → calls `get_adapter_registry().generate()` with a structured medical interpretation prompt, parses JSON with markdown code-block stripping and fallback.

**Key pattern:** `ocr.py` uses `import app.core.multimodal.doubao_client` (NOT `from ... import`) so test patches at the source module take effect.

### Frontend (`frontend/src/`)

React 18 + TypeScript + Vite. Zustand for state (authStore, chatStore, searchStore, voiceStore). Routes guarded by `ProtectedRoute` with role checking. SSE streaming uses `fetch()` + `ReadableStream` (NOT `EventSource`) to support POST with JWT Authorization header.

Page structure:
- **Patient** (`/patient/*`): Chat (main), History (paginated session list), CarePlan (active plans), ReportDetail (OCR interpretation)
- **Doctor** (`/doctor/*`): Search (RAG knowledge base), PatientRecord (HIS mock data via PatientRecordView), SearchHistory (paginated session list)

Key patterns:
- `streamChat()` in `frontend/src/api/chat.ts` is an async generator that yields `SSEChunk` objects parsed from the SSE stream.
- `ReasoningChain` component renders ReAct reasoning steps (思考/行动/行动输入/观察) in a collapsible panel with color-coded labels. Displayed above chat messages when `currentReasoningSteps` is non-empty.
- `PatientRecordView` component displays structured patient data (基本信息, 病例记录, 就诊记录, 处方记录) as formatted JSON blocks.
- `VoiceInput` component uses `MediaRecorder` API with `onMouseDown`/`onMouseUp`/`onTouchStart`/`onTouchEnd` for press-to-talk recording.
- `ReportUploader` component handles drag-and-drop + file input for medical report images/PDFs, then calls upload → interpret flow.
- `AudioPlayer` component manages `<audio>` element with `URL.createObjectURL`/`revokeObjectURL` lifecycle for TTS playback.
- All pages use 100% inline styles (no CSS modules or styled-components).
- API functions in `frontend/src/api/` use raw `fetch()` with Bearer token from `useAuthStore`. 401 responses trigger redirect to `/login`.

## Key conventions

- Backend follows thin-routers pattern: `api/` layer validates params and delegates to `core/`
- All LLM calls go through `get_adapter_registry()`, never to a specific adapter directly
- `RequestContext` (user_id, role, kb_collection, response_template) is injected via FastAPI `Depends(get_request_context)`
- Error handling: adapters retry 3x with exponential backoff in the registry chain. RAG failures degrade gracefully (BM25 fails → use vector only, and vice versa). Memory layers degrade independently via `asyncio.gather(return_exceptions=True)`.
- Memory services (`get_redis()`, `get_chroma()`) can return `None` if the service isn't initialized — always guard with `if x is None: return []` before using.
- For non-DI contexts (background tasks, memory reader), use `async_session()` from `app.db.session` directly — `get_db()` only works inside FastAPI's dependency injection.
- Chinese medical text tokenization uses `jieba` (not whitespace splitting) for BM25
- **Python 3.11–3.12 required.** Python 3.13 causes numpy 1.26.4 segfaults (chromadb-client depends on numpy<2.0). Use Python 3.12 for development.
- **`import module` pattern for test-patchable dependencies.** Never use `from app.db.session import async_session` — it captures the reference at import time and blocks test patching. Always `import app.db.session` and access `app.db.session.async_session()` at runtime. Same applies to `from app.core.model_adapter.adapter_registry import get_adapter_registry` and similar singletons that tests need to mock.

## Spec and plan docs

- PRD: `docs/superpowers/specs/2026-05-08-medagent-prd.md`
- Memory system design: `docs/superpowers/specs/2026-05-08-memory-system-design.md`
- Memory system plan: `docs/superpowers/plans/2026-05-08-memory-system-plan.md`
- Step 8 multimodal plan: `C:\Users\20530\.claude\plans\hashed-wibbling-storm.md`

## Test architecture

Three-tier test suite in `backend/tests/`, all using `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` needed):

```
tests/
├── conftest.py          # test_settings fixture (SQLite URL, test secrets)
├── unit/                # Pure sync unit tests — no I/O, no async
│   ├── test_bm25_index.py       # jieba tokenization + BM25 search
│   ├── test_adaptive_router.py  # role→collection, complexity→strategy
│   ├── test_post_processor.py   # RRF fusion (k=60), dedup, sorting
│   ├── test_citation.py         # SourceCitation field extraction
│   ├── test_jwt.py              # JWT create/decode roundtrip
│   ├── test_schemas.py          # Pydantic model validation
│   ├── test_short_term.py       # Redis short-term memory ops
│   ├── test_event_extractor.py  # LLM event extraction + JSON parsing
│   ├── test_memory_reader.py    # 3-layer memory fusion + degradation
│   ├── test_mcp_base.py         # BaseMCPModule ABC + timeout config
│   └── test_mcp_schemas.py      # ToolStatus, ToolDefinition, ToolCall* models
├── async_unit/          # Async unit tests — mock LLM adapter, no real I/O
│   ├── conftest.py              # mock_adapter fixture + patch_registry
│   ├── test_intent.py           # IntentClassifier with mocked LLM
│   ├── test_query_processor.py  # Query rewrite + decomposition
│   ├── test_response_gen.py     # ResponseGenerator prompt injection
│   ├── test_adapter_registry.py # AdapterRegistry chain fallback
│   ├── test_long_term.py        # ChromaDB long-term memory
│   ├── test_memory_service.py   # MemoryService facade orchestration
│   ├── test_mcp_registry.py     # Registry routing + timeout + error handling
│   ├── test_mcp_patient_record.py # PatientRecordModule mock HIS queries
│   ├── test_mcp_identity.py     # IdentityModule role verification + permissions
│   ├── test_react_engine.py     # ReAct loop: parsing, max iter, observations
│   ├── test_tool_router.py      # ToolRouter: RAG/MCP/Memory dispatch
│   ├── test_orchestrator.py     # Orchestrator: SSE events, memory passthrough
│   ├── test_doubao_client.py    # DoubaoClient STT/TTS/OCR + auth headers
│   └── test_ocr.py              # OCR extraction + LLM report interpretation
└── api/                 # API integration tests — httpx ASGITransport + SQLite :memory:
    ├── conftest.py              # app.dependency_overrides + mock services
    ├── test_auth.py             # register/login/me endpoints
    ├── test_chat.py             # SSE streaming endpoint
    ├── test_search.py           # RAG search endpoint
    ├── test_mcp.py              # MCP tools/invoke endpoint integration
    ├── test_voice.py            # Voice transcribe/synthesize endpoints
    ├── test_report.py           # Report upload/interpret endpoints
    ├── test_chat_history.py     # Chat history pagination + detail
    ├── test_patient.py          # Patient profile + care plan CRUD
    └── test_doctor.py           # Doctor patient record access control
```

Key test patterns:
- **API tests** use `app.dependency_overrides[get_db]` (FastAPI official) to inject SQLite, NOT `patch()`. The real `app.db.session.engine` and `app.db.session.async_session` are patched at module level before the app lifespan runs.
- **API conftest** patches `get_adapter_registry` in all agent modules: `intent`, `query_processor`, `response_gen`, `react_engine`, and the `event_extractor`.
- **Async unit tests** use a `StreamWrapper` class (not `AsyncMock`) to capture call args from async generator functions like `generate_stream()`.
- **ReAct engine tests** feed multi-step `generate.side_effect` lists to simulate LLM outputs across ReAct iterations, then assert on `result.steps[i].action/observation/action_input`.
- **ToolRouter tests** patch `router.hybrid_retriever.search` and `router.post_processor.process` with `AsyncMock` for RAG tests; patch `get_mcp_registry` for MCP dispatch tests.
- **Orchestrator tests** iterate the async generator `orchestrator.run()` to collect SSE events, then assert on `type` and `content`/`steps`/`sources` fields.
- **MCP async unit tests** have two mocking strategies: PatientRecordModule tests mock `_resolve_patient` directly with `AsyncMock`; IdentityModule tests patch `async_session()` and use a `_make_session()` helper that sets `mock_db.execute.return_value = MagicMock()` (NOT `AsyncMock`) to prevent coroutine cascade in `scalar_one_or_none()` calls.
- **MCP registry tests** use an inline `MockModule` subclass with dual sync/async `execute_fn` support, rather than `MagicMock` directly.
- **Unit tests** are plain `def` functions; `pytest-asyncio` auto-mode converts `async def` tests automatically.
- Test database is SQLite `aiosqlite:///:memory:` — no MySQL needed for tests.
