"""Compare a project's old and new build frame by frame: python3 tools/frame_diff.py OLD_DIR NEW_DIR out_dir [artboard] [--data k=v ...] [times...]
Both dirs are rive projects (with rive.yaml). Prints, per time, the biggest per-channel difference and how many pixels differ by more than 3/255."""
import subprocess, sys, os, shutil
RIVE = shutil.which('rive') or os.path.expanduser('~/.rive/bin/rive')
from PIL import Image, ImageChops
args = sys.argv[1:]
old, new, out = args[:3]; rest = args[3:]
artboard = None; data = []; times = []
i = 0
while i < len(rest):
    a = rest[i]
    if a == '--data': data.append(rest[i + 1]); i += 2; continue
    if a.endswith('s') and a[:-1].replace('.', '').isdigit(): times.append(a); i += 1; continue
    artboard = a; i += 1
times = times or [f'{t/10:.1f}s' for t in range(2, 90, 4)]
os.makedirs(out, exist_ok=True)
worst_all = 0
for t in times:
    imgs = []
    for tag, d in (('o', old), ('n', new)):
        cmd = [RIVE, '.', '--screenshot=' + os.path.abspath(f'{out}/{tag}-{t}.png'), f'--advance={t}']
        if artboard: cmd.append(f'--artboard={artboard}')
        for kv in data: cmd.append(f'--data={kv}')
        subprocess.run(cmd, cwd=d, capture_output=True)
        imgs.append(Image.open(f'{out}/{tag}-{t}.png').convert('RGB'))
    diff = ImageChops.difference(*imgs)
    ex = diff.getextrema(); mx = max(e[1] for e in ex)
    n = sum(1 for p in diff.getdata() if max(p) > 3)
    worst_all = max(worst_all, mx)
    if mx > 3: print(f'{t}: max {mx}, {n} px differ by >3')
print(f'worst difference over {len(times)} frames: {worst_all}/255')
