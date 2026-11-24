# Shadow AI — Complete Testing Baseline Report

**Project:** Shadow AI
**Repository:** `~/Shadow---AI`
**Current Branch:** `redesign/pastel-aura`
**Date:** November 24, 2026
**Auditor:** Senior QA Automation Engineer, Application Security Tester & Full-Stack Developer

---

## 1. Project Overview & Technologies

Shadow AI is an enterprise security gateway designed to intercept, analyze, sanitize, and govern user interactions with Large Language Models (LLMs). It provides data loss prevention (DLP), multi-modal document inspection (OCR, PDF, DOCX, XLSX, PPTX), credential/secret masking, threat detection, human-in-the-loop (HITL) approval, and audit trails.

### 1.1 Backend Technologies
- **Runtime:** Python 3.14.10 (x86_64 Linux)
- **Framework:** FastAPI (with Starlette ASGI core and Uvicorn server)
- **DLP & Entity Detection:**
  - Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`)
  - Spacy (`en_core_web_lg`)
  - Custom contextual and regular expression pattern recognizers
  - Encoding detectors (Base64, Rot13, Homoglyphs, Zero-width spaces)
- **Multi-Modal Document Processing:**
  - Tesseract OCR 5.5.0 (`pytesseract`) with automated cross-platform binary resolution
  - PyMuPDF (`fitz` 1.25.3) for PDF parsing and page-level OCR rendering
  - `python-docx` for Word document processing
  - `openpyxl` for Excel spreadsheet processing
  - `python-pptx` for PowerPoint presentation processing
  - `Pillow` (PIL) for image normalization and OCR preprocessing
- **AI Integrations:**
  - Ollama AsyncClient (`http://localhost:11434`, model: `gemma3:4b`)
  - Google Gemini integration architecture
- **Databases & Persistence:**
  - Redis 8.0.6 (`localhost:6379`) — User account store, active sessions, password reset tokens, pending HITL queue, and stateful session risk histories.
  - SQLite 3 (`data/shadow_ai_conversations.db`, WAL journal mode) — Conversation threads and message audit logs.

### 1.2 Frontend Technologies
- **Architecture:** Semantic HTML5, Vanilla ES6 JavaScript, CSS3 Custom Properties (Variables)
- **Design System:** Pastel Aura (`#E4D7CF` Taupe × `#D9A9AE` Rose Dust), Glassmorphism, Responsive Grid / Flexbox
- **Theme Support:** Dynamic Light and Dark modes with `localStorage` persistence and `prism-theme-init.js`
- **Total Pages:** 20 HTML pages (2 core workspace pages + 18 modular analytics & governance views)

---

## 2. Application Entry Points

- **ASGI Web Server:** FastAPI / Uvicorn server (Default port: `8000` / `58015`)
  - Server start command: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
- **Web Portal Routes:**
  - `GET /` — Authentication Portal (`frontend/login.html`)
  - `GET /dashboard` — Primary Analyst Workspace & AI Chat Gateway (`frontend/index.html`)
  - `GET /views/{view_name}` — Dynamic secure router for modular analytics pages
  - `GET /assets/*` — Static asset mount serving CSS, JS, icons, and SVG tokens
  - `GET /favicon.ico` — Application brand icon handler

---

## 3. API Endpoints & HTTP Methods

| Method | Endpoint | Authentication | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | Returns gateway operational status, Presidio status, and Redis connectivity. |
| `POST` | `/auth/signup` | None | Registers a new Analyst account in Redis. |
| `POST` | `/auth/login` | None | Authenticates credentials, generates session ID, and sets secure cookie. |
| `GET` | `/auth/me` | Cookie (`shadow_ai_auth`) | Returns profile and role of currently signed-in user. |
| `POST` | `/auth/logout` | Cookie (`shadow_ai_auth`) | Revokes user session from Redis and clears session cookie. |
| `POST` | `/auth/forgot-password` | None | Generates a time-limited password reset token. |
| `POST` | `/auth/reset-password` | None | Verifies token and updates password hash. |
| `GET` | `/conversations` | Cookie (`shadow_ai_auth`) | Fetches all active and historical chat sessions for user. |
| `GET` | `/conversations/{session_id}` | Cookie (`shadow_ai_auth`) | Retrieves chronological messages, DLP audit decisions, and metadata. |
| `POST` | `/gateway/scan` | Cookie (`shadow_ai_auth`) | Intercepts, scans, scores, and enforces DLP policy on prompt text. |
| `POST` | `/gateway/hitl` | Cookie (`shadow_ai_auth`) | Resolves pending human-in-the-loop review (ALLOW, SANITIZE_AND_SEND, BLOCK). |
| `POST` | `/gateway/scan-file` | Cookie (`shadow_ai_auth`) | Inspects uploaded documents/images and enforces DLP. |

---

## 4. Database Models & Schema Relationships

### 4.1 Redis Data Structures (`localhost:6379`)
1. **User Accounts:** `shadow_ai:user:{username}` (Hash)
   - Fields: `full_name`, `username`, `email`, `password_hash`, `role`, `created_at`
2. **Email Index:** `shadow_ai:email:{email}` (String)
   - Value: `{username}` (Enforces unique email mapping)
