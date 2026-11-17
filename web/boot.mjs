// Keep startup independent of browser globals so the deployed logic can also be
// tested with Node. The generated WASM module is loaded only after the GPU check.
export async function bootScreech({
  window = globalThis.window,
  document = globalThis.document,
  loadGame = () => import("./pkg/screech.js"),
} = {}) {
  const boot = document.getElementById("boot");
  const status = document.getElementById("boot-status");
  const controls = document.getElementById("controls");
  const reload = document.getElementById("reload");
  const canvas = document.getElementById("blade");
  let state = "loading";

  const messageOf = (error) =>
    typeof error?.message === "string" ? error.message : String(error);
  const focusCanvas = () => {
    if (state === "ready") canvas?.focus({ preventScroll: true });
  };
  const showOverlay = (message, isError, buttonLabel) => {
    if (boot) boot.hidden = false;
    if (controls) controls.hidden = true;
    if (status) {
      status.setAttribute("role", isError ? "alert" : "status");
      status.setAttribute("aria-live", isError ? "assertive" : "polite");
      // Error text may contain arbitrary server/browser content; never use HTML.
      status.textContent = message;
    }
    canvas?.setAttribute("aria-busy", "false");
    if (reload) {
      reload.textContent = buttonLabel;
      reload.hidden = false;
      reload.focus({ preventScroll: true });
    }
  };
  const fail = (error) => {
    if (state === "failed") return;
    const heading = state === "ready"
      ? "Screech stopped unexpectedly."
      : "Screech couldn't start.";
    state = "failed";
    showOverlay(`${heading}\n\n${messageOf(error)}\n\nReload the page to try again.`, true, "Reload game");
  };

  // Subscribe before importing: the Rust entry point can start during init().
  window.addEventListener("screech-ready", () => {
    if (state !== "loading") return;
    state = "ready";
    if (boot) boot.hidden = true;
    if (controls) controls.hidden = false;
    canvas?.setAttribute("aria-busy", "false");
    focusCanvas();
  });
  window.addEventListener("screech-exit", () => {
    if (state === "failed" || state === "exited") return;
    state = "exited";
    showOverlay("Session ended.\nReload to drive again.", false, "Play again");
  });
  window.addEventListener("error", (event) => {
    fail(event.error ?? event.message);
  });
  window.addEventListener("unhandledrejection", (event) => {
    fail(event.reason);
  });
  reload?.addEventListener("click", () => window.location.reload());
  canvas?.addEventListener("pointerdown", focusCanvas);
  canvas?.addEventListener("keydown", (event) => {
    // Do not scroll the page with driving/jump keys, or capture browser shortcuts.
    if (state === "ready" && !event.ctrlKey && !event.altKey && !event.metaKey &&
        ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(event.code)) {
      event.preventDefault();
    }
  });

  try {
    let gl;
    try {
      gl = document.createElement("canvas").getContext("webgl2", { antialias: false });
    } catch {
      // Some browsers throw instead of returning null when WebGL is blocked.
    }
    if (!gl) {
      throw new Error(
        "WebGL 2 is unavailable. Enable graphics acceleration in your browser's settings " +
        "and restart it, or try another browser or device. If you are using an embedded " +
        "or remote browser, try opening the game in a regular browser on your device.",
      );
    }
    // Release the temporary context before Blade allocates its own on #blade.
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    const { default: init } = await loadGame();
    await init();
    // Only Rust's first rendered frame dismisses the overlay, never init() alone.
  } catch (error) {
    fail(error);
    window.console?.error("Screech startup failed:", error);
  }
}
