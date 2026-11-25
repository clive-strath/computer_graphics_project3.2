import bpy, sys, time, os
s = bpy.context.scene
ts = [float(x) for x in sys.argv[sys.argv.index('--')+1:]]
s.render.use_overwrite = True; s.render.use_placeholder = False
for t in ts:
    s.frame_set(int(round(t*24))+1)
    s.render.filepath = os.path.join(bpy.path.abspath('//test'), f"t{t:06.1f}.png")
    a = time.time(); bpy.ops.render.render(write_still=True); print("RENDERED", t, round(time.time()-a,2))
