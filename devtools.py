# THE ZOMBIE APOCALYPSE - developer / test tools (replaces render_test.py, side_test.py,
# lineup.py, probe2.py, probe_bld.py, probe_chars.py). Pick a tool after "--":
#
#   blender -b TheZombieApocalypse.blend --python devtools.py -- render 58 150.5 250   (was render_test.py)
#   blender -b TheZombieApocalypse.blend --python devtools.py -- side                  (was side_test.py)
#   blender -b --python devtools.py -- lineup                                          (was lineup.py)
#   blender -b <any_char>.blend          --python devtools.py -- probe_rig             (was probe2.py)
#   blender -b --python devtools.py -- probe_bld                                       (was probe_bld.py)
#   blender -b --python devtools.py -- probe_chars <file.blend|.gltf|.fbx>             (was probe_chars.py)
#
# Pipeline order (unchanged):  build_zombie.py -> render frames -> make_audio.py -> assemble.py
import bpy, sys, os, time, glob
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DL = r"C:/Users/clive/Downloads"
BLD = DL + "/Models with Materials-20261123T074857Z-1-001/Models with Materials/Blends"
ZK = DL + "/Zombie Apocalypse Kit - March 2024-20261123T075223Z-1-001/Zombie Apocalypse Kit - March 2024/Characters/Blends"


# ------------------------------------------------------------------ render <t> [t ...]
def render(args):
    """Render stills of the open film .blend at the given times (seconds) into //test."""
    s = bpy.context.scene
    ts = [float(x) for x in args]
    s.render.use_overwrite = True; s.render.use_placeholder = False
    for t in ts:
        s.frame_set(int(round(t*24))+1)
        s.render.filepath = os.path.join(bpy.path.abspath('//test'), f"t{t:06.1f}.png")
        a = time.time(); bpy.ops.render.render(write_still=True); print("RENDERED", t, round(time.time()-a,2))


# ------------------------------------------------------------------ side
def side(args):
    """Side-angle checks of the bench sit and floor sit (clears camera animation - don't save!)."""
    s=bpy.context.scene; s.render.use_overwrite=True; s.render.use_placeholder=False
    cam=bpy.data.objects['Camera']; root=bpy.data.objects['CamRoot']
    root.animation_data_clear(); cam.data.animation_data_clear(); cam.animation_data_clear(); cam.location=(0,0,0)
    def shot(t, loc, tgt, lens, name):
        s.frame_set(int(t*24)+1); root.location=loc; root.rotation_mode='QUATERNION'
        root.rotation_quaternion=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y'); cam.data.lens=lens
        s.render.filepath=bpy.path.abspath(f'//test/{name}.png'); bpy.ops.render.render(write_still=True)
    shot(58,(11.2,-2.4,0.8),(8.6,-2.1,0.5),35,'side_sit')
    shot(250,(197.2,-2.2,0.9),(196.4,0,0.4),30,'side_floor')


# ------------------------------------------------------------------ lineup
def lineup(args):
    """Render every building model in a grid (test/lineup.png) plus a Maya/zombie scale check (test/scale.png)."""
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
    sc.render.filepath = os.path.join(HERE, "test", "lineup.png")
    bpy.ops.render.render(write_still=True)
    # close-up for scale check
    cam.data.type = "PERSP"; cam.data.lens = 35
    cam.location = (-3, -9, 2.2); d = Vector((1, 0, 1.6)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(HERE, "test", "scale.png")
    bpy.ops.render.render(write_still=True)
    print("MISSING", [im.name for im in bpy.data.images if im.filepath and not im.has_data])


# ------------------------------------------------------------------ probe_rig
def probe_rig(args):
    """Print bones, actions, objects and images of the currently open .blend."""
    a=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    print("BONES", [b.name for b in a.data.bones])
    print("ARMOBJ", a.name, tuple(round(v,3) for v in a.scale), tuple(round(v,3) for v in a.rotation_euler), a.parent)
    for ac in bpy.data.actions:
        print("ACT", ac.name, tuple(int(x) for x in ac.frame_range), len(ac.slots))
    for o in bpy.data.objects: print("OB", o.name, o.type, o.parent.name if o.parent else None, [m.type for m in o.modifiers], tuple(round(v,3) for v in o.scale))
    for im in bpy.data.images: print("IMG", im.name, im.filepath)
    print("FPS", bpy.context.scene.render.fps)


# ------------------------------------------------------------------ probe_bld
def probe_bld(args):
    """Print mesh count, dimensions and materials of the first 26 building models."""
    for fp in sorted(glob.glob(BLD+"/*.blend"))[:26]:
        with bpy.data.libraries.load(fp) as (src, dst):
            dst.objects = src.objects
        obs=[o for o in dst.objects if o and o.type=='MESH']
        dims=[tuple(round(x,1) for x in o.dimensions) for o in obs]
        mats=sorted({m.name for o in obs for m in o.data.materials if m})
        print("BLD", os.path.basename(fp), len(obs), dims[:2], mats[:6])


# ------------------------------------------------------------------ probe_chars <file>
def probe_chars(args):
    """Open/import a character file and print its armature, meshes and actions."""
    fp = args[0]
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


# ------------------------------------------------------------------ dispatch
TOOLS = {"render": render, "side": side, "lineup": lineup,
         "probe_rig": probe_rig, "probe_bld": probe_bld, "probe_chars": probe_chars}

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv or argv[0] not in TOOLS:
    print("usage: blender -b [file.blend] --python devtools.py -- <tool> [args]")
    for name, fn in TOOLS.items():
        print(f"  {name:12s} {fn.__doc__}")
else:
    TOOLS[argv[0]](argv[1:])
