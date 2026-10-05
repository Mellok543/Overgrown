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

# ================================================================ two-handed garden shears (FP_Shears_Idle / FP_Shears_Cut)
# Garden_Shears (lying-flat pickup model) is split at the pivot bolt into two rigid halves:
#   Shears_A = upper blade + the handle on its opposite side (held by the RIGHT hand)
#   Shears_B = lower blade + its opposite handle               (held by the LEFT hand)
# Shears local frame (original model coords, pivot bolt at the origin): +X blades, -X handles, Z = plate normal.
SH_SCALE = 1.6                          # first-person viewmodel scale (fists need room between the handles)
SH_OPEN, SH_CLOSED = math.radians(19), math.radians(2.5)      # blade opening 38 deg -> 5 deg
SH_GRIP_T = 0.9                        # where along the handle the fist sits (0 = pivot, 1 = handle end)
_beta = math.radians(55)                # handles lean 55 deg from vertical; blades point forward, below the crosshair
SX = Vector((0, -math.sin(_beta), math.cos(_beta)))
SY = Vector((1, 0, 0))
SZ = SX.cross(SY)                       # plate normal faces the camera
SH_FRAME = Matrix((SX, SY, SZ)).transposed()
GRIPS_MID = Vector((-0.07, -0.52, -0.27))
_grip_local_x = (-0.02 - 0.18 * SH_GRIP_T) * SH_SCALE
SH_P0 = GRIPS_MID - SX * _grip_local_x - SZ * 0.013 * SH_SCALE

def handle_local(sign, t):
    """Handle centreline (original shears coords) and its unit direction towards the pivot."""
    x = -0.02 - 0.18 * t
    y = -sign * (0.006 + 0.04 * t ** 1.2 - 0.012 * math.sin(math.pi * t))
    dx = -0.18
    dy = -sign * (0.048 * t ** 0.2 - 0.012 * math.pi * math.cos(math.pi * t))
    return Vector((x, y, 0.013)), -Vector((dx, dy, 0)).normalized()

def shears_world(phi, off=Vector()):
    """Grip points + handle axes (towards the pivot) for both halves at opening phi."""
    out = {}
    for half, sign, ang in (("A", 1, phi), ("B", -1, -phi)):
        R = Matrix.Rotation(ang, 3, 'Z')
        p, a = handle_local(sign, SH_GRIP_T)
        out[half] = (SH_P0 + off + SH_FRAME @ (R @ p) * SH_SCALE, (SH_FRAME @ (R @ a)).normalized())
    return out

def fist_on_handle(P, a, is_left):
    """Fist around a near-vertical handle: thumb side towards the pivot, back of the hand outward;
    the handle runs slightly diagonally across the palm so the fingers stay roughly horizontal."""
    U = Vector((1 if is_left else -1, -0.75, 0.0))      # back of hand out + forward: fingertips end up behind the handle, not between the fists
    U = (U - a * U.dot(a)).normalized()
    F0 = (U.cross(a) if is_left else a.cross(U)).normalized()
    best = None
    for k in range(-900, 901):                       # 0.05 deg steps: no visible stepping of the fist between frames
        g = math.radians(k * 0.05)
        F = Matrix.Rotation(g, 3, U) @ F0
        score = abs(F.z + 0.08)
        if best is None or score < best[0]:
            best = (score, F)
    F = best[1]
    return HP(wrist_for_grip(P, F, U), F, U, curl=1.0, thumb=1.0)       # thumb wraps over the index finger, never reaches towards the other fist

def shears_hands(phi, off=Vector()):
    sw = shears_world(phi, off)
    return fist_on_handle(*sw["A"], False), fist_on_handle(*sw["B"], True)


