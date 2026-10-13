"""Regression checks for the supplied-file Bandra reconciliation."""
import collections
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
import openpyxl

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location('reconcile', APP / 'analysis/reconcile_bandra_sources.py')
reconcile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconcile)


class BandraSourceTests(unittest.TestCase):
    def setUp(self):
        self.run = APP / 'runs/20261011-232828-eb72'
        self.receipt = json.loads((APP / 'analysis/bandra-source-reconciliation.json').read_text())

    def test_sources_unchanged_and_all_workbooks_reviewed(self):
        self.assertEqual(len(self.receipt['sources']), 13)
        for name, expected in self.receipt['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_both_bandra_runs_and_no_duplicate_anchors_or_tables(self):
        for target in reconcile.TARGETS:
            directory = APP / 'runs' / target
            mf = json.loads((directory / 'manifest.json').read_text())
            self.assertEqual(len(mf['chapters']), 10)
            self.assertEqual(mf['source_reconciliation']['version'], 2)
            doc = BeautifulSoup((directory / 'report.html').read_text(), 'html.parser')
            ids = [n['id'] for n in doc.select('[id]')]
            self.assertEqual(len(ids), len(set(ids)))
            for a in doc.select('a[href^="#"]'):
                self.assertIn(a['href'][1:], ids)
            signatures = [tuple(tuple(c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td']))
                                for tr in table.find_all('tr')) for table in doc.find_all('table')]
            self.assertEqual(len(signatures), len(set(signatures)))
            self.assertIsNone(doc.select_one('#p57-source-records'))
            self.assertIsNone(doc.select_one('.p57-monthly'))
            for ch in mf['chapters']:
                single = BeautifulSoup((directory / (ch['id'] + '.html')).read_text(), 'html.parser')
                for section in ch['sections']:
                    self.assertIsNotNone(single.find(id=section['id']))
                for a in single.select('.source-cross-reference a'):
                    self.assertIn(a['href'].split('#')[1], ids)

    def test_requested_chapter_order_in_document_navigation_and_manifest(self):
        expected = list(reconcile.FILES)
        for target in reconcile.TARGETS:
            directory = APP / 'runs' / target
            mf = json.loads((directory / 'manifest.json').read_text())
            self.assertEqual([c['id'] for c in mf['chapters']], expected)
            self.assertEqual([c['n'] for c in mf['chapters']], list(range(1, 11)))
            doc = BeautifulSoup((directory / 'report.html').read_text(), 'html.parser')
            headings = [section.find('h2')['id'] for section in doc.select('.wrap > section')]
            self.assertEqual(headings, ['chapter-' + cid for cid in expected])
            links = [a['href'][1:] for a in doc.select('.wrap > nav.toc a')]
            self.assertEqual(links, [c['slug'] for c in mf['chapters']])

    def test_future_combined_reports_follow_requested_order(self):
        from types import SimpleNamespace
        from engine.build import _combined
        chapters = [dict(id=cid, n=n, slug=cid, title=cid, body='<p>Evidence</p>',
                         kpis=[], recs=[]) for n, cid in enumerate(reconcile.FILES, 1)]
        # Input order and stale chapter numbers must not override presentation order.
        chapters.reverse()
        for ch in chapters:
            ch["n"] = 1
        metrics = SimpleNamespace(studio='Test', D=SimpleNamespace(sources=[]),
                                  y=2026, m=9, sales={}, room={}, core={})
        doc = BeautifulSoup(_combined(metrics, chapters, 'September 2026'), 'html.parser')
        self.assertEqual([s['id'] for s in doc.select('.wrap > section')], list(reconcile.FILES))

    def test_sales_and_trial_conflicts_resolved_in_content_and_ai(self):
        sales = BeautifulSoup((self.run / 'sales.html').read_text(), 'html.parser')
        text = sales.select_one('.wrap').get_text(' ', strip=True)
        self.assertIn('195', sales.select_one('.kpis').get_text())
        self.assertIn('98 single-purchase buyers', text)
        self.assertIn('205 members with one September visit', text)
        self.assertNotIn('103 single-purchase members', text)
        self.assertNotIn('Lifting the 98 members who came exactly once', text)
        leads = BeautifulSoup((self.run / 'leads.html').read_text(), 'html.parser')
        text = leads.select_one('.wrap').get_text(' ', strip=True)
        self.assertIn('911 of them bought', text)
        self.assertNotIn('1006 of them', text)
        for table in leads.find_all('table'):
            if 'Ever won' in table.get_text():
                yes = next(tr for tr in table.select('tbody tr') if tr.td.get_text(strip=True) == 'Yes')
                self.assertEqual(yes.find_all('td')[3].get_text(), '911')
        from ai.metrics_pack import load_pack
        pack = load_pack(str(APP / 'runs'), self.run.name)
        tx = [m for m in pack['metrics'] if m['id'] == 'transactions']
        self.assertEqual(tx[0]['value'], 195)
        self.assertEqual(len(tx), 1)
        self.assertEqual(next(m['value'] for m in pack['metrics'] if m['id'] == 'aov'), 7843)
        from ai.metrics_pack import from_manifest
        fallback = from_manifest(json.loads((self.run / 'manifest.json').read_text()))
        self.assertEqual(next(m['value'] for m in fallback['metrics'] if m['id'] == 'transactions'), 195)
        self.assertEqual(next(m['value'] for m in fallback['metrics'] if m['id'] == 'aov'), 7843)

    def test_supplementary_workbook_values_exactly_preserved(self):
        workbook = openpyxl.load_workbook(ROOT / 'Bandra_September_2026_Data.xlsx', data_only=True)
        for cid, names in reconcile.SUPPLEMENTS.items():
            doc = BeautifulSoup((self.run / (cid + '.html')).read_text(), 'html.parser')
            blocks = {b.h2.get_text(strip=True): b for b in doc.select('.source-supplement')}
            for name in names:
                rows = [[c.get_text() for c in tr.find_all(['th', 'td'])] for tr in blocks[name].select('tr')]
                expected = [['n/a' if v is None else str(v) for v in row] for row in workbook[name].values]
                self.assertEqual(rows, expected, name)

    def test_new_source_sections_present_once(self):
        sales = BeautifulSoup((self.run / 'sales.html').read_text(), 'html.parser')
        headings = [h.get_text(strip=True) for h in sales.select('h2')]
        for title in ['Observed membership upgrades', 'Annual and private member purchases',
                      'Source performance register', 'Month-by-month source scorecard']:
            self.assertEqual(headings.count(title), 1)
        self.assertIn('source', str(sales.select_one('.source-reconciliation')).lower())
        self.assertIn('18 October 2026', sales.select_one('.source-reconciliation').get_text())


if __name__ == '__main__':
    unittest.main()
