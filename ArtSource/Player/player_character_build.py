"""Player_Character: stylized young gardener, Unity Humanoid rig, T-pose.
Run: blender -b --factory-startup -P player_character_build.py
Blender is Z-up here, character faces -Y (Unity +Z); character's left = +X here (Unity -X)."""
import os, sys, math
import bpy, bmesh
from mathutils import Matrix, Vector, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib, player_common
importlib.reload(player_common)
from player_common import *

OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\Player"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ================================================================ skeleton (T-pose, metres)
SH_Z = 1.455
B = {}
B["Root"] = (Vector((0, 0, 0)), Vector((0, 0, 0.12)), Vector((0, -1, 0)))
B["Hips"] = (Vector((0, 0, 0.95)), Vector((0, 0, 1.05)), Vector((0, -1, 0)))
B["Spine"] = (Vector((0, 0, 1.05)), Vector((0, 0, 1.22)), Vector((0, -1, 0)))
B["Chest"] = (Vector((0, 0, 1.22)), Vector((0, 0, 1.43)), Vector((0, -1, 0)))
B["Neck"] = (Vector((0, 0, 1.47)), Vector((0, 0, 1.57)), Vector((0, -1, 0)))
B["Head"] = (Vector((0, 0, 1.57)), Vector((0, 0, 1.78)), Vector((0, -1, 0)))
parents = {"Root": None, "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "Neck": "Chest", "Head": "Neck"}
connected = {"Spine", "Chest", "Head"}
for s, sx in (("_L", 1), ("_R", -1)):
    B["Shoulder" + s] = (Vector((sx * 0.03, 0, 1.44)), Vector((sx * 0.16, 0, SH_Z)), Vector((0, 0, 1)))
    B["UpperArm" + s] = (Vector((sx * 0.16, 0, SH_Z)), Vector((sx * 0.44, 0, SH_Z)), Vector((0, 0, 1)))
    B["LowerArm" + s] = (Vector((sx * 0.44, 0, SH_Z)), Vector((sx * 0.69, 0, SH_Z)), Vector((0, 0, 1)))
    B["UpperLeg" + s] = (Vector((sx * 0.09, 0, 0.92)), Vector((sx * 0.1, -0.005, 0.52)), Vector((0, -1, 0)))
    B["LowerLeg" + s] = (Vector((sx * 0.1, -0.005, 0.52)), Vector((sx * 0.1, 0.01, 0.1)), Vector((0, -1, 0)))
    B["Foot" + s] = (Vector((sx * 0.1, 0.01, 0.1)), Vector((sx * 0.1, -0.1, 0.03)), Vector((0, 0, 1)))
    B["Toes" + s] = (Vector((sx * 0.1, -0.1, 0.03)), Vector((sx * 0.1, -0.17, 0.03)), Vector((0, 0, 1)))
    parents.update({"Shoulder" + s: "Chest", "UpperArm" + s: "Shoulder" + s, "LowerArm" + s: "UpperArm" + s,
                    "UpperLeg" + s: "Hips", "LowerLeg" + s: "UpperLeg" + s, "Foot" + s: "LowerLeg" + s, "Toes" + s: "Foot" + s})
    connected |= {"UpperArm" + s, "LowerArm" + s, "LowerLeg" + s, "Foot" + s, "Toes" + s}

# hands: palm down, fingers along +-X, thumb to the front (-Y)
HAND_S = 1.12                       # slightly oversized gloves for readability
hands = {}
for s, sx in (("_L", 1), ("_R", -1)):
    W = Vector((sx * 0.69, 0, SH_Z))
    layout, _ = hand_layout(W, Vector((sx, 0, 0)), Vector((0, 0, 1)), s == "_L", HAND_S)
    for name, v in layout.items():
        B[name] = v
        if name.startswith("Hand"):
            parents[name] = "LowerArm" + s; connected.add(name)
        else:
            base = name[:-2]                      # e.g. Index1
            idx = int(base[-1])
            parents[name] = ("Hand" + s) if idx == 1 else f"{base[:-1]}{idx - 1}{s}"
            if idx > 1:
                connected.add(name)

# ================================================================ body: skin-modifier base mesh
def build_body():
    V, E, R = [], [], []
    def add(p, r, link=None):
        V.append(p); R.append(r)
        if link is not None:
            E.append((link, len(V) - 1))
        return len(V) - 1
    pelvis = add((0, 0, 0.93), (0.162, 0.115))
    a = pelvis
    for z, rx, ry in ((0.97, 0.158, 0.111), (1.01, 0.152, 0.106), (1.05, 0.147, 0.101), (1.09, 0.144, 0.099),
                      (1.13, 0.145, 0.099), (1.17, 0.148, 0.1), (1.21, 0.154, 0.103), (1.25, 0.16, 0.106),
                      (1.29, 0.165, 0.108), (1.33, 0.168, 0.109), (1.37, 0.167, 0.107)):
        a = add((0, 0, z), (rx, ry), a)
    up = add((0, 0, 1.42), (0.16, 0.1), a)
    nb = add((0, 0, 1.475), (0.07, 0.065), up)
    nb = add((0, 0, 1.52), (0.058, 0.056), nb)
    add((0, 0, 1.58), (0.052, 0.052), nb)
    for sx in (1, -1):
        prev = up
        for x, r in ((0.15, 0.066), (0.19, 0.063), (0.23, 0.06), (0.27, 0.057), (0.31, 0.055), (0.35, 0.053),
                     (0.39, 0.05), (0.42, 0.048), (0.445, 0.046), (0.47, 0.045), (0.5, 0.044), (0.54, 0.042),
                     (0.58, 0.04), (0.62, 0.037), (0.67, 0.034)):
            prev = add((sx * x, 0, SH_Z), (r, r), prev)
        prev = pelvis
        for (x, z, r) in ((0.088, 0.88, 0.104), (0.091, 0.82, 0.099), (0.094, 0.76, 0.094), (0.097, 0.7, 0.089),
                          (0.099, 0.64, 0.084), (0.1, 0.58, 0.08), (0.1, 0.545, 0.078), (0.1, 0.52, 0.077), (0.1, 0.495, 0.077),
                          (0.1, 0.46, 0.076), (0.1, 0.4, 0.074), (0.1, 0.34, 0.072), (0.1, 0.28, 0.072), (0.1, 0.22, 0.074),
                          (0.1, 0.17, 0.076)):
            prev = add((sx * x, 0.0, z), (r, r), prev)
    me = bpy.data.meshes.new("body")
    me.from_pydata(V, E, [])
    ob = bpy.data.objects.new("body", me)
    scene.collection.objects.link(ob)
    mod = ob.modifiers.new("Skin", 'SKIN')
    mod.branch_smoothing = 0.6
    mod.use_smooth_shade = True
    if not me.skin_vertices:
        me.skin_vertices.new()
    for i, r in enumerate(R):
        me.skin_vertices[0].data[i].radius = r
    me.skin_vertices[0].data[0].use_root = True
    sub = ob.modifiers.new("Sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Skin")
    bpy.ops.object.modifier_apply(modifier="Sub")
    ob.select_set(False)
    # clothing colours per face
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); n = f.normal
        ax = abs(c.x)
        if c.z > 1.468 and ax < 0.09:
            key = "skin"
        elif c.z > 1.3 and ax > 0.13:
            key = "shirt" if ax < 0.45 else ("skin" if ax < 0.64 else "glove")
        elif c.z >= 0.985:
            key = "shirt"          # the open front (t-shirt strip + shirt edges) is added as surface-fitted geometry
        else:
            key = "pants"
        f.material_index = KEYS.index(key)
        f.smooth = True
    bm.to_mesh(ob.data); bm.free()
    return ob

