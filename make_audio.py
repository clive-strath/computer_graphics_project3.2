# Soundtrack for THE ZOMBIE APOCALYPSE (330 s): procedural SFX + music + TTS dialogue
#   blender -b --factory-startup --python make_audio.py
import numpy as np, wave, os

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
DUR = 330.0
N = int(SR * DUR)
rng = np.random.default_rng(5)
L = np.zeros(N)
R = np.zeros(N)


def tt(d):
    return np.arange(int(d * SR)) / SR


def add(sig, t0, vol=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or len(sig) == 0:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * vol * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * vol * (1 + min(0, pan))


def band(x, lo, hi):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(X, len(x))


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def noise(d):
    return rng.standard_normal(int(d * SR))


def norm(x):
    m = np.max(np.abs(x)) or 1
    return x / m


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad(midis, d, a=2.0, r=2.0, bright=3):
    t = tt(d)
    s = np.zeros(len(t))
    for m in midis:
        for det in (-0.12, 0.12):
            for h in range(1, bright + 1):
                s += np.sin(2 * np.pi * note(m) * h * t * (1 + det / 100) + h) / (h * h)
    return norm(s) * env(len(t), a, r)


def pluck(m, d=2.5, decay=2.5):
    t = tt(d)
    s = sum(np.sin(2 * np.pi * note(m) * h * t) * np.exp(-t * decay * h) / h for h in range(1, 6))
    return norm(s) * env(len(t), 0.004, 0.05)


def kick(fh=110, fl=42, d=0.5, dec=8):
    t = tt(d)
    f = fl + (fh - fl) * np.exp(-t * 20)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * dec)


def thud(d=0.5, lo=40, hi=400, dec=10):
    t = tt(d)
    return norm(band(noise(d), lo, hi)) * np.exp(-t * dec) * 0.8 + kick(90, 40, d, dec) * 0.6


def knock():
    t = tt(0.18)
    return norm(band(noise(0.18), 200, 2500)) * np.exp(-t * 40) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30) * 0.5


def step(hard=False):
    d = 0.12
    t = tt(d)
    return norm(band(noise(d), 120, 3000 if hard else 1500)) * np.exp(-t * (35 if hard else 45))


def birds(d, count):
    s = np.zeros(int(d * SR))
    for _ in range(count):
        t0 = rng.uniform(0, d - 1)
        for k in range(rng.integers(2, 5)):
            cd = rng.uniform(0.06, 0.14)
            t = tt(cd)
            fq = rng.uniform(2600, 4200) + rng.uniform(-1400, 1400) * t / cd
            c = np.sin(2 * np.pi * np.cumsum(fq) / SR) * np.sin(np.pi * t / cd)
            i = int((t0 + k * 0.17) * SR)
            s[i:i + len(c)] += c[: len(s) - i]
    return s


def wind(d, lo=60, hi=500):
    t = tt(d)
    return norm(band(noise(d), lo, hi)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + 1) * np.sin(2 * np.pi * 0.023 * t))


def static(d, density=1.0):
    n = noise(d)
    hiss = norm(band(n, 1500, 9000))
    crack = np.zeros(len(n))
    idx = rng.integers(0, max(1, len(n) - 300), int(d * 40 * density))
    for i in idx:
        ln = rng.integers(20, 200)
        crack[i:i + ln] += rng.standard_normal(ln) * rng.uniform(0.5, 1.5)
    return norm(hiss * 0.5 + crack * 0.5)


def groan(d=1.8, f0=None, dist=1.0):
    t = tt(d)
    f0 = f0 or rng.uniform(85, 140)
    fq = f0 * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(3, 6) * t) - 0.15 * t / d)
    ph = 2 * np.pi * np.cumsum(fq) / SR
    saw = sum(np.sin(h * ph) / h for h in range(1, 18))
    sig = band(saw + 0.3 * noise(d), 180, 1100 if dist > 0.5 else 600)
    sig = np.tanh(norm(sig) * 2.0)
    return norm(sig) * env(len(t), 0.35, 0.6) * (0.7 + 0.3 * np.sin(2 * np.pi * 1.7 * t))


def rumble(d):
    t = tt(d)
    return norm(band(noise(d), 18, 90)) * env(len(t), d * 0.4, d * 0.4)


def creak(d=0.9):
    t = tt(d)
    fq = 300 + 200 * np.sin(2 * np.pi * 1.5 * t)
    s = np.sin(2 * np.pi * np.cumsum(fq) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 40 * t)))
    return norm(band(s, 200, 3000)) * env(len(t), 0.05, 0.2)


def load_voice(name):
    with wave.open(os.path.join(HERE, "voices", name + ".wav")) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    return x


