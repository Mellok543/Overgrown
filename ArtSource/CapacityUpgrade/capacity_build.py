"""CapacityUpgrade_Stand: stylized low-poly garden stand with carry upgrades.
Run: blender -b --factory-startup -P capacity_build.py
Shelves by tier: top = small sack + tote (1), middle = big sack + basket (2), bottom = hand cart (3).
Blender is Z-up here; FBX export converts to Y-up with transforms baked (Unity: rot 0, scale 1)."""
import os, math, random
import bpy, bmesh
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\CapacityUpgrade"
NAME = "CapacityUpgrade_Stand"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(9)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette atlas (sRGB)
PALETTE = {
    "wood":        (150, 104, 64),
    "wood2":       (134, 94, 58),
    "wood_old":    (128, 114, 98),
    "wood_dark":   (84, 58, 38),
    "burlap":      (196, 160, 105),
    "burlap_dark": (158, 124, 80),
    "patch":       (112, 134, 88),
    "rope":        (206, 184, 132),
    "canvas":      (96, 128, 80),
    "canvas_dark": (70, 96, 60),
    "strap":       (96, 70, 46),
    "basket":      (184, 134, 72),
    "basket_dark": (140, 96, 50),
    "cart_red":    (178, 66, 48),
    "cart_red_dk": (130, 46, 36),
    "tire":        (46, 43, 41),
    "metal":       (86, 88, 92),
    "sign":        (206, 190, 152),
    "paint":       (58, 108, 38),
    "paint_dark":  (62, 48, 36),
    "tag":         (232, 222, 190),
    "grass":       (92, 124, 40),
    "blade":       (112, 158, 48),
    "cloth_a":     (176, 92, 70),
    "cloth_b":     (212, 190, 120),
}
PAL_GRID, PAL_CELL = 8, 8
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)
MATS = {k: bpy.data.materials.new("tmp_" + k) for k in KEYS}
parts = []

def jitter(a):
    return rng.uniform(-a, a)

def new_obj(name, bm, mats):
    """mats: list of palette keys; faces carry material_index into it."""
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

def lathe(name, profile, n, mat_fn, center, rot=(0, 0, 0), scale=(1, 1, 1), noise=0.0,
          cap_bottom=True, cap_top=True, phase=0.0, cap_mats=None):
    """Revolve (r, z) profile around Z. r == 0 -> pole. mat_fn(row, seg) -> palette key."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for i in range(n):
            a = phase + math.tau * i / n
            rr = r * (1 + jitter(noise))
            ring.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z + jitter(noise * 0.25 * r))))
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

def flat_poly(name, pts2d, y, mat, x0=0.0, z0=0.0):
    """Painted decal polygon in the XZ plane at depth y, facing -Y (the front)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x0 + x, y, z0 + z)) for x, z in pts2d]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    return new_obj(name, bm, [mat])

def tube_path(name, pts, thick, mat):
    """Chain of thin boxes along points (handles, ropes)."""
    for k in range(len(pts) - 1):
        a, b = Vector(pts[k]), Vector(pts[k + 1])
        d = b - a
        rot = d.to_track_quat('Z', 'Y').to_euler()
        box(f"{name}{k}", (a + b) / 2, (thick, thick, d.length + thick * 0.8), mat, rot=rot)

def blades(name, center, radius, count, z, h_range):
    bm = bmesh.new()
    cx, cy = center
    for _ in range(count):
        ang = rng.uniform(0, math.tau)
        r = radius * math.sqrt(rng.random())
        base = Vector((cx + math.cos(ang) * r, cy + math.sin(ang) * r, z))
        h = rng.uniform(*h_range)
        lean = Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(0.03, 0.10)
        side = Vector((-math.sin(ang + 1.1), math.cos(ang + 1.1), 0)) * rng.uniform(0.012, 0.02)
        mid = base + Vector((0, 0, h * 0.55)) + lean * 0.35
        tip = base + Vector((0, 0, h)) + lean
        for flip in (False, True):
            v = [bm.verts.new(p) for p in (base - side, base + side, mid + side * 0.6, mid - side * 0.6, tip)]
            for f in ((v[0], v[1], v[2], v[3]), (v[3], v[2], v[4])):
                bm.faces.new(tuple(reversed(f)) if flip else f)
    return new_obj(name, bm, ["blade"])

