# Shadow AI — Complete Project Workflow, DLP Pipeline & Module Audit

**Document:** Comprehensive System Walkthrough & Technical Audit  
**Project:** Shadow AI — Enterprise AI Security Gateway & Reverse Proxy  
**Current Branch:** `redesign/pastel-aura`  
**Author:** Senior Full-Stack Software Architect, Cybersecurity Auditor & QA Specialist  
**Date:** November 23, 2026  

---

## 1. Executive Summary

Shadow AI is an enterprise-grade AI Security Gateway and Data Loss Prevention (DLP) reverse proxy built to protect organizations from accidental data leakage, credential exposure, and prompt-injection attacks when employees interact with AI language models.

Rather than giving client applications unconstrained access to LLMs, Shadow AI sits inline as an intelligent proxy. Every prompt and document is intercepted, parsed, evaluated by multiple DLP engines, assessed for cumulative multi-turn risk, and routed according to strict security policies before any external or internal AI invocation can take place.

---

## 2. Authentication & Session Security (Phase 2 Walkthrough)

### 2.1 The Login Interface (`frontend/login.html`)
The login screen features the Pastel Aura design system with an interactive constellation canvas background (`#shadow-constellation`), responsive glass cards, and accessible ARIA attributes. It provides three operational screens switched without page reload:
1. **Login Screen (`#loginScreen`)**: User credential inputs for username or email and password.
2. **Registration Screen (`#signupScreen`)**: New account onboarding with input validation.
3. **Password Recovery Screen (`#forgotScreen`)**: Self-service reset token request.

### 2.2 Client-Side Validation
Input fields are validated before network submission:
- **Username / Login**: Validated via regex `^[A-Za-z0-9_.-]{3,32}$`. Disallows whitespace and shell metacharacters.
- **Email**: Validated via RFC 5322 regex pattern `^[^@\s]+@[^@\s]+\.[^@\s]+$`.
- **Password**: Enforces length constraints (8 to 128 characters) and matching confirmation fields during registration.

### 2.3 Backend Authentication Flow (`backend/auth.py` & `backend/main.py`)
1. **Submission**: The user submits credentials to `POST /auth/login`.
2. **Account Lookup**: The backend checks if the login contains `@`. If present, it queries `shadow_ai:email:<email>` in Redis to resolve the canonical username; otherwise, it queries `shadow_ai:user:<username>`.
3. **Password Verification**: Passwords are never stored in plaintext. They are hashed using `bcrypt.hashpw()` with random salts. Verification calls `bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))`.
4. **Session Token Generation**: Upon successful authentication, the server generates a cryptographically secure 48-byte URL-safe token using `secrets.token_urlsafe(48)`.
5. **Redis Session Storage**: The token is saved to Redis key `shadow_ai:auth:<token>` with metadata:
   ```json
   {
     "username": "analyst_qa",
     "created_at": "2026-11-23T12:00:00+00:00"
   }
   ```
   A strict Time-to-Live (TTL) of 3600 seconds (1 hour) is set via `redis_client.expire(key, 3600)`.
6. **Cookie Delivery**: The backend returns an HTTP `Set-Cookie` header:
   ```http
   Set-Cookie: shadow_ai_auth=<token>; HttpOnly; Max-Age=3600; Path=/; SameSite=lax
   ```
   The `HttpOnly` flag prevents client-side JavaScript from accessing the session token, mitigating XSS session hijacking.

### 2.4 Session Expiration & Logout
- **Active Verification (`get_current_user`)**: Every protected endpoint evaluates `request.cookies.get("shadow_ai_auth")`. If the token is missing or has expired in Redis, a `401 Unauthorized` exception is thrown, prompting the frontend to redirect to `/`.
- **Logout (`POST /auth/logout`)**: Deletes the session key from Redis (`redis_client.delete()`) and clears the cookie in the client response (`response.delete_cookie("shadow_ai_auth")`).

---

## 3. Main Workspace Walkthrough (Phase 3 Walkthrough)

