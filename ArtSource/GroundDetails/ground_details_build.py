"""Ground detail pack: 12 tiny background props sharing GroundDetails_Atlas.png.
Run: blender -b --factory-startup -P ground_details_build.py

Each model -> Assets/Art/Models/GroundDetails/<Name>.fbx, pivot at the ground contact (min height = 0, centred
on its footprint), rotation 0 / scale 1, Y up. Colours are deliberately muted so nothing reads as a pickup.
Blender is Z-up here (Unity +Z = Blender -Y). Export converts to Y-up manually."""
import os, math, random, struct
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\GroundDetails"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(12)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    "stone": (118, 116, 108), "stone_warm": (128, 120, 106), "stone_dark": (96, 94, 88), "stone_light": (140, 136, 124),
    "moss": (104, 118, 64),
    "twig": (122, 92, 62), "twig_dark": (92, 68, 46), "twig_light": (150, 118, 80),
    "leaf_orange": (176, 118, 62), "leaf_brown": (140, 98, 60), "leaf_beige": (182, 160, 112), "leaf_red": (152, 86, 58),
    "leaf_base": (110, 84, 56),
    "weed": (72, 104, 56), "weed_dark": (56, 86, 46), "weed_yellow": (122, 132, 64), "weed_flower": (206, 188, 110),
    "dirt": (118, 90, 62), "dirt_dark": (96, 72, 50), "dirt_light": (138, 110, 76),
    "wood_grey": (128, 118, 104), "wood_old": (110, 100, 88), "rust": (128, 80, 50), "rust_dark": (96, 60, 40),
    "metal_dark": (74, 72, 70),
}
PAL_GRID, PAL_CELL = 8, 8
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)

def J(a):
    return rng.uniform(-a, a)

class Builder:
    def __init__(self):
        self.bm = bmesh.new()

    def tag(self, faces, key):
        for f in faces:
            f.material_index = KEYS.index(key)

    def rock(self, center, size, keys, subdiv=1, noise=0.18, flat_bottom=True, top_key=None):
        """Jittered icosphere; faces facing up get top_key (subtle painted highlight)."""
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1.0)
        for v in tmp.verts:
            v.co = Vector((v.co.x * size[0] * (1 + J(noise)), v.co.y * size[1] * (1 + J(noise)), v.co.z * size[2] * (1 + J(noise))))
            if flat_bottom and v.co.z < -size[2] * 0.35:
                v.co.z = -size[2] * 0.35 + J(0.003)
        bmesh.ops.transform(tmp, matrix=Matrix.Translation(Vector(center) + Vector((0, 0, size[2] * 0.35))), verts=tmp.verts)
        self._merge(tmp, lambda f: (top_key if top_key and f.normal.z > 0.75 else rng.choice(keys)))

    def hull(self, points, keys, top_key=None):
        tmp = bmesh.new()
        vs = [tmp.verts.new(p) for p in points]
        bmesh.ops.convex_hull(tmp, input=vs)
        for v in [v for v in tmp.verts if not v.link_faces]:
            tmp.verts.remove(v)
        self._merge(tmp, lambda f: (top_key if top_key and f.normal.z > 0.8 else rng.choice(keys)))

    def tube(self, pts, radii, n, key_fn, caps=True):
        tmp = bmesh.new()
        pts = [Vector(p) for p in pts]
        rings = []
        ref = Vector((0, 0, 1))
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            if abs(t.dot(ref)) > 0.9:
                ref = Vector((1, 0, 0))
            u = t.cross(ref).normalized(); v = t.cross(u).normalized()
            rings.append([tmp.verts.new(p + (u * math.cos(math.tau * i / n) + v * math.sin(math.tau * i / n)) * radii[k]) for i in range(n)])
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            for i in range(n):
                tmp.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])).material_index = KEYS.index(key_fn(k))
        if caps:
            tmp.faces.new(list(reversed(rings[0]))).material_index = KEYS.index(key_fn(0))
            tmp.faces.new(rings[-1]).material_index = KEYS.index(key_fn(len(rings) - 2))
        self._merge(tmp, None)

    def leaf(self, base, direction, normal, length, width, key, curl=0.15):
        d = direction.normalized()
        nrm = (normal - d * normal.dot(d)).normalized()
        side = d.cross(nrm).normalized()
        tip = base + d * length + nrm * length * curl
        mid = base + d * length * 0.45
        l = mid + side * width * 0.5 + nrm * width * curl
        r = mid - side * width * 0.5 + nrm * width * curl
        tmp = bmesh.new()
        for flip in (False, True):
            vs = [tmp.verts.new(p) for p in (base, r, tip, l)]
            for t in ((vs[0], vs[1], vs[2]), (vs[0], vs[2], vs[3])):
                tmp.faces.new(tuple(reversed(t)) if flip else t).material_index = KEYS.index(key)
        self._merge(tmp, None)

    def mound(self, radius, height, keys, n=10, rings=3, noise=0.15, center=(0, 0, 0)):
        prof = [(radius * (1 - k / rings), height * math.sin(math.pi / 2 * k / rings)) for k in range(rings)] + [(0.0, height)]
        tmp = bmesh.new()
        rr = []
        for r, z in prof:
            if r == 0:
                rr.append([tmp.verts.new((0, 0, z))])
            else:
                rr.append([tmp.verts.new((math.cos(math.tau * i / n) * r * (1 + J(noise)), math.sin(math.tau * i / n) * r * (1 + J(noise)),
                                          max(0.0, z + (J(noise * height) if z > 0 else 0)))) for i in range(n)])
        for j in range(len(rr) - 1):
            a, b = rr[j], rr[j + 1]
            for i in range(n):
                i2 = (i + 1) % n
                f = tmp.faces.new((a[i], a[i2], b[0])) if len(b) == 1 else tmp.faces.new((a[i], a[i2], b[i2], b[i]))
                f.material_index = KEYS.index(rng.choice(keys))
        tmp.faces.new(list(reversed(rr[0]))).material_index = KEYS.index(keys[0])
        bmesh.ops.transform(tmp, matrix=Matrix.Translation(Vector(center)), verts=tmp.verts)
        self._merge(tmp, None)

    def prism(self, pts, z0, z1, key, side_key=None):
        area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
        if area < 0:
            pts = list(reversed(pts))
        tmp = bmesh.new()
        lo = [tmp.verts.new((x, y, z0)) for x, y in pts]
        hi = [tmp.verts.new((x, y, z1)) for x, y in pts]
        tmp.faces.new(list(reversed(lo))).material_index = KEYS.index(side_key or key)
        tmp.faces.new(hi).material_index = KEYS.index(key)
        n = len(pts)
        for i in range(n):
            tmp.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i])).material_index = KEYS.index(side_key or key)
        self._merge(tmp, None)

    def _merge(self, tmp, key_fn):
        tmp.normal_update()
        if key_fn:
            for f in tmp.faces:
                f.material_index = KEYS.index(key_fn(f))
        me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me); tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def finish(self, name, xform=None):
        if xform is not None:
            bmesh.ops.transform(self.bm, matrix=xform, verts=self.bm.verts)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        # pivot at ground contact, centred on the footprint
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
        off = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)))
        for v in me.vertices:
            v.co -= off
        ob = bpy.data.objects.new(name, me)
        scene.collection.objects.link(ob)
        return ob

