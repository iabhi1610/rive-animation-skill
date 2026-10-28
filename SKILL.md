---
name: rive-animation
description: How to build, tune and ship Rive animations with RML and the Rive CLI. Covers keeping the .riv file small, state management with view models, syncing sound and music, cutting keyframes down to the fewest that still give the same motion, responsive layout for many device sizes, and a short choreography and target-device check based on the 12 principles of animation for vague briefs. Use when creating, editing, optimising or reviewing any .rml file, RML generator script or .riv.
---

# Rive animation

RML and the Rive CLI are newer than your training data. Never guess a type,
property or key number. Look it up:

- `rive schema <Type>` / `rive schema --search <text>`
- `rive docs <topic>`: `assets`, `state-machines`, `data`, `easing`, `gotchas`, `workflow`, `format`

The CLI installs to `~/.rive/bin/rive` if `rive` is not on PATH. Written against Rive CLI 1.3.0;
if a type or flag here disagrees with `rive schema`/`rive docs`, trust the CLI.
`--advance` takes frames (`40`), seconds (`1.5s`) or ms (`250ms`). A bare `0.7` is an error.

When a visual is unclear, match the project's design source (Figma frame, mockup or reference video).
If the project has one, it should be named in the project's AGENTS.md (or your agent's instructions file).

Preview with `rive .` (it opens a window and rebuilds on save; start it once, in the background).
Do not preview with `rive push`: it uploads to the user's Rive account.

The helper scripts named below live in the `tools/` folder next to this file
(for example `rive-animation/tools/thin_keys.py`). They need Python 3, and
`frame_diff.py` also needs Pillow (`pip install pillow`).

Order of work for any new animation:

1. Read the brief. If it is vague, or does not say which devices it is for, ask the questions in
   section 5. Otherwise go.
2. Pick the layout kind (section 6) and design the state model (section 2), then the timelines.
3. Build the responsive shell and check it at the smallest and largest device size before adding detail.
4. Build, then thin the keys (section 4), then check size (section 1).
5. `rive . --verify`, `rive inspect . --summary`, `rive . --screenshot --advance=<t>` at the key moments,
   at each device size in section 6. Look at the PNGs. A clean build is not proof the animation is right.

---

## 1. Keep the .riv file small

What usually makes a file big, from largest to smallest:
**keyframes > embedded images > fonts > audio > shapes.**
Real production screens, measured after each step (thinning checked with frame_diff: worst
difference 2/255 or less on the files checked):

| Screen | Before | Fonts and photos referenced | Keys thinned | Saved |
|---|---:|---:|---:|---:|
| Reward unlock (chest, confetti) | 2,829 KB | 805 KB | **485 KB** | 83% |
| Word of the day card | 735 KB | 57 KB | **55 KB** | 93% |
| Streak goal | 461 KB | 320 KB | **290 KB** | 37% |
| Result screen | 374 KB | 209 KB | **198 KB** | 47% |
| Streak challenge | 292 KB | 152 KB | **122 KB** | 58% |
| Daily streak | 238 KB | 97 KB | **88 KB** | 63% |

Text-heavy files gain most from referencing fonts. Busy motion (confetti, particles) gains most from
thinning: the reward screen had about 50,000 keys.

### Checklist

1. **Do not embed fonts the app already has.** Mark the `FontAsset` `exportTypeValue="referenced"` with a
   fixed `assetId` and a clear `name`. The app supplies the bytes through its runtime's asset loader.
   Use the same id and name in every file so one loader serves them all.
2. **User photos and swappable pictures are referenced, not embedded.** Either reference them by name the
   same way, or expose a `ViewModelPropertyAssetImage` that the app sets.
   Keep a table of every referenced asset (name, id, type, which files use it) in the project README.
3. **Embedded art goes in at display size, never bigger.** Export at the largest size it is shown
   (for example 2x the artboard size), as WebP: lossless for flat art and emblems, lossy (q ≈ 85) for
   photos and painterly art. A 1024 px PNG drawn at 120 px is the most common waste.
