"""HandUpgrade_Stand: three separate garden tool racks, one child mesh per upgrade.
Run: blender -b --factory-startup -P handupgrade_build.py
  BundlesSection - grab more per action: wide hand rake, leaf-grabber paddles, garden tongs, scoop
  SpeedSection   - work faster: cloth -> garden -> leather gauntlet gloves, elbow pad, wrist guards
  RadiusSection  - reach further: small hand rake -> long hook -> fan rake
Each child's origin sits at its own base centre. Blender is Z-up; FBX export bakes to Y-up (Unity rot 0, scale 1).
Tools hang on the front (-Y) of each rack."""
import os, math, random
import bpy, bmesh
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\HandUpgrade"
NAME = "HandUpgrade_Stand"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(21)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette atlas (sRGB)
PALETTE = {
    "wood":         (150, 104, 64),
    "wood2":        (134, 94, 58),
    "wood_old":     (128, 114, 98),
    "wood_dark":    (84, 58, 38),
    "handle":       (196, 154, 98),
    "metal":        (104, 108, 112),
    "metal_dark":   (62, 64, 68),
    "rust":         (122, 76, 46),
    "sign":         (208, 192, 154),
    "paint_dark":   (62, 48, 36),
    "green":        (78, 140, 52),
    "green_dark":   (52, 96, 38),
    "orange":       (222, 132, 42),
    "orange_dark":  (160, 86, 30),
    "teal":         (58, 132, 142),
    "teal_dark":    (38, 90, 100),
    "glove_cloth":  (222, 208, 172),
    "glove_cloth2": (186, 170, 134),
    "glove_green":  (104, 152, 72),
    "glove_leather":(146, 94, 54),
    "cuff_red":     (174, 62, 46),
    "rubber":       (54, 58, 52),
    "pad":          (70, 84, 96),
    "strap":        (96, 70, 46),
    "blade":        (112, 158, 48),
    "grass":        (92, 124, 40),
}
PAL_GRID, PAL_CELL = 8, 8
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)
MATS = {k: bpy.data.materials.new("tmp_" + k) for k in KEYS}
parts = []

def jitter(a):
    return rng.uniform(-a, a)

def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for k in mats:
        me.materials.append(MATS[k])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def xform(bm, center, rot=(0, 0, 0), scale=(1, 1, 1)):
    M = Matrix.Translation(Vector(center)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)

def box(name, center, size, mat, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect='EDGES', profile=0.5)
    xform(bm, center, rot)
    return new_obj(name, bm, [mat])

