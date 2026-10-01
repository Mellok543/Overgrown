"""Overgrown environment kit: 15 stylized low-poly props sharing one palette atlas.
Run: blender -b --factory-startup -P environment_build.py

Each model -> Assets/Art/Models/Environment/<Name>.fbx (pivot at base centre, rotation 0, scale 1, Y up).
Shared texture: Environment_Atlas.png (Base Color). Greenhouse panes use a second material M_Glass.
WoodenFenceGate has a child "Gate" with its pivot on the hinge axis (rotate around local Y to open).
Blender is Z-up here, front = -Y (Unity +Z). Export converts to Y-up manually (see bottom)."""
import os, math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\Environment"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(2026)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- shared palette (sRGB)
PALETTE = {
    "wood": (150, 104, 64), "wood2": (134, 94, 58), "wood_light": (176, 132, 84), "wood_old": (128, 114, 98),
    "wood_dark": (84, 58, 38), "wood_grey": (110, 104, 96),
    "plaster": (226, 214, 186), "plaster_dirty": (196, 182, 150),
    "stone1": (138, 136, 128), "stone2": (118, 116, 110), "stone3": (156, 150, 138), "stone_dark": (92, 90, 86),
    "moss": (98, 120, 56),
    "roof": (156, 72, 52), "roof_dark": (118, 52, 40), "roof_tar": (70, 70, 74), "brick": (150, 78, 58),
    "glass_dark": (60, 78, 92), "shutter": (82, 122, 108), "door_paint": (70, 104, 130),
    "metal_dark": (62, 64, 68), "rust": (128, 78, 46), "black": (40, 40, 42), "white_frame": (226, 224, 214),
    "glow": (255, 214, 120),
    "soil": (78, 58, 40), "compost": (92, 70, 44), "leaf": (92, 140, 56), "leaf_dark": (64, 104, 44),
    "clippings": (128, 140, 70), "pot": (176, 96, 64),
    "glass": (190, 222, 214),
}
PAL_GRID, PAL_CELL = 8, 8
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)
MATS = {k: bpy.data.materials.new("tmp_" + k) for k in KEYS}
parts = []

def J(a):
    return rng.uniform(-a, a)

def wood():
    return rng.choice(["wood", "wood", "wood2", "wood_old", "wood_light"])

def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for k in mats:
        me.materials.append(MATS[k])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def mtx(center, rot):
    R = rot.to_matrix().to_4x4() if isinstance(rot, (Quaternion, Euler)) else Euler(rot).to_matrix().to_4x4()
    return Matrix.Translation(Vector(center)) @ R

def box(center, size, mat, rot=(0, 0, 0), bevel=0.0, seg=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect='EDGES', profile=0.5)
    bmesh.ops.transform(bm, matrix=mtx(center, rot), verts=bm.verts)
    return new_obj("box", bm, [mat])

def stick(a, b, t, mat, depth=None, bevel=0.0):
    a, b = Vector(a), Vector(b)
    d = b - a
    return box((a + b) / 2, (t, depth or t, d.length), mat, rot=d.to_track_quat('Z', 'Y').to_euler(), bevel=bevel)

