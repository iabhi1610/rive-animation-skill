"""Drop keyframes that change nothing: the file is smaller, the animation is the same.

Run on a generated scene.rml (or call thin(text) from a generator before it writes the file):
    python3 tools/thin_keys.py <project>        # rewrites <project>/scene.rml, prints what it saved

Keyframes may be written with their attributes in any order; one-line keys are rewritten in a fixed order first.

Two exact-or-invisible rules, applied per animated property:
  * a hold key right after a hold key with the same value is redundant (exact);
  * inside a run of linear keys, a key that sits on the straight line between its neighbours is redundant
    (Ramer-Douglas-Peucker, so no kept key is ever further than the tolerance from the line it replaced).
Any other property (mesh points, trim, strengths) gets at most 0.02. Tolerances are far below what the eye or an 8-bit screen can show: 0.02 px for position, 0.0002 for scale and
rotation (0.02 px on 100 px of artwork), 0.001 for opacity (a quarter of one 8-bit level).
Cubic keys (they carry their own easing curve) and keys of any other kind are left alone.

Opt-in, thin(text, fit=True): a run of linear keys sampled off a smooth curve (confetti flights, a twisting mesh, sampled
loops) is replaced, stretch by stretch, by single keys that carry a cubic ease (the same CubicEaseInterpolator the
generators write), wherever the ease stays within the same tolerances at every original key and halfway between them.
A stretch is only turned into a curve when that saves keys over the straight-line thinning. Off by default: each
generator turns it on once its frames are checked with tools/frame_diff.py. The cubic keys it writes are not matched
again, so thin() stays the same when run on its own output.
"""
import re, sys, os

TOL = {'13': 0.02, '14': 0.02, '15': 0.0002, '16': 0.0002, '17': 0.0002, '18': 0.001}
KEYED = re.compile(r'(<KeyedProperty propertyKey="(\d+)">\n)(.*?)(\n[ \t]*</KeyedProperty>)', re.S)
KEY = re.compile(r'^[ \t]*<KeyFrameDouble frame="(-?\d+)" value="([^"]*)" interpolationType="(linear|hold)"/>$')
ANYKEY = re.compile(r'^[ \t]*<KeyFrameDouble frame="(-?\d+)" value="([^"]*)" interpolationType="(\w+)"')   # fit=True: eased keys too


def _rdp(pts, tol):
    keep = {0, len(pts) - 1}
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        fa, va = pts[a]; fb, vb = pts[b]
        worst, wi = -1.0, None
        for i in range(a + 1, b):
            f, v = pts[i]
            e = abs(va + (vb - va) * (f - fa) / (fb - fa) - v)
            if e > worst:
                worst, wi = e, i
        if worst > tol:
            keep.add(wi); stack.append((a, wi)); stack.append((wi, b))
    return keep


# ---- curve fitting (opt-in)
# A cubic ease maps the segment's time u (0..1) to its value share y through a Bezier with fixed ends (0,0), (1,1) and
# controls (x1, y1), (x2, y2). For each candidate (x1, x2) the curve's parameter s at every key's u comes from a lookup
# table; y1, y2 then follow from least squares (the value is linear in them), and the worst miss decides.
_XS = [(1 / 3, 2 / 3), (0.25, 0.75), (0.5, 0.5), (0.15, 0.5), (0.5, 0.85), (0.3, 0.9), (0.1, 0.7), (0.42, 0.58), (0.6, 1.0), (0.0, 0.4)]
_TABLE_N = 512

def _table(x1, x2):
    """u -> s for the Bezier x(s) = 3(1-s)^2 s x1 + 3(1-s) s^2 x2 + s^3, on _TABLE_N + 1 even steps of u."""
    out, s = [], 0.0
    for k in range(_TABLE_N + 1):
        u = k / _TABLE_N
        lo, hi = 0.0, 1.0
        for _ in range(30):
            m = (lo + hi) / 2
            if 3 * (1 - m) ** 2 * m * x1 + 3 * (1 - m) * m * m * x2 + m ** 3 < u: lo = m
            else: hi = m
        out.append((lo + hi) / 2)
    return out

