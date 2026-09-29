"""Procedural low-poly grass clumps -> ASCII FBX 7.4 (Y up, metres, pivot at base centre)."""
import math, os, random
import numpy as np
from PIL import Image

OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\Grass"
os.makedirs(OUT, exist_ok=True)

ATLAS = "Grass_Atlas.png"
STRIPS = 8          # colour variants in the atlas, one per vertical strip
TEX = 256
MARGIN = 3 / TEX    # keep UVs away from strip edges (bilinear bleed)

# ---------------------------------------------------------------- atlas
def make_atlas():
    rng = np.random.default_rng(7)
    img = np.zeros((TEX, TEX, 3), np.float32)
    sw = TEX // STRIPS
    # (base, mid, tip) colours per strip, linear-ish sRGB 0..1
    palettes = [
        ((0.12, 0.24, 0.07), (0.28, 0.48, 0.14), (0.52, 0.66, 0.24)),
        ((0.10, 0.22, 0.08), (0.24, 0.44, 0.15), (0.44, 0.62, 0.22)),
        ((0.14, 0.26, 0.06), (0.32, 0.50, 0.12), (0.62, 0.68, 0.28)),
        ((0.09, 0.20, 0.08), (0.22, 0.40, 0.16), (0.40, 0.56, 0.24)),
        ((0.13, 0.25, 0.07), (0.30, 0.47, 0.13), (0.58, 0.62, 0.30)),
        ((0.11, 0.23, 0.09), (0.26, 0.46, 0.18), (0.46, 0.64, 0.28)),
        ((0.15, 0.25, 0.07), (0.34, 0.48, 0.14), (0.66, 0.64, 0.32)),
        ((0.10, 0.21, 0.07), (0.25, 0.42, 0.13), (0.48, 0.58, 0.22)),
    ]
    for s in range(STRIPS):
        b, m, t = (np.array(c) for c in palettes[s])
        for y in range(TEX):
            v = 1.0 - (y + 0.5) / TEX          # image row 0 = top = v 1
            col = b + (m - b) * (v / 0.55) if v < 0.55 else m + (t - m) * ((v - 0.55) / 0.45)
            img[y, s * sw:(s + 1) * sw] = col
        # faint vertical streaks along the blade (midrib feel)
        streak = 1.0 + 0.06 * rng.standard_normal(sw)
        streak[sw // 2 - 1: sw // 2 + 1] *= 1.08
        img[:, s * sw:(s + 1) * sw] *= streak[None, :, None]
    img *= 1.0 + 0.025 * rng.standard_normal((TEX, TEX, 1))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, ATLAS))

# ---------------------------------------------------------------- mesh building
class Mesh:
    def __init__(self):
        self.pos, self.nrm, self.uv, self.tris = [], [], [], []

    def vert(self, p, n, uv):
        self.pos.append(p); self.nrm.append(n); self.uv.append(uv)
        return len(self.pos) - 1

def norm(v):
    return v / (np.linalg.norm(v) + 1e-9)

UP = np.array([0.0, 1.0, 0.0])