STONE = ["stone", "stone", "stone_warm", "stone_dark"]
LEAVES = ["leaf_orange", "leaf_orange", "leaf_brown", "leaf_beige", "leaf_red", "leaf_brown"]
models = []

# 1. rounded flattened stone
B = Builder(); B.rock((0, 0, 0), (0.13, 0.1, 0.06), STONE, subdiv=2, noise=0.12, top_key="stone_light")
models.append(B.finish("GroundDetail_SmallStone_A"))

# 2. angular low stone (convex hull of jittered points)
B = Builder()
pts = []
for k in range(18):
    a = math.tau * k / 18 + J(0.15)
    r = rng.uniform(0.09, 0.15)
    pts.append((math.cos(a) * r * 1.3, math.sin(a) * r, 0.0))
for k in range(10):
    a = rng.uniform(0, math.tau)
    pts.append((math.cos(a) * 0.08 * 1.3, math.sin(a) * 0.06, rng.uniform(0.04, 0.065)))
B.hull(pts, ["stone_warm", "stone", "stone_dark"], top_key="stone_light")
models.append(B.finish("GroundDetail_SmallStone_B"))

# 3. cluster of 3 stones, a hint of moss on the biggest
B = Builder()
B.rock((0, 0, 0), (0.12, 0.09, 0.07), STONE, subdiv=2, noise=0.12, top_key="moss")
B.rock((0.13, 0.06, 0), (0.07, 0.06, 0.045), STONE, top_key="stone_light")
B.rock((0.04, -0.11, 0), (0.06, 0.05, 0.035), STONE, top_key="stone_light")
models.append(B.finish("GroundDetail_SmallStone_C"))

# 4. curved twig lying on the ground
B = Builder()
pts = [(-0.2 + 0.4 * t, 0.06 * math.sin(t * math.pi * 1.2) + J(0.01), 0.014 - 0.004 * t) for t in [k / 6 for k in range(7)]]
B.tube(pts, [0.015 - 0.008 * k / 6 for k in range(7)], 5, lambda k: "twig" if k % 3 else "twig_dark")
B.tube([(-0.05, 0.035, 0.012), (-0.02, 0.07, 0.014), (0.0, 0.09, 0.012)], [0.007, 0.005, 0.003], 4, lambda k: "twig_light")
B.tube([(0.1, 0.0, 0.01), (0.13, -0.04, 0.012)], [0.006, 0.003], 4, lambda k: "twig")
models.append(B.finish("GroundDetail_DryTwig_A"))

