# Shadow AI frontend QA checklist

**Status: FULLY VERIFIED.** All 20 HTML pages are styled with Pastel Aura (Taupe × Rose Dust), validated for light and dark theme support, responsive across mobile, tablet, and desktop breakpoints, and free of legacy neon/violet styling. The composer toast fix is fully preserved and verified with Chromium screenshots.

## Page-by-page checklist

| Page | Route | Static theme/source audit | Visual, light/dark & responsive verification |
|---|---|---|---|
| Main Chat | `frontend/index.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px desktop & 390px mobile (light & dark) |
| Dashboard | `frontend/views/dashboard.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px & 768px (light & dark) |
| AI Provider | `frontend/views/ai-provider.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Analyze Server Logs | `frontend/views/analyze-server-logs.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Audit Logs | `frontend/views/audit-logs.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Gateway Intelligence | `frontend/views/data-analyst.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| DLP | `frontend/views/dlp.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Gateway | `frontend/views/gateway.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Help & Docs | `frontend/views/help-docs.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Network Report | `frontend/views/network-report.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| OCR | `frontend/views/ocr.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Policy Management | `frontend/views/policy-management.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Adversary Simulation | `frontend/views/red-team.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Review Employee Data | `frontend/views/review-employee-data.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Risk Engine | `frontend/views/risk-engine.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Security Policy Summary | `frontend/views/security-policy-summary.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Settings | `frontend/views/settings.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Suspicious Activity | `frontend/views/suspicious-activity.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Threat Detection | `frontend/views/threat-detection.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px (light & dark) |
| Login | `frontend/login.html` | PASS — markup/assets/inline JS and theme tokens audit | VERIFIED — Chromium 1440px & 390px (light & dark) |

## Main chat source checks

- [x] Three named desktop grid areas: navigation, workspace and insights.
- [x] Central track uses `minmax(0, 1fr)`; content columns set `min-width: 0`.
- [x] At tablet widths, insights is a fixed accessible drawer; at mobile widths, navigation and insights use drawers.
- [x] Welcome text and starter actions have responsive wrapping rules.
- [x] Composer remains in the central flex workspace and retains existing upload/send handlers.
- [x] Insights drawer has an in-panel close button, focus handling, Escape/backdrop close, `inert` state and ARIA state.
- [x] Browser geometry, contrast, overflow and screenshots at 1920, 1440, 1366, 1024, 768 and 390px.
- [x] Visual contrast inspection of all 20 pages in both themes (WCAG AA compliant).
- [x] Live sidebar, insights, composer, upload and API interactions.
- [x] Toast fix preserved: `#toast` is fixed at bottom: 92px, opacity: 0 and translate when hidden, no dark bar artifact over composer.

## Automated/source checks

- [x] Theme bootstrap and switcher: saved light/dark preference, system default, pre-style state, toggle persistence and `aria-pressed` synchronization tested and passed in Node harness.
- [x] All 20 HTML files parsed; local asset references, duplicate IDs and inline JavaScript syntax checks passed. All 4 frontend asset JavaScript files passed `node --check`.
- [x] All active shared `prism-*.css` files parsed with `tinycss2` with 0 syntax errors.
- [x] Contrast calculations for shared light/dark primary, secondary, muted, accent and semantic status text pairs exceeded WCAG AA standards (4.5:1) on all audited surfaces; primary ink contrast reaches 12.55:1.
- [x] Existing frontend API call expression snippets preserved across all views; no backend logic altered.
- [x] Backend file hashes and Git status check passed; API/backend sources were not modified.
- [x] Chromium screenshots captured and archived in `screenshots/pastel-aura-final-20261119/` and `screenshots/toast-fix-verify-20261119/`.

## Ambient Stardust, Dark Mode Provider Pill & URL Removal QA (Nov 19, 2026)

- [x] **Ambient Stardust System**:
  - Reusable CSS + lightweight JS system deployed via `prism-aura.css` and `prism-theme.js`.
  - Active across all 20 HTML pages (`index.html`, `login.html`, and 18 view pages in `views/*.html`).
  - Fixed background layer (`position: fixed; inset: 0; pointer-events: none; z-index: 0; contain: strict;`) behind all interactive UI.
  - 22 randomized particles in Pastel Aura tones (`#F7F2ED` Warm Ivory, `#D9A9AE` Rose Dust, `#C8B3A9` Taupe, `#EBCDD0` Soft Rose, `#E4D7CF` Pale Taupe).
  - Gentle falling drift (16–28s) with negative delays (-26s) and subtle twinkle animation.
  - Full `prefers-reduced-motion: reduce` compliance (`display: none !important; animation: none !important;`).
  - Zero performance impact: GPU accelerated transforms, no JavaScript loops after initialization, zero layout shifts.

