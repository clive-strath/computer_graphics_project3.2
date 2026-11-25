# THE ZOMBIE APOCALYPSE - scene build script (Blender 5.3)
#   blender -b -y --python build_zombie.py
import bpy, bmesh, math, random, os, re
from mathutils import Vector, Matrix, Euler, Quaternion

random.seed(11)
pi = math.pi
FPS = 24
E = 1.0 / FPS
END_T = 330
HERE = os.path.dirname(os.path.abspath(__file__))
DL = r"C:/Users/clive/Downloads"
BLD = DL + "/Models with Materials-20261123T074857Z-1-001/Models with Materials/Blends"
ZK = DL + "/Zombie Apocalypse Kit - March 2024-20261123T075223Z-1-001/Zombie Apocalypse Kit - March 2024"
NAT = DL + "/The_Winners_Silence_Curated_Assets/The_Winners_Silence_Curated_Assets/02_Nature_Environment"


def f(t):
    return int(round(t * FPS)) + 1


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "ZombieFilm"
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = f(END_T) - 1
COL = scene.collection

# ------------------------------------------------------------------ generic helpers
MATS = {}


def M(name, col, rough=0.8, emit=0.0, ecol=None, metal=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*(ecol or col), 1)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def M_noise(name, c1, c2, scale=8.0, rough=0.9):
    m = M(name, c1, rough=rough)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*c1, 1)
    cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF")


def K(owner, path, value, t=None, frame=None, index=-1):
    fr = frame if frame is not None else f(t)
    if index >= 0:
        getattr(owner, path)[index] = value
    else:
        setattr(owner, path, value)
    owner.keyframe_insert(path, index=index, frame=fr)


def D(owner, path, expr, index=-1):
    fc = owner.driver_add(path, index)
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = expr
    return fc


def W(t0, t1):
    return f"({f(t0)}<=frame<{f(t1)})"


MESH = {}


def mesh_for(kind, mat, seg=8, r2=0.5):
    key = (kind, mat.name if mat else "", seg, r2)
    if key in MESH:
        return MESH[key]
    bm = bmesh.new()
    if kind == "cube":
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=0.5, radius2=r2, depth=1.0)
    elif kind == "ico":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    me = bpy.data.meshes.new(kind)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    MESH[key] = me
    return me


def mk(name, kind, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, parent=None, **kw):
    ob = bpy.data.objects.new(name, mesh_for(kind, mat, **kw))
    COL.objects.link(ob)
    if parent:
        ob.parent = parent
    ob.location = loc
    ob.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
    ob.rotation_euler = rot
    return ob


def emp(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    COL.objects.link(ob)
    if parent:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def vis(obj, windows):
    for o in [obj] + list(obj.children_recursive):
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        for t0, t1 in windows:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f(t0))
            if t1 < END_T:
                o.hide_render = True
                o.keyframe_insert("hide_render", frame=f(t1))
        o.hide_render = False


def text3d(name, body, loc, size, mat, rot=(pi / 2, 0, 0), extrude=0.05):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.extrude = extrude
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    COL.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def face_ang(dx, dy):
    return math.atan2(dx, -dy)  # rig forward is -Y


# ------------------------------------------------------------------ ground & layout
m_grass = M_noise("lawn", (0.16, 0.33, 0.08), (0.26, 0.45, 0.12), scale=0.35)
m_path = M_noise("paving", (0.55, 0.52, 0.47), (0.66, 0.63, 0.57), scale=1.5)
m_court = M_noise("courtyard", (0.45, 0.43, 0.4), (0.55, 0.52, 0.48), scale=1.2)
mk("Lawn", "cube", (0, 0, -0.05), (160, 160, 0.1), mat=m_grass)
mk("PathNS", "cube", (0, 3, 0.005), (3.2, 42, 0.02), mat=m_path)
mk("PathEW", "cube", (0, -3.6, 0.006), (52, 2.6, 0.02), mat=m_path)
mk("PathEast", "cube", (22, -10, 0.007), (2.6, 14, 0.02), mat=m_path)
mk("Courtyard", "cube", (0, -27, 0.004), (64, 18, 0.02), mat=m_court)
mk("ArchApron", "cube", (0, 21.5, 0.006), (12, 5, 0.02), mat=m_path)

# ------------------------------------------------------------------ buildings
S = 2.2
PALETTE = [((0.78, 0.68, 0.52), (0.45, 0.3, 0.22)), ((0.62, 0.3, 0.22), (0.4, 0.36, 0.33)),
           ((0.84, 0.8, 0.7), (0.5, 0.42, 0.35)), ((0.7, 0.55, 0.4), (0.38, 0.3, 0.26)),
           ((0.56, 0.24, 0.18), (0.5, 0.46, 0.4))]
FACING = {"S": 0.0, "N": pi, "E": pi / 2, "W": -pi / 2}
bcount = [0]


def building(model, X, Y, facing="S", pal=None):
    fp = f"{BLD}/{model}_Mat.blend"
    with bpy.data.libraries.load(fp, link=False) as (src, dst):
        dst.objects = list(src.objects)
    ob = [o for o in dst.objects if o and o.type == "MESH"][0]
    COL.objects.link(ob)
    ob.scale = (S, S, S)
    vs = [Vector(c) for c in ob.bound_box]
    minx, maxx = min(v.x for v in vs) * S, max(v.x for v in vs) * S
    miny, maxy = min(v.y for v in vs) * S, max(v.y for v in vs) * S
    minz = min(v.z for v in vs) * S
    th = FACING[facing]
    ob.rotation_euler = (0, 0, th)
    cx = (minx + maxx) / 2
    lx, ly = cx, miny
    wx = lx * math.cos(th) - ly * math.sin(th)
    wy = lx * math.sin(th) + ly * math.cos(th)
    ob.location = (X - wx, Y - wy, -minz)
    pal = pal or PALETTE[bcount[0] % len(PALETTE)]
    bcount[0] += 1
    for slot in ob.material_slots:
        m = slot.material
        if not m:
            continue
        base = m.name.split(".")[0]
        if base == "Main":
            bsdf(m).inputs["Base Color"].default_value = (*pal[0], 1)
        elif base == "Bricks":
            bsdf(m).inputs["Base Color"].default_value = (*pal[1], 1)
        elif base in ("RoofBricks",):
            bsdf(m).inputs["Base Color"].default_value = (0.32, 0.2, 0.16, 1)
    ob.name = f"Bld_{model}"
    width = maxx - minx
    return ob, width, (maxy - miny)


# main north range with central arch
m_stone = M_noise("arch_stone", (0.72, 0.64, 0.5), (0.8, 0.72, 0.58), scale=3)
m_dark = M("tunnel_dark", (0.008, 0.008, 0.008), rough=1.0)
AY = 24.0  # front line of the main building
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, AY + 3, 5)) @ Matrix.Diagonal((10, 6, 10, 1)))
blk = bpy.data.meshes.new("ArchBlock")
bm.to_mesh(blk)
bm.free()
blk.materials.append(m_stone)
arch = bpy.data.objects.new("MainArch", blk)
COL.objects.link(arch)
cut = mk("ArchCut", "cube", (0, AY + 3, 2.25), (4.4, 7, 4.5))
cutc = mk("ArchCutTop", "cyl", (0, AY + 3, 4.5), (4.4, 4.4, 7), rot=(pi / 2, 0, 0), seg=24)
for c_ in (cut, cutc):
    c_.hide_render = True
    c_.hide_viewport = True
    mod = arch.modifiers.new("cut", "BOOLEAN")
    mod.object = c_
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
mk("TunnelBack", "cube", (0, AY + 6.2, 4), (6, 0.4, 8), mat=m_dark)
mk("TunnelFloor", "cube", (0, AY + 3, 0.01), (4.4, 6, 0.02), mat=m_dark)
mk("ArchTrim", "cube", (0, AY - 0.15, 9.8), (10.6, 0.5, 0.5), mat=M("trim", (0.9, 0.85, 0.75)))
m_letter = M("letters", (0.2, 0.17, 0.12))
text3d("UniSign", "UNIVERSITY", (0, AY - 0.06, 7.6), 0.95, m_letter, extrude=0.04)
for sx in (-1, 1):
    building("4Story_Wide_2Doors_Roof", sx * 12.5, AY, "S", pal=PALETTE[0])
    building("4Story_Center", sx * 22.6, AY, "S", pal=PALETTE[2])
    building("6Story_Stack", sx * 27.6, AY + 0.5, "S", pal=PALETTE[0])

