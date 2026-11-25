#!/usr/bin/env python3
"""Generate the original TM2-look arena assets: HDR sky, walls, landmark tower.

No imported artwork. The equirect sky is authored in pre-tonemap linear values
so Blade's raster Reinhard operator still reads as a saturated arcade blue.
"""
from __future__ import annotations

import base64
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# ---------------------------------------------------------------------------
# glTF helpers (same conventions as generate-charge-pad.py)
# ---------------------------------------------------------------------------

def new_doc(generator: str):
    return dict(
        asset=dict(version="2.0", generator=generator),
        scene=0,
        scenes=[dict(nodes=[0])],
        nodes=[dict(mesh=0)],
        meshes=[dict(primitives=[])],
        buffers=[],
        bufferViews=[],
        accessors=[],
        materials=[],
    )


def write_gltf(doc, blob: bytearray, dest: Path):
    doc["buffers"].append(
        dict(
            byteLength=len(blob),
            uri="data:application/octet-stream;base64," + base64.b64encode(blob).decode("ascii"),
        )
    )
    dest.write_text(json.dumps(doc, separators=(",", ":")) + "\n")


def make_accessors(doc, blob: bytearray):
    def accessor(values, packing, kind, bounds=False):
        while len(blob) % 4:
            blob.append(0)
        start = len(blob)
        for value in values:
            blob.extend(struct.pack("<" + packing, *value))
        view = len(doc["bufferViews"])
        doc["bufferViews"].append(dict(buffer=0, byteOffset=start, byteLength=len(blob) - start))
        item = dict(
            bufferView=view,
            componentType=5123 if packing == "H" else 5126,
            count=len(values),
            type=kind,
        )
        if bounds:
            item.update(min=list(map(min, zip(*values))), max=list(map(max, zip(*values))))
        doc["accessors"].append(item)
        return len(doc["accessors"]) - 1

    def emit(name, color, glow, positions, normals, uvs, indices, metallic=0.2, roughness=0.7):
        material = len(doc["materials"])
        doc["materials"].append(
            dict(
                name=name,
                emissiveFactor=glow,
                pbrMetallicRoughness=dict(
                    baseColorFactor=color + [1],
                    metallicFactor=metallic,
                    roughnessFactor=roughness,
                ),
            )
        )
        doc["meshes"][0]["primitives"].append(
            dict(
                material=material,
                indices=accessor(indices, "H", "SCALAR"),
                attributes=dict(
                    POSITION=accessor(positions, "3f", "VEC3", True),
                    NORMAL=accessor(normals, "3f", "VEC3"),
                    TEXCOORD_0=accessor(uvs, "2f", "VEC2"),
                ),
            )
        )

    def boxes(name, color, glow, shapes, metallic=0.2, roughness=0.7):
        p, n, uv, idx = [], [], [], []
        for center, size in shapes:
            for a, b, c in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
                for sign in (1, -1):
                    start = len(p)
                    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        vtx = list(center)
                        vtx[a] += sign * size[a] / 2
                        vtx[b] += u * size[b] / 2
                        vtx[c] += v * size[c] / 2
                        p.append(tuple(vtx))
                        n.append(tuple(sign if i == a else 0 for i in range(3)))
                        uv.append(((u + 1) / 2, (v + 1) / 2))
                    order = (0, 1, 2, 0, 2, 3) if sign > 0 else (0, 2, 1, 0, 3, 2)
                    idx.extend((start + i,) for i in order)
        emit(name, color, glow, p, n, uv, idx, metallic, roughness)

    return boxes, emit


# ---------------------------------------------------------------------------
# Landmark: chunky low-poly monument tower (original, not a TM2 mesh)
# Local space, base at y=0 so level.ron can sit it on the ground plane.
# ---------------------------------------------------------------------------

