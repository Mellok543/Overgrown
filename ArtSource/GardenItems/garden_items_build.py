"""Garden_Shears + Gate_Vines (shared palette atlas GardenItems_Atlas.png).
Run: blender -b --factory-startup -P garden_items_build.py

Garden_Shears: old bypass secateurs lying on the ground (pickup item). Pivot: base centre. ~28 cm.
Gate_Vines:    thick tangled vines for a wooden garden gate. The gate plane is assumed at Unity z = 0,
               x in [-0.9, 0.9] (gate centred on the pivot); stems weave back and forth through that plane.
               Pivot: base centre. Leaves are double-sided (no special material needed).
Blender is Z-up here (Unity +Z = Blender -Y). Export converts to Y-up manually."""
import os, math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\GardenItems"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(77)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    "metal": (150, 154, 158), "metal_edge": (212, 214, 210), "metal_dark": (72, 74, 78),
    "rust": (142, 84, 44), "rust_dark": (104, 62, 38),
    "grip": (176, 58, 44), "grip_worn": (150, 84, 62), "grip_black": (40, 40, 42),
    "stem": (96, 84, 52), "stem_dark": (70, 60, 40), "stem_green": (88, 112, 52),
    "leaf": (84, 140, 52), "leaf_dark": (58, 104, 42), "leaf_light": (122, 170, 70), "leaf_yellow": (172, 160, 70),
    "flower": (238, 234, 222), "flower_pink": (228, 172, 192), "flower_core": (236, 200, 90),
}
PAL_GRID, PAL_CELL = 8, 8
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)

def J(a):
    return rng.uniform(-a, a)

class Builder:
    """Accumulates geometry into one bmesh; faces carry a palette index as material_index."""
    def __init__(self):
        self.bm = bmesh.new()

    def face(self, verts, key):
        f = self.bm.faces.new(verts)
        f.material_index = KEYS.index(key)
        return f

    def prism(self, pts, z0, z1, key, side_key=None):
        # make the outline counter-clockwise so the caps face outwards
        area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
        if area < 0:
            pts = list(reversed(pts))
        lo = [self.bm.verts.new((x, y, z0)) for x, y in pts]
        hi = [self.bm.verts.new((x, y, z1)) for x, y in pts]
        self.face(list(reversed(lo)), key)
        self.face(hi, key)
        n = len(pts)
        for i in range(n):
            self.face((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]), side_key or key)

    def tube(self, pts, radii, n, key_fn, caps=True, flatten=1.0, up=Vector((0, 0, 1))):
        """Sweep an n-gon along pts. radii per point. key_fn(segment_index) -> palette key."""
        pts = [Vector(p) for p in pts]
        rings = []
        ref = up.copy()
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            if abs(t.dot(ref)) > 0.9:
                ref = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
            u = t.cross(ref).normalized()
            v = t.cross(u).normalized()
            r = radii[k]
            rings.append([self.bm.verts.new(p + (u * math.cos(math.tau * i / n) * flatten + v * math.sin(math.tau * i / n)) * r)
                          for i in range(n)])
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            for i in range(n):
                self.face((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]), key_fn(k))
        if caps:
            self.face(list(reversed(rings[0])), key_fn(0))
            self.face(rings[-1], key_fn(len(rings) - 2))

    def lathe(self, profile, n, key_fn, M):
        rings = []
        for r, z in profile:
            if r == 0:
                rings.append([self.bm.verts.new(M @ Vector((0, 0, z)))])
            else:
                rings.append([self.bm.verts.new(M @ Vector((math.cos(math.tau * i / n) * r, math.sin(math.tau * i / n) * r, z)))
                              for i in range(n)])
        for j in range(len(rings) - 1):
            a, b = rings[j], rings[j + 1]
            for i in range(n):
                i2 = (i + 1) % n
                if len(a) == 1:
                    self.face((a[0], b[i2], b[i]), key_fn(j))
                elif len(b) == 1:
                    self.face((a[i], a[i2], b[0]), key_fn(j))
                else:
                    self.face((a[i], a[i2], b[i2], b[i]), key_fn(j))

    def leaf(self, base, direction, normal, length, width, key):
        """Double-sided leaf with a slight fold along the midrib."""
        d = direction.normalized()
        nrm = (normal - d * normal.dot(d)).normalized()
        side = d.cross(nrm).normalized()
        tip = base + d * length
        mid = base + d * length * 0.45
        l = mid + side * width * 0.5 - nrm * width * 0.15     # slight cup instead of a modelled midrib
        r = mid - side * width * 0.5 - nrm * width * 0.15
        for flip in (False, True):
            vs = [self.bm.verts.new(p) for p in (base, r, tip, l)]
            for t in ((vs[0], vs[1], vs[2]), (vs[0], vs[2], vs[3])):
                self.face(tuple(reversed(t)) if flip else t, key)

    def finish(self, name):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new(name, me)
        scene.collection.objects.link(ob)
        return ob

