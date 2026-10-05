"""Shared helpers for Player_Character and Player_Arms_FP builds (imported by both build scripts)."""
import math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector, Quaternion

PALETTE = {
    "skin": (214, 172, 140), "skin_dark": (188, 146, 116), "mouth": (150, 92, 84), "eye": (46, 38, 34),
    "hair": (112, 78, 50), "hair_dark": (92, 62, 40),
    "shirt": (112, 124, 72), "shirt_dark": (92, 104, 60), "tshirt": (226, 214, 188),
    "pants": (98, 112, 126), "pants_dark": (82, 94, 108), "patch": (196, 176, 132),
    "belt": (98, 70, 46), "buckle": (150, 146, 130),
    "boot": (122, 84, 54), "boot_dark": (92, 62, 40), "sole": (58, 50, 44), "lace": (204, 186, 140),
    "glove": (196, 168, 118), "glove_dark": (160, 132, 90), "glove_palm": (176, 150, 104),
    # Garden_Shears colours (appended: existing cells keep their place in the atlas)
    "sh_metal": (150, 154, 158), "sh_metal_edge": (212, 214, 210), "sh_metal_dark": (72, 74, 78),
    "sh_rust": (142, 84, 44), "sh_rust_dark": (104, 62, 38),
    "sh_grip": (176, 58, 44), "sh_grip_worn": (150, 84, 62), "sh_grip_black": (40, 40, 42),
}
PAL_GRID, PAL_CELL = 8, 128           # 1024 x 1024 atlas
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)

rng = random.Random(1701)
def J(a):
    return rng.uniform(-a, a)

def smoothstep(a, b, x):
    if a == b:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- mesh building
class Part:
    """Accumulates bmesh geometry; every face carries a palette key as material_index."""
    def __init__(self, name, smooth=True):
        self.name = name
        self.bm = bmesh.new()
        self.smooth = smooth

    def _merge(self, tmp):
        me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me); tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def lathe(self, profile, n, key_fn, M=Matrix(), cap_bottom=True, cap_top=True, noise=0.0):
        tmp = bmesh.new()
        rings = []
        for r, z in profile:
            if r == 0:
                rings.append([tmp.verts.new(M @ Vector((0, 0, z)))])
            else:
                rings.append([tmp.verts.new(M @ Vector((math.cos(math.tau * i / n) * r * (1 + J(noise)),
                                                        math.sin(math.tau * i / n) * r * (1 + J(noise)), z))) for i in range(n)])
        for j in range(len(rings) - 1):
            a, b = rings[j], rings[j + 1]
            for i in range(n):
                i2 = (i + 1) % n
                if len(a) == 1:
                    f = tmp.faces.new((a[0], b[i2], b[i]))
                elif len(b) == 1:
                    f = tmp.faces.new((a[i], a[i2], b[0]))
                else:
                    f = tmp.faces.new((a[i], a[i2], b[i2], b[i]))
                f.material_index = KEYS.index(key_fn(j, i))
        if cap_bottom and len(rings[0]) > 1:
            tmp.faces.new(list(reversed(rings[0]))).material_index = KEYS.index(key_fn(0, 0))
        if cap_top and len(rings[-1]) > 1:
            tmp.faces.new(rings[-1]).material_index = KEYS.index(key_fn(len(rings) - 2, 0))
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
        self._merge(tmp)

    def tube(self, pts, radii, n, key_fn, caps=True, scale_u=1.0, up=None):
        tmp = bmesh.new()
        pts = [Vector(p) for p in pts]
        rings = []
        ref = up.copy() if up is not None else Vector((0, 0, 1))
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            r = ref if abs(t.dot(ref)) < 0.95 else Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
            u = t.cross(r).normalized(); v = t.cross(u).normalized()
            rad = radii[k]
            rings.append([tmp.verts.new(p + (u * math.cos(math.tau * i / n) * scale_u + v * math.sin(math.tau * i / n)) * rad)
                          for i in range(n)])
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            for i in range(n):
                tmp.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])).material_index = KEYS.index(key_fn(k, i))
        if caps:
            tmp.faces.new(list(reversed(rings[0]))).material_index = KEYS.index(key_fn(0, 0))
            tmp.faces.new(rings[-1]).material_index = KEYS.index(key_fn(len(rings) - 2, 0))
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
        self._merge(tmp)

    def ellipsoid(self, center, radii, key, M=None, segs=10, rings=6):
        tmp = bmesh.new()
        bmesh.ops.create_uvsphere(tmp, u_segments=segs, v_segments=rings, radius=1.0)
        for v in tmp.verts:
            v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
        R = M if M is not None else Matrix()
        bmesh.ops.transform(tmp, matrix=Matrix.Translation(Vector(center)) @ R, verts=tmp.verts)
        for f in tmp.faces:
            f.material_index = KEYS.index(key)
        self._merge(tmp)

    def box(self, center, size, key, R=None, bevel=0.0, seg=1, key_fn=None):
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0)
        for v in tmp.verts:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if bevel > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=bevel, segments=seg, affect='EDGES', profile=0.5)
        RR = R if R is not None else Matrix()
        bmesh.ops.transform(tmp, matrix=Matrix.Translation(Vector(center)) @ RR, verts=tmp.verts)
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)     # a mirrored frame would turn the box inside out
        tmp.normal_update()
        for f in tmp.faces:
            f.material_index = KEYS.index(key_fn(f) if key_fn else key)
        self._merge(tmp)

    def to_object(self, scene):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me); self.bm.free()
        for p in me.polygons:
            p.use_smooth = self.smooth
        ob = bpy.data.objects.new(self.name, me)
        scene.collection.objects.link(ob)
        return ob

