# Shadow AI — Comprehensive Viva & Technical Interview Preparation Guide

**Project:** Shadow AI — AI Security Gateway & Reverse Proxy
**Target Audience:** B.Tech Computer Science & Engineering (Cybersecurity) Students & Viva Examiners
**Author:** Senior Cybersecurity Architect & Academic Viva Specialist
**Date:** November 23, 2026

---

## 1. Project Explanations

### 1.1 The 60-Second Elevator Pitch (Simple Explanation)
> *"Shadow AI is an enterprise cybersecurity firewall and reverse proxy that protects organizations when their employees use Artificial Intelligence. Normally, when an employee pastes source code, customer records, or credentials into an AI chat tool, that sensitive data leaves the company and can cause massive data breaches or regulatory violations. Shadow AI intercepts every prompt before it ever reaches the AI model. It scans the text and attached documents for sensitive entities like passwords, credit cards, emails, and prompt injections. If the prompt is safe, it lets it pass; if it contains sensitive data, it either redacts the secrets with synthetic tokens or stops the prompt entirely and asks a security analyst to approve it. In short, it is an intelligent, automated security gatekeeper for GenAI."*

### 1.2 Deep Technical Explanation (For Technical Evaluators)
> *"Architecturally, Shadow AI is an inline, asynchronous reverse proxy built with FastAPI. It enforces multi-tiered Data Loss Prevention (DLP) across multimodal inputs (plain text, PDFs, Word documents, Excel sheets, PowerPoint decks, and OCR-extracted image text). The detection pipeline combines deterministic regular expressions, Microsoft Presidio Named Entity Recognition powered by Spacy NLP, and custom heuristic classifiers.
>
> Unlike conventional stateless DLP tools that only inspect a single query in isolation, Shadow AI implements a stateful, mathematical Contextual Risk Engine. It calculates total risk by synthesizing three variables: isolated prompt risk, historical risk decayed exponentially over prior conversation turns using a decay factor $\lambda = 0.8$, and a synergy multiplier $\alpha = 1.5$ that penalizes dangerous co-occurring entity pairs (such as a password appearing alongside an email address across multiple turns).
>
> The system enforces strict policy thresholds: prompts scoring $\le 10.0$ are allowed; scores between $10.0$ and $25.0$ are quarantined for Human-in-the-Loop (HITL) analyst review or synthetic token masking; scores exceeding $25.0$ are blocked. The persistence layer separates volatile, low-latency session tokens and conversation state in Redis from immutable, append-only audit trails stored in an ACID-compliant SQLite database with Write-Ahead Logging (WAL)."*

---

## 2. Module-by-Module Technical Breakdown

1. **Main Chat Workspace (`/dashboard`)**: The primary conversational interface providing prompt submission, document attachment, HITL quarantine alerts, and interactive risk gauge visualization.
2. **Security Dashboard (`/views/dashboard.html`)**: Executive security posture monitoring displaying real-time decision distributions (Allowed vs. Sanitized vs. Blocked), active threat indicators, and session throughput.
3. **Gateway Intelligence (`/views/data-analyst.html`)**: Evaluates engine performance metrics, comparing V1 baseline precision/recall against the V2 adaptive engine and monitoring evasion rates.
4. **Adversary Simulation (`/views/red-team.html`)**: Automated security testing module that replays stored prompt-injection attacks, jailbreaks, and obfuscation vectors (ROT13, Base64) to validate DLP robustness.
5. **Threat Detection (`/views/threat-detection.html`)**: Security Operations Center (SOC) screen listing flagged prompt injections, anomalous patterns, and high-risk queries.
6. **Risk Engine (`/views/risk-engine.html`)**: Interactive model explorer displaying mathematical parameters ($\lambda$-decay, $\alpha$-synergy) and entity weight distributions.
7. **DLP Module (`/views/dlp.html`)**: Policy configuration interface defining active rules for 11+ entity types including Credentials, PII, and Financial records.
8. **OCR Processing (`/views/ocr.html`)**: Optical Character Recognition testing bench running Tesseract OCR to extract and inspect text hidden inside uploaded screenshots or scanned documents.
9. **Analyze Server Logs (`/views/analyze-server-logs.html`)**: Security utility for ingesting server access logs and flagging leaked credentials or authorization tokens.
10. **Network Report (`/views/network-report.html`)**: Outbound network telemetry monitoring latency, protocol distributions, and upstream endpoint destinations.
11. **Suspicious Activity (`/views/suspicious-activity.html`)**: Forensic monitor tracking rapid-fire prompt submissions and multi-turn risk escalation attempts.
12. **Review Employee Data (`/views/review-employee-data.html`)**: Privacy compliance tool displaying masked corporate identifiers (`[EMP_NAME]`) to prevent unauthorized internal profiling.
13. **Policy Management (`/views/policy-management.html`)**: Rule enforcement plane allowing administrators to configure threshold parameters and review requirements.
14. **Security Policy Summary (`/views/security-policy-summary.html`)**: High-level compliance readiness summary mapping active protections to GDPR, HIPAA, and SOC 2 frameworks.
15. **Audit Logs (`/views/audit-logs.html`)**: Forensic audit trail providing searchable, tamper-evident records of all user queries, decisions, and sanitized metadata.
16. **Approved AI Provider (`/views/ai-provider.html`)**: LLM integration view verifying that only approved local models (Ollama Gemma 3:4B) receive traffic.
17. **Gateway Status (`/views/gateway.html`)**: Low-level infrastructure health monitor verifying Redis, SQLite, and detection pipeline uptime.
18. **Platform Settings (`/views/settings.html`)**: Session control screen displaying active user identity, role, theme preferences, and secure logout.

