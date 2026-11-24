# Shadow AI — Comprehensive System Architecture & Data Flow

**Document:** Architecture Specification
**Project:** Shadow AI — Enterprise AI Security Gateway & Reverse Proxy
**Current Branch:** `redesign/pastel-aura`
**Author:** Senior Full-Stack Software Architect & Cybersecurity Auditor
**Date:** November 23, 2026

---

## 1. System Overview

Shadow AI operates as an inline, stateful Security Gateway and Data Loss Prevention (DLP) reverse proxy designed to govern interactions between corporate users and upstream Large Language Models (LLMs). Rather than allowing enterprise users to communicate directly with external or internal AI services, all requests—whether plain text or file uploads (PDF, DOCX, XLSX, PPTX, Images)—are routed through Shadow AI's multi-tier inspection pipeline.

The platform provides:
1. **Multi-Engine DLP Inspection**: Combines pattern-based regular expressions, Microsoft Presidio NER (Named Entity Recognition), Spacy linguistic analysis, custom recognizers, and OCR document processing.
2. **Contextual & Stateful Risk Scoring**: Evaluates not only the current prompt's isolated sensitivity, but also historical risk decaying over multiple conversation turns ($\lambda = 0.8$) and multi-entity synergy amplification ($\alpha = 1.5$).
3. **Adaptive Policy Enforcement**: Automatically permits low-risk queries (`ALLOW`), redacts and masks sensitive entities (`SANITIZE_AND_SEND`), quarantines ambiguous requests for Human-in-the-Loop review (`HITL`), or outright drops malicious injections (`BLOCK`).
4. **Dual Data Persistence**: Utilizes Redis for sub-millisecond session authentication, TTL tokens, and active turn cache, alongside an append-only SQLite store with WAL (Write-Ahead Logging) for tamper-evident conversation logs and audit trails.

---

## 2. Architecture Diagrams

