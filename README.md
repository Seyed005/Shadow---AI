# Shadow AI — Adaptive Multimodal Security Gateway

**Adaptive Multimodal Shadow AI Security Gateway with Red–Purple Team Feedback for Sensitive Data Leakage Prevention**

Shadow AI is a security checkpoint that sits between users and approved external AI services (e.g. ChatGPT-style APIs). It inspects prompts and uploaded files for PII, secrets, and risky content *before* they're sent to an external AI, and inspects AI responses before they're shown back to the user — minimizing accidental sensitive-data leakage while staying out of the way for safe requests.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Team Collaboration](#team-collaboration)
- [Modules & Branch Ownership](#modules--branch-ownership)
- [Testing](#testing)
- [Research Foundation](#research-foundation)
- [Limitations](#limitations)
- [Future Scope](#future-scope)

---

## Problem Statement

Users increasingly submit prompts and files to external Generative AI systems for coding, analysis, summarization, and document processing. These inputs may unintentionally contain PII, passwords, API keys, internal information, or confidential documents. Shadow AI introduces a security checkpoint before approved external AI forwarding.

## Key Features

- ✅ Text, document (PDF/DOCX/XLSX/PPTX/TXT), and image input support
- ✅ PII and secret/credential detection (Microsoft Presidio + custom regex recognizers)
- ✅ Prompt-injection indicator detection
- ✅ Risk scoring engine
- ✅ Conditional security checkpoint: **ALLOW / SANITIZE & SEND / BLOCK**
- ✅ AI output inspection before display
- ✅ Privacy-preserving audit logging
- ✅ Red Team / Purple Team adversarial testing loop with regression tests

## System Architecture

```
User → Shadow AI Chatbot → Multimodal Processing & Normalization
     → Threat Detection & Risk Engine → Conditional Security Checkpoint
     → Approved AI Gateway → Output Inspection → Audit / Analytics → User
```

### Modules

| Module | Description |
|---|---|
| M1 | Cybersecurity Chatbot & Input Management |
| M2 | Multimodal Processing & Normalization |
| M3 | Threat Detection & Risk Engine |
| M4 | Security Policy & Human Checkpoint |
| M5 | Approved AI Gateway + Output Security + Audit |
| M6 | Red Team + Purple Team + Data Analytics |

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic
- **Frontend:** HTML, CSS, JavaScript
- **PII/Secret Detection:** Microsoft Presidio (Analyzer + Anonymizer), spaCy, Regex/custom recognizers
- **Document Processing:** PyMuPDF (PDF), python-docx (Word), openpyxl (Excel), python-pptx (PowerPoint)
- **Image/OCR:** Tesseract, pytesseract, Pillow
- **AI Integration:** Approved external LLM API
- **Storage:** SQLite / JSON (prototype audit data)
- **Testing:** pytest
- **Version Control:** Git / GitHub
- **Optional:** Docker

## Project Structure

```
shadow-ai/
├── app/
│   ├── main.py           # FastAPI entrypoint
│   ├── modules/          # M1–M6 core logic
│   ├── static/            # CSS/JS assets
│   ├── templates/         # HTML frontend
│   ├── tests/             # pytest test suite
│   └── data/               # SQLite/JSON audit logs (gitignored)
├── requirements.txt        # Dependencies
├── requirements-lock.txt   # Pinned exact versions
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+
- Git
- Tesseract OCR binary ([Windows](https://github.com/UB-Mannheim/tesseract/wiki) / `brew install tesseract` on Mac / `sudo apt install tesseract-ocr` on Linux)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/shadow-ai.git
cd shadow-ai

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the spaCy language model (required by Presidio)
python -m spacy download en_core_web_lg

# 5. Run the app
uvicorn app.main:app --reload

# 6. Open in browser
# http://127.0.0.1:8000
```

### Verify Setup

```bash
python -c "
from presidio_analyzer import AnalyzerEngine
analyzer = AnalyzerEngine()
results = analyzer.analyze(text='My name is John and my email is john@test.com', language='en')
print(results)
"
```
If entities like `PERSON` and `EMAIL_ADDRESS` print out, your setup is working.

## Team Collaboration

- **Never commit directly to `main`.** Create a feature branch per module.
- Open a **Pull Request** for review before merging.
- Pull `main` before starting new work each day:
  ```bash
  git checkout main
  git pull origin main
  ```
- Commit message convention: `"M#: short description"` (e.g. `"M3: add regex recognizer for API keys"`)
- Never commit `.env` files or real API keys — use `.env.example` as a template.

## Modules & Branch Ownership

| Branch | Module | Owner |
|---|---|---|
| `feature/input-management` | M1 | _TBD_ |
| `feature/multimodal-processing` | M2 | _TBD_ |
| `feature/threat-detection` | M3 | _TBD_ |
| `feature/checkpoint-policy` | M4 | _TBD_ |
| `feature/ai-gateway-audit` | M5 | _TBD_ |
| `feature/redteam-purpleteam` | M6 | _TBD_ |

## Testing

```bash
pytest app/tests/
```

Evaluation metrics tracked across V1/V2/V3 iterations:
- Precision, Recall, F1-score
- False positive / false negative rate
- Bypass rate
- Sanitization effectiveness
- Processing latency
- Multimodal detection accuracy

> All experimental results must come from actual runs — no invented numbers.

## Research Foundation

**Base Paper:** Z. Shen, Z. Xi, Y. He, W. Tong, J. Hua, and S. Zhong, "ProSan: Utility-Based Prompt Privacy Sanitizer," *IEEE Transactions on Information Forensics and Security*, vol. 21, pp. 1198–1212, 2026.

Shadow AI extends ProSan's prompt-privacy sanitization concept into a full end-to-end multimodal security gateway with risk scoring, human-in-the-loop checkpoints, output inspection, auditing, and Red–Purple Team feedback. See supporting references in the project's base-paper analysis document.

## Limitations

- Detection can miss obfuscated or context-dependent sensitive information
- OCR and document extraction can fail on poor-quality inputs
- False positives/negatives are possible
- The gateway only protects traffic routed through the Shadow AI application

## Future Scope

- Advanced semantic privacy analysis
- Multilingual detection
- Stronger prompt-injection defenses
- Enterprise identity and policy integration
- Threat-intelligence integration
- Automated adversarial test generation
- Scalable deployment

---

## License

Santhosh.S
Balaji.M
Seyed Ismail Bilal.S
Aravindsamy.D