def build_tower():
    doc = new_doc("Screech TM2 landmark tower")
    blob = bytearray()
    boxes, _ = make_accessors(doc, blob)

    bronze = ([0.42, 0.26, 0.12], [0.04, 0.02, 0.0])
    iron = ([0.18, 0.16, 0.15], [0, 0, 0])
    gold = ([0.92, 0.68, 0.18], [0.35, 0.18, 0.02])
    teal = ([0.05, 0.72, 0.78], [0.02, 0.45, 0.5])

    # Plinth
    boxes("sandstone plinth", [0.76, 0.62, 0.42], [0, 0, 0], [
        ((0, 0.3, 0), (5.2, 0.6, 5.2)),
        ((0, 0.65, 0), (4.6, 0.16, 4.6)),
    ], metallic=0.05, roughness=0.85)

    # Four splayed legs from the plinth corners up to a mid deck
    leg_shapes = []
    for sx, sz in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        # Two stacked chunky beams approximating a taper
        leg_shapes.append(((sx * 1.7, 2.2, sz * 1.7), (0.7, 3.2, 0.7)))
        leg_shapes.append(((sx * 1.05, 5.4, sz * 1.05), (0.58, 3.2, 0.58)))
    boxes("bronze legs", *bronze, leg_shapes, metallic=0.45, roughness=0.45)

    # Cross braces at mid height
    boxes("iron braces", *iron, [
        ((0, 3.7, 0), (3.4, 0.22, 0.28)),
        ((0, 3.7, 0), (0.28, 0.22, 3.4)),
        ((0, 6.8, 0), (2.2, 0.2, 0.24)),
        ((0, 6.8, 0), (0.24, 0.2, 2.2)),
    ], metallic=0.5, roughness=0.4)

    # Mid deck + teal accent ring (echoes the charge pad, stays readable)
    boxes("gold mid deck", *gold, [
        ((0, 8.15, 0), (3.4, 0.3, 3.4)),
        ((0, 8.0, 0), (3.0, 0.16, 3.0)),
    ], metallic=0.55, roughness=0.35)
    boxes("teal mid ring", *teal, [
        ((0, 8.38, 0), (3.6, 0.16, 0.28)),
        ((0, 8.38, 0), (0.28, 0.16, 3.6)),
    ], metallic=0.2, roughness=0.4)

    # Upper shaft
    boxes("bronze shaft", *bronze, [
        ((0, 11.2, 0), (1.5, 5.8, 1.5)),
        ((0, 11.2, -0.82), (0.28, 5.4, 0.16)),
        ((0, 11.2, 0.82), (0.28, 5.4, 0.16)),
        ((-0.82, 11.2, 0), (0.16, 5.4, 0.28)),
        ((0.82, 11.2, 0), (0.16, 5.4, 0.28)),
    ], metallic=0.45, roughness=0.45)

    # Lookout
    boxes("gold lookout", *gold, [
        ((0, 14.25, 0), (2.8, 0.28, 2.8)),
        ((0, 14.55, 0), (2.2, 0.18, 2.2)),
    ], metallic=0.55, roughness=0.35)
    boxes("teal lookout ring", *teal, [
        ((0, 14.48, 0), (3.0, 0.14, 0.22)),
        ((0, 14.48, 0), (0.22, 0.14, 3.0)),
    ], metallic=0.2, roughness=0.4)

    # Spire
    boxes("bronze spire", *bronze, [
        ((0, 16.1, 0), (1.0, 2.4, 1.0)),
        ((0, 18.2, 0), (0.62, 1.8, 0.62)),
        ((0, 19.7, 0), (0.34, 1.2, 0.34)),
        ((0, 20.55, 0), (0.16, 0.7, 0.16)),
    ], metallic=0.5, roughness=0.35)
    boxes("gold beacon", [1.0, 0.82, 0.25], [0.8, 0.45, 0.05], [
        ((0, 21.05, 0), (0.42, 0.42, 0.42)),
    ], metallic=0.3, roughness=0.3)

    write_gltf(doc, blob, DATA / "landmark-tower.gltf")
    print("wrote", DATA / "landmark-tower.gltf")


# ---------------------------------------------------------------------------
# Tall, brightly colored arena walls (visual only; colliders stay as-is)
# ---------------------------------------------------------------------------

