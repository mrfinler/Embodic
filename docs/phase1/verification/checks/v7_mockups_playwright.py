# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Playwright/Chromium checks of the static mockups: horizontal overflow at stated widths, compat mode, language
# (Thai block, "Xcoil"), personal-name scan (name tokens are read at run time from the pitch deck and never printed),
# keyboard Tab walk on mockup 01, unit + EQ-ID + status badge on every numeric result in mockup 04.
# Run: python3 docs/phase1/verification/checks/v7_mockups_playwright.py
import re, subprocess, glob, json, os
from playwright.sync_api import sync_playwright
M = '/home/claude/embodic/docs/phase1/design/mockups/'
files = sorted(glob.glob(M + '*.html'))
# --- personal-name tokens from the deck (line after "Presented by:"), never printed
deck = subprocess.run(['pdftotext', '/mnt/user-data/uploads/Desktop/Embodic-PDF.pdf', '-'], capture_output=True, text=True).stdout.splitlines()
deck = [l.strip() for l in deck if l.strip()]
i = next(k for k, l in enumerate(deck) if l.lower().startswith('presented by'))
name_tokens = [t for t in deck[i + 1].split() if len(t) >= 4]
THAI = re.compile('[\u0E00-\u0E7F]')
def name_hits(text): return sum(text.lower().count(t.lower()) for t in name_tokens)
widths = {'06_phone.html': [320, 360, 390, 420], '05b_kicad_window.html': [880]}
default_widths = [1920, 1440, 1280, 1024, 960, 768]
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in files:
        n = os.path.basename(f); src = open(f, encoding='utf-8').read(); r = res[n] = {}
        r['source_thai'] = len(THAI.findall(src)); r['source_xcoil'] = len(re.findall('xcoil', src, re.I)); r['source_name_hits'] = name_hits(src)
        r['overflow'] = {}
        for w in widths.get(n, default_widths):
            pg = b.new_page(viewport={'width': w, 'height': 600 if n.startswith('05b') else 900})
            pg.goto('file://' + f)
            m = pg.evaluate("""() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
                bsw: document.body.scrollWidth, mode: document.compatMode, lang: document.documentElement.lang,
                text: document.body.innerText,
                attrs: Array.from(document.querySelectorAll('[aria-label],[title],[alt],[placeholder]')).map(e => [e.getAttribute('aria-label'), e.getAttribute('title'), e.getAttribute('alt'), e.getAttribute('placeholder')].filter(Boolean).join(' ')).join(' ')})""")
            r['overflow'][w] = m['sw'] - m['cw']
            if n.startswith('05b'):   # REQ-K-15 / UX-AC-21: Place action visible without scrolling at 880 x 600
                r['k15'] = pg.evaluate("""() => { const bs = Array.from(document.querySelectorAll('button, a.btn')).filter(e => /place/i.test(e.innerText));
                    return {vertical_overflow: document.documentElement.scrollHeight - document.documentElement.clientHeight,
                            place_buttons: bs.map(e => { const r = e.getBoundingClientRect(); return {text: e.innerText.trim().slice(0, 30), bottom: Math.round(r.bottom), right: Math.round(r.right), visible: r.bottom <= innerHeight && r.right <= innerWidth && r.top >= 0}; })}; }""")
            r['mode'] = m['mode']; r['lang'] = m['lang']
            r['rendered_thai'] = len(THAI.findall(m['text'] + m['attrs'])); r['rendered_xcoil'] = len(re.findall('xcoil', m['text'] + m['attrs'], re.I))
            r['rendered_name_hits'] = name_hits(m['text'] + m['attrs'])
            r['illustrative_stamp'] = bool(re.search(r'illustrative|not computed|example values', m['text'], re.I))
            pg.close()
    # --- keyboard walk, mockup 01 at 1440 px
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); pg.goto('file://' + M + '01_overview_desktop.html')
    walk = []
    for k in range(70):
        pg.keyboard.press('Tab')
        d = pg.evaluate("""() => { const e = document.activeElement; if (!e || e === document.body) return null;
            const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
            return {tag: e.tagName.toLowerCase(), id: e.id || '', name: (e.getAttribute('aria-label') || e.innerText || e.value || '').trim().slice(0, 40).replace(/\\s+/g, ' '),
                    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                    outline: cs.outlineStyle + ' ' + cs.outlineWidth, region: (e.closest('header,nav,aside,main,footer,[role=region]') || {}).tagName || ''}; }""")
        walk.append(d)
        if d and len(walk) > 3 and walk[0] and d['id'] == walk[0]['id'] and d['name'] == walk[0]['name'] and d['x'] == walk[0]['x']: break
    res['tabwalk_01'] = walk
    pg.close()
    # --- mockup 04: every numeric result (class .num inside result cards / rails / tables)
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); pg.goto('file://' + M + '04_results_traceability.html')
    cards = pg.evaluate("""() => Array.from(document.querySelectorAll('article.rcard')).map(c => {
        const nums = Array.from(c.querySelectorAll('.rcard-main .val .num'));
        const unit = c.querySelector('.rcard-main .val .u'); const meta = c.querySelector('.rcard-main .meta');
        return {id: c.id || c.getAttribute('aria-labelledby'), title: (c.querySelector('h3')||{}).innerText,
                value: nums.map(n => n.innerText).join('|'), unit: unit ? unit.innerText : null,
                badges: meta ? meta.querySelectorAll(':scope > .badge').length : 0,
                badge_status: meta ? Array.from(meta.querySelectorAll(':scope > .badge')).map(b => b.dataset.status) : [],
                eq: meta ? Array.from(meta.querySelectorAll('a.eq')).map(a => a.innerText) : [],
                tags: meta ? Array.from(meta.querySelectorAll('.tag')).map(t => t.innerText) : []}; })""")
    other = pg.evaluate("""() => Array.from(document.querySelectorAll('.num, td.num')).filter(e => !e.closest('article.rcard .rcard-main')).map(e => {
        const row = e.closest('tr, li, .tile, .kv, div'); return {text: e.innerText.slice(0, 30), ctx: (row ? row.innerText : '').replace(/\\s+/g,' ').slice(0, 90),
        has_badge: !!(row && row.querySelector('.badge')), has_eq: !!(row && row.querySelector('a.eq'))}; })""")
    res['m04_cards'] = cards; res['m04_other_numbers'] = other
    b.close()
print(json.dumps({k: v for k, v in res.items() if k not in ('tabwalk_01', 'm04_cards', 'm04_other_numbers')}, indent=1))
print('TAB WALK mockup 01 (1440 px):')
for k, d in enumerate(res['tabwalk_01']):
    print(f"  {k+1:2d}", None if d is None else f"{d['tag']}#{d['id']} '{d['name']}' at ({d['x']},{d['y']}) {d['w']}x{d['h']} outline={d['outline']} region={d['region']}")
print('MOCKUP 04 result cards:')
for c in res['m04_cards']: print('  ', c)
print('MOCKUP 04 other numeric elements:', len(res['m04_other_numbers']))
for o in res['m04_other_numbers'][:60]: print('  ', o)