# ================================================================ tools: sickle / trimmer / mower (rigid hand attachment)
# Each tool rides on a socket bone (Tool_Sickle / Tool_Trimmer under Hand_R, Tool_Mower under FP_Root).
# In Unity the existing tool object is parented to its socket with an identity local transform.
# Hands are attached rigidly: their pose is stored in the tool's own space and re-applied every frame,
# so a hand can never slide along its handle.
EYE = 1.7                                   # game eye height above the ground
ARMS_OFF = Vector((0, 0.22, 0.2))           # camera in FP_Root space for camera-locked tools (Unity arms localPosition (0,-0.2,0.22), 8 deg tilt)
CAM_LEVEL = Vector((0, -0.15, 0.0))       # camera in FP_Root space for levelled tools (trimmer, mower): shoulders stay behind the camera
                                            # -> FPToolGroundFollow puts the arms at camera + yaw * (0, 0, -0.15) (Unity)
GROUND_Z = CAM_LEVEL.z - EYE                # ground height in FP_Root space for the levelled tools
SOCKET_BASIS = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))   # bone Y up, Z back -> identity orientation in Unity

def frame_fu(f, u):
    """Tool rotation from a 'forward' (blade / local -Y) and an 'up' (handle / local +Z) direction."""
    Z = Vector(u).normalized()
    Y = -(Vector(f) - Z * Vector(f).dot(Z)).normalized()
    return Matrix((Y.cross(Z), Y, Z)).transposed()

def attach(hp, P0, R0):
    Ri = R0.transposed()
    return (Ri @ (hp.W - P0), Ri @ hp.F, Ri @ hp.U, hp.curl, hp.thumb)

def detach(loc, P, R, curl=None, thumb=None):
    w, f, u, c, t = loc
    return HP(P + R @ w, R @ f, R @ u, c if curl is None else curl, t if thumb is None else thumb)

def fist_rigid(P, a, U_guess, is_left, curl=0.92, thumb=0.6):
    U = (U_guess - a * U_guess.dot(a)).normalized()
    F = (U.cross(a) if is_left else a.cross(U)).normalized()
    return HP(wrist_for_grip(P, F, U), F, U, curl=curl, thumb=thumb)

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def ease5(x):
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)

def qcont(q, ref):
    return -q if q.dot(ref) < 0 else q

# ---------------------------------------------------------------- sickle (right fist on the wooden handle, model axis +Z)
SK_P0 = Vector((-0.2, -0.33, -0.05))
SK_R0 = frame_fu((0.2, -0.7, -0.45), (-0.35, -0.55, 0.8))
def sickle_fist(P, R):
    a = R @ Vector((0, 0, 1))
    U = -(R @ Vector((1, 0, 0))) - (R @ Vector((0, 1, 0))) * 0.45
    return fist_rigid(P, a, U, False, curl=0.92, thumb=0.6)
SK_RH = attach(sickle_fist(SK_P0, SK_R0), SK_P0, SK_R0)
SK_LH = HP((0.2, -0.37, -0.15), (-0.1, -1, -0.45), (1, 0.05, 0.3), curl=0.35)     # relaxed, lower left, holds nothing
def sk_key(dp, f, u):
    return (SK_P0 + Vector(dp), frame_fu(f, u))
SK_WIND = sk_key((-0.05, 0.05, 0.03), (-0.25, -0.8, -0.35), (-0.7, -0.3, 0.8))   # small draw back / out
SK_MID = sk_key((0.12, -0.14, -0.03), (0.9, -0.2, -0.35), (0.25, -1, 0.15))     # blade flat, sweeping right -> left, low in view
SK_END = sk_key((0.32, -0.08, -0.04), (0.75, 0.55, -0.3), (0.65, -0.75, 0.1))