---

## 3. End-to-End Execution Trace

### Scenario: An employee accidentally pastes database credentials into a chat prompt
1. **User Action**: The employee types:
   `"Please debug why my connection fails for user admin@company.com with password SecretPass#2026 at https://db.internal.net"`
2. **Network Interception**: The browser dispatches an HTTP POST request to `/gateway/scan` carrying the prompt and active `session_id`.
3. **Authentication Check**: FastAPI's `get_current_user` dependency reads the `shadow_ai_auth` cookie and validates the active session in Redis.
4. **DLP Inspection**:
   - `detection/basic_detector.py` identifies the email `admin@company.com`, the URL `https://db.internal.net`, and the password `SecretPass#2026`.
   - `detection/presidio_detector.py` analyzes the text and detects `EMAIL_ADDRESS` and `URL`.
   - `detection/normalizer.py` deduplicates findings: it normalizes entities to canonical forms (`EMAIL`, `URL`, `PASSWORD`), confirms character spans, and discards redundant overlap.
5. **Risk Engine Calculation**:
   - $\text{Isolated Risk} = \text{Weight}(\text{PASSWORD}) \times 1.0 + \text{Weight}(\text{EMAIL}) \times 1.0 + \text{Weight}(\text{URL}) \times 1.0 = 80.0 + 20.0 + 20.0 = 120.0$.
   - $\text{Synergy Risk}$: Because `EMAIL` and `PASSWORD` appear together, synergy penalty triggers: $\alpha \times 10.0 = 1.5 \times 10.0 = 15.0$.
   - $\text{Total Risk} = 120.0 + 15.0 = 135.0$.
6. **Policy Decision**: Since $\text{Total Risk} (135.0) > 25.0$, the policy engine issues a `QUARANTINE_HITL` (Critical) directive.
7. **Quarantine Storage**: The raw prompt is held in Redis under `shadow_ai:hitl:<session_id>`. **Zero data is transmitted to the AI model.**
8. **UI Warning**: The browser renders the red `renderHitl()` card showing a risk gauge at 135, warning badges for Email, Password, and URL, and three action buttons: *ALLOW*, *SANITIZE & SEND*, and *BLOCK*.
9. **Analyst Intervention**: The user clicks **SANITIZE & SEND**.
10. **Masking & Forwarding**:
    - The backend retrieves the quarantined text and calls `mask_sensitive_data()`.
    - It transforms the text to: `"Please debug why my connection fails for user analyst@example.com with password [SYNTHETIC_PASSWORD] at https://example.com"`.
    - The safe, sanitized prompt is forwarded to the local Ollama Gemma 3:4B model.
    - The model's answer is returned to the user, and an immutable audit log is written to SQLite.

---