parts = []        # (object, weighting mode)

body = build_body()
parts.append((body, "body"))

# ================================================================ head, face, hair (rigid to Head)
HC = Vector((0, 0, 1.665))
head = Part("head")
prof = [(0.0, -0.118), (0.045, -0.114), (0.078, -0.092), (0.096, -0.055), (0.104, -0.012), (0.105, 0.03),
        (0.099, 0.068), (0.083, 0.1), (0.055, 0.122), (0.0, 0.132)]
head.lathe(prof, 20, lambda j, i: "skin", Matrix.Translation(HC) @ Matrix.Diagonal((1.0, 1.08, 1.0, 1.0)))
for sx in (1, -1):
    head.ellipsoid(HC + Vector((sx * 0.104, 0.004, 0.0)), (0.012, 0.022, 0.03), "skin_dark", segs=8, rings=5)       # ears
    head.ellipsoid(HC + Vector((sx * 0.037, -0.103, 0.018)), (0.011, 0.006, 0.014), "eye", segs=8, rings=5)       # eyes
    head.ellipsoid(HC + Vector((sx * 0.037 + 0.004, -0.108, 0.023)), (0.0035, 0.002, 0.0035), "tshirt", segs=6, rings=4)  # catch-light
    head.box(HC + Vector((sx * 0.039, -0.1, 0.046)), (0.03, 0.01, 0.008), "hair_dark",
             R=Matrix.Rotation(sx * -0.12, 4, 'Y'), bevel=0.003)                                                  # brows
