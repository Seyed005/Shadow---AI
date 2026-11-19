/* One saved theme state shared by the chat, tool pages, and sign-in screen. */
(() => {
  const KEY = "shadow-ai-theme";
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");
  const stored = () => {
    try { return localStorage.getItem(KEY); } catch (_) { return null; }
  };
  const setTheme = (theme, persist = false) => {
    const active = theme === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = active;
    document.documentElement.style.colorScheme = active;
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const isDark = active === "dark";
      button.textContent = isDark ? "☀" : "☾";
      button.setAttribute("aria-pressed", String(isDark));
      button.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} theme`);
      button.title = `Switch to ${isDark ? "light" : "dark"} theme`;
    });
    if (persist) {
      try { localStorage.setItem(KEY, active); } catch (_) { /* private storage may be unavailable */ }
    }
  };

  const initial = stored();
  setTheme(initial === "dark" || initial === "light" ? initial : (media?.matches ? "dark" : "light"));
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-toggle]");
    if (!button) return;
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
  });
  window.addEventListener("storage", (event) => {
    if (event.key === KEY) {
      const next = event.newValue;
      setTheme(next === "dark" || next === "light" ? next : (media?.matches ? "dark" : "light"));
    }
  });
  media?.addEventListener?.("change", (event) => {
    if (!stored()) setTheme(event.matches ? "dark" : "light");
  });

  // Standalone pages share the same control; the main chat keeps its existing button.
  if (!document.querySelector("[data-theme-toggle]")) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "prism-theme-toggle";
    button.dataset.themeToggle = "";
    button.textContent = "☾";
    button.setAttribute("aria-pressed", "false");
    button.setAttribute("aria-label", "Switch to dark theme");
    button.title = "Switch to dark theme";
    if (document.body.dataset.prismPage) {
      const header = document.querySelector(".top, body > header, .page > header");
      if (header) header.append(button);
    } else {
      button.classList.add("prism-login-theme-toggle");
      document.body.append(button);
    }
    setTheme(document.documentElement.dataset.theme);
  }

  /* Ambient Falling Star / Stardust Sprinkle System (All 20 Pages) */
  const initAmbientStardust = () => {
    if (window.__shadowStardustInit) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    if (document.querySelector(".prism-stardust-layer")) return;

    window.__shadowStardustInit = true;
    const layer = document.createElement("div");
    layer.className = "prism-stardust-layer";
    layer.setAttribute("aria-hidden", "true");

    // Pastel Aura Palette: Warm Ivory, Rose Dust, Taupe, Soft Rose, Pale Taupe
    const colors = [
      "#F7F2ED",
      "#D9A9AE",
      "#C8B3A9",
      "#EBCDD0",
      "#E4D7CF"
    ];

    const count = 24;
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < count; i++) {
      const star = document.createElement("span");
      const isSparkle = i % 4 === 0;
      star.className = "stardust-particle" + (isSparkle ? " stardust-sparkle" : "");

      const left = (Math.random() * 96 + 2).toFixed(2);
      const size = (1.5 + Math.random() * (isSparkle ? 2.1 : 1.7)).toFixed(1);
      const duration = (14 + Math.random() * 12).toFixed(1);
      const delay = (-Math.random() * 26).toFixed(1);
      const driftX = ((Math.random() - 0.5) * 56).toFixed(1);
      const opacity = (0.35 + Math.random() * 0.45).toFixed(2);
      const color = colors[i % colors.length];

      star.style.setProperty("--left", `${left}%`);
      star.style.setProperty("--size", `${size}px`);
      star.style.setProperty("--duration", `${duration}s`);
      star.style.setProperty("--delay", `${delay}s`);
      star.style.setProperty("--drift-x", `${driftX}px`);
      star.style.setProperty("--star-opacity", opacity);
      star.style.setProperty("--star-color", color);
      star.style.setProperty("--twinkle-duration", `${(2.8 + Math.random() * 3.4).toFixed(1)}s`);

      fragment.appendChild(star);
    }

    layer.appendChild(fragment);

    // Pause animation when tab is inactive to preserve CPU/GPU
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        layer.classList.add("is-paused");
      } else {
        layer.classList.remove("is-paused");
      }
    });

    const mount = () => {
      if (document.body && !document.querySelector(".prism-stardust-layer")) {
        document.body.insertAdjacentElement("afterbegin", layer);
      }
    };

    if (document.body) mount();
    else document.addEventListener("DOMContentLoaded", mount, { once: true });
  };

  initAmbientStardust();

  /* Universal Popup URL Security Guard: ensures no security alert popup leaks URLs */
  const URL_REGEX = /(https?:\/\/[^\s<>\"']+|www\.[^\s<>\"']+|[a-zA-Z0-9-]+\.(?:com|org|net|io|dev|ai|app|co|edu|gov|xyz|info|biz|me|cc|tv|online|ly|site|top|live|club|icu|pro|security)(?::\d+)?(?:\/[^\s<>\"']*)?)/gi;

  const sanitizePopupTree = (root) => {
    if (!root || !root.querySelectorAll) return;
    const dialogs = root.matches?.("dialog, [role='dialog'], .finding-dialog") ? [root] : Array.from(root.querySelectorAll("dialog, [role='dialog'], .finding-dialog"));
    dialogs.forEach((dialog) => {
      // Remove any <a> links containing URLs or pointing to URLs
      dialog.querySelectorAll("a").forEach((a) => {
        const href = a.getAttribute("href") || "";
        const text = a.textContent || "";
        if (URL_REGEX.test(href) || URL_REGEX.test(text)) {
          a.replaceWith(document.createTextNode("[URL Hidden for Security]"));
        }
      });
      // Scrub title tooltips
      dialog.querySelectorAll("[title]").forEach((el) => {
        const title = el.getAttribute("title") || "";
        if (URL_REGEX.test(title)) {
          el.setAttribute("title", title.replace(URL_REGEX, "[URL Hidden for Security]"));
        }
      });
    });
  };

  if (typeof MutationObserver !== "undefined") {
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const node of m.addedNodes) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            sanitizePopupTree(node);
          }
        }
      }
    });
    const attachObserver = () => {
      if (document.body) observer.observe(document.body, { childList: true, subtree: true });
    };
    if (document.body) attachObserver();
    else document.addEventListener("DOMContentLoaded", attachObserver, { once: true });
  }
})();