def build_walls():
    doc = new_doc("Screech TM2 arena walls")
    blob = bytearray()
    boxes, _ = make_accessors(doc, blob)

    # Closed box just outside the short gray curb in ground.gltf.
    # Short enough that the spawn camera still sees the sky above them, tall
    # enough to read from across the arena. Base sits on the ground (y=1).
    # Per-side heights. The far (+Z) wall is shorter so the default spawn
    # camera, which looks slightly down, still shows sky behind the tower.
    heights = {"+z": 3.2, "-z": 5.0, "+x": 5.0, "-x": 5.0}
    thick = 1.2
    length = 42.4
    radius = 21.0
    cream = [0.86, 0.74, 0.52]
    shadow = [0.22, 0.16, 0.12]
    cornice = [0.95, 0.86, 0.68]
    # Per-side arcade bands, Hong Kong / Paris readable color blocking.
    bands = {
        "+z": [0.86, 0.22, 0.16],  # terracotta far wall
        "-z": [0.10, 0.62, 0.70],  # teal near wall
        "+x": [0.95, 0.68, 0.12],  # amber
        "-x": [0.72, 0.22, 0.68],  # magenta
    }

    def wall_axis(side):
        height = heights[side]
        wall_y = 1.0 + height / 2.0
        if side.endswith("z"):
            z = radius if side == "+z" else -radius
            return (0, wall_y, z), (length, height, thick), (1, 0, 0)
        x = radius if side == "+x" else -radius
        return (x, wall_y, 0), (thick, height, length), (0, 0, 1)

    for side, band in bands.items():
        center, size, along = wall_axis(side)
        boxes(f"{side} body", cream, [0, 0, 0], [(center, size)], metallic=0.04, roughness=0.8)
        # Dark kickboard
        kick = list(size)
        kick[1] = 0.8
        kick_c = list(center)
        kick_c[1] = 1.35
        boxes(f"{side} kickboard", shadow, [0, 0, 0], [(tuple(kick_c), tuple(kick))], metallic=0.1, roughness=0.7)
        # Bright stripe near the top
        stripe = list(size)
        stripe[1] = min(1.1, size[1] * 0.35)
        if along[0]:
            stripe[2] += 0.16
        else:
            stripe[0] += 0.16
        stripe_c = list(center)
        top = center[1] + size[1] / 2
        stripe_c[1] = top - 0.55 - stripe[1] / 2
        boxes(f"{side} band", band, [c * 0.12 for c in band], [(tuple(stripe_c), tuple(stripe))], metallic=0.08, roughness=0.55)
        # Cornice
        cap = list(size)
        cap[1] = 0.32
        if along[0]:
            cap[2] += 0.3
            cap[0] += 0.2
        else:
            cap[0] += 0.3
            cap[2] += 0.2
        cap_c = list(center)
        cap_c[1] = top + 0.05
        boxes(f"{side} cornice", cornice, [0, 0, 0], [(tuple(cap_c), tuple(cap))], metallic=0.06, roughness=0.65)
        # Recessed inner panels
        panel_h = min(1.5, size[1] * 0.45)
        panel_y = 1.0 + 0.9 + panel_h / 2
        panel = [2.8, panel_h, 2.8]
        if along[0]:
            panel[0], panel[2] = 2.8, 0.18
            inner = 1 if center[2] < 0 else -1
            py, pz = panel_y, center[2] + inner * (thick / 2 - 0.08)
            shapes = [((x, py, pz), tuple(panel)) for x in (-12.0, -4.0, 4.0, 12.0)]
        else:
            panel[0], panel[2] = 0.18, 2.8
            inner = 1 if center[0] < 0 else -1
            px, py = center[0] + inner * (thick / 2 - 0.08), panel_y
            shapes = [((px, py, z), tuple(panel)) for z in (-12.0, -4.0, 4.0, 12.0)]
        boxes(f"{side} panels", [0.62, 0.48, 0.32], [0, 0, 0], shapes, metallic=0.05, roughness=0.8)

    write_gltf(doc, blob, DATA / "arena-walls.gltf")
    print("wrote", DATA / "arena-walls.gltf")


# ---------------------------------------------------------------------------
# Equirectangular Radiance HDR sky
# ---------------------------------------------------------------------------

def inv_reinhard(c: float) -> float:
    c = min(max(c, 0.0), 0.98)
    return c / (1.0 - c)


def hash2(x: int, y: int) -> float:
    n = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return n - math.floor(n)


def value_noise(x: float, y: float) -> float:
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    u = fx * fx * (3 - 2 * fx)
    v = fy * fy * (3 - 2 * fy)
    return (
        (hash2(ix, iy) * (1 - u) + hash2(ix + 1, iy) * u) * (1 - v)
        + (hash2(ix, iy + 1) * (1 - u) + hash2(ix + 1, iy + 1) * u) * v
    )


def fbm(x: float, y: float, octaves: int = 5) -> float:
    amp, freq, total, norm = 1.0, 1.0, 0.0, 0.0
    for _ in range(octaves):
        total += amp * value_noise(x * freq, y * freq)
        norm += amp
        amp *= 0.5
        freq *= 2.05
    return total / norm


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(3))


def float_to_rgbe(rgb) -> tuple[int, int, int, int]:
    r, g, b = (max(0.0, c) for c in rgb)
    v = max(r, g, b)
    if v < 1e-32:
        return (0, 0, 0, 0)
    mantissa, exp = math.frexp(v)
    factor = mantissa * 256.0 / v
    return (
        min(255, int(r * factor)),
        min(255, int(g * factor)),
        min(255, int(b * factor)),
        exp + 128,
    )


