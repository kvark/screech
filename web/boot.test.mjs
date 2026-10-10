// Run with: node --test web/boot.test.mjs
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { bootScreech } from "./boot.mjs";

const html = await readFile(new URL("./index.html", import.meta.url), "utf8");
const source = await readFile(new URL("./boot.mjs", import.meta.url), "utf8");

class Target {
  listeners = new Map();
  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) ?? [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }
  emit(type, properties = {}) {
    const event = {
      defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; },
      ...properties,
    };
    for (const listener of this.listeners.get(type) ?? []) listener(event);
    return event;
  }
}

function createHarness(options = {}) {
  const events = [];
  const nodes = Object.fromEntries(["boot", "boot-status", "controls", "reload", "blade"].map((id) => {
    const node = new Target();
    Object.assign(node, {
      hidden: ["controls", "reload"].includes(id),
      textContent: id === "boot-status" ? "Loading the arena…" : "",
      attributes: {},
      focusCount: 0,
      focus(attributes) {
        assert.equal(attributes.preventScroll, true);
        this.focusCount += 1;
      },
      setAttribute(name, value) { this.attributes[name] = value; },
    });
    // Any accidental HTML interpolation fails immediately.
    Object.defineProperty(node, "innerHTML", {
      set() { assert.fail("Startup must never inject HTML"); },
    });
    return [id, node];
  }));
  nodes["boot-status"].attributes.role = "status";
  nodes.blade.attributes["aria-busy"] = "true";
  const window = new Target();
  window.console = { error: (...args) => events.push(["console.error", ...args]) };
  window.location = { reload: () => events.push("reload") };
  const document = {
    getElementById(id) {
      assert.ok(Object.hasOwn(nodes, id));
      return options.missingMarkup ? null : nodes[id];
    },
    createElement(tag) {
      assert.equal(tag, "canvas");
      return {
        getContext(type, attributes) {
          events.push("webgl");
          assert.equal(type, "webgl2");
          assert.deepEqual(attributes, { antialias: false });
          if (options.contextError) throw options.contextError;
          if (options.webgl === false) return null;
          return {
            getExtension(name) {
              assert.equal(name, "WEBGL_lose_context");
              return options.noLoseContext ? null : { loseContext: () => events.push("release") };
            },
          };
        },
      };
    },
  };
  const loadGame = async () => {
    events.push("import");
    if (Object.hasOwn(options, "importError")) throw options.importError;
    if (options.beforeImport) await options.beforeImport(window);
    return {
      default: async () => {
        events.push("init");
        if (options.onInit) await options.onInit(window);
        if (Object.hasOwn(options, "initError")) throw options.initError;
      },
    };
  };
  return { events, nodes, window, run: () => bootScreech({ window, document, loadGame }) };
}

async function runBoot(options) {
  const harness = createHarness(options);
  await harness.run();
  return harness;
}

test("the shipped page wires the tested bootstrap and accessible Blade canvas", () => {
  assert.match(html, /import \{ bootScreech \} from "\.\/boot\.mjs"/);
  assert.match(html, /await bootScreech\(\)/);
  assert.match(html, /<canvas id="blade" tabindex="0"[^>]*aria-label=/);
  assert.match(html, /id="boot-status" role="status" aria-live="polite"/);
  assert.match(html, /<aside id="controls"[^>]*hidden>/);
  assert.match(html, /<button id="reload" type="button" hidden>/);
  assert.match(html, /<noscript>/);
  assert.match(source, /loadGame = \(\) => import\("\.\/pkg\/screech\.js"\)/);
});

test("the control legend pairs WASD, arrows, and arena restart with their actions", () => {
  const controls = html.match(/<aside id="controls"[^>]*>([\s\S]*?)<\/aside>/)?.[1];
  assert.ok(controls, "The page should include a control legend");
  assert.match(controls, /<kbd>W S<\/kbd>\s+or\s+<kbd>↑ ↓<\/kbd>\s+Drive \/ reverse/);
  assert.match(controls, /<kbd>A D<\/kbd>\s+or\s+<kbd>← →<\/kbd>\s+Steer/);
  assert.match(controls, /<kbd>Space<\/kbd>\s+Jump/);
  assert.match(controls, /<kbd>F<\/kbd>\s+Fire/);
  assert.match(controls, /<kbd>, \.<\/kbd>\s+Roll left \/ right/);
  assert.match(controls, /<kbd>R<\/kbd>\s+Restart arena/);
  assert.match(controls, /<kbd>Esc<\/kbd>\s+Quit/);
});

