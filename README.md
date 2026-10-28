# Rive animation skill

An AI agent skill for building Rive animations with RML and the Rive CLI. It teaches your coding agent to:

- **Keep `.riv` files small**: reference fonts and swappable images, size the art correctly, and thin keyframes.
- **Manage state well**: drive state machines with view model properties, one layer per behaviour, and give every state a way out.
- **Sync sound and music**: key audio events on the exact frame, use app-played sounds, and time motion to the BPM.
- **Use the fewest keyframes**: use eases instead of sampled keys, and prove the motion is unchanged frame by frame.
- **Support many device sizes**: build a responsive layout shell, handle safe areas, and test at real phone and tablet sizes.
- **Ask good questions**: when a brief is vague, ask up to 3 questions based on the 12 principles of animation, plus which devices it's for.

## Install

For every project:

```bash
git clone https://github.com/iabhi1610/rive-animation-skill ~/.claude/skills/rive-animation
```

For one project, run this in the project folder:

```bash
git clone https://github.com/iabhi1610/rive-animation-skill .claude/skills/rive-animation
```

You end up with:

```
your-project/.claude/skills/rive-animation/
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