head.ellipsoid(HC + Vector((0, -0.114, -0.008)), (0.014, 0.014, 0.018), "skin_dark", segs=8, rings=5)            # nose
head.tube([HC + Vector((-0.022, -0.098, -0.048)), HC + Vector((0, -0.104, -0.054)), HC + Vector((0.022, -0.098, -0.048))],
          [0.0035, 0.004, 0.0035], 5, lambda k, i: "mouth")
o_head = head.to_object(scene); parts.append((o_head, "Head"))

hair = Part("hair")
hp = [(0.104, -0.035), (0.112, 0.0), (0.114, 0.04), (0.108, 0.078), (0.09, 0.11), (0.06, 0.135), (0.0, 0.146)]
hb = bmesh.new()
rings = []
n = 22
for r, z in hp:
    if r == 0:
        rings.append([hb.verts.new(HC + Vector((0, 0, z)))])
    else:
        rings.append([hb.verts.new(HC + Vector((math.cos(math.tau * i / n) * r * (1 + J(0.04)),
                                                math.sin(math.tau * i / n) * r * 1.1 * (1 + J(0.04)), z + J(0.004)))) for i in range(n)])
for j in range(len(rings) - 1):
    a, b = rings[j], rings[j + 1]
    for i in range(n):
        f = hb.faces.new((a[i], a[(i + 1) % n], b[0])) if len(b) == 1 else hb.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        f.material_index = KEYS.index("hair_dark" if j == 0 else "hair")
hb.normal_update()
# open the face: remove the low front faces (forehead line ~4.5 cm above the eyes)
kill = [f for f in hb.faces if f.calc_center_median().y < -0.03 and f.calc_center_median().z < HC.z + 0.075]
bmesh.ops.delete(hb, geom=kill, context='FACES')
bmesh.ops.recalc_face_normals(hb, faces=hb.faces)
for f in hb.faces:          # make sure the cap faces outwards
    if (f.calc_center_median() - HC).dot(f.normal) < 0:
        f.normal_flip()
mh = bpy.data.meshes.new("tmp"); hb.to_mesh(mh); hb.free(); hair.bm.from_mesh(mh); bpy.data.meshes.remove(mh)
# side-swept fringe over the forehead
hair.ellipsoid(HC + Vector((0.02, -0.088, 0.098)), (0.085, 0.035, 0.026), "hair",
               M=Matrix.Rotation(-0.25, 4, 'Y') @ Matrix.Rotation(0.35, 4, 'X'), segs=10, rings=6)
hair.ellipsoid(HC + Vector((0.065, -0.07, 0.085)), (0.04, 0.03, 0.022), "hair_dark",
               M=Matrix.Rotation(-0.6, 4, 'Y'), segs=8, rings=5)
for k in range(4):          # a few soft crown tufts
    a = rng.uniform(0, math.tau)
    p = HC + Vector((math.cos(a) * 0.05, math.sin(a) * 0.055 + 0.02, 0.135))
    hair.ellipsoid(p, (0.035, 0.03, 0.018), "hair" if k % 2 else "hair_dark", M=Matrix.Rotation(a, 4, 'Z'), segs=8, rings=4)
o_hair = hair.to_object(scene); parts.append((o_hair, "Head"))

# ================================================================ clothing details
cloth = Part("cloth")
# collar (open at the front)
pts = [Vector((math.cos(a) * 0.078, math.sin(a) * 0.072, 1.485 + 0.012 * math.sin(a))) for a in
       [math.radians(-60 - 300 * k / 14) for k in range(15)]]
cloth.tube(pts, [0.016] * len(pts), 8, lambda k, i: "shirt_dark", caps=True, scale_u=1.6)
# rolled sleeves (just above the elbow)
for sx in (1, -1):
    M = Matrix.Translation((sx * 0.43, 0, SH_Z)) @ Matrix.Rotation(sx * math.pi / 2, 4, 'Y')
    cloth.lathe([(0.05, -0.022), (0.058, -0.016), (0.06, 0.0), (0.058, 0.016), (0.05, 0.022)], 14,
                lambda j, i: "shirt_dark" if j in (0, 3) else "shirt", M, cap_bottom=False, cap_top=False)