def sickle_swing(f):
    """Tool (P, R) at frame f of the 11-frame swing (30 fps, 0.367 s)."""
    q0 = SK_R0.to_quaternion()
    qw = qcont(SK_WIND[1].to_quaternion(), q0)
    qm = qcont(SK_MID[1].to_quaternion(), qw)
    qe = qcont(SK_END[1].to_quaternion(), qm)
    if f <= 2.5:                                            # 0.00-0.08 s anticipation
        s = ease(f / 2.5)
        return SK_P0.lerp(SK_WIND[0], s), q0.slerp(qw, s).to_matrix()
    if f <= 7.5:                                            # 0.08-0.25 s main pass along an arc
        s = ease5((f - 2.5) / 5.0)
        ctrl = SK_MID[0] * 2 - (SK_WIND[0] + SK_END[0]) * 0.5
        P = SK_WIND[0] * (1 - s) ** 2 + ctrl * 2 * (1 - s) * s + SK_END[0] * s * s
        return P, qw.slerp(qm, s).slerp(qm.slerp(qe, s), s).to_matrix()
    s = ease((f - 7.5) / 3.5)                               # 0.25-0.37 s settle back into idle
    return SK_END[0].lerp(SK_P0, s), qe.slerp(qcont(q0, qe), s).to_matrix()

# ---------------------------------------------------------------- trimmer (right fist on the rear grip, left on the D-handle)
_c38, _s38 = math.cos(math.radians(38)), math.sin(math.radians(38))
TRM_D = Vector((0, -_c38, -_s38))                           # shaft direction in model space
TRM_BAR = TRM_D * 0.36 + Vector((0, 0, 0.19))               # D-handle top bar centre (model space)
TRM_HEAD_BOTTOM = Vector((0, -_c38 * 0.95 - 0.035, -_s38 * 0.95 - 0.115 - 0.036))
# camera-locked like the sickle (hands visible at a normal gaze); FPToolGroundFollow only lifts it if the head would dip into the ground
TRM_YAW = math.radians(20)                                  # shaft runs forward and towards the lower left
_trm_base = Matrix.Rotation(TRM_YAW, 3, 'Z') @ Matrix.Rotation(math.radians(-10), 3, 'X')   # 10 deg shallower than modelled
TRM_R0 = Matrix.Rotation(math.radians(-60), 3, _trm_base @ TRM_D) @ _trm_base           # rolled: battery faces out to the right
TRM_P0 = Vector((-0.15, -0.40, -0.05))                      # hands low in frame, shaft + head visible, battery off-centre
def trimmer_hands(P, R):
    D = R @ TRM_D
    u = Vector((-0.5, 0, 1)); u = (u - D * u.dot(D)).normalized()
    f = D.cross(u).normalized()
    rh = HP(wrist_for_grip(P, f, u), f, u, curl=0.88, thumb=0.6)
    ax = R @ Vector((1, 0, 0))
    u = Vector((0, 0.3, 1)); u = (u - ax * u.dot(ax)).normalized()
    f = ax.cross(u).normalized()
    lh = HP(wrist_for_grip(P + R @ TRM_BAR, f, u), f, u, curl=0.88, thumb=0.6)
    return rh, lh
_tr, _tl = trimmer_hands(TRM_P0, TRM_R0)
TRM_RH, TRM_LH = attach(_tr, TRM_P0, TRM_R0), attach(_tl, TRM_P0, TRM_R0)
TRM_PIVOT = TRM_P0 + TRM_R0 @ TRM_D * 0.18                  # sway pivot between the hands
def trimmer_pose(yaw_delta, off=Vector(), roll=0.0):
    Rd = Matrix.Rotation(yaw_delta, 3, 'Z') @ Matrix.Rotation(roll, 3, (TRM_R0 @ TRM_D))
    return TRM_PIVOT + Rd @ (TRM_P0 - TRM_PIVOT) + off, Rd @ TRM_R0

# ---------------------------------------------------------------- mower (both hands overhand on the T-bar, body on the ground)
MW_BAR_LOCAL = Vector((0, 0.76, 1.0))
MW_P0 = Vector((0, -0.42 - 0.76, GROUND_Z))                 # mower root = ground contact under the deck
MW_R0 = Matrix.Identity(3)
def mower_hands(P, R):
    out = []
    for sx, is_left in ((-1, False), (1, True)):
        g = P + R @ (MW_BAR_LOCAL + Vector((sx * 0.13, 0, 0)))
        ax = R @ Vector((1, 0, 0))
        u = R @ Vector((0, 0.25, 1)); u = (u - ax * u.dot(ax)).normalized()
        f = ax.cross(u).normalized()
        if f.y > 0:
            f = -f
        out.append(HP(wrist_for_grip(g, f, u), f, u, curl=0.85, thumb=0.55))
    return out
