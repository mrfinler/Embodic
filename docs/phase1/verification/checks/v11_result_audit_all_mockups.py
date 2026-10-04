# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Re-verification: audit every numeric RESULT shown in every mockup for value + unit + exactly one status badge +
# EQ-ID link (or kind tag input/derived/count) + "n assumptions" tag (D-007). A result container is the nearest
# .mini/.tile/.rcard-main/li/.row/[data-role=result] ancestor of a status badge that also holds a number; badges inside the
# status filter, the status legend, oracle tables, input tables of "How was this computed" and DRC rows are excluded.
# Run: python3 docs/phase1/verification/checks/v11_result_audit_all_mockups.py
import glob, os, json
from playwright.sync_api import sync_playwright
M = '/home/claude/embodic/docs/phase1/design/mockups/'
JS = r"""() => {
  const out = [];
  const excl = e => e.closest('fieldset, #res-filter-status, table, [data-role=legend], .legend, .status-defs, aside .defs, [aria-label*="Status labels"], .drc, [id*=drc]');
  document.querySelectorAll('.badge[data-status]').forEach(b => {
    if (excl(b)) return;
    let c = b.closest('.mini, .tile, .rcard-main, [data-role=result], li, .row, .kv, .res');
    if (!c) return;
    const txt = c.innerText.replace(/\s+/g, ' ');
    if (!/\d/.test(txt.replace(/EQ-\d+|\d+ assum\w*( inputs?)?|O\d|L\d|[ABC]\d\+?/g, ''))) return;   // must show a number
    if (/\(input\)|\binput\b · default|Route:/.test(txt) || /^(Plating|Via|Stator thickness)/.test(txt)) return;   // inputs / non-numeric labels, not results
    const badges = c.querySelectorAll('.badge[data-status]').length;
    const unit = !!c.querySelector('.u, .unit, small.u') || /\d\s*(Ω|mΩ|V|mV|µH|mH|A|mA|N·m|mN·m|W|mW|K|°C|mm|µm|g|T|%|A\/mm²|rpm|V·s\/rad|mV·s\/rad|mN·m\/A|Hz)(?![\w])/.test(txt);
    const eq = !!c.querySelector('a.eq') || /\b(input|derived|count)\b/.test(Array.from(c.querySelectorAll('.tag')).map(t => t.innerText).join(' '));
    const asm = /\d+\s+assum(ptions?|ed inputs?)/i.test(txt);
    out.push({text: txt.slice(0, 70), badges, unit, eq, asm, status: b.dataset.status});
  });
  const seen = new Set(); return out.filter(o => { if (seen.has(o.text)) return false; seen.add(o.text); return true; });
}"""
with sync_playwright() as p:
    br = p.chromium.launch()
    for f in sorted(glob.glob(M + '*.html')):
        pg = br.new_page(viewport={'width': 1440 if '06' not in f else 390, 'height': 900}); pg.goto('file://' + f)
        rs = pg.evaluate(JS); bad = [r for r in rs if not (r['badges'] == 1 and r['unit'] and r['eq'] and r['asm'])]
        print(f"{os.path.basename(f)}: result containers {len(rs)}, complete {len(rs) - len(bad)}")
        for r in bad: print('   INCOMPLETE', json.dumps(r, ensure_ascii=False))
        pg.close()
    br.close()
