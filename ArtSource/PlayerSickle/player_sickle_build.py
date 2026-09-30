"""Player_Sickle: first-person hand sickle.
Run: blender -b --factory-startup -P player_sickle_build.py

Orientation in Unity (Y up):
  pivot  = centre of the grip (where the hand holds it)
  handle = along +Y (butt at -Y)
  blade  = rises from the ferrule and curves forward towards +Z, tip hooks back down
  cutting edge = inner side of the curve; blade plane = YZ, thickness along X
Blender is Z-up here (Unity +Z forward = Blender -Y)."""
import os, math
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\PlayerSickle"
NAME = "Player_Sickle"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- palette: (sRGB colour, metallic, smoothness)
PALETTE = {
    "wood":       ((156, 104, 60),  0.0, 0.18),
    "wood_worn":  ((184, 136, 84),  0.0, 0.28),   # polished by the hand in the grip area
    "wood_dark":  ((96, 62, 36),    0.0, 0.12),   # butt end grain
    "metal":      ((78, 82, 88),    0.75, 0.38),  # dark matte blade body
    "metal_spine":((96, 100, 106),  0.75, 0.42),
    "metal_edge": ((196, 202, 204), 0.9, 0.62),   # honed cutting edge
    "ferrule":    ((112, 104, 92),  0.8, 0.40),
    "rivet":      ((150, 146, 134), 0.85, 0.50),
}
PAL_GRID, PAL_CELL = 4, 16
PAL_SIZE = PAL_GRID * PAL_CELL
KEYS = list(PALETTE)

bm = bmesh.new()

def face(verts, key):
    f = bm.faces.new(verts)
    f.material_index = KEYS.index(key)      # survives triangulation
    return f

# ---------------------------------------------------------------- handle (lathe along Z)
N = 12
HANDLE = [  # (radius, z, key for the band above this ring)
    (0.0,    -0.100, "wood_dark"),
    (0.0175, -0.100, "wood_dark"),
    (0.0215, -0.092, "wood"),       # butt knob
    (0.0195, -0.078, "wood_worn"),
    (0.0182, -0.050, "wood_worn"),
    (0.0190, -0.010, "wood_worn"),  # slight belly where the palm sits
    (0.0182,  0.030, "wood_worn"),
    (0.0170,  0.060, "wood"),
    (0.0165,  0.078, "wood"),
]
rings = []
for r, z, _ in HANDLE:
    if r == 0:
        rings.append([bm.verts.new((0, 0, z))])
    else:
        rings.append([bm.verts.new((math.cos(math.tau * i / N) * r, math.sin(math.tau * i / N) * r, z)) for i in range(N)])
for j in range(len(rings) - 1):
    a, b = rings[j], rings[j + 1]
    key = HANDLE[j][2]
    for i in range(N):
        i2 = (i + 1) % N
        if len(a) == 1:
            face((a[0], b[i2], b[i]), key)
        else:
            face((a[i], a[i2], b[i2], b[i]), key)

# ferrule: metal collar with a small lip, capped on top
FER = [(0.0165, 0.078), (0.0195, 0.080), (0.0195, 0.108), (0.0170, 0.112), (0.0, 0.114)]
prev = rings[-1]
for k, (r, z) in enumerate(FER):
    if r == 0:
        top = bm.verts.new((0, 0, z))
        for i in range(N):
            face((prev[i], prev[(i + 1) % N], top), "ferrule")
        break
    ring = [bm.verts.new((math.cos(math.tau * i / N) * r, math.sin(math.tau * i / N) * r, z)) for i in range(N)]
    for i in range(N):
        face((prev[i], prev[(i + 1) % N], ring[(i + 1) % N], ring[i]), "ferrule")
    prev = ring
# two rivet heads on the ferrule sides (+X / -X)
for s in (-1, 1):
    c = Vector((s * 0.0197, 0, 0.094))
    rv = [bm.verts.new(c + Vector((0, math.cos(math.tau * i / 6) * 0.005, math.sin(math.tau * i / 6) * 0.005))) for i in range(6)]
    tip = bm.verts.new(c + Vector((s * 0.003, 0, 0)))
    for i in range(6):
        f = face((rv[i], rv[(i + 1) % 6], tip), "rivet")

# ---------------------------------------------------------------- blade
# Arc in the (y, z) plane; forward = -Y (Unity +Z). Angles measured from +(-Y) axis.
R = 0.165
C = Vector((0.0, -0.115, 0.235))          # arc centre (x, y, z)
A0, A1 = math.radians(-40), math.radians(165)
SEG = 36

def arc_dir(a):
    # a = 0 -> pointing backwards (+Y, over the handle), a = 90deg -> up, 180 -> forward (-Y)
    return Vector((0.0, math.cos(a), math.sin(a)))

# cross-section (x offset, radial offset from the outer radius), closed loop, spine at radial 0
def section(width):
    e = width                       # inner (cutting) edge radial depth
    bev = width * 0.62              # where the honed edge band starts
    return [
        (0.0,     0.000, "metal_spine"),
        (0.0052, -0.004, "metal"),
        (0.0040, -bev,   "metal_edge"),
        (0.0007, -e,     "metal_edge"),
        (-0.0007, -e,    "metal_edge"),
        (-0.0040, -bev,  "metal_edge"),
        (-0.0052, -0.004, "metal_spine"),
    ]