_mr, _ml = mower_hands(MW_P0, MW_R0)
MW_RH, MW_LH = attach(_mr, MW_P0, MW_R0), attach(_ml, MW_P0, MW_R0)
def mower_pose(dy=0.0, dz=0.0, roll=0.0):
    return MW_P0 + Vector((0, dy, dz)), Matrix.Rotation(roll, 3, 'Y') @ MW_R0

SOCKETS = {"Tool_Sickle": ("Hand_R", SK_P0, SK_R0), "Tool_Trimmer": ("Hand_R", TRM_P0, TRM_R0),
           "Tool_Mower": ("FP_Root", MW_P0, MW_R0)}

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
# shears bones: Y axis = pivot (plate normal), so opening/closing is a rotation about local Y
for name, par in (("Shears_Root", "Hand_R"), ("Shears_A", "Shears_Root"), ("Shears_B", "Shears_Root")):
    bone_defs[name] = (SH_P0.copy(), SH_P0 + SZ * 0.05, SX)
    parents[name] = par
for name, (par, P0, R0) in SOCKETS.items():
    bone_defs[name] = (P0.copy(), P0 + Vector((0, 0, 0.1)), Vector((0, -1, 0)))
    parents[name] = par
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
# ---------------------------------------------------------------- Garden_Shears_FP: the existing pickup model, split at the bolt
GI_KEYS = ["metal", "metal_edge", "metal_dark", "rust", "rust_dark", "grip", "grip_worn", "grip_black"]
with bpy.data.libraries.load(os.path.join(ART, "GardenItems", "GardenItems.blend"), link=False) as (src, dst):
    dst.objects = ["Garden_Shears"]
src_ob = dst.objects[0]
sbm = bmesh.new(); sbm.from_mesh(src_ob.data)
uvl = sbm.loops.layers.uv.active
sbm.faces.ensure_lookup_table(); sbm.verts.ensure_lookup_table()
# islands (connected pieces)
island_of = {}
islands = []
for f in sbm.faces:
    if f.index in island_of:
        continue
    stack, isl = [f], []
    island_of[f.index] = len(islands)
    while stack:
        g = stack.pop(); isl.append(g)
        for v in g.verts:
            for h in v.link_faces:
                if h.index not in island_of:
                    island_of[h.index] = len(islands); stack.append(h)
    islands.append(isl)
def isl_stats(isl):
    vs = {v for f in isl for v in f.verts}
    xs = [v.co.x for v in vs]; ys = [v.co.y for v in vs]; zs = [v.co.z for v in vs]
    c = Vector((sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)))
    return vs, c, (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)), min(zs)
stats = [isl_stats(i) for i in islands]
bolt = [k for k, (vs, c, e, zmin) in enumerate(stats) if e[0] < 0.026 and e[1] < 0.026 and e[2] > 0.024]
assert bolt, "pivot bolt not found in Garden_Shears"
cb = stats[bolt[0]][1]
origin = Vector((cb.x, cb.y, 0.0))
label = {}                                   # vert index -> "A" | "B" | "AB"
for k, (vs, c, e, zmin) in enumerate(stats):
    r = c - origin
    if k in bolt:
        lab = "A"
    elif -0.06 < r.x < -0.02 and abs(r.y) < 0.008 and e[1] > 0.018:
        lab = "AB"                           # coil spring between the handles: half / half
    elif r.z > 0.017 and r.x < -0.015:
        lab = "A"                            # safety latch
    elif e[2] < 0.0075:
        lab = "A" if r.z > 0.012 else "B"    # blade plates (upper = A, lower = B)
    else:
        lab = "A" if r.y < 0 else "B"        # handle tubes + end caps
    for v in vs:
        label[v.index] = lab