# ================================================================ Garden_Shears (lying flat, length along X)
def garden_shears():
    B = Builder()
    T = 0.006                          # blade thickness
    # cutting blade (bypass): curved, shiny edge band, rust near the pivot; upper layer
    def blade(sign, z0, length, w0, curve, body_key, edge_key, rust_key):
        N = 7
        cl = []
        for k in range(N + 1):
            t = k / N
            x = -0.025 + t * (length + 0.025)
            y = sign * curve * (x / length) ** 2 * length
            w = w0 * (1 - t) ** 0.6 + 0.002
            cl.append((x, y, w))
        spine = [(x, y + sign * w * 0.5) for x, y, w in cl]
        mid = [(x, y) for x, y, w in cl]
        edge = [(x, y - sign * w * 0.5) for x, y, w in cl]
        # spine half (body, rusty near pivot) and edge half (bright / dark)
        for k in range(N):
            key = rust_key if k < 2 else body_key
            q1 = [spine[k], spine[k + 1], mid[k + 1], mid[k]]
            q2 = [mid[k], mid[k + 1], edge[k + 1], edge[k]]
            for q, kk in ((q1, key), (q2, edge_key if k >= 1 else key)):
                if sign < 0:
                    q = list(reversed(q))
                B.prism(q, z0, z0 + T, kk)
    blade(+1, 0.012, 0.085, 0.03, 0.22, "metal", "metal_edge", "rust")
    blade(-1, 0.006, 0.07, 0.026, 0.12, "metal_dark", "rust_dark", "rust_dark")
    # handles: metal tangs + worn red grips, slightly opened
    for sign, z in ((+1, 0.009), (-1, 0.009)):
        pts = []
        for k in range(8):
            t = k / 7
            x = -0.02 - t * 0.18
            y = -sign * (0.006 + 0.04 * t ** 1.2 - 0.012 * math.sin(t * math.pi))
            pts.append((x, y, z + 0.004))
        radii = [0.008 + 0.004 * min(1, k / 2) for k in range(8)]
        radii[-1] = 0.009
        B.tube(pts, radii, 6, lambda k: "metal" if k < 2 else ("grip_worn" if k in (4, 5) else "grip"), flatten=0.75)
        # end cap
        e = Vector(pts[-1])
        B.lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.012), (0.0, 0.014)], 6, lambda j: "grip_black",
                Matrix.Translation(e) @ Vector((-1, -sign * 0.3, 0)).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4())
    # pivot bolt + nut
    B.lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.026), (0.008, 0.029), (0.0, 0.03)], 8,
            lambda j: "rust" if j < 2 else "metal_dark", Matrix.Translation((0, 0, 0.0)))
    # coil spring between the handles
    sp = []
    for k in range(10):
        t = k / 9
        a = t * math.tau * 3
        sp.append((-0.04 - 0.035 * t * 0 + math.cos(a) * 0.006, -0.012 + 0.024 * t, 0.012 + math.sin(a) * 0.006))
    B.tube(sp, [0.0022] * len(sp), 4, lambda k: "metal_dark", caps=False)
    # safety latch near the pivot
    B.prism([(-0.035, 0.012), (-0.02, 0.012), (-0.02, 0.018), (-0.035, 0.018)], 0.018, 0.024, "metal_dark")
    ob = B.finish("Garden_Shears")
    # pivot: base centre
    me = ob.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    off = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)))
    for v in me.vertices:
        v.co -= off
    return ob