# pant cuffs bunched over the boot tops
for sx in (1, -1):
    cloth.lathe([(0.076, 0.16), (0.082, 0.18), (0.08, 0.21), (0.074, 0.23)], 14, lambda j, i: "pants_dark" if j == 0 else "pants",
                Matrix.Translation((sx * 0.1, 0, 0)), cap_bottom=False, cap_top=False)
# open overshirt front: light t-shirt strip + darker shirt edges, raycast onto the torso surface
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
def front_hit(x, z, off):
    hit = bvh.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
    return (hit[0] if hit[0] is not None else Vector((x, -0.1, z))) + Vector((0, -off, 0))
def half_w(z):
    return 0.028 + 0.034 * smoothstep(1.28, 1.455, z)
zs = [1.0 + 0.455 * k / 16 for k in range(17)]
tb = bmesh.new()
grid = [[tb.verts.new(front_hit(t * half_w(z), z, 0.0025)) for t in (-1.0, -0.5, 0.0, 0.5, 1.0)] for z in zs]
for r in range(len(zs) - 1):
    for c in range(4):
        q = (grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c])
        f = tb.faces.new(q)
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
        f.material_index = KEYS.index("tshirt")
mt = bpy.data.meshes.new("tmp"); tb.to_mesh(mt); tb.free(); cloth.bm.from_mesh(mt); bpy.data.meshes.remove(mt)
for sx in (1, -1):
    pts = [front_hit(sx * (half_w(z) + 0.004), z, 0.006) for z in zs]
    cloth.tube(pts, [0.009] * len(pts), 6, lambda k, i: "shirt_dark", caps=True, scale_u=1.8, up=Vector((0, -1, 0)))
# chest pocket
cloth.box((0.075, -0.108, 1.35), (0.06, 0.012, 0.065), "shirt_dark", bevel=0.004)
cloth.box((0.075, -0.113, 1.38), (0.064, 0.008, 0.02), "shirt_dark", bevel=0.003)
# untucked overshirt hem, open at the front (thin shell: outer, inner, rim)
def hem_ring(z, grow):
    out = []
    for k in range(29):
        a = math.radians(-62 + 304 * k / 28)                 # front (-90 deg) left open
        out.append(Vector((math.cos(a) * (0.153 + grow), math.sin(a) * (0.108 + grow * 0.8), z)))
    return out
hb2 = bmesh.new()
top_o, bot_o = hem_ring(1.06, 0.004), hem_ring(0.965, 0.016)
top_i, bot_i = hem_ring(1.06, -0.004), hem_ring(0.965, 0.008)
V = {key: [hb2.verts.new(p) for p in ring] for key, ring in (("to", top_o), ("bo", bot_o), ("ti", top_i), ("bi", bot_i))}
for k in range(28):
    for a, b, flip in (("to", "bo", False), ("ti", "bi", True), ("bo", "bi", False)):
        q = (V[a][k], V[a][k + 1], V[b][k + 1], V[b][k])
        f = hb2.faces.new(tuple(reversed(q)) if flip else q)
        f.material_index = KEYS.index("shirt_dark" if a == "bo" else "shirt")
for k in (0, 28):                                            # close the front edges
    q = (V["to"][k], V["bo"][k], V["bi"][k], V["ti"][k])
    hb2.faces.new(q if k == 0 else tuple(reversed(q))).material_index = KEYS.index("shirt_dark")
bmesh.ops.recalc_face_normals(hb2, faces=hb2.faces)
mh2 = bpy.data.meshes.new("tmp"); hb2.to_mesh(mh2); hb2.free(); cloth.bm.from_mesh(mh2); bpy.data.meshes.remove(mh2)
# belt + buckle
cloth.lathe([(0.157, -0.02), (0.157, 0.02)], 20, lambda j, i: "belt", Matrix.Translation((0, 0, 0.985)) @ Matrix.Diagonal((1.0, 0.72, 1.0, 1.0)),
            cap_bottom=False, cap_top=False)
cloth.box((0, -0.115, 0.985), (0.05, 0.012, 0.038), "buckle", bevel=0.004)
o_cloth = cloth.to_object(scene); parts.append((o_cloth, "general"))