for f in sbm.faces:
    u, v = f.loops[0][uvl].uv
    gi = min(int(u * 8), 7) + min(int(v * 8), 7) * 8
    f.material_index = KEYS.index("sh_" + GI_KEYS[gi])
for v in sbm.verts:
    v.co = SH_P0 + SH_FRAME @ ((v.co - origin) * SH_SCALE)
shme = bpy.data.meshes.new("Garden_Shears_FP")
sbm.to_mesh(shme); sbm.free()
for p in shme.polygons:
    p.use_smooth = False
shob = bpy.data.objects.new("Garden_Shears_FP", shme)
scene.collection.objects.link(shob)
bpy.data.objects.remove(src_ob, do_unlink=True)
for g in ("Shears_A", "Shears_B"):
    shob.vertex_groups.new(name=g)
for vi, lab in label.items():
    if lab == "AB":
        shob.vertex_groups["Shears_A"].add([vi], 0.5, 'REPLACE'); shob.vertex_groups["Shears_B"].add([vi], 0.5, 'REPLACE')
    else:
        shob.vertex_groups["Shears_" + lab].add([vi], 1.0, 'REPLACE')
for p in shme.polygons:                       # palette_uvs reads material_index
    pass
uvs = shme.uv_layers
while len(uvs):
    uvs.remove(uvs[0])
palette_uvs(shob, mat)
print("SHEARS halves:", {k: sum(1 for l in label.values() if l == k) for k in ("A", "B", "AB")}, "tris", len(shme.polygons))
meshes.append(shob)

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

def pose_shears(state):
    """state None: shears bones at rest (they just ride on Hand_R). Else (phi, offset): place the
    shears in camera space and open the halves; the fists were already solved onto the handles."""
    if state is None:
        for n in ("Shears_Root", "Shears_A", "Shears_B"):
            pb[n].rotation_quaternion = (1, 0, 0, 0); pb[n].location = (0, 0, 0)
        return
    phi, off = state
    pb["Shears_Root"].matrix = frame_matrix(SY, SZ, SX, SH_P0 + off)
    bpy.context.view_layer.update()
    pb["Shears_A"].rotation_quaternion = Quaternion((0, 1, 0), phi)
    pb["Shears_B"].rotation_quaternion = Quaternion((0, 1, 0), -phi)
    pb["Shears_A"].location = (0, 0, 0); pb["Shears_B"].location = (0, 0, 0)

def pose_sockets(tools):
    for name in SOCKETS:
        if tools and name in tools:
            P, R = tools[name]
            M = (R @ SOCKET_BASIS).to_4x4()
            M.translation = P
            pb[name].matrix = M
            bpy.context.view_layer.update()
        else:
            pb[name].rotation_quaternion = (1, 0, 0, 0)
            pb[name].location = (0, 0, 0)

REACH_WARN = []
def key_pose(frame, R, L, shears=None, tools=None):
    if shears is not None:
        R, L = shears_hands(*shears)
    for side, hp in (("_R", R), ("_L", L)):
        if (hp.W - SHOULDER[side]).length > L_UP + L_LO - 1e-3:
            REACH_WARN.append((frame, side, round((hp.W - SHOULDER[side]).length, 3)))
    apply_pose("_R", R)
    apply_pose("_L", L)
    bpy.context.view_layer.update()
    pose_shears(shears)
    bpy.context.view_layer.update()
    pose_sockets(tools)
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
        if p.name.startswith(("UpperArm", "Shears", "Tool_")):
            p.keyframe_insert("location", frame=frame)

def clip(name, keys):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    last_q.clear()
    for k in keys:
        key_pose(*k)
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
def smooth_track(points, frame):
    """Piecewise smoothstep through (frame, value) points: zero velocity at every key, no overshoot."""
    for (f0, v0), (f1, v1) in zip(points[:-1], points[1:]):
        if f0 <= frame <= f1:
            t = (frame - f0) / (f1 - f0)
            t = t * t * (3 - 2 * t)
            return v0 + (v1 - v0) * t
    return points[-1][1]