# 5. forked branch
B = Builder()
main = [(-0.18, 0.0, 0.016), (-0.06, 0.02, 0.016), (0.03, 0.0, 0.014)]
B.tube(main, [0.018, 0.015, 0.013], 5, lambda k: "twig_dark" if k == 0 else "twig")
B.tube([main[-1], (0.12, 0.06, 0.012), (0.2, 0.08, 0.009)], [0.013, 0.009, 0.005], 5, lambda k: "twig")
B.tube([main[-1], (0.1, -0.05, 0.011), (0.17, -0.12, 0.008), (0.2, -0.13, 0.008)], [0.012, 0.008, 0.005, 0.003], 5, lambda k: "twig_light" if k else "twig")
B.tube([(0.1, -0.05, 0.011), (0.14, 0.0, 0.01)], [0.005, 0.003], 4, lambda k: "twig")
models.append(B.finish("GroundDetail_DryTwig_B"))

# 6. compact leaf pile
B = Builder()
B.mound(0.1, 0.05, ["leaf_brown", "leaf_base"], n=8, rings=2)
for k in range(34):
    a = rng.uniform(0, math.tau); r = 0.16 * math.sqrt(rng.random())
    z = 0.06 * (1 - (r / 0.17) ** 2) + 0.004 + k * 0.0004
    base = Vector((math.cos(a) * r, math.sin(a) * r, z))
    d = Vector((math.cos(a + J(1.2)), math.sin(a + J(1.2)), J(0.3)))
    B.leaf(base, d, Vector((J(0.3), J(0.3), 1)), rng.uniform(0.08, 0.12), 0.06, rng.choice(LEAVES), curl=0.1)
models.append(B.finish("GroundDetail_DryLeaves_A"))

# 7. flatter, wider leaf pile
B = Builder()
B.mound(0.16, 0.025, ["leaf_brown", "leaf_base"], n=10, rings=2)
for k in range(40):
    a = rng.uniform(0, math.tau); r = 0.22 * math.sqrt(rng.random())
    z = 0.035 * (1 - (r / 0.23) ** 2) + 0.004
    base = Vector((math.cos(a) * r * 1.05, math.sin(a) * r * 0.85, z))
    d = Vector((math.cos(a + J(1.5)), math.sin(a + J(1.5)), J(0.15)))
    B.leaf(base + Vector((0, 0, k * 0.0003)), d, Vector((J(0.2), J(0.2), 1)), rng.uniform(0.08, 0.12), 0.06, rng.choice(LEAVES), curl=0.08)
models.append(B.finish("GroundDetail_DryLeaves_B"))

# 8. low broad-leaf rosette weed with two small flower stalks
B = Builder()
for k in range(8):
    a = math.tau * k / 8 + J(0.25)
    d = Vector((math.cos(a), math.sin(a), rng.uniform(0.35, 0.7)))
    B.leaf(Vector((0, 0, 0.005)), d, Vector((0, 0, 1)), rng.uniform(0.11, 0.16), 0.055, rng.choice(["weed", "weed_dark", "weed"]), curl=0.2)
for k in range(2):
    tip = Vector((J(0.04), J(0.04), rng.uniform(0.17, 0.22)))
    B.tube([(0, 0, 0.0), tip * 0.5 + Vector((J(0.01), J(0.01), 0)), tip], [0.004, 0.003, 0.003], 3, lambda k: "weed_yellow", caps=False)
    B.rock(tuple(tip - Vector((0, 0, 0.01))), (0.012, 0.012, 0.012), ["weed_flower"], subdiv=1, noise=0.1, flat_bottom=False)
models.append(B.finish("GroundDetail_WeedClump_A"))

# 9. taller, sparse spiky weed (stems with paired narrow leaves)
B = Builder()
for s in range(5):
    a = math.tau * s / 5 + J(0.4)
    lean = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.03, 0.08)
    h = rng.uniform(0.22, 0.38)
    top = Vector((0, 0, h)) + lean
    B.tube([(J(0.02), J(0.02), 0.0), top * 0.5, top], [0.005, 0.004, 0.002], 3, lambda k: "weed_dark", caps=False)
    for t in (0.35, 0.6, 0.85):
        p = top * t
        for side in (-1, 1):
            d = Vector((math.cos(a + side * 1.4), math.sin(a + side * 1.4), 0.9))
            B.leaf(p, d, Vector((J(0.3), J(0.3), 1)), rng.uniform(0.04, 0.07) * (1.1 - t * 0.5), 0.018,
                   rng.choice(["weed", "weed_dark", "weed_yellow"]), curl=0.05)
