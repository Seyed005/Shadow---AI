/* Apply the saved/system theme before stylesheets paint to prevent a theme flash. */
(() => {
  const key = "shadow-ai-theme";
  let saved = null;
  try { saved = localStorage.getItem(key); } catch (_) { /* storage may be unavailable */ }
  const systemDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  const theme = saved === "dark" || saved === "light" ? saved : (systemDark ? "dark" : "light");
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
})();