# west range (faces +x) - door 1 at y=-8, door 2 at y=0, alley 4..7
DOORS = {}
WX = -26.0
DOORS["d1"] = (WX, -8.0)
DOORS["d2"] = (WX, 0.0)
building("2Story", WX, -8.0, "E", pal=PALETTE[1])
building("2Story_Columns", WX, 0.0, "E", pal=PALETTE[2])
building("3Story_Balcony", WX, -14.5, "E", pal=PALETTE[3])
building("2Story_Wide", WX, 10.8, "E", pal=PALETTE[4])
building("4Story", WX, 17.5, "E", pal=PALETTE[0])
mk("AlleyDark", "cube", (WX - 6, 5.6, 2.5), (0.3, 3.4, 5), mat=m_dark)
# east range (faces -x) - Maya walks past these
EX = 26.0
building("2Story_Balcony", EX, -14.0, "W", pal=PALETTE[2])
building("2Story_Wide_2Doors", EX, -5.5, "W", pal=PALETTE[1])
building("3Story_Slim", EX, 2.0, "W", pal=PALETTE[3])
building("2Story_Double", EX, 7.0, "W", pal=PALETTE[0])
building("4Story_Wide_2Doors", EX, 15.0, "W", pal=PALETTE[4])
# south courtyard range (faces +y) - the last door at x=-12
SY = -28.0
DOORS["d3"] = (-12.0, SY)
building("2Story", -12.0, SY, "N", pal=PALETTE[0])
building("2Story_Wide", -21.0, SY, "N", pal=PALETTE[3])
building("2Story_Sidehouse", -3.0, SY, "N", pal=PALETTE[2])
building("2Story_GableRoof", 5.5, SY, "N", pal=PALETTE[1])
building("3Story_Small", 13.0, SY, "N", pal=PALETTE[4])
building("2Story_Stairs", 21.0, SY, "N", pal=PALETTE[0])
building("4Story_Center", -29.0, SY, "N", pal=PALETTE[2])

# door slabs (front of model doors); door 3 opens
m_doorwood = M("doorwood", (0.3, 0.17, 0.08))
m_metal = M("metal", (0.25, 0.25, 0.27), rough=0.4, metal=0.8)


def door_slab(name, x, y, facing, hinge_side=1):
    th = FACING[facing]
    nrm = Vector((math.sin(th) * -1, math.cos(th) * -1, 0)) * -1  # outward normal
    nrm = Vector((-math.sin(-th), -math.cos(th), 0)) if False else Vector((math.sin(th), -math.cos(th), 0))
    tang = Vector((math.cos(th), math.sin(th), 0))
    base = Vector((x, y, 0)) + nrm * 0.03
    dw, dh = 1.15, 2.1
    back = mk(name + "_dark", "cube", base + nrm * 0.0 + Vector((0, 0, dh / 2)), (dw, 0.02, dh), rot=(0, 0, th), mat=m_dark)
    hinge = emp(name + "_hinge", base + nrm * 0.04 - tang * (dw / 2) * hinge_side, rot=(0, 0, th))
    slab = mk(name, "cube", (dw / 2 * hinge_side, 0, dh / 2), (dw, 0.07, dh), mat=m_doorwood, parent=hinge)
    mk(name + "_knob", "ico", (dw * 0.85 * hinge_side, -0.07, 1.0), (0.08, 0.08, 0.08), mat=m_metal, parent=hinge)
    return hinge, nrm


h1, n1 = door_slab("Door1", *DOORS["d1"], "E")
h2, n2 = door_slab("Door2", *DOORS["d2"], "E")
h3, n3 = door_slab("Door3", *DOORS["d3"], "N")
door3 = h3
for t_, a_ in ((219.4, 0.0), (220.2, -1.7), (222.7, -1.7), (223.0, 0.0), (270.2, 0.0), (270.9, -1.7)):
    K(door3, "rotation_euler", FACING["N"] + a_, t=t_, index=2)
# locked doors rattle a little
for h_, ts in ((h1, (191.6, 192.6, 193.6)), (h2, (198.3, 199.2, 200.1))):
    th0 = h_.rotation_euler[2]
    for t_ in ts:
        K(h_, "rotation_euler", th0, t=t_, index=2)
        K(h_, "rotation_euler", th0 - 0.04, t=t_ + 0.12, index=2)
        K(h_, "rotation_euler", th0, t=t_ + 0.25, index=2)

# steel fence with a gap at x=-18 between quad and courtyard
m_steel = M("steel", (0.18, 0.19, 0.2), rough=0.35, metal=0.9)
FY = -18.5
xs = [x * 0.25 for x in range(-120, 121)]
bm = bmesh.new()
for x in xs:
    if -19.2 < x < -16.8:
        continue
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((x, FY, 0.75)) @ Matrix.Diagonal((0.04, 0.04, 1.5, 1)))
for z in (0.15, 1.35):
    for (a, b) in ((-30, -19.2), (-16.8, 30)):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((a + b) / 2, FY, z)) @ Matrix.Diagonal((b - a, 0.06, 0.06, 1)))
fm = bpy.data.meshes.new("Fence")
bm.to_mesh(fm)
bm.free()
fm.materials.append(m_steel)
fence = bpy.data.objects.new("SteelFence", fm)
COL.objects.link(fence)

# ------------------------------------------------------------------ nature (Quaternius stylized nature, CC0)
NATLIB = {}


m_leafA = M("leafA", (0.16, 0.36, 0.1))
m_leafB = M("leafB", (0.22, 0.42, 0.12))
m_leafC = M("leafC", (0.12, 0.3, 0.09))
m_bark = M("bark", (0.28, 0.18, 0.1))
m_flower = M("flowers", (0.9, 0.35, 0.45))
m_flower2 = M("flowers2", (0.95, 0.85, 0.3))
m_rock = M("rock", (0.42, 0.42, 0.4))
m_gr1 = M("grassblade", (0.2, 0.42, 0.1))
m_gr2 = M("grassblade2", (0.3, 0.5, 0.14))


def build_mesh(name, items):
    """items: (kind, loc, scale, rot, mat)"""
    bm = bmesh.new()
    mats = []
    for kind, loc, sc, rot, mat in items:
        if mat not in mats:
            mats.append(mat)
        mi = mats.index(mat)
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*sc, 1))
        if kind == "cube":
            res = bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)
        elif kind == "cyl":
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.5, radius2=0.35, depth=1.0, matrix=mtx)
        elif kind == "cone":
            res = bmesh.ops.create_cone(bm, cap_ends=False, segments=3, radius1=0.5, radius2=0.0, depth=1.0, matrix=mtx)
        else:
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5, matrix=mtx)
        for v in res["verts"]:
            for fc in v.link_faces:
                fc.material_index = mi
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


NATLIB = {}


def nat_mesh(name):
    if name in NATLIB:
        return NATLIB[name]
    R = random.Random(hash(name) % 1000)
    it = []
    if name.startswith("CommonTree") or name.startswith("TwistedTree"):
        h = {"CommonTree_1": 3.2, "CommonTree_3": 4.0, "CommonTree_5": 2.6, "TwistedTree_1": 2.6}[name]
        it.append(("cyl", (0, 0, h / 2), (0.45, 0.45, h), (0, 0, 0), m_bark))
        lm = {"CommonTree_1": m_leafA, "CommonTree_3": m_leafB, "CommonTree_5": m_leafC, "TwistedTree_1": m_leafC}[name]
        for k in range(7):
            a = k * 2 * pi / 7
            r_ = 1.3 if k else 0.0
            it.append(("ico", (r_ * math.cos(a), r_ * math.sin(a), h + 0.6 + R.uniform(-0.4, 0.8)),
                       (R.uniform(2.2, 3.0),) * 2 + (R.uniform(1.8, 2.4),), (0, 0, k), lm))
        it.append(("ico", (0, 0, h + 1.7), (2.4, 2.4, 2.0), (0, 0, 0), lm))
    elif name.startswith("Bush"):
        for k in range(4):
            a = k * 2 * pi / 4
            it.append(("ico", (0.35 * math.cos(a), 0.35 * math.sin(a), 0.55 + R.uniform(-0.1, 0.15)), (1.0, 1.0, 0.85), (0, 0, k), m_leafB))
        if "Flowers" in name:
            for k in range(10):
                a = R.uniform(0, 2 * pi)
                it.append(("ico", (0.7 * math.cos(a), 0.7 * math.sin(a), R.uniform(0.5, 1.0)), (0.14,) * 3, (0, 0, 0), m_flower))
    elif name.startswith("Grass") or name.startswith("Clover"):
        n = 9 if "Tall" in name else 7
        hh = 0.75 if "Tall" in name else 0.4
        for k in range(n):
            a = R.uniform(0, 2 * pi)
            r_ = R.uniform(0, 0.18)
            it.append(("cone", (r_ * math.cos(a), r_ * math.sin(a), hh / 2), (0.09, 0.09, hh * R.uniform(0.7, 1.2)),
                       (R.uniform(-0.25, 0.25), R.uniform(-0.25, 0.25), 0), m_gr1 if k % 2 else m_gr2))
    elif name.startswith("Flower"):
        for k in range(6):
            a = R.uniform(0, 2 * pi)
            x, y = 0.25 * math.cos(a), 0.25 * math.sin(a)
            it.append(("cone", (x, y, 0.2), (0.05, 0.05, 0.4), (0, 0, 0), m_gr1))
            it.append(("ico", (x, y, 0.42), (0.12,) * 3, (0, 0, 0), m_flower if k % 2 else m_flower2))
    elif name.startswith("Fern") or name.startswith("Plant"):
        for k in range(6):
            a = k * 2 * pi / 6
            it.append(("cone", (0.25 * math.cos(a), 0.25 * math.sin(a), 0.3), (0.2, 0.08, 0.7), (0.5 * math.sin(a), -0.5 * math.cos(a), a), m_leafA))
    else:  # rocks
        it.append(("ico", (0, 0, 0.3), (1.2, 1.0, 0.75), (0, 0, 0), m_rock))
    NATLIB[name] = build_mesh(name, it)
    return NATLIB[name]


