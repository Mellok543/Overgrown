"""Player_Arms_FP: first-person arms (same sleeves / gloves as Player_Character) + 7 animation clips.
Run: blender -b --factory-startup -P player_arms_fp_build.py

FP_Root sits at the camera. Blender coords here: camera at origin looking -Y, up +Z, screen-right = -X
(Unity: x = -bx, y = bz, z = -by). Rest pose = idle pose. All clips are plain FK keys (no constraints).
Tool placements for the hold clips (relative to FP_Root / the camera) are printed as TOOL lines."""
import os, sys, math
import bpy, bmesh
from mathutils import Matrix, Vector, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib, player_common
importlib.reload(player_common)
from player_common import *

OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\Player"
ART = r"E:\UnityProject\Overgrown\ArtSource"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30

HS = 1.1                                # glove scale (matches the character's chunky gloves)
L_UP, L_LO = 0.34, 0.34
SHOULDER = {"_R": Vector((-0.18, -0.05, -0.32)), "_L": Vector((0.18, -0.05, -0.32))}
POLE = {"_R": Vector((-1.0, 0.4, -0.9)), "_L": Vector((1.0, 0.4, -0.9))}

def mirror(v):
    return Vector((-v.x, v.y, v.z))

def solve_elbow(S, W, pole):
    d = (W - S).length
    d = min(d, L_UP + L_LO - 1e-4)
    dirv = (W - S).normalized()
    W2 = S + dirv * d
    ca = (L_UP ** 2 + d ** 2 - L_LO ** 2) / (2 * L_UP * d)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    p = (pole - dirv * pole.dot(dirv)).normalized()
    return S + dirv * L_UP * ca + p * L_UP * sa, W2

def arm_frames(S, E, W):
    """Bone matrices (armature space) for upper / lower arm: Y along the bone, X = elbow hinge axis."""
    h = (E - S).cross(W - E)
    h = h.normalized() if h.length > 1e-6 else Vector((1, 0, 0))
    out = []
    for a, b in ((S, E), (E, W)):
        Y = (b - a).normalized()
        X = (h - Y * h.dot(Y)).normalized()
        Z = X.cross(Y)
        out.append(frame_matrix(X, Y, Z, a))
    return out

class HP:
    """Hand pose: wrist position, finger direction, back-of-hand direction, curls."""
    def __init__(self, W, F, U, curl=0.3, thumb=None):
        self.W, self.F, self.U = Vector(W), Vector(F).normalized(), Vector(U)
        self.curl, self.thumb = curl, (curl * 0.7 if thumb is None else thumb)
    def mirrored(self):
        return HP(mirror(self.W), mirror(self.F), mirror(self.U), self.curl, self.thumb)
    def moved(self, dW=(0, 0, 0), curl=None, thumb=None, F=None, U=None):
        return HP(self.W + Vector(dW), F if F is not None else self.F, U if U is not None else self.U,
                  self.curl if curl is None else curl, self.thumb if thumb is None and curl is None else (thumb if thumb is not None else curl * 0.7))

def wrist_for_grip(P, F, U):
    """Wrist position that puts the fist's grip axis through point P."""
    X, F2, U2 = orthonormal(Vector(F), Vector(U))
    return P - F2 * 0.058 * HS + U2 * 0.022 * HS

# ================================================================ poses
IDLE_R = HP((-0.18, -0.45, -0.205), (0.15, -1, -0.15), (-1, 0.05, 0.35), curl=0.3)
IDLE_L = IDLE_R.mirrored()

# sickle: fist around a vertical handle, back of hand outward, thumb on top
SF, SU = Vector((0.45, -1, 0)).normalized(), Vector((-1, -0.45, 0)).normalized()
SICKLE_GRIP = Vector((-0.17, -0.47, -0.26))
SICKLE_R = HP(wrist_for_grip(SICKLE_GRIP, SF, SU), SF, SU, curl=0.88, thumb=0.6)
LOW_L = HP((0.21, -0.4, -0.38), (-0.1, -1, -0.5), (1, 0.05, 0.3), curl=0.35)