4. **Draw it as vectors when you can.** A flat icon as shapes is a few hundred bytes. The same icon as
   a PNG is kilobytes. Gradients, strokes and simple paths are cheap. Images are not.
5. **Reuse, do not duplicate.** One `ImageAsset` referenced by many `Image`s. One component artboard
   placed many times (with `isStateful="true"` when each copy needs its own data) instead of copied art.
   One timeline played at a different `speed`, or `-1` to reverse, instead of a mirrored copy.
6. **Thin the keyframes** (section 4). This is usually the biggest win.
7. **Strip the leftovers.** Delete unused assets, hidden test art, old timelines and orphan view model
   properties. `exportFlags="2"` keeps an asset out of the build. Note that `hidden="true"` art still ships,
   it just does not draw.
8. **Audio:** short mono WAV costs about 88 KB a second at 44.1 kHz/16-bit. Prefer MP3 (WAV, MP3 and FLAC decode;
   Ogg/M4A fail the build), trim to the sound itself, and keep music out of the file (section 3).
9. **SVG and Lottie assets are stripped on export.** Convert them to shapes first.

### Measure, do not guess

```bash
ls -l build/*.riv                                   # size now
rive inspect . --json | jq -c '[..|objects|select((.type//"")|endswith("Asset"))|{type,name,exportTypeValue}]'
grep -c '<KeyFrame' scene.rml                        # key count
```

Write before and after sizes into the project README.

---

## 2. State management

### Rules

1. **Drive everything with view model properties.** `StateMachineBool/Number/Trigger` inputs are
   deprecated. A listener writes a property with `ListenerViewModelChange`. A transition reads it with
   `TransitionViewModelCondition`. The same property can also bind to colours, sizes and text.
2. **The view model is the API between the app and the animation.** Name it for the app developer:
   - inputs the app sets: plain names (`title`, `count`, `complete`, `showTrophies`)
   - triggers the app fires: verbs (`play`, `dismiss`)
   - signals the animation sends back: past tense (`finished`)
   - internal helpers: a leading underscore (`_count`, `_roll`, `_screenW`). The app must not touch these.
   Document every public property in the project README.
3. **Pick the right property type.**
   - Boolean for a two-way state (`connected`, `complete`).
   - Enum for one of several modes (`idle | searching | found | error`). This beats three booleans
     that could all be true at once.
   - Trigger for a one-off moment (`play`, `dismiss`). It is used up at the end of the frame it fires in.
   - Number for continuous values (progress, counts). Feed blend states or converters with it.
4. **One layer per independent thing.** Layers run at the same time. An idle loop, an entrance and a
   button's hover each get their own layer, so you never need a state for every combination. If two
   layers key the same property, the later layer wins. Plan for this or keep the properties apart.
5. **Every state needs a way out.** Author both directions of a toggle. A state with no exit builds
   clean and works once.
6. **Sequences:** chain timelines with `enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"`
   (the typo is in the format, so write it that way).
7. **Hold states are one-key timelines.** Rest, hover and pressed each hold one pose. Set the transition's
   `duration` (milliseconds) and the runtime blends between them. Do not key the in-between yourself.
8. **Loops at rest:** one state, a timeline with `loopValue="loop"`, no outgoing transitions.
9. **Tell the app when it is done.** Set a `finished` trigger, or fire an `Event`, at the end of the
   outro. For example, a loader can end when the app sets `complete` to true.
10. **Components:** a nested artboard reads its parent's data unless the placement has
    `isStateful="true"`. Forgetting this is the classic "works alone, dead when nested" bug.
11. **Every state gets an `x`/`y`** so the editor graph is readable. `StateMachine` is declared before
    any `LinearAnimation`. The artboard names it in `defaultStateMachineId`.

### Prove it

