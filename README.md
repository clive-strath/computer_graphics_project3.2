# The Zombie Apocalypse

**Computer Graphics Group Project:** a 5½-minute 3D animated short film. The whole film is built, animated, scored and edited **from Python scripts that drive Blender**.

|                |                                                                                         |
| -------------- | --------------------------------------------------------------------------------------- |
| **Team**       | Sekandi Clive · Glen Musila · Lenny Mwaura · Theuri Matthew · Gabriel Kibet             |
| **Repository** | https://github.com/clive-strath/computer_graphics_project3.2                            |
| **Tool chain** | Blender 5.3 (bpy / bmesh / mathutils), EEVEE renderer, NumPy, Windows Speech (TTS)      |
| **Output**     | `The_Zombie_Apocalypse.mp4`: 1280×720, 24 fps, 330 s (7,920 frames), H.264 + AAC stereo |

> **Note on OpenGL:** the course outline lists OpenGL for Checkpoint 3. As a group we decided to use **Blender** instead. Blender's viewport and its EEVEE renderer both run on OpenGL/GPU rasterisation, and its Python API let us apply the same concepts (primitives, meshes, transforms, hierarchies, animation and lighting) at the scale of a full film. Wherever the outline says "OpenGL", read it as "Blender / EEVEE" in this README.

![Contact sheet of the finished film](docs/images/contact_sheet.png)

---

## Story

Maya, a student, sits on a campus bench listening to the radio on a quiet morning. The weather report says *"Stay safe out there, folks."* A strange sound follows. Zombies shuffle out of the university arch and claw their way up from the garden, and the radio starts warning people not to go outside. Maya runs. She jumps a hedge, ducks under a branch and pounds on two locked doors. The third door opens. She hides inside while the zombies batter the walls and crack the window. When she steps back out into the courtyard, the horde surrounds her. Before the camera pulls away, she records a last message: *"Always listen to the warnings."*

| Scene | Time (s)  | Content                                                                    |
| ----- | --------- | -------------------------------------------------------------------------- |
| 1     | 0 – 30    | Aerial drift over the campus, title card                                   |
| 2     | 30 – 70   | Maya walks in, sits on the bench, radio weather report                     |
| 3     | 70 – 110  | The strange sound: pigeons scatter, Maya looks around                      |
| 4     | 110 – 150 | Zombies emerge from the arch, the ground cracks, more rise from the garden |
| 5     | 150 – 180 | Realisation: emergency broadcast, the radio dies, Maya is surrounded       |
| 6     | 180 – 240 | The chase: hedge jump, branch duck, two locked doors, the third door opens |
| 7     | 240 – 270 | Interior: Maya on the floor, zombies at the window, the glass cracks       |
| 8 – 9 | 270 – 320 | Courtyard: Maya surrounded, final message, camera cranes up and away       |
| 10    | 320 – 330 | "THE END" and credits over radio static                                    |

---

## Pipeline

```
build_zombie.py ──► TheZombieApocalypse.blend ──► render ──► frames/f_0001…f_7920.png ─┐
make_voices.ps1 ──► voices/*.wav ──► make_audio.py ──► soundtrack.wav ─────────────────┤
                                                                                        ▼
                                          assemble.py ──► Final_Edit.blend ──► The_Zombie_Apocalypse.mp4
```

| File                               | Purpose                                                                                                                                |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| [build_zombie.py](build_zombie.py) | Builds the entire 3D scene from code: ground, buildings, vegetation, props, characters, zombies, lighting, cameras and render settings |
| [make_voices.ps1](make_voices.ps1) | Generates the 10 dialogue lines with Windows text-to-speech                                                                            |
| [make_audio.py](make_audio.py)     | Synthesises the full soundtrack (music, SFX, ambience) with NumPy and mixes in the voices                                              |
| [assemble.py](assemble.py)         | Edits the final cut in Blender's Video Sequencer: frames, fades, title, subtitles, credits and soundtrack, exported to MP4             |
| [devtools.py](devtools.py)         | Test and inspection tools: test stills, side-angle pose checks, asset line-ups, rig and asset probes                                   |

---

