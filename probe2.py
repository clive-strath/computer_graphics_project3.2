import bpy, sys
a=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print("BONES", [b.name for b in a.data.bones])
print("ARMOBJ", a.name, tuple(round(v,3) for v in a.scale), tuple(round(v,3) for v in a.rotation_euler), a.parent)
for ac in bpy.data.actions:
    print("ACT", ac.name, tuple(int(x) for x in ac.frame_range), len(ac.slots))
for o in bpy.data.objects: print("OB", o.name, o.type, o.parent.name if o.parent else None, [m.type for m in o.modifiers], tuple(round(v,3) for v in o.scale))
for im in bpy.data.images: print("IMG", im.name, im.filepath)
print("FPS", bpy.context.scene.render.fps)