# ---------------------------------------------------------------- stand frame
PX, PY, POST = 0.58, 0.26, 0.07
POST_H = 1.50
SHELF_Z = [0.14, 0.62, 1.08]         # plank centres
SHELF_T = 0.04
wood_pick = lambda: rng.choice(["wood", "wood", "wood2", "wood_old"])

for sx in (-1, 1):
    for sy in (-1, 1):
        h = POST_H + (0.25 if sy == 1 else 0.0)          # back posts carry the sign
        box(f"post{sx}{sy}", (sx * PX, sy * PY, h / 2), (POST, POST, h), "wood_dark", rot=(jitter(0.01), jitter(0.01), 0), bevel=0.01)

for si, z in enumerate(SHELF_Z):
    # side rails holding the shelf
    for sx in (-1, 1):
        box(f"rail{si}{sx}", (sx * (PX - 0.005), 0, z - SHELF_T / 2 - 0.025), (0.05, 2 * PY + POST, 0.05), "wood_dark", bevel=0.008)
    # shelf planks along X
    for k in range(3):
        y = -0.18 + k * 0.18
        box(f"shelf{si}{k}", (jitter(0.01), y, z + jitter(0.004)), (2 * PX + POST + 0.04 + jitter(0.02), 0.17, SHELF_T),
            wood_pick(), rot=(0, 0, jitter(0.01)), bevel=0.008)
    # back lip
    box(f"lip{si}", (0, PY + 0.02, z + 0.06), (2 * PX, 0.025, 0.08), wood_pick(), bevel=0.006)

# diagonal back brace
a, b = Vector((-PX, PY + 0.045, 0.2)), Vector((PX, PY + 0.045, 1.0))
d = b - a
box("brace", (a + b) / 2, (0.05, 0.022, d.length), "wood2", rot=d.to_track_quat('Z', 'Y').to_euler(), bevel=0.006)

# ---------------------------------------------------------------- main sign with icon: sack + up arrow
SIGN_Z, SIGN_Y = 1.62, PY - 0.045
box("sign", (0, SIGN_Y, SIGN_Z), (0.86, 0.035, 0.26), "sign", rot=(0, math.radians(-1.2), 0), bevel=0.012)
box("sign_top", (0, SIGN_Y, SIGN_Z + 0.14), (0.92, 0.05, 0.03), "wood_dark", bevel=0.006)
fy = SIGN_Y - 0.035 / 2 - 0.004
sack_icon = [(-0.09, -0.08), (0.09, -0.08), (0.11, -0.02), (0.08, 0.04), (0.035, 0.065), (0.06, 0.1),
             (-0.06, 0.1), (-0.035, 0.065), (-0.08, 0.04), (-0.11, -0.02)]
flat_poly("icon_sack", sack_icon, fy, "burlap_dark", x0=-0.13, z0=SIGN_Z - 0.01)
flat_poly("icon_tie", [(-0.04, 0.055), (0.04, 0.055), (0.04, 0.072), (-0.04, 0.072)], fy - 0.002, "paint_dark", x0=-0.13, z0=SIGN_Z - 0.01)
flat_poly("icon_arrow_head", [(-0.075, 0.0), (0.075, 0.0), (0.0, 0.09)], fy, "paint", x0=0.15, z0=SIGN_Z + 0.01)
flat_poly("icon_arrow_stem", [(-0.03, -0.1), (0.03, -0.1), (0.03, 0.001), (-0.03, 0.001)], fy, "paint", x0=0.15, z0=SIGN_Z + 0.01)

# tier tags on shelf fronts: 1 / 2 / 3 dots
for tier, z in zip((3, 2, 1), SHELF_Z):
    ty = -0.18 - 0.085 - 0.012
    tz = z - 0.045
    box(f"tag{tier}", (-0.46, ty, tz), (0.17, 0.012, 0.075), "tag", bevel=0.004)
    for k in range(tier):
        dx = (k - (tier - 1) / 2) * 0.045
        flat_poly(f"dot{tier}{k}", [(-0.013, -0.013), (0.013, -0.013), (0.013, 0.013), (-0.013, 0.013)],
                  ty - 0.0075, "paint_dark", x0=-0.46 + dx, z0=tz)

