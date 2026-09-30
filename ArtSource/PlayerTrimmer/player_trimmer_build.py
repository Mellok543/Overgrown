"""Player_Trimmer: first-person cordless string trimmer, modelled in its natural holding pose.
Run: blender -b --factory-startup -P player_trimmer_build.py

Hierarchy (Unity, Y up, +Z forward), every node rotation 0 / scale 1:
  Player_Trimmer   empty, pivot at the main (rear) grip
    TrimmerBody    housing + battery, main grip + trigger, shaft, D side handle, motor pod   (pivot: main grip)
    TrimmerHead    spool + cutting line; spins around its local +Y                           (pivot: spin centre)
    TrimmerGuard   half-round shroud behind the head, towards the player                    (pivot: head centre)
The shaft runs forward (+Z) and down from the grip; the cutting head is level with the ground.
Blender is Z-up here (Unity +Z forward = Blender -Y). Export converts to Y-up manually (see bottom)."""
import os, math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\PlayerTrimmer"
NAME = "Player_Trimmer"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette: (sRGB, metallic, smoothness)
PALETTE = {
    "orange":      ((230, 124, 34), 0.0, 0.45),
    "orange_dark": ((170, 84, 26),  0.0, 0.40),
    "orange_worn": ((200, 120, 64), 0.0, 0.30),
    "black":       ((42, 42, 44),   0.0, 0.30),
    "rubber":      ((30, 32, 32),   0.0, 0.15),
    "grey":        ((92, 94, 98),   0.0, 0.35),
    "metal":       ((150, 154, 158), 0.85, 0.55),   # shaft
    "metal_dark":  ((82, 84, 88),   0.8, 0.45),
    "line":        ((236, 212, 64), 0.0, 0.40),
    "stain":       ((96, 122, 52),  0.0, 0.10),     # dried grass stains on the guard
    "dirt":        ((110, 92, 66),  0.0, 0.10),
    "vent":        ((24, 24, 26),   0.0, 0.10),
}
PAL_GRID, PAL_CELL = 4, 16
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

# ---------------------------------------------------------------- layout (Blender coords, grip at origin)
A = math.radians(38)                                  # shaft angle below horizontal
D = Vector((0, -math.cos(A), -math.sin(A)))           # along the shaft, forward/down
Q = D.to_track_quat('Z', 'Y')                         # local Z -> shaft, local Y -> "up" side of the shaft
UP = Q @ Vector((0, 1, 0))
def along(t, up=0.0, side=0.0):
    return D * t + UP * up + Vector((side, 0, 0))

SHAFT_END = 0.95
S1 = along(SHAFT_END)
H = S1 + Vector((0, -0.035, -0.115))                  # spin centre of the cutting head

# ================================================================ TrimmerBody
# rear housing (motor electronics) + battery pack
box("housing", along(-0.17, up=0.01), (0.08, 0.11, 0.2), "orange", rot=Q, bevel=0.022, seg=2)
box("housing_band", along(-0.085, up=0.0), (0.084, 0.1, 0.03), "orange_dark", rot=Q, bevel=0.01)
box("battery", along(-0.215, up=0.085), (0.07, 0.07, 0.13), "black", rot=Q, bevel=0.012, seg=2)
box("battery_latch", along(-0.155, up=0.12), (0.035, 0.012, 0.03), "orange", rot=Q, bevel=0.004)
for k in range(3):   # side vents
    for s in (-1, 1):
        box(f"vent{k}{s}", along(-0.23 + k * 0.035, up=-0.005, side=s * 0.0405), (0.004, 0.05, 0.012), "vent", rot=Q)
box("scuff", along(-0.26, up=-0.045), (0.06, 0.02, 0.05), "orange_worn", rot=Q, bevel=0.008)
# main grip (rubber, finger ridges) + trigger
GRIP_PROFILE = [(0.0, -0.075), (0.023, -0.075), (0.026, -0.05), (0.024, -0.035), (0.027, -0.02), (0.025, -0.005),
                (0.027, 0.01), (0.025, 0.025), (0.027, 0.04), (0.024, 0.06), (0.02, 0.075), (0.0, 0.075)]
lathe("grip", GRIP_PROFILE, 14, lambda j, i: "rubber", along(0.0), rot=Q)
box("trigger", along(-0.015, up=-0.034), (0.016, 0.03, 0.04), "orange", rot=Q @ Quaternion((1, 0, 0), 0.25), bevel=0.005)
box("trigger_guard", along(-0.005, up=-0.052), (0.022, 0.008, 0.09), "black", rot=Q, bevel=0.003)
# shaft
lathe("shaft", [(0.0145, 0.07), (0.0145, SHAFT_END - 0.02)], 12, lambda j, i: "metal", (0, 0, 0), rot=Q)
lathe("shaft_joint", [(0.018, 0.5), (0.019, 0.51), (0.019, 0.55), (0.018, 0.56)], 12,
      lambda j, i: "black", (0, 0, 0), rot=Q, cap_bottom=False, cap_top=False)
# D side handle on a clamp
CL = along(0.36)
box("dh_clamp", CL, (0.05, 0.05, 0.06), "orange_dark", rot=Q, bevel=0.01)
dpts = [CL + Vector(p) for p in [(-0.03, 0.0, 0.02), (-0.075, 0.0, 0.09), (-0.065, 0.0, 0.165), (-0.02, 0.0, 0.19),
                                 (0.03, 0.0, 0.19), (0.07, 0.0, 0.165), (0.078, 0.0, 0.09), (0.03, 0.0, 0.02)]]
