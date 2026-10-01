"""Paints Ground_Stylized.png: seamless stylized ground (1024x1024, Base Color, no alpha).
Run: python paint_ground.py   (needs numpy, scipy, Pillow)

All noise is built in the frequency domain (periodic by construction) and brush dabs wrap around the
edges, so the result tiles seamlessly. Only broad / mid frequencies: no fine photographic grain."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = r"E:\UnityProject\Overgrown\Assets\Art\Textures\Ground"
N = 1024
rng = np.random.default_rng(60)

def periodic_noise(sigma_px):
    """Gaussian-filtered white noise via FFT -> tileable, normalised to 0..1."""
    white = rng.standard_normal((N, N))
    fx = np.fft.fftfreq(N)[:, None]
    fy = np.fft.fftfreq(N)[None, :]
    k = np.exp(-2 * (np.pi * sigma_px) ** 2 * (fx ** 2 + fy ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * k))
    return (n - n.min()) / (n.max() - n.min())

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

low = periodic_noise(130)
mid = periodic_noise(42)
small = periodic_noise(12)
dry_n = periodic_noise(90)

# 0 = bare earth .. 1 = lush grass
g = 0.55 * low + 0.3 * mid + 0.15 * small
g = (g - g.min()) / (g.max() - g.min())
g = 0.28 + 0.72 * smoothstep(0.12, 0.9, g)      # mostly grass tones; bare earth only in the lowest spots
# painterly: soft posterisation into broad tonal bands
levels = 7
q = np.round(g * (levels - 1)) / (levels - 1)
g = np.clip(0.6 * q + 0.4 * g, 0.0, 1.0)         # clip: float error > 1 would fall outside the ramp

# palette (sRGB, muted, warm)
EARTH = np.array([128, 110, 80], float)
EARTH_WARM = np.array([134, 118, 82], float)
OLIVE = np.array([118, 128, 70], float)
GREEN = np.array([100, 128, 66], float)
GREEN_LIGHT = np.array([122, 146, 78], float)
BEIGE = np.array([172, 158, 112], float)

def ramp(t):
    stops = [(0.0, EARTH), (0.3, EARTH_WARM), (0.5, OLIVE), (0.75, GREEN), (1.0, GREEN_LIGHT)]
    out = np.zeros(t.shape + (3,))
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        m = (t >= t0) & (t <= t1 + 1e-9)
        f = ((t - t0) / (t1 - t0))[m][:, None]
        out[m] = c0 + (c1 - c0) * f
    return out

img = ramp(g)
# occasional dry beige areas, mostly where the grass is thinner
dry = smoothstep(0.68, 0.85, dry_n) * (1 - 0.5 * g)
img = img + (BEIGE - img) * (dry[..., None] * 0.5)
# gentle warm/cool drift so large areas never look flat
img *= (0.96 + 0.08 * mid)[..., None]

# painterly brush dabs (soft, low contrast, wrapped across the edges)
base = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")
# transparent background carries the base colours: blurring straight alpha over (0,0,0,0) would leave dark rims
dab = base.convert("RGBA")
dab.putalpha(0)
d = ImageDraw.Draw(dab)
for _ in range(2600):
    x, y = rng.uniform(0, N, 2)
    r = rng.uniform(5, 18)
    sx, sy = r * rng.uniform(1.0, 2.2), r
    c = np.array(base.getpixel((int(x) % N, int(y) % N)), float)
    c = c * rng.uniform(0.94, 1.06) + rng.uniform(-6, 6, 3)
    col = tuple(int(v) for v in c.clip(0, 255)) + (int(rng.uniform(60, 120)),)
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            cx, cy = x + ox, y + oy
            if -40 < cx < N + 40 and -40 < cy < N + 40:
                d.ellipse([cx - sx, cy - sy, cx + sx, cy + sy], fill=col)
# wrap-safe blur: blur a 3x3 tile and crop the centre
def wrap_blur(im, radius):
    big = Image.new(im.mode, (N * 3, N * 3))
    for i in range(3):
        for j in range(3):
            big.paste(im, (i * N, j * N))
    return big.filter(ImageFilter.GaussianBlur(radius)).crop((N, N, 2 * N, 2 * N))
dab = wrap_blur(dab, 2.5)
out = base.convert("RGBA")
out.alpha_composite(dab)
out = wrap_blur(out.convert("RGB"), 0.8)

os.makedirs(OUT_DIR, exist_ok=True)
out.save(os.path.join(OUT_DIR, "Ground_Stylized.png"), optimize=True)

# 3x3 tiling preview (checks seams + repetition), downsized
tile = Image.new("RGB", (N * 3, N * 3))
for i in range(3):
    for j in range(3):
        tile.paste(out, (i * N, j * N))
tile.resize((1200, 1200), Image.LANCZOS).save(os.path.join(HERE, "preview_tiled_3x3.png"))
print("saved", os.path.join(OUT_DIR, "Ground_Stylized.png"))
