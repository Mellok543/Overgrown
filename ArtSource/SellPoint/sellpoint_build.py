"""SellPoint_Bin: stylized low-poly wooden grass bin. Run: blender -b --factory-startup -P sellpoint_build.py
Blender is Z-up here; FBX export converts to Y-up with transforms baked (Unity: rot 0, scale 1)."""
import os, math, random
import bpy, bmesh
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\SellPoint"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(4)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
def material(name, rgb, rough=0.85, metal=0.0, double=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.use_backface_culling = not double
    return m

# Colours live in a small sRGB palette texture (one material, colours identical in Blender and Unity).
# Per-part placeholder materials only mark which palette cell a face uses; they are merged on export.
PALETTE = {
    "wood":      (150, 104, 64),
    "wood2":     (136, 96, 60),
    "wood_old":  (128, 114, 98),    # grey, weathered boards
    "wood_dark": (84, 58, 38),      # frame: posts, skids, rim
    "metal":     (72, 74, 78),
    "rust":      (112, 72, 46),
    "sign":      (202, 186, 150),
    "paint":     (58, 108, 38),
    "grass":     (92, 124, 40),
    "grass_dry": (138, 138, 62),
    "blade":     (112, 158, 48),
}
PAL_GRID, PAL_CELL = 4, 16
PAL_SIZE = PAL_GRID * PAL_CELL
MATS = {k: bpy.data.materials.new("tmp_" + k) for k in PALETTE}
parts = []

def new_obj(name, bm, mat, extra=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(MATS[mat])
    for e in extra:
        me.materials.append(MATS[e])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def box(name, center, size, mat, rot=(0, 0, 0), bevel=0.01):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect='EDGES', profile=0.5)
    M = Matrix.Translation(Vector(center)) @ Euler(rot).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return new_obj(name, bm, mat)

def jitter(a):
    return rng.uniform(-a, a)

# ---------------------------------------------------------------- dimensions (metres)
W, D = 1.40, 1.00          # outer width (X) / depth (Y)
SKID_H = 0.08
FLOOR_T = 0.04
PX, PY = 0.62, 0.42        # corner post centres
POST = 0.08
TOP = 0.92                 # top of walls
PLANK_T = 0.035
ROWS = 4
PLANK_H = 0.175
GAP = (TOP - SKID_H - FLOOR_T - ROWS * PLANK_H) / (ROWS - 1)

# skids (runners) under the bin
for s in (-1, 1):
    box(f"skid{s}", (0, s * 0.34, SKID_H / 2), (W, 0.10, SKID_H), "wood_dark", bevel=0.012)

# floor boards
z_floor = SKID_H + FLOOR_T / 2
for i in range(5):
    y = -0.38 + i * 0.19
    box(f"floor{i}", (0, y, z_floor), (W - 0.06, 0.18, FLOOR_T), "wood_old", bevel=0.006)

# corner posts
z0 = SKID_H + FLOOR_T
for sx in (-1, 1):
    for sy in (-1, 1):
        h = TOP - SKID_H + 0.03
        box(f"post{sx}{sy}", (sx * PX, sy * PY, SKID_H + h / 2), (POST, POST, h), "wood_dark", bevel=0.012)

# wall planks: long walls (front/back) along X, short walls (sides) along Y
y_long = PY + POST / 2 + PLANK_T / 2
x_short = PX + POST / 2 + PLANK_T / 2
for r in range(ROWS):
    zc = z0 + PLANK_H / 2 + r * (PLANK_H + GAP)
    for sy in (-1, 1):
        L = W - 0.01 + jitter(0.02)
        cx, tilt, z, y = jitter(0.01), jitter(0.018), zc + jitter(0.006), sy * y_long
        mat = rng.choice(["wood", "wood", "wood2", "wood_old"])
        if sy == -1 and r == ROWS - 1:
            # broken front top board: shorter, sagging to the right, left end stays attached;
            # pushed slightly outward so it never z-fights with the row below
            L, cx, tilt = 0.82, -0.28, math.radians(4)
            z = zc - (L / 2) * math.sin(tilt)
            y -= 0.012
        box(f"long{r}{sy}", (cx, y, z), (L, PLANK_T, PLANK_H - 0.01), mat, rot=(0, tilt, 0), bevel=0.008)
    for sx in (-1, 1):
        L = 2 * (PY + POST / 2) + jitter(0.015)
        mat = rng.choice(["wood", "wood", "wood2", "wood_old"])
        box(f"short{r}{sx}", (sx * x_short, jitter(0.008), zc + jitter(0.006)), (PLANK_T, L, PLANK_H - 0.01),
            mat, rot=(jitter(0.018), 0, 0), bevel=0.008)

# top rim boards (back and sides only: open, lower front edge for dropping grass in)
RIM_W, RIM_T = 0.09, 0.03
zr = TOP + RIM_T / 2
box("rim_back", (0, PY + 0.03, zr), (W + 0.02, RIM_W, RIM_T), "wood_dark", bevel=0.008)
for sx in (-1, 1):
    box(f"rim_side{sx}", (sx * (PX + 0.03), 0, zr), (RIM_W, D - 0.02, RIM_T), "wood_dark", rot=(0, 0, 0), bevel=0.008)

# metal corner angles (top and bottom of each vertical corner)
MT = 0.006
for sx in (-1, 1):
    for sy in (-1, 1):
        for zc in (z0 + 0.10, TOP - 0.09):
            ox = sx * (x_short + PLANK_T / 2 + MT / 2)
            oy = sy * (y_long + PLANK_T / 2 + MT / 2)
            ex = sx * (PX + POST / 2 + PLANK_T) - sx * 0.06
            ey = sy * (PY + POST / 2 + PLANK_T) - sy * 0.06
            mm = "rust" if rng.random() < 0.3 else "metal"
            box(f"angle_x{sx}{sy}{zc:.2f}", (ex, oy, zc), (0.13, MT, 0.16), mm, bevel=0)
            box(f"angle_y{sx}{sy}{zc:.2f}", (ox, ey, zc), (MT, 0.13, 0.16), mm, bevel=0)

# sign: two stakes on the back wall + board facing the front (-Y)
SIGN_Y = y_long + PLANK_T / 2 + 0.02
for sx in (-1, 1):
    box(f"stake{sx}", (sx * 0.32, SIGN_Y, 0.78), (0.045, 0.035, 0.44), "wood_dark", bevel=0.006)
sign = box("sign", (0, SIGN_Y - 0.03, 1.08), (0.78, 0.03, 0.22), "sign", rot=(0, math.radians(1.5), 0), bevel=0.01)
# painted emblem: stylized grass tuft (flat triangles just in front of the board)
bm = bmesh.new()
fy = SIGN_Y - 0.03 - 0.016
for i, (x, h, lean) in enumerate([(-0.07, 0.11, -0.05), (-0.025, 0.15, -0.015), (0.02, 0.16, 0.02), (0.065, 0.12, 0.05)]):
    a = bm.verts.new((x - 0.02, fy, 1.00))
    b = bm.verts.new((x + 0.02, fy, 1.00))
    c = bm.verts.new((x + lean, fy, 1.00 + h))
    bm.faces.new((a, b, c))
# base stripe
q = [bm.verts.new(p) for p in [(-0.13, fy, 0.985), (0.13, fy, 0.985), (0.13, fy, 1.005), (-0.13, fy, 1.005)]]
bm.faces.new(q)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:                       # must face -Y (towards the player)
    if f.normal.y > 0:
        f.normal_flip()
new_obj("emblem", bm, "paint")

# grass pile inside (low-poly mound)
IX, IY = PX - 0.02, PY - 0.02
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=8, y_segments=6, size=1.0)
for v in bm.verts:
    x, y = v.co.x, v.co.y                 # -1..1
    edge = max(abs(x), abs(y))
    hmound = 0.62 + 0.16 * (1 - edge ** 2) + jitter(0.03)
    v.co = Vector((x * IX, y * IY, hmound))
