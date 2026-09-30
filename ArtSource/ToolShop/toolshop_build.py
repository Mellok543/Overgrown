"""ToolShop_Stand: shed tool wall with three purchasable tools.
Run: blender -b --factory-startup -P toolshop_build.py

Hierarchy (Unity):
  ToolShop_Stand            empty, base centre
    SickleSection           wall section mesh (+ secateurs, whetstone, twine)   -> Sickle  (pivot: blade/handle joint)
    TrimmerSection          wall section mesh (+ line spools, hedge shears)     -> Trimmer (pivot: main grip)
    MowerSection            wall section + pallet (+ jerrycan, oil can, blades) -> Mower   (pivot: wheel axle centre)
Blender is Z-up; FBX export bakes to Y-up (Unity rot 0, scale 1). Everything faces -Y (front)."""
import os, math, random
import bpy, bmesh
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\ToolShop"
NAME = "ToolShop_Stand"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(33)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette atlas (sRGB)
PALETTE = {
    "wood":        (150, 104, 64),
    "wood2":       (134, 94, 58),
    "wood_old":    (128, 114, 98),
    "wood_dark":   (84, 58, 38),
    "handle":      (188, 142, 88),
    "handle_dark": (140, 98, 58),
    "metal":       (122, 126, 130),
    "metal_edge":  (206, 210, 208),
    "metal_dark":  (64, 66, 70),
    "rust":        (128, 78, 46),
    "sign":        (208, 192, 154),
    "paint_dark":  (62, 48, 36),
    "green":       (78, 140, 52),
    "green_dark":  (52, 96, 38),
    "orange":      (226, 128, 36),
    "orange_dark": (164, 84, 28),
    "red":         (182, 58, 44),
    "red_dark":    (128, 40, 32),
    "black":       (40, 40, 42),
    "tire":        (46, 43, 41),
    "line":        (232, 214, 80),
    "stone":       (110, 118, 124),
    "twine":       (206, 184, 132),
    "blade":       (112, 158, 48),
    "yellow":      (232, 186, 60),
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
    a, b = Vector(a), Vector(b)
    d = b - a
    return box(name, (a + b) / 2, (thick, depth or thick, d.length + thick * 0.6), mat,
               rot=d.to_track_quat('Z', 'Y').to_euler(), bevel=bevel)

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

def cyl(name, a, b, r, n, mat, cap_mat=None):
    """Cylinder between points a and b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = lathe(name, [(r, 0.0), (r, d.length)], n, lambda j, i: mat, (0, 0, 0),
               cap_mats=(cap_mat or mat, cap_mat or mat))
    ob.matrix_world = Matrix.Translation(a) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    return ob

def ribbon(name, outer, inner, thick, mat):
    """Flat strip in the XZ plane between two polylines, extruded thick along Y."""
    bm = bmesh.new()
    h = thick / 2
    fo = [bm.verts.new((p[0], -h, p[1])) for p in outer]
    fi = [bm.verts.new((p[0], -h, p[1])) for p in inner]
    bo = [bm.verts.new((p[0], h, p[1])) for p in outer]
    bi = [bm.verts.new((p[0], h, p[1])) for p in inner]
    n = len(outer)
    for k in range(n - 1):
        bm.faces.new((fo[k], fo[k + 1], fi[k + 1], fi[k]))
        bm.faces.new((bo[k], bi[k], bi[k + 1], bo[k + 1]))
        bm.faces.new((fo[k], bo[k], bo[k + 1], fo[k + 1]))
        bm.faces.new((fi[k], fi[k + 1], bi[k + 1], bi[k]))
    bm.faces.new((fo[0], fi[0], bi[0], bo[0]))
    bm.faces.new((fo[-1], bo[-1], bi[-1], fi[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, [mat])

def decal(name, pts2d, y, mat, x0=0.0, z0=0.0):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x0 + x, y, z0 + z)) for x, z in pts2d])
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    return new_obj(name, bm, [mat])

def ring_decal(name, r_in, r_out, n, y, mat, x0, z0, a0=0.0, a1=math.tau):
    bm = bmesh.new()
    closed = abs(a1 - a0 - math.tau) < 1e-6
    cnt = n if closed else n + 1
    angs = [a0 + (a1 - a0) * i / n for i in range(cnt)]
    inner = [bm.verts.new((x0 + math.cos(a) * r_in, y, z0 + math.sin(a) * r_in)) for a in angs]
    outer = [bm.verts.new((x0 + math.cos(a) * r_out, y, z0 + math.sin(a) * r_out)) for a in angs]
    for i in range(n):
        i2 = (i + 1) % cnt
        f = bm.faces.new((inner[i], outer[i], outer[i2], inner[i2]))
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    return new_obj(name, bm, [mat])

def tuft(name, cx, cy, count, radius=0.06, h=(0.12, 0.28)):
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

def collect(name, pivot):
    """Join everything built since the last collect into one object whose origin is `pivot` (world)."""
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

# ---------------------------------------------------------------- wall section frame
PANEL_Y, PANEL_T = 0.10, 0.025
FRONT = PANEL_Y - PANEL_T / 2
WALL_H = 1.72
SIGN_Z = 1.80

def frame(cx, width, accent, accent_dark, tier):
    px = width / 2 - 0.05
    for sx in (-1, 1):
        x = cx + sx * px
        box(f"post{sx}", (x, PANEL_Y + 0.035, WALL_H / 2 + 0.05), (0.075, 0.075, WALL_H + 0.1), "wood_dark",
            rot=(jitter(0.01), jitter(0.01), 0), bevel=0.01)
        box(f"foot{sx}", (x, -0.05, 0.03), (0.08, 0.5, 0.06), "wood_dark", bevel=0.01)
        stick(f"brace{sx}", (x, -0.26, 0.05), (x, PANEL_Y + 0.01, 0.6), 0.045, "wood2", bevel=0.006)
    n = max(4, round((2 * px - 0.075) / 0.14))
    bw = (2 * px - 0.075) / n
    for k in range(n):
        x = cx - px + 0.0375 + bw * (k + 0.5)
        top = WALL_H - 0.02 + jitter(0.025)
        box(f"board{k}", (x, PANEL_Y + jitter(0.003), (0.1 + top) / 2), (bw - 0.008, PANEL_T, top - 0.1),
            rng.choice(["wood", "wood", "wood2", "wood_old"]))
    for z in (0.2, 1.62):
        box(f"crossrail{z}", (cx, PANEL_Y + 0.028, z), (2 * px, 0.03, 0.07), "wood_dark")
    # header plaque (icon + tier dots, no text) and little shed roof
    box("plaque", (cx, FRONT - 0.02, SIGN_Z), (0.5, 0.035, 0.26), "sign", rot=(0, jitter(0.02), 0), bevel=0.012)
    box("plaque_band", (cx, FRONT - 0.02, SIGN_Z - 0.145), (0.5, 0.04, 0.03), accent)
    half = width / 2 - 0.03
    for sx in (-1, 1):
        box(f"roof{sx}", (cx + sx * half / 2, 0.0, 2.0), (half * 1.02, 0.46, 0.03), accent_dark,
            rot=(0, sx * math.radians(14), 0), bevel=0.008)
    box("ridge", (cx, 0.0, 2.0 + half / 2 * math.tan(math.radians(14)) + 0.01), (0.06, 0.48, 0.04), "wood_dark", bevel=0.006)
    face = FRONT - 0.02 - 0.0175 - 0.003
    for k in range(tier):
        dx = (k - (tier - 1) / 2) * 0.045
        decal(f"tierdot{k}", [(-0.014, -0.014), (0.014, -0.014), (0.014, 0.014), (-0.014, 0.014)], face, accent_dark,
              x0=cx + dx, z0=SIGN_Z - 0.09)
    tuft("tuft_l", cx - px + 0.04, -0.2, 6)
    tuft("tuft_r", cx + px - 0.04, 0.0, 5, h=(0.1, 0.22))
    return face

def peg(name, x, z, length=0.08):
    stick(name, (x, FRONT, z), (x, FRONT - length, z + 0.015), 0.02, "wood_dark")

def bracket(name, x, z, depth=0.12):
    """Metal L-hook for tools."""
    stick(name + "_arm", (x, FRONT, z), (x, FRONT - depth, z), 0.018, "metal_dark")
    stick(name + "_tip", (x, FRONT - depth, z), (x, FRONT - depth, z + 0.05), 0.018, "metal_dark")

# ---------------------------------------------------------------- layout
SEC = {"Sickle": (-0.96, 0.8), "Trimmer": (-0.10, 0.8), "Mower": (0.86, 1.0)}
objects = {}

# ================================================================ 1) SICKLE section
cx, w = SEC["Sickle"]
face = frame(cx, w, "green", "green_dark", 1)
# icon: crescent blade + handle
ring_decal("icon_blade", 0.06, 0.092, 8, face, "metal_dark", cx + 0.03, SIGN_Z + 0.025, a0=math.radians(-10), a1=math.radians(200))
decal("icon_handle", [(-0.016, 0.0), (0.016, 0.0), (0.016, -0.08), (-0.016, -0.08)], face, "handle_dark",
      x0=cx - 0.046, z0=SIGN_Z + 0.02)
# small shelf with whetstone + twine
box("shelf", (cx, FRONT - 0.1, 0.72), (w - 0.18, 0.2, 0.03), "wood2", bevel=0.006)
for sx in (-1, 1):
    stick(f"shelf_bracket{sx}", (cx + sx * 0.25, FRONT, 0.6), (cx + sx * 0.25, FRONT - 0.17, 0.71), 0.03, "wood_dark")
box("whetstone", (cx - 0.14, FRONT - 0.1, 0.755), (0.16, 0.05, 0.04), "stone", rot=(0, 0, 0.15), bevel=0.01)
lathe("twine", [(0.0, -0.05), (0.04, -0.045), (0.055, -0.02), (0.055, 0.02), (0.04, 0.045), (0.0, 0.05)], 8,
      lambda j, i: "twine", (cx + 0.12, FRONT - 0.1, 0.735 + 0.05), noise=0.04)
# secateurs hanging on a peg
sx0, sz0 = cx + 0.2, 1.08
peg("sec_peg", sx0, sz0 + 0.02)
for s in (-1, 1):
    stick(f"sec_handle{s}", (sx0, FRONT - 0.06, sz0), (sx0 + s * 0.04, FRONT - 0.06 - 0.004 * s, sz0 - 0.17), 0.022, "red", bevel=0.005)
    stick(f"sec_blade{s}", (sx0, FRONT - 0.06, sz0), (sx0 - s * 0.015, FRONT - 0.06 - 0.004 * s, sz0 + 0.07), 0.018, "metal", depth=0.008)
path("sec_spring", [(sx0 - 0.02, FRONT - 0.06, sz0 - 0.04), (sx0, FRONT - 0.06, sz0 - 0.02), (sx0 + 0.02, FRONT - 0.06, sz0 - 0.04)], 0.008, "metal_dark")
peg("sickle_peg_a", cx - 0.085, 1.27)
peg("sickle_peg_b", cx + 0.1, 1.38)
sickle_section = collect("SickleSection", (cx, 0, 0))

# the sickle itself (hangs on the two pegs), pivot at blade/handle joint
J = Vector((cx - 0.12, FRONT - 0.07, 1.12))
S = 1.25                      # slightly oversized for readability
R = 0.16 * S
C = Vector((J.x + 0.13 * S, J.z + 0.09 * S))
outer, mid, inner = [], [], []
N = 12
a0, a1 = math.radians(205), math.radians(-18)
for k in range(N + 1):
    t = k / N
    a = a0 + (a1 - a0) * t
    d = Vector((math.cos(a), math.sin(a)))
    wdt = (0.06 * (1 - t) ** 0.7 + 0.005) * S
    outer.append(C + d * R)
    mid.append(C + d * (R - wdt * 0.5))
    inner.append(C + d * (R - wdt))
ribbon("sickle_spine", outer, mid, 0.007, "metal")
ribbon("sickle_edge", mid, inner, 0.005, "metal_edge")
# tang from handle to the blade root
start = outer[0]
ribbon("sickle_tang", [(J.x - 0.012, J.z + 0.01), (start.x - 0.004, start.y)],
       [(J.x + 0.012, J.z + 0.01), (inner[0].x + 0.004, inner[0].y)], 0.008, "metal_dark")
for ob in parts[-3:]:
    ob.location.y = J.y
lathe("sickle_handle", [(0.0, 0.0), (0.02, 0.0), (0.024, 0.05), (0.022, 0.17), (0.026, 0.24), (0.0, 0.245)], 6,
      lambda j, i: "handle" if j else "metal_dark", (J.x, J.y, J.z + 0.012), rot=(math.pi, 0, 0), scale=(S, S, S))
lathe("sickle_ferrule", [(0.026, 0.0), (0.026, 0.025)], 6, lambda j, i: "metal_dark", (J.x, J.y, J.z - 0.012),
      scale=(S, S, 1), cap_bottom=False, cap_top=False)
sickle = collect("Sickle", J)

# ================================================================ 2) TRIMMER section
cx, w = SEC["Trimmer"]
face = frame(cx, w, "orange", "orange_dark", 2)
# icon: shaft line + head disc + motor block
stick("icon_shaft", (cx - 0.08, face, SIGN_Z + 0.08), (cx + 0.05, face, SIGN_Z - 0.035), 0.026, "metal_dark", depth=0.002)
ring_decal("icon_head", 0.0, 0.048, 8, face - 0.001, "orange_dark", cx + 0.065, SIGN_Z - 0.045)
decal("icon_motor", [(-0.035, -0.025), (0.035, -0.025), (0.035, 0.035), (-0.035, 0.035)], face - 0.001, "orange",
      x0=cx - 0.09, z0=SIGN_Z + 0.08)
# line spools on a peg + hedge shears
peg("spool_peg", cx + 0.25, 1.35)
for k in range(2):
    lathe(f"spool{k}", [(0.0, -0.022), (0.05, -0.022), (0.05, -0.014), (0.036, -0.012), (0.036, 0.012),
                        (0.05, 0.014), (0.05, 0.022), (0.0, 0.022)], 10,
          lambda j, i: "line" if j in (3, 4) else "black", (cx + 0.25, FRONT - 0.03 - k * 0.046, 1.3),
          rot=(math.pi / 2, 0, 0))
hx, hz = cx + 0.24, 0.95
peg("shears_peg", hx, hz + 0.02)
for s in (-1, 1):
    stick(f"shears_handle{s}", (hx, FRONT - 0.06, hz), (hx + s * 0.07, FRONT - 0.06 - 0.005 * s, hz - 0.3), 0.026, "handle_dark", bevel=0.006)
    box(f"shears_grip{s}", (hx + s * 0.063, FRONT - 0.06 - 0.005 * s, hz - 0.25), (0.036, 0.036, 0.1), "black",
        rot=(0, -s * 0.23, 0), bevel=0.008)
    stick(f"shears_blade{s}", (hx, FRONT - 0.06 - 0.005 * s, hz), (hx - s * 0.03, FRONT - 0.06 - 0.005 * s, hz + 0.26), 0.035, "metal", depth=0.008)
bracket("trim_hook_top", cx - 0.08, 1.30)
bracket("trim_hook_low", cx - 0.08, 0.7, depth=0.1)
trimmer_section = collect("TrimmerSection", (cx, 0, 0))

# the trimmer (hangs vertically, head down), pivot at the main grip
tx, ty = cx - 0.08, FRONT - 0.11
GRIP = Vector((tx, ty, 1.36))
cyl("trim_shaft", (tx, ty, 0.52), (tx, ty, 1.3), 0.017, 6, "metal_dark")
# rear housing / battery with trigger grip
box("trim_housing", (tx, ty, 1.47), (0.085, 0.1, 0.2), "orange", bevel=0.02)
box("trim_battery", (tx, ty + 0.035, 1.6), (0.07, 0.07, 0.08), "black", bevel=0.012)
box("trim_grip", (tx, ty - 0.055, 1.36), (0.035, 0.05, 0.13), "black", rot=(0.25, 0, 0), bevel=0.01)
box("trim_trigger", (tx, ty - 0.085, 1.39), (0.018, 0.02, 0.04), "orange_dark")
box("trim_collar", (tx, ty, 1.33), (0.05, 0.05, 0.05), "orange_dark", bevel=0.008)
# front D-handle
dz = 1.08
path("trim_dhandle", [(tx, ty, dz), (tx, ty - 0.05, dz + 0.05), (tx, ty - 0.14, dz + 0.07), (tx, ty - 0.16, dz - 0.02),
                      (tx, ty - 0.1, dz - 0.07), (tx, ty, dz)], 0.022, "black")
box("trim_clamp", (tx, ty, dz), (0.045, 0.045, 0.05), "orange_dark", bevel=0.006)
# bent neck + motor head + guard + spool + line
neck_a, neck_b = Vector((tx, ty, 0.52)), Vector((tx, ty - 0.08, 0.40))
cyl("trim_neck", neck_a, neck_b, 0.017, 6, "metal_dark")
lathe("trim_motor", [(0.0, 0.0), (0.045, 0.0), (0.05, 0.05), (0.04, 0.1), (0.0, 0.11)], 8,
      lambda j, i: "orange", (neck_b.x, neck_b.y, neck_b.z - 0.1), rot=(0.55, 0, 0))
head = Vector((neck_b.x, neck_b.y - 0.02, neck_b.z - 0.11))
lathe("trim_spool", [(0.0, -0.02), (0.055, -0.02), (0.06, 0.0), (0.055, 0.02), (0.0, 0.02)], 10,
      lambda j, i: "black", head, rot=(0.55, 0, 0))
ring_prof = [(0.0, 0.0), (0.13, 0.0), (0.13, 0.008), (0.0, 0.008)]
guard = lathe("trim_guard", ring_prof, 10, lambda j, i: "orange_dark", (head.x, head.y + 0.03, head.z + 0.035), rot=(0.55, 0, 0),
              scale=(1.0, 0.55, 1.0))
for s in (-1, 1):
    stick(f"trim_line{s}", head, (head.x + s * 0.11, head.y - 0.02, head.z - 0.04), 0.008, "line")
trimmer = collect("Trimmer", GRIP)

# ================================================================ 3) MOWER section
cx, w = SEC["Mower"]
face = frame(cx, w, "red", "red_dark", 3)
# icon: mower body + two wheels + handle
decal("icon_body", [(-0.06, -0.02), (0.05, -0.02), (0.05, 0.02), (-0.06, 0.02)], face, "red", x0=cx - 0.02, z0=SIGN_Z - 0.02)
for k, x in enumerate((-0.06, 0.04)):
    ring_decal(f"icon_wheel{k}", 0.0, 0.025, 8, face - 0.001, "black", cx + x - 0.01, SIGN_Z - 0.045)
stick("icon_handle", (cx + 0.02, face, SIGN_Z), (cx + 0.1, face, SIGN_Z + 0.09), 0.014, "metal_dark", depth=0.002)
# pallet in front of the wall
PAL_TOP = 0.12
for k in range(5):
    box(f"pallet_top{k}", (cx, -0.62 + k * 0.17, PAL_TOP - 0.015), (w - 0.06, 0.13, 0.03), rng.choice(["wood", "wood2", "wood_old"]), bevel=0.005)
for k, y in enumerate((-0.6, -0.26, 0.06)):
    box(f"pallet_block{k}", (cx, y, PAL_TOP / 2 - 0.015), (w - 0.06, 0.1, PAL_TOP - 0.03), "wood_dark", bevel=0.006)
# jerrycan and oil can on the pallet
jc = Vector((cx + 0.36, -0.1, PAL_TOP))
box("jerry_body", (jc.x, jc.y, jc.z + 0.16), (0.1, 0.24, 0.32), "red", rot=(0, 0, 0.2), bevel=0.02)
box("jerry_handle", (jc.x, jc.y + 0.02, jc.z + 0.345), (0.03, 0.12, 0.03), "red_dark", rot=(0, 0, 0.2), bevel=0.006)
cyl("jerry_spout", (jc.x + 0.01, jc.y - 0.08, jc.z + 0.32), (jc.x + 0.01, jc.y - 0.13, jc.z + 0.38), 0.016, 6, "black")
oc = Vector((cx - 0.38, -0.55, PAL_TOP))
lathe("oilcan", [(0.0, 0.0), (0.05, 0.0), (0.055, 0.06), (0.03, 0.1), (0.012, 0.12), (0.0, 0.12)], 8,
      lambda j, i: "yellow" if j < 2 else "metal", oc)
cyl("oil_spout", (oc.x, oc.y, oc.z + 0.11), (oc.x + 0.02, oc.y - 0.1, oc.z + 0.2), 0.006, 4, "metal")
# spare reel blades + wrench on the wall
for k in range(2):
    peg(f"blade_peg{k}", cx - 0.3 + k * 0.1, 1.35)
    box(f"spare_blade{k}", (cx - 0.3 + k * 0.1, FRONT - 0.04, 1.12), (0.04, 0.008, 0.42), "metal", rot=(0, 0.05 * (k - 0.5), 0))
    box(f"spare_edge{k}", (cx - 0.3 + k * 0.1 + 0.018, FRONT - 0.045, 1.12), (0.008, 0.009, 0.42), "metal_edge", rot=(0, 0.05 * (k - 0.5), 0))
peg("wrench_peg", cx + 0.3, 1.4)
stick("wrench", (cx + 0.3, FRONT - 0.05, 1.38), (cx + 0.3, FRONT - 0.05, 1.15), 0.025, "metal_dark", depth=0.01)
ring_decal("wrench_jaw", 0.012, 0.03, 6, FRONT - 0.056, "metal_dark", cx + 0.3, 1.13, a0=math.radians(-60), a1=math.radians(240))
mower_section = collect("MowerSection", (cx, 0, 0))

# the push reel mower on the pallet, facing front, handle leaning back to the wall; pivot at axle centre
WR = 0.13
AX = Vector((cx - 0.05, -0.36, PAL_TOP + WR))
for s in (-1, 1):
    wx = AX.x + s * 0.24
    lathe(f"wheel{s}", [(0.0, -0.03), (0.08, -0.03), (0.11, -0.04), (WR, -0.025), (WR, 0.025), (0.11, 0.04),
                        (0.08, 0.03), (0.0, 0.03)], 12, lambda j, i: "tire" if 1 <= j <= 5 else "red",
          (wx, AX.y, AX.z), rot=(0, math.pi / 2, 0))
    # side plate from hub to the rear roller
    stick(f"sideplate{s}", (AX.x + s * 0.2, AX.y, AX.z), (AX.x + s * 0.2, AX.y + 0.17, AX.z - 0.09), 0.05, "red", depth=0.02)
cyl("axle", (AX.x - 0.23, AX.y, AX.z), (AX.x + 0.23, AX.y, AX.z), 0.012, 6, "metal_dark")
# reel: end discs + 5 twisted blades
for s in (-1, 1):
    lathe(f"reel_disc{s}", [(0.0, -0.006), (0.085, -0.006), (0.085, 0.006), (0.0, 0.006)], 10,
          lambda j, i: "red_dark", (AX.x + s * 0.17, AX.y, AX.z), rot=(0, math.pi / 2, 0))
for k in range(5):
    a = math.tau * k / 5
    a2 = a + 0.5
    p1 = (AX.x - 0.17, AX.y + math.cos(a) * 0.08, AX.z + math.sin(a) * 0.08)
    p2 = (AX.x + 0.17, AX.y + math.cos(a2) * 0.08, AX.z + math.sin(a2) * 0.08)
    stick(f"reel_blade{k}", p1, p2, 0.012, "metal_edge" if k % 2 else "metal", depth=0.03)
cyl("roller", (AX.x - 0.2, AX.y + 0.17, AX.z - 0.09), (AX.x + 0.2, AX.y + 0.17, AX.z - 0.09), 0.035, 8, "black")
box("bedknife", (AX.x, AX.y - 0.05, AX.z - 0.1), (0.36, 0.05, 0.012), "metal_dark", rot=(0.3, 0, 0))
box("front_guard", (AX.x, AX.y - 0.1, AX.z + 0.02), (0.36, 0.015, 0.1), "red", rot=(-0.25, 0, 0), bevel=0.006)
# handle: two tubes into a T-bar near the wall
top = Vector((AX.x, FRONT - 0.12, 1.02))
for s in (-1, 1):
    a = Vector((AX.x + s * 0.2, AX.y + 0.02, AX.z + 0.02))
    m = Vector((AX.x + s * 0.06, (AX.y + top.y) / 2 + 0.05, (AX.z + top.z) / 2 + 0.04))
    cyl(f"handle_low{s}", a, m, 0.014, 6, "metal_dark")
    cyl(f"handle_up{s}", m, (top.x + s * 0.03, top.y, top.z), 0.014, 6, "metal_dark")
cyl("tbar", (top.x - 0.24, top.y, top.z), (top.x + 0.24, top.y, top.z), 0.016, 6, "metal_dark")
for s in (-1, 1):
    cyl(f"tgrip{s}", (top.x + s * 0.12, top.y, top.z), (top.x + s * 0.25, top.y, top.z), 0.024, 6, "black")
box("handle_brace", ((AX.x + top.x) / 2, (AX.y + top.y) / 2 + 0.05, (AX.z + top.z) / 2 + 0.04), (0.14, 0.02, 0.03), "red_dark",
    rot=(math.atan2(top.y - AX.y, top.z - AX.z) * -1, 0, 0))
mower = collect("Mower", AX)

# ---------------------------------------------------------------- hierarchy
root = bpy.data.objects.new(NAME, None)
scene.collection.objects.link(root)
root.empty_display_size = 0.3
def parent(child, par):
    world = child.matrix_world.translation.copy()
    child.parent = par
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.location = world - par.matrix_world.translation
for sec in (sickle_section, trimmer_section, mower_section):
    parent(sec, root)
bpy.context.view_layer.update()
parent(sickle, sickle_section)
parent(trimmer, trimmer_section)
parent(mower, mower_section)
bpy.context.view_layer.update()

# ---------------------------------------------------------------- palette atlas, UVs, triangulate, one material
img = bpy.data.images.new(NAME + "_Atlas", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(KEYS):
    ccx, ccy = idx % PAL_GRID, idx // PAL_GRID
    col = [c / 255 for c in PALETTE[k]]
    for y in range(ccy * PAL_CELL, (ccy + 1) * PAL_CELL):
        for x in range(ccx * PAL_CELL, (ccx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (*col, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, NAME + "_Atlas.png")
img.file_format = 'PNG'
img.save()

final = bpy.data.materials.new("M_ToolShop")
final.use_nodes = True
nt = final.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
bsdf.inputs["Metallic"].default_value = 0.0

mesh_objs = [sickle_section, sickle, trimmer_section, trimmer, mower_section, mower]
total = 0
for ob in mesh_objs:
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
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free(); me.update()
    tris = len(me.polygons)
    total += tris
    wmin = min((ob.matrix_world @ v.co).z for v in me.vertices)
    print(f"OBJ {ob.name:15s} parent={ob.parent.name if ob.parent else '-':15s} tris={tris:5d} "
          f"local={tuple(round(c, 3) for c in ob.location)} dims=({ob.dimensions.x:.2f},{ob.dimensions.y:.2f},{ob.dimensions.z:.2f}) minZ={wmin:.3f}")
print(f"TOTAL tris={total}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, NAME + ".blend"))

# ---------------------------------------------------------------- preview renders
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.85, 0.15, -0.45))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=12)
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.10, 0.06, 1)
bpy.context.object.data.materials.append(g)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C"); cam_data.lens = 35
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
for tag, loc, target, res in (("front", (0.8, -4.3, 1.6), (0, 0, 1.0), (1400, 850)),
                              ("sickle_trimmer", (-0.3, -1.9, 1.35), (-0.55, 0, 1.05), (1000, 850)),
                              ("mower", (1.9, -2.0, 1.2), (0.85, -0.2, 0.55), (1000, 850))):
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED")

# ---------------------------------------------------------------- export
# Blender's bake_space_transform mishandles grandchildren (Sickle/Trimmer/Mower got 90 deg rotations),
# so convert to Y-up ourselves: rotate mesh data and local offsets by -90 deg about X, export with no axis
# conversion, then mark the file as Y-up in GlobalSettings. Result: every node has rotation 0 / scale 1.
import struct
for o in bpy.context.selected_objects:
    o.select_set(False)
R = Matrix.Rotation(-math.pi / 2, 4, 'X')
for ob in mesh_objs:
    ob.data.transform(R)
for ob in [root] + mesh_objs:
    ob.location = R @ ob.location
for o in [root] + mesh_objs:
    o.select_set(True)
fbx_path = os.path.join(OUT, NAME + ".fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True, object_types={'EMPTY', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='Y', axis_up='Z', bake_space_transform=False,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
    path_mode='RELATIVE', embed_textures=False,
)

def set_int_prop(buf, name, value):
    key = b"S" + struct.pack("<I", len(name)) + name.encode()
    tail = b"S\x03\x00\x00\x00intS\x07\x00\x00\x00IntegerS\x00\x00\x00\x00I"
    i = buf.find(key + tail)
    assert i >= 0, name
    j = i + len(key) + len(tail)
    buf[j:j + 4] = struct.pack("<i", value)

buf = bytearray(open(fbx_path, "rb").read())
for k, v in (("UpAxis", 1), ("UpAxisSign", 1), ("FrontAxis", 2), ("FrontAxisSign", 1),
             ("CoordAxis", 0), ("CoordAxisSign", 1), ("OriginalUpAxis", 1), ("OriginalUpAxisSign", 1)):
    set_int_prop(buf, k, v)
open(fbx_path, "wb").write(buf)
print("EXPORTED")
