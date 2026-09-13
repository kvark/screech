# Rusted-Metal (Screech)

Twisted Metal 2 remake on [Blade](https://github.com/kvark/blade).

Current playable slice: **one driveable car in a walled arena** that can fire a simple physics projectile. Adapted from Blade's `examples/vehicle`.

## Requirements

- Rust 1.92+ (tested with 1.98)
- Vulkan-capable GPU (or lavapipe for headless CPU Vulkan)

## Run

From the crate root:

```bash
cargo run --release
```

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

Initializes the engine, loads assets, ticks physics, renders a few frames
(including one projectile spawn), then **exits 0**. Prefer this over wrapping
the infinite game loop in `timeout` (exit 124).

```bash
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json \
  xvfb-run -a cargo run --release -- --smoke
# or: SCREECH_SMOKE=1 ...
```

## Controls

| Key | Action |
|-----|--------|
| ↑ / ↓ | Drive forward / reverse |
| ← / → | Steer |
| Space | Jump impulse |
| `F` | Fire projectile |
| `,` / `.` | Roll left / right |
| Esc | Quit |

Right HUD (debug builds): camera distance/angles, recover/respawn, impulse tweaks.

## Arena / combat

- Flat ground plus four wall cuboids (`data/level.ron` colliders; meshes in `ground.gltf`).
- `F` spawns a small dynamic ball (`data/projectile.gltf`) ahead of the car with forward velocity + CCD.
- Projectiles despawn on lifetime (~3s) or after contact with ground/walls/other bodies (short grace so the shot clears the chassis).

## CI

Workflow definition lives at `ci/github-actions-ci.yml` (copy to `.github/workflows/ci.yml`
once a GitHub token with the `workflow` scope can push Actions files). On PR/push to `main` it:

1. Installs mesa lavapipe, vulkan-tools, Xvfb, and windowing libs on `ubuntu-latest`
2. Runs `cargo build --release --locked`
3. Runs `./target/release/screech --smoke` under `VK_ICD_FILENAMES=…/lvp_icd.json` + `xvfb-run -a`

## Layout

- `src/main.rs`, `src/config.rs` — game loop and RON config types (from Blade vehicle example)
- `data/` — level + vehicle assets (`level.ron`, `raceFuture.ron`, glTF/GLB, ground, projectile)
- `data/shaders/` — Blade render shaders copied from `blade-render` 0.6 (`code/`), so `cargo run` works as an external crate without a Blade workspace checkout

Shader path and data path are resolved via `CARGO_MANIFEST_DIR`.

## Credits

- Engine: [Blade](https://github.com/kvark/blade) (MIT) — `blade-engine` from crates.io
- Vehicle example + assets (`raceFuture*`, `wheelRacing.glb`, `ground.*`, `orange_light_grid.png`) from Blade's `examples/vehicle` (MIT)
- Shaders from `blade-render` (MIT)

## Status

Combat arena slice: driveable car, solid/visible walls, simple projectile, CI smoke.