```bash
rive inspect . --json | jq '.problems'
rive . --screenshot=a.png --data=complete=true --advance=1.5s   # prints `data: complete = true` when the path resolves
rive . --data-dump=- --data=complete=true --advance=1.5s | jq '.viewModel'   # read values back
```

Render each state and each transition at its start, middle and end. Check the two-way paths too.

---

## 3. Sound and music sync

### Sound effects inside the file (frame accurate)

Declare the audio, give it an `AudioEvent`, and **key the event's `trigger` on the timeline** with a
`KeyFrameCallback` at the frame where the sound hits:

```xml
<AudioAsset file="sfx/pop.mp3" name="pop" id="0:70"/>
<!-- inside the Artboard -->
<AudioEvent assetId="0:70" name="pop" id="0:61"/>
<!-- inside the LinearAnimation -->
<KeyedObject objectId="0:61">
    <KeyedProperty propertyKey="395">          <!-- Event.trigger, a callback property -->
        <KeyFrameCallback frame="30"/>
    </KeyedProperty>
</KeyedObject>
```

This is checked: a test file with the key at frame 30 logged nothing at `--advance=20` and
`sound pop: triggered` at `--advance=40`. The key fires again on every loop.

Other ways to fire it:
- on entering or leaving a state: `<StateMachineFireEvent eventId="0:61" occursValue="0"/>` (`0` start, `1` end)
- on a tap: `<ListenerFireEvent eventId="0:61"/>` inside the listener

### Sounds the app plays (usually the better choice in a mobile app)

Fire a plain, named `Event` (for example `sfx_pop`, `sfx_coin`) at the same keyed frame. The app listens
for Rive events and plays the sound itself. This keeps audio out of the `.riv`, follows the phone's silent
switch and volume settings, and lets the app preload sounds. Add custom properties to the event when the
app needs more detail (`CustomPropertyNumber name="pitch"`).

### Music

Never put music in the `.riv`. The app plays it. Fit the animation to the beat:

- frames per beat = `fps × 60 / BPM`. At 60 fps: 120 BPM = 30 frames, 100 BPM = 36 frames.
- Land the big moments (impact, reveal, the number landing) **on** a beat. Start the anticipation one
  beat before it.
- Fire an event (`beat_start`) on the first frame so the app can start the music in sync. Do not rely on
  both starting "at the same time".

### Timing rules for sound

- **Sound leads the picture slightly, or lands on it, never after it.** Put the sound key on the contact
  frame, or one or two frames before it. Sound that comes late feels broken. Sound that comes a little
  early feels snappy.
- Allow for output delay. Phones add about 20–100 ms (Android is often worse). For critical hits, fire the
  app-side event 2–3 frames (about 40 ms at 60 fps) before contact.
- One sound per beat of action. Stacked sounds blur together. Stagger them by at least 3–4 frames.
- Size each sound to the motion it goes with: a short tick for a small pop, a longer swell for a reveal.

### Checking

Screenshots run silently, but the log shows each fire: `sound <name>: triggered | muted | did not decode`.
Run `--advance` to just before and just after each sound key. Whether it *sounds* right is a listening
test in the previewer (`rive .`).

---

## 4. Fewest keyframes, same motion

### Author with few keys from the start

1. **Ease the segment, do not sample the curve.** Two keys with a `CubicEaseInterpolator` replace ten
   linear keys. The ease goes on the **first** key of the segment. The ease on the last key is never read.
2. **Overshoot without extra keys:** `elastic` with an `ElasticInterpolator`, or `cubicValue` with a
   `CubicValueInterpolator` whose `y1`/`y2` go past the end value. That gives one segment instead of
   three keys (go, overshoot, settle).
3. **Key only what moves.** Do not key x, y, scale and rotation "just in case". A property that never
   changes needs no keys at all. Its value in the scene is enough.
4. **Key the parent, not every child.** Move a group once instead of keying each piece. Put rigs and
   constraints on top of that (follow-through, `DistanceConstraint`, bones) instead of hand-keyed copies.