# trimmer: rear grip in the right fist, left hand on the D-handle; trimmer yawed 30 deg towards the left
TR_YAW = math.radians(30)
RZ = Matrix.Rotation(TR_YAW, 3, 'Z')
TR_G = Vector((-0.06, -0.48, -0.42))
D_SHAFT = RZ @ Vector((0, -math.cos(math.radians(38)), -math.sin(math.radians(38))))
TR_T = TR_G + RZ @ (Vector((0, -math.cos(math.radians(38)), -math.sin(math.radians(38)))) * 0.36 + Vector((0, 0, 0.19)))
AX = RZ @ Vector((1, 0, 0))
u = Vector((-0.5, 0, 1)); u = (u - D_SHAFT * u.dot(D_SHAFT)).normalized()
f = D_SHAFT.cross(u).normalized()
TRIM_R = HP(wrist_for_grip(TR_G, f, u), f, u, curl=0.85, thumb=0.55)
u = Vector((0, 0.3, 1)); u = (u - AX * u.dot(AX)).normalized()
f = AX.cross(u).normalized()
TRIM_L = HP(wrist_for_grip(TR_T, f, u), f, u, curl=0.85, thumb=0.55)

# mower: both hands overhand on the T-bar (bar along X), mower standing on the ground below the camera
MW_BAR = Vector((0, -0.46, -0.6))
mu = Vector((0, 0.25, 1)).normalized()
mf_r = Vector((1, 0, 0)).cross(mu).normalized()                 # fingers wrap forward/down over the bar
if mf_r.y > 0:
    mf_r = -mf_r
MOWER_R = HP(wrist_for_grip(MW_BAR + Vector((-0.17, 0, 0)), mf_r, mu), mf_r, mu, curl=0.85, thumb=0.55)
MOWER_L = MOWER_R.mirrored()
MOWER_L = HP(wrist_for_grip(MW_BAR + Vector((0.17, 0, 0)), MOWER_L.F, MOWER_L.U), MOWER_L.F, MOWER_L.U, 0.85, 0.55)

# shears: right fist around the handles, blades pointing forward-up and inward
SHEARS_R = HP((-0.13, -0.46, -0.24), (0.35, -1, 0.3), (-0.75, -0.1, 0.65), curl=0.6, thumb=0.45)

# grass / pickup reach
GRASS_REACH = HP((-0.1, -0.56, -0.42), (0.1, -0.55, -1), (-0.8, -0.45, 0.25), curl=0.05, thumb=0.05)
PICK_REACH = HP((-0.07, -0.55, -0.36), (0.15, -0.7, -0.75), (-0.7, -0.3, 0.5), curl=0.05, thumb=0.05)

# ================================================================ rig (rest = idle)
bone_defs, parents, connected = {}, {}, set()
bone_defs["FP_Root"] = (Vector((0, 0, 0)), Vector((0, -0.1, 0)), Vector((0, 0, 1)))
parents["FP_Root"] = None
rest_joints = {}
for s, hp in (("_R", IDLE_R), ("_L", IDLE_L)):
    S = SHOULDER[s]
    E, W = solve_elbow(S, hp.W, POLE[s])
    hp.W = W
    rest_joints[s] = (S, E, W)
    mu_, ml_ = arm_frames(S, E, W)
    bone_defs["UpperArm" + s] = (S, E, mu_.col[2].to_3d())
    bone_defs["LowerArm" + s] = (E, W, ml_.col[2].to_3d())
    parents["UpperArm" + s] = "FP_Root"
    parents["LowerArm" + s] = "UpperArm" + s; connected.add("LowerArm" + s)
    layout, _ = hand_layout(W, hp.F, hp.U, s == "_L", HS)
    for name, v in layout.items():
        bone_defs[name] = v
        if name.startswith("Hand"):
            parents[name] = "LowerArm" + s; connected.add(name)
        else:
            base = name[:-2]; idx = int(base[-1])
            parents[name] = ("Hand" + s) if idx == 1 else f"{base[:-1]}{idx - 1}{s}"
            if idx > 1:
                connected.add(name)
