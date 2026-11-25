p = r'C:/Users/clive/Downloads/TheZombieApocalypse/build_zombie.py'
s = open(p, encoding='utf-8').read()
rep = [
 ("(74.5, 84.0, (BX, BY - 2.2, 0.9), (BX, BY, 0.9), 42, None, None, None),", "(74.5, 84.0, (BX, BY - 2.6, 0.95), (BX, BY, 0.85), 30, None, None, None),"),
 ("(150.0, 154.0, (BX, BY - 1.5, 0.95), (BX, BY, 1.05), 50, None, None, None),", "(150.0, 154.0, (BX, BY - 2.0, 0.95), (BX, BY, 0.95), 36, None, None, None),"),
 ("(211.2, 216.0, (-15.0, -24.6, 1.1), (-15.5, -22.0, 1.15), 40, None, None, None),", "(211.2, 216.0, (-14.6, -25.2, 1.2), (-15.5, -22.0, 0.95), 28, None, None, None),"),
 ("(258.0, 264.0, (IX - 2.2, -0.35, 0.65), (IX - 3.5, 0.0, 0.6), 40, None, None, None),", "(258.0, 264.0, (IX - 1.9, -0.5, 0.7), (IX - 3.5, 0.0, 0.55), 32, None, None, None),"),
 ("lamp.energy = 25", "lamp.energy = 70"),
 ("ee.taa_render_samples = 8", "ee.taa_render_samples = 6"),
]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print("PATCHED")