3. **Session Store:** `shadow_ai:auth:{session_id}` (Hash)
   - Fields: `username`, `created_at` (TTL: 3600 seconds)
4. **Password Reset Tokens:** `shadow_ai:reset:{token}` (String)
   - Value: `{username}` (TTL: 900 seconds)
5. **Pending HITL Decisions:** `pending_hitl:{session_id}` (String)
   - Value: JSON-serialized request context awaiting analyst review
6. **Session Risk History:** `shadow_ai:history:{session_id}` (String)
   - Value: JSON-serialized list of past risk events for stateful cumulative scoring

### 4.2 SQLite Schema (`data/shadow_ai_conversations.db`)
1. **`conversations` Table:**
   - `username` (TEXT, NOT NULL)
   - `session_id` (TEXT, NOT NULL)
   - `title` (TEXT, NOT NULL)
   - `created_at` (INTEGER, NOT NULL)
   - `updated_at` (INTEGER, NOT NULL)
   - **Primary Key:** `(username, session_id)`
   - **Index:** `idx_conversations_user_updated` on `(username, updated_at DESC)`

2. **`conversation_messages` Table:**
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `username` (TEXT, NOT NULL)
   - `session_id` (TEXT, NOT NULL)
   - `role` (TEXT, NOT NULL — e.g. "user", "assistant", "system")
   - `content` (TEXT, NOT NULL)
   - `input_type` (TEXT, DEFAULT 'text')
   - `file_name` (TEXT, NULLABLE)
   - `decision` (TEXT, NULLABLE — "ALLOW", "BLOCK", "HITL", "SANITIZE_AND_SEND")
   - `risk_level` (TEXT, NULLABLE — "LOW", "MEDIUM", "HIGH", "CRITICAL")
   - `risk_score` (REAL, DEFAULT 0.0)
   - `redacted` (INTEGER, DEFAULT 0)
   - `metadata_json` (TEXT, DEFAULT '{}')
   - `created_at` (INTEGER, NOT NULL)
   - **Foreign Key:** `(username, session_id) REFERENCES conversations(username, session_id) ON DELETE CASCADE`
   - **Index:** `idx_messages_user_session` on `(username, session_id, id)`

---

## 5. Dependencies and Configuration

- **Virtual Environment:** `.venv/` (Python 3.14.10)
- **Configuration Files:**
  - `.env.example`: Documents environment variables (`REDIS_HOST`, `REDIS_PORT`, `SQLITE_PATH`, `OLLAMA_HOST`, `OLLAMA_MODEL`)
  - `pytest.ini`: Configures test discovery in `tests/` and test paths.
- **Key Installed Packages:**
  - `fastapi`, `uvicorn`, `redis`, `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `pymupdf`, `python-docx`, `openpyxl`, `python-pptx`, `pytesseract`, `pillow`, `pytest`, `pytest-asyncio`, `playwright` (available in environment).

---

## 6. Existing Tests & Commands

- **Unit & Integration Suite:** `tests/`
- **Execution Command:** `source .venv/bin/pytest`
- **Current Baseline Test Status:** 58 tests passed in 5.33 seconds
  - `tests/test_detection.py`: 25 passed
  - `tests/test_enforcement.py`: 5 passed
  - `tests/test_multimodal.py`: 11 passed
  - `tests/test_risk_policy.py`: 17 passed

---

## 7. Git Status & Uncommitted Work

- **Active Branch:** `redesign/pastel-aura`
- **Status:** Uncommitted working tree changes preserved and intact.
- **Modified files:**
  - `backend/main.py`: Favicon route, login parameter default handling.
  - `backend/risk_engine.py`: URL entity weight addition.
  - `backend/test_hitl.py`: Async execution wrapper.
  - `backend/test_redis_store.py`: Async main entry point.
  - `detection/basic_detector.py`: Standalone URL detection regex with email boundary guards.
  - `detection/custom_recognizers.py`: Stopwords filter to reduce false positive password detection.
  - `detection/normalizer.py`: Normalization mappings for URL entities.
  - `detection/presidio_detector.py`: Filter preventing URLs from matching inside email addresses or file names.
  - `frontend/assets/prism-chat-final.css`: Responsive dashboard layouts, CSS variables, and panel dimensions.
  - `frontend/assets/prism-pages.js`: Updated navigation labels (Adversary Simulation, Gateway Intelligence).
  - `frontend/index.html`: Responsive grid refinements (`260px minmax(0,1fr) 320px`), flex container adjustments.
  - `frontend/views/data-analyst.html`: Gateway Intelligence title update.
  - `frontend/views/red-team.html`: Adversary Simulation title update.
  - `processing/image_processor.py`: Dynamic Tesseract binary path detection.
  - `processing/pdf_processor.py`: Dynamic Tesseract binary path detection.

---

## 8. Current Application State

- Redis server running on `127.0.0.1:6379`.
- Tesseract OCR 5.5.0 verified and functioning.
- Spacy `en_core_web_lg` model loaded.
- SQLite database verified at `data/shadow_ai_conversations.db`.
- Baseline suite: 58/58 unit tests passing.