## 4. 50 Comprehensive Viva Questions & Answers

### Part 1: Core Concepts & Project Overview

#### Q1: What problem does Shadow AI solve?
**A:** It addresses "Shadow AI"—the unauthorized or ungoverned use of Generative AI tools in enterprises. It prevents sensitive corporate data (PII, credentials, intellectual property) from being leaked to external or internal language models by providing an inline security proxy.

#### Q2: Why is client-side DLP insufficient for AI security?
**A:** Client-side checks can be bypassed by intercepting HTTP requests, modifying browser memory, or using alternative clients (e.g. `curl` or scripts). Server-side inspection guarantees that every request must pass security validation before hitting the AI model.

#### Q3: What is the difference between a forward proxy and a reverse proxy?
**A:** A forward proxy sits in front of users and regulates access to the public Internet. A reverse proxy sits in front of backend servers (in our case, the LLM API) and intercepts incoming requests to enforce security, load balancing, and authentication.

#### Q4: Why is Shadow AI designed specifically for GenAI rather than generic web traffic?
**A:** GenAI traffic consists of unstructured natural language prompts and multi-turn conversational context. Generic firewalls only inspect headers and URLs; Shadow AI inspects semantic text, recognizes entity co-occurrences, understands prompt-injection attacks, and tracks risk across conversation turns.

#### Q5: What are the three primary security policy decisions in Shadow AI?
**A:**
1. `ALLOW`: Permits benign prompts to reach the AI model without modification.
2. `SANITIZE_AND_SEND`: Replaces sensitive entities with synthetic tokens before forwarding.
3. `BLOCK` / `HITL`: Quarantines high-risk prompts and prevents AI forwarding until a human analyst reviews the request.

#### Q6: How does the system handle multi-turn conversational memory?
**A:** It stores the last 20 conversation turns in Redis with a 1-hour TTL. When calculating risk for a new turn, the risk engine retrieves the session history to detect multi-turn risk escalation.

#### Q7: What is Human-in-the-Loop (HITL)?
**A:** HITL is a security workflow where ambiguous or high-risk requests are paused so a human analyst can inspect the findings and explicitly decide whether to allow, sanitize, or block the request.

#### Q8: What design system does the user interface utilize?
**A:** The Pastel Aura design system (featuring Taupe and Rose Dust tones, glassmorphism cards, stardust background particles, and accessible light/dark theme toggles).

#### Q9: What happens if an employee tries to access protected views without logging in?
**A:** The `get_current_user` FastAPI dependency intercepts the request, detects the absence of a valid `shadow_ai_auth` cookie, and returns an HTTP 401 Unauthorized status, triggering a client redirect to the login page (`/`).

#### Q10: How does Shadow AI maintain audit compliance?
**A:** It records every prompt, decision, risk score, and detected entity in an append-only SQLite database using Write-Ahead Logging (WAL), creating an immutable audit trail for GDPR, HIPAA, and SOC 2 audits.

---

### Part 2: Architecture & Networking

#### Q11: Explain the high-level architecture of Shadow AI.
**A:** Shadow AI follows a modular, three-tier architecture:
1. **Presentation Layer**: Vanilla HTML5, ES6 JavaScript, and responsive CSS (Pastel Aura).
2. **Application & Security Layer**: FastAPI backend hosting the reverse proxy, DLP pipeline, risk engine, and policy enforcement modules.
3. **Persistence & Inference Layer**: Redis for volatile caching/sessions, SQLite for permanent audit logs, and a local Ollama instance hosting the Gemma 3:4B model.

#### Q12: Why was FastAPI chosen instead of Flask or Django?
**A:** FastAPI is natively asynchronous (`async`/`await`), built on Starlette and Pydantic. It provides high throughput for I/O-bound operations (such as waiting for LLM completions or streaming file uploads), auto-generates OpenAPI documentation, and provides robust type validation.

#### Q13: What port numbers are used across the system?
**A:**
- Port `8000`: FastAPI Backend and Web UI.
- Port `6379`: Redis in-memory cache and session store.
- Port `11434`: Local Ollama AI daemon.

#### Q14: How does the backend communicate with the frontend?
**A:** Via RESTful HTTP APIs using JSON payloads for data and standard HTML/FileResponses for views. Authentication is maintained via HTTP-only session cookies.