models.append(B.finish("GroundDetail_WeedClump_B"))

# 10. subtle dirt mound with a couple of clods
B = Builder()
B.mound(0.17, 0.055, ["dirt", "dirt", "dirt", "dirt_light"], n=12, rings=4, noise=0.1)
for k in range(3):
    a = rng.uniform(0, math.tau)
    B.rock((math.cos(a) * 0.16, math.sin(a) * 0.16, 0), (0.028, 0.024, 0.018), ["dirt_dark", "dirt"], subdiv=1, noise=0.2)
models.append(B.finish("GroundDetail_DirtClump"))

# 11. broken weathered plank fragment with a bent nail
B = Builder()
outline = [(-0.14, -0.04), (0.08, -0.04), (0.1, -0.02), (0.085, 0.0), (0.12, 0.015), (0.095, 0.04), (-0.14, 0.04), (-0.15, 0.0)]
B.prism(outline, 0.0, 0.018, "wood_grey", side_key="wood_old")
B.tube([(-0.1, 0.0, 0.018), (-0.1, 0.0, 0.03), (-0.08, 0.005, 0.034)], [0.003, 0.003, 0.0025], 4, lambda k: "rust", caps=False)
B.prism([(-0.03, -0.035), (0.0, -0.035), (0.0, -0.02), (-0.03, -0.02)], 0.018, 0.0185, "wood_old")
models.append(B.finish("GroundDetail_GardenDebris_A", Matrix.Rotation(0.02, 4, 'X')))

# 12. dented scrap of rusty tin lying flat, one edge bent up (reads as junk, not a pickup)
B = Builder()
tmp = bmesh.new()
GX, GY = 4, 3
for flip in (False, True):
    grid = {}
    for i in range(GX + 1):
        for j in range(GY + 1):
            x = -0.09 + 0.18 * i / GX + J(0.008)
            y = -0.06 + 0.12 * j / GY + J(0.008)
            z = 0.004 + (0.045 * ((i - GX + 1) / 1) ** 2 if i >= GX - 1 else 0.0) + J(0.004)
            if (i, j) in ((0, 0), (0, GY)):          # torn corners
                x += 0.02
            grid[i, j] = tmp.verts.new((x, y, z))
    for i in range(GX):
        for j in range(GY):
            q = (grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1])
            f = tmp.faces.new(tuple(reversed(q)) if flip else q)
            f.material_index = KEYS.index(rng.choice(["rust", "rust", "rust_dark", "metal_dark"]))
B._merge(tmp, None)
models.append(B.finish("GroundDetail_GardenDebris_B", Matrix.Rotation(0.6, 4, 'Z')))

# ---------------------------------------------------------------- atlas + UVs + material
img = bpy.data.images.new("GroundDetails_Atlas", PAL_SIZE, PAL_SIZE, alpha=False)
px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
for idx, k in enumerate(KEYS):
    cx, cy = idx % PAL_GRID, idx // PAL_GRID
    col = [c / 255 for c in PALETTE[k]]
    for y in range(cy * PAL_CELL, (cy + 1) * PAL_CELL):
        for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
            i = (y * PAL_SIZE + x) * 4
            px[i:i + 4] = (*col, 1.0)
img.pixels = px
img.filepath_raw = os.path.join(OUT, "GroundDetails_Atlas.png")
img.file_format = 'PNG'
img.save()
mat = bpy.data.materials.new("M_GroundDetails")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
for ob in models:
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
    print(f"MODEL {ob.name:30s} tris={len(me.polygons):4d} size x={d.x:.2f} y={d.y:.2f} h={d.z:.2f}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "GroundDetails.blend"))

# ---------------------------------------------------------------- preview: 4 x 3 grid on a ground-coloured plane
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.6, 0.72, 1)
bpy.ops.object.light_add(type='SUN', rotation=(0.85, 0.2, -0.7))
bpy.context.object.data.energy = 3.5
bpy.ops.mesh.primitive_plane_add(size=20)
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.17, 0.22, 0.08, 1)
bpy.context.object.data.materials.append(gm)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
for i, ob in enumerate(models):
    ob.location = ((i % 4) * 0.7 - 1.05, -(i // 4) * 0.7 + 0.7, 0)
cam_data = bpy.data.cameras.new("C"); cam_data.lens = 40
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (0.0, -2.9, 2.3)
cam.rotation_euler = (Vector((0, -0.05, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
scene.render.filepath = os.path.join(HERE, "render_pack.png")
bpy.ops.render.render(write_still=True)
for ob in models:
    ob.location = (0, 0, 0)
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
for ob in models:
    ob.data.transform(R)
for ob in models:
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
