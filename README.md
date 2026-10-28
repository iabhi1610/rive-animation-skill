# Rive animation skill

An AI agent skill for building Rive animations with RML and the Rive CLI. It teaches your coding agent to:

- **Keep `.riv` files small**: reference fonts and swappable images, size the art correctly, and thin keyframes.
- **Manage state well**: drive state machines with view model properties, one layer per behaviour, and give every state a way out.
- **Sync sound and music**: key audio events on the exact frame, use app-played sounds, and time motion to the BPM.
- **Use the fewest keyframes**: use eases instead of sampled keys, and prove the motion is unchanged frame by frame.
- **Support many device sizes**: build a responsive layout shell, handle safe areas, and test at real phone and tablet sizes.
- **Ask good questions**: when a brief is vague, ask up to 3 questions based on the 12 principles of animation, plus which devices it's for.

## Example: file size

Real production screens, measured after each step. Thinning was checked frame by frame with
`frame_diff.py` (worst difference 2/255 or less on the files checked), so the motion looks the same.

| Screen | Before | Fonts and photos referenced | Keys thinned | Saved |
|---|---:|---:|---:|---:|
| Reward unlock (chest, confetti) | 2,829 KB | 805 KB | **485 KB** | 83% |
| Word of the day card | 735 KB | 57 KB | **55 KB** | 93% |
| Streak goal | 461 KB | 320 KB | **290 KB** | 37% |
| Result screen | 374 KB | 209 KB | **198 KB** | 47% |
| Streak challenge | 292 KB | 152 KB | **122 KB** | 58% |
| Daily streak | 238 KB | 97 KB | **88 KB** | 63% |

- **Fonts and photos referenced** (biggest win for text-heavy files): the app already has the font, so the `.riv` keeps only its name.
- **Keys thinned** (biggest win for busy motion like confetti): the reward screen had about 50,000 keyframes.

A small version of what thinning does:

Before: 31 linear keys sampling a straight move, and 7 hold keys repeating the same opacity.

```xml
<KeyFrameDouble value="50" frame="0" interpolationType="linear"/>
<KeyFrameDouble value="55" frame="2" interpolationType="linear"/>
<KeyFrameDouble value="60" frame="4" interpolationType="linear"/>
<!-- ... 27 more on the same line ... -->
<KeyFrameDouble value="200" frame="60" interpolationType="linear"/>
```

After `thin_keys.py`: 4 keys in all, and `frame_diff.py` reports 0/255 difference.

```xml
<KeyFrameDouble frame="0" value="50" interpolationType="linear"/>
<KeyFrameDouble frame="60" value="200" interpolationType="linear"/>
```

## Install

It uses the open Agent Skills format (a folder with a `SKILL.md`), so it works in any coding agent that
supports skills: Cursor, Codex, and others.

### One command, any agent

```bash
npx skills add iabhi1610/rive-animation-skill
```

It asks which of your installed agents to add it to. Add `-g` to install it for all your projects.

### Or clone it into your agent's skills folder

Most agents read `.agents/skills/`, so this one command covers Cursor and Codex:

```bash
# this project only (run in the project folder)
git clone https://github.com/iabhi1610/rive-animation-skill .agents/skills/rive-animation

# every project
git clone https://github.com/iabhi1610/rive-animation-skill ~/.agents/skills/rive-animation
```

| Agent | This project | Every project |
|---|---|---|
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Any other agent | its skills folder (see its docs) | its skills folder |

If your agent has no skills support, point it at the file from your `AGENTS.md` or rules file:
"For Rive work, follow `rive-animation/SKILL.md`."

You end up with:

```
.agents/skills/rive-animation/
├── SKILL.md
└── tools/
    ├── thin_keys.py     drop keyframes that change nothing
    └── frame_diff.py    compare two builds frame by frame
```

The agent picks it up automatically when you work on Rive files.

## Requirements

- [Rive CLI](https://rive.app) (written against 1.3.0)
- Python 3. `frame_diff.py` also needs Pillow: `pip install pillow`

## Tools

```bash
# thin keys in <project>/scene.rml (rewrites it in place, so commit first)
python3 tools/thin_keys.py <project>

# compare old and new builds; pass is a worst difference of 3/255 or less
python3 tools/frame_diff.py OLD_PROJECT NEW_PROJECT out_dir 0.5s 1s 1.5s
```

## Contributors

- Abhijeet Ranjan ([@iabhi1610](https://x.com/iabhi1610))
- Jahanvi Singh ([@me_Jahanvi](https://x.com/me_Jahanvi))

## License

MIT. See [LICENSE](LICENSE).