loops = []
for k in range(SEG + 1):
    t = k / SEG
    a = A0 + (A1 - A0) * t
    d = arc_dir(a)
    # broad near the heel, long elegant taper to a sharp tip
    width = 0.068 * (1 - t) ** 0.7 + 0.005
    if t < 0.08:                    # heel rounds into the tang
        width *= 0.8 + 2.5 * t
    sec = section(width)
    thin = 1.0 - 0.55 * t           # blade gets thinner towards the tip
    loop = []
    for x, rad, key in sec:
        p = C + d * (R + rad) + Vector((x * thin, 0, 0))
        loop.append((bm.verts.new(p), key))
    loops.append(loop)

M = len(loops[0])
for k in range(SEG):
    a, b = loops[k], loops[k + 1]
    for i in range(M):
        i2 = (i + 1) % M
        key = a[i][1] if a[i][1] == a[i2][1] else ("metal_edge" if "edge" in a[i][1] and "edge" in a[i2][1] else "metal")
        if {a[i][1], a[i2][1]} == {"metal_spine"}:
            key = "metal_spine"
        face((a[i][0], a[i2][0], b[i2][0], b[i][0]), key)
# close the tip
face([v for v, _ in reversed(loops[-1])], "metal")

# tang: tapered neck from the ferrule top into the blade heel (heel loop projected onto the ferrule)
heel = loops[0]
base_z = 0.112
cy = sum(v.co.y for v, _ in heel) / M
tang_ring = [bm.verts.new((max(-0.008, min(0.008, v.co.x * 1.5)), (v.co.y - cy) * 0.45, base_z)) for v, _ in heel]
for i in range(M):
    i2 = (i + 1) % M
    face((tang_ring[i], tang_ring[i2], heel[i2][0], heel[i][0]), "metal")
face(list(reversed(tang_ring)), "metal")

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

me = bpy.data.meshes.new(NAME)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new(NAME, me)
scene.collection.objects.link(ob)

# ---------------------------------------------------------------- atlas: BaseColor + MetallicSmoothness (Unity: R metallic, A smoothness)
def save_png(name, cell_rgba, srgb=True):
    img = bpy.data.images.new(name, PAL_SIZE, PAL_SIZE, alpha=True)
    if not srgb:
        img.colorspace_settings.name = 'Non-Color'
    px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
    for idx, k in enumerate(KEYS):
        cx, cy_ = idx % PAL_GRID, idx // PAL_GRID
        col = cell_rgba(k)
        for y in range(cy_ * PAL_CELL, (cy_ + 1) * PAL_CELL):
            for x in range(cx * PAL_CELL, (cx + 1) * PAL_CELL):
                i = (y * PAL_SIZE + x) * 4
                px[i:i + 4] = col
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = 'PNG'
    img.save()
    return img

base_img = save_png(NAME + "_Atlas", lambda k: (*[c / 255 for c in PALETTE[k][0]], 1.0))
ms_img = save_png(NAME + "_MetallicSmoothness", lambda k: (PALETTE[k][1], PALETTE[k][1], PALETTE[k][1], PALETTE[k][2]), srgb=False)

uvl = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    idx = poly.material_index
    u = ((idx % PAL_GRID) + 0.5) / PAL_GRID
    v = ((idx // PAL_GRID) + 0.5) / PAL_GRID
    for li in poly.loop_indices:
        uvl.data[li].uv = (u, v)
    poly.material_index = 0

mat = bpy.data.materials.new("M_PlayerSickle")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = base_img; t1.interpolation = 'Closest'
nt.links.new(t1.outputs["Color"], bsdf.inputs["Base Color"])
t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = ms_img; t2.interpolation = 'Closest'
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(t2.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs[0], bsdf.inputs["Metallic"])
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(t2.outputs["Alpha"], inv.inputs[1])
nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
me.materials.append(mat)

# flat-shaded low-poly look on the blade, smooth handle
for poly in me.polygons:
    poly.use_smooth = False
me.update()

tris = len(me.polygons)
d = ob.dimensions
print(f"SICKLE tris={tris} dims(x={d.x:.3f}, y={d.y:.3f}, z={d.z:.3f}) zmin={min(v.co.z for v in me.vertices):.3f} zmax={max(v.co.z for v in me.vertices):.3f}")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, NAME + ".blend"))

ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, NAME + ".fbx"),
    use_selection=True, object_types={'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z', axis_up='Y', bake_space_transform=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
    path_mode='RELATIVE', embed_textures=False,
)
print("EXPORTED")

# ---------------------------------------------------------------- previews: side view + first-person view
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
bpy.ops.object.light_add(type='SUN', rotation=(0.9, 0.3, -0.6))
bpy.context.object.data.energy = 3.5
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data); scene.collection.objects.link(cam); scene.camera = cam

# side (orthographic, looking along -X... from +X)
cam_data.type = 'ORTHO'; cam_data.ortho_scale = 0.62
cam.location = (1.0, -0.11, 0.15)
cam.rotation_euler = (Vector((0, -0.11, 0.15)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x, scene.render.resolution_y = 800, 800
scene.render.filepath = os.path.join(HERE, "render_side.png")
bpy.ops.render.render(write_still=True)

# first-person: camera at eye, sickle held bottom-right, blade forward
cam_data.type = 'PERSP'; cam_data.lens = 24
ob.location = (-0.24, -0.55, -0.3)          # camera looks along -Y, so screen-right is -X
ob.rotation_euler = (math.radians(-20), math.radians(15), math.radians(35))
cam.location = (0, 0, 0)
cam.rotation_euler = (Vector((0, -1, -0.05))).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -1.6))
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.16, 0.05, 1)
bpy.context.object.data.materials.append(g)
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.filepath = os.path.join(HERE, "render_fp.png")
bpy.ops.render.render(write_still=True)
print("RENDERED")