_TABLES = None

def _s_of(tab, u):
    t = u * _TABLE_N
    k = int(t)
    if k >= _TABLE_N: return tab[-1]
    return tab[k] + (tab[k + 1] - tab[k]) * (t - k)

def _fit(pts, tol):
    """pts: [(frame, value)] from a key to the key a stretch ends on. Returns (x1, y1, x2, y2) or None."""
    global _TABLES
    if _TABLES is None:
        _TABLES = [(x1, x2, _table(x1, x2)) for x1, x2 in _XS]
    (f0, v0), (f1, v1) = pts[0], pts[-1]
    dv, df = v1 - v0, f1 - f0
    if abs(dv) < 1e-9:
        return None
    # Check at every key (within tol), and halfway between keys. There the keys are only samples of a curve, joined by
    # straight lines; a curve through them bows away from each chord by about an eighth of the local second difference,
    # so halfway points get that much room (and no more: no overshoot between keys).
    probe = []
    for k in range(len(pts) - 1):
        if k:
            probe.append((pts[k][0], pts[k][1], tol))
        def d2(j):                                   # second difference round key j (0 at the ends)
            return abs(pts[j - 1][1] - 2 * pts[j][1] + pts[j + 1][1]) if 0 < j < len(pts) - 1 else 0.0
        bend = max(d2(k), d2(k + 1))
        probe.append(((pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2, tol + 0.2 * bend))
    for x1, x2, tab in _TABLES:
        A = B = C = D = E = 0.0
        rows = []
        for f, v, t in probe:
            s = _s_of(tab, (f - f0) / df)
            a, b = 3 * (1 - s) ** 2 * s, 3 * (1 - s) * s * s
            r = (v - v0) / dv - s ** 3
            rows.append((a, b, r, t))
            w = 1.0 if t == tol else 0.0           # fit the keys; the halfway points only bound it
            A += w * a * a; B += w * a * b; C += w * b * b; D += w * a * r; E += w * b * r
        det = A * C - B * B
        if abs(det) < 1e-12:
            continue
        y1, y2 = (D * C - E * B) / det, (A * E - B * D) / det
        if all(abs((a * y1 + b * y2 - r) * dv) <= t for a, b, r, t in rows):
            return (x1, y1, x2, y2)
    return None

def _straight(pts, tol):
    (f0, v0), (f1, v1) = pts[0], pts[-1]
    return all(abs(v0 + (v1 - v0) * (f - f0) / (f1 - f0) - v) <= tol for f, v in pts[1:-1])

def _fit_run(pts, tol):
    """Greedy over a run of linear segments: from each key, the longest stretch a straight line covers, or a longer one
    a cubic ease covers (only when that is smaller in the file: an eased key costs about three plain ones).
    Returns [(index, ease or None)] for the keys to keep (the last key is the caller's)."""
    out, i, n = [], 0, len(pts)
    while i < n - 1:
        j = i + 1
        while j + 1 < n and _straight(pts[i:j + 2], tol):
            j += 1
        # longest cubic stretch: grow by doubling, then binary search back
        best, lo, step = None, j + 1, 2
        hi = None
        k = i + 3
        while k < n:
            e = _fit(pts[i:k + 1], tol)
            if e: best = (k, e); k += step; step *= 2
            else: hi = k; break
        if best:
            lo = best[0] + 1
            hi = min(hi if hi is not None else n, n)
            while lo < hi:
                mid = (lo + hi) // 2
                e = _fit(pts[i:mid + 1], tol)
                if e: best = (mid, e); lo = mid + 1
                else: hi = mid
        # in the .riv an eased key costs about three plain ones (its ease is four more numbers): take the curve only when
        # it covers more ground per byte than the straight line does
        if best and (best[0] - i) > 3 * (j - i):
            out.append((i, best[1])); i = best[0]
        else:
            out.append((i, None)); i = j
    return out


def _thin_property(key, lines, fit=False):
    """lines: the property's key lines. Returns the lines worth keeping."""
    parsed = [(ANYKEY if fit else KEY).match(l) for l in lines]
    if not all(parsed) or len(lines) < 3:
        return lines                                   # (with fit, an eased key only ends a run of linear ones)
    ks = [(int(m.group(1)), float(m.group(2)), m.group(3)) for m in parsed]
    if any(ks[i][0] >= ks[i + 1][0] for i in range(len(ks) - 1)):
        return lines                                   # frames must strictly rise
    drop = set()
    eases = {}
    # exact: hold after a hold of the same value
    last = 0                                           # the last key kept so far
    for i in range(1, len(ks)):
        if ks[i][2] == 'hold' and ks[last][2] == 'hold' and ks[i][1] == ks[last][1] and i < len(ks) - 1:
            drop.add(i)
        else:
            last = i
    # linear runs: keys i..j are linear, so the segments up to key j+1 are straight lines
    i = 0
    n = len(ks)
    while i < n:
        if ks[i][2] != 'linear' or i in drop:
            i += 1
            continue
        j = i
        while j + 1 < n and ks[j + 1][2] == 'linear' and (j + 1) not in drop:
            j += 1
        end = min(j + 1, n - 1)
        pts = [(ks[x][0], ks[x][1]) for x in range(i, end + 1)]
        if len(pts) > 2 and all(x not in drop for x in range(i, end + 1)):
            vals = [p[1] for p in pts]
            tol = TOL.get(key, min(0.02, 0.0005 * max(1.0, abs(max(vals)), abs(min(vals)))))
            if fit and len(pts) > 3:
                kept = _fit_run(pts, tol)
                keep_idx = {k for k, _ in kept} | {len(pts) - 1}
                for k, e in kept:
                    if e:
                        eases[i + k] = e
                for k in range(1, len(pts) - 1):
                    if k not in keep_idx:
                        drop.add(i + k)
            else:
                keep = _rdp(pts, tol)
                for k in range(1, len(pts) - 1):
                    if k not in keep:
                        drop.add(i + k)
        i = j + 1
    out = []
    for x, l in enumerate(lines):
        if x in drop:
            continue
        if x in eases:
            x1, y1, x2, y2 = eases[x]
            l = l.replace('interpolationType="linear"/>', 'interpolationType="cubic">'
                          f'<CubicEaseInterpolator x1="{x1:.4g}" y1="{y1:.5g}" x2="{x2:.4g}" y2="{y2:.5g}"/></KeyFrameDouble>')
        out.append(l)
    return out


_ONEKEY = re.compile(r'^([ \t]*)<KeyFrameDouble((?:\s+\w+="[^"]*")+)\s*/>$', re.M)
_ATTR = re.compile(r'(\w+)="([^"]*)"')


def _normalise(text):
    """Rewrite one-line keys with only frame/value/interpolationType, in any attribute order, as
    frame, value, interpolationType (a missing interpolationType is hold, the format's default), so the
    matchers above see hand-written RML too. Keys with any other attribute are left alone."""
    def sub(m):
        a = dict(_ATTR.findall(m.group(2)))
        if not {'frame', 'value'} <= a.keys() or not a.keys() <= {'frame', 'value', 'interpolationType'}:
            return m.group(0)
        return (f'{m.group(1)}<KeyFrameDouble frame="{a["frame"]}" value="{a["value"]}" '
                f'interpolationType="{a.get("interpolationType", "hold")}"/>')
    return _ONEKEY.sub(sub, text)


def thin(text, fit=False):
    text = _normalise(text)
    def sub(m):
        body = m.group(3).split('\n')
        return m.group(1) + '\n'.join(_thin_property(m.group(2), body, fit)) + m.group(4)
    return KEYED.sub(sub, text)


if __name__ == '__main__':
    for proj in [a for a in sys.argv[1:] if not a.startswith('--')]:
        p = os.path.join(proj, 'scene.rml')
        before = open(p).read()
        after = thin(before, fit='--fit' in sys.argv)
        n0, n1 = before.count('<KeyFrameDouble'), after.count('<KeyFrameDouble')
        open(p, 'w').write(after)
        print(f'{proj}: {n0} -> {n1} keyframes')
