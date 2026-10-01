"""Paints Grass_Stylized_Atlas.png: stylized hand-painted-look grass clusters on a transparent 1024x1024 atlas.
Run: python paint_grass_atlas.py   (needs Pillow + numpy)

Layout (pixels, origin top-left; each cluster's roots sit on the bottom edge of its cell):
  row 1  y   0..512 : Tall_A | Tall_Thin | Tall_Seed | Tall_Lean      (256 x 512 each)
  row 2  y 512..768 : Wide_Dense | Wide_Soft                          (512 x 256 each)
  row 3  y 768..1024: Short_A | Short_B | Short_Sparse | Short_Dry     (256 x 256 each)
UV rects (0..1, Unity convention: v=0 at the bottom) are written to Grass_Stylized_Atlas_UV.json."""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = r"E:\UnityProject\Overgrown\Assets\Art\Textures\Grass"
SIZE = 1024
SS = 4                                   # supersampling
rng = random.Random(1024)

# ---------------------------------------------------------------- palette (sRGB), warm & muted
ROOT_DRY = (176, 162, 108)
FAMILIES = {
    #            root          mid             tip
    "green":  ((104, 134, 60), (98, 158, 64),  (156, 192, 88)),
    "green2": ((96, 128, 58),  (88, 146, 60),  (144, 182, 80)),
    "olive":  ((118, 132, 62), (122, 148, 62), (170, 180, 90)),
    "yellow": ((130, 144, 68), (152, 172, 76), (196, 200, 110)),
    "dry":    ((176, 162, 108), (170, 160, 96), (198, 186, 124)),
}

def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def blade_color(fam, t, depth, dry=0.6, dry_len=0.18):
    root, mid, tip = FAMILIES[fam]
    c = lerp(root, mid, smooth(t / 0.55)) if t < 0.55 else lerp(mid, tip, smooth((t - 0.55) / 0.45))
    # soft dry-beige wash near the roots, amount and length vary per blade
    c = lerp(c, ROOT_DRY, dry * (1 - smooth(t / dry_len)))
    k = 0.9 + 0.1 * depth                         # back blades only slightly darker
    return tuple(max(0, min(255, int(v * k))) for v in c)

def draw_blade(draw, ox, oy, base_x, height, width, lean, curve, fam, depth):
    """Tapered curved blade, quadratic bezier centreline; one half slightly darker (soft stylized shading).
    The control point sits low, so the blade stays upright at the root and bends towards the tip."""
    N = 28
    dry = rng.uniform(0.2, 0.75)
    dry_len = rng.uniform(0.1, 0.24)
    p0 = (base_x, 0.0)
    p2 = (base_x + lean, height)
    p1 = (base_x + lean * 0.1 + curve * 0.5, height * 0.62)
    def bez(t):
        a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t * t
        return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])
    pts = [bez(i / N) for i in range(N + 1)]
    L, C, R = [], [], []
    for i, (x, y) in enumerate(pts):
        t = i / N
        nx, ny = pts[min(i + 1, N)][0] - pts[max(i - 1, 0)][0], pts[min(i + 1, N)][1] - pts[max(i - 1, 0)][1]
        ln = math.hypot(nx, ny) or 1
        px, py = -ny / ln, nx / ln
        w = width * 0.5 * (1 - t) ** 0.85 * (1 + 0.15 * math.sin(t * math.pi))
        L.append((x + px * w, y + py * w)); C.append((x, y)); R.append((x - px * w, y - py * w))
    def to_img(p):
        return ((ox + p[0]) * SS, (oy - p[1]) * SS)
    for i in range(N):
        t = (i + 0.5) / N
        col = blade_color(fam, t, depth, dry, dry_len)
        dark = tuple(int(v * 0.91) for v in col)
        draw.polygon([to_img(L[i]), to_img(L[i + 1]), to_img(C[i + 1]), to_img(C[i])], fill=dark + (255,))
        draw.polygon([to_img(C[i]), to_img(C[i + 1]), to_img(R[i + 1]), to_img(R[i])], fill=col + (255,))

def seed_head(draw, ox, oy, x, y, fam):
    """Small stylized seed head: stacked ovals along a stem tip."""
    col = (196, 180, 112)
    for k in range(5):
        cx, cy = (ox + x + (k % 2) * 2 - 1) * SS, (oy - y - k * 7) * SS
        r = (4.2 - k * 0.5) * SS
        draw.ellipse([cx - r * 0.6, cy - r, cx + r * 0.6, cy + r], fill=col + (255,))