# ================================================================ Gate_Vines
def gate_vines():
    B = Builder()
    stems = []
    # thick climbing stems from the ground, weaving through the gate plane (y = 0), kept inside |x| < 0.95
    for st in range(6):
        x0 = -0.82 + st * 0.33 + J(0.05)
        drift = J(0.35)
        top = rng.uniform(1.25, 1.5)
        amp = rng.uniform(0.08, 0.12)
        freq = rng.uniform(2.2, 3.0)
        ph = rng.uniform(0, math.tau)
        N = 7
        pts, rad = [], []
        for k in range(N + 1):
            t = k / N
            x = max(-0.95, min(0.95, x0 + drift * t + 0.1 * math.sin(t * 6 + st)))
            z = top * t - 0.02 + (J(0.03) if k else 0.0)
            pts.append((x, amp * math.sin(freq * t * math.pi + ph), z))
            rad.append(0.05 * (1 - t) ** 0.8 + 0.014)
        stems.append(pts)
        B.tube(pts, rad, 5, lambda k: "stem_dark" if k < 2 else ("stem" if k < 5 else "stem_green"))
    # horizontal runners lashing the gate shut
    for z0, span in ((1.12, 1.85), (0.6, 1.75), (1.36, 1.5)):
        N = 8
        pts, rad = [], []
        ph = rng.uniform(0, math.tau)
        for k in range(N + 1):
            t = k / N
            pts.append((-span / 2 + span * t, 0.1 * math.sin(t * math.pi * 4 + ph), z0 + 0.06 * math.sin(t * 7 + ph)))
            rad.append(0.03 * (1 - abs(t - 0.5)) + 0.012)
        stems.append(pts)
        B.tube(pts, rad, 5, lambda k: "stem" if k % 3 else "stem_green")
    # a few curly tendrils
    for k in range(3):
        c = Vector((J(0.75), J(0.08), rng.uniform(0.6, 1.4)))
        pts = [c + Vector((math.cos(a) * 0.05 * (1 - a / 7), J(0.015), math.sin(a) * 0.05 * (1 - a / 7) + a * 0.012))
               for a in [i * 1.1 for i in range(6)]]
        B.tube(pts, [0.006] * len(pts), 3, lambda k: "stem_green", caps=False)
    # big leaves in bunches, facing the front and back of the gate so they read as a green wall
    leaf_keys = ["leaf", "leaf", "leaf_dark", "leaf_dark", "leaf_light", "leaf_yellow"]
    for pts in stems:
        P = [Vector(p) for p in pts]
        for k in range(len(P) - 1):
            for _ in range(rng.choice([2, 3, 3])):
                base = P[k].lerp(P[k + 1], rng.random())
                face = rng.choice([-1, 1])
                a = rng.uniform(0, math.tau)
                direction = Vector((math.cos(a), face * rng.uniform(0.1, 0.4), math.sin(a) * 0.8 + 0.25)).normalized()
                normal = Vector((J(0.35), face, J(0.35)))
                size = rng.uniform(0.12, 0.22)
                B.leaf(base + Vector((0, face * 0.03, 0)), direction, normal, size, size * 0.7, rng.choice(leaf_keys))
    # ground clumps at the base
    for k in range(8):
        base = Vector((-0.85 + k * 0.24 + J(0.05), J(0.15), 0.01))
        for _ in range(3):
            d = Vector((J(1), J(1), rng.uniform(0.4, 0.9))).normalized()
            B.leaf(base, d, Vector((J(0.5), J(0.5), 1)), rng.uniform(0.16, 0.24), 0.12, rng.choice(leaf_keys))
    # bindweed flowers (little trumpets)
    for k in range(5):
        pts = rng.choice(stems)
        p = Vector(pts[rng.randrange(2, len(pts) - 1)]) + Vector((0, rng.choice([-1, 1]) * 0.04, 0))
        d = Vector((J(0.5), (1 if p.y > 0 else -1), rng.uniform(0.0, 0.6))).normalized()
        M = Matrix.Translation(p) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        col = rng.choice(["flower", "flower", "flower_pink"])
        B.lathe([(0.0, 0.0), (0.012, 0.02), (0.04, 0.045), (0.0, 0.035)], 5,
                lambda j, c=col: "flower_core" if j == 2 else c, M)
    ob = B.finish("Gate_Vines")
    me = ob.data
    zmin = min(v.co.z for v in me.vertices)
    for v in me.vertices:
        v.co.z -= zmin
    return ob