for f in bm.faces:
    f.material_index = 1 if rng.random() < 0.3 else 0
new_obj("pile", bm, "grass", extra=("grass_dry",))

# loose blades sticking out of the pile, some hanging over the rim (double-sided)
bm = bmesh.new()
for i in range(26):
    ang = rng.uniform(0, math.tau)
    r = rng.uniform(0.1, 1.0)
    bx, by = math.cos(ang) * r * IX * 0.95, math.sin(ang) * r * IY * 0.95
    edge = max(abs(bx / IX), abs(by / IY))
    bz = 0.62 + 0.16 * (1 - edge ** 2) - 0.02
    h = rng.uniform(0.14, 0.3)
    lean = Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(0.04, 0.14) * (0.4 + r)
    side = Vector((-math.sin(ang + 1.2), math.cos(ang + 1.2), 0)) * rng.uniform(0.012, 0.02)
    base = Vector((bx, by, bz))
    mid = base + Vector((0, 0, h * 0.55)) + lean * 0.35
    tip = base + Vector((0, 0, h * 0.85)) + lean
    for flip in (False, True):
        v = [bm.verts.new(p) for p in (base - side, base + side, mid + side * 0.6, mid - side * 0.6, tip)]
        fs = [(v[0], v[1], v[2], v[3]), (v[3], v[2], v[4])]
        for f in fs:
            bm.faces.new(tuple(reversed(f)) if flip else f)