def prism(pts, depth, mat, M, side_mat=None):
    """Polygon in local XY extruded along local Z (0..depth), transformed by M."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, 0)) for x, y in pts]
    hi = [bm.verts.new((x, y, depth)) for x, y in pts]
    used = [mat] + ([side_mat] if side_mat and side_mat != mat else [])
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    n = len(pts)
    for i in range(n):
        f = bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
        f.material_index = used.index(side_mat or mat)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return new_obj("prism", bm, used)

# local XY polygon -> world: x=along X, profile Y -> world Z, extrusion along world Y starting at y0
def M_xz(x0=0.0, y0=0.0, z0=0.0):
    return Matrix(((1, 0, 0, x0), (0, 0, 1, y0), (0, 1, 0, z0), (0, 0, 0, 1)))
# profile in (y, z), extruded along world X starting at x0
def M_yz(x0=0.0):
    return Matrix(((0, 0, 1, x0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))

def lathe(profile, n, mat_fn, center, rot=(0, 0, 0), cap_bottom=True, cap_top=True, phase=0.0, noise=0.0):
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))]); continue
        rings.append([bm.verts.new((math.cos(phase + math.tau * i / n) * r * (1 + J(noise)),
                                    math.sin(phase + math.tau * i / n) * r * (1 + J(noise)), z)) for i in range(n)])
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
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0]))).material_index = mi(mat_fn(0, 0))
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1]).material_index = mi(mat_fn(len(rings) - 2, 0))
    bmesh.ops.transform(bm, matrix=mtx(center, rot), verts=bm.verts)
    return new_obj("lathe", bm, used)

def stone(pts, h, side, top, z0=0.0, bev=0.015):
    """Flat stone slab: polygon pts (XY), height h, bevelled top."""
    c = Vector((sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)))
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    mid = [bm.verts.new((x, y, z0 + h - bev)) for x, y in pts]
    ins = []
    for x, y in pts:
        d = Vector((x, y)) - c
        k = max(0.0, d.length - bev) / max(d.length, 1e-6)
        ins.append(c + d * k)
    hi = [bm.verts.new((p.x, p.y, z0 + h + J(0.004))) for p in ins]
    used = [side, top] if side != top else [side]
    n = len(pts)
    bm.faces.new(list(reversed(lo)))
    for i in range(n):
        i2 = (i + 1) % n
        bm.faces.new((lo[i], lo[i2], mid[i2], mid[i]))
        bm.faces.new((mid[i], mid[i2], hi[i2], hi[i])).material_index = used.index(top)
    bm.faces.new(hi).material_index = used.index(top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj("stone", bm, used)

def quad2(a, b, c, d, mat):
    """Double-sided quad (thin panes)."""
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in (a, b, c, d)]
    w = [bm.verts.new(p) for p in (a, b, c, d)]
    bm.faces.new(v)
    bm.faces.new(list(reversed(w)))
    return new_obj("pane", bm, [mat])

def tri2(a, b, c, mat):
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in (a, b, c)]
    w = [bm.verts.new(p) for p in (a, b, c)]
    bm.faces.new(v)
    bm.faces.new(list(reversed(w)))
    return new_obj("pane", bm, [mat])

def blob(center, r, mat_fn, n=6, squash=0.8):
    """Low-poly leafy clump."""
    prof = [(0.0, -r * 0.5 * squash), (r * 0.75, -r * 0.35 * squash), (r, 0.0), (r * 0.75, r * 0.5 * squash), (0.0, r * 0.75 * squash)]
    return lathe(prof, n, mat_fn, center, rot=(0, 0, J(3)), noise=0.18)

def collect(name, pivot=(0, 0, 0)):
    global parts
    objs, parts = parts, []
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.name = ob.data.name = name
    ob.select_set(False)
    P = Vector(pivot)
    for v in ob.data.vertices:
        v.co -= P
    ob.location = P
    return ob

def clip_rect(poly, xmin, xmax, ymin, ymax):
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a):
                    out.append(inter(a, b))
                out.append(b)
            elif inside(a):
                out.append(inter(a, b))
        return out
    def ix(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def iy(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    p = poly
    for inside, inter in ((lambda q: q[0] >= xmin, ix(xmin)), (lambda q: q[0] <= xmax, ix(xmax)),
                          (lambda q: q[1] >= ymin, iy(ymin)), (lambda q: q[1] <= ymax, iy(ymax))):
        if not p:
            break
        p = clip(p, inside, inter)
    return p

def shrink(poly, d):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        v = Vector((x - cx, y - cy))
        k = max(0.0, v.length - d) / max(v.length, 1e-6)
        out.append((cx + v.x * k, cy + v.y * k))
    return out

models = {}

# ================================================================ shared bits
def window(cx, y, cz, w, h, facing, shutters=True):
    """Window on a wall plane. facing: -1 front (-Y), +1 back, or 'x+' / 'x-' for side walls (y is then x)."""
    def P(u, d, z):    # u along wall, d outward depth, z height
        if facing in (-1, 1):
            return (cx + u, y + facing * d, z)
        s = 1 if facing == "x+" else -1
        return (y + s * d, cx + u, z)
    def B(u, d, z, su, sd, sz, mat, bevel=0.0):
        if facing in (-1, 1):
            box(P(u, d, z), (su, sd, sz), mat, bevel=bevel)
        else:
            box(P(u, d, z), (sd, su, sz), mat, bevel=bevel)
    fw = 0.08
    B(0, 0.02, cz, w, 0.02, h, "glass_dark")
    B(0, 0.05, cz + h / 2 + fw / 2, w + 2 * fw, 0.07, fw, "white_frame")
    B(0, 0.07, cz - h / 2 - 0.03, w + 2 * fw + 0.06, 0.12, 0.06, "wood_dark", bevel=0.01)
    for s in (-1, 1):
        B(s * (w / 2 + fw / 2), 0.05, cz, fw, 0.07, h + 2 * fw, "white_frame")
    B(0, 0.045, cz, 0.04, 0.05, h, "white_frame")
    B(0, 0.045, cz, w, 0.05, 0.04, "white_frame")
    if shutters:
        for s in (-1, 1):
            u = s * (w / 2 + fw + w / 4 + 0.02)
            B(u, 0.035, cz, w / 2, 0.035, h + 0.1, "shutter", bevel=0.008)
            for z in (cz - h / 3, cz + h / 3):
                B(u, 0.055, z, w / 2 - 0.04, 0.01, 0.05, "black")

def grass_tuft(cx, cy, count=6, radius=0.08, h=(0.12, 0.3), z=0.0):
    bm = bmesh.new()
    for _ in range(count):
        a = rng.uniform(0, math.tau); r = radius * math.sqrt(rng.random())
        base = Vector((cx + math.cos(a) * r, cy + math.sin(a) * r, z))
        hh = rng.uniform(*h)
        lean = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.03, 0.09)
        side = Vector((-math.sin(a + 1.1), math.cos(a + 1.1), 0)) * rng.uniform(0.012, 0.02)
        tip = base + Vector((0, 0, hh)) + lean
        for flip in (False, True):
            v = [bm.verts.new(p) for p in (base - side, base + side, tip)]
            bm.faces.new(tuple(reversed(v)) if flip else v)
    return new_obj("tuft", bm, ["leaf"])

# ================================================================ 1. SmallHouse
def small_house():
    W, D, H0, HW = 6.0, 5.0, 0.35, 2.6
    ridge = H0 + HW + 1.7
    # stone foundation + a few proud stones
    box((0, 0, H0 / 2), (W + 0.12, D + 0.12, H0), "stone2", bevel=0.03)
    for k in range(14):
        side = rng.choice([-1, 1])
        if rng.random() < 0.5:
            box((J(W / 2 - 0.3), side * (D / 2 + 0.07), rng.uniform(0.08, 0.27)), (rng.uniform(0.2, 0.4), 0.04, rng.uniform(0.1, 0.16)),
                rng.choice(["stone1", "stone3", "moss"]), bevel=0.015)
        else:
            box((side * (W / 2 + 0.07), J(D / 2 - 0.3), rng.uniform(0.08, 0.27)), (0.04, rng.uniform(0.2, 0.4), rng.uniform(0.1, 0.16)),
                rng.choice(["stone1", "stone3", "moss"]), bevel=0.015)
    # plaster body with gables (pentagon prism along X)
    prism([(-D / 2, H0), (D / 2, H0), (D / 2, H0 + HW), (0, ridge), (-D / 2, H0 + HW)], W, "plaster", M_yz(-W / 2))
    box((0, 0, H0 + 0.15), (W + 0.01, D + 0.01, 0.3), "plaster_dirty")          # dirty splash band
    # timber frame: corner posts, top plate, diagonal braces on the front
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), H0 + HW / 2), (0.18, 0.18, HW), "wood_dark")
    for sy in (-1, 1):
        box((0, sy * (D / 2 + 0.03), H0 + HW - 0.06), (W + 0.05, 0.08, 0.14), "wood_dark")
    for sx in (-1, 1):
        box((sx * (W / 2 + 0.03), 0, H0 + HW - 0.06), (0.08, D + 0.05, 0.14), "wood_dark")
    for x0, x1 in ((-2.9, -2.35), (2.9, 2.35)):
        stick((x0, -D / 2 - 0.03, H0 + 0.1), (x1, -D / 2 - 0.03, H0 + HW - 0.15), 0.12, "wood_dark", depth=0.06)
    # gable boards (vertical planks on the triangles)
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.03)
        for k in range(9):
            y = -2.2 + k * 0.55
            top = H0 + HW + (1 - abs(y) / (D / 2)) * 1.7 - 0.05
            if top > H0 + HW + 0.1:
                box((x, y, (H0 + HW + top) / 2), (0.04, 0.5, top - H0 - HW), wood())
        window(0, sx * (W / 2 + 0.04), H0 + HW + 0.6, 0.45, 0.45, "x+" if sx > 0 else "x-", shutters=False)
    # roof: shingle rows on both slopes
    pitch = math.atan2(1.7, D / 2)
    slope_len = math.hypot(1.7, D / 2) + 0.45
    rows = 7
    for sy in (-1, 1):
        for r in range(rows):
            t = (r + 0.5) / rows
            # position along the slope from eave (t=0) to ridge (t=1)
            yy = sy * (D / 2 + 0.38 - t * slope_len * math.cos(pitch))
            zz = H0 + HW - 0.38 * math.tan(pitch) + t * slope_len * math.sin(pitch) + 0.1
            box((J(0.02), yy, zz + r * 0.004), (W + 0.6, slope_len / rows + 0.06, 0.07),
                "roof_dark" if r % 2 else "roof", rot=(-sy * pitch + J(0.008), 0, 0))
    box((0, 0, ridge + 0.14), (W + 0.62, 0.22, 0.14), "roof_dark", bevel=0.02)
    for sx in (-1, 1):   # barge boards
        for sy in (-1, 1):
            a = Vector((sx * (W / 2 + 0.3), sy * (D / 2 + 0.4), H0 + HW - 0.2))
            b = Vector((sx * (W / 2 + 0.3), 0, ridge + 0.12))
            stick(a, b, 0.05, "wood_dark", depth=0.2)
    # chimney
    box((-1.6, 1.0, ridge - 0.2), (0.6, 0.6, 2.0), "brick", bevel=0.02)
    box((-1.6, 1.0, ridge + 0.85), (0.72, 0.72, 0.1), "stone_dark", bevel=0.02)
    # front: door + windows
    fy = -D / 2 - 0.01
    box((0.9, fy - 0.03, H0 + 1.05), (1.05, 0.08, 2.15), "wood_dark")
    for k in range(3):
        box((0.9 - 0.3 + k * 0.3, fy - 0.07, H0 + 1.0), (0.28, 0.04, 1.95), "door_paint", bevel=0.01)
    box((0.9, fy - 0.1, H0 + 1.45), (0.5, 0.02, 0.3), "glass_dark")
    box((1.2, fy - 0.11, H0 + 0.95), (0.05, 0.04, 0.12), "black")
    window(-1.6, fy, H0 + 1.45, 0.9, 1.0, -1)
    window(2.35, fy, H0 + 1.45, 0.7, 1.0, -1, shutters=False)
    for x in (-1.6, 1.4):
        window(x, D / 2 + 0.01, H0 + 1.45, 0.9, 1.0, 1)
    for sx in (-1, 1):
        window(-0.8 * sx, sx * (W / 2 + 0.01), H0 + 1.45, 0.8, 1.0, "x+" if sx > 0 else "x-")
    # porch: deck, steps, posts, lean-to roof
    PW, PD = 2.6, 1.6
    py = -D / 2 - PD / 2
    for k in range(6):
        box((0.6, py - PD / 2 + 0.13 + k * 0.27, H0 - 0.03), (PW, 0.25, 0.06), wood(), bevel=0.01)
    box((0.6, py, (H0 - 0.06) / 2), (PW - 0.1, PD - 0.1, H0 - 0.06), "wood_dark")
    for k, (h, dy) in enumerate(((0.24, 0.0), (0.12, 0.3))):
        box((0.6, py - PD / 2 - 0.15 - dy, h / 2), (1.2, 0.3, h), "wood2", bevel=0.01)
    for sx in (-1, 1):
        px = 0.6 + sx * (PW / 2 - 0.1)
        box((px, py - PD / 2 + 0.1, H0 + 1.2), (0.12, 0.12, 2.4), "wood_dark", bevel=0.01)
        stick((px, py - PD / 2 + 0.1, H0 + 2.0), (px, py - PD / 2 + 0.5, H0 + 2.38), 0.08, "wood_dark")
    # lean-to from just under the main eave (H0+HW) down to the post beam (H0+2.45)
    lean = math.atan2(HW - 2.45 + 0.1, PD + 0.1)
    box((0.6, py - 0.05, H0 + (HW + 0.1 + 2.45) / 2 + 0.05), (PW + 0.4, (PD + 0.5) / math.cos(lean), 0.07), "roof", rot=(lean, 0, 0))
    box((0.6, py - PD / 2 + 0.1, H0 + 2.43), (PW + 0.1, 0.12, 0.12), "wood_dark")
    # overgrowth: ivy clumps at a corner, tufts along the base
    for k in range(5):
        blob((W / 2 + 0.1, -D / 2 + 0.2 + k * 0.12, 0.3 + k * 0.45), rng.uniform(0.18, 0.28),
             lambda j, i: "leaf" if (i + j) % 3 else "leaf_dark")
    for k in range(10):
        grass_tuft(rng.uniform(-W / 2, W / 2), rng.choice([-1, 1]) * (D / 2 + 0.12), 5, 0.1)
    return collect("SmallHouse")

# ================================================================ 2. GardenShed
def garden_shed():
    W, D = 2.4, 2.0
    HF, HB = 2.25, 1.95                     # lean-to roof: front high, back low
    hz = lambda y: HB + (HF - HB) * (D / 2 - y) / D
    box((0, 0, 0.06), (W + 0.06, D + 0.06, 0.12), "stone_dark", bevel=0.02)
    box((0, 0, 1.1), (W - 0.06, D - 0.06, 2.0), "wood_dark")         # dark inner box behind the boards
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), hz(sy * D / 2) / 2), (0.1, 0.1, hz(sy * D / 2)), "wood_dark")
    BW = 0.2
    # front / back boards (door gap in the front)
    for sy in (-1, 1):
        y = sy * (D / 2 + 0.015)
        h = hz(sy * D / 2)
        for k in range(12):
            x = -W / 2 + BW / 2 + k * BW
            if sy == -1 and abs(x - 0.1) < 0.5:
                continue
            hh = h - 0.12 + J(0.03)
            box((x + J(0.005), y, 0.12 + hh / 2), (BW - 0.012, 0.03, hh), wood())
    # side boards follow the roof slope
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.015)
        for k in range(10):
            y = -D / 2 + BW / 2 + k * BW
            hh = hz(y) - 0.12 + J(0.03)
            if sx == 1 and abs(y - 0.0) < 0.35:      # window opening area, boards below / above
                box((x, y, 0.12 + 0.55), (0.03, BW - 0.012, 1.1), wood())
                box((x, y, (1.65 + 0.12 + hh) / 2), (0.03, BW - 0.012, 0.12 + hh - 1.65), wood())
                continue
            box((x, y + J(0.005), 0.12 + hh / 2), (0.03, BW - 0.012, hh), wood())
    # side window (dark glass + cross frame)
    xw = W / 2 + 0.03
    box((xw, 0, 1.43), (0.02, 0.6, 0.45), "glass_dark")
    for dz, sz in ((0.26, 0.07), (-0.26, 0.07)):
        box((xw + 0.02, 0, 1.43 + dz), (0.05, 0.72, sz), "wood_dark")
    for dy in (-0.33, 0.33):
        box((xw + 0.02, dy, 1.43), (0.05, 0.07, 0.6), "wood_dark")
    box((xw + 0.025, 0, 1.43), (0.04, 0.04, 0.45), "wood_dark")
    box((xw + 0.025, 0, 1.43), (0.04, 0.6, 0.04), "wood_dark")
    # old plank door with Z-brace, hinges, latch
    dx, dy = 0.1, -D / 2 - 0.03
    box((dx, dy + 0.01, 1.08), (1.04, 0.05, 1.96), "wood_dark")
    for k in range(4):
        hh = 1.82 + J(0.03) - (0.08 if k == 3 else 0)       # one board rotted shorter
        box((dx - 0.36 + k * 0.24, dy - 0.02, 0.18 + hh / 2), (0.225, 0.035, hh), rng.choice(["wood_old", "wood_grey", "wood2"]))
    for z in (0.45, 1.75):
        box((dx, dy - 0.05, z), (0.92, 0.03, 0.12), "wood2")
    stick((dx - 0.4, dy - 0.05, 0.5), (dx + 0.4, dy - 0.05, 1.7), 0.1, "wood2", depth=0.03)
    for z in (0.45, 1.75):
        box((dx - 0.3, dy - 0.07, z), (0.4, 0.012, 0.05), "rust")
    box((dx + 0.38, dy - 0.07, 1.1), (0.04, 0.03, 0.14), "black")
    box((0.1, -D / 2 - 0.03, 2.13), (1.15, 0.06, 0.1), "wood_dark")
    # tar-paper lean-to roof with trims
    pitch = math.atan2(HF - HB, D)
    box((0, 0, (HF + HB) / 2 + 0.08), (W + 0.4, D / math.cos(pitch) + 0.45, 0.08), "roof_tar", rot=(-pitch, 0, 0), bevel=0.01)
    for sx in (-1, 1):
        box((sx * (W / 2 + 0.2), 0, (HF + HB) / 2 + 0.06), (0.04, D / math.cos(pitch) + 0.45, 0.14), "wood_dark", rot=(-pitch, 0, 0))
    box((0, -D / 2 - 0.22, HF + 0.08), (W + 0.42, 0.04, 0.16), "wood_dark")
    # rain barrel corner + tufts
    for k in range(6):
        grass_tuft(rng.uniform(-W / 2, W / 2), rng.choice([-1, 1]) * (D / 2 + 0.08), 5, 0.08)
    blob((-W / 2 - 0.05, -D / 2 + 0.3, 0.15), 0.25, lambda j, i: "leaf" if i % 2 else "leaf_dark")
    return collect("GardenShed")

# ================================================================ 3. Greenhouse
def greenhouse():
    W, L, HE, HR = 2.2, 3.0, 1.7, 2.4
    # wooden sill
    for sy in (-1, 1):
        box((0, sy * (L / 2), 0.15), (W + 0.1, 0.1, 0.3), "wood2", bevel=0.01)
    for sx in (-1, 1):
        box((sx * (W / 2), 0, 0.15), (0.1, L, 0.3), "wood2", bevel=0.01)
    bays = [-L / 2, -L / 2 + 1.0, -L / 2 + 2.0, L / 2]
    # white frame: posts, eaves, rafters, ridge
    for y in bays:
        for sx in (-1, 1):
            box((sx * W / 2, y, 0.3 + (HE - 0.3) / 2), (0.06, 0.06, HE - 0.3), "white_frame")
            stick((sx * W / 2, y, HE), (0, y, HR), 0.06, "white_frame")
    for sx in (-1, 1):
        box((sx * W / 2, 0, HE), (0.07, L + 0.06, 0.06), "white_frame")
    box((0, 0, HR + 0.02), (0.08, L + 0.1, 0.08), "white_frame")
    # door frame on the front gable
    for sx in (-1, 1):
        box((sx * 0.4, -L / 2, 0.3 + (HE + 0.25 - 0.3) / 2), (0.06, 0.07, HE + 0.25 - 0.3), "white_frame")
    box((0, -L / 2, HE + 0.25), (0.86, 0.07, 0.06), "white_frame")
    # glass panes (M_Glass): side walls, roof, gables (one roof pane missing - abandoned)
    g = 0.0
    for k in range(3):
        y0, y1 = bays[k] + 0.03, bays[k + 1] - 0.03
        for sx in (-1, 1):
            x = sx * (W / 2 + 0.005)
            quad2((x, y0, 0.31), (x, y1, 0.31), (x, y1, HE - 0.03), (x, y0, HE - 0.03), "glass")
            if not (sx == 1 and k == 1):
                quad2((sx * (W / 2 - 0.03), y0, HE + 0.03), (sx * (W / 2 - 0.03), y1, HE + 0.03),
                      (sx * 0.04, y1, HR - 0.01), (sx * 0.04, y0, HR - 0.01), "glass")
    for sy in (-1, 1):
        y = sy * (L / 2 + 0.005)
        tri2((-W / 2 + 0.04, y, HE + 0.02), (W / 2 - 0.04, y, HE + 0.02), (0, y, HR - 0.03), "glass")
        if sy == 1:
            quad2((-W / 2 + 0.03, y, 0.31), (W / 2 - 0.03, y, 0.31), (W / 2 - 0.03, y, HE - 0.03), (-W / 2 + 0.03, y, HE - 0.03), "glass")
        else:
            for sx in (-1, 1):
                a, b = sorted((sx * 0.43, sx * (W / 2 - 0.03)))
                quad2((a, y, 0.31), (b, y, 0.31), (b, y, HE - 0.03), (a, y, HE - 0.03), "glass")
    # door (slightly ajar is avoided: keeps the collider simple) - glazed panel
    box((0, -L / 2 - 0.04, 0.32 + 0.9), (0.72, 0.03, 0.05), "white_frame")
    for sx in (-1, 1):
        box((sx * 0.35, -L / 2 - 0.04, 0.3 + (HE + 0.2 - 0.3) / 2), (0.05, 0.03, HE + 0.2 - 0.3), "white_frame")
    quad2((-0.33, -L / 2 - 0.04, 0.32), (0.33, -L / 2 - 0.04, 0.32), (0.33, -L / 2 - 0.04, HE + 0.18), (-0.33, -L / 2 - 0.04, HE + 0.18), "glass")
    box((0.27, -L / 2 - 0.07, 1.0), (0.03, 0.03, 0.1), "black")
    # inside: potting bench + pots + seedlings
    box((W / 2 - 0.35, 0.2, 0.75), (0.55, 2.0, 0.05), "wood", bevel=0.01)
    for y in (-0.7, 1.1):
        for dx in (-0.22, 0.22):
            box((W / 2 - 0.35 + dx, y, 0.37), (0.05, 0.05, 0.74), "wood_dark")
    for k in range(5):
        p = Vector((W / 2 - 0.35 + J(0.12), -0.6 + k * 0.38, 0.775))
        lathe([(0.0, 0.0), (0.06, 0.0), (0.085, 0.13), (0.075, 0.13), (0.0, 0.12)], 8, lambda j, i: "pot" if j < 2 else "soil", p)
        if k % 2 == 0:
            blob(p + Vector((0, 0, 0.17)), 0.08, lambda j, i: "leaf")
    for k in range(8):
        grass_tuft(rng.uniform(-W / 2, W / 2), rng.choice([-1, 1]) * (L / 2 + 0.07), 5, 0.07)
    return collect("Greenhouse")

# ================================================================ 4/5. Fence + gate
FH = 1.05
def picket_pts(w, h):
    return [(-w / 2, 0), (w / 2, 0), (w / 2, h - w * 0.6), (0, h), (-w / 2, h - w * 0.6)]

def fence_post(x):
    box((x, 0.0, 0.62), (0.11, 0.11, 1.24), "wood_dark", bevel=0.01)
    lathe([(0.075, 0.0), (0.0, 0.08)], 4, lambda j, i: "wood_dark", (x, 0.0, 1.24), phase=math.pi / 4, cap_top=False)

def fence_run(x0, x1, missing=()):
    for z in (0.3, 0.82):
        box(((x0 + x1) / 2, 0.06, z), (x1 - x0, 0.03, 0.09), "wood2", rot=(0, J(0.01), 0), bevel=0.006)
    n = max(1, int(round((x1 - x0) / 0.21)))
    step = (x1 - x0) / n
    for k in range(n):
        if k in missing:
            continue
        x = x0 + step * (k + 0.5)
        h = FH + J(0.04)
        tilt = J(0.035) if rng.random() < 0.8 else rng.choice([-1, 1]) * 0.12
        M = Matrix.Translation((x, 0.03, 0.04)) @ Matrix.Rotation(tilt, 4, 'Y') @ M_xz(0, 0, 0)
        prism(picket_pts(0.1, h), 0.025, rng.choice(["wood_old", "wood_old", "wood_grey", "wood"]), M)

def wooden_fence():
    fence_post(-1.0)
    fence_run(-0.95, 1.0, missing=(6,))
    for k in range(4):
        grass_tuft(rng.uniform(-1, 1), J(0.08), 5, 0.06)
    return collect("WoodenFence")

def wooden_fence_gate():
    fence_post(-1.0)
    fence_run(-0.95, -0.56)
    fence_post(-0.5)
    fence_post(0.5)
    fence_run(0.56, 1.0)
    for k in range(3):
        grass_tuft(rng.uniform(-1, 1), J(0.08), 5, 0.06)
    root = collect("WoodenFenceGate")
    # gate leaf, hinge axis at x = -0.44
    hx = -0.44
    for z in (0.28, 0.85):
        box((hx + 0.45, -0.02, z), (0.86, 0.03, 0.09), "wood2", bevel=0.006)
    stick((hx + 0.08, -0.02, 0.3), (hx + 0.82, -0.02, 0.83), 0.08, "wood2", depth=0.03)
    for k in range(4):
        x = hx + 0.1 + k * 0.23
        M = Matrix.Translation((x, -0.065, 0.06)) @ M_xz(0, 0, 0)
        prism(picket_pts(0.11, FH - 0.08 + J(0.02)), 0.025, rng.choice(["wood_old", "wood", "wood_grey"]), M)
    for z in (0.28, 0.85):
        box((hx + 0.06, -0.035, z), (0.16, 0.012, 0.04), "black")
        lathe([(0.012, -0.03), (0.012, 0.03)], 6, lambda j, i: "black", (hx, -0.03, z))
    box((hx + 0.86, -0.04, 0.85), (0.06, 0.03, 0.025), "metal_dark")
    box((0.47, -0.02, 0.85), (0.05, 0.05, 0.05), "metal_dark")
    gate = collect("Gate", (hx, 0, 0))
    gate.parent = root
    gate.matrix_parent_inverse = Matrix.Identity(4)
    gate.location = Vector((hx, 0, 0))
    return root, gate

# ================================================================ 6/7. Stone paths
def stone_mats():
    side = rng.choice(["stone1", "stone2", "stone3", "stone_dark"])
    top = "moss" if rng.random() < 0.18 else rng.choice(["stone1", "stone2", "stone3"])
    return side if top != "moss" else "stone2", top

def path_straight():
    WX, LY = 1.2, 2.0
    cols, rows = 3, 5
    cw, rh = WX / cols, LY / rows
    for r in range(rows):
        off = (r % 2) * cw * 0.5          # running bond
        for c in range(-1, cols + 1):
            x0 = -WX / 2 + c * cw + off - cw * 0.25
            x1 = x0 + cw * rng.uniform(0.85, 1.1)
            y0 = -LY / 2 + r * rh
            y1 = y0 + rh
            ch = rng.uniform(0.03, 0.07)
            poly = [(x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch), (x1, y1 - ch), (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch), (x0, y0 + ch)]
            poly = [(x + J(0.025), y + J(0.025)) for x, y in poly]
            poly = clip_rect(poly, -WX / 2 + 0.02, WX / 2 - 0.02, -LY / 2 + 0.02, LY / 2 - 0.02)
            if len(poly) < 3:
                continue
            poly = shrink(poly, 0.025)
            area = 0.5 * abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly))))
            if area < 0.01 or rng.random() < 0.05:
                continue
            side, top = stone_mats()
            stone(poly, rng.uniform(0.045, 0.07), side, top)
    return collect("StonePath_Straight")

def path_corner():
    S = 1.2
    P = Vector((S / 2, -S / 2))          # inner corner of the turn (path enters from -Y, leaves to -X... any rotation works)
    radii = [0.0, 0.42, 0.84, 1.26, 1.72]
    sectors = [2, 3, 4, 5]
    for ri in range(4):
        r0, r1 = radii[ri], radii[ri + 1]
        n = sectors[ri]
        for k in range(n):
            a0 = math.pi / 2 + (math.pi / 2) * k / n + J(0.04)
            a1 = math.pi / 2 + (math.pi / 2) * (k + 1) / n + J(0.04)
            arc = 4
            outer = [(P.x + math.cos(a0 + (a1 - a0) * t / arc) * r1, P.y + math.sin(a0 + (a1 - a0) * t / arc) * r1) for t in range(arc + 1)]
            inner = [(P.x + math.cos(a1 - (a1 - a0) * t / arc) * r0, P.y + math.sin(a1 - (a1 - a0) * t / arc) * r0) for t in range(arc + 1)] if r0 > 0 else [(P.x, P.y)]
            poly = [(x + J(0.015), y + J(0.015)) for x, y in outer + inner]
            poly = clip_rect(poly, -S / 2 + 0.02, S / 2 - 0.02, -S / 2 + 0.02, S / 2 - 0.02)
            if len(poly) < 3:
                continue
            poly = shrink(poly, 0.025)
            area = 0.5 * abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly))))
            if area < 0.01:
                continue
            side, top = stone_mats()
            stone(poly, rng.uniform(0.045, 0.07), side, top)
    return collect("StonePath_Corner")

# ================================================================ 8. WoodenBench
def wooden_bench():
    L = 1.5
    for k in range(3):
        box((J(0.01), -0.16 + k * 0.13, 0.45), (L, 0.12, 0.04), wood(), rot=(0, 0, J(0.01)), bevel=0.008)
    for k, z in enumerate((0.66, 0.82)):
        box((0, 0.27 + k * 0.035, z), (L, 0.035, 0.11), wood(), rot=(-0.25, 0, 0), bevel=0.008)
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.12)
        stick((x, -0.2, 0.0), (x, -0.18, 0.43), 0.06, "wood_dark", bevel=0.006)
        stick((x, 0.24, 0.0), (x, 0.33, 0.9), 0.06, "wood_dark", bevel=0.006)
        box((x, 0.0, 0.41), (0.06, 0.5, 0.05), "wood_dark")
        box((x, 0.02, 0.62), (0.07, 0.52, 0.04), "wood2", bevel=0.008)
        stick((x, -0.2, 0.43), (x, -0.22, 0.62), 0.05, "wood_dark")
    box((0, 0.05, 0.15), (L - 0.3, 0.05, 0.05), "wood_dark")
    return collect("WoodenBench")

# ================================================================ 9. WoodenCrate
def wooden_crate():
    W, D, H = 0.6, 0.48, 0.44
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * (W / 2 - 0.025), sy * (D / 2 - 0.025), H / 2), (0.05, 0.05, H), "wood_dark", bevel=0.006)
    for r in range(3):
        z = 0.08 + r * 0.14
        for sy in (-1, 1):
            box((J(0.005), sy * (D / 2 + 0.008), z), (W - 0.01, 0.018, 0.11), wood(), bevel=0.004)
        for sx in (-1, 1):
            box((sx * (W / 2 + 0.008), J(0.005), z), (0.018, D - 0.01, 0.11), wood(), bevel=0.004)
    for k in range(4):
        box((J(0.005), -D / 2 + 0.06 + k * 0.12, H + 0.01), (W + 0.02, 0.11, 0.02), wood(), rot=(0, 0, J(0.02)), bevel=0.004)
    for sy in (-1, 1):
        stick((-W / 2 + 0.05, sy * (D / 2 + 0.02), 0.05), (W / 2 - 0.05, sy * (D / 2 + 0.02), H - 0.05), 0.07, "wood2", depth=0.015)
    box((0, 0, 0.01), (W - 0.04, D - 0.04, 0.02), "wood_dark")
    return collect("WoodenCrate")

# ================================================================ 10. Barrel
def barrel():
    prof = [(0.25, 0.0), (0.29, 0.12), (0.315, 0.3), (0.32, 0.45), (0.315, 0.6), (0.29, 0.78), (0.25, 0.9),
            (0.235, 0.9), (0.235, 0.86)]
    lathe(prof, 14, lambda j, i: ("wood" if i % 2 else "wood2") if j < 6 else "wood_dark", (0, 0, 0), cap_top=False)
    lathe([(0.235, 0.86), (0.0, 0.86)], 14, lambda j, i: "wood_dark", (0, 0, 0), cap_bottom=False, cap_top=False)
    for z, r in ((0.1, 0.287), (0.3, 0.318), (0.6, 0.318), (0.8, 0.287)):
        lathe([(r, z - 0.025), (r + 0.008, z - 0.02), (r + 0.008, z + 0.02), (r, z + 0.025)], 14,
              lambda j, i: "rust" if i % 5 == 0 else "metal_dark", (0, 0, 0), cap_bottom=False, cap_top=False)
    for k in (-1, 1):   # lid boards lines
        box((k * 0.08, 0, 0.865), (0.012, 0.42, 0.01), "black")
    return collect("Barrel")

# ================================================================ 11. GardenLamp
def garden_lamp():
    box((0, 0, 0.04), (0.22, 0.22, 0.08), "stone2", bevel=0.015)
    box((0, 0, 0.42), (0.06, 0.06, 0.7), "metal_dark", bevel=0.008)
    box((0, 0, 0.78), (0.16, 0.16, 0.03), "metal_dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * 0.075, sy * 0.075, 0.9), (0.02, 0.02, 0.22), "black")
    box((0, 0, 0.9), (0.13, 0.13, 0.2), "glow")
    for sx in (-1, 1):
        box((sx * 0.07, 0, 0.9), (0.005, 0.012, 0.2), "black")
        box((0, sx * 0.07, 0.9), (0.012, 0.005, 0.2), "black")
    lathe([(0.13, 0.0), (0.0, 0.11)], 4, lambda j, i: "metal_dark", (0, 0, 1.01), phase=math.pi / 4)
    lathe([(0.0, 0.0), (0.02, 0.0), (0.02, 0.03), (0.0, 0.05)], 6, lambda j, i: "rust", (0, 0, 1.11))
    grass_tuft(0.05, 0.05, 5, 0.1)
    return collect("GardenLamp")

# ================================================================ 12. CompostBin
def compost_bin():
    S, H = 1.0, 0.85
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * (S / 2 - 0.04), sy * (S / 2 - 0.04), H / 2), (0.08, 0.08, H), "wood_dark", bevel=0.008)
    for r in range(5):
        z = 0.08 + r * 0.16
        for sy in (-1, 1):
            if sy == -1 and r == 4:
                continue          # front top slat removed for access
            box((J(0.008), sy * (S / 2 + 0.01), z), (S - 0.02, 0.025, 0.12), wood(), rot=(0, J(0.012), 0), bevel=0.005)
        for sx in (-1, 1):
            box((sx * (S / 2 + 0.01), J(0.008), z), (0.025, S - 0.02, 0.12), wood(), rot=(J(0.012), 0, 0), bevel=0.005)
    # contents: compost body + bumpy grass clippings on top
    box((0, 0, 0.3), (S - 0.06, S - 0.06, 0.6), "compost")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=5, y_segments=5, size=(S - 0.08) / 2)
    for v in bm.verts:
        v.co.z = 0.62 + 0.06 * (1 - max(abs(v.co.x), abs(v.co.y)) / ((S - 0.08) / 2)) + J(0.025)
    for f in bm.faces:
        f.material_index = 1 if rng.random() < 0.35 else 0
    new_obj("clippings", bm, ["clippings", "compost"])
    for k in range(4):
        grass_tuft(J(0.3), J(0.3), 4, 0.06, h=(0.08, 0.16), z=0.64)
    return collect("CompostBin")

# ================================================================ 13. GardenTable
def garden_table():
    L, Wd, H = 1.4, 0.8, 0.75
    for k in range(5):
        box((J(0.008), -Wd / 2 + 0.08 + k * 0.16, H - 0.02), (L, 0.15, 0.04), wood(), bevel=0.008)
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.18)
        box((x, 0, H - 0.07), (0.07, Wd - 0.06, 0.06), "wood_dark")
        for sy in (-1, 1):
            stick((x, sy * (Wd / 2 - 0.05), 0.0), (x, sy * 0.06, H - 0.1), 0.07, "wood_dark", bevel=0.006)
        box((x, 0, 0.25), (0.06, Wd - 0.25, 0.05), "wood2")
    box((0, 0, 0.25), (L - 0.36, 0.06, 0.05), "wood2")
    return collect("GardenTable")

# ================================================================ 14. GardenChair
def garden_chair():
    S, H = 0.46, 0.45
    for k in range(3):
        box((0, -S / 2 + 0.08 + k * 0.15, H), (S, 0.14, 0.035), wood(), bevel=0.006)
    for sx in (-1, 1):
        x = sx * (S / 2 - 0.03)
        box((x, -S / 2 + 0.04, H / 2), (0.05, 0.05, H), "wood_dark", bevel=0.006)
        stick((x, S / 2 - 0.04, 0.0), (x, S / 2 + 0.02, 0.92), 0.05, "wood_dark", bevel=0.006)
        box((x, 0, H - 0.04), (0.04, S - 0.04, 0.05), "wood_dark")
        box((x, 0, 0.15), (0.03, S - 0.06, 0.03), "wood2")
    for k, z in enumerate((0.6, 0.72, 0.84)):
        box((0, S / 2 - 0.04 + (z - H) * 0.066, z), (S - 0.05, 0.025, 0.08), wood(), rot=(-0.066, 0, 0), bevel=0.005)
    return collect("GardenChair")

# ================================================================ 15. PlanterBox
def planter_box():
    L, Wd, H = 1.2, 0.5, 0.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((sx * (L / 2 - 0.03), sy * (Wd / 2 - 0.03), H / 2), (0.06, 0.06, H), "wood_dark", bevel=0.006)
    for r in range(2):
        z = 0.1 + r * 0.18
        for sy in (-1, 1):
            box((J(0.005), sy * (Wd / 2 + 0.005), z), (L - 0.02, 0.025, 0.16), wood(), bevel=0.005)
        for sx in (-1, 1):
            box((sx * (L / 2 + 0.005), 0, z), (0.025, Wd - 0.02, 0.16), wood(), bevel=0.005)
    for sy in (-1, 1):
        box((0, sy * (Wd / 2), H + 0.01), (L + 0.06, 0.08, 0.025), "wood2", bevel=0.005)
    for sx in (-1, 1):
        box((sx * (L / 2), 0, H + 0.01), (0.08, Wd + 0.06, 0.025), "wood2", bevel=0.005)
    box((0, 0, 0.17), (L - 0.06, Wd - 0.06, 0.34), "soil")
    for k in range(3):
        blob((-0.35 + k * 0.35 + J(0.05), J(0.05), 0.4), rng.uniform(0.1, 0.14), lambda j, i: "leaf" if (i + j) % 3 else "leaf_dark")
    for k in range(4):
        grass_tuft(-0.5 + k * 0.33, J(0.12), 3, 0.03, h=(0.06, 0.12), z=0.34)
    return collect("PlanterBox")

# ---------------------------------------------------------------- build all
build_order = [small_house, garden_shed, greenhouse, wooden_fence, wooden_fence_gate, path_straight, path_corner,
               wooden_bench, wooden_crate, barrel, garden_lamp, compost_bin, garden_table, garden_chair, planter_box]
roots = []
for fn in build_order:
    res = fn()
    if isinstance(res, tuple):
        roots.append(res[0])
    else:
        roots.append(res)

# ---------------------------------------------------------------- atlas, UVs, materials, triangulation
img = bpy.data.images.new("Environment_Atlas", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(KEYS):
    cx, cy = idx % PAL_GRID, idx // PAL_GRID
    col = [c / 255 for c in PALETTE[k]]
    for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
        for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (*col, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, "Environment_Atlas.png")
img.file_format = 'PNG'
img.save()

M_ENV = bpy.data.materials.new("M_Environment")
M_ENV.use_nodes = True
nt = M_ENV.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
M_GLASS = bpy.data.materials.new("M_Glass")
M_GLASS.use_nodes = True
gb = M_GLASS.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.55, 0.75, 0.7, 1)
gb.inputs["Alpha"].default_value = 0.28
gb.inputs["Roughness"].default_value = 0.1
try:
    M_GLASS.surface_render_method = 'BLENDED'
except Exception:
    M_GLASS.blend_method = 'BLEND'

mesh_objs = []
for r in roots:
    mesh_objs.append(r)
    mesh_objs.extend(r.children)
stats = {}
for ob in mesh_objs:
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap")
    slot_key = [m.name[4:] for m in me.materials]
    has_glass = "glass" in slot_key
    for poly in me.polygons:
        key = slot_key[poly.material_index]
        idx = KEYS.index(key)
        u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
        v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
        for li in poly.loop_indices:
            uvl.data[li].uv = (u, v)
        poly.material_index = 1 if key == "glass" else 0
    me.materials.clear()
    me.materials.append(M_ENV)
    if has_glass:
        me.materials.append(M_GLASS)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free(); me.update()
total = 0
for r in roots:
    obs = [r] + list(r.children)
    tris = sum(len(o.data.polygons) for o in obs)
    total += tris
    ws = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    mn = [min(p[i] for p in ws) for i in range(3)]; mx = [max(p[i] for p in ws) for i in range(3)]
    print(f"MODEL {r.name:20s} tris={tris:5d} size W={mx[0]-mn[0]:.2f} D={mx[1]-mn[1]:.2f} H={mx[2]-mn[2]:.2f} minZ={mn[2]:.3f}"
          + (f" children={[c.name for c in r.children]}" if r.children else ""))
print(f"TOTAL tris={total}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Environment_Kit.blend"))

# ---------------------------------------------------------------- preview renders (line-ups)
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.6, 0.72, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.85, 0.2, -0.7))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=80)
ground = bpy.context.object
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.16, 0.05, 1)
ground.data.materials.append(gm)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_data)
scene.collection.objects.link(cam); scene.camera = cam
by = {r.name: r for r in roots}
def shot(tag, layout, loc, target, res=(1600, 900), lens=35):
    for r in roots:
        r.location = (0, 0, -100)
    for name, pos in layout.items():
        by[name].location = pos
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
shot("house", {"SmallHouse": (0, 0, 0)}, (-7.5, -10.5, 4.5), (0.2, -0.8, 2.0), lens=35)
shot("buildings", {"SmallHouse": (-6.0, 1.0, 0), "GardenShed": (0.6, -0.5, 0), "Greenhouse": (4.6, 0, 0)},
     (0.0, -17.0, 6.5), (0, 0, 1.8), lens=32)
shot("fences_paths", {"WoodenFence": (-3.0, 0, 0), "WoodenFenceGate": (-1.0, 0, 0), "StonePath_Straight": (1.5, -0.6, 0),
                      "StonePath_Corner": (1.5, -2.2, 0), "Barrel": (3.4, 0, 0), "WoodenCrate": (4.3, -0.4, 0)},
     (0.5, -6.8, 3.2), (0.6, -0.6, 0.4), lens=35)
shot("props", {"WoodenBench": (-2.6, 0, 0), "WoodenCrate": (-1.0, -0.1, 0), "Barrel": (0.0, 0, 0),
               "PlanterBox": (1.4, -0.1, 0), "GardenLamp": (2.7, 0, 0)},
     (0.0, -5.6, 2.4), (0.0, 0, 0.4), lens=35)
shot("props2", {"GardenTable": (-1.8, 0, 0), "GardenChair": (-0.6, -0.1, 0), "CompostBin": (1.0, 0, 0),
                "WoodenBench": (2.7, 0.1, 0)},
     (0.3, -5.0, 2.3), (0.3, 0, 0.45), lens=35)
for r in roots:
    r.location = (0, 0, 0)
print("RENDERED")

# ---------------------------------------------------------------- export, one FBX per model
# Convert to Y-up ourselves (mesh data + child offsets rotated -90 deg about X), export without axis
# conversion, then mark the file Y-up. Every node keeps rotation 0 / scale 1 in Unity.
R = Matrix.Rotation(-math.pi / 2, 4, 'X')
for ob in mesh_objs:
    ob.data.transform(R)
for r in roots:
    for c in r.children:
        c.location = R @ c.location

def set_int_prop(buf, name, value):
    key = b"S" + struct.pack("<I", len(name)) + name.encode()
    tail = b"S" + struct.pack("<I", 3) + b"int" + b"S" + struct.pack("<I", 7) + b"Integer" + b"S" + struct.pack("<I", 0) + b"I"
    i = buf.find(key + tail)
    assert i >= 0, name
    j = i + len(key) + len(tail)
    buf[j:j + 4] = struct.pack("<i", value)

for r in roots:
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in [r] + list(r.children):
        o.select_set(True)
    path = os.path.join(OUT, r.name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'MESH'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='Y', axis_up='Z', bake_space_transform=False,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
        path_mode='RELATIVE', embed_textures=False,
    )
    buf = bytearray(open(path, "rb").read())
    for k, v in (("UpAxis", 1), ("UpAxisSign", 1), ("FrontAxis", 2), ("FrontAxisSign", 1),
                 ("CoordAxis", 0), ("CoordAxisSign", 1), ("OriginalUpAxis", 1), ("OriginalUpAxisSign", 1)):
        set_int_prop(buf, k, v)
    open(path, "wb").write(buf)
print("EXPORTED")
