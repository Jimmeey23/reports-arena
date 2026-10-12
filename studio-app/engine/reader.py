"""Embed current reader assets in served, generated and downloaded reviews."""
from pathlib import Path
import re
STATIC = Path(__file__).resolve().parent.parent / 'static'

def enhance_report(html):
    # Refresh older embedded readers without duplicating their controls.
    html = re.sub(r'<style id="p57-reader-assets">.*?</style><script>.*?</script>', '', html, flags=re.S)
    css = (STATIC / 'report-tools.css').read_text() + '\n' + (STATIC / 'presenter.css').read_text() + '\n' + (STATIC / 'chapter-explorer.css').read_text()
    js = (STATIC / 'report-tools.js').read_text() + '\n' + (STATIC / 'presenter.js').read_text() + '\n' + (STATIC / 'chapter-explorer.js').read_text()
    assets = f'<style id="p57-reader-assets">{css}</style><script>{js}</script>'
    index = html.lower().rfind('</body>')
    return html[:index] + assets + html[index:] if index >= 0 else html + assets
