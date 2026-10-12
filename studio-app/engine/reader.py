"""Embed current reader assets in served, generated and downloaded reviews."""
from pathlib import Path
import re, base64
STATIC = Path(__file__).resolve().parent.parent / 'static'

def enhance_report(html):
    # Update visible legacy copy only; leave frozen source data and scripts intact.
    def refresh_copy(match):
        text = match.group(0)
        text = text.replace('Cash taken', 'Sales revenue').replace('cash taken', 'sales revenue')
        text = re.sub(r'(₹[\d,]+(?:\.\d+)?) was taken', r'Sales revenue reached \1', text)
        text = re.sub(r'(₹[\d,]+(?:\.\d+)?) taken', r'\1 in sales revenue', text)
        replacements = {'The till, and what sits behind it': 'Sales at a glance',
                        'The commitment-length problem': 'Short packages, shorter runway',
                        'Pricing and the product ladder': 'Price points that pull their weight',
                        'Trading pattern through the month': 'When sales picked up',
                        'Where the cash actually arrived': 'Sales across the month',
                        'How the month was paid for': 'Basket size and repeat buyers',
                        'Who sold it': 'The team behind the sales',
                        'How the money arrived': 'How members paid',
                        'Who the money came from': 'Who drove the sales',
                        'What the first purchase predicts': 'First purchase, next steps',
                        'What else could explain it': 'Other factors to check',
                        'The one-line version, if you read nothing else.': 'The key takeaway',
                        'The loyal core halved its frequency': 'Regulars: are they coming back?',
                        'Cash is the least interesting number in this chapter.': 'Read sales alongside session revenue.',
                        'That ratio is what tells a studio whether it is trading or borrowing from next month.': 'Sales and delivered session revenue measure different activity; this ratio is not a reconciliation of purchases and usage.'}
        for old, new in replacements.items(): text = text.replace(old, new)
        return text
    html = re.sub(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)|([^<]+)',
                  lambda m: m.group(1) or refresh_copy(m), html, flags=re.S | re.I)
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