o_, c_ = SH_OPEN, SH_CLOSED
# 0.10 s squeeze starts, ~0.23 s fully closed, hold to 0.30 s, open again 0.35-0.50 s (30 fps)
CUT_PHI = [(0, o_), (3, o_ - math.radians(2.5)), (6, c_ + math.radians(3)), (7, c_), (9, c_),
           (10.5, c_ + math.radians(1.5)), (15, o_)]
CUT_PUSH = [(0, 0.0), (15, 0.0)]                                     # the tool itself stays put
shears_idle = []
for f in range(0, 61, 2):
    b = 0.5 - 0.5 * math.cos(math.tau * f / 60)                       # breathing, 2 s cycle
    shears_idle.append((f, None, None, (o_ + math.radians(0.6) * b, Vector((0, -0.001 * b, -0.003 * b)))))
shears_cut = [(f, None, None, (smooth_track(CUT_PHI, f), SX * smooth_track(CUT_PUSH, f))) for f in range(0, 16)]
clips += [("FP_Shears_Idle", shears_idle), ("FP_Shears_Cut", shears_cut)]

def breathe(f, period=60):
    return 0.5 - 0.5 * math.cos(math.tau * f / period)

def sickle_keys(f, P, R, lh):
    return (f, detach(SK_RH, P, R), lh, None, {"Tool_Sickle": (P, R)})
sickle_idle = []
for f in range(0, 61, 2):
    b = breathe(f)
    P = SK_P0 + Vector((0, -0.002 * b, -0.005 * b))
    R = Matrix.Rotation(math.radians(0.8) * b, 3, 'X') @ SK_R0
    sickle_idle.append(sickle_keys(f, P, R, SK_LH.moved((0, -0.002 * b, -0.006 * b))))
sickle_swing_keys = []
for f in range(0, 12):
    P, R = sickle_swing(f)
    push = math.sin(math.pi * min(1.0, f / 11.0))           # the free hand counter-moves a little
    sickle_swing_keys.append(sickle_keys(f, P, R, SK_LH.moved((0.04 * push, 0.02 * push, -0.05 * push))))   # free hand ducks out of the arc

def trimmer_keys(f, P, R):
    return (f, detach(TRM_RH, P, R), detach(TRM_LH, P, R), None, {"Tool_Trimmer": (P, R)})
trimmer_idle = []
for f in range(0, 61, 2):
    b = breathe(f)
    P, R = trimmer_pose(math.radians(1.2) * math.sin(math.tau * f / 60), Vector((0, 0, 0.004 * b)))
    trimmer_idle.append(trimmer_keys(f, P, R))
trimmer_work = []
for f in range(0, 33):                                      # 32 frames = 1.067 s loop
    sway = math.radians(10) * math.sin(math.tau * f / 32)
    vib = 0.0015 * (1 + math.sin(math.tau * f / 4))         # engine buzz, never pushes the head down
    P, R = trimmer_pose(sway, Vector((0, 0, vib)), math.radians(0.4) * math.sin(math.tau * f / 4 + 1.0))
    trimmer_work.append(trimmer_keys(f, P, R))

def mower_keys(f, P, R):
    return (f, detach(MW_RH, P, R), detach(MW_LH, P, R), None, {"Tool_Mower": (P, R)})
mower_idle = []
for f in range(0, 61, 2):
    P, R = mower_pose(dy=-0.003 * breathe(f))
    mower_idle.append(mower_keys(f, P, R))
mower_push = []
for f in range(0, 29):                                      # 28 frames = 0.933 s loop
    P, R = mower_pose(dy=-0.015 * math.sin(math.tau * f / 28),          # arms push forward / ease back
                      dz=0.0012 * (1 + math.sin(math.tau * f / 4)),     # engine vibration, only upwards
                      roll=math.radians(0.5) * math.sin(math.tau * f / 14))
    mower_push.append(mower_keys(f, P, R))

clips += [("FP_Sickle_Idle", sickle_idle), ("FP_Sickle_Swing", sickle_swing_keys),
          ("FP_Trimmer_Idle", trimmer_idle), ("FP_Trimmer_Work", trimmer_work),
          ("FP_Mower_Idle", mower_idle), ("FP_Mower_Push", mower_push)]
