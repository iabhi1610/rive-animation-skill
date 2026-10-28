# Rive animation skill

An AI agent skill for building Rive animations with RML and the Rive CLI. It teaches your coding agent to:

- **Keep `.riv` files small**: reference fonts and swappable images, size the art correctly, and thin keyframes.
- **Manage state well**: drive state machines with view model properties, one layer per behaviour, and give every state a way out.
- **Sync sound and music**: key audio events on the exact frame, use app-played sounds, and time motion to the BPM.
- **Use the fewest keyframes**: use eases instead of sampled keys, and prove the motion is unchanged frame by frame.
- **Support many device sizes**: build a responsive layout shell, handle safe areas, and test at real phone and tablet sizes.
- **Ask good questions**: when a brief is vague, ask up to 3 questions based on the 12 principles of animation, plus which devices it's for.

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
