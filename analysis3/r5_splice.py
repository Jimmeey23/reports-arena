"""Splice the round-5 additions into the three round-4 report builders."""
import io, os, re

A = '/home/user/analysis3/'
IMPORTS = {
    'build_class.py': 'import d2_extra as X',
    'build_sales.py': 'import d2_extra as X',
    'build_teacher.py': 'import d2_extra as X',
}
DATA = {'build_class.py': 'r5_class.txt', 'build_sales.py': 'r5_sales.txt', 'build_teacher.py': 'r5_teacher.txt'}

for fn, datafile in DATA.items():
    p = A + fn
    s = open(p).read()
    if '# round-5 additions' in s:
        print(f'{fn}: already spliced, skipping'); continue
    if 'import d2_extra as X' not in s:
        # insert the alias import on the line after the d1_data import
        s = s.replace('import d1_data as D\n', 'import d1_data as D\nimport d2_extra as X\n', 1)
    data = open(A + datafile.replace('.txt','_d.txt')).read()
    # data block goes immediately before REC_HTML
    anchor = 'REC_HTML = rec_html(RECS)'
    assert anchor in s, f'{fn}: REC_HTML anchor missing'
    s = s.replace(anchor, data.rstrip() + '\n\n' + anchor, 1)
    # recommendations append inside RECS list; strip the leading stray comma on the separator line
    s = s.replace('\n ,\n', '\n')
    recs = open(A + datafile.replace('.txt', '_recs.txt')).read()
    tail = '\n]\nREC_HTML = rec_html(RECS)'
    assert tail in s, f'{fn}: RECS tail anchor missing'
    s = s.replace(tail, '\n' + recs.rstrip() + tail, 1)
    # narrative section before Recommendations
    sec = open(A + datafile.replace('.txt', '_sec.txt')).read()
    assert '<h2>Recommendations</h2>' in s, f'{fn}: Recommendations heading missing'
    s = s.replace('<h2>Recommendations</h2>', sec.rstrip() + '\n\n<h2>Recommendations</h2>', 1)
    open(p, 'w').write(s)
    print(f'spliced {fn}: {len(s):,} chars')
print('done')
