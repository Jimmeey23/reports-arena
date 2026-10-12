"""Embed current reader assets in served, generated and downloaded reviews."""
from pathlib import Path
import re, base64
STATIC = Path(__file__).resolve().parent.parent / 'static'

def enhance_report(html):
    # Refresh older embedded readers without duplicating their controls.
    html = re.sub(r'<style id="p57-reader-assets">.*?</style><script>.*?</script>', '', html, flags=re.S)
    css = '\n'.join((STATIC / f).read_text() for f in
                    ('report-tools.css', 'presenter.css', 'chapter-explorer.css',
                     'report-edit.css', 'ai-assistant.css', 'report-interface.css', 'atlas-theme.css',
                     'sticky-notes.css'))
    for font in ('archivo', 'archivo-ext', 'instrument-sans', 'instrument-sans-ext'):
        encoded = base64.b64encode((STATIC / 'fonts' / (font + '.woff2')).read_bytes()).decode()
        css = css.replace('/static/fonts/' + font + '.woff2', 'data:font/woff2;base64,' + encoded)
    js = '\n'.join((STATIC / f).read_text() for f in
                   ('report-tools.js', 'presenter.js', 'chapter-explorer.js',
                    'report-edit.js', 'ai-assistant.js', 'report-interface.js', 'chapter-art.js',
                    'chart-interact.js', 'talking-points.js', 'sticky-notes.js', 'presentation-stage.js'))
    assets = f'<style id="p57-reader-assets">{css}</style><script>{js}</script>'
    index = html.lower().rfind('</body>')
    return html[:index] + assets + html[index:] if index >= 0 else html + assets