def add_blade(mesh, base, h, width, lean_dir, lean, twist, strip, cut_top=None, rng=None):
    """One blade. rows: list of (t, width_factor). Tip row has width 0 -> triangle.
    Built double-sided: front and back faces with separate verts/normals."""
    face_dir = norm(np.array([lean_dir[0], 0.0, lean_dir[2]]))       # blade faces its lean direction
    side0 = np.cross(UP, face_dir)
    u0 = strip / STRIPS + MARGIN
    u1 = (strip + 1) / STRIPS - MARGIN
    uc = (u0 + u1) / 2

    if cut_top is None:
        rows = [(0.0, 1.0), (0.45, 0.85), (0.78, 0.55), (1.0, 0.0)]
        vscale = 1.0
    else:
        seg = cut_top["segments"]
        rows = [(0.0, 1.0), (0.5, 0.95), (1.0, 0.9)] if seg == 2 else [(0.0, 1.0), (1.0, 0.9)]
        vscale = cut_top["vscale"]

    def point(t):
        # quadratic lean gives a gentle curve; slight droop keeps length believable
        off = face_dir * (lean * h * t * t)
        return base + UP * (h * t * (1.0 - 0.18 * lean * t)) + off

    rings = []
    for i, (t, wf) in enumerate(rows):
        c = point(t)
        a = twist * t
        side = side0 * math.cos(a) + face_dir * math.sin(a)
        # tangent along the blade for the normal
        tan = norm(point(min(t + 0.05, 1.0)) - point(max(t - 0.05, 0.0)))
        fn = norm(np.cross(side, tan))
        hw = width * wf * 0.5
        if cut_top is not None and i == len(rows) - 1:
            # slanted sickle cut: one edge a bit higher
            s = cut_top["slant"]
            L, R = c - side * hw + UP * (-s), c + side * hw + UP * s
            rings.append((L, R, fn, t))
        elif wf == 0.0:
            rings.append((c, None, fn, t))
        else:
            rings.append((c - side * hw, c + side * hw, fn, t))

    for sign in (1.0, -1.0):
        ids = []
        for L, R, fn, t in rings:
            n = norm(fn * sign * 0.55 + UP * 0.45)                     # upward-biased normals: softer grass shading
            v = t * vscale
            if R is None:
                ids.append((mesh.vert(L, n, (uc, v)), None))
            else:
                ids.append((mesh.vert(L, n, (u0, v)), mesh.vert(R, n, (u1, v))))
        for (a0, a1), (b0, b1) in zip(ids[:-1], ids[1:]):
            if b1 is None:
                tri = [(a0, a1, b0)]
            else:
                tri = [(a0, a1, b1), (a0, b1, b0)]
            for t3 in tri:
                mesh.tris.append(t3 if sign > 0 else (t3[0], t3[2], t3[1]))

def clump(seed, n, base_r, h_range, w_range, lean_range, cut=None):
    rng = random.Random(seed)
    m = Mesh()
    for i in range(n):
        # denser towards the centre
        r = base_r * math.sqrt(rng.random()) ** 1.3
        a = rng.random() * math.tau
        base = np.array([math.cos(a) * r, 0.0, math.sin(a) * r])
        # lean outward from centre with some randomness
        out = a + rng.uniform(-0.7, 0.7)
        lean_dir = np.array([math.cos(out), 0.0, math.sin(out)])
        h = rng.uniform(*h_range)
        w = rng.uniform(*w_range)
        lean = rng.uniform(*lean_range) * (0.5 + 0.5 * r / base_r if base_r > 0 else 1)
        twist = rng.uniform(-0.6, 0.6)
        strip = rng.randrange(STRIPS)
        if cut:
            ch = rng.uniform(*cut["h"])
            add_blade(m, base, ch, w, lean_dir, lean * 0.15, twist * 0.2, strip,
                      cut_top={"segments": 1 if ch < 0.1 else 2,
                               "vscale": ch / h,          # keep the dark lower part of the gradient
                               "slant": rng.uniform(0.004, 0.012)})
        else:
            add_blade(m, base, h, w, lean_dir, lean, twist, strip)
    return m

# ---------------------------------------------------------------- FBX writer
def arr(vals, fmt="{:.6g}"):
    return ",".join(fmt.format(v) for v in vals)