# ---------------------------------------------------------------- props
top = lambda si: SHELF_Z[si] + SHELF_T / 2

# squat lumpy sack, bunched cloth tied with rope, floppy gathered top
SACK = [(0.21, 0.0), (0.26, 0.06), (0.27, 0.16), (0.24, 0.25), (0.15, 0.31), (0.095, 0.34),
        (0.095, 0.37), (0.13, 0.41), (0.08, 0.44), (0.0, 0.43)]
def sack_mats(patch_seg=None):
    def f(j, i):
        if j in (4, 5):
            return "rope"
        if patch_seg is not None and j == 1 and i == patch_seg:
            return "patch"
        return "burlap" if j < 6 else "burlap_dark"
    return f

# tier 1 (top shelf): small sack, tote bag with grass, folded cloth
lathe("sack_small", SACK, 10, sack_mats(), (-0.3, -0.02, top(2)), rot=(0, 0, 0.4), scale=(0.62, 0.55, 0.6), noise=0.09)

TOTE = [(0.20, 0.0), (0.215, 0.24), (0.195, 0.24), (0.18, 0.03)]
tote_c = Vector((0.2, -0.02, top(2)))
lathe("tote", TOTE, 4, lambda j, i: "canvas" if j == 0 else "canvas_dark", tote_c,
      rot=(0, 0, 0.12), scale=(1.35, 0.6, 1.0), phase=math.pi / 4, cap_mats=("canvas_dark", "canvas_dark"))
for s in (-1, 1):
    hy = tote_c.y + s * 0.07
    pts = [(tote_c.x - 0.09, hy, top(2) + 0.23), (tote_c.x - 0.06, hy, top(2) + 0.33),
           (tote_c.x + 0.06, hy, top(2) + 0.33), (tote_c.x + 0.09, hy, top(2) + 0.23)]
    tube_path(f"tote_strap{s}", pts, 0.018, "strap")
blades("tote_grass", (tote_c.x, tote_c.y), 0.08, 9, top(2) + 0.12, (0.18, 0.28))
box("cloth1", (0.47, 0.02, top(2) + 0.025), (0.2, 0.26, 0.05), "cloth_a", rot=(0, 0, -0.1), bevel=0.012)
box("cloth2", (0.47, 0.02, top(2) + 0.07), (0.18, 0.24, 0.04), "cloth_b", rot=(0, 0, 0.08), bevel=0.012)

# tier 2 (middle shelf): big sack, woven basket with grass
lathe("sack_big", SACK, 12, sack_mats(patch_seg=9), (-0.28, 0.0, top(1)), rot=(0, 0, -0.3), scale=(0.95, 0.85, 0.82), noise=0.09)

BASKET = [(0.15, 0.0), (0.18, 0.08), (0.205, 0.17), (0.22, 0.24), (0.235, 0.255),
          (0.21, 0.25), (0.185, 0.15), (0.14, 0.03)]
def basket_mat(j, i):
    if j >= 3:
        return "basket_dark"
    return "basket" if (i + j) % 2 else "basket_dark"
bc = Vector((0.27, -0.01, top(1)))
lathe("basket", BASKET, 14, basket_mat, bc, noise=0.015, cap_mats=("basket_dark", "basket_dark"))
arc = [(bc.x + math.cos(t) * 0.2, bc.y, top(1) + 0.245 + math.sin(t) * 0.16) for t in [math.pi * k / 6 for k in range(7)]]
tube_path("basket_handle", arc, 0.022, "basket_dark")
blades("basket_grass", (bc.x, bc.y), 0.15, 12, top(1) + 0.14, (0.14, 0.24))

# tier 3 (bottom shelf): hand cart - tub, spare wheel, handles leaning on the side
TUB = [(0.19, 0.0), (0.27, 0.2), (0.25, 0.2), (0.17, 0.025)]
lathe("cart_tub", TUB, 4, lambda j, i: "cart_red" if j == 0 else "cart_red_dk", (0.18, 0.0, top(0) + 0.035),
      rot=(0, 0, 0.05), scale=(1.25, 0.95, 1.0), phase=math.pi / 4, cap_mats=("cart_red_dk", "cart_red_dk"))
