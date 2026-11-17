# Rusted-Metal (Screech)

Twisted Metal 2 remake on [Blade](https://github.com/kvark/blade).

Current playable slice: **one driveable car in a walled arena**, a parked opponent mecho with HP, and a simple physics projectile. Adapted from Blade's `examples/vehicle`.

## Requirements

- Rust 1.92+ (tested with 1.98)
- Native: Vulkan-capable GPU (or lavapipe for headless CPU Vulkan)
- Browser: WebGL 2 and a keyboard (desktop browser recommended)

## Run

From the crate root:

```bash
cargo run --release
```

### Browser build (experimental)

The first web bootstrap embeds the game data and Blade shaders in the WASM
module. It uses the rasterizer and needs WebGL 2. No deployed web version is
provided by this repository; browser gameplay still needs validation on a
WebGL 2-capable device.

```bash
rustup target add wasm32-unknown-unknown
# Match the wasm-bindgen version in Cargo.lock:
cargo install wasm-bindgen-cli --version 0.2.128 --locked
./scripts/build-web.sh
python3 -m http.server 8000 --directory dist
```

Open <http://localhost:8000>. The build script checks the CLI version before
building and uses `--locked`. Keep `.cargo/config.toml`: Blade's web shader
pipelines need `--cfg gles`. If overriding `RUSTFLAGS`, preserve that flag.
Do not open `dist/index.html` directly via `file://`.

The loading overlay stays visible until the first rendered frame. Click the
canvas to focus keyboard input. WASD or arrows drive/steer, and R restarts the
arena. Escape exits and presents a reload button.
Resizing keeps the WebGL drawing buffer aligned with the canvas's device pixels.
If WebGL 2 is unavailable, the page explains how to try another browser/device
before downloading the game. Module, WASM, and asynchronous startup failures
remain visible with a reload option.

Run the browser-shell regression checks (Node 18+):

```bash
node --test web/boot.test.mjs
```

These checks use mocked browser APIs and do not prove WebGL rendering or gameplay.

### Headless / lavapipe (CI / Cloud Agents)

Lavapipe has **no ray-query**, so Screech defaults to `RenderBackend::Rasterizer`. Optional ray tracing:

```bash
SCREECH_RT=1 cargo run --release   # requires a ray-query capable device
```

CPU Vulkan + virtual display:

```bash
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json \
  xvfb-run -a cargo run --release
```

### Smoke mode (CI-friendly)

Initializes the engine, loads assets (including a parked opponent), ticks physics,
renders a few frames (including one projectile fired toward the opponent), then
**exits 0**. Prefer this over wrapping the infinite game loop in `timeout` (exit 124).

```bash
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json \
  xvfb-run -a cargo run --release -- --smoke
# or: SCREECH_SMOKE=1 ...
```

## Controls

| Key | Action |
|-----|--------|
| W / S or ↑ / ↓ | Drive forward / reverse |
| A / D or ← / → | Steer |
| Space | Jump impulse |
| `F` | Fire projectile |
| `,` / `.` | Roll left / right |
| R | Restart arena (restore target, clear shots, reset car) |
| Esc | Quit |

Right HUD: objective, **opponent HP**, high-contrast completion feedback, and **Restart arena**. Camera and dynamics controls include recover/respawn and impulse tweaks. Respawn only resets the car; Restart restores the entire encounter.

## Arena / combat

- Flat ground plus four wall cuboids (`data/level.ron` colliders; meshes in `ground.gltf`).
- Parked opponent mecho ahead of spawn (+Z), red tint, **100 HP**.
- `F` spawns a small dynamic ball (`data/projectile.gltf`) ahead of the car with forward velocity + CCD.
- Projectile contact with the opponent deals **25 damage** and despawns the shot; at 0 HP the opponent is marked destroyed (dark tint, no further hits).
- Destroying the target clears the current arena slice. Use **Restart arena** or `R` to replay without relaunching.
- Projectiles also despawn on lifetime (~3s) or contact with ground/walls/other bodies (short grace so the shot clears the chassis).

## CI

Workflow definition lives at `.github/workflows/ci.yml`. On every pull request (including stacked PRs) and pushes to `main`, it:

1. Installs mesa lavapipe, vulkan-tools, Xvfb, and windowing libs on `ubuntu-latest`
2. Checks formatting and runs `cargo test --release --locked`
3. Runs `cargo build --release --locked`
4. Runs `./target/release/screech --smoke` under `VK_ICD_FILENAMES=…/lvp_icd.json` + `xvfb-run -a`
5. Tests the browser startup shell and builds the locked WASM bundle

## Layout

- `src/main.rs`, `src/config.rs` — game loop and RON config types (from Blade vehicle example)
- `data/` — level + vehicle assets (`level.ron`, `raceFuture.ron`, glTF/GLB, ground, projectile)

Data path is resolved via `CARGO_MANIFEST_DIR`. Shader path comes from `blade_render::shader_dir()` (WGSL shipped in the `blade-render` crate). Native reads files normally; the browser mounts both directories into Blade’s VFS before starting the engine. `build.rs` resolves the pinned shader source through Cargo metadata.

## Credits

- Engine: [Blade](https://github.com/kvark/blade) (MIT) — `blade-engine` / `blade-render` from git (main)
- Vehicle example + assets (`raceFuture*`, `wheelRacing.glb`, `ground.*`, `orange_light_grid.png`) from Blade's `examples/vehicle` (MIT)
- Render shaders via `blade_render::shader_dir()` (MIT, packaged in `blade-render`)

## Status

Combat arena slice: driveable car, parked opponent with HP, solid/visible walls, simple projectile, CI smoke.