def stick(name, a, b, thick, mat, bevel=0.0, depth=None):
    """Box from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = d.to_track_quat('Z', 'Y').to_euler()
    return box(name, (a + b) / 2, (thick, depth or thick, d.length + thick * 0.6), mat, rot=rot, bevel=bevel)

def path(name, pts, thick, mat):
    for k in range(len(pts) - 1):
        stick(f"{name}{k}", pts[k], pts[k + 1], thick, mat)

def lathe(name, profile, n, mat_fn, center, rot=(0, 0, 0), scale=(1, 1, 1), noise=0.0,
          cap_bottom=True, cap_top=True, phase=0.0, cap_mats=None):
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))]); continue
        ring = []
        for i in range(n):
            a = phase + math.tau * i / n
            rr = r * (1 + jitter(noise))
            ring.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z)))
        rings.append(ring)
    used = []
    def mi(k):
        if k not in used:
            used.append(k)
        return used.index(k)
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(n):
            i2 = (i + 1) % n
            if len(a) == 1:
                f = bm.faces.new((a[0], b[i2], b[i]))
            elif len(b) == 1:
                f = bm.faces.new((a[i], a[i2], b[0]))
            else:
                f = bm.faces.new((a[i], a[i2], b[i2], b[i]))
            f.material_index = mi(mat_fn(j, i))
    cm = cap_mats or (mat_fn(0, 0), mat_fn(len(rings) - 2, 0))
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0]))).material_index = mi(cm[0])
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1]).material_index = mi(cm[1])
    xform(bm, center, rot, scale)
    return new_obj(name, bm, used)

def decal(name, pts2d, y, mat, x0=0.0, z0=0.0):
    """Flat painted polygon in the XZ plane facing -Y."""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x0 + x, y, z0 + z)) for x, z in pts2d])
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    return new_obj(name, bm, [mat])

def ring_decal(name, r_in, r_out, n, y, mat, x0, z0):
    bm = bmesh.new()
    inner = [bm.verts.new((x0 + math.cos(math.tau * i / n) * r_in, y, z0 + math.sin(math.tau * i / n) * r_in)) for i in range(n)]
    outer = [bm.verts.new((x0 + math.cos(math.tau * i / n) * r_out, y, z0 + math.sin(math.tau * i / n) * r_out)) for i in range(n)]
    for i in range(n):
        f = bm.faces.new((inner[i], outer[i], outer[(i + 1) % n], inner[(i + 1) % n]))
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    return new_obj(name, bm, [mat])

def tuft(name, cx, cy, count, radius=0.1, h=(0.12, 0.26)):
    bm = bmesh.new()
    for _ in range(count):
        ang = rng.uniform(0, math.tau)
        r = radius * math.sqrt(rng.random())
        base = Vector((cx + math.cos(ang) * r, cy + math.sin(ang) * r, 0.0))
        hh = rng.uniform(*h)
        lean = Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(0.03, 0.09)
        side = Vector((-math.sin(ang + 1.1), math.cos(ang + 1.1), 0)) * rng.uniform(0.012, 0.02)
        mid = base + Vector((0, 0, hh * 0.55)) + lean * 0.35
        tip = base + Vector((0, 0, hh)) + lean
        for flip in (False, True):
            v = [bm.verts.new(p) for p in (base - side, base + side, mid + side * 0.6, mid - side * 0.6, tip)]
            for f in ((v[0], v[1], v[2], v[3]), (v[3], v[2], v[4])):
                bm.faces.new(tuple(reversed(f)) if flip else f)
    return new_obj(name, bm, ["blade"])

# ---------------------------------------------------------------- rack frame (local coords, origin = base centre)
SEC_W, GAP = 0.70, 0.08
PX = 0.31                 # post x
POST = 0.07
PANEL_Y = 0.10            # back panel centre
PANEL_T = 0.025
FRONT = PANEL_Y - PANEL_T / 2       # front face of the panel; tools hang in front of it
POST_H = 1.62
SHELF_Z = 0.42

def peg(name, x, z, length=0.07):
    stick(name, (x, FRONT, z), (x, FRONT - length, z + 0.012), 0.018, "wood_dark")

def frame(accent, accent_dark):
    for sx in (-1, 1):
        box(f"post{sx}", (sx * PX, PANEL_Y + 0.03, POST_H / 2), (POST, POST, POST_H), "wood_dark",
            rot=(jitter(0.01), jitter(0.01), 0), bevel=0.01)
        box(f"foot{sx}", (sx * PX, -0.04, 0.03), (0.08, 0.56, 0.06), "wood_dark", bevel=0.01)
        stick(f"brace{sx}", (sx * PX, -0.24, 0.05), (sx * PX, PANEL_Y + 0.01, 0.62), 0.045, "wood2", bevel=0.006)
    # vertical panel boards (a couple weathered)
    n = 5
    bw = (2 * PX - POST) / n
    for k in range(n):
        x = -PX + POST / 2 + bw * (k + 0.5)
        top = 1.46 + jitter(0.02)
        box(f"board{k}", (x, PANEL_Y + jitter(0.003), (0.34 + top) / 2), (bw - 0.008, PANEL_T, top - 0.34),
            rng.choice(["wood", "wood", "wood2", "wood_old"]))
    for z in (0.40, 1.40):
        box(f"crossrail{z}", (0, PANEL_Y + 0.025, z), (2 * PX, 0.03, 0.06), "wood_dark")
    # shelf with front lip
    box("shelf", (0, -0.06, SHELF_Z), (2 * PX + 0.02, 0.30, 0.035), "wood2", bevel=0.006)
    box("shelf_lip", (0, -0.205, SHELF_Z + 0.03), (2 * PX + 0.02, 0.02, 0.05), accent_dark)
    # sign + little roof
    box("sign", (0, FRONT - 0.02, 1.64), (0.60, 0.035, 0.24), "sign", rot=(0, jitter(0.02), 0), bevel=0.012)
    box("sign_band", (0, FRONT - 0.02, 1.515), (0.60, 0.04, 0.03), accent)
    for sx in (-1, 1):
        # slopes down and outward; stays inside the section footprint (|x| < SEC_W / 2)
        box(f"roof{sx}", (sx * 0.175, 0.0, 1.80), (0.37, 0.44, 0.03), accent_dark,
            rot=(0, sx * math.radians(18), 0), bevel=0.008)
    box("ridge", (0, 0.0, 1.865), (0.06, 0.46, 0.04), "wood_dark", bevel=0.006)
    tuft("tuft_l", -PX + 0.03, -0.14, 6, radius=0.05)
    tuft("tuft_r", PX - 0.03, 0.02, 5, radius=0.05, h=(0.1, 0.2))

SIGN_FACE = FRONT - 0.02 - 0.035 / 2 - 0.003
SIGN_Z = 1.64

# ---------------------------------------------------------------- tools
def hand_rake(tag, cx, ztop, handle_len, width, tines, tine_len, head_mat="metal", grip="handle"):
    """Hanging rake: handle up, head bar, tines down curling forward."""
    zhead = ztop - handle_len
    stick(f"{tag}_handle", (cx, FRONT - 0.05, ztop), (cx, FRONT - 0.05, zhead), 0.03, grip, bevel=0.006)
    box(f"{tag}_ferrule", (cx, FRONT - 0.05, zhead + 0.02), (0.038, 0.038, 0.04), "metal_dark")
    box(f"{tag}_head", (cx, FRONT - 0.05, zhead - 0.005), (width, 0.02, 0.025), head_mat)
    for k in range(tines):
        x = cx - width / 2 + 0.01 + (width - 0.02) * k / max(1, tines - 1)
        a = (x, FRONT - 0.05, zhead - 0.01)
        b = (x, FRONT - 0.055, zhead - tine_len * 0.75)
        c = (x, FRONT - 0.085, zhead - tine_len)
        stick(f"{tag}_tine{k}a", a, b, 0.012, head_mat)
        stick(f"{tag}_tine{k}b", b, c, 0.012, head_mat)
    peg(f"{tag}_peg", cx, ztop - 0.03)

def fan_rake(tag, cx, ztop, handle_len, fan_len, tines, spread):
    zhub = ztop - handle_len
    y = FRONT - 0.05
    stick(f"{tag}_handle", (cx, y, ztop), (cx, y, zhub), 0.032, "handle", bevel=0.006)
    box(f"{tag}_hub", (cx, y, zhub), (0.05, 0.03, 0.06), "teal_dark")
    ends = []
    for k in range(tines):
        a = -spread / 2 + spread * k / (tines - 1)
        end = (cx + math.sin(a) * fan_len, y - 0.01, zhub - math.cos(a) * fan_len)
        tip = (end[0] + math.sin(a) * 0.02, y - 0.05, end[2] - math.cos(a) * 0.03)
        stick(f"{tag}_tine{k}", (cx, y, zhub - 0.02), end, 0.012, "metal")
        stick(f"{tag}_tip{k}", end, tip, 0.012, "metal")
        ends.append(a)
    bar = [(cx + math.sin(a) * fan_len * 0.55, y - 0.012, zhub - math.cos(a) * fan_len * 0.55)
           for a in [-spread / 2 + spread * k / 6 for k in range(7)]]
    path(f"{tag}_bar", bar, 0.014, "teal")
    peg(f"{tag}_peg", cx, ztop - 0.03)

def long_hook(tag, cx, zpeg, handle_len):
    """Hook hangs over a peg by its curved metal end; handle points down."""
    y = FRONT - 0.07
    r = 0.075
    arc = [(cx + r - r * math.cos(t), y, zpeg + 0.01 + r * math.sin(t)) for t in [math.pi * k / 7 for k in range(8)]]
    # arc goes from handle top (cx) over the peg to the tip at cx + 2r
    path(f"{tag}_arc", arc, 0.016, "metal")
    stick(f"{tag}_point", arc[-1], (arc[-1][0] + 0.005, y, arc[-1][2] - 0.07), 0.016, "metal")
    stick(f"{tag}_handle", (cx, y, zpeg + 0.01), (cx, y, zpeg - handle_len), 0.03, "handle", bevel=0.006)
    box(f"{tag}_grip", (cx, y, zpeg - handle_len + 0.07), (0.04, 0.04, 0.13), "teal", bevel=0.008)
    peg(f"{tag}_peg", cx + r, zpeg)

def tongs(tag, cx, zc):
    y = FRONT - 0.05
    for s in (-1, 1):
        a = (cx - s * 0.05, y - 0.005 * s, zc + 0.20)
        b = (cx + s * 0.045, y - 0.005 * s, zc - 0.17)
        stick(f"{tag}_arm{s}", a, b, 0.018, "metal", depth=0.012)
        box(f"{tag}_grip{s}", (a[0], a[1], a[2] - 0.035), (0.03, 0.03, 0.09), "green", rot=(0, s * 0.25, 0), bevel=0.006)
        box(f"{tag}_claw{s}", (b[0] + s * 0.018, b[1], b[2] - 0.035), (0.06, 0.015, 0.07), "green_dark", rot=(0, -s * 0.2, 0))
    lathe(f"{tag}_bolt", [(0.0, -0.02), (0.018, -0.02), (0.018, 0.02), (0.0, 0.02)], 8,
          lambda j, i: "metal_dark", (cx, y, zc + 0.015), rot=(math.pi / 2, 0, 0))
    peg(f"{tag}_peg", cx - 0.05, zc + 0.23)

def grabber_paddle(tag, cx, ztop, mirror):
    """Leaf-grabber 'big hand': wide paddle with finger tines, hanging by a strap."""
    y = FRONT - 0.04
    box(f"{tag}_palm", (cx, y, ztop - 0.13), (0.15, 0.018, 0.17), "green", rot=(0, mirror * 0.08, 0), bevel=0.01)
    for k in range(4):
        x = cx - 0.055 + k * 0.037
        box(f"{tag}_finger{k}", (x + mirror * 0.01, y - 0.004, ztop - 0.27), (0.024, 0.016, 0.1), "green_dark",
            rot=(0, mirror * 0.08, 0))
    box(f"{tag}_grip", (cx, y - 0.02, ztop - 0.11), (0.1, 0.022, 0.03), "handle", bevel=0.006)
    path(f"{tag}_strap", [(cx - 0.03, y, ztop - 0.05), (cx, y - 0.01, ztop + 0.01), (cx + 0.03, y, ztop - 0.05)], 0.01, "strap")
    peg(f"{tag}_peg", cx, ztop - 0.005)

def scoop(tag, cx, cy):
    prof = [(0.09, 0.0), (0.12, 0.09), (0.11, 0.09), (0.08, 0.012)]
    lathe(f"{tag}_body", prof, 4, lambda j, i: "metal" if j == 0 else "metal_dark", (cx, cy, SHELF_Z + 0.018),
          rot=(0, 0, 0.2), scale=(1.2, 1.0, 1.0), phase=math.pi / 4, cap_mats=("metal_dark", "metal_dark"))
    stick(f"{tag}_handle", (cx + 0.12, cy + 0.02, SHELF_Z + 0.07), (cx + 0.25, cy + 0.06, SHELF_Z + 0.1), 0.03, "handle", bevel=0.006)
    # a heap of grass in the scoop
    bm = bmesh.new()
    for _ in range(7):
        ang = rng.uniform(0, math.tau); r = rng.uniform(0, 0.06)
        base = Vector((cx + math.cos(ang) * r, cy + math.sin(ang) * r, SHELF_Z + 0.04))
        hh = rng.uniform(0.08, 0.14)
        side = Vector((-math.sin(ang), math.cos(ang), 0)) * 0.015
        tip = base + Vector((math.cos(ang) * 0.05, math.sin(ang) * 0.05, hh))
        for flip in (False, True):
            v = [bm.verts.new(p) for p in (base - side, base + side, tip)]
            bm.faces.new(tuple(reversed(v)) if flip else v)
    new_obj(f"{tag}_heap", bm, ["blade"])

def glove(tag, cx, ztop, main, cuff, tier):
    """Glove hanging by its cuff, fingers down, facing -Y."""
    y = FRONT - 0.045
    s = 1.12
    cuff_h = (0.07 if tier < 3 else 0.12) * s
    zc = ztop - cuff_h / 2
    box(f"{tag}_cuff", (cx, y, zc), (0.12 * s, 0.04 * s, cuff_h), cuff, bevel=0.01)
    zp = ztop - cuff_h - 0.055 * s
    box(f"{tag}_palm", (cx, y, zp), (0.105 * s, 0.034 * s, 0.11 * s), main, bevel=0.012)
    lens = (0.06, 0.075, 0.08, 0.07)
    for k in range(4):
        x = cx + (-0.039 + k * 0.026) * s
        L = lens[k] * s
        box(f"{tag}_f{k}", (x, y, zp - 0.055 * s - L / 2 + 0.006), (0.023 * s, 0.028 * s, L), main,
            rot=(0, (k - 1.5) * 0.06, 0), bevel=0.007)
    box(f"{tag}_thumb", (cx + 0.066 * s, y, zp + 0.005), (0.024 * s, 0.028 * s, 0.065 * s), main,
        rot=(0, math.radians(-38), 0), bevel=0.007)
    fy = y - 0.017 * s - 0.004
    if tier == 2:        # rubber grip dots
        for k in range(3):
            for m in range(2):
                decal(f"{tag}_dot{k}{m}", [(-0.01, -0.01), (0.01, -0.01), (0.01, 0.01), (-0.01, 0.01)], fy, "rubber",
                      x0=cx + (k - 1) * 0.035, z0=zp + (m - 0.5) * 0.05)
    if tier == 3:        # knuckle guard + stitch band
        box(f"{tag}_guard", (cx, y - 0.02, zp - 0.045 * s), (0.11 * s, 0.02, 0.03 * s), "rubber", bevel=0.006)
        decal(f"{tag}_band", [(-0.06, -0.008), (0.06, -0.008), (0.06, 0.008), (-0.06, 0.008)], fy - 0.001, cuff,
              x0=cx, z0=zp + 0.03)
    peg(f"{tag}_peg", cx, ztop - 0.02)

# ---------------------------------------------------------------- sections
sections = {}

def finish(name, x_offset):
    global parts
    objs = parts
    parts = []
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = name
    ob.select_set(False)
    ob.location = (x_offset, 0, 0)
    sections[name] = ob

# 1) Bundles: grab more per action (green)
frame("green", "green_dark")
hand_rake("wide_rake", -0.17, 1.36, 0.26, 0.26, 7, 0.1)
grabber_paddle("paddleL", 0.08, 1.33, -1)
grabber_paddle("paddleR", 0.23, 1.33, 1)
tongs("tongs", -0.15, 0.72)
scoop("scoop", 0.12, -0.08)
peg("spare_peg", 0.17, 0.85)
# sign icon: three bundles + plus
for k, x in enumerate((-0.17, -0.07, 0.03)):
    decal(f"icon_tuft{k}", [(-0.035, -0.06), (0.035, -0.06), (0.028, 0.0), (0.012, 0.055), (0.0, 0.0),
                            (-0.012, 0.06), (-0.028, 0.0)], SIGN_FACE, "green", x0=x, z0=SIGN_Z - 0.01)
    decal(f"icon_tie{k}", [(-0.03, -0.028), (0.03, -0.028), (0.03, -0.012), (-0.03, -0.012)], SIGN_FACE - 0.002,
          "paint_dark", x0=x, z0=SIGN_Z - 0.01)
decal("icon_plus_v", [(-0.018, -0.06), (0.018, -0.06), (0.018, 0.06), (-0.018, 0.06)], SIGN_FACE, "green_dark", x0=0.17, z0=SIGN_Z)
decal("icon_plus_h", [(-0.06, -0.018), (0.06, -0.018), (0.06, 0.018), (-0.06, 0.018)], SIGN_FACE - 0.001, "green_dark", x0=0.17, z0=SIGN_Z)
finish("BundlesSection", -(SEC_W + GAP))

# 2) Speed: gloves cloth -> garden -> leather gauntlet (orange)
frame("orange", "orange_dark")
glove("glove1", -0.2, 1.34, "glove_cloth", "glove_cloth2", 1)
glove("glove2", 0.0, 1.34, "glove_green", "green_dark", 2)
glove("glove3", 0.2, 1.34, "glove_leather", "cuff_red", 3)
# pair of elbow pads hanging on pegs
for k, px_ in enumerate((-0.14, 0.14)):
    lathe(f"pad{k}", [(0.0, 0.035), (0.05, 0.03), (0.085, 0.012), (0.095, -0.01), (0.0, -0.01)], 10,
          lambda j, i: "pad" if j < 3 else "rubber", (px_, FRONT - 0.03, 0.8), rot=(math.pi / 2, 0, 0), scale=(1.0, 1.25, 1.0))
    box(f"pad_strap{k}", (px_, FRONT - 0.03, 0.8), (0.23, 0.02, 0.028), "strap")
    peg(f"pad_peg{k}", px_, 0.92)
    path(f"pad_hang{k}", [(px_, FRONT - 0.07, 0.92), (px_ - 0.03, FRONT - 0.05, 0.87)], 0.01, "strap")
# wrist guards lying on the shelf
for k, x in enumerate((0.07, 0.19)):
    lathe(f"wrist{k}", [(0.045, -0.04), (0.05, -0.03), (0.05, 0.03), (0.045, 0.04), (0.038, 0.04), (0.038, -0.04)], 10,
          lambda j, i: "orange" if j == 1 else "rubber", (x, -0.08, SHELF_Z + 0.068), rot=(0, math.pi / 2, 0.2 * k),
          cap_bottom=False, cap_top=False)
# sign icon: double chevron >>
for k, x in enumerate((-0.08, 0.06)):
    decal(f"chev{k}", [(-0.06, 0.08), (-0.02, 0.08), (0.06, 0.0), (-0.02, -0.08), (-0.06, -0.08), (0.02, 0.0)],
          SIGN_FACE, "orange", x0=x, z0=SIGN_Z)
finish("SpeedSection", 0.0)

# 3) Radius: small rake -> long hook -> fan rake (teal)
frame("teal", "teal_dark")
hand_rake("small_rake", -0.2, 1.36, 0.2, 0.12, 5, 0.08, grip="handle")
long_hook("hook", -0.1, 1.2, 0.7)
fan_rake("fan", 0.13, 1.40, 0.42, 0.42, 9, math.radians(70))
# sign icon: reach ring + centre dot + outward ticks
ring_decal("icon_ring", 0.07, 0.09, 16, SIGN_FACE, "teal", 0.0, SIGN_Z)
decal("icon_dot", [(-0.022, -0.022), (0.022, -0.022), (0.022, 0.022), (-0.022, 0.022)], SIGN_FACE, "teal_dark", x0=0, z0=SIGN_Z)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    cx, cz = math.cos(a) * 0.105, math.sin(a) * 0.105
    decal(f"icon_tick{k}", [(-0.012, -0.012), (0.012, -0.012), (0.012, 0.012), (-0.012, 0.012)], SIGN_FACE - 0.001,
          "teal_dark", x0=cx, z0=SIGN_Z + cz)
for sx in (-1, 1):
    decal(f"icon_arrow{sx}", [(0, 0.03), (sx * 0.05, 0.0), (0, -0.03)], SIGN_FACE, "teal_dark", x0=sx * 0.17, z0=SIGN_Z)
    decal(f"icon_arrow_stem{sx}", [(0, -0.01), (0, 0.01), (-sx * 0.04, 0.01), (-sx * 0.04, -0.01)], SIGN_FACE, "teal_dark",
          x0=sx * 0.17, z0=SIGN_Z)
finish("RadiusSection", SEC_W + GAP)

# ---------------------------------------------------------------- palette atlas + UVs, one shared material
img = bpy.data.images.new(NAME + "_Atlas", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(KEYS):
    cx, cy = idx % PAL_GRID, idx // PAL_GRID
    col = [c / 255 for c in PALETTE[k]]
    for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
        for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (*col, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, NAME + "_Atlas.png")
img.file_format = 'PNG'
img.save()

final = bpy.data.materials.new("M_HandUpgrade")
final.use_nodes = True
nt = final.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
bsdf.inputs["Metallic"].default_value = 0.0

total = 0
for name, ob in sections.items():
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap")
    slot_key = [m.name[4:] for m in me.materials]
    for poly in me.polygons:
        idx = KEYS.index(slot_key[poly.material_index])
        u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
        v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
        for li in poly.loop_indices:
            uvl.data[li].uv = (u, v)
        poly.material_index = 0
    me.materials.clear(); me.materials.append(final)
    zmin = min(v.co.z for v in me.vertices)       # base on the ground
    for v in me.vertices:
        v.co.z -= zmin
    me.update()
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    total += tris
    d = ob.dimensions
    print(f"SECTION {name} tris={tris} loc={tuple(round(c, 3) for c in ob.location)} W={d.x:.2f} D={d.y:.2f} H={d.z:.2f}")
print(f"TOTAL tris={total}")

for ob in sections.values():
    ob.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, NAME + ".fbx"),
    use_selection=True, object_types={'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z', axis_up='Y', bake_space_transform=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
    path_mode='RELATIVE', embed_textures=False,
)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, NAME + ".blend"))
print("EXPORTED")

# ---------------------------------------------------------------- preview renders
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.85, 0.15, -0.45))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=10)
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.10, 0.06, 1)
bpy.context.object.data.materials.append(g)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C"); cam_data.lens = 35
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
for tag, loc, target, res in (("front", (0.6, -3.6, 1.5), (0, 0, 0.95), (1200, 800)),
                              ("close", (0.35, -1.6, 1.35), (0.0, 0, 1.05), (900, 800))):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED")
