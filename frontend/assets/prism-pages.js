/* Shared navigation and page context for the standalone security tools. */
(() => {
  const tools = [
    { label: "Main Chat", file: "../dashboard", group: "Workspace", href: "/dashboard" },
    { label: "Security Dashboard", file: "dashboard.html", group: "Overview" },
    { label: "Threat Detection", file: "threat-detection.html", group: "Detection" },
    { label: "Suspicious Activity", file: "suspicious-activity.html", group: "Detection" },
    { label: "Risk Engine", file: "risk-engine.html", group: "Detection" },
    { label: "DLP", file: "dlp.html", group: "Data security" },
    { label: "OCR Processing", file: "ocr.html", group: "Data security" },
    { label: "Review Employee Data", file: "review-employee-data.html", group: "Data security" },
    { label: "Network Report", file: "network-report.html", group: "Intelligence" },
    { label: "Analyze Server Logs", file: "analyze-server-logs.html", group: "Intelligence" },
    { label: "Audit Logs", file: "audit-logs.html", group: "Governance" },
    { label: "Policy Management", file: "policy-management.html", group: "Governance" },
    { label: "Security Policy Summary", file: "security-policy-summary.html", group: "Governance" },
    { label: "Adversary Simulation", file: "red-team.html", group: "Validation" },
    { label: "Gateway Intelligence", file: "data-analyst.html", group: "Validation" },
    { label: "Approved AI Provider", file: "ai-provider.html", group: "Platform" },
    { label: "Gateway Status", file: "gateway.html", group: "Platform" },
    { label: "Settings", file: "settings.html", group: "Platform" },
    { label: "Help & Docs", file: "help-docs.html", group: "Platform" }
  ];

  const contexts = {
    "dashboard.html": ["SECURITY COMMAND", "LIVE POSTURE & ACTIVITY"],
    "ai-provider.html": ["PROVIDER CONTROL", "APPROVED MODEL"],
    "analyze-server-logs.html": ["LOG INTELLIGENCE", "SECURE INGESTION"],
    "audit-logs.html": ["AUDIT TRAIL", "STORED ACTIVITY"],
    "data-analyst.html": ["SECURITY RESEARCH", "BENCHMARKS"],
    "dlp.html": ["DATA PROTECTION", "POLICY ENFORCEMENT"],
    "gateway.html": ["CONTROL PLANE", "GATEWAY HEALTH"],
    "help-docs.html": ["KNOWLEDGE BASE", "WORKSPACE GUIDE"],
    "network-report.html": ["NETWORK INTELLIGENCE", "INDICATORS"],
    "ocr.html": ["DOCUMENT INTELLIGENCE", "OCR PROCESSING"],
    "policy-management.html": ["POLICY CONTROL", "ACTIVE RULES"],
    "red-team.html": ["ADVERSARY SIMULATION", "SAFE VALIDATION"],
    "review-employee-data.html": ["DATA REVIEW", "SENSITIVE FINDINGS"],
    "risk-engine.html": ["RISK INTELLIGENCE", "SCORING MODEL"],
    "security-policy-summary.html": ["SECURITY POSTURE", "POLICY SUMMARY"],
    "settings.html": ["PLATFORM SETTINGS", "SESSION & SERVICES"],
    "suspicious-activity.html": ["THREAT OPERATIONS", "ANOMALIES"],
    "threat-detection.html": ["THREAT OPERATIONS", "DETECTION"]
  };

  const path = window.location.pathname;
  const filename = path.slice(path.lastIndexOf("/") + 1);
  const page = document.querySelector("main.page, .page");
  const header = document.querySelector(".top") ||
    document.querySelector(".page > header") ||
    document.querySelector("body > header");
  if (!header) return;

  document.body.dataset.prismPage = filename.replace(/\.html$/, "");
  document.body.insertAdjacentHTML(
    "afterbegin",
    '<div class="prism-page-atmosphere" aria-hidden="true"></div>'
  );

  const title = page?.querySelector("h1");
  if (title) {
    const [eyebrow, detail] = contexts[filename] || ["SECURITY WORKSPACE", "SHADOW AI"];
    const context = document.createElement("div");
    context.className = "prism-page-eyebrow";
    context.setAttribute("aria-label", eyebrow + ": " + detail);
    context.innerHTML =
      '<span class="prism-eyebrow-mark" aria-hidden="true">✦</span>' +
      '<span>' + eyebrow + '</span><i aria-hidden="true"></i><small>' + detail + '</small>';
    title.parentElement.insertBefore(context, title);
  }

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "prism-tools-trigger";
  trigger.setAttribute("aria-haspopup", "true");
  trigger.setAttribute("aria-expanded", "false");
  trigger.setAttribute("aria-controls", "prismToolsMenu");
  trigger.innerHTML =
    '<span class="prism-menu-glyph" aria-hidden="true">⌘</span>' +
    '<span>TOOLS</span><span class="prism-menu-caret" aria-hidden="true">⌄</span>';

  // Insert before a direct child. A generic `button` selector can match a tab
  // nested inside the dashboard navigation and make insertBefore throw.
  const insertBefore = header.querySelector(":scope > .topright, :scope > .back") ||
    header.lastElementChild;
  if (insertBefore) header.insertBefore(trigger, insertBefore);
  else header.appendChild(trigger);

  const menu = document.createElement("nav");
  menu.className = "prism-tools-menu";
  menu.id = "prismToolsMenu";
  menu.setAttribute("aria-label", "Shadow AI tools");
  menu.hidden = true;
  const list = document.createElement("div");
  list.className = "prism-tools-grid";
  for (const tool of tools) {
    const link = document.createElement("a");
    link.href = tool.href || "/views/" + tool.file;
    link.className = "prism-tool-link";
    link.dataset.group = tool.group;
    link.textContent = tool.label;
    if (tool.file === filename) {
      link.classList.add("is-current");
      link.setAttribute("aria-current", "page");
    }
    list.appendChild(link);
  }
  menu.appendChild(list);
  document.body.appendChild(menu);

  const setOpen = (open) => {
    trigger.setAttribute("aria-expanded", String(open));
    menu.hidden = !open;
    document.body.classList.toggle("prism-tools-open", open);
  };
  trigger.addEventListener("click", () => {
    setOpen(trigger.getAttribute("aria-expanded") !== "true");
  });
  menu.addEventListener("click", (event) => {
    if (event.target.closest("a")) setOpen(false);
  });
  document.addEventListener("pointerdown", (event) => {
    if (!menu.contains(event.target) && !trigger.contains(event.target)) setOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && trigger.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      trigger.focus();
    }
  });
})();
