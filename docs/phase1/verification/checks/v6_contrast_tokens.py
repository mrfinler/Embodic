# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Recomputes every contrast pair in design/tokens.json with an own implementation of the WCAG 2.x relative-luminance
# formula (sRGB linearisation threshold 0.04045, L = 0.2126 R + 0.7152 G + 0.0722 B, ratio (L1+0.05)/(L2+0.05)),
# checks that fg/bg hex values match the theme tokens, and that the mockups' CSS custom properties use the same values.
# Run: python3 docs/phase1/verification/checks/v6_contrast_tokens.py
import json, re, glob
D = '/home/claude/embodic/docs/phase1/design/'
T = json.load(open(D + 'tokens.json'))
def lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def lum(h):
    h = h.lstrip('#'); h = ''.join(x * 2 for x in h) if len(h) == 3 else h
    r, g, b = (int(h[i:i + 2], 16) for i in range(0, 6, 2))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
def ratio(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
light = T['themes']['light']['tokens']
def tokhex(theme, name):
    v = T['themes'][theme].get('tokens', {}).get(name)
    if v is None and theme == 'light_pure_greyscale_variant':
        v = T['themes'][theme]['overrides'].get(name) or light.get(name)
    if isinstance(v, dict): v = v.get('value') or v.get('hex')
    return v
tot = fails = mism = disagree = 0; worst = []; exempt = []
for th, v in T['themes'].items():
    for p in v['contrast_pairs']:
        tot += 1
        r = ratio(p['fg_hex'], p['bg_hex'])
        if p.get('min') is None:   # exempt pairs (disabled text, decorative lines): recompute ratio only
            exempt.append((th, p['fg'], p['bg'], round(r, 2), p['ratio'])); 
            if abs(r - p['ratio']) > 0.015: disagree += 1
            continue
        ok = r >= p['min'] - 1e-9
        if not ok: fails += 1
        if abs(r - p['ratio']) > 0.015: disagree += 1; print('  ratio disagreement', th, p['fg'], p['bg'], round(r, 3), p['ratio'])
        if ok != p['pass']: print('  pass flag disagreement', th, p)
        fh, bh = tokhex(th, p['fg']), tokhex(th, p['bg'])
        if (fh and fh.lower() != p['fg_hex'].lower()) or (bh and bh.lower() != p['bg_hex'].lower()):
            mism += 1; print('  hex differs from token', th, p['fg'], fh, p['fg_hex'], '|', p['bg'], bh, p['bg_hex'])
        worst.append((r / p['min'], th, p['fg'], p['bg'], round(r, 2), p['requirement']))
print(f'exempt pairs (no minimum, ratio recomputed only): {len(exempt)}')
print(f'pairs {tot}; below requirement {fails}; stated ratio differs from recomputed by >0.015: {disagree}; pair hex != theme token: {mism}')
for w in sorted(worst)[:6]: print('  tightest margin:', w)
# mockup CSS custom properties vs light tokens
for f in sorted(glob.glob(D + 'mockups/*.html')):
    css = open(f).read()
    props = dict(re.findall(r'--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', css))
    hx = lambda v: (v.get('hex') if isinstance(v, dict) else v).lower()
    diff = [(k, props[k], hx(light[k])) for k in props if k in light and hx(light[k]) != props[k].lower()]
    print(f.split('/')[-1], 'CSS hex colour props', len(props), '| same name in light tokens', sum(1 for k in props if k in light),
          '| value differences', diff, '| props without a token of that name', sorted(k for k in props if k not in light))
