p = r'C:/Users/clive/Downloads/TheZombieApocalypse/build_zombie.py'
s = open(p, encoding='utf-8').read()
start = s.index('def relink_images(texdir):')
end = s.index('TREES = [(8.6, 1.6, "CommonTree_1", 0.75)]')
new = '''m_leafA = M("leafA", (0.16, 0.36, 0.1))
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


'''
s = s[:start] + new + s[end:]
s = s.replace('    place(n, x, y, s)\n', '    place(n, x, y, s * 1.6)\n')
open(p, 'w', encoding='utf-8').write(s)
print("PATCHED")