## Checkpoint 1: Design & Foundations *(week of 2 Nov)*

### What are we building?
A short **3D animated horror film** set on a university campus. The project brief asks for graphics, animation, lighting and rendering. We chose to apply these to a complete narrative piece rather than a single demo scene: one hero character (Maya), 30 animated zombies, a campus environment, an interior set and a full soundtrack, with the whole build expressed as code so it can be reproduced.

### What graphics concepts will we use?
| Area                | Concepts                                                                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Modelling           | Geometric primitives (cube, cylinder/cone, icosphere), polygon meshes, Constructive Solid Geometry (Boolean difference), text / font curves                |
| Transformations     | Translation, rotation and scaling matrices, composite transforms (`T · R · S`), hierarchical (parent–child) transforms, Euler angles and quaternions       |
| Animation           | Keyframe interpolation (Bézier and linear), procedural animation with mathematical drivers, skeletal (armature) animation, animation blending and layering |
| Appearance          | Physically based materials (Principled BSDF), procedural noise textures, emission, transparency                                                            |
| Lighting            | Directional (sun), point and area lights, a gradient sky, a time-of-day lighting progression                                                               |
| Viewing & rendering | Virtual camera (position, look-at, focal length), a rasterised real-time renderer (EEVEE), shadows, anti-aliasing, tone mapping                            |
| Post / audio        | Video compositing with alpha blending and fades; digital signal processing for sound                                                                       |

### What have we completed?
- The story, scene breakdown and timing (the 10-scene table above).
- Choice of tools: Blender driven entirely by Python scripts, with CC0 assets from Quaternius for characters, zombies and buildings.
- Asset survey: probe tools in [devtools.py](devtools.py) (`probe_bld`, `probe_chars`, `probe_rig`) list every model's meshes, dimensions, materials, bones and built-in animations.
- An asset line-up render to check scale between buildings, Maya and the zombies:

![Asset line-up and scale check](docs/images/asset_lineup.png)

### What are we doing next?
Build the campus layout and props from primitives and polygon meshes (Phase 2).

---

## Checkpoint 2: Build the Graphics *(week of 9 Nov)*

### What algorithms have been implemented?
All of these are in [build_zombie.py](build_zombie.py):

- **Primitive generation (bmesh):** cubes, cones/cylinders with configurable segments and taper, and icospheres, created by `mesh_for()` and `mk()`. Meshes are cached and shared between objects (instancing) to save memory.
- **Composite mesh building:** `build_mesh()` combines many primitives into one polygon mesh by applying a per-part matrix `Translation · Rotation(Euler) · Scale` and assigning a material index to each face. Every tree, bush, grass clump, fern, flower and rock is generated this way, with a seeded RNG so the results are reproducible.
- **Constructive Solid Geometry:** the university arch is a solid block with a box and a cylinder **subtracted** (Boolean `DIFFERENCE`, exact solver) to cut the tunnel.
- **Curves and text:** the "UNIVERSITY" sign is an extruded 3D font (Bézier outline) curve.
- **Procedural geometry:** the steel fence (≈240 posts plus rails with a gap), the ground crack (a random-walk polyline turned into segments) and the radial window-crack pattern.
- **Procedural materials:** noise texture → colour ramp → base colour for the lawn, paving, courtyard, arch stone and wooden floor. Principled BSDF materials cover metal, wood, emission (radio dial) and alpha-blended glass.
- **Asset placement:** `building()` loads each building, scales it, computes its bounding box and rotates it around its door line so the front faces the correct compass direction. It then recolours the materials from a palette.

### Screenshot of current scene
| Bench and radio                              | Pose check (side view)                                            |
| -------------------------------------------- | ----------------------------------------------------------------- |
| ![Bench scene](docs/images/scene2_bench.png) | ![Side view of the seated pose](docs/images/pose_check_bench.png) |

### GitHub link
https://github.com/clive-strath/computer_graphics_project3.2

### What remains?
Characters and zombies, transformations and animation, the camera work, lighting changes over time, and the interior set.

---

## Checkpoint 3: Transform and Animate *(week of 16 Nov)*