def radio_fx(x, staticky=0.25):
    y = band(x, 350, 3200)
    y = np.tanh(norm(y) * 2.5)
    st = static(len(y) / SR) * staticky
    if staticky > 0.4:  # drop-outs
        gate = (np.sin(2 * np.pi * 0.9 * tt(len(y) / SR)) > -0.35).astype(float)
        y = y * gate
    return norm(y * 0.8 + st)


def echo(x, delay=0.22, fb=0.35, n=4):
    out = np.concatenate([x, np.zeros(int(delay * SR * n))])
    for k in range(1, n + 1):
        i = int(delay * SR * k)
        out[i:i + len(x)] += x * (fb ** k)
    return out


# ---------------- scene 1-2: peaceful morning
add(pad([60, 64, 67], 72, a=5, r=4, bright=2), 0.5, 0.12)
add(wind(110), 0, 0.05)
add(birds(84, 70), 0, 0.05, pan=-0.3)
add(birds(84, 50), 0, 0.04, pan=0.35)
for k, m in enumerate([72, 74, 76, 79, 76, 74, 72, 67, 69, 72, 74, 72]):
    add(pluck(m, 2.4), 8 + k * 1.6, 0.08)
t_ = 30.0
k = 0
while t_ < 51.3:
    add(step(), t_, 0.18, pan=0.25 if k % 2 else -0.25)
    t_ += 0.52
    k += 1
add(thud(0.3, 60, 600, 18), 52.8, 0.25)
add(knock() * 0.5, 55.5, 0.3)
add(radio_fx(load_voice("R1"), 0.12), 56.5, 0.5, pan=0.3)
add(load_voice("M1"), 64.0, 0.85)
# ---------------- scene 3: strange sound
add(rumble(6), 69.5, 0.6)
for k in range(10):
    add(norm(band(noise(0.06), 200, 2500)) * np.exp(-tt(0.06) * 30), 70.6 + k * 0.11, 0.18)
add(pad([48, 51, 54], 42, a=8, r=2, bright=3), 76, 0.1)
add(static(26, 1.5), 84, 0.13, pan=0.3)
add(groan(2.4, 75, dist=0.3), 92.5, 0.25, pan=-0.6)
add(groan(2.0, 95, dist=0.3), 101, 0.18, pan=-0.4)
# ---------------- scene 4: zombies emerge
add(norm(band(noise(42), 25, 160)), 110, 0.15)
add(pad([36, 43, 46, 49], 42, a=3, r=2, bright=4), 110, 0.13)
for k in range(12):
    add(groan(rng.uniform(1.5, 2.6)), 112 + k * 3.1 + rng.uniform(0, 1.5), 0.3, pan=rng.uniform(-0.6, 0.6))
for k in range(9):  # dragging feet on stone
    d = 0.5
    add(norm(band(noise(d), 300, 4000)) * env(int(d * SR), 0.1, 0.3), 117.2 + k * 0.65, 0.22)
t = tt(3.5)
add(norm(band(noise(3.5), 40, 2500)) * np.exp(-t * 0.7) + rumble(3.5) * 0.8, 133.0, 0.5)
for k in range(8):
    add(norm(band(noise(0.8), 80, 900)) * env(int(0.8 * SR), 0.1, 0.4), 137 + k * 0.9, 0.2, pan=-0.4)
add(static(4, 2.0), 146, 0.35, pan=0.2)
# ---------------- scene 5: realisation
for k in range(12):
    add(kick(70, 40, 0.3, 12), 150 + k * 0.75, 0.35)
    add(kick(70, 40, 0.3, 12), 150.28 + k * 0.75, 0.22)
add(thud(0.4, 60, 800, 14), 155.8, 0.3)
add(load_voice("M2"), 156.4, 0.9)
add(radio_fx(load_voice("R2"), 0.6), 159.6, 0.55, pan=0.3)
add(static(6.0, 2.0), 159.4, 0.18, pan=0.3)
add(knock() * 0.8, 166.0, 0.45)
for k in range(6):
    add(groan(rng.uniform(1.4, 2.2)), 168.2 + rng.uniform(0, 0.3), 0.3, pan=rng.uniform(-0.8, 0.8))
for k in range(26):
    add(step(), 169 + k * 0.42 + rng.uniform(0, 0.2), 0.12, pan=rng.uniform(-0.8, 0.8))