flat = Part("pockets", smooth=False)
for sx in (1, -1):
    flat.box((sx * 0.165, -0.005, 0.68), (0.03, 0.11, 0.13), "pants_dark", R=Matrix.Rotation(sx * -0.06, 4, 'Y'), bevel=0.008)
    flat.box((sx * 0.168, -0.005, 0.745), (0.034, 0.115, 0.03), "pants_dark", R=Matrix.Rotation(sx * -0.06, 4, 'Y'), bevel=0.006)
flat.box((0.1, -0.07, 0.45), (0.075, 0.012, 0.07), "patch", R=Matrix.Rotation(0.08, 4, 'Y'), bevel=0.004)  # knee patch (left)
o_flat = flat.to_object(scene); parts.append((o_flat, "general"))

# ================================================================ boots
for s, sx in (("_L", 1), ("_R", -1)):
    boot = Part("boot" + s)
    c = Vector((sx * 0.1, 0.0, 0.0))
    boot.lathe([(0.064, 0.06), (0.066, 0.12), (0.064, 0.2), (0.068, 0.215), (0.06, 0.215)], 12,
               lambda j, i: "boot_dark" if j >= 2 else "boot", Matrix.Translation(c), cap_bottom=False, cap_top=True)
    boot.box(c + Vector((0, -0.045, 0.055)), (0.118, 0.25, 0.1), "boot", bevel=0.035, seg=2,
             key_fn=lambda f: "boot")
    boot.box(c + Vector((0, -0.045, 0.012)), (0.124, 0.262, 0.026), "sole", bevel=0.008)
    for k in range(3):
        boot.box(c + Vector((0, -0.07 - k * 0.025 + 0.06, 0.12 - k * 0.018)), (0.05, 0.01, 0.008), "lace",
                 R=Matrix.Rotation(-0.6, 4, 'X'))
    o_boot = boot.to_object(scene)
    parts.append((o_boot, "boot" + s))

# ================================================================ gloves (fingers weighted per finger)
glove_parts = []
for s, sx in (("_L", 1), ("_R", -1)):
    palm = Part("glove" + s)
    fparts = {n: Part(f"{n}{s}") for n in ("Thumb", "Index", "Middle", "Ring", "Little")}
    build_hand(palm, fparts, Vector((sx * 0.69, 0, SH_Z)), Vector((sx, 0, 0)), Vector((0, 0, 1)), s == "_L", HAND_S)
    parts.append((palm.to_object(scene), "palm" + s))
    for n, p in fparts.items():
        parts.append((p.to_object(scene), f"finger:{n}{s}"))

# ================================================================ armature + weights
arm = build_armature(scene, "Player_Rig", B, parents, connected)
bone_defs = {k: (v[0], v[1]) for k, v in B.items()}
ALL = [k for k in B if k != "Root"]

def body_fade(name, p):
    side = 1 if name.endswith("_L") else (-1 if name.endswith("_R") else 0)
    sx = side * p.x
    sidef = smoothstep(-0.03, 0.03, sx) if side else 1.0
    base = name[:-2] if side else name
    if base in ("UpperLeg",):
        return smoothstep(1.03, 0.93, p.z) * sidef
    if base in ("LowerLeg", "Foot", "Toes"):
        return smoothstep(0.75, 0.6, p.z) * sidef
    if base == "Shoulder":
        return smoothstep(0.02, 0.1, sx) * smoothstep(1.28, 1.36, p.z)
    if base in ("UpperArm", "LowerArm", "Hand"):
        return smoothstep(0.1, 0.17, sx) * smoothstep(1.3, 1.37, p.z)
    if base.startswith(("Thumb", "Index", "Middle", "Ring", "Little")):
        return 0.0
    if name == "Neck":
        return smoothstep(1.43, 1.49, p.z)
    if name == "Head":
        return smoothstep(1.56, 1.6, p.z)
    if name in ("Spine", "Chest"):
        return smoothstep(0.96, 1.04, p.z)
    return 1.0