def frame_matrix(X, Y, Z, origin=Vector()):
    M = Matrix((X, Y, Z)).transposed().to_4x4()
    M.translation = origin
    return M

def orthonormal(F, U):
    """Return (X, Y=F, Z=U') right-handed with Y along F and Z as close to U as possible."""
    Y = F.normalized()
    Z = (U - Y * U.dot(Y)).normalized()
    X = Y.cross(Z).normalized()
    return X, Y, Z

# ---------------------------------------------------------------- glove hand (mesh + bone layout from one source)
FINGERS = [("Index", 0.03, (0.04, 0.028, 0.022)), ("Middle", 0.01, (0.045, 0.03, 0.024)),
           ("Ring", -0.01, (0.042, 0.028, 0.022)), ("Little", -0.03, (0.032, 0.022, 0.018))]

def hand_layout(W, F, U, is_left, s=1.0):
    """Bone layout for a hand. side = thumb/index direction across the palm."""
    X, F, U = orthonormal(F, U)
    side = (F.cross(U) if is_left else U.cross(F)).normalized()
    sfx = "_L" if is_left else "_R"
    bones = {}
    bones["Hand" + sfx] = (W.copy(), W + F * 0.09 * s, U)
    for name, off, lens in FINGERS:
        p = W + F * 0.095 * s + side * off * s
        for k, l in enumerate(lens):
            q = p + F * l * s
            bones[f"{name}{k + 1}{sfx}"] = (p, q, U)
            p = q
    tb = W + F * 0.035 * s + side * 0.04 * s - U * 0.012 * s
    td = (F * 0.7 + side * 0.55 - U * 0.35).normalized()
    tz = side + U
    p = tb
    for k, l in enumerate((0.035, 0.028, 0.024)):
        q = p + td * l * s
        bones[f"Thumb{k + 1}{sfx}"] = (p, q, tz)
        p = q
    return bones, side

def build_hand(part_palm, finger_parts, W, F, U, is_left, s=1.0, n=10):
    """Glove: cuff + palm on part_palm; each finger tube appended to finger_parts[name] (weighted separately)."""
    bones, side = hand_layout(W, F, U, is_left, s)
    X, F, U = orthonormal(F, U)
    R = frame_matrix(side, F, U)
    part_palm.box(W + F * 0.05 * s, (0.086 * s, 0.1 * s, 0.036 * s), "glove", R=R, bevel=0.012 * s, seg=2,
                  key_fn=lambda f: "glove_palm" if f.normal.dot(U) < -0.5 else "glove")
    cuff = Matrix.Translation(W - F * 0.035 * s) @ frame_matrix(side, U, F)
    part_palm.lathe([(0.0, 0.0), (0.038 * s, 0.0), (0.042 * s, 0.045 * s), (0.039 * s, 0.05 * s), (0.033 * s, 0.05 * s)], 12,
                    lambda j, i: "glove_dark" if j >= 2 else "glove", cuff, cap_bottom=False, cap_top=False)
    sfx = "_L" if is_left else "_R"
    for name in ("Thumb", "Index", "Middle", "Ring", "Little"):
        segs = [bones[f"{name}{k}{sfx}"] for k in (1, 2, 3)]
        pts, radii = [], []
        r0 = (0.0125 if name == "Thumb" else 0.0115) * s
        for k, (h, t, _) in enumerate(segs):
            for u in ((0.0, 0.5) if k < 2 else (0.0, 0.45, 0.85)):
                pts.append(h.lerp(t, u))
                radii.append(r0 * (1 - 0.08 * (k + u)))
        pts.append(segs[-1][1] + (segs[-1][1] - segs[-1][0]).normalized() * 0.002)
        radii.append(r0 * 0.55)
        if name != "Thumb":            # start a little inside the palm
            pts.insert(0, segs[0][0] - F * 0.012 * s); radii.insert(0, r0 * 1.05)
        finger_parts[name].tube(pts, radii, n, lambda k, i: "glove", caps=True, up=U)
    return bones

# ---------------------------------------------------------------- skinning
def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length

