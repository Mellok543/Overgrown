"""Player_Mower: first-person push rotary lawn mower.
Run: blender -b --factory-startup -P player_mower_build.py

Hierarchy (Unity, Y up, +Z forward = mowing direction), every node rotation 0 / scale 1:
  Player_Mower     empty, pivot at the deck centre on the ground
    MowerBody      deck, engine cover, grass bag                     (pivot: root)
    MowerHandle    push handle, grip, bail lever, cable              (pivot: handle mount hinge)
    Wheel_FL/FR/BL/BR                                                 (pivot: wheel centre, spin axis = local X)
L/R are named for Unity (player standing behind the handle looking +Z).
Blender is Z-up here (Unity +Z forward = Blender -Y, Unity +X = Blender -X). Export converts to Y-up manually."""
import os, math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\PlayerMower"
NAME = "Player_Mower"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(8)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette: (sRGB, metallic, smoothness)
PALETTE = {
    "red":         ((196, 58, 44),  0.0, 0.45),
    "red_dark":    ((138, 40, 32),  0.0, 0.40),
    "cream":       ((232, 218, 180), 0.0, 0.40),
    "dirt":        ((104, 86, 60),  0.0, 0.10),
    "black":       ((42, 42, 44),   0.0, 0.30),
    "rubber":      ((30, 32, 32),   0.0, 0.15),
    "grey":        ((96, 98, 102),  0.0, 0.35),
    "grey_light":  ((140, 142, 146), 0.0, 0.40),
    "vent":        ((24, 24, 26),   0.0, 0.10),
    "yellow":      ((236, 190, 60), 0.0, 0.40),
    "metal":       ((150, 154, 158), 0.85, 0.55),
    "metal_dark":  ((82, 84, 88),   0.8, 0.45),
    "canvas":      ((74, 104, 70),  0.0, 0.15),
    "canvas_dark": ((52, 74, 50),   0.0, 0.10),
    "stain":       ((96, 128, 50),  0.0, 0.10),
    "tire":        ((46, 44, 42),   0.0, 0.20),
    "tire_dark":   ((30, 29, 28),   0.0, 0.15),
    "hub":         ((200, 196, 186), 0.0, 0.35),
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

def to_matrix(center, rot):
    R = rot.to_matrix().to_4x4() if isinstance(rot, (Quaternion, Euler)) else Euler(rot).to_matrix().to_4x4()
    return Matrix.Translation(Vector(center)) @ R

def box(name, center, size, mat, rot=(0, 0, 0), bevel=0.0, seg=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect='EDGES', profile=0.5)
    bmesh.ops.transform(bm, matrix=to_matrix(center, rot), verts=bm.verts)
    return new_obj(name, bm, [mat])

def lathe(name, profile, n, mat_fn, center, rot=(0, 0, 0), cap_bottom=True, cap_top=True, phase=0.0, cap_mats=None):
    """Revolve (r, z) around local Z; r == 0 -> pole. mat_fn(row, seg)."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))]); continue
        rings.append([bm.verts.new((math.cos(phase + math.tau * i / n) * r, math.sin(phase + math.tau * i / n) * r, z)) for i in range(n)])
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
    bmesh.ops.transform(bm, matrix=to_matrix(center, rot), verts=bm.verts)
    return new_obj(name, bm, used)

def arc_lathe(name, loop, a0, a1, seg, mat_fn, center):
    """Revolve a closed (r, z) loop through [a0, a1] around Z, with end caps. mat_fn(edge_index, seg)."""
    bm = bmesh.new()
    rings = []
    for k in range(seg + 1):
        a = a0 + (a1 - a0) * k / seg
        rings.append([bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)) for r, z in loop])
    used = []
    def mi(key):
        if key not in used:
            used.append(key)
        return used.index(key)
    m = len(loop)
    for k in range(seg):
        a, b = rings[k], rings[k + 1]
        for i in range(m):
            i2 = (i + 1) % m
            bm.faces.new((a[i], a[i2], b[i2], b[i])).material_index = mi(mat_fn(i, k))
    bm.faces.new(list(reversed(rings[0]))).material_index = mi(mat_fn(0, 0))
    bm.faces.new(rings[-1]).material_index = mi(mat_fn(0, seg - 1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(center)), verts=bm.verts)
    return new_obj(name, bm, used)

def tube(name, pts, r, n, mat, caps=True):
    """Round tube swept along a polyline."""
    bm = bmesh.new()
    pts = [Vector(p) for p in pts]
    rings = []
    ref = Vector((0, 0, 1))
    for k, p in enumerate(pts):
        t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        if abs(t.dot(ref)) > 0.95:
            ref = Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        v = t.cross(u).normalized()
        rings.append([bm.verts.new(p + (u * math.cos(math.tau * i / n) + v * math.sin(math.tau * i / n)) * r) for i in range(n)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, [mat])

def collect(name, pivot):
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

# ---------------------------------------------------------------- layout (Blender coords: front = -Y, root at deck centre on the ground)
DECK_W, DECK_L = 0.54, 0.62
WR_F, WR_B = 0.095, 0.115                 # front / back wheel radius (bigger rear wheels)
WX = 0.305                                # wheel centre |x|
WY_F, WY_B = -0.22, 0.23
# Blender +X becomes Unity -X (FBX handedness flip); L/R are named for the Unity side: Unity left (-X) = Blender +X.
WHEELS = {"Wheel_FL": (WX, WY_F, WR_F), "Wheel_FR": (-WX, WY_F, WR_F),
          "Wheel_BL": (WX, WY_B, WR_B), "Wheel_BR": (-WX, WY_B, WR_B)}
HINGE = Vector((0, 0.285, 0.21))          # handle mount axis

# ================================================================ MowerBody
# lower skirt + rounded upper shell
box("skirt", (0, 0.0, 0.085), (DECK_W + 0.02, DECK_L + 0.02, 0.07), "red_dark", bevel=0.022, seg=2)
box("shell", (0, 0.0, 0.15), (DECK_W - 0.02, DECK_L - 0.04, 0.1), "red", bevel=0.04, seg=3)
box("skirt_dirt", (0, 0.0, 0.056), (DECK_W + 0.025, DECK_L + 0.025, 0.014), "dirt", bevel=0.006)
# cream stripe over the front
box("stripe", (0, -0.2, 0.2), (0.12, 0.16, 0.012), "cream", bevel=0.004)
# wheel arches / height adjusters / stub axles
for name, (x, y, r) in WHEELS.items():
    s = 1 if x > 0 else -1
    box(f"arch_{name}", (s * (DECK_W / 2 - 0.005), y, 0.13), (0.03, 0.16, 0.06), "red_dark", bevel=0.012)
    box(f"lever_{name}", (s * (DECK_W / 2 + 0.012), y + 0.05, 0.19), (0.012, 0.025, 0.09), "metal_dark",
        rot=(0.35, 0, 0), bevel=0.004)
    lathe(f"lever_knob_{name}", [(0.0, -0.012), (0.014, -0.012), (0.014, 0.012), (0.0, 0.012)], 8, lambda j, i: "black",
          (s * (DECK_W / 2 + 0.012), y + 0.066, 0.235), rot=(0, math.pi / 2, 0))
    lathe(f"axle_{name}", [(0.012, 0.0), (0.012, 0.035)], 8, lambda j, i: "metal_dark",
          (s * (DECK_W / 2 + 0.005), y, r), rot=(0, s * math.pi / 2, 0), cap_bottom=False)
# front bumper bar
bump = [Vector((x, -0.35 - 0.02 * (1 - (x / 0.24) ** 2), 0.1)) for x in [-0.24 + 0.08 * k for k in range(7)]]
tube("bumper", [Vector((-0.26, -0.3, 0.1))] + bump + [Vector((0.26, -0.3, 0.1))], 0.012, 8, "metal_dark")
# engine: simple rounded cover, no heavy detail
ENG = Vector((0, -0.04, 0.195))
lathe("engine_base", [(0.0, 0.0), (0.15, 0.0), (0.155, 0.035), (0.0, 0.035)], 18, lambda j, i: "black", ENG)
lathe("engine_cover", [(0.14, 0.035), (0.145, 0.06), (0.13, 0.12), (0.095, 0.16), (0.05, 0.178), (0.0, 0.182)], 18,
      lambda j, i: "grey" if j < 3 else "grey_light", ENG, cap_bottom=False)
for k in range(5):   # cooling slots on the cover side
    a = math.radians(200 + k * 14)
    box(f"slot{k}", ENG + Vector((math.cos(a) * 0.142, math.sin(a) * 0.142, 0.085)), (0.008, 0.03, 0.05), "vent",
        rot=(0, 0, a))
lathe("fuel_cap", [(0.0, 0.0), (0.028, 0.0), (0.028, 0.03), (0.022, 0.036), (0.0, 0.036)], 10, lambda j, i: "yellow",
      ENG + Vector((0.06, 0.06, 0.15)))
box("air_filter", ENG + Vector((-0.1, 0.07, 0.1)), (0.08, 0.06, 0.07), "black", rot=(0, 0, 0.3), bevel=0.012)
box("pull_grip", ENG + Vector((0.0, 0.11, 0.17)), (0.07, 0.022, 0.022), "black", bevel=0.008)
tube("pull_cord", [ENG + Vector((0.0, 0.1, 0.16)), ENG + Vector((0.0, 0.09, 0.12))], 0.004, 4, "black")
# rear discharge flap + grass bag
box("rear_flap", (0, 0.315, 0.12), (0.34, 0.02, 0.1), "black", rot=(-0.2, 0, 0), bevel=0.006)
box("bag", (0, 0.49, 0.265), (0.4, 0.33, 0.26), "canvas", bevel=0.06, seg=2)
box("bag_bottom", (0, 0.49, 0.145), (0.38, 0.31, 0.03), "canvas_dark", bevel=0.012)
box("bag_stain", (0, 0.33, 0.17), (0.3, 0.012, 0.05), "stain", bevel=0.004)
tube("bag_frame", [Vector((-0.2, 0.33, 0.4)), Vector((-0.2, 0.66, 0.4)), Vector((0.2, 0.66, 0.4)),
                   Vector((0.2, 0.33, 0.4)), Vector((-0.2, 0.33, 0.4))], 0.01, 6, "metal_dark", caps=False)
tube("bag_handle", [Vector((-0.07, 0.5, 0.4)), Vector((-0.06, 0.5, 0.45)), Vector((0.06, 0.5, 0.45)), Vector((0.07, 0.5, 0.4))],
     0.01, 6, "black")
for k in range(3):   # mesh vents on the bag top
    box(f"bag_vent{k}", (0, 0.4 + k * 0.09, 0.396), (0.3, 0.05, 0.004), "canvas_dark")
# handle mount brackets on the deck
for s in (-1, 1):
    box(f"mount{s}", (s * 0.225, HINGE.y - 0.015, 0.2), (0.03, 0.06, 0.07), "red_dark", bevel=0.01)
body = collect("MowerBody", (0, 0, 0))

# ================================================================ MowerHandle (pivot on the mount hinge)
TOP_Y, TOP_Z = 0.76, 1.0
for s in (-1, 1):
    base = Vector((s * 0.225, HINGE.y, HINGE.z))
    knee = Vector((s * 0.225, 0.52, 0.6))
    top = Vector((s * 0.215, TOP_Y - 0.02, TOP_Z - 0.03))
    tube(f"tube_low{s}", [base, knee], 0.013, 10, "metal")
    tube(f"tube_up{s}", [knee, top], 0.013, 10, "metal")
    lathe(f"fold_knob{s}", [(0.0, -0.02), (0.022, -0.02), (0.026, 0.0), (0.022, 0.02), (0.0, 0.02)], 10,
          lambda j, i: "black", knee + Vector((s * 0.028, 0, 0)), rot=(0, math.pi / 2, 0))
    lathe(f"hinge_bolt{s}", [(0.0, -0.012), (0.016, -0.012), (0.016, 0.012), (0.0, 0.012)], 8,
          lambda j, i: "metal_dark", base + Vector((s * 0.025, 0, 0)), rot=(0, math.pi / 2, 0))
# top bar with soft grip
tube("top_bar", [Vector((-0.215, TOP_Y - 0.02, TOP_Z - 0.03)), Vector((-0.2, TOP_Y, TOP_Z)),
                 Vector((0.2, TOP_Y, TOP_Z)), Vector((0.215, TOP_Y - 0.02, TOP_Z - 0.03))], 0.013, 10, "metal")
GRIP = [(0.0, -0.17), (0.02, -0.17), (0.023, -0.15), (0.023, 0.15), (0.02, 0.17), (0.0, 0.17)]
lathe("grip", GRIP, 12, lambda j, i: "rubber", Vector((0, TOP_Y, TOP_Z)), rot=(0, math.pi / 2, 0))
# safety bail lever (red) just in front of the grip
tube("bail", [Vector((-0.2, TOP_Y - 0.035, TOP_Z - 0.02)), Vector((-0.19, TOP_Y - 0.075, TOP_Z + 0.035)),
              Vector((0.19, TOP_Y - 0.075, TOP_Z + 0.035)), Vector((0.2, TOP_Y - 0.035, TOP_Z - 0.02))], 0.009, 8, "red")
# throttle cable running down one tube to the engine
tube("cable", [Vector((0.2, TOP_Y - 0.05, TOP_Z - 0.03)), Vector((0.245, 0.6, 0.7)), Vector((0.245, 0.45, 0.42)),
               Vector((0.2, 0.3, 0.3)), Vector((0.12, 0.12, 0.3))], 0.004, 4, "black")
box("cable_clip", (0.24, 0.52, 0.6), (0.02, 0.02, 0.03), "black")
handle = collect("MowerHandle", HINGE)

# ================================================================ wheels (spin axis = local X)
TIRE = lambda r: [(0.0, -0.028), (r * 0.42, -0.028), (r * 0.58, -0.032), (r * 0.82, -0.03), (r * 0.97, -0.022),
                  (r, -0.01), (r, 0.01), (r * 0.97, 0.022), (r * 0.82, 0.03), (r * 0.58, 0.032), (r * 0.42, 0.028), (0.0, 0.028)]
def tire_mat(j, i):
    if j <= 1 or j >= 10:
        return "hub" if j in (0, 10) else "grey"
    if j in (4, 5, 6):
        return "tire" if i % 2 else "tire_dark"      # tread blocks: readable spin
    return "tire"
wheels = []
for name, (x, y, r) in WHEELS.items():
    lathe(name + "_tire", TIRE(r), 18, tire_mat, (x, y, r), rot=(0, math.pi / 2, 0))
    s = 1 if x > 0 else -1
    lathe(name + "_cap", [(0.0, 0.0), (0.022, 0.0), (0.018, 0.012), (0.0, 0.014)], 8, lambda j, i: "red",
          (x + s * 0.03, y, r), rot=(0, s * math.pi / 2, 0), cap_bottom=False)
    wheels.append(collect(name, (x, y, r)))

# ---------------------------------------------------------------- hierarchy
root = bpy.data.objects.new(NAME, None)
scene.collection.objects.link(root)
root.empty_display_size = 0.2
for ch in [body, handle] + wheels:
    w = ch.location.copy()
    ch.parent = root
    ch.matrix_parent_inverse = Matrix.Identity(4)
    ch.location = w
bpy.context.view_layer.update()

# ---------------------------------------------------------------- atlases + UVs + one material
def save_png(name, cell_rgba, srgb=True):
    img = bpy.data.images.new(name, PAL_SIZE, PAL_SIZE, alpha=True)
    if not srgb:
        img.colorspace_settings.name = 'Non-Color'
    px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
    for idx, k in enumerate(KEYS):
        cx, cy = idx % PAL_GRID, idx // PAL_GRID
        col = cell_rgba(k)
        for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
            for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
                i = (y * PAL_SIZE + x) * 4
                px[i:i + 4] = col
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = 'PNG'
    img.save()
    return img

base_img = save_png(NAME + "_Atlas", lambda k: (*[c / 255 for c in PALETTE[k][0]], 1.0))
ms_img = save_png(NAME + "_MetallicSmoothness", lambda k: (PALETTE[k][1],) * 3 + (PALETTE[k][2],), srgb=False)

mat = bpy.data.materials.new("M_PlayerMower")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = base_img; t1.interpolation = 'Closest'
nt.links.new(t1.outputs["Color"], bsdf.inputs["Base Color"])
t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = ms_img; t2.interpolation = 'Closest'
sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(t2.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs[0], bsdf.inputs["Metallic"])
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(t2.outputs["Alpha"], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])

mesh_objs = [body, handle] + wheels
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
    me.materials.clear(); me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free(); me.update()
    total += len(me.polygons)
    print(f"OBJ {ob.name:13s} tris={len(me.polygons):5d} pivot(blender)={tuple(round(c, 3) for c in ob.location)} "
          f"dims=({ob.dimensions.x:.3f},{ob.dimensions.y:.3f},{ob.dimensions.z:.3f})")
allv = [ob.matrix_world @ v.co for ob in mesh_objs for v in ob.data.vertices]
mn = [min(p[i] for p in allv) for i in range(3)]; mx = [max(p[i] for p in allv) for i in range(3)]
print(f"TOTAL tris={total} width={mx[0]-mn[0]:.2f} length={mx[1]-mn[1]:.2f} height={mx[2]-mn[2]:.2f} minZ={mn[2]:.3f}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, NAME + ".blend"))

# ---------------------------------------------------------------- previews
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.9, 0.3, -0.6))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=30)
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.16, 0.05, 1)
bpy.context.object.data.materials.append(g)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
def shot(tag, loc, target, res, lens=35):
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
shot("front34", (-1.5, -1.7, 1.1), (0, 0.15, 0.35), (1000, 800), lens=40)
shot("side", (2.4, 0.2, 0.6), (0, 0.2, 0.45), (1000, 700), lens=40)
shot("fp", (0, 1.25, 1.6), (0, -0.4, 0.1), (1280, 720), lens=22)      # player standing behind the handle
print("RENDERED")

# ---------------------------------------------------------------- export
# Convert to Y-up ourselves (rotate mesh data + local offsets by -90 deg about X), export without axis
# conversion, then mark the file Y-up. Keeps every node at rotation 0 / scale 1 in Unity.
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
    filepath=fbx_path, use_selection=True, object_types={'EMPTY', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='Y', axis_up='Z', bake_space_transform=False,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
    path_mode='RELATIVE', embed_textures=False,
)

def set_int_prop(buf, name, value):
    key = b"S" + struct.pack("<I", len(name)) + name.encode()
    tail = b"S" + struct.pack("<I", 3) + b"int" + b"S" + struct.pack("<I", 7) + b"Integer" + b"S" + struct.pack("<I", 0) + b"I"
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