def write_fbx(path, name, mesh):
    P = np.array(mesh.pos)
    verts = P.reshape(-1)
    poly, normals, uvs, uvidx = [], [], [], []
    for tri in mesh.tris:
        for k, vi in enumerate(tri):
            poly.append(vi if k < 2 else -vi - 1)
            normals.extend(mesh.nrm[vi])
            uvidx.append(vi)
    uvflat = [c for uv in mesh.uv for c in uv]
    L = []
    w = L.append
    w("; FBX 7.4.0 project file")
    w("FBXHeaderExtension:  {\n\tFBXHeaderVersion: 1003\n\tFBXVersion: 7400\n\tCreator: \"Overgrown grass generator\"\n}")
    w("GlobalSettings:  {\n\tVersion: 1000\n\tProperties70:  {")
    for k, v in [("UpAxis", 1), ("UpAxisSign", 1), ("FrontAxis", 2), ("FrontAxisSign", 1),
                 ("CoordAxis", 0), ("CoordAxisSign", 1), ("OriginalUpAxis", 1), ("OriginalUpAxisSign", 1)]:
        w(f"\t\tP: \"{k}\", \"int\", \"Integer\", \"\",{v}")
    w("\t\tP: \"UnitScaleFactor\", \"double\", \"Number\", \"\",100")
    w("\t\tP: \"OriginalUnitScaleFactor\", \"double\", \"Number\", \"\",100")
    w("\t}\n}")
    w("Definitions:  {\n\tVersion: 100\n\tCount: 6")
    for t in ["GlobalSettings", "Model", "Geometry", "Material", "Texture", "Video"]:
        w(f"\tObjectType: \"{t}\" {{\n\t\tCount: 1\n\t}}")
    w("}")
    w("Objects:  {")
    w(f"\tGeometry: 1000001, \"Geometry::{name}\", \"Mesh\" {{")
    w(f"\t\tVertices: *{len(verts)} {{\n\t\t\ta: {arr(verts)}\n\t\t}}")
    w(f"\t\tPolygonVertexIndex: *{len(poly)} {{\n\t\t\ta: {arr(poly, '{}')}\n\t\t}}")
    w("\t\tGeometryVersion: 124")
    w("\t\tLayerElementNormal: 0 {\n\t\t\tVersion: 101\n\t\t\tName: \"\"\n\t\t\tMappingInformationType: \"ByPolygonVertex\"\n\t\t\tReferenceInformationType: \"Direct\"")
    w(f"\t\t\tNormals: *{len(normals)} {{\n\t\t\t\ta: {arr(normals)}\n\t\t\t}}\n\t\t}}")
    w("\t\tLayerElementUV: 0 {\n\t\t\tVersion: 101\n\t\t\tName: \"UVMap\"\n\t\t\tMappingInformationType: \"ByPolygonVertex\"\n\t\t\tReferenceInformationType: \"IndexToDirect\"")
    w(f"\t\t\tUV: *{len(uvflat)} {{\n\t\t\t\ta: {arr(uvflat)}\n\t\t\t}}")
    w(f"\t\t\tUVIndex: *{len(uvidx)} {{\n\t\t\t\ta: {arr(uvidx, '{}')}\n\t\t\t}}\n\t\t}}")
    w("\t\tLayerElementMaterial: 0 {\n\t\t\tVersion: 101\n\t\t\tName: \"\"\n\t\t\tMappingInformationType: \"AllSame\"\n\t\t\tReferenceInformationType: \"IndexToDirect\"\n\t\t\tMaterials: *1 {\n\t\t\t\ta: 0\n\t\t\t}\n\t\t}")
    w("\t\tLayer: 0 {\n\t\t\tVersion: 100")
    for t in ["LayerElementNormal", "LayerElementMaterial", "LayerElementUV"]:
        w(f"\t\t\tLayerElement:  {{\n\t\t\t\tType: \"{t}\"\n\t\t\t\tTypedIndex: 0\n\t\t\t}}")
    w("\t\t}\n\t}")
    w(f"\tModel: 2000001, \"Model::{name}\", \"Mesh\" {{\n\t\tVersion: 232\n\t\tProperties70:  {{")
    w("\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",1")
    w("\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",0")
    w("\t\t\tP: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",0,0,0")
    w("\t\t\tP: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",0,0,0")
    w("\t\t\tP: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",1,1,1")
    w("\t\t}\n\t\tShading: T\n\t\tCulling: \"CullingOff\"\n\t}")
    w("\tMaterial: 3000001, \"Material::M_Grass\", \"\" {\n\t\tVersion: 102\n\t\tShadingModel: \"phong\"\n\t\tMultiLayer: 0\n\t\tProperties70:  {")
    for line in ["\"DiffuseColor\", \"Color\", \"\", \"A\",1,1,1",
                 "\"SpecularColor\", \"Color\", \"\", \"A\",0,0,0",
                 "\"SpecularFactor\", \"Number\", \"\", \"A\",0",
                 "\"ShininessExponent\", \"Number\", \"\", \"A\",1",
                 "\"ReflectionFactor\", \"Number\", \"\", \"A\",0"]:
        w(f"\t\t\tP: {line}")
    w("\t\t}\n\t}")
    w(f"\tVideo: 5000001, \"Video::Grass_Atlas\", \"Clip\" {{\n\t\tType: \"Clip\"\n\t\tProperties70:  {{\n\t\t\tP: \"Path\", \"KString\", \"XRefUrl\", \"\", \"{ATLAS}\"\n\t\t}}\n\t\tUseMipMap: 0\n\t\tFilename: \"{ATLAS}\"\n\t\tRelativeFilename: \"{ATLAS}\"\n\t}}")
    w(f"\tTexture: 4000001, \"Texture::Grass_Atlas\", \"\" {{\n\t\tType: \"TextureVideoClip\"\n\t\tVersion: 202\n\t\tTextureName: \"Texture::Grass_Atlas\"\n\t\tMedia: \"Video::Grass_Atlas\"\n\t\tFileName: \"{ATLAS}\"\n\t\tRelativeFilename: \"{ATLAS}\"\n\t\tModelUVTranslation: 0,0\n\t\tModelUVScaling: 1,1\n\t\tTexture_Alpha_Source: \"None\"\n\t\tCropping: 0,0,0,0\n\t}}")
    w("}")
    w("Connections:  {")
    w("\tC: \"OO\",2000001,0")
    w("\tC: \"OO\",1000001,2000001")
    w("\tC: \"OO\",3000001,2000001")
    w("\tC: \"OP\",4000001,3000001, \"DiffuseColor\"")
    w("\tC: \"OO\",5000001,4000001")
    w("}")
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return P

# ---------------------------------------------------------------- variants
VARIANTS = {
    #               seed  n   base_r  height        width           lean
    "Grass_Tall_01": dict(seed=11, n=32, base_r=0.12, h_range=(0.50, 0.80), w_range=(0.026, 0.038), lean_range=(0.20, 0.45)),
    "Grass_Tall_02": dict(seed=23, n=36, base_r=0.15, h_range=(0.45, 0.72), w_range=(0.026, 0.040), lean_range=(0.30, 0.52)),
    "Grass_Tall_03": dict(seed=37, n=22, base_r=0.12, h_range=(0.62, 0.92), w_range=(0.024, 0.034), lean_range=(0.15, 0.35)),
    # same seed/layout as Tall_01 -> reads as the stubble left after cutting it
    "Grass_Cut":     dict(seed=11, n=32, base_r=0.12, h_range=(0.50, 0.80), w_range=(0.026, 0.038), lean_range=(0.20, 0.45),
                          cut={"h": (0.08, 0.14)}),
}

if __name__ == "__main__":
    make_atlas()
    for name, cfg in VARIANTS.items():
        m = clump(**cfg)
        P = np.array(m.pos)
        mn, mx = P.min(0), P.max(0)
        print(f"{name}: tris={len(m.tris)} verts={len(m.pos)} "
              f"height={mx[1]-mn[1]:.2f} width_x={mx[0]-mn[0]:.2f} width_z={mx[2]-mn[2]:.2f} minY={mn[1]:.3f}")
        np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".npz"),
                 pos=P, tris=np.array(m.tris), uv=np.array(m.uv), nrm=np.array(m.nrm))
