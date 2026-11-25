# Final edit for THE ZOMBIE APOCALYPSE: frames + title + subtitles + credits + soundtrack -> MP4
#   blender -b --factory-startup --python assemble.py [-- still <frame>]
import bpy, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(DIR, "frames")
FPS = 24
TOTAL = 7920


def f(t):
    return int(round(t * FPS)) + 1


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Final"
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, TOTAL
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.view_settings.view_transform = "Standard"
se = sc.sequence_editor_create()

files = sorted(x for x in os.listdir(FR) if x.endswith(".png"))
img = se.strips.new_image("Film", os.path.join(FR, files[0]), 1, 1)
for fn in files[1:]:
    img.elements.append(fn)


def key(strip, prop, t, v):
    setattr(strip, prop, v)
    strip.keyframe_insert(prop, frame=f(t) if isinstance(t, float) else t)


black = se.strips.new_effect("Black", "COLOR", 2, 1, length=TOTAL)
black.color = (0, 0, 0)
black.blend_type = "ALPHA_OVER"
key(black, "blend_alpha", 1, 1.0)
key(black, "blend_alpha", 0.5, 1.0)
key(black, "blend_alpha", 4.0, 0.0)
key(black, "blend_alpha", 316.0, 0.0)
key(black, "blend_alpha", 320.0, 1.0)

FONT = None
for fp in (r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\arial.ttf"):
    if os.path.exists(fp):
        FONT = bpy.data.fonts.load(fp)
        break
FONTB = None
for fp in (r"C:\Windows\Fonts\impact.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
    if os.path.exists(fp):
        FONTB = bpy.data.fonts.load(fp)
        break


def text(name, body, t0, t1, ch, size, y, fade=0.4, color=(1, 1, 1, 1), font=None, y_end=None):
    s = se.strips.new_effect(name, "TEXT", ch, f(t0), length=f(t1) - f(t0))
    s.text = body
    s.font_size = size
    s.location = (0.5, y)
    s.color = color
    if font or FONT:
        s.font = font or FONT
    for prop, val in (("use_shadow", True), ("anchor_x", "CENTER"), ("anchor_y", "CENTER"),
                      ("alignment_x", "CENTER"), ("wrap_width", 0.9)):
        try:
            setattr(s, prop, val)
        except Exception:
            pass
    s.blend_type = "ALPHA_OVER"
    key(s, "blend_alpha", float(t0), 0.0)
    key(s, "blend_alpha", float(t0 + fade), 1.0)
    key(s, "blend_alpha", float(t1 - fade), 1.0)
    key(s, "blend_alpha", float(t1) - 1 / FPS, 0.0)
    if y_end is not None:
        s.location = (0.5, y)
        s.keyframe_insert("location", frame=f(t0))
        s.location = (0.5, y_end)
        s.keyframe_insert("location", frame=f(t1) - 1)
    return s


# title
text("Title", "THE ZOMBIE APOCALYPSE", 5.0, 15.0, 3, 84, 0.58, fade=1.5, color=(0.85, 0.08, 0.06, 1), font=FONTB)
# subtitles (dialogue)
SUBS = [
    (56.5, 63.4, "RADIO: ...and that's the weather. Clear skies all week. Stay safe out there, folks."),
    (64.0, 69.8, "MAYA: Stay safe. From what? Nothing ever happens here."),
    (156.4, 159.5, "MAYA: No. No, no, no..."),
    (159.6, 164.0, "RADIO: ...do not go outside... repeat... do not..."),
    (198.6, 201.6, "MAYA: Open, please, anyone, open the door!"),
    (212.5, 215.4, "MAYA: Think. Think..."),
    (258.8, 262.0, "MAYA (whispering): I thought we had more time."),
    (284.0, 290.8, "MAYA: If you're watching this... be careful. Always listen to the warnings."),
    (293.8, 295.6, "MAYA: Bye."),
    (307.0, 309.4, "MAYA (V.O.): Goodbye."),
]
for i, (a, b, tx) in enumerate(SUBS):
    text(f"Sub{i}", tx, a, b, 4 + (i % 2), 26, 0.07, fade=0.15)
# end card and credits
text("TheEnd", "THE END", 320.2, 323.8, 6, 90, 0.5, fade=0.6, color=(0.85, 0.08, 0.06, 1), font=FONTB)
CREDITS = ("THE ZOMBIE APOCALYPSE\nComputer Graphics Group Project\n\n"
           "SEKANDI CLIVE\nGLEN MUSILA\nLENNY MWAURA\nTHEURI MATTHEW\nGABRIEL KIBET\n\n"
           "Characters, zombies and buildings: Quaternius (CC0)\n"
           "Voices: Microsoft Windows text-to-speech\n"
           "Music and sound effects: generated procedurally")
text("Credits", CREDITS, 323.6, 330.0, 7, 24, 0.32, fade=0.5, y_end=0.68)

se.strips.new_sound("Soundtrack", os.path.join(DIR, "soundtrack.wav"), 8, 1)

r = sc.render
if "still" in sys.argv:
    fr = int(sys.argv[-1])
    sc.frame_set(fr)
    r.image_settings.media_type = "IMAGE"
    r.image_settings.file_format = "PNG"
    r.filepath = os.path.join(DIR, "test", f"final_{fr}.png")
    bpy.ops.render.render(write_still=True)
else:
    r.image_settings.media_type = "VIDEO"
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.ffmpeg.audio_codec = "AAC"
    r.ffmpeg.audio_bitrate = 192
    r.ffmpeg.audio_channels = "STEREO"
    r.ffmpeg.audio_mixrate = 44100
    r.filepath = os.path.join(DIR, "The_Zombie_Apocalypse.mp4")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DIR, "Final_Edit.blend"))
    bpy.ops.render.render(animation=True)
    print("VIDEO OK", r.filepath)