### Current implementation (Blender in place of OpenGL)
The scene is rendered with **Blender EEVEE**, a GPU rasteriser in the same family as an OpenGL pipeline: vertex transforms, depth testing, shadow maps and temporal anti-aliasing. Settings: 1280×720, 6 TAA samples, shadows on, ray tracing off for speed, AgX tone mapping with a medium-high-contrast look.

**Transformations used:**
- **Hierarchical transforms (scene graph):** door slabs are parented to hinge empties, so rotating the hinge swings the door. The radio, its antenna and dial, the pigeons and their wing pivots, and the window crack are all child objects. Maya's bag is parented to her **Torso bone**, so it follows the skeleton.
- **Quaternions:** camera and sun orientations are built with `to_track_quat()` (a look-at). Each new quaternion is negated if its dot product with the previous one is negative, so interpolation always takes the short path and the camera never spins the long way round.
- **Angle wrapping:** character headings wrap into ±π so turns between waypoints take the shortest direction.

### Animation / interaction evidence
- **Keyframe animation:** character paths (`route()` waypoints), door swings, the bag falling off the bench, pigeons flying off, dirt mounds growing, the crack spreading, the radio dial switching off, and roughly 50 camera shots (the `SH` table: start and end position, target and lens per shot).
- **Skeletal animation and NLA blending:** Maya and the zombies use armature rigs. Base actions (Walk, Run, Jump, Duck, Punch, Wave, Idle, Crawl) are placed as NLA strips with speed scaling and repeat counts. **Custom pose layers** written from scratch as quaternion bone keys (`P_Sit`, `P_Floor`, `P_LookLR`, `P_LookBack`, `P_Talk`, `P_Around`, `P_Reach`) are blended on top in `COMBINE` mode with blend-in and blend-out times.
- **Procedural animation (drivers):** sine-wave expressions make the grass tremble before the zombies rise, flap the pigeon wings and add hand-held camera shake during the chase. Each is limited to a time window.
- **Crowd choreography:** 30 zombies in 5 groups (arch, garden, east trees, alley, courtyard). Each follows its own route with randomised offsets, closes in on Maya around a circle (`ring()`) and swaps to a fallback animation when a rig lacks one.
- **Visibility and teleporting:** objects are shown or hidden with keyframed `hide_render`, and characters move off-stage between scenes.
- **Lighting animation:** sky horizon and zenith colours, world strength, and sun direction, energy and colour are keyframed from golden morning to an overcast, desaturated end. Hard cuts at scene changes.

| Zombies rising                                                   | The chase                                              |
| ---------------------------------------------------------------- | ------------------------------------------------------ |
| ![Zombies rising from the garden](docs/images/scene4_rising.png) | ![Maya at a locked door](docs/images/scene6_chase.png) |

> **Interaction:** this project is a film, so its "interaction" is between characters (zombies track and surround Maya, doors respond to knocks) rather than user input. Each scene was checked interactively by scrubbing the timeline in Blender and with [devtools.py](devtools.py) `render` / `side`.

### GitHub link
https://github.com/clive-strath/computer_graphics_project3.2

### What remains?
Rendering all 7,920 frames, the soundtrack and dialogue, titles, subtitles and credits, and the final edit.

---

## Checkpoint 4: Render & Integrate *(week of 23 Nov)*

### Final demonstration
The final film is `The_Zombie_Apocalypse.mp4` (330 s, 1280×720). Video files are not committed to Git because of their size (see `.gitignore`). Running the pipeline below regenerates the film, and the team can share the rendered copy directly.

| Interior                                                         | Final scene                                           |
| ---------------------------------------------------------------- | ----------------------------------------------------- |
| ![Interior with cracked window](docs/images/scene7_interior.png) | ![Maya surrounded](docs/images/scene8_surrounded.png) |

### What works?
- **A fully reproducible build:** one script creates the whole scene (about 1,200 lines), with seeded randomness so every rebuild gives the same film.
- **The complete 10-scene film** with 31 animated characters, about 50 camera shots, lighting changes over time and an interior set.
- **A procedural soundtrack** ([make_audio.py](make_audio.py)), written in NumPy with no audio samples:
  - Synthesised pads, plucks, kick drums and a 150 BPM chase cue.
  - FFT band-pass filtering for footsteps, wind, rumble, knocks and zombie groans.
  - Radio effects (band-limited speech, distortion, static, drop-outs) and echo on the final line.
  - Soft clipping (`tanh`) and normalisation on the final mix.
