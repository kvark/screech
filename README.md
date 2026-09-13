# Rusted-Metal (Screech)

Twisted Metal 2 remake on [Blade](https://github.com/kvark/blade).

This repository currently ships the first playable slice: **one driveable car on flat ground** (with simple wall cuboids), adapted from Blade's `examples/vehicle`.

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

## Controls

| Key | Action |
|-----|--------|
| ↑ / ↓ | Drive forward / reverse |
| ← / → | Steer |
| Space | Jump impulse |
| `,` / `.` | Roll left / right |
| Esc | Quit |

Debug HUD (debug builds): camera distance/angles, recover/respawn, impulse tweaks.

## Layout

- `src/main.rs`, `src/config.rs` — game loop and RON config types (from Blade vehicle example)
- `data/` — level + vehicle assets (`level.ron`, `raceFuture.ron`, glTF/GLB, ground)
- `data/shaders/` — Blade render shaders copied from `blade-render` 0.6 (`code/`), so `cargo run` works as an external crate without a Blade workspace checkout

Shader path and data path are resolved via `CARGO_MANIFEST_DIR`.

## Credits

- Engine: [Blade](https://github.com/kvark/blade) (MIT) — `blade-engine` from crates.io
- Vehicle example + assets (`raceFuture*`, `wheelRacing.glb`, `ground.*`, `orange_light_grid.png`) from Blade's `examples/vehicle` (MIT)
- Shaders from `blade-render` (MIT)

## Status

Scaffold only: driveable car, flat arena, no weapons/combat yet.