shears = garden_shears()
vines = gate_vines()
objs = [shears, vines]

# ---------------------------------------------------------------- atlas + UVs + material
img = bpy.data.images.new("GardenItems_Atlas", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(KEYS):
    cx, cy = idx % PAL_GRID, idx // PAL_GRID
    col = [c / 255 for c in PALETTE[k]]
    for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
        for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (*col, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, "GardenItems_Atlas.png")
img.file_format = 'PNG'
img.save()
mat = bpy.data.materials.new("M_GardenItems")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.8
for ob in objs:
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        idx = poly.material_index
        u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
        v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
        for li in poly.loop_indices:
            uvl.data[li].uv = (u, v)
        poly.material_index = 0
    me.materials.append(mat)
    d = ob.dimensions
    print(f"MODEL {ob.name:14s} tris={len(me.polygons):5d} size x={d.x:.3f} y={d.y:.3f} z={d.z:.3f}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "GardenItems.blend"))

# ---------------------------------------------------------------- previews
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.6, 0.72, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.85, 0.2, -0.7))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=40)
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.15, 0.07, 1)
bpy.context.object.data.materials.append(gm)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_data)
scene.collection.objects.link(cam); scene.camera = cam
def shot(tag, loc, target, res, lens):
    cam_data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, f"render_{tag}.png")
    bpy.ops.render.render(write_still=True)
vines.location = (0, 0, -50)
shot("shears", (0.12, -0.28, 0.32), (0, 0, 0.01), (900, 700), 50)
vines.location = (0, 0, 0); shears.location = (0, 0, -50)
# a stand-in gate (not exported) to judge how the vines wrap it
gate_parts = []
for x in [-0.8 + 0.2 * k for k in range(9)]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0.62)); o = bpy.context.object
    o.scale = (0.09, 0.025, 1.15); gate_parts.append(o)
for z in (0.35, 1.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.03, z)); o = bpy.context.object
    o.scale = (1.75, 0.03, 0.09); gate_parts.append(o)
wm = bpy.data.materials.new("GateWood"); wm.use_nodes = True
wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.28, 0.17, 0.08, 1)
for o in gate_parts:
    o.data.materials.append(wm)
shot("vines", (1.2, -3.3, 1.5), (0, 0, 0.75), (1100, 900), 40)
shot("vines_back", (-1.0, 3.0, 1.3), (0, 0, 0.75), (1100, 900), 40)
for o in gate_parts:
    bpy.data.objects.remove(o, do_unlink=True)
vines.location = (0, 0, 0); shears.location = (0, 0, 0)
print("RENDERED")

# ---------------------------------------------------------------- export (manual Y-up, rotation 0 / scale 1)
R = Matrix.Rotation(-math.pi / 2, 4, 'X')
def set_int_prop(buf, name, value):
    key = b"S" + struct.pack("<I", len(name)) + name.encode()
    tail = b"S" + struct.pack("<I", 3) + b"int" + b"S" + struct.pack("<I", 7) + b"Integer" + b"S" + struct.pack("<I", 0) + b"I"
    i = buf.find(key + tail)
    assert i >= 0, name
    j = i + len(key) + len(tail)
    buf[j:j + 4] = struct.pack("<i", value)
for ob in objs:
    ob.data.transform(R)
for ob in objs:
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    path = os.path.join(OUT, ob.name + ".fbx")
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