def weight_object(ob, bone_defs, candidates, fade=None, power=4.0, max_inf=4):
    """Inverse-distance-to-bone-segment weights over `candidates`, optionally multiplied by fade(bone, p)."""
    for name in candidates:
        if name not in ob.vertex_groups:
            ob.vertex_groups.new(name=name)
    for v in ob.data.vertices:
        p = v.co
        ws = []
        for name in candidates:
            h, t = bone_defs[name][0], bone_defs[name][1]
            f = fade(name, p) if fade else 1.0
            if f <= 0:
                continue
            d = seg_dist(p, h, t) + 0.004
            ws.append((f / d ** power, name))
        ws.sort(reverse=True)
        ws = ws[:max_inf]
        tot = sum(w for w, _ in ws) or 1.0
        for w, name in ws:
            if w / tot > 0.01:
                ob.vertex_groups[name].add([v.index], w / tot, 'REPLACE')

def rigid_weight(ob, bone):
    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    g.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')

# ---------------------------------------------------------------- armature
def build_armature(scene, name, bone_defs, parents, connected=()):
    """bone_defs: name -> (head, tail, roll_up_vector)."""
    data = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for bname, (h, t, up) in bone_defs.items():
        eb = data.edit_bones.new(bname)
        eb.head, eb.tail = h, t
        if up is not None:
            eb.align_roll(up)
    for bname, par in parents.items():
        if par:
            eb = data.edit_bones[bname]
            eb.parent = data.edit_bones[par]
            eb.use_connect = bname in connected
    bpy.ops.object.mode_set(mode='OBJECT')
    data.display_type = 'STICK'
    return ob

def bind(mesh_ob, arm_ob):
    mesh_ob.parent = arm_ob
    mod = mesh_ob.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_ob

# ---------------------------------------------------------------- palette atlas / UVs
def make_atlas(path, name):
    img = bpy.data.images.new(name, PAL_SIZE, PAL_SIZE, alpha=False)
    px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
    for idx, k in enumerate(KEYS):
        cx, cy = idx % PAL_GRID, idx // PAL_GRID
        col = [c / 255 for c in PALETTE[k]]
        for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
            row = (y * PAL_SIZE + cx * PAL_CELL) * 4
            px[row:row + PAL_CELL * 4] = (col + [1.0]) * PAL_CELL
    img.pixels = px
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return img

def make_material(img, name="M_Player"):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat

def palette_uvs(ob, mat):
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        idx = poly.material_index
        u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
        v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
        for li in poly.loop_indices:
            uvl.data[li].uv = (u, v)
        poly.material_index = 0
    me.materials.clear()
    me.materials.append(mat)

# ---------------------------------------------------------------- FBX export (Y-up, every node rotation 0 / scale 1)
def to_yup(objs):
    """Rotate armature + meshes -90 deg about X and apply: data becomes Y-up (call once before exporting)."""
    for o in bpy.context.selected_objects:
        o.select_set(False)
    roots = [o for o in objs if o.parent is None]
    for o in roots:
        o.rotation_euler = (-math.pi / 2, 0, 0)
    bpy.context.view_layer.update()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = roots[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

def export_yup(scene, objs, path, anim=False, convert=True, all_actions=True):
    """Export without axis conversion and mark the file Y-up. Unity then sees identity transforms, front = +Z.
    all_actions=False exports only the active action as one take named after the scene."""
    if convert:
        to_yup(objs)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='Y', axis_up='Z', bake_space_transform=False,
        mesh_smooth_type='FACE', use_tspace=False, use_armature_deform_only=True,
        add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
        bake_anim=anim, bake_anim_use_all_actions=anim and all_actions, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        path_mode='RELATIVE', embed_textures=False,
    )
    buf = bytearray(open(path, "rb").read())
    def set_int_prop(name, value):
        key = b"S" + struct.pack("<I", len(name)) + name.encode()
        tail = b"S" + struct.pack("<I", 3) + b"int" + b"S" + struct.pack("<I", 7) + b"Integer" + b"S" + struct.pack("<I", 0) + b"I"
        i = buf.find(key + tail)
        assert i >= 0, name
        j = i + len(key) + len(tail)
        buf[j:j + 4] = struct.pack("<i", value)
    for k, v in (("UpAxis", 1), ("UpAxisSign", 1), ("FrontAxis", 2), ("FrontAxisSign", 1),
                 ("CoordAxis", 0), ("CoordAxisSign", 1), ("OriginalUpAxis", 1), ("OriginalUpAxisSign", 1)):
        set_int_prop(k, v)
    open(path, "wb").write(buf)

def setup_render(scene, res=(1000, 1000)):
    world = bpy.data.worlds.new("W"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.6, 0.72, 1)
    bpy.ops.object.light_add(type='SUN', rotation=(0.8, 0.2, -0.6))
    bpy.context.object.data.energy = 3.2
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = res
    cam_data = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
    return cam

def aim(cam, loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