5. **Hold poses are one key.** Keep resting states as one-key timelines and let the transition `duration` blend.
6. **Loops:** use `loopValue="loop"` or `pingPong` instead of keying the way back. A ping-pong breathe
   needs two keys.
7. **Stagger by time, not by copies.** For rows of similar items, use the same short curve offset per
   item. If the motion is truly identical, use one component placed several times.
8. **Hand-off to code:** if something is driven by data (progress, counts), bind it to a view model
   number through a converter. Do not key every possible value.

### Clean up generated or imported keys

Run `tools/thin_keys.py` on any RML with many keys (sampled, generated or converted motion). If a
script generates the RML, import it and call `thin(text)` before writing the file. It only drops keys
within tolerances far below what a screen can show (0.02 px position, 0.0002 scale/rotation,
0.001 opacity):

- drops a hold key that repeats the same value
- drops a linear key that sits on the straight line between its neighbours (Ramer–Douglas–Peucker)
- `thin(text, fit=True)` (opt-in) swaps runs of sampled linear keys for single cubic-eased keys

```bash
python3 tools/thin_keys.py <project>       # rewrites <project>/scene.rml, prints what it saved
```

It handles one-line `KeyFrameDouble`s in any attribute order. Cubic keys and other keyframe types are
left alone. It reads only `scene.rml`; for other `.rml` files, call `thin()` from Python.
Commit or copy first: it rewrites the file in place.

### Prove the motion did not change

Copy the old project, thin, then compare frame by frame:

```bash
python3 tools/frame_diff.py OLD_DIR NEW_DIR /tmp/diff [artboard] [--data k=v] [times...]
```

Pass: worst difference **≤ 3/255** at every sampled time. Times need a unit (`0.5s`); with none given it samples 0.2–8.6 s.
If a frame fails, lower the tolerance for that property or leave that run alone. Always run it before
turning on `fit=True` (`--fit` on the command line).

### Common mistakes

- `cubic` with no nested interpolator eases nothing (`rive docs gotchas`).
- A key with no `interpolationType` is `hold` and snaps. This is the "slideshow" look.
- Rotation is in **radians**. Transition `duration` is in **ms**. Keyframe `frame` is in **frames**.

---

## 5. Choreography questions (12 principles)

**Ask only when the brief is vague.** A brief is vague when you cannot say what moves first, what the
main moment is, or how long it runs. If the brief, the design source or a sibling animation already
answers a question, do not ask it. Pick a default and say so.

**Keep it short:** at most **3 questions**, once per brief, all in one message (use your agent's question tool if it has one, with
options, and put a recommended default first). Never stop again mid-build to ask more. Use the defaults
below for anything left open.

### Pick the 1–3 questions that matter most for this brief

| Principle | Question to ask | Default if not answered |
|---|---|---|
| Staging | What is the **one** thing the eye should land on, and when? | The headline element / the badge |
| Timing | How long should the whole thing take, and is it snappy or calm? | Celebration 1.2–2 s; micro-interaction 150–300 ms; loader loop 1–1.6 s |
| Anticipation | Should the main move wind up first (a small dip, squash or pull back)? | Yes, 4–8 frames, about 10% of the move |
| Squash & stretch | How rubbery is it: rigid, soft or cartoony? | Soft: 5–10% squash, keep the volume the same |
| Follow-through & overlap | Do the parts arrive together, or does each settle after the one before? | Stagger children by 2–4 frames; small parts settle last |
| Slow in / slow out | Should it feel physical (ease), mechanical (linear) or bouncy (overshoot)? | ease-out to arrive, ease-in to leave, overshoot for celebrations |
| Arcs | Should things travel on curves or straight lines? | Curves for anything thrown, jumping or falling |
| Secondary action | Is there supporting motion (sparkles, glow, confetti), and how loud is it? | Yes, clearly quieter than the main action, starts after it lands |
| Exaggeration | How big is this moment for the user: subtle, normal or big win? | Match the product moment: milestone or reward = big, loader = subtle |
| Straight ahead vs pose to pose | Are there key poses (from the design) it must hit exactly? | Pose to pose, with the design frame as the final pose |
| Solid drawing | Does anything turn in depth (flip, tilt), or is it all flat? | Flat 2D. Fake depth with scaleX only if asked |
| Appeal | Any reference animation or feel to match? | Match the project's existing animations |