#### Q15: Why is Redis used in addition to SQLite?
**A:** Redis provides sub-millisecond in-memory read/write performance and automatic key expiration (TTL), making it ideal for transient session tokens, active conversation history, and pending HITL queues. SQLite provides durable, ACID-compliant, structured storage for historical analytics and forensic audits.

#### Q16: How does the reverse proxy prevent SSRF (Server-Side Request Forgery)?
**A:** The backend rejects user-supplied upstream URLs. The upstream AI endpoint is strictly hardcoded to the local loopback Ollama daemon (`http://127.0.0.1:11434`), preventing users from redirecting requests to internal network services.

#### Q17: What is the purpose of the `/health` endpoint?
**A:** It provides a lightweight, unauthenticated health check that monitoring tools or container orchestrators can ping to verify that the application process is alive and responding.

#### Q18: What is Write-Ahead Logging (WAL) in SQLite and why is it used?
**A:** In standard SQLite, writes lock the entire database file. WAL mode writes changes to a separate `-wal` file first. This allows concurrent readers to continue reading without blocking writers, significantly improving concurrency under heavy audit logging.

#### Q19: How are multimodal file attachments ingested?
**A:** Uploaded via `multipart/form-data` to `POST /gateway/scan-file`. The server saves the file to a secure temporary path, routes it to the matching extractor (`pdf_processor`, `docx_processor`, etc.), scans the extracted text, and securely unlinks the temporary file in a `finally` block.

#### Q20: How are CORS (Cross-Origin Resource Sharing) restrictions handled?
**A:** By serving the frontend views directly from the same FastAPI domain and port (same-origin), eliminating CORS vulnerabilities and CSRF attack surfaces.

---

### Part 3: DLP, Regex, & Presidio Detection

#### Q21: What are the three primary detection engines in the DLP pipeline?
**A:**
1. **Basic Regex Detector**: High-speed pattern matching for structured entities (emails, IPs, phones, URLs).
2. **Microsoft Presidio with Spacy NER**: Context-aware NLP detection for unstructured entities (person names, locations, dates).
3. **Custom Recognizers**: Specialized heuristics for corporate IDs, API keys, database connection strings, obfuscated text, and prompt injections.

#### Q22: How does the system detect URLs without triggering false positives on email addresses?
**A:** The regex detector uses lookaround assertions and explicitly checks if a matched domain falls within the character span of an already detected email address. Furthermore, the normalizer executes a cross-type filter that strips any URL finding that overlaps with an email finding.

#### Q23: Why did Presidio previously flag `report.docx` as a URL, and how was it fixed?
**A:** Presidio's `UrlRecognizer` recognized `.do` as the valid top-level domain for the Dominican Republic, matching `report.do` inside `report.docx`. This was resolved by adding boundary filters that discard URL findings followed immediately by alphanumeric characters or matching common document extensions (`.docx`, `.pdf`, `.xlsx`, etc.).

#### Q24: What is Named Entity Recognition (NER)?
**A:** NER is a Natural Language Processing (NLP) subtask that identifies and classifies named entities in unstructured text into predefined categories (such as Person, Organization, Location, or Date).

#### Q25: How does the system detect obfuscated text?
**A:** It includes a `ROT13_DETECTOR` that applies Caesar cipher rotation and tests for english dictionary matches, and a `BASE64_DETECTOR` that attempts Base64 decoding and inspects the decoded string for sensitive patterns.

#### Q26: What is a prompt-injection attack?
**A:** An adversarial technique where an attacker embeds instructions in their input to override the system prompt, bypass safety guardrails, or force the LLM to reveal confidential instructions or training data.

#### Q27: How does Shadow AI detect prompt-injection attacks?
**A:** Via regex and semantic keyword classifiers in `prompt_injection_detector.py` that match known attack signatures (e.g. "ignore previous instructions", "system prompt reveal", "jailbreak mode", "DAN mode").

#### Q28: How does the OCR pipeline work?
**A:** The image is preprocessed (converting to grayscale, applying thresholding to improve contrast), and passed to Google Tesseract OCR via `pytesseract`. The extracted text is then fed directly into the standard DLP detection pipeline.