add(pad([38, 45, 49], 12, a=4, r=0.3, bright=4), 168.5, 0.14)
# ---------------- scene 6: the chase (intense music)
bpm = 150
beat = 60 / bpm
tb = 180.0
k = 0
bass = [38, 38, 41, 38, 43, 41, 38, 36]
while tb < 223.0:
    add(kick(), tb, 0.5)
    if k % 2 == 1:
        add(norm(band(noise(0.2), 1000, 7000)) * np.exp(-tt(0.2) * 20), tb, 0.22)
    add(norm(band(noise(0.05), 6000, 12000)) * np.exp(-tt(0.05) * 60), tb + beat / 2, 0.1)
    m = bass[(k // 2) % 8]
    t = tt(beat * 0.9)
    add(np.tanh(np.sin(2 * np.pi * note(m) * t) * 3) * env(len(t), 0.005, 0.05), tb, 0.18)
    tb += beat
    k += 1
for c, t0 in (([50, 53, 57], 180), ([48, 52, 55], 188), ([46, 50, 53], 196), ([45, 49, 52], 204), ([50, 53, 57], 212)):
    t = tt(8.2)
    s = sum(sum(np.sin(2 * np.pi * note(mm) * h * t) / h for h in range(1, 7)) for mm in c)
    add(norm(s) * env(len(t), 0.3, 0.3), t0, 0.09)
t_ = 180.0
while t_ < 211.0:  # running footsteps
    add(step(True), t_, 0.16)
    t_ += 0.27
add(thud(0.35, 50, 900, 14), 184.95, 0.35)
for t0 in (191.6, 192.6, 193.6, 198.3, 199.2, 200.1):
    add(knock(), t0, 0.6)
    add(norm(band(noise(0.25), 400, 3000)) * np.exp(-tt(0.25) * 20), t0 + 0.05, 0.15)
add(load_voice("M3"), 198.6, 1.0)
for k in range(14):
    add(groan(rng.uniform(1.2, 2.0)), 186 + k * 2.6 + rng.uniform(0, 1), 0.2, pan=rng.uniform(-0.8, 0.8))
t = tt(4.8)
add(np.sin(2 * np.pi * 120 * t) * 0.3 + norm(band(noise(4.8), 100, 1500)) * 0.5 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.2 * t)), 211.3, 0.12)
add(load_voice("M4"), 212.5, 0.9)
add(creak(0.9), 219.4, 0.35)
add(thud(0.8, 40, 1500, 6), 222.85, 0.8)
# thuds on the wood from outside
for k in range(22):
    t0 = 224 + k * 0.75 + rng.uniform(0, 0.25)
    add(thud(0.45, 40, 600, 10), t0, 0.5)
add(pad([37, 44, 48], 18, a=1, r=3, bright=4), 223, 0.13)
for k in range(8):
    add(groan(rng.uniform(1.3, 2.0)), 224 + k * 2.0, 0.28, pan=rng.uniform(-0.6, 0.6))
# ---------------- scene 7: a moment of quiet (muffled)
for k in range(14):
    t0 = 240 + k * 0.9 + rng.uniform(0, 0.4)
    add(band(thud(0.4, 40, 300, 12), 30, 250) * 1.5, t0, 0.4)
for k in range(10):
    d = 1.1
    add(norm(band(noise(d), 300, 2500)) * np.sin(np.pi * tt(d) / d) ** 2, 240.5 + k * 1.3, 0.06)
t = tt(1.2)
add(norm(band(noise(1.2), 1500, 12000)) * np.exp(-t * 8) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 6) * 0.3, 255.0, 0.45)
add(load_voice("M5") * 0.6, 258.8, 0.8)
add(pad([45, 48, 52, 55], 16, a=4, r=2, bright=2), 256, 0.1)
add(norm(band(noise(30), 30, 200)), 240, 0.06)
# ---------------- scene 8-9: the last scene
add(creak(0.8), 270.3, 0.3)
for k in range(6):
    add(step(), 271.2 + k * 0.5, 0.15)
for k in range(10):
    add(groan(rng.uniform(1.6, 2.6), dist=0.4), 271 + k * 4.5 + rng.uniform(0, 2), 0.12, pan=rng.uniform(-0.7, 0.7))
sad = [69, 72, 76, 74, 72, 71, 69, 64, 65, 69, 72, 71, 69, 67, 64, 69, 72, 71, 69, 64, 65, 64]
for k, m in enumerate(sad):
    add(pluck(m, 3.0, 1.3), 276 + k * 1.9, 0.11)
for i, c in enumerate([[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56], [45, 52, 57, 60]]):
    add(pad(c, 9.0, a=2, r=2, bright=2), 276 + i * 8.6, 0.09)
add(load_voice("M6"), 284.0, 0.95)
add(load_voice("M7"), 293.8, 0.95)
add(echo(load_voice("M8"), 0.25, 0.4, 5), 307.0, 0.8)
for k in range(8):
    add(groan(rng.uniform(1.4, 2.2)), 301 + k * 1.4, 0.2, pan=rng.uniform(-0.6, 0.6))
# ---------------- scene 10: credits over radio static
add(static(10.5, 1.2) * env(int(10.5 * SR), 1.0, 3.0), 319.5, 0.2)

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix /= np.max(np.abs(mix)) / 0.9
fade = np.ones(N)
fade[-int(2.5 * SR):] = np.linspace(1, 0, int(2.5 * SR))
mix *= fade[:, None]
with wave.open(os.path.join(HERE, "soundtrack.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("AUDIO OK")
