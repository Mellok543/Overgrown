import os, bpy, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"E:\UnityProject\Overgrown\Assets\Art\Models\Grass"
ATLAS = os.path.join(OUT, "Grass_Atlas.png")
NAMES = ["Grass_Tall_01", "Grass_Tall_02", "Grass_Tall_03", "Grass_Cut"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# one shared material
mat = bpy.data.materials.new("M_Grass")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(ATLAS)
tex.interpolation = 'Linear'
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
bsdf.inputs["Metallic"].default_value = 0.0
for key in ("Specular IOR Level", "Specular"):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = 0.1
        break

for name in NAMES:
    d = np.load(os.path.join(HERE, name + ".npz"))
    pos, tris, uv, nrm = d["pos"], d["tris"], d["uv"], d["nrm"]
    # generator is Y-up; Blender is Z-up: (x, y, z) -> (x, -z, y)
    bpos = [(p[0], -p[2], p[1]) for p in pos]
    bnrm = [(n[0], -n[2], n[1]) for n in nrm]

    me = bpy.data.meshes.new(name)
    me.from_pydata(bpos, [], [tuple(int(i) for i in t) for t in tris])
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uvl.data[loop.index].uv = tuple(uv[loop.vertex_index])
    # upward-biased custom normals (softer grass lighting)
    me.normals_split_custom_set_from_vertices(bnrm)
    me.materials.append(mat)

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.location = (0, 0, 0); ob.rotation_euler = (0, 0, 0); ob.scale = (1, 1, 1)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, name + ".fbx"),
        use_selection=True,
        object_types={'MESH'},
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z', axis_up='Y',
        bake_space_transform=True,
        use_mesh_modifiers=True,
        mesh_smooth_type='OFF',
        use_tspace=False,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode='RELATIVE',
        embed_textures=False,
    )
    print("EXPORTED", name, len(me.polygons), "tris")

# reference .blend with all four, side by side, for later edits
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for i, name in enumerate(NAMES):
    ob = bpy.data.objects.new(name, bpy.data.meshes[name])
    scene.collection.objects.link(ob)
    ob.location = (i * 1.0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Grass_Set.blend"))

# preview render
bpy.ops.object.light_add(type='SUN', rotation=(0.8, 0.2, 0.6))
bpy.context.object.data.energy = 3.5
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.55, 0.7, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
bpy.ops.mesh.primitive_plane_add(size=6, location=(1.5, 0, 0))
g = bpy.data.materials.new("Ground"); g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.13, 0.08, 1)
bpy.context.object.data.materials.append(g)
bpy.ops.object.camera_add(location=(1.5, -3.4, 0.85), rotation=(1.40, 0, 0))
scene.camera = bpy.context.object
scene.camera.data.lens = 32
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1400, 600
scene.render.filepath = os.path.join(HERE, "grass_render.png")
bpy.ops.render.render(write_still=True)
print("RENDERED")