for ob, mode in parts:
    if mode == "Head":
        rigid_weight(ob, "Head")
    elif mode in ("body", "general"):
        weight_object(ob, bone_defs, ALL, fade=body_fade, power=4.0)
    elif mode.startswith("boot"):
        s = mode[-2:]
        weight_object(ob, bone_defs, ["LowerLeg" + s, "Foot" + s, "Toes" + s], power=4.0)
    elif mode.startswith("palm"):
        s = mode[-2:]
        weight_object(ob, bone_defs, ["Hand" + s, "LowerArm" + s], fade=lambda n, p: 0.15 if n.startswith("Lower") else 1.0, power=4.0)
    elif mode.startswith("finger:"):
        n, s = mode[7:-2], mode[-2:]
        weight_object(ob, bone_defs, ["Hand" + s] + [f"{n}{k}{s}" for k in (1, 2, 3)],
                      fade=lambda b, p: 0.3 if b.startswith("Hand") else 1.0, power=5.0)

img = make_atlas(os.path.join(OUT, "Player_Atlas.png"), "Player_Atlas")
mat = make_material(img)
for ob, _ in parts:
    palette_uvs(ob, mat)

# join into one skinned mesh
for o in bpy.context.selected_objects:
    o.select_set(False)
objs = [o for o, _ in parts]
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = mesh.data.name = "Player_Character_Mesh"
bpy.ops.object.select_all(action='DESELECT')
bm = bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
bm.to_mesh(mesh.data); bm.free()
bind(mesh, arm)
# drop empty groups (bones with no weights) -- Unity doesn't need them
used = {x.group for v in mesh.data.vertices for x in v.groups if x.weight > 0}
for g in list(mesh.vertex_groups):
    if g.index not in used:
        mesh.vertex_groups.remove(g)
unweighted = sum(1 for v in mesh.data.vertices if not v.groups)
d = mesh.dimensions
print(f"CHAR tris={len(mesh.data.polygons)} verts={len(mesh.data.vertices)} unweighted={unweighted} "
      f"size W={d.x:.2f} D={d.y:.2f} H={d.z:.2f} bones={len(arm.data.bones)}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Player_Character.blend"))

# ================================================================ QA renders: rest pose + deformation test pose
cam = setup_render(scene, (900, 1100))
bpy.ops.mesh.primitive_plane_add(size=10)
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.16, 0.07, 1)
bpy.context.object.data.materials.append(gm)
ground = bpy.context.object
cam.data.lens = 50
for tag, loc in (("front", (0.9, -3.4, 1.2)), ("back", (-1.2, 3.2, 1.3))):
    aim(cam, loc, (0, 0, 0.92))
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
aim(cam, (0.25, -0.75, 1.68), (0, 0, 1.64)); cam.data.lens = 60
scene.render.resolution_x, scene.render.resolution_y = 800, 800
scene.render.filepath = os.path.join(HERE, "render_face.png")
bpy.ops.render.render(write_still=True)
# deformation test
pb = arm.pose.bones
def rot(name, axis, deg):
    pb[name].rotation_mode = 'XYZ'
    e = list(pb[name].rotation_euler); e["XYZ".index(axis)] = math.radians(deg); pb[name].rotation_euler = e
for s, sg in (("_L", 1), ("_R", -1)):
    rot("UpperArm" + s, "X", 0); rot("UpperArm" + s, "Z", -sg * 55)
    rot("LowerArm" + s, "Z", -sg * 95 if s == "_L" else -sg * 60)
    for f in ("Index", "Middle", "Ring", "Little"):
        for k in (1, 2, 3):
            rot(f"{f}{k}{s}", "X", -70 if s == "_L" else -25)
    rot("Thumb2" + s, "X", -30)
rot("UpperLeg_L", "X", 70); rot("LowerLeg_L", "X", -90)
rot("UpperLeg_R", "X", -25); rot("LowerLeg_R", "X", -20)
rot("Spine", "X", 10); rot("Head", "Z", 20)
bpy.context.view_layer.update()
scene.render.resolution_x, scene.render.resolution_y = 900, 1100
cam.data.lens = 50
for tag, loc in (("pose_front", (1.2, -3.2, 1.3)), ("pose_side", (3.3, -0.3, 1.1))):
    aim(cam, loc, (0, 0, 0.92))
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
for p in pb:
    p.rotation_mode = 'QUATERNION'
    p.rotation_quaternion = (1, 0, 0, 0); p.rotation_euler = (0, 0, 0); p.location = (0, 0, 0)
bpy.context.view_layer.update()
print("RENDERED")

# ================================================================ export
bpy.data.objects.remove(ground, do_unlink=True)
export_yup(scene, [arm, mesh], os.path.join(OUT, "Player_Character.fbx"), anim=False)
print("EXPORTED")