def place(name, x, y, s=1.0, rz=None, z=0.0):
    ob = bpy.data.objects.new(name, nat_mesh(name))
    COL.objects.link(ob)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, random.uniform(0, 2 * pi) if rz is None else rz)
    ob.scale = (s, s, s)
    return ob


TREES = [(8.6, 1.6, "CommonTree_1", 0.75)]  # bench tree
for (x, y) in [(-12, 14), (-18, 9), (-7, 18), (12, 15), (18, 9), (7, 19), (-20, -6), (-6, -15), (14, -13), (20, 2),
               (-15, 2), (15, -2), (-10, -2), (4, 10), (-3, -12), (17, -16), (-22, 12), (22, -9)]:
    TREES.append((x + random.uniform(-0.8, 0.8), y + random.uniform(-0.8, 0.8),
                  random.choice(["CommonTree_1", "CommonTree_3", "CommonTree_5"]), random.uniform(0.7, 0.95)))
for x, y, n, s in TREES:
    place(n, x, y, s * 1.6)
# tree with a low branch for the duck (x=-14, path y=-12.5)
place("TwistedTree_1", -14.0, -10.3, 0.8)
mk("LowBranch", "cyl", (-14.0, -12.0, 1.38), (0.16, 0.16, 4.2), rot=(pi / 2, 0, 0.12), mat=M("branch", (0.27, 0.18, 0.1)), seg=7)
for k in range(5):
    place("Bush_Common", -14.0 + random.uniform(-0.4, 0.4), -13.6 - k * 0.1, 0.45, z=1.3).scale *= 0.6
# hedge line at x=-4 (jumped at y=-10)
for k in range(16):
    place("Bush_Common", -4.0, -16.5 + k * 0.85, 0.48)
for k in range(10):
    place("Bush_Common_Flowers", 4.0, -16.5 + k * 1.1, 0.45)
for k in range(30):
    x, y = random.uniform(-24, 24), random.uniform(-17, 20)
    if abs(x) < 2.5 or abs(y + 3.6) < 2 or (abs(x - 8.6) < 3 and abs(y + 2) < 3):
        continue
    place(random.choice(["Bush_Common", "Bush_Common_Flowers", "Fern_1", "Plant_1"]), x, y, random.uniform(0.4, 0.7))
for k in range(380):
    x, y = random.uniform(-25, 25), random.uniform(-17.5, 21)
    if abs(x) < 2.2 or abs(y + 3.6) < 1.8 or (abs(x - 22) < 1.8 and y < -3):
        continue
    place(random.choice(["Grass_Common_Short", "Grass_Common_Short", "Grass_Wispy_Short", "Grass_Common_Tall", "Clover_1"]),
          x, y, random.uniform(0.45, 0.8))
for k in range(30):
    place(random.choice(["Flower_3_Group", "Flower_4_Group"]), random.uniform(-20, 20), random.uniform(-15, 18), 0.5)
for k in range(10):
    place(random.choice(["Rock_Medium_1", "Rock_Medium_2", "Pebble_Round_1"]), random.uniform(-25, 25), random.uniform(-17, 20), 0.35)
# garden where zombies rise - trembling grass clumps around (-10..-5, 4..9)
RISE = [(-11.5, 5.0), (-9.0, 7.5), (-7.0, 4.5), (-12.5, 8.5), (-5.5, 8.0), (-8.5, 3.2)]
tremble = []
for k in range(70):
    x, y = random.uniform(-14, -3.5), random.uniform(2, 10)
    g = place(random.choice(["Grass_Common_Short", "Grass_Common_Tall", "Grass_Wispy_Tall"]), x, y, random.uniform(0.5, 0.8))
    tremble.append(g)
    D(g, "rotation_euler", f"0.18*sin(frame*2.1+{k})*{W(132, 142)}", 0)
    D(g, "rotation_euler", f"0.18*sin(frame*2.7+{k * 1.3})*{W(132, 142)}", 1)
# crack & dirt mounds
m_dirt = M("dirt", (0.16, 0.1, 0.06), rough=1.0)
m_crack = M("crack", (0.02, 0.015, 0.01), rough=1.0)
cr_root = emp("Crack", (-13.5, 6.0, 0.02))
pts = [(0, 0)]
for k in range(9):
    pts.append((pts[-1][0] + random.uniform(0.7, 1.1), pts[-1][1] + random.uniform(-0.5, 0.5)))
for k in range(len(pts) - 1):
    a, b = Vector((*pts[k], 0)), Vector((*pts[k + 1], 0))
    d = b - a
    seg = mk(f"CrackSeg{k}", "cube", (a + b) / 2, (d.length, 0.09, 0.03), rot=(0, 0, math.atan2(d.y, d.x)), mat=m_crack, parent=cr_root)
    t0 = 133 + k * 0.35
    K(seg, "scale", Vector((0.0, 0.0, 0.0)), t=t0)
    K(seg, "scale", Vector((d.length, 0.09, 0.03)), t=t0 + 0.35)
for i, (x, y) in enumerate(RISE):
    mound = mk(f"Mound{i}", "cyl", (x, y, 0.0), (1.6, 1.6, 0.12), mat=m_dirt, seg=10, r2=0.35)
    K(mound, "scale", Vector((0, 0, 0)), t=136 + i * 0.6)
    K(mound, "scale", Vector((1.6, 1.6, 0.12)), t=137 + i * 0.6)

# ------------------------------------------------------------------ bench, radio, bag, pigeons
m_benchwood = M("benchwood", (0.42, 0.26, 0.13))
BX, BY = 8.6, -2.0
SEAT = 0.30
for k in range(3):
    mk("BenchSlat", "cube", (BX, BY - 0.12 + k * 0.13, SEAT), (1.9, 0.11, 0.04), mat=m_benchwood)
for k in range(2):
    mk("BenchBack", "cube", (BX, BY + 0.2, SEAT + 0.17 + k * 0.14), (1.9, 0.04, 0.1), rot=(0.18, 0, 0), mat=m_benchwood)
for sx in (-0.85, 0.85):
    mk("BenchLeg", "cube", (BX + sx, BY, SEAT / 2), (0.06, 0.4, SEAT), mat=m_metal)
    mk("BenchArm", "cube", (BX + sx, BY - 0.02, SEAT + 0.14), (0.06, 0.42, 0.04), mat=m_metal)
m_radio = M("radio", (0.55, 0.12, 0.08), rough=0.5)
radio = emp("Radio", (BX + 0.62, BY - 0.05, SEAT + 0.02))
mk("RadioBody", "cube", (0, 0, 0.09), (0.3, 0.12, 0.18), mat=m_radio, parent=radio)
mk("RadioGrille", "cube", (-0.05, -0.061, 0.09), (0.15, 0.01, 0.13), mat=M("grille", (0.1, 0.1, 0.1)), parent=radio)
mk("RadioAntenna", "cyl", (0.1, 0.0, 0.34), (0.012, 0.012, 0.36), rot=(0, 0.35, 0), mat=m_metal, parent=radio, seg=5)
m_dial = M("dial", (1.0, 0.6, 0.2), emit=3.0, ecol=(1.0, 0.55, 0.15))
dial = mk("RadioDial", "cube", (0.09, -0.062, 0.12), (0.06, 0.01, 0.04), mat=m_dial, parent=radio)
K(bsdf(m_dial).inputs["Emission Strength"], "default_value", 3.0, t=165.9)
K(bsdf(m_dial).inputs["Emission Strength"], "default_value", 0.0, t=166.0)
vis(radio, [(55.5, 330)])
m_bag = M("bag", (0.12, 0.2, 0.32), rough=0.7)
bag_bench = emp("BagBench", (BX - 0.62, BY - 0.02, SEAT + 0.02))
mk("BagBody", "cube", (0, 0, 0.14), (0.42, 0.18, 0.28), mat=m_bag, parent=bag_bench)
mk("BagStrap", "cube", (0, 0, 0.3), (0.32, 0.03, 0.05), mat=M("strap", (0.08, 0.08, 0.08)), parent=bag_bench)
K(bag_bench, "location", Vector(bag_bench.location), t=155.5)
K(bag_bench, "rotation_euler", Vector((0, 0, 0)), t=155.5)
K(bag_bench, "location", Vector((BX - 1.0, BY - 0.35, 0.0)), t=155.95)
K(bag_bench, "rotation_euler", Vector((1.4, 0.2, 0.3)), t=155.95)
vis(bag_bench, [(53.5, 330)])