- **Dialogue:** 10 TTS lines, synchronised to the subtitles.
- **The final edit:** fade-in and fade-out to black, title card, alternating subtitle channels, "THE END" card and rolling credits, all composited with alpha blending in the Video Sequencer and exported as H.264/AAC MP4.
- **Render safety:** placeholder and no-overwrite settings let several machines or sessions render frames in parallel and resume after a crash.

### What doesn't work / known limitations
- **Hard-coded asset paths:** the scripts load the Quaternius asset packs from absolute `C:/Users/clive/Downloads/...` paths, so the build only runs on the original machine until those paths are changed.
- **Assets are not in the repo:** the building and character packs must be downloaded separately.
- **Version-specific API:** the build uses Blender 5.x APIs (layered/slotted actions, `sequence_editor.strips`) and will not run on older Blender versions.
- **Synthetic voices:** the TTS dialogue sounds robotic, and lip movement is a simple head-nod layer rather than true lip-sync.
- **Simplified character interaction:** zombies follow pre-planned routes rather than true AI pathfinding, so a limb can occasionally clip through a wall or another zombie.
- **Long render:** 7,920 EEVEE frames take a long time to render; there is no low-resolution preview mode yet.


### Final changes / recommendations
1. Move asset locations into a config file or environment variable and document where to download each pack.
2. Add a `--preview` option (lower resolution or every Nth frame) for quick review renders.
3. Replace the TTS with recorded voice acting and add basic mouth shapes.
4. Remove the unused code, and add `*.blend1` to `.gitignore`.
5. Upload the final MP4 to a release or video host and link it here.

---

## Project development progression

| Stage                                     | Course expectation                                            | How it was met in this project                                                                                             |
| ----------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **CP1: Technical Foundation**             | Implement graphics techniques and build simplified components | Primitive and mesh generators, CSG arch, procedural vegetation, materials, asset probes and line-up renders                |
| **CP2: Transformation & Animation**       | Add transformations and animation to the components           | Matrix-composed meshes, hierarchical rigs, quaternion cameras, keyframes, drivers, skeletal and NLA animation, pose layers |
| **CP3: Integration** *(OpenGL → Blender)* | Bring the components into one rendering system                | Everything brought together in one Blender/EEVEE scene with lighting, cameras and render settings                          |
| **Prototype**                             | Combine the components into a working prototype               | Test stills and side-angle checks ([devtools.py](devtools.py)) used to tune poses and shots before the full render         |
| **Final Project**                         | Complete graphics, animation, interaction and other features  | Fully rendered 330 s film with soundtrack, dialogue, subtitles, title and credits                                          |

---

## How to run

Requires **Blender 5.3** on `PATH`, **NumPy** (bundled with Blender) and **Windows** for the TTS step. Update the asset paths at the top of `build_zombie.py` first.

```bash
# 1. Build the scene
blender -b -y --python build_zombie.py

# 2. Render all frames into frames/  (resumable; can be run in several sessions at once)
blender -b TheZombieApocalypse.blend -a

# 3. Voices and soundtrack
powershell -ExecutionPolicy Bypass -File make_voices.ps1
blender -b --factory-startup --python make_audio.py

# 4. Final edit -> The_Zombie_Apocalypse.mp4
blender -b --factory-startup --python assemble.py

# Optional: test stills at given times (seconds) into test/
blender -b TheZombieApocalypse.blend --python devtools.py -- render 58 150.5 250
```

## Credits

- **Team:** Sekandi Clive, Glen Musila, Lenny Mwaura, Theuri Matthew, Gabriel Kibet
- **Characters, zombies and buildings:** [Quaternius](https://quaternius.com) (CC0)
- **Voices:** Microsoft Windows text-to-speech
- **Music and sound effects:** generated procedurally ([make_audio.py](make_audio.py))