Also confirm, only if it is unclear: does it **loop, play once, or wait for the app** (`complete`, a
trigger)? And what **sound**, if any, goes with the main moment (section 3)?

### Target devices

If the brief does not say which devices it is for, ask this as one of the questions. This applies even
when the rest of the brief is clear, because it decides the layout kind (section 6). It still counts
toward the limit of 3.

> Which devices is this for?
> - **Phones only, portrait (Recommended)**: iOS and Android, about 320–430 pt wide
> - Phones and tablets: adds iPad and Android tablets, up to about 1024 pt wide
> - Phones in portrait and landscape
> - A fixed slot in the app UI (badge, loader, card), so it only scales

Default if not answered: phones only, portrait, iOS and Android. If the brief says where it sits
("full-screen celebration", "loader in the search bar"), infer the layout kind from that and do not ask.

### Turn the answers into a beat sheet before keying

Write a short timeline in the README or as a comment before building:

```
0.00s  anticipation: badge dips to 0.92 scale (6f, ease-in)
0.10s  main action: badge pops to 1.08 (10f, ease-out) + sfx_pop on contact frame
0.27s  settle 1.08 → 1.0 (elastic)
0.30s  follow-through: ring and sparkles, staggered 3f each
0.80s  hold. Fire `finished`
```

Then check the result against it with screenshots at each beat time.

---

## 6. Responsive layout (many device sizes)

Read `rive docs layout` before building a shell. Its silent failures are the main source of layout bugs.

### First, pick the layout kind

| Kind | Used for | Artboard | App fit | How it adapts |
|---|---|---|---|---|
| **Full screen** | celebrations, onboarding, results, rewards | your design base, e.g. 360 × 800 | `Fit.Layout` | artboard resized to the screen; layout shell pins regions to edges |
| **Fixed slot** | loaders, badges, icons, inline cards | its own size | `Fit.Contain` | the whole drawing scales into the slot the app gives it; no layout needed |

Decide this before anything else. A fixed-slot animation with a layout shell is wasted work. A full
screen without one crops or leaves gaps on every phone that is not exactly the design size.

### Full screen: the shell

Below, `W × H` is the design base (360 × 800 in the examples). If you generate RML, write this once as a
helper and reuse it in every screen.

```
Artboard (W × H, own LayoutComponentStyle)
  Screen      one LayoutComponent filling the artboard: the single layout root
    Region    full-screen absolute box (insets 0) that pins a fixed W × H Stage to an edge or the centre
                (the Region's style alignment picks the edge: topCenter, center, bottomCenter ...)
      Stage
        Content   plain Node with the hand-placed art in its authored coordinates
    Bleed     full-screen box painted edge to edge (backgrounds, gradients)
    Box       other absolute boxes, e.g. a button pinned 16 pt from the sides and the bottom
```

Rules:

1. **Think in edges, not coordinates.** For every element, decide which edge it belongs to: top
   (status area, title), centre (the hero moment), bottom (buttons, tray). Put each group in the
   region for that edge. The space between regions grows and shrinks with the phone.
2. **Backgrounds bleed. Content does not stretch.** Fills, gradients and glows go in a full-screen
   `Bleed` box. The hero art keeps its drawn size inside a `Node`, so it never distorts.
3. **Buttons and bars stretch across the width and keep their height:** absolute box with left/right
   insets, `hug` width, `fixed` height.
4. **Keep safe areas clear.** Keep important content about 48 pt from the top (status bar, notch,
   Dynamic Island) and 34 pt from the bottom (home indicator). Backgrounds still go under them.
   If the app passes real insets, bind them to view model numbers instead of guessing.