tube("dh_loop", dpts, 0.011, 10, "black")
top_mid = (dpts[3] + dpts[4]) / 2
lathe("dh_grip", [(0.0, -0.05), (0.017, -0.05), (0.019, -0.03), (0.019, 0.03), (0.017, 0.05), (0.0, 0.05)], 10,
      lambda j, i: "rubber", top_mid, rot=Vector((1, 0, 0)).to_track_quat('Z', 'Y'))
# motor pod at the head + coupler
POD_C = Vector((H.x, H.y, H.z + 0.03))
lathe("motor_pod", [(0.0, 0.0), (0.05, 0.0), (0.054, 0.03), (0.05, 0.075), (0.036, 0.1), (0.0, 0.105)], 18,
      lambda j, i: "orange" if j < 3 else "orange_dark", POD_C)
for k in range(4):
    a = math.radians(-60 + k * 40)
    box(f"pod_vent{k}", POD_C + Vector((math.cos(a) * 0.052, math.sin(a) * 0.052 + 0.0, 0.045)), (0.006, 0.02, 0.03), "vent",
        rot=(0, 0, a + math.pi / 2))
box("coupler", S1 + Vector((0, -0.005, -0.02)), (0.04, 0.045, 0.08), "orange_dark", rot=Q, bevel=0.01)
box("pod_dirt", POD_C + Vector((0, -0.05, 0.012)), (0.05, 0.01, 0.02), "dirt", bevel=0.004)
body = collect("TrimmerBody", (0, 0, 0))

# ================================================================ TrimmerHead (spins around local Z in Blender = Unity Y)
SPOOL = [(0.0, -0.036), (0.022, -0.036), (0.03, -0.03), (0.034, -0.022), (0.056, -0.02), (0.062, -0.006),
         (0.062, 0.008), (0.058, 0.02), (0.04, 0.026), (0.0, 0.026)]
def spool_mat(j, i):
    if j <= 1:
        return "metal_dark"          # bump knob
    if j in (4, 5):
        return "line" if i % 4 else "black"   # wound line band (the gaps show the spin)
    return "black" if j != 7 else "grey"
lathe("spool", SPOOL, 20, spool_mat, H)
for s in (-1, 1):
    ey = H + Vector((s * 0.06, 0, 0.0))
    box(f"eyelet{s}", ey, (0.012, 0.018, 0.014), "metal_dark")
    # cutting line trails slightly backwards (spin direction)
    tube(f"cutline{s}", [ey, ey + Vector((s * 0.075, s * 0.008, -0.002)), ey + Vector((s * 0.15, s * 0.03, -0.006))], 0.0035, 4, "line")
head = collect("TrimmerHead", H)

# ================================================================ TrimmerGuard (behind the head, towards the player = +Y)
GUARD = [(0.066, 0.052), (0.175, 0.045), (0.182, 0.0), (0.176, -0.012), (0.168, 0.0), (0.162, 0.036), (0.066, 0.043)]
def guard_mat(i, k):
    if i in (2, 3) and (k * 7 + i) % 5 == 0:
        return "stain"
    if i in (2, 3, 4):
        return "black"
    return "orange_dark" if i == 0 else "orange"
arc_lathe("guard", GUARD, math.radians(-5), math.radians(185), 20, guard_mat, H)
box("guard_mount", H + Vector((0, 0.07, 0.05)), (0.04, 0.05, 0.02), "orange_dark", bevel=0.005)
box("line_cutter", H + Vector((-math.cos(math.radians(170)) * -0.17, math.sin(math.radians(170)) * 0.17, 0.0)),
    (0.02, 0.012, 0.012), "metal")
guard = collect("TrimmerGuard", H)

# ---------------------------------------------------------------- hierarchy
root = bpy.data.objects.new(NAME, None)
scene.collection.objects.link(root)
root.empty_display_size = 0.1
for ch in (body, head, guard):
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

mat = bpy.data.materials.new("M_PlayerTrimmer")
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

mesh_objs = [body, head, guard]
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
ext = [max(p[i] for p in allv) - min(p[i] for p in allv) for i in range(3)]
print(f"TOTAL tris={total} extent x={ext[0]:.2f} y(fwd)={ext[1]:.2f} z={ext[2]:.2f} length={math.hypot(ext[1], ext[2]):.2f}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, NAME + ".blend"))

# ---------------------------------------------------------------- previews
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.9, 0.3, -0.6))
sun = bpy.context.object; sun.data.energy = 3.5
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
def shot(tag, loc, target, res, ortho=None, lens=35):
    cam_data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam_data.ortho_scale = ortho
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
mid = (Vector((0, 0.25, 0.15)) + H) / 2
shot("side", mid + Vector((2.0, 0, 0)), mid, (1100, 800), ortho=1.55)
shot("head", H + Vector((0.35, -0.45, 0.25)), H, (800, 700), lens=50)
# first person: eye above/behind the grip, tool held low right (camera looks -Y: screen-right is -X)
root.location = (-0.2, -0.25, -0.5)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -1.55))
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.16, 0.05, 1)
bpy.context.object.data.materials.append(g)
shot("fp", (0, 0, 0), (0, -1, -0.78), (1280, 720), lens=22)
root.location = (0, 0, 0)
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