arm = build_armature(scene, "Player_Arms_FP", bone_defs, parents, connected)
bdefs = {k: (v[0], v[1]) for k, v in bone_defs.items()}

# ================================================================ meshes: Arm_L/R (sleeve + forearm), Hand_L/R (glove)
img = make_atlas(os.path.join(OUT, "Player_Atlas.png"), "Player_Atlas")
mat = make_material(img)
meshes = []
for s, hp in (("_R", IDLE_R), ("_L", IDLE_L)):
    S, E, W = rest_joints[s]
    du, dl = (E - S).normalized(), (W - E).normalized()
    a0 = S.lerp(E, 0.42)
    e1, e2 = E - du * 0.07, E + dl * 0.07
    pts, radii, keys = [], [], []
    for k in range(7):                                     # upper arm (shirt sleeve)
        t = k / 6
        pts.append(a0.lerp(e1, t)); radii.append(0.057 - 0.004 * t); keys.append("shirt")
    for k in range(1, 8):                                  # rounded elbow
        t = k / 8
        p = (1 - t) ** 2 * e1 + 2 * (1 - t) * t * E + t * t * e2
        pts.append(p); radii.append(0.053 - 0.008 * t); keys.append("shirt" if t < 0.45 else "skin")
    for k in range(13):                                    # forearm (bare skin) to the wrist
        t = k / 12
        pts.append(e2.lerp(W, t)); radii.append(0.045 - 0.011 * t * t); keys.append("skin")
    part = Part("Arm" + s)
    part.tube(pts, radii, 16, lambda k, i: keys[k], caps=True)
    X, Y, Z = orthonormal(du, Vector((0, 0, 1)))
    part.lathe([(0.052, -0.026), (0.061, -0.018), (0.063, 0.0), (0.061, 0.018), (0.052, 0.026)], 16,
               lambda j, i: "shirt_dark" if j in (0, 3) else "shirt", Matrix.Translation(E - du * 0.035) @ frame_matrix(X, Z, Y),
               cap_bottom=False, cap_top=False)
    ob = part.to_object(scene)
    weight_object(ob, bdefs, ["UpperArm" + s, "LowerArm" + s], power=4.0)
    palette_uvs(ob, mat)
    meshes.append(ob)
    # glove: palm/cuff + per-finger tubes, then joined into Hand_x
    palm = Part("Hand" + s)
    fparts = {n: Part(f"{n}{s}") for n in ("Thumb", "Index", "Middle", "Ring", "Little")}
    build_hand(palm, fparts, W, hp.F, hp.U, s == "_L", HS, n=10)
    hobs = [palm.to_object(scene)]
    weight_object(hobs[0], bdefs, ["Hand" + s, "LowerArm" + s], fade=lambda n, p: 0.1 if n.startswith("Lower") else 1.0, power=4.0)
    for n, p in fparts.items():
        o = p.to_object(scene)
        weight_object(o, bdefs, ["Hand" + s] + [f"{n}{k}{s}" for k in (1, 2, 3)],
                      fade=lambda b, q: 0.3 if b.startswith("Hand") else 1.0, power=5.0)
        hobs.append(o)
    for o in hobs:
        palette_uvs(o, mat)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in hobs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = hobs[0]
    bpy.ops.object.join()
    hob = bpy.context.view_layer.objects.active
    hob.name = hob.data.name = "Hand" + s
    hob.select_set(False)
    meshes.append(hob)
for ob in meshes:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(ob.data); bm.free()
    bind(ob, arm)
tris = sum(len(o.data.polygons) for o in meshes)
print("FP tris", tris, {o.name: len(o.data.polygons) for o in meshes},
      "unweighted", sum(1 for o in meshes for v in o.data.vertices if not v.groups))

# ================================================================ posing (pure FK keys)
pb = arm.pose.bones
for p in pb:
    p.rotation_mode = 'QUATERNION'