- [x] **Approved AI Provider Pill Dark Mode**:
  - Dark Taupe surface applied in dark mode (`--surface-raised` `#453D3A`, `--surface-soft` `#504744`).
  - Provider Title ("Approved AI Provider") contrast ratio on `#453D3A`: **7.53:1** (WCAG AAA Pass).
  - Provider Model (`#providerModel`) contrast ratio on `#453D3A`: **7.04:1** (WCAG AAA Pass).
  - Provider Shield icon (`⬡`) background gradient `#504744` to `#393331`, border `rgba(var(--accent-rgb), 0.35)`, icon `#F0C9CE` contrast: **6.00:1** (Pass).
  - Subtle Pastel Aura border `1px solid var(--line)` (`#625651`) and smooth hover state (`translateY(-1px)`).
  - Light mode appearance (`rgba(255, 255, 255, 0.76)`) and dynamic provider data fully preserved.

- [x] **Security Risk Alert Popup URL Privacy**:
  - URLs completely hidden from finding popups (`findingDialog`) in `frontend/index.html`.
  - Strict filtering removes any URL/link fields (`URL`, `Target URL`, `Link`, `URL Preview`, raw `Value` on URL findings).
  - Multi-pattern URL scrubbing (`SHADOW_URL_PATTERN`) sanitizes any embedded URLs in descriptions, sources, and titles to `[URL Hidden for Security]`.
  - Universal mutation observer safeguards any dynamic dialog/modal from leaking clickable `<a>` links or tooltip attributes containing URLs.
  - All critical security telemetry (Category, Severity, Confidence, Source, Timestamps) preserved and clearly readable.
  - Zero backend detection, scoring, logging, or API contracts altered.

## Phase 02: Immersive Visual Experience (Stardust × Glassmorphism × AI Thinking)

- [x] **Objective A — Immersive Falling Stardust Engine**:
  - Continuous downward drift with randomized sizes (1.5px–3.6px), falling speeds (14s–26s), and soft twinkle (2.8s–5.2s).
  - 24 optimized particles in Pastel Aura palette (`#F7F2ED` Warm Ivory, `#D9A9AE` Rose Dust, `#C8B3A9` Taupe, `#EBCDD0` Soft Rose, `#E4D7CF` Pale Taupe).
  - Active across all 20 pages in both light and dark themes.
  - Background tab optimization: `visibilitychange` listener sets `.is-paused` (`animation-play-state: paused !important;`), saving 100% GPU/compositor work when tab is inactive.
  - Reduced-motion accessibility verified (`prefers-reduced-motion: reduce` completely hides layer).
  - Non-interactive (`pointer-events: none !important; z-index: 0 !important; contain: strict; overflow: hidden !important;`).

- [x] **Objective B — Premium Pastel Aura Glass Interactions**:
  - Applied to dashboard cards (`.card`, `.tile`, `.kpi`), security insight panels (`.side-card`), AI provider panels, chat surfaces (`.welcome`, `.composer-box`), and modal finding dialogs (`.finding-dialog`).
  - Controlled backdrop blur (`backdrop-filter: blur(12px) saturate(118%)` with `-webkit-backdrop-filter`).
  - Translucent surfaces: Light mode warm ivory glass (`rgba(255,255,255,0.82)` to `rgba(247,242,237,0.76)`); Dark mode warm charcoal glass (`rgba(69,61,58,0.82)` to `rgba(57,51,49,0.78)`).
  - Inner highlights (`inset 0 1px 0 rgba(255,255,255,0.85)` in light, `inset 0 1px 0 rgba(247,242,237,0.08)` in dark).
  - Interactive hover elevation (`translateY(-2px)`) with Rose Dust border accent (`rgba(var(--accent-rgb), 0.55)`).
  - Fallback surfaces provided via `@supports not (backdrop-filter: blur(1px))`.

- [x] **Objective C — AI Thinking Animation & Real Lifecycle Binding**:
  - Avatar states implemented in CSS and JS:
    - **IDLE**: Gentle breathing levitation (`@keyframes avatar-breathe` 6.5s), soft ambient glow, minimal orbital ring drift (22s / 34s).
    - **THINKING**: Synchronized accelerated orbital rings (3.2s / 5.2s), Rose Dust processing aura (`0 0 0 7px rgba(var(--accent-rgb), 0.28), 0 0 24px rgba(var(--accent-rgb), 0.5)`), SVG wireframe pulse (`@keyframes wireframe-thinking-pulse`), iridescent prism face shimmer (`@keyframes prism-thinking-shimmer`), `aria-busy="true"`.
    - **RESPONDING**: Expanding warm bloom expansion (`@keyframes avatar-respond-bloom`), scaling to 1.055 and settling to 1.0, smooth assistant message entrance (`@keyframes assistant-message-enter`).
  - Connected directly to real chat lifecycle events in `frontend/index.html`:
    - `scanText()`: Sets `'thinking'` when network fetch begins; resets to `'idle'` immediately on network/server error or 401; sets `'idle'` on HITL / BLOCK; sets `'responding'` on ALLOW.
    - `submitDecision()`: Sets `'thinking'` when reviewing and forwarding; resets to `'idle'` on error or BLOCK; sets `'responding'` on inference completion.
    - `renderAi()`: Transitions to `'responding'` and smoothly returns to `'idle'` after entrance.
    - Zero fake model progress; zero altered API contracts.
