import bpy, os, glob, math
from mathutils import Vector
DL = r"C:/Users/clive/Downloads"
BLD = DL + "/Models with Materials-20261123T074857Z-1-001/Models with Materials/Blends"
ZK = DL + "/Zombie Apocalypse Kit - March 2024-20261123T075223Z-1-001/Zombie Apocalypse Kit - March 2024/Characters/Blends"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
files = sorted(glob.glob(BLD + "/*.blend"))
S = 2.6
x = 0
for i, fp in enumerate(files):
    with bpy.data.libraries.load(fp, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    for o in dst.objects:
        if o and o.type == "MESH":
            sc.collection.objects.link(o)
            o.scale = (S, S, S)
            o.location = (x, (i // 13) * 14, 0)
            o.rotation_euler = (0, 0, 0)
            bpy.context.view_layer.update()
            cu = bpy.data.curves.new("t", "FONT"); cu.body = os.path.basename(fp).replace("_Mat.blend", ""); cu.size = 0.6
            t = bpy.data.objects.new("t", cu); sc.collection.objects.link(t); t.location = (x - 2, (i // 13) * 14 - 5, 0.05)
            x += 9 if (i % 13) != 12 else -9 * 12
            break
for n, xx in (("Characters_Lis", -6), ("Zombie_Basic", -4)):
    with bpy.data.libraries.load(f"{ZK}/{n}.blend", link=False) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        if o and o.type in ("ARMATURE", "MESH") and o.name.split(".")[0] in ("CharacterArmature", "Lis", "Zombie", "Eyelid"):
            sc.collection.objects.link(o)
            if o.type == "ARMATURE":
                o.location = (xx, 0, 0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 125
cam.location = (50, -60, 30); d = Vector((50, 7, 3)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sun = bpy.data.objects.new("sun", bpy.data.lights.new("s", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (0.8, 0.2, 0.4); sun.data.energy = 3
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.5, 0.6, 0.7)
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = 1920; sc.render.resolution_y = 900
sc.render.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "lineup.png")
bpy.ops.render.render(write_still=True)
# close-up for scale check
cam.data.type = "PERSP"; cam.data.lens = 35
cam.location = (-3, -9, 2.2); d = Vector((1, 0, 1.6)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "scale.png")
bpy.ops.render.render(write_still=True)
print("MISSING", [im.name for im in bpy.data.images if im.filepath and not im.has_data])
