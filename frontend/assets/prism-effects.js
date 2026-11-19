/* Reusable Assistant Animation Engine: IDLE, THINKING, and RESPONDING state coordination */
(() => {
  const avatars = () => document.querySelectorAll(".assistant-avatar");
  let respondTimer = null;
  let safetyTimer = null;

  const setState = (state) => {
    const validState = state === "thinking" ? "thinking" : state === "responding" ? "responding" : "idle";

    // Clear any pending transition timers
    if (respondTimer) { clearTimeout(respondTimer); respondTimer = null; }
    if (safetyTimer) { clearTimeout(safetyTimer); safetyTimer = null; }

    avatars().forEach((avatar) => {
      avatar.dataset.state = validState;
      avatar.setAttribute("aria-busy", String(validState === "thinking"));
    });

    if (validState === "responding") {
      // Smoothly transition from responding back to idle after the entrance bloom
      respondTimer = setTimeout(() => {
        avatars().forEach((avatar) => {
          avatar.dataset.state = "idle";
          avatar.setAttribute("aria-busy", "false");
        });
        respondTimer = null;
      }, 1400);
    } else if (validState === "thinking") {
      // Safety watchdog: if network stalls unexpectedly, return to idle after 25s
      safetyTimer = setTimeout(() => {
        avatars().forEach((avatar) => {
          if (avatar.dataset.state === "thinking") {
            avatar.dataset.state = "idle";
            avatar.setAttribute("aria-busy", "false");
          }
        });
        safetyTimer = null;
      }, 25000);
    }
  };

  // Expose global hook for direct chat lifecycle binding
  window.setAssistantState = setState;

  // Defensive fallback: observe messages container for assistant message additions
  const messages = document.getElementById("messages");
  if (messages) {
    new MutationObserver((records) => {
      const hasAssistantReply = records.some((record) =>
        [...record.addedNodes].some((node) =>
          node.nodeType === Node.ELEMENT_NODE &&
          (node.matches(".assistant-head") || node.querySelector(".assistant-head"))
        )
      );
      if (hasAssistantReply) {
        setState("responding");
      }
    }).observe(messages, { childList: true });
  }

  // Set initial idle state
  setState("idle");
})();