5. **Short and narrow phones scale the hero down, never up.** Bind the Screen's `computedWidth` (key 810)
   and `computedHeight` (key 811) into internal numbers (`_screenW`, `_screenH`, written with
   `direction="true"`). Then a formula converter sets the hero's scale to
   `s = min(1, width / W, (height − tray) / topContent)`, and shifts x by `W/2 × (1 − s)` to keep it
   centred (`DataConverterFormula`, see `rive docs data` → converters). Larger phones stay at s = 1.
6. **Large phones and tablets do not get bigger art.** Cap the content: a `maxWidth` on the content
   column (for example 430 pt) centred in the screen, with only the background filling the rest. The
   art stays crisp, and the layout looks deliberate rather than zoomed.
7. **Text must fit at every width.** Give titles a bounded width and an `overflowValue` (`fitFontSize` for
   one-line headlines, `wrap` for subtitles). Test with the longest real string, including other languages
   and big numbers ("1,000,000 points").
8. **Animate on top of layout, not by changing it.** Key `x`, `y`, `scale` and `opacity` on boxes or Nodes.
   These offset from the position the layout worked out, so motion stays correct at every size. Do not
   key widths, insets or padding for motion. Give scaled boxes a `ComponentOrigin` (0.5, 0.5).
9. **Motion distances are relative to the screen when they cross it.** A slide in from off-screen must
   start beyond the *largest* screen's edge, or be bound to `_screenW`/`_screenH`. Small moves (a pop,
   a 20 pt rise) can stay in points.
10. **Repeated symbols:** put them in their own artboard and place them with `NestedArtboardLeaf fit="contain"`.
    One definition renders right at any slot size.

The silent-failure checklist (every one builds clean and looks wrong):
- the artboard has no `LayoutComponentStyle` (`inspect` warns `artboard-without-style`; the editor can't fix it later)
- a style is nested but `styleId` doesn't point at it, so nothing applies
- padding, gap or inset with no `*UnitsValue="points"` is ignored
- a Shape/Text with no `LayoutParticipant` inside a fixed/fill box gets stretched to the box
- `fill` is a weight, not 100%; `fractionalWidth` goes on the component, not the style; `flexGrow` does nothing

### Fixed slot: scale-safe drawing

1. Draw centred in the artboard with a little padding, so `Contain` letterboxes evenly.
2. Pick an artboard aspect that matches the slot the app gives it, or the drawing shrinks to fit
   the short side.
3. Nothing important at the very edges. Glows and particles must fade out inside the artboard, or they
   will be cut at the edge.
4. Strokes and fine detail must still read at the smallest size it is shown. Check at 0.5× too.

### Device sizes to test (points)

| Device class | Size | Why |
|---|---|---|
| Small / old phone | 320 × 568, 375 × 667 | narrowest and shortest; no notch |
| Design base | your W × H | the authored size |
| Common modern phones | 390 × 844, 393 × 852 | most iPhones and many Androids |
| Large phone | 430 × 932 | widest phone |
| Tablet (only if in scope) | 768 × 1024, 1024 × 1366 | content cap and background fill |
| Landscape (only if in scope) | 844 × 390 | regions must not overlap |

```bash
for v in 320x568 375x667 360x800 393x852 430x932; do
  rive . --screenshot=build/size-$v.png --viewport=$v --advance=1.5s
done
```

Look at every PNG at the key beats (start, main moment, end). Check that:
- fixed regions keep their size and the gaps absorb the difference
- nothing overlaps (the hero vs the buttons on 320 × 568) and nothing is cut off at the sides
- backgrounds reach every edge
- text fits

For fixed-slot files use `--fit=contain` with a few slot sizes instead.

In the previewer (`rive .`), the default fit is `layout`, so dragging the window resizes the scene for
real. `z` snaps the window back to the artboard size.