m_pigeon = M("pigeon", (0.45, 0.46, 0.5))
pigeons = []
for k in range(4):
    px, py = BX - 1.2 + k * 0.7, BY - 1.6 - (k % 2) * 0.5
    pg = emp(f"Pigeon{k}", (px, py, 0))
    mk("PBody", "ico", (0, 0, 0.12), (0.12, 0.2, 0.12), mat=m_pigeon, parent=pg)
    mk("PHead", "ico", (0, -0.12, 0.22), (0.08, 0.08, 0.08), mat=m_pigeon, parent=pg)
    for sgn in (-1, 1):
        w = emp("PWingPivot", (sgn * 0.05, 0, 0.16), parent=pg)
        mk("PWing", "cube", (sgn * 0.12, 0, 0), (0.24, 0.12, 0.01), mat=m_pigeon, parent=w)
        D(w, "rotation_euler", f"{sgn}*0.9*sin(frame*2.4+{k})*({f(70.6 + k * 0.2)}<=frame)", 1)
    t0 = 70.6 + k * 0.2
    K(pg, "location", Vector((px, py, 0)), t=t0)
    K(pg, "location", Vector((px + random.uniform(-4, 4), py - 8 - k, 7 + k)), t=t0 + 3.0)
    pg.rotation_euler = (0, 0, random.uniform(-0.6, 0.6))
    vis(pg, [(0, 74.5)])

# ------------------------------------------------------------------ characters
WEAPONS = {"Axe", "Guitar", "Knife", "Knife_2", "Pistol", "Rifle", "Shotgun", "SMG", "Shoulder", "Spear",
           "WoodenBat_Barbed", "WoodenBat_Saw"}


def load_char(fname):
    fp = f"{ZK}/Characters/Blends/{fname}.blend"
    with bpy.data.libraries.load(fp, link=False) as (src, dst):
        names_a = list(src.actions)
        dst.objects = list(src.objects)
        dst.actions = list(src.actions)
    acts = {n: a for n, a in zip(names_a, dst.actions)}
    arm = [o for o in dst.objects if o and o.type == "ARMATURE"][0]
    meshes = [o for o in dst.objects if o and o.type == "MESH" and o.name.split(".")[0] not in WEAPONS]
    for a in acts.values():
        a.use_fake_user = True
    return arm, meshes, acts


class Rig:
    def __init__(self, name, arm, meshes, acts):
        self.name = name
        self.arm = arm.copy()
        self.arm.name = name
        self.arm.animation_data_clear()
        COL.objects.link(self.arm)
        self.meshes = []
        for m in meshes:
            m2 = m.copy()
            m2.parent = self.arm
            for md in m2.modifiers:
                if md.type == "ARMATURE":
                    md.object = self.arm
            COL.objects.link(m2)
            self.meshes.append(m2)
        self.acts = acts
        ad = self.arm.animation_data_create()
        self.base = ad.nla_tracks.new()
        self.base.name = "base"
        self.posetracks = []
        self.segs = []  # (t0, t1, action, speed)
        self.keys = []  # (t, loc, ang)

    def track(self, i):
        while len(self.posetracks) <= i:
            tr = self.arm.animation_data.nla_tracks.new()
            tr.name = f"pose{len(self.posetracks)}"
            self.posetracks.append(tr)
        return self.posetracks[i]


def add_strip(track, action, t0, t1, speed=1.0, blend="REPLACE", bin_=0.0, bout=0.0, first=False):
    fr0, fr1 = f(t0), f(t1)
    st = track.strips.new(f"{action.name}_{fr0}", fr0, action)
    try:
        st.action_slot = action.slots[0]
    except Exception:
        pass
    st.use_sync_length = False
    st.scale = 0.8 / speed
    a0, a1 = action.frame_range
    cyc = max(1.0, (a1 - a0)) * st.scale
    st.repeat = max(0.05, (fr1 - fr0 - 0.01) / cyc)
    st.blend_type = blend
    st.extrapolation = "HOLD" if first else ("HOLD_FORWARD" if blend == "REPLACE" else "NOTHING")
    st.use_auto_blend = False
    st.blend_in = bin_ * FPS
    st.blend_out = bout * FPS
    return st


OFF = Vector((0, -200, -60))


def route(rig, pts, end_t=None):
    """pts: list of dicts {t, p:(x,y[,z]), a:action, face:(x,y)|angle|None, sp:speed}"""
    arm = rig.arm
    prev_ang = None
    for i, P in enumerate(pts):
        t = P["t"]
        loc = Vector((P["p"][0], P["p"][1], P["p"][2] if len(P["p"]) > 2 else 0.0))
        nxt = pts[i + 1] if i + 1 < len(pts) else None
        face = P.get("face")
        if isinstance(face, tuple):
            ang = face_ang(face[0] - loc.x, face[1] - loc.y)
        elif isinstance(face, (int, float)):
            ang = float(face)
        elif nxt is not None and (Vector(nxt["p"][:2]) - loc.xy).length > 0.05:
            ang = face_ang(nxt["p"][0] - loc.x, nxt["p"][1] - loc.y)
        else:
            ang = prev_ang if prev_ang is not None else 0.0
        if prev_ang is not None:  # shortest turn
            while ang - prev_ang > pi:
                ang -= 2 * pi
            while ang - prev_ang < -pi:
                ang += 2 * pi
        turn = P.get("turn", 0.35)
        if i > 0 and prev_ang is not None and abs(ang - prev_ang) > 0.01:
            # rotate over a short time at the start of this waypoint
            K(arm, "rotation_euler", prev_ang, t=t, index=2)
            K(arm, "rotation_euler", ang, t=min(t + turn, (nxt["t"] if nxt else t + turn) - E), index=2)
        else:
            K(arm, "rotation_euler", ang, t=t, index=2)
        K(arm, "location", loc, t=t)
        prev_ang = ang
        if nxt is not None:
            t1 = nxt["t"]
            if not nxt.get("jump", False):
                K(arm, "location", loc + (Vector((nxt["p"][0], nxt["p"][1], nxt["p"][2] if len(nxt["p"]) > 2 else 0.0)) - loc) * 0.0, t=t)
            rig.segs.append((t, t1, P.get("a", "Idle"), P.get("sp", 1.0)))
        else:
            t1 = end_t if end_t is not None else END_T
            K(arm, "location", loc, t=t1 - E)
            rig.segs.append((t, t1, P.get("a", "Idle"), P.get("sp", 1.0)))
    return prev_ang


def finish_rig(rig, first_t, last_t):
    arm = rig.arm
    if first_t > 0:
        K(arm, "location", OFF, frame=1)
        K(arm, "location", OFF, t=first_t - E)
    if last_t < END_T:
        K(arm, "location", OFF, t=last_t)
    # merge consecutive segments with same action+speed
    merged = []
    for s in sorted(rig.segs):
        if merged and merged[-1][2] == s[2] and merged[-1][3] == s[3] and abs(merged[-1][1] - s[0]) < 1e-6:
            merged[-1] = (merged[-1][0], s[1], s[2], s[3])
        else:
            merged.append(s)
    for i, (t0, t1, a, sp) in enumerate(merged):
        if f(t1) - f(t0) < 1:
            continue
        add_strip(rig.base, rig.acts[a], t0, t1, speed=sp, first=(i == 0))


def P(t, x, y, a="Idle", **kw):
    d = {"t": t, "p": (x, y) if "z" not in kw else (x, y, kw.pop("z")), "a": a}
    d.update(kw)
    return d


# ---- pose (COMBINE) actions created from scratch
def make_action(name, channels):
    """channels: {(data_path, index): [(frame, value), ...]}"""
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name="Pose")
    layer = act.layers.new("L")
    strip = layer.strips.new(type="KEYFRAME")
    cb = strip.channelbags.new(slot)
    for (path, idx), kfs in channels.items():
        fc = cb.fcurves.new(path, index=idx)
        for fr, v in kfs:
            kp = fc.keyframe_points.insert(fr, v)
            kp.interpolation = "BEZIER"
        fc.update()
    return act


def pb(bone, prop):
    return f'pose.bones["{bone}"].{prop}'


def qkeys(bone, keys):
    """keys: [(frame, axis(x,y,z), angle)] -> 4 channels quaternion"""
    ch = {}
    for fr, ax, ang in keys:
        q = Quaternion(Vector(ax), ang)
        for i in range(4):
            ch.setdefault((pb(bone, "rotation_quaternion"), i), []).append((fr, q[i]))
    return ch


