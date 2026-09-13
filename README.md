# Rusted-Metal (Screech)

Twisted Metal 2 remake on [Blade](https://github.com/kvark/blade).

Current playable slice: **one driveable car in a walled arena**, a parked opponent mecho with HP, and a simple physics projectile. Adapted from Blade's `examples/vehicle`.

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
| ↑ / ↓ | Drive forward / reverse |
| ← / → | Steer |
| Space | Jump impulse |
| `F` | Fire projectile |
| `,` / `.` | Roll left / right |
| Esc | Quit |

Right HUD: camera distance/angles, recover/respawn, impulse tweaks, **opponent HP** bar.

## Arena / combat

- Flat ground plus four wall cuboids (`data/level.ron` colliders; meshes in `ground.gltf`).
- Parked opponent mecho ahead of spawn (+Z), red tint, **100 HP**.
- `F` spawns a small dynamic ball (`data/projectile.gltf`) ahead of the car with forward velocity + CCD.
- Projectile contact with the opponent deals **25 damage** and despawns the shot; at 0 HP the opponent is marked destroyed (dark tint, no further hits).
- Projectiles also despawn on lifetime (~3s) or contact with ground/walls/other bodies (short grace so the shot clears the chassis).

## CI

Workflow definition lives at `ci/github-actions-ci.yml` (copy to `.github/workflows/ci.yml`
once a GitHub token with the `workflow` scope can push Actions files). On PR/push to `main` it:

1. Installs mesa lavapipe, vulkan-tools, Xvfb, and windowing libs on `ubuntu-latest`
2. Runs `cargo build --release --locked`
3. Runs `./target/release/screech --smoke` under `VK_ICD_FILENAMES=…/lvp_icd.json` + `xvfb-run -a`

## Layout

- `src/main.rs`, `src/config.rs` — game loop and RON config types (from Blade vehicle example)
- `data/` — level + vehicle assets (`level.ron`, `raceFuture.ron`, glTF/GLB, ground, projectile)

Data path is resolved via `CARGO_MANIFEST_DIR`. Shader path comes from `blade_render::shader_dir()` (WGSL shipped in the `blade-render` crate).

## Credits

- Engine: [Blade](https://github.com/kvark/blade) (MIT) — `blade-engine` / `blade-render` from git (main)
- Vehicle example + assets (`raceFuture*`, `wheelRacing.glb`, `ground.*`, `orange_light_grid.png`) from Blade's `examples/vehicle` (MIT)
- Render shaders via `blade_render::shader_dir()` (MIT, packaged in `blade-render`)

## Status

Combat arena slice: driveable car, parked opponent with HP, solid/visible walls, simple projectile, CI smoke.