The main workspace ([frontend/index.html](file:///home/titan/Shadow---AI/frontend/index.html)) serves as the primary conversational interface for analysts.

### 3.1 Header & System Navigation
- **Brand Mark**: Displays "SHADOW **AI**" with gradient typography.
- **Tools Menu (`#prismToolsMenu`)**: Injected dynamically by [frontend/assets/prism-pages.js](file:///home/titan/Shadow---AI/frontend/assets/prism-pages.js). Exposes grouped navigational shortcuts to all 18 security views without cluttering the screen.
- **Theme Switcher**: Interacts with [frontend/assets/prism-theme.js](file:///home/titan/Shadow---AI/frontend/assets/prism-theme.js) to toggle between Pastel Aura Light and Dark themes, persisting the preference to `localStorage.getItem("shadow-ai-theme")`.
- **User Profile Pill**: Queries `GET /auth/me` on page load to fetch the analyst's full name, role, and initials for the avatar badge.

### 3.2 Sidebar & Conversation History
- **New Chat Button (`#newChatBtn`)**: Clears the current active session in `sessionStorage` (`shadow_ai_session_id`), empties the message scroll container, and restores the starter question cards.
- **Stored Conversations List**: Calls `GET /conversations` to fetch recent chats from SQLite. Clicking an entry retrieves the stored messages via `GET /conversations/{session_id}` and renders the conversation history with sanitized tokens and past policy badges.

### 3.3 Composer & Multimodal Attachments
- **Textarea (`#message`)**: Elastic auto-expanding input for multi-line prompts. Submits on Enter and inserts newlines on Shift+Enter.
- **Attachment Button (`#attachBtn`)**: Triggers an invisible file input accepting PDF, DOCX, XLSX, PPTX, TXT, PNG, JPG, BMP, TIFF, and WebP files. Displays a dismissible file chip with human-readable file size before submission.
- **Send Button (`#sendBtn`)**: Disables itself upon click, sets the avatar animation state to `thinking`, and dispatches the payload to either `/gateway/scan` (for text) or `/gateway/scan-file` (for multipart uploads).

### 3.4 Security Insights Drawer (`#securityInsightsPanel`)
A collapsible right-hand drawer providing real-time telemetry:
- **Decision Donut Chart**: A conic-gradient SVG chart illustrating the breakdown between Allowed (Green), Sanitized (Amber), and Blocked (Red) requests.
- **Recent Detections**: Live feed of the latest 5 entity findings flagged in the active session.
- **Gateway Counters**: Cumulative counters tracking PII detections, Secrets, OCR analyses, and processed documents.
- **Policy Guardrails Checklist**: Visual indicators showing that input DLP, credential detection, prompt-injection filters, and human-in-the-loop review are active.

---

## 4. Security Gateway & DLP Processing Pipeline (Phase 4 Walkthrough)

Every prompt submitted to Shadow AI traverses an 8-stage inspection pipeline:

```
User Prompt ──► Validation ──► Multimodal Parsing ──► DLP Detection ──► Normalization ──► Contextual Risk Engine ──► Policy Evaluation ──► AI / HITL
```

### 4.1 Stage 1: Validation
The gateway verifies that the incoming request contains non-empty text or a valid file attachment and an active `session_id`. Empty or malformed inputs are rejected immediately with HTTP 400.

### 4.2 Stage 2: Multimodal Document Parsing (`processing/`)
If a file attachment is provided, the gateway delegates to specialized extractors:
- **PDF Documents (`processing/pdf_processor.py`)**: Uses `pypdf` to extract text streams and embedded metadata.
- **Word Documents (`processing/docx_processor.py`)**: Uses `python-docx` to iterate through paragraphs, tables, and document properties.
- **Excel Spreadsheets (`processing/xlsx_processor.py`)**: Uses `openpyxl` to extract cell values and sheet names.
- **PowerPoint Presentations (`processing/pptx_processor.py`)**: Uses `python-pptx` to parse slide shapes, text frames, and speaker notes.
- **Images (`processing/image_processor.py`)**: Ingests image bytes, applies contrast preprocessing, and runs Tesseract OCR (`pytesseract`) to extract embedded text.

### 4.3 Stage 3: Multi-Engine DLP Detection (`detection/`)
Extracted text is submitted to `detection_pipeline.run_detection()`, running three complementary detection tiers:
1. **Basic Regex Detector (`detection/basic_detector.py`)**:
   - `EMAIL`: RFC 5322 regex pattern.
   - `URL`: Matches `https?://`, `www.`, and verified top-level web domains (`.com`, `.org`, `.net`, `.io`, `.ai`, etc.) while ignoring domains inside email addresses.
   - `IP_ADDRESS`: Matches private IPv4 CIDR blocks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and public IP structures.
   - `PHONE`: Matches international and domestic phone formats.
   - `PASSWORD`: Matches common assignment syntax (e.g. `password = "Secret123"`).
2. **Microsoft Presidio & Spacy NER (`detection/presidio_detector.py`)**:
   - Leverages Spacy's `en_core_web_sm` model and Presidio's `AnalyzerEngine`.
   - Recognizes `PERSON` (names), `LOCATION` (cities/countries), `DATE_TIME`, and `CREDIT_CARD`.
   - Filters out overlapping phone numbers from IP addresses and strips invalid subword URL matches (e.g. prevents flagging `report.docx` as `.do` TLD).
3. **Custom Recognizers & Threat Classifiers (`detection/custom_recognizers.py`)**:
   - `EMPLOYEE_ID`: Matches corporate employee identifiers (e.g., `EMP-12345`).
   - `API_KEY_LIKE`: High-entropy regex identifying AWS, GitHub, OpenAI, and generic API keys.
   - `DATABASE_CREDENTIAL`: Identifies connection URIs containing username/password credentials.
   - `ROT13_DETECTOR` & `BASE64_DETECTOR`: Flags obfuscated text payloads intended to evade keyword filters.
   - `PROMPT_INJECTION_DETECTOR`: Flags adversarial jailbreak attempts (e.g., "ignore all previous instructions", "DAN mode", system prompt leak requests).

### 4.4 Stage 4: Deduplication & Normalization (`detection/normalizer.py`)
Because multiple detectors analyze the same text in parallel, findings often overlap.
- `canonical_type()` maps diverse vendor names to standard identifiers (`EMAIL_ADDRESS -> EMAIL`, `PHONE_NUMBER -> PHONE`, `URL -> URL`).
- Overlapping findings spanning the same character indices are merged: the finding with the highest confidence is retained, and detection sources are concatenated (e.g. `source: "BASIC+PRESIDIO"`).
- Cross-type collision rules discard URL findings that fall entirely within an email address span.

### 4.5 Stage 5: Contextual & Multi-Turn Risk Scoring (`backend/risk_engine.py`)
Rather than relying on static single-turn thresholds, Shadow AI calculates contextual risk using three additive mathematical components:

$$\text{Risk}_{\text{total}} = \text{Risk}_{\text{isolated}} + \text{Risk}_{\text{historical}} + \text{Risk}_{\text{synergy}}$$

1. **Isolated Risk ($\text{Risk}_{\text{isolated}}$)**:
   $$\text{Risk}_{\text{isolated}} = \sum_{i} \left( \text{Weight}(E_i) \times \text{Confidence}_i \right)$$
   Where entity weights are calibrated based on sensitivity:
   - `DATABASE_CREDENTIAL`: $100.0$
   - `API_KEY_LIKE` / `CREDIT_CARD`: $90.0$
   - `PASSWORD`: $80.0$
   - `EMPLOYEE_ID` / `IP_ADDRESS`: $30.0$
   - `EMAIL` / `PHONE` / `URL` / `PROMPT_INJECTION`: $20.0$
   - `PERSON`: $10.0$
   - `DATE_TIME`: $0.0$

2. **Historical Risk ($\text{Risk}_{\text{historical}}$)**:
   Recognizes that adversaries split sensitive data across multiple conversation turns to avoid single-turn triggers. Recent turns have more weight than older turns using an exponential decay factor $\lambda = 0.8$:
   $$\text{Risk}_{\text{historical}} = \sum_{k=1}^{N} \lambda^{(N - k)} \times \text{TurnRisk}_k$$

3. **Synergy Risk ($\text{Risk}_{\text{synergy}}$)**:
   Amplifies risk when combinations of entities appear together that create an identity-theft or system-compromise vector:
   $$\text{Risk}_{\text{synergy}} = \alpha \times 10.0 \quad (\alpha = 1.5)$$
   Triggered when `EMAIL` + `PASSWORD`, `EMPLOYEE_ID` + `PASSWORD`, or `IP_ADDRESS` + `API_KEY_LIKE` co-occur across the active session.

### 4.6 Stage 6: Policy Evaluation (`backend/policy.py`)
The total risk score is mapped to a definitive operational action:
- **$\text{Risk}_{\text{total}} \le 10.0$ (`TAU_LOW`)**: Action = `ALLOW`. The request is benign; forward directly to the AI model.
- **$10.0 < \text{Risk}_{\text{total}} \le 25.0$ (`TAU_HITL`)**: Action = `QUARANTINE_HITL`. Moderate sensitivity (e.g., single email or URL); prompt the human analyst for disposition.
- **$\text{Risk}_{\text{total}} > 25.0$**: Action = `BLOCK` / `CRITICAL HITL`. High-risk sensitivity (e.g. passwords or database credentials); quarantined and blocked from upstream AI forwarding.

### 4.7 Stage 7: Redaction & Sanitization (`backend/masking.py`)
When the decision is `SANITIZE_AND_SEND`, all detected entities are replaced with synthetic, type-specific tokens:
- Passwords $\rightarrow$ `[SYNTHETIC_PASSWORD]`
- Emails $\rightarrow$ `analyst@example.com`
- URLs $\rightarrow$ `https://example.com`
- Names $\rightarrow$ `[SYNTHETIC_PERSON]`
- Dates $\rightarrow$ `[SYNTHETIC_DATE_TIME]`

The sanitized prompt is then safely forwarded to the upstream AI model, ensuring the model never observes real corporate secrets while maintaining semantic context.

### 4.8 Stage 8: Dual Persistence & Audit Logging
1. **Redis**: Updates the current session history with the new turn score and findings list (capped at 20 turns, 3600s TTL). If quarantined for HITL, the raw prompt is saved to `shadow_ai:hitl:<session_id>`.
2. **SQLite (`data/shadow_ai_conversations.db`)**: Writes an immutable audit record to `conversation_messages` with user identity, decision, risk score, redacted flag, and detection metadata.

---

## 5. Comprehensive Audit of All 18 Views (Phase 5 Review)

| # | View Route | Module Name | Primary Purpose | Key Interactive Elements | Implementation Status |
|---|---|---|---|---|---|
| **01** | `/views/dashboard.html` | Security Dashboard | Executive overview of gateway activity, real-time posture, and threat metrics. | KPI tiles, decision distribution chart, timeframe filters, export CSV button. | **FULLY IMPLEMENTED** (Live data via SQLite) |
| **02** | `/views/data-analyst.html` | Gateway Intelligence | Security benchmark research, V1 vs V2 engine comparison, precision/recall analysis. | Comparison cards, F1 score indicators, bypass metrics, stateful risk experiment tab. | **FULLY IMPLEMENTED** (UI + Preserved Experiment) |
| **03** | `/views/red-team.html` | Adversary Simulation | Controlled validation of DLP robustness against prompt injections and jailbreaks. | Test scenario cards, evasion simulation trigger, evasion rate metrics. | **FULLY IMPLEMENTED** (UI + Preserved Benchmark) |
| **04** | `/views/policy-management.html` | Policy Management | Operational controls for enabling/disabling security guardrails and review thresholds. | Policy toggle switches, risk threshold controls, rule status indicators. | **PARTIALLY IMPLEMENTED** (Persists in localStorage) |
| **05** | `/views/audit-logs.html` | Audit Logs | Governance interface for auditing all user requests, decisions, and redacted findings. | Keyword search input, decision dropdown filter, timestamp sorter, pagination. | **FULLY IMPLEMENTED** (Live data via `/conversations`) |
| **06** | `/views/settings.html` | Platform Settings | Platform session controls, component health status, and user sign-out. | Component status badges, signed-in user card, theme controls, `#out` Sign Out button. | **FULLY IMPLEMENTED** (Live `/auth/me` & `/auth/logout`) |
| **07** | `/views/help-docs.html` | Help & Docs | Knowledge base and operator guide explaining gateway rules and risk scoring. | Search query input, accordion topic headers, technical reference cards. | **FULLY IMPLEMENTED** (Interactive client-side) |
| **08** | `/views/threat-detection.html` | Threat Detection | Dedicated operations screen for investigating flagged prompt injections and anomalies. | Threat severity filter pills, threat record table, incident detail modal. | **FULLY IMPLEMENTED** (Live SQLite audit feed) |
| **09** | `/views/risk-engine.html` | Risk Engine | Explanatory and tuning interface for the stateful $\lambda$-decay and $\alpha$-synergy mathematical models. | Parameter sliders ($\lambda, \alpha$), formula visualizer, entity weight table. | **PARTIALLY IMPLEMENTED** (Client-side interactive model) |
| **10** | `/views/dlp.html` | DLP Module | Control plane for data loss prevention rules across 11+ entity categories. | Entity rule toggles, detection confidence indicators, sample test evaluator. | **PARTIALLY IMPLEMENTED** (Client-side rule explorer) |
| **11** | `/views/ocr.html` | OCR Processing | Dedicated interface for uploading documents and testing Optical Character Recognition. | Drag-and-drop image upload zone, extracted text viewer, OCR confidence meter. | **FULLY IMPLEMENTED** (Connected to `/gateway/scan-file`) |
| **12** | `/views/gateway.html` | Gateway Status | Low-level health check and architectural component uptime monitor. | Service health table, ping button, memory and Redis connection status. | **FULLY IMPLEMENTED** (Live `/health` integration) |
| **13** | `/views/analyze-server-logs.html`| Analyze Server Logs | Log ingestion utility for scanning server access and audit files for leaked credentials. | Log file dropzone, ingestion progress bar, parsed credential findings table. | **FULLY IMPLEMENTED** (Processes files via backend) |
| **14** | `/views/network-report.html` | Network Report | Network telemetry interface displaying outbound AI connections and request latencies. | Outbound endpoint cards, latency charts, protocol distribution table. | **UI ONLY** (Populated via static telemetry) |
| **15** | `/views/suspicious-activity.html`| Suspicious Activity | Security operations screen tracking rapid-fire prompt anomalies and multi-turn escalation. | Anomaly severity badges, session threat timeline, forensic inspect buttons. | **FULLY IMPLEMENTED** (Aggregates high-risk SQLite turns) |
| **16** | `/views/review-employee-data.html`| Review Employee Data | Compliance screen for inspecting masked employee identifiers and corporate PII. | Search filter input, masked employee table, bulk unmask/mask toggle. | **PARTIALLY IMPLEMENTED** (Client-side toggle) |
| **17** | `/views/security-policy-summary.html`| Security Policy Summary | Executive posture summary demonstrating enterprise compliance (GDPR, HIPAA, SOC 2). | Compliance readiness meters, rule coverage breakdown, export audit summary. | **FULLY IMPLEMENTED** (Reads live SQLite policies) |
| **18** | `/views/ai-provider.html` | Approved AI Provider | Dedicated configuration and monitoring view for the approved local Ollama LLM. | Approved provider card (Ollama), model card (Gemma 3:4B), reply counters, rule cards. | **FULLY IMPLEMENTED** (Live `/conversations` metrics) |

---

## 6. AI Provider Integration & Upstream Routing (Phase 6 Walkthrough)

### 6.1 Provider Selection & Model Architecture (`backend/ai_provider.py`)
Shadow AI enforces a single-approved-provider policy:
- **Approved Engine**: Local **Ollama** daemon running on `http://127.0.0.1:11434`.
- **Approved Model**: **Gemma 3:4B** (`OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")`).
- **Isolation Guarantee**: All requests to unapproved public AI APIs (such as OpenAI or Anthropic) are dropped at the gateway level.

### 6.2 Prompt Construction & System Context
When a request is approved (`ALLOW` or `SANITIZE_AND_SEND`), `send_to_approved_ai(text)` constructs an asynchronous chat request with trusted system context:
```python
current_date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %B %Y")
messages = [
    {
        "role": "system",
        "content": (
            "You are the approved local AI assistant behind the Shadow AI Security Gateway. "
            f"The current date in India is {current_date}. "
            "Use this date when answering questions about today's date. "
            "Never invent live weather, news, or other current facts that have not been "
            "provided by an approved live data source. "
            "Follow the user's request while respecting applicable safety and security requirements."
        )
    },
    {
        "role": "user",
        "content": text
    }
]
```

### 6.3 Resilience & Fallback Handling
If the local Ollama service is stopped or overloaded, the exception is trapped gracefully:
```python
except Exception as exc:
    return {
        "provider": "OLLAMA",
        "model": OLLAMA_MODEL,
        "status": "ERROR",
        "response": (
            "The local AI service is temporarily unavailable. "
            "Your request was not forwarded."
        )
    }
```
This guarantees that an AI service failure never leaks prompt data, exposes raw stack traces, or causes an unhandled 500 error in the user interface.