### Diagram 1: Overall System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer (Frontend)"]
        UI["Web Browser (Vanilla ES6 + Pastel Aura CSS)"]
        Chat["Main Chat Workspace (/dashboard)"]
        AdminViews["18 Security Views (/views/*.html)"]
        AuthView["Login & Registration (/login.html)"]
    end

    subgraph GatewayLayer["Shadow AI Gateway (FastAPI Backend)"]
        ReverseProxy["FastAPI Application Server (main.py)"]
        AuthMiddleware["Session & Auth Dependency (auth.py)"]
        FileParser["Multimodal Document Ingestion (processing/)"]
        PipelineEngine["Detection Pipeline Coordinator (detection_pipeline.py)"]
        RiskEngine["Contextual Risk Engine (risk_engine.py)"]
        PolicyDecision["Policy Enforcement (policy.py)"]
        MaskingModule["Sanitization & Masking (masking.py)"]
    end

    subgraph DetectionEngines["Multi-Engine DLP & Threat Detection"]
        RegexEngine["Basic Detector (basic_detector.py)"]
        PresidioEngine["Presidio & Spacy NER (presidio_detector.py)"]
        CustomRec["Custom Recognizers (custom_recognizers.py)"]
        InjectionDet["Prompt Injection Detector (prompt_injection_detector.py)"]
        OCRModule["Tesseract OCR Processor (image_processor.py)"]
        Normalizer["Deduplication & Canonical Normalizer (normalizer.py)"]
    end

    subgraph PersistenceLayer["Dual Persistence Layer"]
        RedisDB[("Redis In-Memory Cache (Port 6379)
• Auth Sessions (3600s TTL)
• Multi-Turn History
• Pending HITL State")]
        SQLiteDB[("SQLite Database (WAL Mode)
• conversations
• conversation_messages
• Audit Trails")]
    end

    subgraph UpstreamAI["Upstream AI Provider"]
        OllamaService["Local Ollama Daemon (Port 11434)"]
        ModelInstance["Gemma 3:4B LLM"]
    end

    UI --> AuthView
    UI --> Chat
    UI --> AdminViews

    AuthView --> ReverseProxy
    Chat --> ReverseProxy
    AdminViews --> ReverseProxy

    ReverseProxy --> AuthMiddleware
    AuthMiddleware <--> RedisDB

    ReverseProxy --> FileParser
    ReverseProxy --> PipelineEngine

    PipelineEngine --> RegexEngine
    PipelineEngine --> PresidioEngine
    PipelineEngine --> CustomRec
    PipelineEngine --> InjectionDet
    FileParser --> OCRModule
    OCRModule --> PipelineEngine

    RegexEngine & PresidioEngine & CustomRec & InjectionDet --> Normalizer
    Normalizer --> RiskEngine

    RiskEngine <--> RedisDB
    RiskEngine --> PolicyDecision

    PolicyDecision -->|ALLOW| OllamaService
    PolicyDecision -->|SANITIZE_AND_SEND| MaskingModule
    MaskingModule --> OllamaService
    PolicyDecision -->|HITL Quarantine| RedisDB
    PolicyDecision -->|BLOCK| ReverseProxy

    OllamaService --> ModelInstance
    ModelInstance --> ReverseProxy

    ReverseProxy --> SQLiteDB
```

---

### Diagram 2: Authentication & Session Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Security Analyst
    participant Browser as Web Browser (login.html)
    participant AuthAPI as FastAPI /auth/*
    participant Redis as Redis Cache (Port 6379)
    participant Chat as Workspace (/dashboard)

    User->>Browser: Enters username/email & password
    Browser->>AuthAPI: POST /auth/login {login, password}
    AuthAPI->>Redis: HGET shadow_ai:user:<username>
    Redis-->>AuthAPI: User record + bcrypt password_hash
    AuthAPI->>AuthAPI: bcrypt.checkpw(password, password_hash)
    alt Invalid Credentials
        AuthAPI-->>Browser: 401 Unauthorized {"detail": "Invalid credentials."}
        Browser->>User: Displays inline validation alert
    else Valid Credentials
        AuthAPI->>AuthAPI: secrets.token_urlsafe(48) -> session_token
        AuthAPI->>Redis: HSET shadow_ai:auth:<token> {username, created_at}
        AuthAPI->>Redis: EXPIRE shadow_ai:auth:<token> 3600
        AuthAPI-->>Browser: 200 OK + Set-Cookie: shadow_ai_auth=<token>; HttpOnly; SameSite=Lax
        Browser->>Browser: Redirects to /dashboard
    end

    User->>Browser: Loads /dashboard
    Browser->>AuthAPI: GET /auth/me (Cookie: shadow_ai_auth=<token>)
    AuthAPI->>Redis: HGET shadow_ai:auth:<token>
    Redis-->>AuthAPI: Session data (valid)
    AuthAPI->>Redis: HGET shadow_ai:user:<username>
    Redis-->>AuthAPI: Full profile {full_name, role, email}
    AuthAPI-->>Browser: 200 OK {user: {name, role, email}}
    Browser->>Chat: Renders workspace avatar & user role
```

---

### Diagram 3: Main Chat & Prompt Gateway Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as Enterprise User
    participant UI as Chat UI (index.html)
    participant Gateway as FastAPI Gateway (/gateway/scan)
    participant DLP as DLP & Normalizer
    participant Risk as Risk Engine
    participant Policy as Policy Engine
    participant Store as SQLite Audit Store
    participant AI as Upstream LLM (Ollama)

    User->>UI: Types prompt or attaches document
    UI->>Gateway: POST /gateway/scan (text, session_id)
    Gateway->>DLP: run_detection(text)
    DLP->>DLP: Regex + Presidio + Custom Rules + Overlap Filter
    DLP-->>Gateway: canonical normalized_findings
    Gateway->>Risk: calculate_risk(normalized_findings, session_history)
    Risk-->>Gateway: isolated_risk, historical_risk, synergy_risk, total_risk
    Gateway->>Policy: get_policy_decision(risk_result)
    Policy-->>Gateway: decision: ALLOW / SANITIZE_AND_SEND / HITL / BLOCK

    alt Policy Decision == ALLOW
        Gateway->>AI: send_to_approved_ai(text)
        AI-->>Gateway: LLM Response text
        Gateway->>Store: record_gateway_result(status=ALLOWED, clean prompt)
        Gateway-->>UI: 200 OK {policy: ALLOW, ai_response: text}
        UI->>User: Renders AI Assistant response bubble
    else Policy Decision == HITL
        Gateway->>Gateway: save_pending_hitl(session_id, prompt, findings)
        Gateway-->>UI: 200 OK {policy: HITL, findings, risk_score}
        UI->>User: Displays Security Warning Card + Gauge + Action Buttons
    else Policy Decision == BLOCK
        Gateway->>Store: record_gateway_result(status=BLOCKED)
        Gateway-->>UI: 200 OK {policy: BLOCK, detail: Policy violation}
        UI->>User: Displays Request Blocked Card (No AI call made)
    end
```

---

### Diagram 4: Multi-Layered DLP Detection Engine

```mermaid
flowchart TD
    RawInput["Raw Input Stream (Prompt text or OCR Extracted Text)"] --> PipelineStart["detection_pipeline.run_detection()"]

    subgraph RegexTier["Tier 1: Basic Regex Detector"]
        P1["Email Regex (RFC 5322 compliant)"]
        P2["URL Regex (http/https/www/TLDs)"]
        P3["Internal IP Address Regex (RFC 1918)"]
        P4["Phone Number Regex (E.164 & standard formats)"]
        P5["Password Assignment Heuristics"]
    end

    subgraph PresidioTier["Tier 2: Microsoft Presidio & Spacy"]
        SpacyModel["en_core_web_sm Spacy NLP Pipeline"]
        PresidioAnalyzer["AnalyzerEngine"]
        P6["PERSON Entity Recognizer"]
        P7["LOCATION Entity Recognizer"]
        P8["DATE_TIME Recognizer"]
        P9["CREDIT_CARD Recognizer"]
    end

    subgraph CustomTier["Tier 3: Custom Pattern Recognizers"]
        C1["Employee ID Pattern (EMP-[0-9]{4,6})"]
        C2["API Key High-Entropy Recognizer"]
        C3["Database Connection String Recognizer"]
        C4["ROT13 Obfuscation Detector"]
        C5["Base64 Encoded Payload Detector"]
        C6["Prompt Injection Pattern Classifier"]
    end

    subgraph NormalizationTier["Tier 4: Cross-Engine Normalization & Filtering"]
        CanonicalMap["Canonical Type Mapping
EMAIL_ADDRESS -> EMAIL
PHONE_NUMBER -> PHONE
URL -> URL"]
        Deduplication["Position-Based Deduplication
(Overlap & Source Confidence Merge)"]
        CrossFilter["Cross-Type Overlap Filter
• Strip URL if inside EMAIL
• Strip Phone if inside IP
• Strip false file extensions (.docx/.pdf)"]
    end

    PipelineStart --> RegexTier
    PipelineStart --> PresidioTier
    PipelineStart --> CustomTier

    RegexTier --> NormalizationTier
    PresidioTier --> NormalizationTier
    CustomTier --> NormalizationTier

    NormalizationTier --> CleanFindings["Standardized Findings Set
[{type, source, confidence, start, end}]"]
```

---

### Diagram 5: Policy Decision Tree & Risk Scoring Matrix

```mermaid
flowchart TD
    Findings["Normalized Findings"] --> IsolatedCalc["1. Isolated Risk Calculation
Risk_iso = Σ (Entity_Weight × Confidence)"]

    subgraph EntityWeights["Entity Weight Catalog (ENTITY_WEIGHTS)"]
        W1["DATABASE_CREDENTIAL: 100.0"]
        W2["API_KEY_LIKE: 90.0 | CREDIT_CARD: 90.0"]
        W3["PASSWORD: 80.0"]
        W4["EMPLOYEE_ID: 30.0 | IP_ADDRESS: 30.0"]
        W5["EMAIL: 20.0 | PHONE: 20.0 | URL: 20.0 | INJECTION: 20.0"]
        W6["PERSON: 10.0 | DATE_TIME: 0.0"]
    end

    IsolatedCalc --> HistoryFetch["2. History Fetch from Redis (Past Turns)"]
    HistoryFetch --> HistoricalCalc["3. Historical Decay Calculation
Risk_hist = Σ (λ^(N-i) × Turn_Risk) | λ = 0.8"]

    HistoricalCalc --> SynergyCalc["4. Synergy Risk Calculation
Risk_syn = α × 10.0 | α = 1.5
(Triggers when sensitive pairs co-occur:
e.g. EMAIL + PASSWORD or IP + API_KEY)"]

    SynergyCalc --> TotalRisk["5. Total Contextual Risk Score
Risk_total = Risk_iso + Risk_hist + Risk_syn"]

    TotalRisk --> ThresholdCheck{"Evaluate Thresholds"}

    ThresholdCheck -->|Risk_total <= 10.0 (TAU_LOW)| ActionAllow["ALLOW (Forward)
• Low risk request
• Forward clean prompt to AI"]
    ThresholdCheck -->|10.0 < Risk_total <= 25.0 (TAU_HITL)| ActionHITL["HITL (Quarantine)
• Medium/High sensitivity
• Prompt analyst for human decision"]
    ThresholdCheck -->|Risk_total > 25.0| ActionBlockOrReview["BLOCK / CRITICAL HITL
• High risk sensitive data
• Password/Credentials detected
• Drop request or require supervisor review"]
```

---

### Diagram 6: AI Provider Upstream Forwarding & Fallback

```mermaid
flowchart TD
    GatewayReq["Approved Request from Gateway (ProcessText / HITL Decision)"] --> ProviderCheck["send_to_approved_ai(text)"]

    subgraph PromptEnrichment["Context Enrichment"]
        SystemPrompt["System Prompt Injected:
• You are the approved local AI assistant behind Shadow AI.
• The current date in India is injected via ZoneInfo('Asia/Kolkata').
• Strict compliance with enterprise safety and security."]
    end

    subgraph OllamaIntegration["Local Ollama Client"]
        ClientInit["ollama.AsyncClient()"]
        ModelParam["Model: os.getenv('OLLAMA_MODEL', 'gemma3:4b')"]
        ChatCall["await client.chat(model, messages)"]
    end

    subgraph FallbackHandler["Error & Resilience Handling"]
        TimeoutCatch["Exception Caught (ConnectionRefused, Timeout, HTTPError)"]
        SafeMessage["Return Graceful Error Payload:
{
  'provider': 'OLLAMA',
  'model': 'gemma3:4b',
  'status': 'ERROR',
  'response': 'The local AI service is temporarily unavailable...'
}"]
    end

    ProviderCheck --> PromptEnrichment
    PromptEnrichment --> OllamaIntegration
    OllamaIntegration -->|HTTP 200 OK| UpstreamSuccess["Return SUCCESS Payload
{
  'provider': 'OLLAMA',
  'model': 'gemma3:4b',
  'status': 'SUCCESS',
  'response': '...'
}"]
    OllamaIntegration -->|Service Offline / Port 11434 Unreachable| FallbackHandler
    FallbackHandler --> FallbackReturn["Return Safe Status to Gateway (Zero Leakage)"]
```

---

### Diagram 7: Dual-Database Workflow & Schema Relationships

```mermaid
erDiagram
    REDIS_AUTH_SESSION {
        string session_token PK "shadow_ai:auth:<token>"
        string username "User account handle"
        string created_at "ISO-8601 Timestamp"
        int ttl "Auto-expires in 3600 seconds"
    }

    REDIS_USER_ACCOUNT {
        string username PK "shadow_ai:user:<username>"
        string email "Unique user email"
        string full_name "Analyst full name"
        string password_hash "Bcrypt salted hash"
        string role "Analyst / Admin"
        string created_at "Account creation timestamp"
    }

    REDIS_CONVERSATION_CACHE {
        string session_id PK "shadow_ai:session:<session_id>"
        string raw_history_json "Last 20 conversation turns"
        int ttl "Session TTL (3600s)"
    }

    REDIS_HITL_QUARANTINE {
        string session_id PK "shadow_ai:hitl:<session_id>"
        string raw_prompt "Quarantined prompt content"
        string raw_findings "Unresolved DLP entity findings"
        int ttl "Quarantine expiration"
    }

    SQLITE_CONVERSATIONS {
        string username PK "User identity"
        string session_id PK "Unique session ID"
        string title "Auto-generated conversation title"
        int created_at "Unix epoch timestamp"
        int updated_at "Unix epoch timestamp"
    }

    SQLITE_CONVERSATION_MESSAGES {
        int id PK "Autoincrement primary key"
        string username FK "References conversations.username"
        string session_id FK "References conversations.session_id"
        string role "user / assistant / system"
        string content "Sanitized prompt or AI response"
        string input_type "TEXT / PDF / DOCX / XLSX / IMAGE"
        string file_name "Attached file name or null"
        string decision "ALLOW / SANITIZE_AND_SEND / HITL / BLOCK"
        string risk_level "LOW / MEDIUM / HIGH / CRITICAL"
        real risk_score "Total numeric risk score"
        int redacted "1 if entities masked, 0 otherwise"
        string metadata_json "DLP finding types and positions"
        int created_at "Unix epoch timestamp"
    }

    REDIS_AUTH_SESSION ||--|| REDIS_USER_ACCOUNT : "resolves to"
    SQLITE_CONVERSATIONS ||--o{ SQLITE_CONVERSATION_MESSAGES : "cascades on delete"
```

---

### Diagram 8: Application Sitemap & Routing Topology

```mermaid
flowchart TD
    Root["Public Entry Point: GET / (login.html)"] --> AuthRoutes

    subgraph AuthRoutes["Authentication & Session Routes"]
        LoginPost["POST /auth/login"]
        SignupPost["POST /auth/signup"]
        LogoutPost["POST /auth/logout"]
        MeGet["GET /auth/me"]
        ForgotPost["POST /auth/forgot-password"]
        ResetPost["POST /auth/reset-password"]
    end

    Root -->|Authenticated Session| MainWorkspace["Main Chat Workspace: GET /dashboard (index.html)"]

    subgraph ChatGatewayRoutes["Security Gateway API"]
        ScanText["POST /gateway/scan"]
        ScanFile["POST /gateway/scan-file"]
        HitlDecision["POST /gateway/hitl"]
        GetConversations["GET /conversations"]
        GetSingleConv["GET /conversations/{session_id}"]
    end

    MainWorkspace --> ChatGatewayRoutes
    MainWorkspace --> ToolsMenu["Tools Navigation Menu (18 Views)"]

    subgraph ViewsTopology["Standalone Views (GET /views/{view_name})"]
        V1["dashboard.html (Security Dashboard)"]
        V2["threat-detection.html (Threat Detection)"]
        V3["suspicious-activity.html (Suspicious Activity)"]
        V4["risk-engine.html (Risk Engine)"]
        V5["dlp.html (DLP Module)"]
        V6["ocr.html (OCR Processing)"]
        V7["review-employee-data.html (Review Employee Data)"]
        V8["network-report.html (Network Report)"]
        V9["analyze-server-logs.html (Analyze Server Logs)"]
        V10["audit-logs.html (Audit Logs)"]
        V11["policy-management.html (Policy Management)"]
        V12["security-policy-summary.html (Security Policy Summary)"]
        V13["red-team.html (Adversary Simulation)"]
        V14["data-analyst.html (Gateway Intelligence)"]
        V15["ai-provider.html (Approved AI Provider)"]
        V16["gateway.html (Gateway Status)"]
        V17["settings.html (Platform Settings)"]
        V18["help-docs.html (Help & Documentation)"]
    end

    ToolsMenu --> ViewsTopology
```