#### Q29: What happens when two detectors flag the same entity with different confidence scores?
**A:** The deduplication logic in `normalizer.py` identifies that the findings share overlapping start/end character spans. It merges them into a single canonical finding, retains the highest confidence score, and combines their source names (e.g. `BASIC+PRESIDIO`).

#### Q30: What is synthetic token masking?
**A:** Replacing sensitive substrings with synthetic, non-sensitive placeholders of identical semantic category (e.g. replacing `john.doe@company.com` with `analyst@example.com` and `Pass#123` with `[SYNTHETIC_PASSWORD]`).

---

### Part 4: Risk Engine, Decay, & Policy Decisions

#### Q31: State the total risk formula used by Shadow AI.
**A:**
$$\text{Risk}_{\text{total}} = \text{Risk}_{\text{isolated}} + \text{Risk}_{\text{historical}} + \text{Risk}_{\text{synergy}}$$

#### Q32: What is Isolated Risk?
**A:** The weighted sensitivity score derived purely from the entities detected in the current prompt:
$$\text{Risk}_{\text{isolated}} = \sum (\text{Weight} \times \text{Confidence})$$

#### Q33: Why do different entities have different weights?
**A:** Because different data types carry vastly different breach consequences. Leaking a database password ($100.0$) or API key ($90.0$) allows total infrastructure compromise, whereas leaking a person's name ($10.0$) or date ($0.0$) carries minimal immediate exploitability.

#### Q34: What is Historical Risk and why is exponential decay used?
**A:** An adversary might attempt "salami slicing"—distributing sensitive data across multiple conversation turns. Historical risk sums past turn scores using $\lambda^{(N - i)}$ ($\lambda = 0.8$). Recent turns contribute heavily, while older turns gradually fade in relevance.

#### Q35: What is Synergy Risk?
**A:** Extra risk added when combinations of entities appear together that create an identity-theft or exploitation chain (e.g. an email alone is low risk, but an email combined with a password provides full account access). Synergy adds $\alpha \times 10.0$ ($\alpha = 1.5$, i.e. $+15.0$ risk points).

#### Q36: What are $\tau_{low}$ and $\tau_{hitl}$?
**A:** The two policy decision threshold boundaries:
- $\tau_{low} = 10.0$: Maximum risk allowed for automatic forwarding (`ALLOW`).
- $\tau_{hitl} = 25.0$: Maximum risk eligible for human review (`QUARANTINE_HITL`). Anything above this is high-risk / critical.

#### Q37: If a prompt contains only an email address, what is the policy decision?
**A:** Weight of `EMAIL` is $20.0$. Since $20.0 > \tau_{low} (10.0)$ and $\le \tau_{hitl} (25.0)$, the decision is `QUARANTINE_HITL` (Medium risk).

#### Q38: If a prompt contains an email address and a password, what is the policy decision?
**A:** Isolated risk is $20.0 (\text{EMAIL}) + 80.0 (\text{PASSWORD}) = 100.0$. Synergy adds $+15.0$, totaling $115.0$. Since $115.0 > 25.0$, the decision is `QUARANTINE_HITL` (Critical) / `BLOCK`.

#### Q39: Can a user override a `BLOCK` decision?
**A:** Standard users cannot override a block. Only an authorized security analyst via the HITL review interface can review quarantined requests and choose to sanitize or allow them.

#### Q40: What happens to the prompt when a user selects "BLOCK" in the HITL interface?
**A:** The quarantined request is deleted from Redis, an audit record with `decision = BLOCK` is committed to SQLite, and no data is ever sent to the AI model.

---

### Part 5: Database, Auth, Security, & Edge Cases

#### Q41: How are passwords stored in Redis?
**A:** Passwords are never stored in plaintext. They are salted and hashed using the `bcrypt` algorithm before insertion into Redis hashes (`shadow_ai:user:<username>`).

#### Q42: What is the purpose of the `HttpOnly` flag on the session cookie?
**A:** It prevents client-side JavaScript (`document.cookie`) from reading the cookie, protecting the session token from theft via Cross-Site Scripting (XSS) attacks.

#### Q43: What is the purpose of the `SameSite=Lax` cookie attribute?
**A:** It prevents the browser from sending the cookie on cross-site subrequests (such as malicious images or iframes), mitigating Cross-Site Request Forgery (CSRF) attacks.

