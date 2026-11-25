import bpy, os
from mathutils import Vector
s=bpy.context.scene; s.render.use_overwrite=True; s.render.use_placeholder=False
cam=bpy.data.objects['Camera']; root=bpy.data.objects['CamRoot']
root.animation_data_clear(); cam.data.animation_data_clear(); cam.animation_data_clear(); cam.location=(0,0,0)
def shot(t, loc, tgt, lens, name):
    s.frame_set(int(t*24)+1); root.location=loc; root.rotation_mode='QUATERNION'
    root.rotation_quaternion=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y'); cam.data.lens=lens
    s.render.filepath=bpy.path.abspath(f'//test/{name}.png'); bpy.ops.render.render(write_still=True)
shot(58,(11.2,-2.4,0.8),(8.6,-2.1,0.5),35,'side_sit')
shot(250,(197.2,-2.2,0.9),(196.4,0,0.4),30,'side_floor')