FINGER_ANG = (70, 85, 60)
THUMB_ANG = (25, 35, 40)
last_q = {}

def apply_pose(s, hp):
    S = SHOULDER[s]
    E, W = solve_elbow(S, hp.W, POLE[s])
    mu_, ml_ = arm_frames(S, E, W)
    pb["UpperArm" + s].matrix = mu_
    bpy.context.view_layer.update()
    pb["LowerArm" + s].matrix = ml_
    bpy.context.view_layer.update()
    X, Y, Z = orthonormal(hp.F, hp.U)
    pb["Hand" + s].matrix = frame_matrix(X, Y, Z, W)
    bpy.context.view_layer.update()
    for name in ("Index", "Middle", "Ring", "Little"):
        for k in (1, 2, 3):
            pb[f"{name}{k}{s}"].rotation_quaternion = Quaternion((1, 0, 0), -math.radians(FINGER_ANG[k - 1]) * hp.curl)
    for k in (1, 2, 3):
        pb[f"Thumb{k}{s}"].rotation_quaternion = Quaternion((1, 0, 0), -math.radians(THUMB_ANG[k - 1]) * hp.thumb)

def key_pose(frame, R, L):
    apply_pose("_R", R)
    apply_pose("_L", L)
    bpy.context.view_layer.update()
    for p in pb:
        if p.name == "FP_Root":
            continue
        q = p.rotation_quaternion.copy()
        prev = last_q.get(p.name)
        if prev is not None and prev.dot(q) < 0:
            q.negate()
            p.rotation_quaternion = q
        last_q[p.name] = q
        p.keyframe_insert("rotation_quaternion", frame=frame)
        if p.name.startswith("UpperArm"):
            p.keyframe_insert("location", frame=frame)

def clip(name, keys):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    last_q.clear()
    for frame, R, L in keys:
        key_pose(frame, R, L)
    return act

GRASS_HOLD = HP((-0.17, -0.45, -0.3), (0.15, -1, -0.15), (-1, 0.0, 0.35), curl=0.95, thumb=0.7)
clips = [
    ("FP_Idle", [(0, IDLE_R, IDLE_L),
                 (30, IDLE_R.moved((0, -0.006, -0.008)), IDLE_L.moved((0, -0.005, -0.009))),
                 (60, IDLE_R, IDLE_L)]),
    ("FP_GrassCollect", [(0, IDLE_R, IDLE_L),
                         (6, GRASS_REACH, IDLE_L),
                         (9, GRASS_REACH.moved((0, -0.01, -0.02), curl=0.95, thumb=0.7), IDLE_L),
                         (13, GRASS_HOLD, IDLE_L),
                         (16, IDLE_R.moved((0.0, 0.02, 0.0), curl=0.8), IDLE_L),
                         (18, IDLE_R, IDLE_L)]),
    ("FP_Pickup", [(0, IDLE_R, IDLE_L),
                   (5, PICK_REACH, IDLE_L),
                   (7, PICK_REACH.moved((0, 0, -0.015), curl=0.85, thumb=0.6), IDLE_L),
                   (12, IDLE_R.moved((0.02, -0.03, 0.04), curl=0.8, thumb=0.6), IDLE_L),
                   (16, IDLE_R.moved((0.0, 0.0, 0.02), curl=0.75, thumb=0.6), IDLE_L)]),
    ("FP_ShearsUse", [(0, SHEARS_R, IDLE_L),
                      (5, SHEARS_R.moved((0.0, -0.01, -0.006), curl=1.0, thumb=0.7), IDLE_L),
                      (10, SHEARS_R, IDLE_L),
                      (15, SHEARS_R, IDLE_L)]),
    ("FP_SickleHold", [(0, SICKLE_R, LOW_L), (30, SICKLE_R, LOW_L)]),
    ("FP_TrimmerHold", [(0, TRIM_R, TRIM_L), (30, TRIM_R, TRIM_L)]),
    ("FP_MowerHold", [(0, MOWER_R, MOWER_L), (30, MOWER_R, MOWER_L)]),
]
actions = {name: clip(name, keys) for name, keys in clips}
arm.animation_data.action = actions["FP_Idle"]