for sx in (-1, 1):          # little feet under the tub
    box(f"tub_foot{sx}", (0.18 + sx * 0.14, 0.0, top(0) + 0.018), (0.04, 0.26, 0.036), "metal")
WHEEL = [(0.0, -0.035), (0.10, -0.035), (0.145, -0.045), (0.17, -0.028), (0.17, 0.028),
         (0.145, 0.045), (0.10, 0.035), (0.0, 0.035)]
wheel_mat = lambda j, i: "tire" if 1 <= j <= 5 else "cart_red"
lathe("wheel", WHEEL, 12, wheel_mat, (-0.33, -0.02, top(0) + 0.175), rot=(math.pi / 2, 0, 0.35))
box("axle", (-0.33, -0.02, top(0) + 0.175), (0.03, 0.03, 0.14), "metal", rot=(math.pi / 2, 0, 0.35))
for k, y in enumerate((-0.14, 0.06)):
    a = Vector((PX + 0.14, y, 0.02)); b = Vector((PX + 0.05, y + 0.02, 0.86))
    d = b - a
    box(f"cart_handle{k}", (a + b) / 2, (0.035, 0.035, d.length), "wood2", rot=d.to_track_quat('Z', 'Y').to_euler(), bevel=0.006)
    box(f"cart_grip{k}", b + d.normalized() * 0.03, (0.045, 0.045, 0.1), "strap", rot=d.to_track_quat('Z', 'Y').to_euler(), bevel=0.008)

# ---------------------------------------------------------------- hanging bits on the sides (hooks, rope, sack)
for sx in (-1, 1):
    hx = sx * (PX + POST / 2 + 0.03)
    box(f"hook_arm{sx}", (hx, -0.1, 1.36), (0.06, 0.018, 0.018), "metal")
    box(f"hook_tip{sx}", (hx + sx * 0.025, -0.1, 1.38), (0.016, 0.016, 0.05), "metal")
# left: small sack hanging on a rope
lx = -(PX + POST / 2 + 0.06)
tube_path("hang_rope", [(lx, -0.1, 1.37), (lx - 0.01, -0.1, 1.24)], 0.014, "rope")
lathe("sack_hang", SACK, 10, sack_mats(), (lx - 0.03, -0.1, 0.98), rot=(0, 0.06, 0), scale=(0.42, 0.36, 0.56), noise=0.09)
# right: coil of rope (torus in the YZ plane)
R, r, N, M = 0.11, 0.022, 12, 6
ring_prof = [(R + r * math.cos(math.tau * k / M), r * math.sin(math.tau * k / M)) for k in range(M + 1)]
lathe("rope_coil", ring_prof, N, lambda j, i: "rope" if (i + j) % 3 else "burlap_dark",
      (PX + POST / 2 + 0.05, -0.1, 1.27), rot=(0, math.pi / 2, 0), cap_bottom=False, cap_top=False)

# ---------------------------------------------------------------- join, palette UVs, single material
for ob in parts:
    ob.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = ob.data.name = NAME
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

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
final = bpy.data.materials.new("M_CapacityUpgrade")
final.use_nodes = True
nt = final.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
bsdf.inputs["Metallic"].default_value = 0.0
me.materials.clear(); me.materials.append(final)

# pivot: structural centre on the ground (z min -> 0)
zmin = min(v.co.z for v in me.vertices)
for v in me.vertices:
    v.co.z -= zmin
me.update()

tris = sum(len(p.vertices) - 2 for p in me.polygons)
d = ob.dimensions
print(f"STAND tris={tris} W={d.x:.2f} D={d.y:.2f} H={d.z:.2f}")

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
bpy.ops.object.light_add(type='SUN', rotation=(0.8, 0.2, -0.5))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=8)
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.10, 0.06, 1)
bpy.context.object.data.materials.append(g)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 800, 900
cam_data = bpy.data.cameras.new("C"); cam_data.lens = 35
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
for tag, loc in (("front", (1.2, -2.9, 1.6)), ("side", (-2.6, -1.3, 1.4))):
    cam.location = loc
    cam.rotation_euler = (Vector((0, 0, 0.85)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED")