test("successful init releases the probe before import but waits for the first rendered frame", async () => {
  const { nodes, events, window } = await runBoot();
  assert.deepEqual(events, ["webgl", "release", "import", "init"]);
  assert.equal(nodes.boot.hidden, false);
  assert.equal(nodes.controls.hidden, true);
  assert.equal(nodes.blade.focusCount, 0);
  assert.equal(nodes.blade.attributes["aria-busy"], "true");
  window.emit("screech-ready");
  assert.equal(nodes.boot.hidden, true);
  assert.equal(nodes.controls.hidden, false);
  assert.equal(nodes.blade.attributes["aria-busy"], "false");
  assert.equal(nodes.blade.focusCount, 1);
  window.emit("screech-ready");
  assert.equal(nodes.blade.focusCount, 1, "Repeated ready signals must not steal focus");
});

test("a ready event emitted during init is not missed", async () => {
  const { nodes } = await runBoot({ onInit: (window) => window.emit("screech-ready") });
  assert.equal(nodes.boot.hidden, true);
  assert.equal(nodes.controls.hidden, false);
  assert.equal(nodes.blade.focusCount, 1);
});

for (const options of [{ webgl: false }, { contextError: new Error("Blocked context") }]) {
  test(`WebGL 2 ${options.webgl === false ? "unavailable" : "throws"}: no WASM download, with recovery guidance`, async () => {
    const { events, nodes } = await runBoot(options);
    assert.equal(events[0], "webgl");
    assert.ok(!events.includes("import"));
    assert.match(nodes["boot-status"].textContent, /WebGL 2 is unavailable/);
    assert.match(nodes["boot-status"].textContent, /graphics acceleration/);
    assert.match(nodes["boot-status"].textContent, /another browser or device/);
    assert.equal(nodes["boot-status"].attributes.role, "alert");
    assert.equal(nodes["boot-status"].attributes["aria-live"], "assertive");
    assert.equal(nodes.reload.hidden, false);
    assert.equal(nodes.controls.hidden, true);
    assert.equal(nodes.blade.attributes["aria-busy"], "false");
  });
}

test("the context-release extension is optional", async () => {
  const { events } = await runBoot({ noLoseContext: true });
  assert.deepEqual(events, ["webgl", "import", "init"]);
});