def write_rle_channel(out: bytearray, data: bytes):
    i, n = 0, len(data)
    while i < n:
        if i + 1 < n and data[i] == data[i + 1]:
            j = i + 2
            while j < n and data[j] == data[i] and (j - i) < 127:
                j += 1
            out.append(128 + (j - i))
            out.append(data[i])
            i = j
        else:
            j = i + 1
            while j < n and (j - i) < 128:
                if j + 1 < n and data[j] == data[j + 1]:
                    break
                j += 1
            out.append(j - i)
            out.extend(data[i:j])
            i = j


def write_hdr(path: Path, width: int, height: int, pixels: list[tuple[float, float, float]]):
    header = (
        "#?RADIANCE\n"
        "# Screech original TM2-look arcade sky\n"
        "FORMAT=32-bit_rle_rgbe\n"
        "GAMMA=1.0\n"
        "EXPOSURE=1.0\n"
        "\n"
        f"-Y {height} +X {width}\n"
    ).encode("ascii")
    body = bytearray()
    # Radiance -Y means first scanline is the top of the image (v=1, zenith).
    for y in range(height - 1, -1, -1):
        row = [float_to_rgbe(pixels[y * width + x]) for x in range(width)]
        body.extend((2, 2, (width >> 8) & 0xFF, width & 0xFF))
        for channel in range(4):
            write_rle_channel(body, bytes(px[channel] for px in row))
    path.write_bytes(header + body)
    print("wrote", path, f"{width}x{height}")


def sky_color(u: float, v: float) -> tuple[float, float, float]:
    # Match blade-render map_equirect_dir_to_uv: v=0 down, v=0.5 horizon, v=1 zenith.
    yaw = (u * 2.0 - 1.0) * math.pi
    pitch = (v - 0.5) * math.pi
    cy, sy = math.cos(pitch), math.sin(pitch)
    direction = (cy * math.sin(yaw), sy, cy * math.cos(yaw))

    zenith = tuple(inv_reinhard(c) for c in (0.16, 0.42, 0.92))
    mid = tuple(inv_reinhard(c) for c in (0.32, 0.60, 0.94))
    horizon = tuple(inv_reinhard(c) for c in (0.48, 0.70, 0.94))
    ground = tuple(inv_reinhard(c) for c in (0.46, 0.50, 0.44))
    cloud_lit = tuple(inv_reinhard(c) for c in (0.94, 0.95, 0.98))
    cloud_shade = tuple(inv_reinhard(c) for c in (0.78, 0.84, 0.94))

    if v < 0.5:
        t = max(0.0, v / 0.5)
        # Tighten the blend near the horizon so the ground doesn't muddy the sky.
        t = t * t * (3 - 2 * t)
        color = lerp3(ground, horizon, t)
    else:
        t = (v - 0.5) / 0.5
        color = lerp3(horizon, mid, min(1.0, t * 1.4)) if t < 0.55 else lerp3(mid, zenith, (t - 0.55) / 0.45)

    # Soft cumulus in mid-to-upper sky, computed in yaw/altitude so they stay chunky.
    if 0.48 < v < 0.92:
        # Two noise layers at different scales; warp by yaw for drifting rows.
        nx = yaw * 1.15
        ny = (v - 0.5) * 6.5
        n = fbm(nx + 2.0, ny * 1.4, 5)
        n2 = fbm(nx * 0.45 + 8.0, ny * 0.7 + 3.0, 4)
        # Density peaks around mid-sky, thins at zenith (Paris-style scattered clouds).
        altitude_window = math.sin((v - 0.48) / (0.92 - 0.48) * math.pi) ** 0.85
        blob = (n * 0.7 + n2 * 0.3 - 0.42) * altitude_window
        coverage = max(0.0, min(1.0, blob * 1.8))
        coverage = coverage * coverage * (3 - 2 * coverage)
        if coverage > 0.0:
            shade = max(0.0, min(1.0, (n2 - 0.35) * 1.6))
            cloud = lerp3(cloud_shade, cloud_lit, shade)
            color = lerp3(color, cloud, coverage)

    # Soft sun glow matching RasterConfig light_dir (towards the light).
    light = (0.35, 1.0, 0.25)
    llen = math.sqrt(sum(c * c for c in light))
    light = tuple(c / llen for c in light)
    mu = max(0.0, direction[0] * light[0] + direction[1] * light[1] + direction[2] * light[2])
    sun = mu ** 80 * 20.0 + mu ** 16 * 1.6
    color = (color[0] + sun * 1.15, color[1] + sun * 1.0, color[2] + sun * 0.7)
    return color


def build_sky(width: int = 1024, height: int = 512):
    pixels = [sky_color((x + 0.5) / width, (y + 0.5) / height) for y in range(height) for x in range(width)]
    write_hdr(DATA / "tm2-sky.hdr", width, height, pixels)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    build_tower()
    build_walls()
    build_sky()