actions = {name: clip(name, keys) for name, keys in clips}
print("REACH warnings (hand target beyond arm length):", len(REACH_WARN), REACH_WARN[:10])
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
shob.hide_render = True
for name, frame, pitch, tool, loc, yaw in shots:
    arm.animation_data.action = actions[name]
    scene.frame_set(frame)
    show_tool(tool, loc, yaw)
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.radians(90 + pitch), 0, math.radians(180))
    scene.render.filepath = os.path.join(HERE, f"fp_{name}.png")
    bpy.ops.render.render(write_still=True)
# ---------------------------------------------------------------- shears QA: Unity-style vertical FOV 70 and 90, plus close-ups
shob.hide_render = False
show_tool(None)
cam.data.sensor_fit = 'VERTICAL'
for fov in (70, 90):
    cam.data.angle_y = math.radians(fov)
    for name, frame in (("FP_Shears_Idle", 0), ("FP_Shears_Cut", 4), ("FP_Shears_Cut", 8), ("FP_Shears_Cut", 12)):
        arm.animation_data.action = actions[name]
        scene.frame_set(frame)
        cam.location = (0, 0, 0)
        cam.rotation_euler = (math.radians(90), 0, math.radians(180))
        scene.render.filepath = os.path.join(HERE, f"fpq_{name}_f{frame:02d}_fov{fov}.png")
        bpy.ops.render.render(write_still=True)
cam.data.sensor_fit = 'AUTO'
cam.data.lens = 50
scene.render.resolution_x, scene.render.resolution_y = 900, 900
for name, frame in (("FP_Shears_Idle", 0), ("FP_Shears_Cut", 8)):
    arm.animation_data.action = actions[name]
    scene.frame_set(frame)
    for tag, loc in (("side", GRIPS_MID + Vector((-0.75, -0.15, 0.25))), ("below", GRIPS_MID + Vector((0.25, -0.45, -0.55))),
                     ("cam", Vector((0.0, -0.05, 0.02)))):
        aim(cam, loc, GRIPS_MID + Vector((0, -0.05, 0.03)))
        scene.render.filepath = os.path.join(HERE, f"fpq_close_{name}_f{frame:02d}_{tag}.png")
        bpy.ops.render.render(write_still=True)
# ---------------------------------------------------------------- tool QA: the game camera (arms offset (0,-0.2,0.22)), FOV 77
def tool_from_socket(socket):
    M = arm.matrix_world @ pb[socket].matrix @ SOCKET_BASIS.inverted().to_4x4()
    return M
def show_only(key):
    for k, t in tools.items():
        if t is None:
            continue
        vis = (k == key)
        t.hide_render = not vis
        for c in t.children_recursive:
            c.hide_render = not vis
shob.hide_render = True
cam.data.sensor_fit = 'VERTICAL'
cam.data.angle_y = math.radians(77)
cam.data.clip_start = 0.3                                   # same near clip as the game camera
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
TOOL_SHOTS = [
    ("FP_Sickle_Idle", 0, "sickle", "Tool_Sickle", 0, False), ("FP_Sickle_Swing", 2, "sickle", "Tool_Sickle", 0, False),
    ("FP_Sickle_Swing", 5, "sickle", "Tool_Sickle", 0, False), ("FP_Sickle_Swing", 6, "sickle", "Tool_Sickle", 0, False),
    ("FP_Sickle_Swing", 8, "sickle", "Tool_Sickle", 0, False), ("FP_Sickle_Swing", 6, "sickle", "Tool_Sickle", -30, False),
    ("FP_Trimmer_Idle", 0, "trimmer", "Tool_Trimmer", 0, False), ("FP_Trimmer_Work", 0, "trimmer", "Tool_Trimmer", 0, False),
    ("FP_Trimmer_Work", 8, "trimmer", "Tool_Trimmer", 0, False), ("FP_Trimmer_Work", 24, "trimmer", "Tool_Trimmer", 0, False),
    ("FP_Mower_Idle", 0, "mower", "Tool_Mower", -25, True), ("FP_Mower_Idle", 0, "mower", "Tool_Mower", -45, True),
    ("FP_Mower_Push", 7, "mower", "Tool_Mower", -45, True),
]
for name, frame, key, socket, pitch, levelled in TOOL_SHOTS:
    arm.animation_data.action = actions[name]
    scene.frame_set(frame)
    show_only(key)
    if tools.get(key) is not None:
        tools[key].matrix_world = tool_from_socket(socket)
    ground.hide_render = not levelled
    ground.location = (0, 0, GROUND_Z)
    cam.location = CAM_LEVEL if levelled else ARMS_OFF
    # camera-locked tools: the arms hang 8 deg pitched down under the camera; levelled tools: yaw-only arms
    cam.rotation_euler = (math.radians(90 + pitch + (0 if levelled else 8)), 0, math.radians(180))
    scene.render.filepath = os.path.join(HERE, f"fpt_{name}_f{frame:02d}_p{abs(pitch)}.png")
    bpy.ops.render.render(write_still=True)
