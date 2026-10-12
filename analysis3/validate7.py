"""Validate the nine Bandra September 2026 reports."""
import re, glob, os
from html.parser import HTMLParser

VOID = {'br','hr','img','input','meta','link','path','circle','line','rect','polyline','polygon','text',
        'use','stop','col','source','ellipse','g','tspan'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.st = []; s.err = []
    def handle_starttag(s, t, a):
        if t not in VOID: s.st.append((t, s.getpos()))
    def handle_endtag(s, t):
        if t in VOID: return
        if s.st and s.st[-1][0] == t: s.st.pop()
        elif any(x[0] == t for x in s.st):
            while s.st and s.st[-1][0] != t:
                b = s.st.pop(); s.err.append('unclosed <%s> at line %d' % b)
            s.st.pop()
        else: s.err.append('stray </%s> at line %d' % (t, s.getpos()[0]))

BAD = ['{R(', '{P(', '{N(', 'nan%', 'NaN', 'np.float', '{ev(', '{dumbbell(', 'np.nan', 'None%',
       '&u25b2', '&u25bc', '&u2014', 'a1}', 'a2}', '{T(', '&amp;amp;', '~~', '<strong>None']
FILES = sorted(glob.glob('/home/user/Bandra_September_2026_[1-9]_*.html'))
print(f'{"file":<52}{"bytes":>9}{"svg":>5}{"tbl":>5}{"ev":>5}{"rec":>5}{"h2":>4}  status')
tot = 0
allok = True
for fp in FILES:
    h = open(fp).read(); tot += len(h)
    p = P(); p.feed(h)
    core = re.sub(r'<details[^>]*>.*?</details>', '', h, flags=re.S)
    hits = [b for b in BAD if b in core]
    nsvg, ntbl, nev = h.count('<svg'), h.count('<table'), h.count('<details')
    nrec, nh2 = h.count('class="rec"'), len(re.findall(r'<h2[^>]*>', h))
    # every chart figure should contain an svg
    figs = re.findall(r'<figure class="chart">(.*?)</figure>', h, flags=re.S)
    emptyfig = sum(1 for f in figs if '<svg' not in f)
    # braces / unrendered template residue
    resid = re.findall(r'\{[A-Za-z_][A-Za-z0-9_ .\[\]\'"()]*\}', core)
    ok = not p.err and not hits and not resid and not emptyfig and not p.st
    allok &= ok
    st = 'OK' if ok else 'PROBLEM'
    print(f'{os.path.basename(fp):<52}{len(h):>9,}{nsvg:>5}{ntbl:>5}{nev:>5}{nrec:>5}{nh2:>4}  {st}')
    if p.err: print('   tags:', p.err[:4])
    if p.st: print('   unclosed at end:', [x[0] for x in p.st][:6])
    if hits: print('   residue:', hits[:6])
    if resid: print('   unevaluated:', sorted(set(resid))[:6])
    if emptyfig: print('   empty chart frames:', emptyfig)
print(f'\ntotal {tot:,} bytes across {len(FILES)} files | all clean: {allok}')