def merge(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out.setdefault(k, []).extend(v)
    return out


# seated on a bench: hips down/back, feet forward, slight lean back
A_SIT = make_action("P_Sit", merge(
    {(pb("Body", "location"), 1): [(0, -0.215), (10, -0.215)], (pb("Body", "location"), 2): [(0, -0.03), (10, -0.03)],
     (pb("Foot.L", "location"), 1): [(0, 0.2), (10, 0.2)], (pb("Foot.R", "location"), 1): [(0, 0.2), (10, 0.2)]},
    qkeys("Torso", [(0, (1, 0, 0), -0.08), (10, (1, 0, 0), -0.08)]),
    qkeys("UpperArm.L", [(0, (1, 0, 0), 0.0), (10, (1, 0, 0), 0.0)])))
# sitting on the floor against the door
A_FLOOR = make_action("P_Floor", merge(
    {(pb("Body", "location"), 1): [(0, -0.42), (10, -0.42)], (pb("Body", "location"), 2): [(0, 0.06), (10, 0.06)],
     (pb("Foot.L", "location"), 1): [(0, 0.38), (10, 0.38)], (pb("Foot.R", "location"), 1): [(0, 0.33), (10, 0.33)],
     (pb("Foot.L", "location"), 0): [(0, 0.05), (10, 0.05)]},
    qkeys("Torso", [(0, (1, 0, 0), -0.15), (10, (1, 0, 0), -0.15)]),
    qkeys("Head", [(0, (1, 0, 0), 0.25), (10, (1, 0, 0), 0.25)])))
# head looks left then right (scene 3)
A_LOOK = make_action("P_LookLR", qkeys("Head", [(0, (0, 1, 0), 0), (24, (0, 1, 0), 0.75), (60, (0, 1, 0), 0.75),
                                               (90, (0, 1, 0), -0.75), (130, (0, 1, 0), -0.75), (160, (0, 1, 0), 0)]))
# turn toward the trees behind (scene 3)
A_BACK = make_action("P_LookBack", merge(qkeys("Head", [(0, (0, 1, 0), 0), (40, (0, 1, 0), 0.9), (200, (0, 1, 0), 0.9)]),
                                         qkeys("Torso", [(0, (0, 1, 0), 0), (40, (0, 1, 0), 0.45), (200, (0, 1, 0), 0.45)])))
# talking nods
A_TALK = make_action("P_Talk", qkeys("Head", [(0, (1, 0, 0), 0), (8, (1, 0, 0), 0.12), (16, (1, 0, 0), -0.04),
                                             (24, (1, 0, 0), 0.1), (32, (1, 0, 0), 0)]))
# look around the room
A_AROUND = make_action("P_Around", qkeys("Head", [(0, (0, 1, 0), 0), (30, (0, 1, 0), 0.8), (70, (0, 1, 0), 0.8),
                                                  (100, (0, 1, 0), -0.7), (140, (0, 1, 0), -0.7), (170, (0, 1, 0), 0)]))
# reach toward the radio
A_REACH = make_action("P_Reach", merge(qkeys("UpperArm.L", [(0, (0, 0, 1), 0), (12, (0, 0, 1), 0.9), (30, (0, 0, 1), 0.9), (44, (0, 0, 1), 0)]),
                                       qkeys("Torso", [(0, (0, 1, 0), 0), (12, (0, 1, 0), -0.3), (30, (0, 1, 0), -0.3), (44, (0, 1, 0), 0)])))

maya_arm0, maya_meshes, maya_acts = load_char("Characters_Lis")
ZTYPES = []
for fn in ("Zombie_Basic", "Zombie_Chubby", "Zombie_Arm"):
    ZTYPES.append(load_char(fn))
KIT_ACTIONS = set(bpy.data.actions)

maya = Rig("Maya", maya_arm0, maya_meshes, maya_acts)


def pose(rig, tr, act, t0, t1, bin_=0.4, bout=0.4, speed=1.0):
    st = add_strip(rig.track(tr), act, t0, t1, speed=speed, blend="COMBINE", bin_=bin_, bout=bout)
    return st


# ------------------------------------------------------------------ MAYA performance
MSX, MSY = BX, BY - 0.08   # seated root position
mp = [
    P(30.0, 24.0, -15.0, "Walk"), P(38.5, 21.0, -6.5, "Walk"), P(47.5, 12.5, -3.4, "Walk"),
    P(51.3, MSX, MSY - 0.45, "Idle", face=0.0, turn=0.8), P(52.4, MSX, MSY, "Idle", face=0.0),
    # seated 52.4 - 154 ; stands up and steps forward
    P(154.2, MSX, MSY, "Idle", face=0.0), P(155.6, MSX, MSY - 0.45, "Idle", face=0.0),
    P(169.0, MSX, MSY - 0.45, "Idle", face=0.0), P(170.5, MSX, MSY - 0.45, "Idle", face=(4, 8)),
    # chase
    P(180.0, MSX, MSY - 0.5, "Run", sp=1.0), P(182.6, 1.5, -7.4, "Run"), P(183.9, -2.6, -9.8, "Jump", sp=0.9),
    P(184.45, -4.0, -10.2, "Jump", z=0.75, jump=True), P(185.0, -5.4, -10.6, "Run"), P(187.0, -11.0, -12.4, "Duck", sp=2.2),
    P(188.4, -15.5, -12.5, "Run"), P(191.4, DOORS["d1"][0] + 0.55, DOORS["d1"][1], "Punch", face=(-40, DOORS["d1"][1]), sp=0.8),
    P(194.0, DOORS["d1"][0] + 0.55, DOORS["d1"][1], "No", face=(-40, DOORS["d1"][1])),
    P(195.6, DOORS["d1"][0] + 0.7, DOORS["d1"][1] - 0.2, "Run"),
    P(198.0, DOORS["d2"][0] + 0.55, DOORS["d2"][1], "Punch", face=(-40, DOORS["d2"][1]), sp=0.8),
    P(201.4, DOORS["d2"][0] + 0.55, DOORS["d2"][1], "No", face=(-40, DOORS["d2"][1])),
    P(203.0, DOORS["d2"][0] + 0.8, DOORS["d2"][1] - 0.5, "Run"), P(205.0, -21.5, -6.0, "Run"),
    P(208.6, -20.0, -16.0, "Run"), P(209.6, -18.0, -18.5, "Run"), P(211.2, -15.5, -22.0, "Idle", face=(-6, -20)),
    P(216.0, -15.5, -22.0, "Run", face=None), P(218.8, -12.0, SY + 0.75, "Idle", face=(-12, -60)),
    P(220.3, -12.0, SY + 0.75, "Walk"), P(221.6, -12.0, SY - 1.2, "Walk"),
]
route(maya, mp, end_t=222.4)
# interior (scene 7) - room at x=200
IX = 200.0
mp2 = [P(240.0, IX - 3.55, 0.0, "Idle", face=(IX + 10, 0.0)), P(270.0 - E, IX - 3.55, 0.0, "Idle")]
route(maya, mp2, end_t=270.0)
# courtyard (scenes 8-9)
mp3 = [P(270.0, -12.0, SY - 0.6, "Idle", face=(-12, 0)), P(271.2, -12.0, SY - 0.6, "Walk"),
       P(274.2, -12.0, -24.6, "Idle", face=(-12, 0)), P(281.6, -12.0, -24.6, "Idle", face=(-12, 0)),
       P(282.0, -12.0, -24.6, "Idle", face=(-12, -60), turn=1.4), P(290.6, -12.0, -24.6, "Wave", face=(-12, -60)),
       P(295.6, -12.0, -24.6, "Idle", face=(-12, -60)), P(303.0, -12.0, -24.6, "Wave", face=(-12, -60)),
       P(308.0, -12.0, -24.6, "Idle", face=(-12, -60))]
route(maya, mp3, end_t=320.0)
# Maya's gaps: off-screen while inside the building (222.4-240)
arm = maya.arm
K(arm, "location", OFF, frame=1)
K(arm, "location", OFF, t=30 - E)
K(arm, "location", OFF, t=222.4)
K(arm, "location", OFF, t=240 - E)
K(arm, "location", OFF, t=320.0)
merged = []
for s in sorted(maya.segs):
    if merged and merged[-1][2] == s[2] and merged[-1][3] == s[3] and abs(merged[-1][1] - s[0]) < 1e-6:
        merged[-1] = (merged[-1][0], s[1], s[2], s[3])
    else:
        merged.append(s)
for i, (t0, t1, a, sp) in enumerate(merged):
    if f(t1) - f(t0) >= 1:
        add_strip(maya.base, maya.acts[a], t0, t1, speed=sp, first=(i == 0))
# pose layers
pose(maya, 0, A_SIT, 51.8, 155.0, bin_=0.9, bout=1.0)
pose(maya, 0, A_FLOOR, 241.0, 270.0 - E, bin_=2.2, bout=0.0)
pose(maya, 1, A_TALK, 62.8, 67.0)
pose(maya, 1, A_LOOK, 74.5, 81.2, bin_=0.0, bout=0.0)
pose(maya, 1, A_BACK, 94.0, 110.0, bin_=0.0, bout=0.6)
pose(maya, 1, A_REACH, 164.6, 166.6, bin_=0.0, bout=0.0)
pose(maya, 1, A_TALK, 156.4, 158.8, speed=1.5)
pose(maya, 1, A_TALK, 258.6, 261.2, speed=0.7)
pose(maya, 1, A_AROUND, 262.0, 269.0, bin_=0.0, bout=0.0)
pose(maya, 1, A_TALK, 284.0, 289.6)
# carried bag (shoulder) while walking in
bag_c = emp("BagCarried", (0, 0, 0))
mk("BagCBody", "cube", (0, 0, 0), (0.36, 0.16, 0.26), mat=m_bag, parent=bag_c)
bag_c.parent = maya.arm
bag_c.parent_type = "BONE"
bag_c.parent_bone = "Torso"
bag_c.location = (0.22, -0.05, 0.12)
vis(bag_c, [(0, 52.8)])

# ------------------------------------------------------------------ ZOMBIES
FALLBACK = {"Idle_Attack": ("Punch", "Idle"), "Crawl": ("Walk",), "Punch": ("Idle",)}
for _a, _m, _acts in ZTYPES:
    print("ZACTS", sorted(_acts))
zombies = []
for i in range(30):
    arm0, meshes, acts = ZTYPES[i % 3]
    z = Rig(f"Zombie{i:02d}", arm0, meshes, acts)
    zombies.append(z)
MAYA_BENCH = (MSX, MSY - 0.45)


def ring(center, r, a0, a1, n):
    out = []
    for k in range(n):
        a = a0 + (a1 - a0) * (k / max(1, n - 1))
        out.append((center[0] + r * math.sin(a), center[1] + r * math.cos(a)))
    return out


routes = {}
# Group A: out of the arch (0-5)
for k in range(6):
    z = zombies[k]
    x0 = random.uniform(-1.2, 1.2)
    ts = 112.0 + k * 2.3 if k else 112.0
    y_mid = AY + 4.5 - 0.48 * (168 - ts)
    tgt = ring(MAYA_BENCH, 6.5, -0.9, 0.9, 6)[k]
    routes[k] = [P(ts, x0, AY + 5.2, "Walk", sp=0.8), P(168.0, x0 * 2.5, max(y_mid, 9.0), "Idle", face=MAYA_BENCH),
                 P(169.0, x0 * 2.5, max(y_mid, 9.0), "Walk", sp=0.8), P(180.0, *tgt, "Walk", sp=0.8)]
# Group B: rise from the garden (6-11)
for k in range(6):
    x, y = RISE[k]
    t0 = 137.0 + k * 0.6
    tgt = ring(MAYA_BENCH, 6.0, -1.9, -1.0, 6)[k]
    routes[6 + k] = [P(t0, x, y, "Crawl", z=-1.5, face=MAYA_BENCH, sp=0.9), P(t0 + 3.2, x, y, "Idle", z=0.0, face=MAYA_BENCH),
                     P(t0 + 4.4, x, y, "Walk", sp=0.75), P(168.0, x + 2.5, y - 2.0, "Idle", face=(30, -10)),
                     P(169.0, x + 2.5, y - 2.0, "Walk", sp=0.8), P(180.0, *tgt, "Walk", sp=0.8)]
# Group C: from behind the east trees (12-16)
for k in range(5):
    sx, sy = 21.0 + random.uniform(-1, 1), 4.0 + k * 2.2
    tgt = ring(MAYA_BENCH, 6.5, 1.0, 2.0, 5)[k]
    routes[12 + k] = [P(158.0 + k * 0.7, sx, sy, "Walk", sp=0.8), P(168.0, sx - 4.0, sy - 2.5, "Idle", face=(-20, sy)),
                      P(169.0, sx - 4.0, sy - 2.5, "Walk", sp=0.8), P(180.0, *tgt, "Walk", sp=0.8)]
# chase: groups A-C keep following toward the west doors
for k in range(17):
    last = routes[k][-1]["p"]
    goal = (DOORS["d1"][0] + 3 + random.uniform(-2, 2), random.uniform(-10, 4))
    routes[k].append(P(180.0 + 0.01, last[0], last[1], "Walk", sp=0.85))
    routes[k].append(P(222.0, goal[0] + (last[0] - goal[0]) * 0.35, goal[1] + (last[1] - goal[1]) * 0.35, "Walk", sp=0.85))
# Group D: spill out of the alley and from the north-west (17-22)
for k in range(6):
    sx, sy = WX - 4.5, 5.6 + random.uniform(-1.2, 1.2)
    routes[17 + k] = [P(196.0 + k * 0.9, sx, sy, "Walk", sp=0.9), P(200.0 + k * 0.9, WX + 2.5, sy - 0.5, "Walk", sp=0.9),
                      P(222.0, -20.0 + random.uniform(-1.5, 1.5), -12.0 - k * 0.8, "Walk", sp=0.9)]
# Group E: courtyard zombies (23-29) close in on the last door, then bang on it
DX, DY = DOORS["d3"]
for k in range(7):
    sx = 8.0 + k * 2.4
    sy = -21.5 - (k % 3) * 1.3
    doorpos = (DX - 1.6 + k * 0.55, DY + 1.1 + (k % 2) * 0.7)
    routes[23 + k] = [P(206.0, sx, sy, "Walk", sp=0.95), P(223.5 + k * 0.4, *doorpos, "Punch", face=(DX + (doorpos[0] - DX) * 0.3, DY - 5), sp=0.7),
                      P(240.0 - E, *doorpos, "Punch", face=(DX, DY - 5), sp=0.7)]
# scene 7: three of them outside the interior window
WIN = (IX + 1.0, 4.4)
for j, k in enumerate((23, 24, 25)):
    routes[k].append(P(240.0, WIN[0] - 1.4 + j * 1.4, WIN[1] + 0.4 + (j % 2) * 0.8, "Idle_Attack" if j != 1 else "Walk",
                       face=(WIN[0], -5), sp=0.6))
    routes[k].append(P(270.0 - E, WIN[0] - 1.4 + j * 1.4, WIN[1] + 0.4 + (j % 2) * 0.8, "Idle_Attack" if j != 1 else "Walk",
                       face=(WIN[0], -5), sp=0.6))
    routes[k][-1]["end"] = 270.0
# scenes 8-9: a crowd of 14 in an arc around Maya, then they close in
MC = (-12.0, -24.6)
arc_ids = list(range(0, 14))
for j, k in enumerate(arc_ids):
    a = -1.75 + 3.5 * j / (len(arc_ids) - 1)
    far = (MC[0] + 6.5 * math.sin(a), MC[1] + 6.5 * math.cos(a))
    near = (MC[0] + 3.2 * math.sin(a), MC[1] + 3.2 * math.cos(a))
    close = (MC[0] + 1.25 * math.sin(a), MC[1] + 1.25 * math.cos(a))
    seq = [P(270.0, *far, "Walk", sp=0.8), P(276.0 + random.uniform(-0.5, 0.5), *near, "Idle", face=MC),
           P(300.5 + random.uniform(0, 1.5), *near, "Walk", sp=0.7), P(311.0 + random.uniform(0, 2), *close, "Idle_Attack", face=MC, sp=0.8)]
    routes[k] += seq

for k, z in enumerate(zombies):
    pts = routes.get(k)
    if not pts:
        K(z.arm, "location", OFF, frame=1)
        continue
    # split into contiguous blocks separated by off-screen gaps
    blocks, cur = [], [pts[0]]
    for p_ in pts[1:]:
        jump_ = (Vector(p_["p"][:2]) - Vector(cur[-1]["p"][:2])).length
        if jump_ > 8.0 and p_["t"] - cur[-1]["t"] > 2.0:
            blocks.append(cur)
            cur = [p_]
        else:
            cur.append(p_)
    blocks.append(cur)
    first_t = pts[0]["t"]
    K(z.arm, "location", OFF, frame=1)
    for bi, blk_ in enumerate(blocks):
        end_t = blk_[-1].get("end", 240.0 if blk_[-1]["t"] < 240 else 320.0)
        if bi + 1 < len(blocks):
            end_t = min(end_t, blocks[bi + 1][0]["t"])
        if blk_[0]["t"] - E > 1 / FPS:
            K(z.arm, "location", OFF, t=blk_[0]["t"] - E)
        route(z, blk_, end_t=end_t)
        K(z.arm, "location", OFF, t=end_t)
    merged = []
    for s in sorted(z.segs):
        if merged and merged[-1][2] == s[2] and merged[-1][3] == s[3] and abs(merged[-1][1] - s[0]) < 1e-6:
            merged[-1] = (merged[-1][0], s[1], s[2], s[3])
        elif merged and s[0] < merged[-1][1]:
            continue
        else:
            merged.append(s)
    for i, (t0, t1, a, sp) in enumerate(merged):
        if f(t1) - f(t0) >= 1:
            act_ = None
            for cand in (a,) + FALLBACK.get(a, ()):
                if cand in z.acts:
                    act_ = z.acts[cand]
                    break
            add_strip(z.base, act_, t0, t1, speed=sp, first=(i == 0))

# ------------------------------------------------------------------ INTERIOR SET (x=200)
m_floorw = M_noise("int_floor", (0.3, 0.2, 0.12), (0.36, 0.25, 0.15), scale=4)
m_wall = M("int_wall", (0.62, 0.58, 0.5))
mk("IntFloor", "cube", (IX, 0, -0.05), (8, 6, 0.1), mat=m_floorw)
mk("IntCeil", "cube", (IX, 0, 3.25), (8, 6, 0.1), mat=m_wall)
mk("IntWallW", "cube", (IX - 4, 0, 1.6), (0.2, 6, 3.2), mat=m_wall)
mk("IntWallE", "cube", (IX + 4, 0, 1.6), (0.2, 6, 3.2), mat=m_wall)
mk("IntWallS", "cube", (IX, -3, 1.6), (8, 0.2, 3.2), mat=m_wall)
# north wall with a window opening (x IX+0.0..IX+2.0, z 1.0..2.3)
mk("IntWallN1", "cube", (IX - 2.0, 3, 1.6), (4.0, 0.2, 3.2), mat=m_wall)
mk("IntWallN2", "cube", (IX + 3.0, 3, 1.6), (2.0, 0.2, 3.2), mat=m_wall)
mk("IntWallN3", "cube", (IX + 1.0, 3, 0.5), (2.0, 0.2, 1.0), mat=m_wall)
mk("IntWallN4", "cube", (IX + 1.0, 3, 2.75), (2.0, 0.2, 0.9), mat=m_wall)
m_glass = M("glass", (0.6, 0.7, 0.75), rough=0.05)
try:
    bsdf(m_glass).inputs["Alpha"].default_value = 0.25
    m_glass.surface_render_method = "BLENDED"
except Exception:
    pass
mk("Glass", "cube", (IX + 1.0, 3.0, 1.65), (2.0, 0.02, 1.3), mat=m_glass)
mk("WinFrameH", "cube", (IX + 1.0, 2.98, 1.65), (2.0, 0.06, 0.06), mat=m_benchwood)
mk("WinFrameV", "cube", (IX + 1.0, 2.98, 1.65), (0.06, 0.06, 1.3), mat=m_benchwood)
cr2 = emp("WindowCrack", (IX + 0.6, 2.97, 1.8))
for k in range(9):
    a = k * 2 * pi / 9 + random.uniform(-0.2, 0.2)
    ln = random.uniform(0.25, 0.6)
    s_ = mk(f"WinCrack{k}", "cube", (math.cos(a) * ln / 2, 0, math.sin(a) * ln / 2), (ln, 0.005, 0.012),
            rot=(0, -a, 0), mat=M("crackwhite", (0.85, 0.9, 0.95), emit=0.5), parent=cr2)
vis(cr2, [(255.0, 330)])
mk("IntDoor", "cube", (IX - 3.88, 0, 1.05), (0.06, 1.15, 2.1), mat=m_doorwood)
mk("IntShelf", "cube", (IX + 3.6, -1.5, 0.9), (0.6, 2.0, 1.8), mat=m_benchwood)
mk("IntDesk", "cube", (IX + 1.5, -2.2, 0.4), (1.8, 0.9, 0.8), mat=m_benchwood)
mk("OutsideGround", "cube", (IX, 15, -0.06), (40, 24, 0.1), mat=m_court)
building("2Story_Wide", IX + 1.0, 14.0, "S", pal=PALETTE[3])
lamp = bpy.data.lights.new("IntLamp", "POINT")
lamp.energy = 70
lamp.color = (1.0, 0.8, 0.6)
lo = bpy.data.objects.new("IntLamp", lamp)
COL.objects.link(lo)
lo.location = (IX - 1.0, -1.0, 2.8)
lamp2 = bpy.data.lights.new("WindowLight", "AREA")
lamp2.energy = 120
lamp2.size = 2.0
lamp2.color = (0.7, 0.75, 0.9)
lo2 = bpy.data.objects.new("WindowLight", lamp2)
COL.objects.link(lo2)
lo2.location = (IX + 1.0, 3.6, 1.7)
lo2.rotation_euler = (pi / 2, 0, 0)

# ------------------------------------------------------------------ WORLD & SUN
world = bpy.data.worlds.new("Sky")
scene.world = world
if world.node_tree is None:
    world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange")
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
hor = nt.nodes.new("ShaderNodeRGB")
zen = nt.nodes.new("ShaderNodeRGB")
mr.inputs["From Min"].default_value = -0.02
mr.inputs["From Max"].default_value = 0.6
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
mixA = [s for s in mix.inputs if s.name == "A" and s.type == "RGBA"][0]
mixB = [s for s in mix.inputs if s.name == "B" and s.type == "RGBA"][0]
mixO = [s for s in mix.outputs if s.type == "RGBA"][0]
nt.links.new(mr.outputs["Result"], mix.inputs[0])
nt.links.new(hor.outputs[0], mixA)
nt.links.new(zen.outputs[0], mixB)
nt.links.new(mixO, bg.inputs["Color"])
nt.links.new(bg.outputs[0], out.inputs[0])
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.angle = 0.05
sun = bpy.data.objects.new("Sun", sun_d)
COL.objects.link(sun)
sun.rotation_mode = "QUATERNION"

LIGHT = [  # t, cut?, horizon, zenith, world strength, sun dir, sun energy, sun color
    (0, True, (1.0, 0.62, 0.38), (0.2, 0.28, 0.5), 0.9, (-0.7, 0.5, -0.25), 2.0, (1, 0.62, 0.38)),
    (30, False, (1.0, 0.85, 0.65), (0.3, 0.48, 0.8), 1.0, (-0.6, 0.55, -0.45), 3.4, (1, 0.88, 0.7)),
    (110, False, (0.95, 0.88, 0.75), (0.32, 0.48, 0.75), 1.0, (-0.55, 0.55, -0.5), 3.6, (1, 0.93, 0.82)),
    (150, False, (0.7, 0.68, 0.66), (0.3, 0.34, 0.42), 0.8, (-0.55, 0.55, -0.5), 2.2, (0.9, 0.9, 0.95)),
    (222, False, (0.55, 0.53, 0.52), (0.22, 0.24, 0.3), 0.7, (-0.5, 0.55, -0.55), 1.6, (0.85, 0.88, 0.95)),
    (240, True, (0.3, 0.3, 0.34), (0.12, 0.13, 0.17), 0.35, (-0.5, 0.55, -0.55), 0.6, (0.75, 0.8, 0.95)),
    (270, True, (0.52, 0.5, 0.5), (0.2, 0.22, 0.28), 0.65, (-0.5, -0.55, -0.55), 1.4, (0.85, 0.85, 0.95)),
    (325, False, (0.4, 0.4, 0.42), (0.15, 0.16, 0.2), 0.5, (-0.5, -0.55, -0.55), 0.9, (0.85, 0.85, 0.95)),
]
prevq = [None]


def sunq(d):
    q = Vector(d).normalized().to_track_quat("-Z", "Y")
    if prevq[0] is not None and prevq[0].dot(q) < 0:
        q.negate()
    prevq[0] = q
    return q


def setl(fr, e):
    _, _, h, z_, ws, sd, se, sc = e
    K(hor.outputs[0], "default_value", (*h, 1), frame=fr)
    K(zen.outputs[0], "default_value", (*z_, 1), frame=fr)
    K(bg.inputs["Strength"], "default_value", ws, frame=fr)
    K(sun, "rotation_quaternion", sunq(sd), frame=fr)
    K(sun_d, "energy", se, frame=fr)
    K(sun_d, "color", Vector(sc), frame=fr)


prev = None
for e in LIGHT:
    if e[1] and prev is not None:
        setl(f(e[0]) - 1, prev)
    setl(f(e[0]), e)
    prev = e

# ------------------------------------------------------------------ CAMERA
cam_d = bpy.data.cameras.new("Cam")
cam_d.clip_start = 0.05
cam_d.clip_end = 600
camroot = emp("CamRoot")
camroot.rotation_mode = "QUATERNION"
cam = bpy.data.objects.new("Camera", cam_d)
COL.objects.link(cam)
cam.parent = camroot
scene.camera = cam
D(cam, "location", f"0.03*(sin(frame*0.9)+0.5*sin(frame*2.3))*{W(180, 223)}", 0)
D(cam, "location", f"0.025*(sin(frame*1.1+1)+0.5*sin(frame*2.9))*{W(180, 223)}", 1)
camq = [None]


def camkey(t, loc, tgt, lens):
    q = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y")
    if camq[0] is not None and camq[0].dot(q) < 0:
        q.negate()
    camq[0] = q
    K(camroot, "location", Vector(loc), t=t)
    K(camroot, "rotation_quaternion", q, t=t)
    K(cam_d, "lens", lens, t=t)


d1x, d1y = DOORS["d1"]
d2x, d2y = DOORS["d2"]
SH = [
    # scene 1: aerial drift
    (0, 30, (-38, -52, 30), (0, 8, 0), 26, (22, -50, 24), (4, 10, 0), 26),
    # scene 2: Maya walks in
    (30, 38.5, (17.5, -19, 1.9), (24, -15, 1.0), 32, (17.5, -16, 1.9), (21, -6.5, 1.0), 32),
    (38.5, 46.5, (18.5, -10.5, 1.4), (20.5, -6.5, 1.0), 34, (13.5, -8.0, 1.4), (13.5, -3.5, 1.0), 34),
    (46.5, 53.0, (5.0, -7.5, 1.4), (11.5, -3.2, 0.9), 34, (5.5, -7.5, 1.4), (BX, BY, 0.7), 34),
    (53.0, 62.0, (BX, BY - 4.6, 1.0), (BX, BY, 0.6), 34, (BX, BY - 4.2, 1.0), (BX, BY, 0.62), 34),
    (62.0, 70.0, (BX - 0.2, BY - 2.6, 0.9), (BX + 0.1, BY, 0.75), 38, None, None, None),
    # scene 3: strange sound
    (70.0, 74.5, (BX - 3.5, BY - 6.5, 1.0), (BX - 0.2, BY - 1.5, 1.4), 26, (BX - 3.5, BY - 6.5, 1.0), (BX, BY - 4, 3.5), 26),
    (74.5, 84.0, (BX, BY - 2.6, 0.95), (BX, BY, 0.85), 30, None, None, None),
    (84.0, 92.0, (BX + 1.0, BY - 1.0, 0.55), (BX + 0.62, BY - 0.05, 0.42), 45, (BX + 0.9, BY - 0.85, 0.5), (BX + 0.62, BY - 0.05, 0.42), 45),
    (92.0, 100.0, (BX - 0.3, BY + 1.0, 1.05), (BX - 6, BY + 12, 1.6), 30, (BX - 0.2, BY + 1.1, 1.05), (BX - 7, BY + 13, 1.8), 30),
    (100.0, 110.0, (BX + 0.4, BY - 2.4, 0.9), (BX, BY, 0.9), 40, None, None, None),
    # scene 4: zombies emerge
    (110.0, 117.0, (0.0, 7.0, 2.2), (0.0, AY + 3, 2.6), 30, (0.0, 9.0, 2.0), (0.0, AY + 3, 2.4), 30),
    (117.0, 123.0, (1.0, AY - 3.6, 0.28), (0.0, AY - 0.5, 0.25), 32, None, None, None),
    (123.0, 132.0, (5.0, 10.0, 1.6), (0.0, AY - 1.0, 1.4), 30, (4.0, 11.0, 1.6), (0.0, AY - 3.0, 1.3), 30),
    (132.0, 137.0, (-8.0, -1.5, 1.2), (-9.5, 6.0, 0.0), 30, None, None, None),
    (137.0, 146.0, (-6.5, -0.5, 1.0), (-9.0, 6.0, 0.5), 32, (-6.5, 0.5, 1.0), (-9.0, 6.0, 0.6), 34),
    (146.0, 150.0, (BX + 1.0, BY - 1.0, 0.55), (BX + 0.62, BY - 0.05, 0.42), 45, None, None, None),
    # scene 5: realisation
    (150.0, 154.0, (BX, BY - 2.0, 0.95), (BX, BY, 0.95), 36, None, None, None),
    (154.0, 159.0, (BX - 0.6, BY - 4.5, 1.0), (BX, BY - 0.4, 0.8), 32, None, None, None),
    (159.0, 166.0, (BX + 1.0, BY - 1.0, 0.55), (BX + 0.62, BY - 0.05, 0.42), 45, None, None, None),
    (166.0, 169.0, (BX + 1.6, BY - 1.8, 1.1), (BX + 0.4, BY - 0.3, 0.6), 32, None, None, None),
    (169.0, 174.0, (BX + 1.5, BY - 3.5, 2.2), (BX - 4, BY + 8, 1.0), 24, None, None, None),
    (174.0, 180.0, (BX + 9, BY - 12, 8.0), (BX - 1, BY + 2, 0.0), 26, (BX + 10, BY - 11, 7.0), (BX - 1, BY + 2, 0.0), 26),
    # scene 6: the chase (quick cuts)
    (180.0, 183.0, (BX + 1.5, BY - 6.5, 1.3), (BX - 1, BY - 3, 0.9), 30, (3.5, -12.0, 1.3), (1.5, -7.5, 0.9), 30),
    (183.0, 185.2, (-3.6, -15.0, 0.9), (-3.8, -10.2, 0.8), 30, None, None, None),
    (185.2, 187.0, (-6.0, -14.6, 0.3), (-7.0, -11.6, 0.2), 30, (-10.0, -14.6, 0.3), (-10.8, -12.3, 0.2), 30),
    (187.0, 188.8, (-14.6, -17.0, 1.0), (-14.0, -12.4, 1.0), 30, None, None, None),
    (188.8, 191.4, (-11.0, 0.0, 0.3), (-11.0, 4.0, 0.25), 30, None, None, None),
    (191.4, 195.6, (d1x + 4.5, d1y - 2.5, 1.4), (d1x, d1y, 1.1), 32, None, None, None),
    (195.6, 198.0, (d1x + 4.5, d1y + 0.5, 1.2), (d1x + 0.8, d1y + 2, 0.9), 30, (d1x + 4.5, d2y - 1.5, 1.2), (d2x + 0.8, d2y, 0.9), 30),
    (198.0, 203.0, (d2x + 4.2, d2y + 2.2, 1.4), (d2x, d2y, 1.1), 32, None, None, None),
    (203.0, 205.0, (-15.0, 9.5, 2.4), (WX + 1.0, 4.5, 1.0), 26, None, None, None),
    (205.0, 208.6, (-16.5, -4.5, 1.4), (-21.5, -6.5, 1.2), 28, (-16.5, -14.5, 1.4), (-20.5, -16.5, 1.2), 28),
    (208.6, 211.2, (-14.5, -15.5, 1.2), (-18.0, -18.5, 0.8), 28, (-14.5, -15.5, 1.2), (-15.8, -21.5, 0.8), 28),
    (211.2, 216.0, (-14.6, -25.2, 1.2), (-15.5, -22.0, 0.95), 28, None, None, None),
    (216.0, 218.8, (-9.0, -20.0, 1.8), (-2.0, -24.0, 0.9), 28, None, None, None),
    (218.8, 223.0, (-9.0, -22.8, 1.5), (DX, DY + 0.3, 1.2), 30, None, None, None),
    (223.0, 232.0, (-8.0, -20.5, 2.0), (DX, DY + 0.8, 1.1), 26, None, None, None),
    (232.0, 240.0, (-3.0, -12.0, 9.0), (-11.0, -25.0, 0.0), 28, (-4.0, -13.0, 10.0), (-11.0, -25.0, 0.0), 28),
    # scene 7: interior
    (240.0, 252.0, (IX + 1.4, -1.6, 1.1), (IX - 3.5, 0.0, 0.7), 30, (IX + 0.8, -1.3, 1.0), (IX - 3.5, 0.0, 0.6), 32),
    (252.0, 258.0, (IX - 0.6, -1.2, 1.15), (IX + 1.0, 3.0, 1.5), 30, (IX - 0.3, -0.6, 1.2), (IX + 1.0, 3.0, 1.6), 34),
    (258.0, 264.0, (IX - 1.9, -0.5, 0.7), (IX - 3.5, 0.0, 0.55), 32, None, None, None),
    (264.0, 270.0, (IX + 2.8, -2.4, 1.7), (IX - 3.2, 0.2, 0.5), 26, None, None, None),
    # scene 8: last scene
    (270.0, 276.0, (-6.0, -24.0, 1.4), (-12.0, -25.5, 1.0), 30, None, None, None),
    (276.0, 282.0, (-12.4, -26.2, 1.3), (-12.0, -20.0, 1.0), 30, None, None, None),
    (282.0, 300.0, (-12.0, -26.4, 1.0), (-12.0, -24.6, 1.05), 34, (-12.0, -26.5, 1.0), (-12.0, -24.6, 1.05), 36),
    # scene 9: pull back and up
    (300.0, 320.0, (-12.0, -26.4, 2.0), (-12.0, -24.6, 1.0), 34, (-12.0, -42.0, 30.0), (-12.0, -22.0, 0.0), 30),
    (320.0, 330.0, (-12.0, -42.0, 30.0), (-12.0, -22.0, 0.0), 30, None, None, None),
]
for t0, t1, l0, g0, n0, l1, g1, n1 in SH:
    camkey(t0, l0, g0, n0)
    camkey(t1 - E, l1 or l0, g1 or g0, n1 or n0)

# ------------------------------------------------------------------ interpolation for my own keys
for a in bpy.data.actions:
    if a in KIT_ACTIONS or a.name.startswith("P_"):
        continue
    for layer in a.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "hide_render":
                        continue
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
                    fc.update()

# ------------------------------------------------------------------ render settings
r = scene.render
r.engine = "BLENDER_EEVEE"
r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
ee = scene.eevee
ee.taa_render_samples = 6
ee.use_shadows = True
ee.shadow_ray_count = 1
ee.shadow_step_count = 4
ee.use_raytracing = False
r.image_settings.media_type = "IMAGE"
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.compression = 15
r.filepath = "//frames/f_"
r.use_overwrite = False
r.use_placeholder = True
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "TheZombieApocalypse.blend"))
print("BUILD OK", len(bpy.data.objects))
