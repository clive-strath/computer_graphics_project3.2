p = r'C:/Users/clive/Downloads/TheZombieApocalypse/build_zombie.py'
s = open(p, encoding='utf-8').read()
old = "            add_strip(z.base, z.acts[a], t0, t1, speed=sp, first=(i == 0))"
new = """            act_ = None
            for cand in (a,) + FALLBACK.get(a, ()):
                if cand in z.acts:
                    act_ = z.acts[cand]
                    break
            add_strip(z.base, act_, t0, t1, speed=sp, first=(i == 0))"""
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("zombies = []\nfor i in range(30):", 'FALLBACK = {"Idle_Attack": ("Punch", "Idle"), "Crawl": ("Walk",), "Punch": ("Idle",)}\nfor _a, _m, _acts in ZTYPES:\n    print("ZACTS", sorted(_acts))\nzombies = []\nfor i in range(30):')
open(p, 'w', encoding='utf-8').write(s)
print("PATCHED")