#### Q44: What happens if the Redis service crashes?
**A:** Active sessions and volatile multi-turn history become temporarily unreachable. However, the persistent conversation history and audit logs remain safe in the SQLite database file (`shadow_ai_conversations.db`).

#### Q45: How does the system handle rapid-fire prompt submissions (DoS attacks)?
**A:** The client-side Send button disables itself immediately upon submission until the gateway response arrives. The server maintains per-session history queues, preventing race conditions during risk calculations.

#### Q46: How are SQL injection vulnerabilities prevented?
**A:** The SQLite repository (`conversation_store.py`) strictly uses parameterized queries (`?` placeholders) for all SQL executions, ensuring user inputs are treated as literal values rather than executable SQL code.

#### Q47: How does Shadow AI handle AI hallucinations about current dates?
**A:** In `backend/ai_provider.py`, the gateway dynamically injects the verified current date in India (`ZoneInfo("Asia/Kolkata")`) directly into the LLM system prompt before each completion call.

#### Q48: What happens if the local Ollama AI daemon is offline?
**A:** The backend catches the connection error, prevents any retry loops from stalling the server, and returns a graceful error message stating that the local AI service is temporarily unavailable without exposing backend infrastructure details.

#### Q49: How does the system protect employee privacy in internal review screens?
**A:** The `Review Employee Data` module automatically replaces corporate employee names and identifiers with synthetic tokens (`[EMP_NAME]`, `[EMP_ID]`), preventing unauthorized internal snooping.

#### Q50: What are the key academic and practical contributions of this project?
**A:**
1. Real-time inline governance of GenAI interactions without requiring modifications to upstream LLM model weights.
2. The introduction of a stateful, multi-turn risk scoring model using mathematical exponential decay and co-occurrence synergy.
3. Multimodal document and OCR DLP coverage with automated synthetic token sanitization.

---

## 5. Technology Stack Summary

| Technology | Role / Purpose in Shadow AI |
|---|---|
| **Python 3.14** | Core programming language for backend services and detection logic. |
| **FastAPI** | High-performance asynchronous web framework hosting the reverse proxy. |
| **Uvicorn** | ASGI web server running the FastAPI application. |
| **Microsoft Presidio** | Enterprise NER library for PII entity recognition. |
| **Spacy (`en_core_web_sm`)** | Natural Language Processing model providing tokenization and linguistic entity recognition. |
| **Tesseract OCR (`pytesseract`)**| Optical Character Recognition engine for parsing image attachments. |
| **Redis** | In-memory key-value database for session tokens, TTLs, and turn cache. |
| **SQLite (WAL mode)** | Persistent, ACID-compliant database for conversations and immutable audit logs. |
| **Ollama** | Local LLM runtime executing open-weight models without cloud dependencies. |
| **Gemma 3:4B** | Approved Google open-weight language model for secure local inference. |
| **Bcrypt** | Industry-standard password hashing algorithm with automatic salting. |
| **Vanilla ES6 & CSS3** | Zero-dependency frontend architecture guaranteeing instant load times and lightweight rendering. |

---

## 6. Project Limitations & Future Enhancements

### Limitations
1. **Local Model Hardware Dependency**: Running Ollama Gemma 3:4B locally requires sufficient RAM/VRAM; high-concurrency environments may encounter inference latency.
2. **Context Window Boundary**: Historical risk tracking is currently capped at the last 20 conversation turns to preserve memory.
3. **Single Supervised Reviewer**: HITL reviews are handled on a per-session basis rather than being queued to a centralized multi-analyst ticketing system.

### Future Enhancements
1. **Streaming Token DLP**: Implementing real-time token-by-token DLP inspection on streaming LLM responses.
2. **Differential Privacy Noise**: Injecting mathematical differential privacy noise into numerical queries to prevent membership inference attacks.
3. **Enterprise SSO Integration**: Adding SAML 2.0 and OAuth2 / OpenID Connect support for corporate identity providers (Okta, Azure AD).
4. **Vector Database RAG Integration**: Providing a secure, DLP-scanned Retrieval-Augmented Generation pipeline for internal corporate knowledge bases.
