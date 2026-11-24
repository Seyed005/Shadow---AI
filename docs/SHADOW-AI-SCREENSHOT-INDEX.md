# Shadow AI — Screenshot Deliverables Index

**Project:** Shadow AI — AI Security Gateway & Reverse Proxy  
**Directory:** `screenshots/project-documentation/`  
**Standard Viewport:** 1440 × 900 Desktop  
**Design System:** Pastel Aura (Taupe × Rose Dust) Light & Dark  
**Generated Date:** November 23, 2026  

---

## 25 Master Screenshots Summary

All 25 target screen states were captured live against the running Shadow AI stack (`FastAPI`, `Redis`, `SQLite`, and `Chromium CDP` automation). No mockups or placeholder graphics were used. Sensitive tokens and live secrets have been protected.

| # | Filename | Target View / Screen State | Route / Trigger | Viewport | Status | Description |
|---|---|---|---|---|---|---|
| **01** | `01-login.png` | Login Page (Initial State) | `GET /` | 1440 × 900 | **CAPTURED LIVE** | Initial landing page showing the brand, constellation canvas, email/username input, password input, and Sign In button. |
| **02** | `02-login-validation.png` | Login Validation / Error State | `POST /auth/login` (Invalid) | 1440 × 900 | **CAPTURED LIVE** | Triggered invalid login attempt displaying inline error banner and toast warning. |
| **03** | `03-dashboard.png` | Security Dashboard | `GET /views/dashboard.html` | 1440 × 900 | **CAPTURED LIVE** | Real-time posture dashboard featuring KPI tiles, activity charts, threat metrics, and gateway status. |
| **04** | `04-new-chat.png` | Main Chat Workspace | `GET /dashboard` | 1440 × 900 | **CAPTURED LIVE** | Default empty workspace showing greeting, starter prompt pills, composer input, and sidebar controls. |
| **05** | `05-normal-prompt-response.png` | Normal Prompt & AI Response | `POST /gateway/scan` (`ALLOW`) | 1440 × 900 | **CAPTURED LIVE** | Safe prompt submitted and answered by the Shadow AI Assistant via approved upstream AI integration. |
| **06** | `06-dlp-warning.png` | DLP Detection Warning Panel | `POST /gateway/scan` (`HITL`) | 1440 × 900 | **CAPTURED LIVE** | Inline security alert card featuring circular SVG risk score gauge, risk level tag, and detected entity rows. |
| **07** | `07-allow-decision.png` | Allow Decision State | Interactive HITL Card | 1440 × 900 | **CAPTURED LIVE** | Focused "ALLOW: Send as it is" button state with glowing accent outline ready for analyst confirmation. |
| **08** | `08-sanitize-send-decision.png` | Sanitize & Send Decision State | Interactive HITL Card | 1440 × 900 | **CAPTURED LIVE** | Focused "SANITIZE & SEND: Remove sensitive data and send" action highlighting synthetic entity masking. |
| **09** | `09-block-decision.png` | Block Decision State | Interactive HITL Card / `BLOCK` | 1440 × 900 | **CAPTURED LIVE** | Quarantined and blocked request banner confirming that zero prompt data reached the AI model. |
| **10** | `10-security-insights.png` | Security Insights Panel | Right Drawer (`#securityInsightsPanel`) | 1440 × 900 | **CAPTURED LIVE** | Expanded right drawer displaying session request mix donut chart, legend, recent detections, and gateway counters. |
| **11** | `11-threat-detection.png` | Threat Detection View | `GET /views/threat-detection.html` | 1440 × 900 | **CAPTURED LIVE** | Security operations view displaying detected anomalies, high-risk requests, and threat classifications. |
| **12** | `12-risk-engine.png` | Risk Engine View | `GET /views/risk-engine.html` | 1440 × 900 | **CAPTURED LIVE** | Multi-factor risk engine parameter breakdown: $\lambda$-decay ($0.8$), $\alpha$-synergy ($1.5$), and entity weights. |
| **13** | `13-adversary-simulation.png` | Adversary Simulation (Red Team) | `GET /views/red-team.html` | 1440 × 900 | **CAPTURED LIVE** | Module for safe security benchmark replay, prompt injection validation, and evasion testing. |
| **14** | `14-gateway-intelligence.png` | Gateway Intelligence (Data Analyst) | `GET /views/data-analyst.html` | 1440 × 900 | **CAPTURED LIVE** | Benchmark metrics, V1 vs V2 engine comparison cards, detection F1 scores, and bypass analysis. |
| **15** | `15-policy-management.png` | Policy Management View | `GET /views/policy-management.html` | 1440 × 900 | **CAPTURED LIVE** | Active rule enforcement controls, risk threshold definitions, and routing behavior configurations. |
| **16** | `16-audit-logs.png` | Audit Logs View | `GET /views/audit-logs.html` | 1440 × 900 | **CAPTURED LIVE** | Immutable session log table listing user actions, timestamps, policy decisions, and findings. |
| **17** | `17-ai-provider-settings.png` | AI Provider Settings | `GET /views/ai-provider.html` | 1440 × 900 | **CAPTURED LIVE** | Approved AI integration control plane showing Ollama provider status, approved model, and reply metrics. |
| **18** | `18-ollama-configuration.png` | Ollama Configuration Details | `GET /views/ai-provider.html` | 1440 × 900 | **CAPTURED LIVE** | Focused inspection card showing Gemma 3:4B runtime configuration and local forwarding rules. |
| **19** | `19-ocr-module.png` | OCR Processing Module | `GET /views/ocr.html` | 1440 × 900 | **CAPTURED LIVE** | Optical Character Recognition pipeline for image attachments (PNG, JPG, BMP, TIFF, WebP). |
| **20** | `20-network-report.png` | Network Report View | `GET /views/network-report.html` | 1440 × 900 | **CAPTURED LIVE** | Outbound traffic monitoring, connection metrics, and external API destination breakdown. |
| **21** | `21-analyze-server-logs.png` | Analyze Server Logs View | `GET /views/analyze-server-logs.html` | 1440 × 900 | **CAPTURED LIVE** | Ingestion pipeline for system logs, parsing authentication events and server access patterns. |
| **22** | `22-suspicious-activity.png` | Suspicious Activity View | `GET /views/suspicious-activity.html` | 1440 × 900 | **CAPTURED LIVE** | Anomaly monitoring screen tracking token abuse, rapid-fire prompts, and multi-turn risk escalation. |
| **23** | `23-review-employee-data.png` | Review Employee Data View | `GET /views/review-employee-data.html` | 1440 × 900 | **CAPTURED LIVE** | Internal data protection screen showing masked employee PII, IDs, and departmental exposure. |
| **24** | `24-security-policy-summary.png` | Security Policy Summary View | `GET /views/security-policy-summary.html` | 1440 × 900 | **CAPTURED LIVE** | High-level compliance and posture summary displaying active guardrails and DLP coverage. |
| **25** | `25-settings-logout.png` | Settings & Logout View | `GET /views/settings.html` | 1440 × 900 | **CAPTURED LIVE** | System configuration view displaying session info, component health, and sign-out control. |

---

## Technical Audit Verification

- **Storage Location**: [screenshots/project-documentation/](file:///home/titan/Shadow---AI/screenshots/project-documentation)
- **Pixel Geometry**: Standardized at $1440 \times 900$ pixels.
- **Visual Styling**: Enforces Pastel Aura design system with active backdrop blur, glass cards, and theme attributes.
- **Zero Fabrication**: All screen captures reflect genuine browser DOM states interacting with FastAPI backend routes and live database instances.