def cluster(draw, cell, kind):
    x0, y0, w, h = cell
    ox, oy = x0, y0 + h - 3                      # roots 3px above the cell's bottom edge
    pad = 10
    usable_w = w - 2 * pad
    spec = {
        #             count  height(frac)   width px     lean px     spread  families (weights)
        "Tall_A":    (22, (0.62, 0.96), (13, 19), (-40, 40), 0.32, ["green"] * 3 + ["olive"] * 2 + ["yellow"]),
        "Tall_Thin": (26, (0.55, 0.95), (8, 12),  (-35, 35), 0.28, ["green2"] * 3 + ["olive"] + ["yellow"]),
        "Tall_Seed": (18, (0.55, 0.85), (12, 17), (-35, 35), 0.32, ["olive"] * 2 + ["green"] * 2 + ["yellow"]),
        "Tall_Lean": (20, (0.6, 0.92),  (12, 17), (10, 70),  0.3,  ["green"] * 2 + ["olive"] * 2 + ["yellow"]),
        "Wide_Dense":(46, (0.55, 0.95), (14, 22), (-60, 60), 0.85, ["green"] * 3 + ["green2"] * 2 + ["olive"] * 2 + ["yellow"]),
        "Wide_Soft": (32, (0.45, 0.9),  (14, 20), (-70, 70), 0.85, ["olive"] * 3 + ["green"] * 2 + ["yellow"] * 2),
        "Short_A":   (18, (0.5, 0.92),  (14, 20), (-30, 30), 0.45, ["green"] * 3 + ["olive"]),
        "Short_B":   (16, (0.45, 0.85), (16, 22), (-40, 40), 0.5, ["green2"] * 2 + ["olive"] + ["yellow"]),
        "Short_Sparse": (9, (0.5, 0.95), (12, 18), (-45, 45), 0.5, ["green"] * 2 + ["olive"] + ["yellow"]),
        "Short_Dry": (15, (0.45, 0.9),  (12, 18), (-40, 40), 0.45, ["dry"] * 3 + ["olive"] * 2 + ["yellow"]),
    }[kind]
    count, (hmin, hmax), (wmin, wmax), (lmin, lmax), spread, fams = spec
    blades = []
    for i in range(count):
        # roots bunched toward the centre, tallest blades near the middle
        u = (rng.random() - 0.5) * spread + rng.gauss(0, 0.06)
        bx = pad + usable_w * min(0.97, max(0.03, 0.5 + u))
        centrality = 1 - min(1, abs(u) * 1.6)
        hh = (h - 14) * rng.uniform(hmin, hmax) * (0.75 + 0.25 * centrality)
        lean = rng.uniform(lmin, lmax) + u * 110 * (hh / (h - 14))      # fountain: outer blades fan out
        lean = max(-bx + pad + 4, min(w - pad - 4 - bx, lean))        # keep tips inside the cell
        curve = rng.uniform(-14, 14) + lean * 0.15
        depth = rng.random()
        blades.append((depth, bx, hh, rng.uniform(wmin, wmax), lean, curve, rng.choice(fams)))
    blades.sort(key=lambda b: -b[0])                                 # far (dark) first
    for depth, bx, hh, ww, lean, curve, fam in blades:
        draw_blade(draw, ox, oy, bx, hh, ww, lean, curve, fam, 1 - depth)
    if kind == "Tall_Seed":
        for depth, bx, hh, ww, lean, curve, fam in blades[-5:]:
            seed_head(draw, ox, oy, bx + lean, hh - 4, fam)

CELLS = {}
for i, name in enumerate(["Tall_A", "Tall_Thin", "Tall_Seed", "Tall_Lean"]):
    CELLS[name] = (i * 256, 0, 256, 512)
for i, name in enumerate(["Wide_Dense", "Wide_Soft"]):
    CELLS[name] = (i * 512, 512, 512, 256)
for i, name in enumerate(["Short_A", "Short_B", "Short_Sparse", "Short_Dry"]):
    CELLS[name] = (i * 256, 768, 256, 256)

big = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
draw = ImageDraw.Draw(big)
for name, cell in CELLS.items():
    cluster(draw, cell, name)

# downsample with premultiplied alpha (no dark fringes)
img = big.convert("RGBa").resize((SIZE, SIZE), Image.LANCZOS).convert("RGBA")
arr = np.asarray(img).astype(np.float32)
# colour bleed into transparent texels so mip-mapped / clipped edges stay green, not black
from scipy import ndimage
solid = arr[..., 3] > 127
_, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
arr[..., :3] = np.where((arr[..., 3] < 128)[..., None], arr[iy, ix, :3], arr[..., :3])
out = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
os.makedirs(OUT_DIR, exist_ok=True)
out.save(os.path.join(OUT_DIR, "Grass_Stylized_Atlas.png"), optimize=True)

uv = {name: {"u": x / SIZE, "v": 1 - (y + h) / SIZE, "w": w / SIZE, "h": h / SIZE} for name, (x, y, w, h) in CELLS.items()}
json.dump(uv, open(os.path.join(HERE, "Grass_Stylized_Atlas_UV.json"), "w"), indent=2)

# preview on a neutral background with cell outlines
prev = Image.new("RGBA", (SIZE, SIZE), (104, 118, 132, 255))
prev.alpha_composite(out)
d = ImageDraw.Draw(prev)
for name, (x, y, w, h) in CELLS.items():
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(255, 255, 255, 70))
    d.text((x + 6, y + 4), name, fill=(255, 255, 255, 200))
prev.convert("RGB").save(os.path.join(HERE, "preview_atlas.png"))
print("saved", os.path.join(OUT_DIR, "Grass_Stylized_Atlas.png"))