new_obj("blades", bm, "blade")

# ---------------------------------------------------------------- join, UV, clean up
for ob in parts:
    ob.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
bin_ob = bpy.context.view_layer.objects.active
bin_ob.name = bin_ob.data.name = "SellPoint_Bin"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# palette texture
keys = list(PALETTE)
img = bpy.data.images.new("SellPoint_Palette", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(keys):
    cx, cy = idx % PAL_GRID, idx // PAL_GRID
    r, g, b = (c / 255 for c in PALETTE[k])
    for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
        for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (r, g, b, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, "SellPoint_Palette.png")
img.file_format = 'PNG'
img.save()

me = bin_ob.data
uvl = me.uv_layers.new(name="UVMap")
slot_key = [m.name[4:] for m in me.materials]
for poly in me.polygons:
    idx = keys.index(slot_key[poly.material_index])
    u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
    v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
    for li in poly.loop_indices:
        uvl.data[li].uv = (u, v)
    poly.material_index = 0

final = bpy.data.materials.new("M_SellPoint")
final.use_nodes = True
nt = final.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
bsdf.inputs["Metallic"].default_value = 0.0
me.materials.clear()
me.materials.append(final)

# pivot at base centre
zs = [v.co.z for v in bin_ob.data.vertices]
xs = [v.co.x for v in bin_ob.data.vertices]
ys = [v.co.y for v in bin_ob.data.vertices]
off = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)))
for v in bin_ob.data.vertices:
    v.co -= off
bin_ob.data.update()

tris = sum(len(p.vertices) - 2 for p in bin_ob.data.polygons)
d = bin_ob.dimensions
print(f"BIN tris={tris} W={d.x:.2f} D={d.y:.2f} H={d.z:.2f} mats={[m.name for m in bin_ob.data.materials]}")

bin_ob.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "SellPoint_Bin.fbx"),
    use_selection=True, object_types={'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z', axis_up='Y', bake_space_transform=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
    path_mode='RELATIVE', embed_textures=False,
)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "SellPoint_Bin.blend"))
print("EXPORTED")

# ---------------------------------------------------------------- preview render
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.75, 0.25, 0.9))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=8)
g = material("Ground", (0.12, 0.10, 0.06)); bpy.context.object.data.materials.append(g)
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 900, 700
cam_data = bpy.data.cameras.new("C"); cam_data.lens = 35
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
for tag, loc in (("front", (1.6, -2.6, 1.7)), ("back", (-1.9, 2.3, 1.5))):
    cam.location = loc
    direction = Vector((0, 0, 0.55)) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED")
