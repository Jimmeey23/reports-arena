"""Embed the reader assets so served and downloaded reviews work offline."""
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / 'static'

def enhance_report(html):
    if 'id="p57-reader-assets"' in html:
        return html
    css = (STATIC / 'report-tools.css').read_text()
    js = (STATIC / 'report-tools.js').read_text()
    assets = f'<style id="p57-reader-assets">{css}</style><script>{js}</script>'
    index = html.lower().rfind('</body>')
    return html[:index] + assets + html[index:] if index >= 0 else html + assets
