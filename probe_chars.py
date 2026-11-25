import bpy, sys, os
fp = sys.argv[sys.argv.index('--')+1]
if fp.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=fp)
elif fp.endswith('.gltf'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=fp)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=fp)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
meshes=[o for o in bpy.data.objects if o.type=='MESH']
print("FILE", os.path.basename(fp), "arm", [(a.name, len(a.data.bones)) for a in arms], "meshes", [(m.name, round(m.dimensions.z,2)) for m in meshes][:6])
print("ACTIONS", os.path.basename(fp), len(bpy.data.actions), sorted(a.name for a in bpy.data.actions)[:70])
