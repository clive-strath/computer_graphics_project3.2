import bpy, glob, os
d=r"C:/Users/clive/Downloads/Models with Materials-20261123T074857Z-1-001/Models with Materials/Blends"
for fp in sorted(glob.glob(d+"/*.blend"))[:26]:
    with bpy.data.libraries.load(fp) as (src, dst):
        dst.objects = src.objects
    obs=[o for o in dst.objects if o and o.type=='MESH']
    dims=[tuple(round(x,1) for x in o.dimensions) for o in obs]
    mats=sorted({m.name for o in obs for m in o.data.materials if m})
    print("BLD", os.path.basename(fp), len(obs), dims[:2], mats[:6])
