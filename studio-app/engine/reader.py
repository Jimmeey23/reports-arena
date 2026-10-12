"""Embed current reader assets in served, generated and downloaded reviews."""
from pathlib import Path
import re
STATIC = Path(__file__).resolve().parent.parent / 'static'

def enhance_report(html):
    # Refresh older embedded readers without duplicating their controls.
    html = re.sub(r'<style id="p57-reader-assets">.*?</style><script>.*?</script>', '', html, flags=re.S)
    css = '\n'.join((STATIC / f).read_text() for f in
                    ('report-tools.css', 'presenter.css', 'chapter-explorer.css',
                     'report-edit.css', 'ai-assistant.css'))
    js = '\n'.join((STATIC / f).read_text() for f in
                   ('report-tools.js', 'presenter.js', 'chapter-explorer.js',
                    'report-edit.js', 'ai-assistant.js'))
    assets = f'<style id="p57-reader-assets">{css}</style><script>{js}</script>'
    index = html.lower().rfind('</body>')
    return html[:index] + assets + html[index:] if index >= 0 else html + assets