# ground clearance of the trimmer head / mower deck through the loops (model-space helpers -> FP space)
for name in ("FP_Trimmer_Idle", "FP_Trimmer_Work"):          # camera-locked: head height above flat ground per camera pitch
    arm.animation_data.action = actions[name]
    f0, f1 = [int(x) for x in actions[name].frame_range]
    out = {}
    for pitch in (0, 15, 30, 45):
        hs = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            q = tool_from_socket("Tool_Trimmer") @ TRM_HEAD_BOTTOM - ARMS_OFF
            hs.append(EYE + (Matrix.Rotation(math.radians(8 + pitch), 3, 'X') @ q).z)
        out[pitch] = round(min(hs) * 100, 1)
    print(f"GROUND {name}: head above flat ground (cm) by camera pitch down {out}")
for name, key, socket, local in (("FP_Mower_Idle", "mower", "Tool_Mower", Vector((0, 0, 0))),
                                 ("FP_Mower_Push", "mower", "Tool_Mower", Vector((0, 0, 0)))):
    arm.animation_data.action = actions[name]
    zs = []
    f0, f1 = [int(x) for x in actions[name].frame_range]
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        zs.append((tool_from_socket(socket) @ local).z - GROUND_Z)
    print(f"GROUND {name}: lowest point above ground min={min(zs) * 100:.1f} cm max={max(zs) * 100:.1f} cm")
print("RENDERED")

# ================================================================ export
for t in tools.values():
    if t:
        for c in list(t.children_recursive) + [t]:
            bpy.data.objects.remove(c, do_unlink=True)
bpy.data.objects.remove(ground, do_unlink=True)
arm.animation_data.action = actions["FP_Idle"]
scene.frame_set(0)
objs = [arm] + meshes
to_yup(objs)
export_yup(scene, objs, os.path.join(OUT, "Player_Arms_FP.fbx"), anim=True, convert=False)
# one clip per file (take named after the scene, baked over the scene frame range)
ANIM_OUT = os.path.join(OUT, "Animations")
os.makedirs(ANIM_OUT, exist_ok=True)
for name, (f0, f1) in (("FP_Shears_Idle", (0, 60)), ("FP_Shears_Cut", (0, 15)),
                       ("FP_Sickle_Idle", (0, 60)), ("FP_Sickle_Swing", (0, 11)),
                       ("FP_Trimmer_Idle", (0, 60)), ("FP_Trimmer_Work", (0, 32)),
                       ("FP_Mower_Idle", (0, 60)), ("FP_Mower_Push", (0, 28))):
    arm.animation_data.action = actions[name]
    scene.name = name
    scene.frame_start, scene.frame_end = f0, f1
    scene.frame_set(f0)
    export_yup(scene, objs, os.path.join(ANIM_OUT, name + ".fbx"), anim=True, convert=False, all_actions=False)
print("EXPORTED")