for (const key of ["importError", "initError"]) {
  test(`${key} replaces the loader with the original error and reload button`, async () => {
    const failure = new Error("<script>unsafe content</script> failed to fetch");
    const { nodes, events, window } = await runBoot({ [key]: failure });
    assert.equal(nodes.boot.hidden, false);
    assert.match(nodes["boot-status"].textContent, /Screech couldn't start/);
    assert.ok(nodes["boot-status"].textContent.includes(failure.message));
    assert.match(nodes["boot-status"].textContent, /Reload the page/);
    assert.equal(nodes["boot-status"].attributes.role, "alert");
    assert.equal(nodes.reload.textContent, "Reload game");
    assert.equal(nodes.reload.focusCount, 1);
    assert.equal(events.at(-1)[2], failure, "Original error should still reach the console");
    window.emit("screech-ready");
    assert.equal(nodes.boot.hidden, false, "A late ready signal must not hide a failure");
    assert.equal(nodes.controls.hidden, true);
    nodes.reload.emit("click");
    assert.equal(events.at(-1), "reload");
  });
}

test("an error after the first frame restores the overlay and hides controls", async () => {
  const { nodes, window } = await runBoot();
  window.emit("screech-ready");
  const event = window.emit("error", { error: new Error("Renderer failed") });
  assert.equal(event.defaultPrevented, false, "Real errors remain visible in browser tools");
  assert.equal(nodes.boot.hidden, false);
  assert.equal(nodes.controls.hidden, true);
  assert.match(nodes["boot-status"].textContent, /Screech stopped unexpectedly/);
  assert.match(nodes["boot-status"].textContent, /Renderer failed/);
});

test("async error events during import are caught by listeners registered in advance", async () => {
  const { nodes } = await runBoot({
    beforeImport: (window) => window.emit("error", { message: "Script failed" }),
  });
  assert.match(nodes["boot-status"].textContent, /Script failed/);
  assert.equal(nodes["boot-status"].attributes.role, "alert");
});

for (const reason of [null, undefined, "Promise failed", new Error("Promise failed")]) {
  test(`unhandled rejection (${String(reason)}) is reported safely`, async () => {
    const { nodes, window } = await runBoot();
    const event = window.emit("unhandledrejection", { reason });
    assert.equal(event.defaultPrevented, false);
    assert.ok(nodes["boot-status"].textContent.includes(reason?.message ?? String(reason)));
    assert.equal(nodes["boot-status"].attributes.role, "alert");
    assert.equal(nodes.controls.hidden, true);
  });
}

test("spawn_app does not suppress errors based on a legacy control-flow message", async () => {
  const { nodes, window } = await runBoot();
  window.emit("unhandledrejection", {
    reason: "Using exceptions for control flow, don't mind me. This isn't actually an error!",
  });
  assert.equal(nodes["boot-status"].attributes.role, "alert");
  assert.equal(nodes.boot.hidden, false);
});

test("the first failure remains visible when duplicate errors or exit events follow", async () => {
  const { nodes, window } = await runBoot();
  window.emit("error", { error: new Error("Original failure") });
  window.emit("unhandledrejection", { reason: new Error("Secondary failure") });
  window.emit("screech-exit");
  assert.match(nodes["boot-status"].textContent, /Original failure/);
  assert.doesNotMatch(nodes["boot-status"].textContent, /Secondary failure/);
  assert.equal(nodes["boot-status"].attributes.role, "alert");
  assert.equal(nodes.reload.focusCount, 1);
});

test("quit shows a focusable restart button and cannot be undone by late ready events", async () => {
  const { nodes, events, window } = await runBoot();
  window.emit("screech-ready");
  window.emit("screech-exit");
  assert.equal(nodes.boot.hidden, false);
  assert.equal(nodes.controls.hidden, true);
  assert.equal(nodes["boot-status"].attributes.role, "status");
  assert.match(nodes["boot-status"].textContent, /Session ended/);
  assert.equal(nodes.reload.hidden, false);
  assert.equal(nodes.reload.textContent, "Play again");
  assert.equal(nodes.reload.focusCount, 1);
  window.emit("screech-exit");
  window.emit("screech-ready");
  assert.equal(nodes.boot.hidden, false);
  assert.equal(nodes.reload.focusCount, 1);
  nodes.reload.emit("click");
  assert.equal(events.at(-1), "reload");
});

test("canvas focus and scroll prevention apply only to the running game", async () => {
  const { nodes, window } = await runBoot();
  nodes.blade.emit("pointerdown");
  assert.equal(nodes.blade.focusCount, 0);
  assert.equal(nodes.blade.emit("keydown", { code: "Space" }).defaultPrevented, false);
  window.emit("screech-ready");
  nodes.blade.emit("pointerdown");
  assert.equal(nodes.blade.focusCount, 2);
  for (const code of ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"]) {
    assert.equal(nodes.blade.emit("keydown", { code }).defaultPrevented, true);
  }
  for (const modifier of ["ctrlKey", "altKey", "metaKey"]) {
    assert.equal(nodes.blade.emit("keydown", { code: "ArrowLeft", [modifier]: true }).defaultPrevented, false);
  }
  assert.equal(nodes.blade.emit("keydown", { code: "Tab" }).defaultPrevented, false);
  window.emit("screech-exit");
  nodes.blade.emit("pointerdown");
  assert.equal(nodes.blade.focusCount, 2);
  assert.equal(nodes.blade.emit("keydown", { code: "Space" }).defaultPrevented, false);
});

test("missing optional markup does not obscure an initialization error", async () => {
  const failure = new Error("WASM failed");
  const { events } = await runBoot({ missingMarkup: true, initError: failure });
  assert.equal(events.at(-1)[0], "console.error");
  assert.equal(events.at(-1)[2], failure);
});