def unity(v):
    return (round(-v.x, 3), round(v.z, 3), round(-v.y, 3))
print("TOOL Player_Sickle   pos", unity(SICKLE_GRIP), "rot (0,0,0)   [FP_SickleHold]")
print("TOOL Player_Trimmer  pos", unity(TR_G), f"rot (0,{-math.degrees(TR_YAW):.0f},0)   [FP_TrimmerHold]")
MOWER_ROOT = MW_BAR - Vector((0, 0.76, 1.0))
print("TOOL Player_Mower    pos", unity(MOWER_ROOT), "rot (0,0,0)   [FP_MowerHold]")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Player_Arms_FP.blend"))

# ================================================================ preview renders through an FOV 80 camera, tools in hand
cam = setup_render(scene, (1280, 720))
cam.data.sensor_width = 36
cam.data.lens = 18 / math.tan(math.radians(40))           # 80 deg horizontal FOV
cam.data.clip_start = 0.02
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.6))
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.16, 0.07, 1)
bpy.context.object.data.materials.append(gm)
ground = bpy.context.object

def load_tool(blend, root_name):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = list(src.objects)
    root = None
    for o in dst.objects:
        if o is None:
            continue
        if o.type in ('MESH', 'EMPTY'):
            scene.collection.objects.link(o)
            if o.name.startswith(root_name):
                root = o if root is None or o.parent is None else root
        else:
            bpy.data.objects.remove(o)
    return root

tools = {
    "sickle": load_tool(os.path.join(ART, "PlayerSickle", "Player_Sickle.blend"), "Player_Sickle"),
    "trimmer": load_tool(os.path.join(ART, "PlayerTrimmer", "Player_Trimmer.blend"), "Player_Trimmer"),
    "mower": load_tool(os.path.join(ART, "PlayerMower", "Player_Mower.blend"), "Player_Mower"),
}
for t in tools.values():
    if t:
        t.hide_render = True
        for c in t.children_recursive:
            c.hide_render = True
def show_tool(key, loc=None, yaw=0.0):
    for k, t in tools.items():
        if t is None:
            continue
        vis = (k == key)
        t.hide_render = not vis
        for c in t.children_recursive:
            c.hide_render = not vis
        if vis:
            t.location = loc; t.rotation_euler = (0, 0, yaw)

def look(pitch_deg):
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.radians(90 + pitch_deg), 0, 0)  # 90 = looking along -Y... (camera looks -Z by default)

shots = [("FP_Idle", 0, 0, None, None, 0), ("FP_GrassCollect", 7, -20, None, None, 0), ("FP_Pickup", 6, -18, None, None, 0),
         ("FP_ShearsUse", 5, -5, None, None, 0), ("FP_SickleHold", 0, -5, "sickle", SICKLE_GRIP, 0),
         ("FP_TrimmerHold", 0, -32, "trimmer", TR_G, TR_YAW), ("FP_MowerHold", 0, -40, "mower", MOWER_ROOT, 0)]
for name, frame, pitch, tool, loc, yaw in shots:
    arm.animation_data.action = actions[name]
    scene.frame_set(frame)
    show_tool(tool, loc, yaw)
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.radians(90 + pitch), 0, math.radians(180))
    scene.render.filepath = os.path.join(HERE, f"fp_{name}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED")

# ================================================================ export
for t in tools.values():
    if t:
        for c in list(t.children_recursive) + [t]:
            bpy.data.objects.remove(c, do_unlink=True)
bpy.data.objects.remove(ground, do_unlink=True)
arm.animation_data.action = actions["FP_Idle"]
scene.frame_set(0)
export_yup(scene, [arm] + meshes, os.path.join(OUT, "Player_Arms_FP.fbx"), anim=True)
print("EXPORTED")
